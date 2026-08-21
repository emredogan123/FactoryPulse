from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.production_order import (
    ProductionOrderCreate,
    ProductionOrderResponse,
)
from app.services.production_order import (
    ProductionOrderCodeAlreadyExistsError,
    ProductionOrderNotFoundError,
    create_production_order,
    get_production_order,
    get_production_orders,
)


router = APIRouter(
    prefix="/api/v1/production-orders",
    tags=["Production Orders"],
)


@router.post(
    "",
    response_model=ProductionOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_production_order_endpoint(
    data: ProductionOrderCreate,
    db: Session = Depends(get_db),
) -> ProductionOrderResponse:
    try:
        return create_production_order(db, data)
    except ProductionOrderCodeAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=list[ProductionOrderResponse],
)
def list_production_orders_endpoint(
    db: Session = Depends(get_db),
) -> list[ProductionOrderResponse]:
    return get_production_orders(db)


@router.get(
    "/{production_order_id}",
    response_model=ProductionOrderResponse,
)
def get_production_order_endpoint(
    production_order_id: UUID,
    db: Session = Depends(get_db),
) -> ProductionOrderResponse:
    try:
        return get_production_order(
            db,
            production_order_id,
        )
    except ProductionOrderNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error