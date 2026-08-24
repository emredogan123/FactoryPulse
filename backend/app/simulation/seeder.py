from dataclasses import dataclass
from datetime import datetime, timedelta
from random import Random

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.machine import (
    Machine,
    MachineStatus,
    StageType,
)
from app.models.pcb_unit import PCBUnit, PCBUnitStatus
from app.models.process_event import (
    ProcessEvent,
    ProcessEventResult,
)
from app.models.production_order import (
    ProductionOrder,
    ProductionOrderStatus,
)
from app.models.quality_measurement import QualityMeasurement
from app.simulation.config import SimulationConfig
from app.simulation.generator import (
    generate_stage_observation,
)
from app.simulation.profiles import STAGE_ORDER


@dataclass(frozen=True)
class SeedSummary:
    machine_count: int
    production_order_count: int
    pcb_count: int
    process_event_count: int
    measurement_count: int
    passed_pcb_count: int
    failed_pcb_count: int
    rework_pcb_count: int


class DemoDataAlreadyExistsError(Exception):
    pass


MACHINE_NAMES: dict[StageType, str] = {
    StageType.SOLDER_PASTE_PRINTING: (
        "Demo Solder Paste Printer"
    ),
    StageType.COMPONENT_PLACEMENT: (
        "Demo Pick and Place Machine"
    ),
    StageType.REFLOW_SOLDERING: (
        "Demo Reflow Oven"
    ),
    StageType.AOI_INSPECTION: (
        "Demo AOI Inspection Machine"
    ),
    StageType.FUNCTIONAL_TESTING: (
        "Demo Functional Test Station"
    ),
}


def demo_data_exists(
    db: Session,
    prefix: str,
) -> bool:
    statement = (
        select(ProductionOrder.id)
        .where(
            ProductionOrder.order_code.like(
                f"{prefix}-%"
            )
        )
        .limit(1)
    )

    return db.scalar(statement) is not None


def create_demo_machines(
    db: Session,
    config: SimulationConfig,
) -> dict[StageType, Machine]:
    machines: dict[StageType, Machine] = {}

    for index, stage_type in enumerate(
        STAGE_ORDER,
        start=1,
    ):
        machine = Machine(
            machine_code=(
                f"{config.data_prefix}-MACHINE-{index:02d}"
            ),
            name=MACHINE_NAMES[stage_type],
            stage_type=stage_type,
            status=MachineStatus.ACTIVE,
            commissioned_at=(
                config.simulation_start
                - timedelta(days=365)
            ),
        )

        db.add(machine)
        machines[stage_type] = machine

    db.flush()

    return machines


def create_process_event(
    db: Session,
    pcb_unit: PCBUnit,
    machine: Machine,
    stage_type: StageType,
    started_at: datetime,
    is_anomalous: bool,
    anomaly_result: ProcessEventResult,
    random_generator: Random,
) -> tuple[ProcessEvent, int]:
    observation = generate_stage_observation(
        random_generator,
        stage_type,
        is_anomalous=is_anomalous,
    )

    completed_at = started_at + timedelta(minutes=5)

    if is_anomalous:
        result = anomaly_result
    else:
        result = ProcessEventResult.PASSED

    process_parameters: dict[str, object] = {
        **observation.process_parameters,
        "drift_score": observation.drift_score,
        "is_simulated": True,
    }

    event = ProcessEvent(
        pcb_unit_id=pcb_unit.id,
        machine_id=machine.id,
        result=result,
        process_parameters=process_parameters,
        notes="Synthetic FactoryPulse demo event",
        started_at=started_at,
        completed_at=completed_at,
        created_at=completed_at,
        updated_at=completed_at,
    )

    db.add(event)
    db.flush()

    for generated_measurement in observation.measurements:
        measurement = QualityMeasurement(
            process_event_id=event.id,
            metric_code=(
                generated_measurement.metric_code
            ),
            value=generated_measurement.value,
            unit=generated_measurement.unit,
            lower_spec_limit=(
                generated_measurement.lower_spec_limit
            ),
            upper_spec_limit=(
                generated_measurement.upper_spec_limit
            ),
            is_within_spec=(
                generated_measurement.is_within_spec
            ),
            measured_at=completed_at,
            created_at=completed_at,
        )

        db.add(measurement)

    return event, len(observation.measurements)


