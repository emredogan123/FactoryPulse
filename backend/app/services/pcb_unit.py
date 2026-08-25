from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.pcb_unit import PCBUnit
from app.repositories.pcb_unit import (
    create_pcb_unit as repository_create,
)
from app.repositories.pcb_unit import (
    get_pcb_unit_by_id,
    get_pcb_unit_by_serial_number,
    list_pcb_units,
)
from app.repositories.production_order import (
    get_production_order_by_id,
)
from app.schemas.pcb_unit import PCBUnitCreate
from app.services.production_order import (
    ProductionOrderNotFoundError,
)
from app.repositories.material_lot import (
    get_material_lot_by_id,
)

class MaterialLotNotFoundError(Exception):
    pass

class PCBUnitNotFoundError(Exception):
    pass


class PCBSerialNumberAlreadyExistsError(Exception):
    pass


def create_pcb_unit(
    db: Session,
    data: PCBUnitCreate,
) -> PCBUnit:
    production_order = get_production_order_by_id(
        db,
        data.production_order_id,
    )

    if production_order is None:
        raise ProductionOrderNotFoundError(
            f"Production order '{data.production_order_id}' was not found"
        )

    existing_pcb = get_pcb_unit_by_serial_number(
        db,
        data.serial_number,
    )
    if data.material_lot_id is not None:
        material_lot = get_material_lot_by_id(
            db,
            data.material_lot_id,
        )

        if material_lot is None:
            raise MaterialLotNotFoundError(
                f"Material lot "
                f"'{data.material_lot_id}' "
                "was not found"
            )
    if existing_pcb is not None:
        raise PCBSerialNumberAlreadyExistsError(
            f"PCB serial number '{data.serial_number}' already exists"
        )

    try:
        return repository_create(db, data)
    except IntegrityError as error:
        db.rollback()

        existing_pcb = get_pcb_unit_by_serial_number(
            db,
            data.serial_number,
        )

        if existing_pcb is not None:
            raise PCBSerialNumberAlreadyExistsError(
                f"PCB serial number '{data.serial_number}' already exists"
            ) from error

        production_order = get_production_order_by_id(
            db,
            data.production_order_id,
        )

        if production_order is None:
            raise ProductionOrderNotFoundError(
                f"Production order '{data.production_order_id}' was not found"
            ) from error
        if data.material_lot_id is not None:
            material_lot = get_material_lot_by_id(
                db,
                data.material_lot_id,
            )

            if material_lot is None:
                raise MaterialLotNotFoundError(
                    f"Material lot "
                    f"'{data.material_lot_id}' "
                    "was not found"
                ) from error
        raise


def get_pcb_unit(
    db: Session,
    pcb_unit_id: UUID,
) -> PCBUnit:
    pcb_unit = get_pcb_unit_by_id(
        db,
        pcb_unit_id,
    )

    if pcb_unit is None:
        raise PCBUnitNotFoundError(
            f"PCB unit '{pcb_unit_id}' was not found"
        )

    return pcb_unit


def get_pcb_units(
    db: Session,
    production_order_id: UUID | None = None,
) -> list[PCBUnit]:
    if production_order_id is not None:
        production_order = get_production_order_by_id(
            db,
            production_order_id,
        )

        if production_order is None:
            raise ProductionOrderNotFoundError(
                f"Production order '{production_order_id}' was not found"
            )

    return list_pcb_units(
        db,
        production_order_id,
    )