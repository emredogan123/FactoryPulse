from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.machine import Machine
from app.repositories import machine as machine_repository
from app.schemas.machine import MachineCreate


class MachineNotFoundError(Exception):
    pass


class MachineCodeAlreadyExistsError(Exception):
    pass


def create_machine(
    database_session: Session,
    machine_data: MachineCreate,
) -> Machine:
    existing_machine = machine_repository.get_machine_by_code(
        database_session,
        machine_data.machine_code,
    )

    if existing_machine is not None:
        raise MachineCodeAlreadyExistsError(
            f"Machine code '{machine_data.machine_code}' already exists."
        )

    try:
        return machine_repository.create_machine(
            database_session,
            machine_data,
        )
    except IntegrityError as error:
        database_session.rollback()

        raise MachineCodeAlreadyExistsError(
            f"Machine code '{machine_data.machine_code}' already exists."
        ) from error


def list_machines(
    database_session: Session,
) -> list[Machine]:
    return machine_repository.list_machines(database_session)


def get_machine(
    database_session: Session,
    machine_id: UUID,
) -> Machine:
    machine = machine_repository.get_machine_by_id(
        database_session,
        machine_id,
    )

    if machine is None:
        raise MachineNotFoundError(
            f"Machine '{machine_id}' was not found."
        )

    return machine