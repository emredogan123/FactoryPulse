import pytest
from pydantic import ValidationError

from app.models.machine import MachineStatus, StageType
from app.schemas.machine import MachineCreate


def test_machine_create_with_valid_data() -> None:
    machine = MachineCreate(
        machine_code="REFLOW-01",
        name="Reflow Oven 1",
        stage_type=StageType.REFLOW_SOLDERING,
    )

    assert machine.machine_code == "REFLOW-01"
    assert machine.name == "Reflow Oven 1"
    assert machine.stage_type == StageType.REFLOW_SOLDERING
    assert machine.status == MachineStatus.ACTIVE


def test_machine_create_rejects_invalid_code() -> None:
    with pytest.raises(ValidationError):
        MachineCreate(
            machine_code="reflow 01",
            name="Reflow Oven 1",
            stage_type=StageType.REFLOW_SOLDERING,
        )