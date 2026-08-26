import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.machine import Machine
from app.models.pcb_unit import PCBUnit,ShiftType
from app.models.process_event import ProcessEvent
from app.models.production_order import ProductionOrder
from app.models.quality_measurement import QualityMeasurement
from app.simulation.config import SimulationConfig
from app.models.material_lot import MaterialLot
from app.simulation.seeder import (
    DemoDataAlreadyExistsError,
    calculate_degradation_score,
    calculate_pcb_anomaly_probability,
    seed_demo_data,
)

def create_test_config() -> SimulationConfig:
    return SimulationConfig(
        data_prefix="TEST-SEED",
        random_seed=42,
        order_count=1,
        pcb_per_order=4,
        anomaly_probability=0.0,
        night_shift_probability=0.0,
        problematic_lot_probability=0.0,
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
    assert summary.material_lot_count == 4
    assert summary.day_shift_pcb_count == 4
    assert summary.night_shift_pcb_count == 0
    assert summary.problematic_lot_pcb_count == 0

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

def test_anomaly_probability_reflects_shift_and_lot() -> None:
    config = SimulationConfig(
        anomaly_probability=0.12,
    )

    normal_day = calculate_pcb_anomaly_probability(
        config,
        ShiftType.DAY,
        uses_problematic_lot=False,
    )
    normal_night = calculate_pcb_anomaly_probability(
        config,
        ShiftType.NIGHT,
        uses_problematic_lot=False,
    )
    problematic_day = (
        calculate_pcb_anomaly_probability(
            config,
            ShiftType.DAY,
            uses_problematic_lot=True,
        )
    )
    problematic_night = (
        calculate_pcb_anomaly_probability(
            config,
            ShiftType.NIGHT,
            uses_problematic_lot=True,
        )
    )

    assert normal_day == pytest.approx(0.12)
    assert normal_night == pytest.approx(0.16)
    assert problematic_day == pytest.approx(0.30)
    assert problematic_night == pytest.approx(0.34)

    assert normal_day < normal_night
    assert normal_day < problematic_day
    assert problematic_day < problematic_night

def test_seed_assigns_shift_and_material_lot(
    database_session: Session,
) -> None:
    config = SimulationConfig(
        data_prefix="TEST-DISTRIBUTION",
        random_seed=42,
        order_count=1,
        pcb_per_order=8,
        anomaly_probability=0.0,
        night_shift_probability=1.0,
        problematic_lot_probability=1.0,
    )

    summary = seed_demo_data(
        database_session,
        config,
    )

    assert summary.material_lot_count == 4
    assert summary.pcb_count == 8
    assert summary.day_shift_pcb_count == 0
    assert summary.night_shift_pcb_count == 8
    assert summary.problematic_lot_pcb_count == 8

    assigned_pcb_count = database_session.scalar(
        select(func.count())
        .select_from(PCBUnit)
        .join(MaterialLot)
        .where(
            PCBUnit.serial_number.like(
                "TEST-DISTRIBUTION-%"
            ),
            PCBUnit.shift == ShiftType.NIGHT,
            MaterialLot.lot_code
            == "TEST-DISTRIBUTION-LP-302",
        )
    )

    assert assigned_pcb_count == 8

def test_degradation_increases_after_threshold() -> None:
    initial_score = calculate_degradation_score(
        pcb_number=1,
        total_pcb_count=100,
        degradation_start_ratio=0.60,
    )

    threshold_score = calculate_degradation_score(
        pcb_number=60,
        total_pcb_count=100,
        degradation_start_ratio=0.60,
    )

    final_score = calculate_degradation_score(
        pcb_number=100,
        total_pcb_count=100,
        degradation_start_ratio=0.60,
    )

    assert initial_score == 0.0
    assert threshold_score == 0.0
    assert final_score == 1.0


def test_degradation_increases_anomaly_probability() -> None:
    config = SimulationConfig(
        anomaly_probability=0.12,
        degradation_anomaly_increase=0.16,
    )

    healthy_probability = (
        calculate_pcb_anomaly_probability(
            config=config,
            shift=ShiftType.DAY,
            uses_problematic_lot=False,
            degradation_score=0.0,
        )
    )

    degraded_probability = (
        calculate_pcb_anomaly_probability(
            config=config,
            shift=ShiftType.DAY,
            uses_problematic_lot=False,
            degradation_score=1.0,
        )
    )

    assert healthy_probability == pytest.approx(0.12)
    assert degraded_probability == pytest.approx(0.28)
    assert degraded_probability > healthy_probability