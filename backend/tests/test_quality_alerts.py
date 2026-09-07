from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.analytics import alerts
from app.analytics.schemas import (
    DailyQualityItem,
    DailyQualityResponse,
)
from app.models.quality_alert import QualityAlert
from app.auth.schemas import UserCreate
from app.auth.service import create_user
from app.models.user import UserRole

def mock_daily_report(monkeypatch, evaluated, issues):
    def fake_report(db, start_date, end_date, prefix=None):
        return DailyQualityResponse(
            prefix=prefix,
            start_date=start_date,
            end_date=end_date,
            timezone="UTC",
            days=[
                DailyQualityItem(
                    date=start_date,
                    evaluated_count=evaluated,
                    passed_count=evaluated - issues,
                    warning_count=0,
                    failed_count=issues,
                    issue_count=issues,
                    issue_rate=(
                        round(100 * issues / evaluated, 2)
                        if evaluated
                        else None
                    ),
                )
            ],
        )

    monkeypatch.setattr(
        alerts,
        "get_daily_quality",
        fake_report,
    )


def create_alert(db, prefix):
    alert = QualityAlert(
        rule_code="DAILY_ISSUE_RATE_V1",
        dataset_prefix=prefix,
        quality_date=date(2026, 8, 1),
        evaluated_count=100,
        issue_count=6,
        threshold_percent=Decimal("5.00"),
        minimum_count=100,
    )
    db.add(alert)
    db.flush()
    return alert


@pytest.mark.parametrize(
    "evaluated,issues,expected",
    [
        (100, 5, 0),       # Tam %5: eşik aşılmadı.
        (100, 6, 1),       # Minimum sayı sağlandı, oran %6.
        (99, 20, 0),       # Oran yüksek ama işlem sayısı yetersiz.
        (0, 0, 0),         # Veri yok.
        (10001, 501, 1),   # Yuvarlanınca %5.00; gerçek oran > %5.
    ],
)
def test_alert_threshold(
    database_session,
    monkeypatch,
    evaluated,
    issues,
    expected,
):
    prefix = f"ALERT-{uuid4().hex}"
    mock_daily_report(monkeypatch, evaluated, issues)

    result = alerts.evaluate_daily_quality_alerts(
        database_session,
        date(2026, 8, 1),
        date(2026, 8, 1),
        prefix,
    )

    stored = database_session.execute(
        select(QualityAlert).where(
            QualityAlert.dataset_prefix == prefix
        )
    ).scalars().all()

    assert result["created_count"] == expected
    assert len(stored) == expected


def test_repeated_evaluation_preserves_review(
    database_session,
    monkeypatch,
):
    prefix = f"ALERT-{uuid4().hex}"
    mock_daily_report(monkeypatch, 100, 6)

    first = alerts.evaluate_daily_quality_alerts(
        database_session,
        date(2026, 8, 1),
        date(2026, 8, 1),
        prefix,
    )

    alert = database_session.execute(
        select(QualityAlert).where(
            QualityAlert.dataset_prefix == prefix
        )
    ).scalar_one()

    reviewed_at = datetime(2026, 8, 2, tzinfo=timezone.utc)
    alert.acknowledged_at = reviewed_at
    database_session.flush()

    second = alerts.evaluate_daily_quality_alerts(
        database_session,
        date(2026, 8, 1),
        date(2026, 8, 1),
        prefix,
    )

    database_session.refresh(alert)

    assert first["created_count"] == 1
    assert second["created_count"] == 0
    assert second["existing_count"] == 1
    assert alert.acknowledged_at == reviewed_at


def test_alert_endpoints_require_login(client):
    assert client.get(
        "/api/v1/analytics/alerts"
    ).status_code == 401

    assert client.post(
        f"/api/v1/analytics/alerts/{uuid4()}/acknowledge"
    ).status_code == 401


def test_acknowledgement_and_status_filter(
    client,
    database_session,
    admin_headers,
):
    prefix = f"ALERT-{uuid4().hex}"
    alert = create_alert(database_session, prefix)
    url = f"/api/v1/analytics/alerts/{alert.id}/acknowledge"

    first = client.post(url, headers=admin_headers)
    assert first.status_code == 200

    body = first.json()
    assert body["acknowledged_at"] is not None
    assert body["acknowledged_by_id"] is not None

    second = client.post(url, headers=admin_headers)
    assert second.status_code == 200
    assert second.json()["acknowledged_at"] == body["acknowledged_at"]
    assert second.json()["acknowledged_by_id"] == body["acknowledged_by_id"]

    pending = client.get(
        "/api/v1/analytics/alerts",
        params={"prefix": prefix, "acknowledged": "false"},
        headers=admin_headers,
    )
    assert pending.status_code == 200
    assert pending.json()["items"] == []

    reviewed = client.get(
        "/api/v1/analytics/alerts",
        params={"prefix": prefix, "acknowledged": "true"},
        headers=admin_headers,
    )
    assert reviewed.status_code == 200
    assert [item["id"] for item in reviewed.json()["items"]] == [
        str(alert.id)
    ]


def test_acknowledgement_returns_404_for_missing_alert(
    client,
    admin_headers,
):
    response = client.post(
        f"/api/v1/analytics/alerts/{uuid4()}/acknowledge",
        headers=admin_headers,
    )
    assert response.status_code == 404
def test_viewer_can_read_but_cannot_acknowledge(
    client,
    database_session,
):
    prefix = f"ALERT-{uuid4().hex}"
    alert = create_alert(database_session, prefix)

    email = f"viewer-{uuid4().hex}@factorypulse.dev"
    password = "SecurePassword123!"

    create_user(
        database_session,
        UserCreate(
            email=email,
            full_name="Alert Test Viewer",
            password=password,
            role=UserRole.VIEWER,
        ),
    )

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )
    assert login.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }

    listing = client.get(
        "/api/v1/analytics/alerts",
        params={"prefix": prefix},
        headers=headers,
    )

    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()["items"]] == [
        str(alert.id)
    ]

    acknowledgement = client.post(
        f"/api/v1/analytics/alerts/{alert.id}/acknowledge",
        headers=headers,
    )

    assert acknowledgement.status_code == 403

    database_session.refresh(alert)
    assert alert.acknowledged_at is None
    assert alert.acknowledged_by_id is None