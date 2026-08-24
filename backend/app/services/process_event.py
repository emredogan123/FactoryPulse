from uuid import UUID

from sqlalchemy.orm import Session

from app.models.machine import (
    MachineStatus,
    StageType,
)
from app.models.pcb_unit import PCBUnitStatus
from app.models.process_event import (
    ProcessEvent,
    ProcessEventResult,
)
from app.repositories.machine import get_machine_by_id
from app.repositories.pcb_unit import get_pcb_unit_by_id
from app.repositories.process_event import (
    create_process_event as repository_create,
)
from app.repositories.process_event import (
    get_process_event_by_id,
    list_process_events,
)
from app.schemas.process_event import ProcessEventCreate
from app.services.machine import MachineNotFoundError
from app.services.pcb_unit import PCBUnitNotFoundError


class ProcessEventNotFoundError(Exception):
    pass


class MachineNotActiveError(Exception):
    pass


class PCBUnitNotProcessableError(Exception):
    pass


def update_pcb_status(
    pcb_status: PCBUnitStatus,
    event_result: ProcessEventResult,
    machine_stage: StageType,
) -> PCBUnitStatus:
    if event_result == ProcessEventResult.FAILED:
        return PCBUnitStatus.FAILED

    if event_result == ProcessEventResult.WARNING:
        return PCBUnitStatus.REWORK

    if (
        event_result == ProcessEventResult.PASSED
        and machine_stage == StageType.FUNCTIONAL_TESTING
    ):
        return PCBUnitStatus.PASSED

    if event_result in {
        ProcessEventResult.PENDING,
        ProcessEventResult.PASSED,
    }:
        return PCBUnitStatus.IN_PRODUCTION

    return pcb_status


def create_process_event(
    db: Session,
    data: ProcessEventCreate,
) -> ProcessEvent:
    pcb_unit = get_pcb_unit_by_id(
        db,
        data.pcb_unit_id,
    )

    if pcb_unit is None:
        raise PCBUnitNotFoundError(
            f"PCB unit '{data.pcb_unit_id}' was not found"
        )

    if pcb_unit.status in {
        PCBUnitStatus.PASSED,
        PCBUnitStatus.FAILED,
    }:
        raise PCBUnitNotProcessableError(
            f"PCB unit '{pcb_unit.serial_number}' cannot be processed "
            f"because its status is {pcb_unit.status.value}"
        )

    machine = get_machine_by_id(
        db,
        data.machine_id,
    )

    if machine is None:
        raise MachineNotFoundError(
            f"Machine '{data.machine_id}' was not found"
        )

    if machine.status != MachineStatus.ACTIVE:
        raise MachineNotActiveError(
            f"Machine '{machine.machine_code}' is not active"
        )

    try:
        process_event = repository_create(
            db,
            data,
        )

        pcb_unit.status = update_pcb_status(
            pcb_unit.status,
            process_event.result,
            machine.stage_type,
        )

        db.commit()
        db.refresh(process_event)

        return process_event
    except Exception:
        db.rollback()
        raise


def get_process_event(
    db: Session,
    process_event_id: UUID,
) -> ProcessEvent:
    process_event = get_process_event_by_id(
        db,
        process_event_id,
    )

    if process_event is None:
        raise ProcessEventNotFoundError(
            f"Process event '{process_event_id}' was not found"
        )

    return process_event


def get_process_events(
    db: Session,
    pcb_unit_id: UUID | None = None,
    machine_id: UUID | None = None,
) -> list[ProcessEvent]:
    if pcb_unit_id is not None:
        pcb_unit = get_pcb_unit_by_id(
            db,
            pcb_unit_id,
        )

        if pcb_unit is None:
            raise PCBUnitNotFoundError(
                f"PCB unit '{pcb_unit_id}' was not found"
            )

    if machine_id is not None:
        machine = get_machine_by_id(
            db,
            machine_id,
        )

        if machine is None:
            raise MachineNotFoundError(
                f"Machine '{machine_id}' was not found"
            )

    return list_process_events(
        db,
        pcb_unit_id,
        machine_id,
    )