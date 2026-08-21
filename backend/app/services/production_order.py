from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.production_order import ProductionOrder
from app.repositories.production_order import (
    create_production_order as repository_create,
)
from app.repositories.production_order import (
    get_production_order_by_code,
    get_production_order_by_id,
    list_production_orders,
)
from app.schemas.production_order import ProductionOrderCreate


class ProductionOrderNotFoundError(Exception):
    pass


class ProductionOrderCodeAlreadyExistsError(Exception):
    pass


def create_production_order(
    db: Session,
    data: ProductionOrderCreate,
) -> ProductionOrder:
    existing_order = get_production_order_by_code(
        db,
        data.order_code,
    )

    if existing_order is not None:
        raise ProductionOrderCodeAlreadyExistsError(
            f"Production order code '{data.order_code}' already exists"
        )

    try:
        return repository_create(db, data)
    except IntegrityError as error:
        db.rollback()

        raise ProductionOrderCodeAlreadyExistsError(
            f"Production order code '{data.order_code}' already exists"
        ) from error


def get_production_order(
    db: Session,
    production_order_id: UUID,
) -> ProductionOrder:
    production_order = get_production_order_by_id(
        db,
        production_order_id,
    )

    if production_order is None:
        raise ProductionOrderNotFoundError(
            f"Production order '{production_order_id}' was not found"
        )

    return production_order


def get_production_orders(
    db: Session,
) -> list[ProductionOrder]:
    return list_production_orders(db)