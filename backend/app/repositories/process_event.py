from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.process_event import ProcessEvent
from app.schemas.process_event import ProcessEventCreate


def get_process_event_by_id(
    db: Session,
    process_event_id: UUID,
) -> ProcessEvent | None:
    return db.get(ProcessEvent, process_event_id)


def list_process_events(
    db: Session,
    pcb_unit_id: UUID | None = None,
    machine_id: UUID | None = None,
) -> list[ProcessEvent]:
    statement = select(ProcessEvent)

    if pcb_unit_id is not None:
        statement = statement.where(
            ProcessEvent.pcb_unit_id == pcb_unit_id
        )

    if machine_id is not None:
        statement = statement.where(
            ProcessEvent.machine_id == machine_id
        )

    statement = statement.order_by(
        ProcessEvent.started_at.desc()
    )

    return list(db.scalars(statement).all())


def create_process_event(
    db: Session,
    data: ProcessEventCreate,
) -> ProcessEvent:
    process_event = ProcessEvent(
        **data.model_dump(exclude_none=True)
    )

    db.add(process_event)
    db.flush()

    return process_event