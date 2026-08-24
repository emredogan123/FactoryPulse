import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.machine import Machine
from app.models.pcb_unit import PCBUnit
from app.models.process_event import ProcessEvent
from app.models.production_order import ProductionOrder
from app.models.quality_measurement import QualityMeasurement
from app.simulation.config import SimulationConfig
from app.simulation.seeder import (
    DemoDataAlreadyExistsError,
    seed_demo_data,
)


def create_test_config() -> SimulationConfig:
    return SimulationConfig(
        data_prefix="TEST-SEED",
        random_seed=42,
        order_count=1,
        pcb_per_order=4,
        anomaly_probability=0.0,
    )


def test_seed_demo_data_creates_expected_records(
    database_session: Session,
) -> None:
    config = create_test_config()

    summary = seed_demo_data(
        database_session,
        config,
    )

    assert summary.machine_count == 5
    assert summary.production_order_count == 1
    assert summary.pcb_count == 4
    assert summary.process_event_count == 20
    assert summary.measurement_count == 40
    assert summary.passed_pcb_count == 4
    assert summary.failed_pcb_count == 0
    assert summary.rework_pcb_count == 0

    machine_count = database_session.scalar(
        select(func.count())
        .select_from(Machine)
        .where(
            Machine.machine_code.like(
                "TEST-SEED-%"
            )
        )
    )

    pcb_count = database_session.scalar(
        select(func.count())
        .select_from(PCBUnit)
        .where(
            PCBUnit.serial_number.like(
                "TEST-SEED-%"
            )
        )
    )

    event_count = database_session.scalar(
        select(func.count())
        .select_from(ProcessEvent)
        .join(PCBUnit)
        .where(
            PCBUnit.serial_number.like(
                "TEST-SEED-%"
            )
        )
    )

    measurement_count = database_session.scalar(
        select(func.count())
        .select_from(QualityMeasurement)
        .join(ProcessEvent)
        .join(PCBUnit)
        .where(
            PCBUnit.serial_number.like(
                "TEST-SEED-%"
            )
        )
    )

    assert machine_count == 5
    assert pcb_count == 4
    assert event_count == 20
    assert measurement_count == 40


def test_seed_rejects_existing_prefix(
    database_session: Session,
) -> None:
    config = create_test_config()

    seed_demo_data(
        database_session,
        config,
    )

    with pytest.raises(DemoDataAlreadyExistsError):
        seed_demo_data(
            database_session,
            config,
        )