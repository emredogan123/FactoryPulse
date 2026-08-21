from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.production_order import ProductionOrder
from app.schemas.production_order import ProductionOrderCreate


def get_production_order_by_id(
    db: Session,
    production_order_id: UUID,
) -> ProductionOrder | None:
    return db.get(ProductionOrder, production_order_id)


def get_production_order_by_code(
    db: Session,
    order_code: str,
) -> ProductionOrder | None:
    statement = select(ProductionOrder).where(
        ProductionOrder.order_code == order_code
    )

    return db.scalar(statement)


def list_production_orders(
    db: Session,
) -> list[ProductionOrder]:
    statement = select(ProductionOrder).order_by(
        ProductionOrder.created_at.desc()
    )

    return list(db.scalars(statement).all())


def create_production_order(
    db: Session,
    data: ProductionOrderCreate,
) -> ProductionOrder:
    production_order = ProductionOrder(
        **data.model_dump()
    )

    db.add(production_order)
    db.commit()
    db.refresh(production_order)

    return production_order