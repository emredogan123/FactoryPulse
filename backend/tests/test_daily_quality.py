from datetime import date, datetime
from uuid import uuid4

import pytest

from app.analytics.daily_quality import get_daily_quality
from app.models.machine import Machine, StageType
from app.models.pcb_unit import PCBUnit
from app.models.process_event import (
    ProcessEvent,
    ProcessEventResult,
)
from app.models.production_order import ProductionOrder


def test_daily_quality_requires_authentication(client):
    response = client.get(
        "/api/v1/analytics/daily-quality",
        params={
            "start_date": "2026-08-01",
            "end_date": "2026-08-03",
        },
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "start_date,end_date",
    [
        ("2026-08-03", "2026-08-01"),
        ("2026-01-01", "2027-01-02"),
    ],
)
def test_daily_quality_rejects_invalid_range(
    client,
    admin_headers,
    start_date,
    end_date,
):
    response = client.get(
        "/api/v1/analytics/daily-quality",
        params={
            "start_date": start_date,
            "end_date": end_date,
        },
        headers=admin_headers,
    )

    assert response.status_code == 422


def test_daily_quality_dates_counts_and_empty_days(
    database_session,
):
    prefix = f"DAILY-{uuid4().hex[:12]}"

    order = ProductionOrder(
        order_code=f"{prefix}-ORDER",
        product_code="TEST-PCB",
        target_quantity=2,
    )

    machine = Machine(
        machine_code=f"{prefix}-MACHINE",
        name="Daily Quality Test Machine",
        stage_type=StageType.REFLOW_SOLDERING,
    )

    database_session.add_all([order, machine])
    database_session.flush()

    pcb = PCBUnit(
        serial_number=f"{prefix}-PCB-001",
        production_order_id=order.id,
    )

    other_pcb = PCBUnit(
        serial_number=f"{prefix}X-PCB-001",
        production_order_id=order.id,
    )

    database_session.add_all([pcb, other_pcb])
    database_session.flush()

    def add_event(result, completed_at, pcb_id=None):
        database_session.add(
            ProcessEvent(
                pcb_unit_id=pcb_id or pcb.id,
                machine_id=machine.id,
                result=result,
                started_at=datetime.fromisoformat(
                    "2026-07-31T00:00:00+00:00"
                ),
                completed_at=(
                    datetime.fromisoformat(completed_at)
                    if completed_at
                    else None
                ),
            )
        )

    # Başlangıç sınırı: dahil edilmeli.
    add_event(
        ProcessEventResult.PASSED,
        "2026-08-01T00:00:00+00:00",
    )

    # +03:00 ile 2 Ağustos; UTC'de hâlâ 1 Ağustos.
    add_event(
        ProcessEventResult.WARNING,
        "2026-08-02T01:00:00+03:00",
    )

    # UTC'de 2 Ağustos.
    add_event(
        ProcessEventResult.FAILED,
        "2026-08-02T00:00:00+00:00",
    )

    # Aralık öncesi ve sonrası: hariç tutulmalı.
    add_event(
        ProcessEventResult.FAILED,
        "2026-07-31T23:59:59+00:00",
    )
    add_event(
        ProcessEventResult.FAILED,
        "2026-08-04T00:00:00+00:00",
    )

    # Tarihi olsa da PENDING değerlendirmeye alınmamalı.
    add_event(
        ProcessEventResult.PENDING,
        "2026-08-01T12:00:00+00:00",
    )

    # Tamamlanma tarihi yok: hariç tutulmalı.
    add_event(
        ProcessEventResult.FAILED,
        None,
    )

    # Farklı prefix: hariç tutulmalı.
    add_event(
        ProcessEventResult.FAILED,
        "2026-08-01T12:00:00+00:00",
        pcb_id=other_pcb.id,
    )

    database_session.flush()

    result = get_daily_quality(
        db=database_session,
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 3),
        prefix=prefix,
    )

    assert result.timezone == "UTC"
    assert [item.date for item in result.days] == [
        date(2026, 8, 1),
        date(2026, 8, 2),
        date(2026, 8, 3),
    ]

    first, second, third = result.days

    assert first.evaluated_count == 2
    assert first.passed_count == 1
    assert first.warning_count == 1
    assert first.failed_count == 0
    assert first.issue_count == 1
    assert first.issue_rate == 50.0

    assert second.evaluated_count == 1
    assert second.failed_count == 1
    assert second.issue_rate == 100.0

    # Kayıt olmayan gün, %0 olarak yorumlanmamalı.
    assert third.evaluated_count == 0
    assert third.issue_count == 0
    assert third.issue_rate is None