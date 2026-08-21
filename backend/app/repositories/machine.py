from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.machine import Machine
from app.schemas.machine import MachineCreate


def get_machine_by_id(
    database_session: Session,
    machine_id: UUID,
) -> Machine | None:
    return database_session.get(Machine, machine_id)


def get_machine_by_code(
    database_session: Session,
    machine_code: str,
) -> Machine | None:
    statement = select(Machine).where(
        Machine.machine_code == machine_code
    )

    return database_session.scalar(statement)


def list_machines(
    database_session: Session,
) -> list[Machine]:
    statement = select(Machine).order_by(Machine.machine_code)

    machines = database_session.scalars(statement).all()

    return list(machines)


def create_machine(
    database_session: Session,
    machine_data: MachineCreate,
) -> Machine:
    machine = Machine(**machine_data.model_dump())

    database_session.add(machine)
    database_session.commit()
    database_session.refresh(machine)

    return machine