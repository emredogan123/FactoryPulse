from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.machine import MachineStatus, StageType


class MachineCreate(BaseModel):
    machine_code: str = Field(
        min_length=2,
        max_length=50,
        pattern=r"^[A-Z0-9-]+$",
        examples=["REFLOW-01"],
    )

    name: str = Field(
        min_length=2,
        max_length=100,
        examples=["Reflow Oven 1"],
    )

    stage_type: StageType
    status: MachineStatus = MachineStatus.ACTIVE
    commissioned_at: datetime | None = None


class MachineResponse(BaseModel):
    id: UUID
    machine_code: str
    name: str
    stage_type: StageType
    status: MachineStatus
    commissioned_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)