from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.process_event import ProcessEventResult


ProcessParameterValue = int | float | str | bool | None


class ProcessEventCreate(BaseModel):
    pcb_unit_id: UUID
    machine_id: UUID

    result: ProcessEventResult = ProcessEventResult.PENDING

    process_parameters: dict[
        str,
        ProcessParameterValue,
    ] = Field(default_factory=dict)

    notes: str | None = Field(
        default=None,
        max_length=500,
    )

    started_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator(
        "started_at",
        "completed_at",
    )
    @classmethod
    def datetime_must_have_timezone(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if (
            value is not None
            and (
                value.tzinfo is None
                or value.utcoffset() is None
            )
        ):
            raise ValueError(
                "datetime values must include timezone information"
            )

        return value

    @model_validator(mode="after")
    def validate_event_state(
        self,
    ) -> "ProcessEventCreate":
        if self.result == ProcessEventResult.PENDING:
            if self.completed_at is not None:
                raise ValueError(
                    "a pending event cannot have completed_at"
                )

            return self

        if self.started_at is None:
            raise ValueError(
                "started_at is required for a completed event"
            )

        if self.completed_at is None:
            raise ValueError(
                "completed_at is required for a completed event"
            )

        if self.completed_at <= self.started_at:
            raise ValueError(
                "completed_at must be later than started_at"
            )

        return self


class ProcessEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pcb_unit_id: UUID
    machine_id: UUID
    result: ProcessEventResult
    process_parameters: dict[
        str,
        ProcessParameterValue,
    ]
    notes: str | None
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime