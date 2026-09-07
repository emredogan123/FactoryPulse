from uuid import uuid4

import pytest

from app.analytics.quality import (
    build_quality_counts,
    get_production_quality,
)
from app.models.pcb_unit import (
    PCBUnit,
    PCBUnitStatus,
    ShiftType,
)
from app.models.production_order import ProductionOrder


def test_quality_rate_excludes_pending_records():
    result = build_quality_counts(
        total=10,
        passed=6,
        failed=1,
        rework=1,
    )

    assert result.evaluated_count == 8
    assert result.pending_count == 2
    assert result.issue_count == 2
    assert result.issue_rate == pytest.approx(25.0)


def test_quality_rate_is_none_without_results():
    result = build_quality_counts(3, 0, 0, 0)

    assert result.pending_count == 3
    assert result.issue_rate is None


def test_quality_empty_prefix(database_session):
    result = get_production_quality(
        database_session,
        prefix=f"EMPTY-{uuid4().hex}",
    )

    assert result.summary.total_count == 0
    assert result.summary.issue_rate is None
    assert len(result.shifts) == 2
    assert result.material_lots == []


def test_quality_groups_pcbs_without_material_lot(database_session):
    prefix = f"QUALITY-{uuid4().hex[:12]}"

    order = ProductionOrder(
        order_code=f"{prefix}-ORDER",
        product_code="TEST-PCB",
        target_quantity=4,
    )
    database_session.add(order)
    database_session.flush()

    records = [
        (ShiftType.DAY, PCBUnitStatus.PASSED),
        (ShiftType.DAY, PCBUnitStatus.FAILED),
        (ShiftType.DAY, PCBUnitStatus.QUEUED),
        (ShiftType.NIGHT, PCBUnitStatus.REWORK),
    ]

    for index, (shift, pcb_status) in enumerate(records):
        database_session.add(
            PCBUnit(
                serial_number=f"{prefix}-{index}",
                production_order_id=order.id,
                shift=shift,
                status=pcb_status,
            )
        )

    database_session.flush()

    result = get_production_quality(
        database_session,
        prefix=prefix,
    )

    assert result.summary.total_count == 4
    assert result.summary.evaluated_count == 3
    assert result.summary.pending_count == 1
    assert result.summary.issue_count == 2
    assert result.summary.issue_rate == pytest.approx(66.67)

    shifts = {item.shift: item for item in result.shifts}
    assert shifts["DAY"].issue_rate == pytest.approx(50.0)
    assert shifts["NIGHT"].issue_rate == pytest.approx(100.0)

    assert len(result.material_lots) == 1
    assert result.material_lots[0].material_lot_id is None
    assert result.material_lots[0].total_count == 4


def test_quality_endpoint_requires_authentication(client):
    response = client.get(
        "/api/v1/analytics/production-quality"
    )

    assert response.status_code == 401