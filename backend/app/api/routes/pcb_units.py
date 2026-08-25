from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.auth.permissions import (
    AdminUser,
    QualityUser,
)
from app.db.session import get_db
from app.schemas.pcb_unit import (
    PCBUnitCreate,
    PCBUnitResponse,
)
from app.services.pcb_unit import (
    PCBSerialNumberAlreadyExistsError,
    PCBUnitNotFoundError,
    MaterialLotNotFoundError,
    create_pcb_unit,
    get_pcb_unit,
    get_pcb_units,
)
from app.services.production_order import (
    ProductionOrderNotFoundError,
)


router = APIRouter(
    prefix="/pcb-units",
    tags=["PCB Units"],
)


DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


@router.post(
    "",
    response_model=PCBUnitResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_pcb_unit_endpoint(
    data: PCBUnitCreate,
    db: DatabaseSession,
    current_user: AdminUser,
) -> PCBUnitResponse:
    try:
        return create_pcb_unit(
            db,
            data,
        )
    except PCBSerialNumberAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except (
        ProductionOrderNotFoundError,
        MaterialLotNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=list[PCBUnitResponse],
)
def list_pcb_units_endpoint(
    db: DatabaseSession,
    current_user: QualityUser,
    production_order_id: UUID | None = None,
) -> list[PCBUnitResponse]:
    try:
        return get_pcb_units(
            db,
            production_order_id,
        )
    except ProductionOrderNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.get(
    "/{pcb_unit_id}",
    response_model=PCBUnitResponse,
)
def get_pcb_unit_endpoint(
    pcb_unit_id: UUID,
    db: DatabaseSession,
    current_user: QualityUser,
) -> PCBUnitResponse:
    try:
        return get_pcb_unit(
            db,
            pcb_unit_id,
        )
    except PCBUnitNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error