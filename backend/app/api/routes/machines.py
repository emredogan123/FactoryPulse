from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.machine import MachineCreate, MachineResponse
from app.services import machine as machine_service
from app.services.machine import (
    MachineCodeAlreadyExistsError,
    MachineNotFoundError,
)


router = APIRouter(
    prefix="/api/v1/machines",
    tags=["Machines"],
)


DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=MachineResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_machine(
    machine_data: MachineCreate,
    database_session: DatabaseSession,
) -> MachineResponse:
    try:
        return machine_service.create_machine(
            database_session,
            machine_data,
        )
    except MachineCodeAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=list[MachineResponse],
)
def list_machines(
    database_session: DatabaseSession,
) -> list[MachineResponse]:
    return machine_service.list_machines(database_session)


@router.get(
    "/{machine_id}",
    response_model=MachineResponse,
)
def get_machine(
    machine_id: UUID,
    database_session: DatabaseSession,
) -> MachineResponse:
    try:
        return machine_service.get_machine(
            database_session,
            machine_id,
        )
    except MachineNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error