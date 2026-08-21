from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.pcb_unit import PCBUnitStatus


SERIAL_NUMBER_PATTERN = r"^[A-Z0-9]+(?:-[A-Z0-9]+)*$"


class PCBUnitCreate(BaseModel):
    serial_number: str = Field(
        min_length=3,
        max_length=100,
        pattern=SERIAL_NUMBER_PATTERN,
        examples=["PCB-2026-000001"],
    )

    production_order_id: UUID


class PCBUnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    serial_number: str
    production_order_id: UUID
    status: PCBUnitStatus
    created_at: datetime
    updated_at: datetime