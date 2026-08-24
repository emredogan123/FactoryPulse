from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.process_event import (
    ProcessEventCreate,
    ProcessEventResponse,
)
from app.services.machine import MachineNotFoundError
from app.services.pcb_unit import PCBUnitNotFoundError
from app.services.process_event import (
    MachineNotActiveError,
    PCBUnitNotProcessableError,
    ProcessEventNotFoundError,
    create_process_event,
    get_process_event,
    get_process_events,
)


router = APIRouter(
    prefix="/api/v1/process-events",
    tags=["Process Events"],
)


@router.post(
    "",
    response_model=ProcessEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_process_event_endpoint(
    data: ProcessEventCreate,
    db: Session = Depends(get_db),
) -> ProcessEventResponse:
    try:
        return create_process_event(db, data)
    except (
        PCBUnitNotFoundError,
        MachineNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except (
        MachineNotActiveError,
        PCBUnitNotProcessableError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=list[ProcessEventResponse],
)
def list_process_events_endpoint(
    pcb_unit_id: UUID | None = None,
    machine_id: UUID | None = None,
    db: Session = Depends(get_db),
) -> list[ProcessEventResponse]:
    try:
        return get_process_events(
            db,
            pcb_unit_id,
            machine_id,
        )
    except (
        PCBUnitNotFoundError,
        MachineNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.get(
    "/{process_event_id}",
    response_model=ProcessEventResponse,
)
def get_process_event_endpoint(
    process_event_id: UUID,
    db: Session = Depends(get_db),
) -> ProcessEventResponse:
    try:
        return get_process_event(
            db,
            process_event_id,
        )
    except ProcessEventNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error