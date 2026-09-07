from uuid import uuid4

import pytest

from app.analytics.stage_quality import get_stage_quality
from app.models.machine import Machine, StageType
from app.models.pcb_unit import PCBUnit
from app.models.process_event import (
    ProcessEvent,
    ProcessEventResult,
)
from app.models.production_order import ProductionOrder


def test_stage_quality_requires_authentication(client):
    response = client.get(
        "/api/v1/analytics/stage-quality"
    )

    assert response.status_code == 401


def test_stage_quality_empty_prefix(database_session):
    result = get_stage_quality(
        database_session,
        prefix=f"EMPTY-{uuid4().hex[:12]}",
    )

    assert len(result.stages) == len(StageType)

    for stage in result.stages:
        assert stage.total_count == 0
        assert stage.evaluated_count == 0
        assert stage.pending_count == 0
        assert stage.issue_count == 0
        assert stage.issue_rate is None


def test_stage_quality_counts_events_and_filters_prefix(
    client,
    database_session,
    admin_headers,
):
    prefix = f"STAGE-{uuid4().hex[:12]}"

    order = ProductionOrder(
        order_code=f"{prefix}-ORDER",
        product_code="TEST-PCB",
        target_quantity=2,
    )

    machine = Machine(
        machine_code=f"{prefix}-MACHINE",
        name="Test Reflow Oven",
        stage_type=StageType.REFLOW_SOLDERING,
    )

    database_session.add_all([order, machine])
    database_session.flush()

    selected_pcb = PCBUnit(
        serial_number=f"{prefix}-PCB-001",
        production_order_id=order.id,
    )

    # Benzer başlayan fakat farklı bir prefix:
    excluded_pcb = PCBUnit(
        serial_number=f"{prefix}X-PCB-001",
        production_order_id=order.id,
    )

    database_session.add_all([
        selected_pcb,
        excluded_pcb,
    ])
    database_session.flush()

    # Aynı PCB'nin dört ayrı proses kaydı.
    for result in (
        ProcessEventResult.PASSED,
        ProcessEventResult.WARNING,
        ProcessEventResult.FAILED,
        ProcessEventResult.PENDING,
    ):
        database_session.add(
            ProcessEvent(
                pcb_unit_id=selected_pcb.id,
                machine_id=machine.id,
                result=result,
            )
        )

    # Bu kayıt seçilen prefix'e dahil edilmemeli.
    database_session.add(
        ProcessEvent(
            pcb_unit_id=excluded_pcb.id,
            machine_id=machine.id,
            result=ProcessEventResult.FAILED,
        )
    )
    database_session.flush()

    response = client.get(
        "/api/v1/analytics/stage-quality",
        params={"prefix": prefix},
        headers=admin_headers,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["prefix"] == prefix

    stages = {
        item["stage_type"]: item
        for item in payload["stages"]
    }

    assert set(stages) == {
        stage.value for stage in StageType
    }

    reflow = stages["REFLOW_SOLDERING"]

    assert reflow["total_count"] == 4
    assert reflow["evaluated_count"] == 3
    assert reflow["pending_count"] == 1
    assert reflow["passed_count"] == 1
    assert reflow["warning_count"] == 1
    assert reflow["failed_count"] == 1
    assert reflow["issue_count"] == 2
    assert reflow["issue_rate"] == pytest.approx(66.67)

    # Kayıt bulunmayan aşamalar sıfır oran yerine null döner.
    for stage_type, item in stages.items():
        if stage_type != "REFLOW_SOLDERING":
            assert item["total_count"] == 0
            assert item["issue_rate"] is None