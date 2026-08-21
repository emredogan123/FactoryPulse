from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pcb_unit import PCBUnit
from app.schemas.pcb_unit import PCBUnitCreate


def get_pcb_unit_by_id(
    db: Session,
    pcb_unit_id: UUID,
) -> PCBUnit | None:
    return db.get(PCBUnit, pcb_unit_id)


def get_pcb_unit_by_serial_number(
    db: Session,
    serial_number: str,
) -> PCBUnit | None:
    statement = select(PCBUnit).where(
        PCBUnit.serial_number == serial_number
    )

    return db.scalar(statement)


def list_pcb_units(
    db: Session,
    production_order_id: UUID | None = None,
) -> list[PCBUnit]:
    statement = select(PCBUnit)

    if production_order_id is not None:
        statement = statement.where(
            PCBUnit.production_order_id == production_order_id
        )

    statement = statement.order_by(
        PCBUnit.created_at.desc()
    )

    return list(db.scalars(statement).all())


def create_pcb_unit(
    db: Session,
    data: PCBUnitCreate,
) -> PCBUnit:
    pcb_unit = PCBUnit(
        **data.model_dump()
    )

    db.add(pcb_unit)
    db.commit()
    db.refresh(pcb_unit)

    return pcb_unit