def seed_demo_data(
    db: Session,
    config: SimulationConfig,
) -> SeedSummary:
    if demo_data_exists(db, config.data_prefix):
        raise DemoDataAlreadyExistsError(
            f"Data with prefix '{config.data_prefix}' "
            "already exists"
        )

    random_generator = Random(config.random_seed)

    machines = create_demo_machines(
        db,
        config,
    )

    pcb_count = 0
    process_event_count = 0
    measurement_count = 0
    passed_pcb_count = 0
    failed_pcb_count = 0
    rework_pcb_count = 0

    global_pcb_number = 1

    for order_number in range(
        1,
        config.order_count + 1,
    ):
        order_start = (
            config.simulation_start
            + timedelta(days=order_number - 1)
        )

        production_order = ProductionOrder(
            order_code=(
                f"{config.data_prefix}-ORDER-"
                f"{order_number:03d}"
            ),
            product_code=(
                f"{config.data_prefix}-PCB-V1"
            ),
            target_quantity=config.pcb_per_order,
            status=ProductionOrderStatus.COMPLETED,
            planned_start_at=order_start,
            planned_end_at=(
                order_start + timedelta(hours=10)
            ),
            actual_start_at=order_start,
            actual_end_at=(
                order_start + timedelta(hours=9)
            ),
        )

        db.add(production_order)
        db.flush()

        for pcb_index in range(
            config.pcb_per_order
        ):
            pcb_started_at = (
                order_start
                + timedelta(minutes=pcb_index * 7)
            )

            pcb_unit = PCBUnit(
                serial_number=(
                    f"{config.data_prefix}-PCB-"
                    f"{global_pcb_number:06d}"
                ),
                production_order_id=production_order.id,
                status=PCBUnitStatus.QUEUED,
            )

            db.add(pcb_unit)
            db.flush()

            pcb_is_anomalous = (
                random_generator.random()
                < config.anomaly_probability
            )

            anomaly_stage = (
                random_generator.choice(STAGE_ORDER)
                if pcb_is_anomalous
                else None
            )

            anomaly_result = (
                ProcessEventResult.WARNING
                if random_generator.random()
                < config.warning_probability
                else ProcessEventResult.FAILED
            )

            for stage_index, stage_type in enumerate(
                STAGE_ORDER
            ):
                event_started_at = (
                    pcb_started_at
                    + timedelta(
                        minutes=(
                            stage_index
                            * config.stage_duration_minutes
                        )
                    )
                )

                is_anomalous_stage = (
                    stage_type == anomaly_stage
                )

                _, generated_measurement_count = (
                    create_process_event(
                        db=db,
                        pcb_unit=pcb_unit,
                        machine=machines[stage_type],
                        stage_type=stage_type,
                        started_at=event_started_at,
                        is_anomalous=is_anomalous_stage,
                        anomaly_result=anomaly_result,
                        random_generator=random_generator,
                    )
                )

                process_event_count += 1
                measurement_count += (
                    generated_measurement_count
                )

                if (
                    is_anomalous_stage
                    and anomaly_result
                    == ProcessEventResult.FAILED
                ):
                    break

            if not pcb_is_anomalous:
                pcb_unit.status = PCBUnitStatus.PASSED
                passed_pcb_count += 1
            elif (
                anomaly_result
                == ProcessEventResult.WARNING
            ):
                pcb_unit.status = PCBUnitStatus.REWORK
                rework_pcb_count += 1
            else:
                pcb_unit.status = PCBUnitStatus.FAILED
                failed_pcb_count += 1

            pcb_count += 1
            global_pcb_number += 1

    db.flush()

    return SeedSummary(
        machine_count=len(machines),
        production_order_count=config.order_count,
        pcb_count=pcb_count,
        process_event_count=process_event_count,
        measurement_count=measurement_count,
        passed_pcb_count=passed_pcb_count,
        failed_pcb_count=failed_pcb_count,
        rework_pcb_count=rework_pcb_count,
    )