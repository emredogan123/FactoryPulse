from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.analytics.service import calculate_rate
from app.auth.schemas import UserCreate
from app.auth.service import create_user
from app.models.user import UserRole
from app.simulation.config import SimulationConfig
from app.simulation.seeder import seed_demo_data


def create_auth_headers(
    client: TestClient,
    database_session: Session,
    email: str,
) -> dict[str, str]:
    password = "SecurePassword123!"

    create_user(
        database_session,
        UserCreate(
            email=email,
            full_name="Dashboard Viewer",
            password=password,
            role=UserRole.VIEWER,
        ),
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


def test_calculate_rate() -> None:
    assert calculate_rate(75, 100) == 75.0
    assert calculate_rate(1, 3) == 33.33
    assert calculate_rate(0, 0) == 0.0


def test_analytics_overview_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/analytics/overview"
    )

    assert response.status_code == 401


def test_analytics_overview_returns_expected_structure(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email="viewer-structure@factorypulse.dev",
    )

    response = client.get(
        "/api/v1/analytics/overview",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert "production_order_count" in data
    assert "pcb_count" in data
    assert "pcb_status_counts" in data
    assert "pass_rate" in data
    assert "failure_rate" in data
    assert "rework_rate" in data
    assert "process_event_count" in data
    assert "quality_measurement_count" in data
    assert "out_of_spec_measurement_count" in data

    assert set(data["pcb_status_counts"]) == {
        "passed",
        "failed",
        "rework",
        "queued",
    }


def test_analytics_overview_reflects_seeded_data(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_auth_headers(
        client,
        database_session,
        email="viewer-seed@factorypulse.dev",
    )

    before_response = client.get(
        "/api/v1/analytics/overview",
        headers=headers,
    )

    assert before_response.status_code == 200

    before = before_response.json()

    config = SimulationConfig(
        data_prefix="TEST-ANALYTICS",
        random_seed=42,
        order_count=1,
        pcb_per_order=4,
        anomaly_probability=0.0,
    )

    seed_demo_data(
        database_session,
        config,
    )

    after_response = client.get(
        "/api/v1/analytics/overview",
        headers=headers,
    )

    assert after_response.status_code == 200

    after = after_response.json()

    assert (
        after["production_order_count"]
        == before["production_order_count"] + 1
    )
    assert after["pcb_count"] == before["pcb_count"] + 4
    assert (
        after["pcb_status_counts"]["passed"]
        == before["pcb_status_counts"]["passed"] + 4
    )
    assert (
        after["process_event_count"]
        == before["process_event_count"] + 20
    )
    assert (
        after["quality_measurement_count"]
        == before["quality_measurement_count"] + 40
    )
    assert (
        after["out_of_spec_measurement_count"]
        == before["out_of_spec_measurement_count"]
    )

    expected_pass_rate = round(
        after["pcb_status_counts"]["passed"]
        / after["pcb_count"]
        * 100,
        2,
    )

    assert after["pass_rate"] == expected_pass_rate