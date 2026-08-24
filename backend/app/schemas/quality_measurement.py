from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


METRIC_CODE_PATTERN = r"^[A-Z][A-Z0-9_]*$"
UNIT_PATTERN = r"^[A-Z][A-Z0-9_]*$"


class QualityMeasurementCreate(BaseModel):
    process_event_id: UUID

    metric_code: str = Field(
        min_length=2,
        max_length=80,
        pattern=METRIC_CODE_PATTERN,
        examples=["PEAK_TEMPERATURE"],
    )

    value: float = Field(
        allow_inf_nan=False,
        examples=[245.5],
    )

    unit: str = Field(
        min_length=1,
        max_length=30,
        pattern=UNIT_PATTERN,
        examples=["CELSIUS"],
    )

    lower_spec_limit: float | None = Field(
        default=None,
        allow_inf_nan=False,
    )

    upper_spec_limit: float | None = Field(
        default=None,
        allow_inf_nan=False,
    )

    measured_at: datetime | None = None

    @field_validator("measured_at")
    @classmethod
    def measured_at_must_have_timezone(
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
                "measured_at must include timezone information"
            )

        return value

    @model_validator(mode="after")
    def validate_spec_limits(
        self,
    ) -> "QualityMeasurementCreate":
        if (
            self.lower_spec_limit is not None
            and self.upper_spec_limit is not None
            and self.lower_spec_limit > self.upper_spec_limit
        ):
            raise ValueError(
                "lower_spec_limit cannot be greater "
                "than upper_spec_limit"
            )

        return self


class QualityMeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    process_event_id: UUID
    metric_code: str
    value: float
    unit: str
    lower_spec_limit: float | None
    upper_spec_limit: float | None
    is_within_spec: bool | None
    measured_at: datetime
    created_at: datetime