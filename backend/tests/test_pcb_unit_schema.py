from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.pcb_unit import PCBUnitCreate


def test_valid_pcb_unit_data() -> None:
    production_order_id = uuid4()

    schema = PCBUnitCreate(
        serial_number="PCB-2026-000001",
        production_order_id=production_order_id,
    )

    assert schema.serial_number == "PCB-2026-000001"
    assert schema.production_order_id == production_order_id


def test_invalid_serial_number_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PCBUnitCreate(
            serial_number="invalid serial number",
            production_order_id=uuid4(),
        )


def test_invalid_production_order_id_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PCBUnitCreate.model_validate(
            {
                "serial_number": "PCB-2026-000002",
                "production_order_id": "not-a-valid-uuid",
            }
        )