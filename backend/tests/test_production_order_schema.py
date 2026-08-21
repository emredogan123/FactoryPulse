from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.production_order import ProductionOrderCreate


def test_valid_production_order_data() -> None:
    schema = ProductionOrderCreate(
        order_code="PO-2026-0001",
        product_code="PCB-CONTROLLER-V1",
        target_quantity=1000,
        planned_start_at=datetime(
            2026,
            8,
            22,
            8,
            0,
            tzinfo=timezone.utc,
        ),
        planned_end_at=datetime(
            2026,
            8,
            22,
            18,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert schema.order_code == "PO-2026-0001"
    assert schema.target_quantity == 1000


def test_invalid_order_code_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProductionOrderCreate(
            order_code="invalid order",
            product_code="PCB-CONTROLLER-V1",
            target_quantity=100,
        )


def test_non_positive_target_quantity_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProductionOrderCreate(
            order_code="PO-2026-0002",
            product_code="PCB-CONTROLLER-V1",
            target_quantity=0,
        )


def test_planned_end_must_be_after_start() -> None:
    with pytest.raises(ValidationError):
        ProductionOrderCreate(
            order_code="PO-2026-0003",
            product_code="PCB-CONTROLLER-V1",
            target_quantity=100,
            planned_start_at=datetime(
                2026,
                8,
                22,
                18,
                0,
                tzinfo=timezone.utc,
            ),
            planned_end_at=datetime(
                2026,
                8,
                22,
                8,
                0,
                tzinfo=timezone.utc,
            ),
        )