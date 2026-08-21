from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.production_order import ProductionOrderStatus


CODE_PATTERN = r"^[A-Z0-9]+(?:-[A-Z0-9]+)*$"


class ProductionOrderCreate(BaseModel):
    order_code: str = Field(
        min_length=3,
        max_length=50,
        pattern=CODE_PATTERN,
        examples=["PO-2026-0001"],
    )

    product_code: str = Field(
        min_length=2,
        max_length=50,
        pattern=CODE_PATTERN,
        examples=["PCB-CONTROLLER-V1"],
    )

    target_quantity: int = Field(
        gt=0,
        le=1_000_000,
        examples=[1000],
    )

    planned_start_at: datetime | None = None
    planned_end_at: datetime | None = None

    @model_validator(mode="after")
    def validate_planned_period(
        self,
    ) -> "ProductionOrderCreate":
        if (
            self.planned_start_at is not None
            and self.planned_end_at is not None
            and self.planned_end_at <= self.planned_start_at
        ):
            raise ValueError(
                "planned_end_at must be later than planned_start_at"
            )

        return self


class ProductionOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_code: str
    product_code: str
    target_quantity: int
    status: ProductionOrderStatus

    planned_start_at: datetime | None
    planned_end_at: datetime | None
    actual_start_at: datetime | None
    actual_end_at: datetime | None

    created_at: datetime
    updated_at: datetime