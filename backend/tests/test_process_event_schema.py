from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.process_event import ProcessEventResult
from app.schemas.process_event import ProcessEventCreate


def utc_datetime(hour: int) -> datetime:
    return datetime(
        2026,
        8,
        24,
        hour,
        0,
        tzinfo=timezone.utc,
    )


def test_valid_pending_process_event() -> None:
    schema = ProcessEventCreate(
        pcb_unit_id=uuid4(),
        machine_id=uuid4(),
        process_parameters={
            "temperature_c": 245.5,
            "conveyor_speed_m_min": 0.9,
        },
    )

    assert schema.result == ProcessEventResult.PENDING
    assert schema.completed_at is None


def test_valid_completed_process_event() -> None:
    schema = ProcessEventCreate(
        pcb_unit_id=uuid4(),
        machine_id=uuid4(),
        result=ProcessEventResult.PASSED,
        started_at=utc_datetime(8),
        completed_at=utc_datetime(9),
    )

    assert schema.result == ProcessEventResult.PASSED


def test_completed_at_must_be_after_started_at() -> None:
    with pytest.raises(ValidationError):
        ProcessEventCreate(
            pcb_unit_id=uuid4(),
            machine_id=uuid4(),
            result=ProcessEventResult.FAILED,
            started_at=utc_datetime(10),
            completed_at=utc_datetime(9),
        )


def test_completed_event_requires_completed_at() -> None:
    with pytest.raises(ValidationError):
        ProcessEventCreate(
            pcb_unit_id=uuid4(),
            machine_id=uuid4(),
            result=ProcessEventResult.PASSED,
            started_at=utc_datetime(8),
        )


def test_pending_event_cannot_have_completed_at() -> None:
    with pytest.raises(ValidationError):
        ProcessEventCreate(
            pcb_unit_id=uuid4(),
            machine_id=uuid4(),
            result=ProcessEventResult.PENDING,
            completed_at=utc_datetime(9),
        )


def test_datetime_without_timezone_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProcessEventCreate(
            pcb_unit_id=uuid4(),
            machine_id=uuid4(),
            started_at=datetime(
                2026,
                8,
                24,
                8,
                0,
            ),
        )