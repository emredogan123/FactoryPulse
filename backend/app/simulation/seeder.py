from uuid import uuid4
from dataclasses import dataclass
from datetime import datetime, timedelta
from random import Random

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.models.machine import (
    Machine,
    MachineStatus,
    StageType,
)
from app.models.pcb_unit import (
    PCBUnit,
    PCBUnitStatus,
    ShiftType,
)
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
from app.models.material_lot import MaterialLot


@dataclass(frozen=True)
class SeedSummary:
    machine_count: int
    material_lot_count: int
    production_order_count: int
    pcb_count: int
    process_event_count: int
    measurement_count: int
    passed_pcb_count: int
    failed_pcb_count: int
    rework_pcb_count: int
    day_shift_pcb_count: int
    night_shift_pcb_count: int
    problematic_lot_pcb_count: int

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

NORMAL_MATERIAL_LOT_SUFFIXES: tuple[str, ...] = (
    "LP-101",
    "LP-205",
    "LP-410",
)

PROBLEMATIC_MATERIAL_LOT_SUFFIX = "LP-302"

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

def create_demo_material_lots(
    db: Session,
    config: SimulationConfig,
) -> dict[str, MaterialLot]:
    lot_suffixes = (
        *NORMAL_MATERIAL_LOT_SUFFIXES,
        PROBLEMATIC_MATERIAL_LOT_SUFFIX,
    )

    material_lots: dict[str, MaterialLot] = {}

    for index, lot_suffix in enumerate(
        lot_suffixes,
        start=1,
    ):
        material_lot = MaterialLot(
            lot_code=(
                f"{config.data_prefix}-{lot_suffix}"
            ),
            material_type="SOLDER_PASTE",
            supplier_code=(
                f"SUPPLIER-{((index - 1) % 2) + 1:02d}"
            ),
            received_at=(
                config.simulation_start
                - timedelta(days=index * 10)
            ),
        )

        db.add(material_lot)
        material_lots[lot_suffix] = material_lot

    db.flush()

    return material_lots

def choose_material_lot(
    random_generator: Random,
    material_lots: dict[str, MaterialLot],
    problematic_lot_probability: float,
) -> tuple[MaterialLot, bool]:
    uses_problematic_lot = (
        random_generator.random()
        < problematic_lot_probability
    )

    if uses_problematic_lot:
        selected_suffix = (
            PROBLEMATIC_MATERIAL_LOT_SUFFIX
        )
    else:
        selected_suffix = random_generator.choice(
            NORMAL_MATERIAL_LOT_SUFFIXES
        )

    return (
        material_lots[selected_suffix],
        uses_problematic_lot,
    )

def calculate_degradation_score(
    pcb_number: int,
    total_pcb_count: int,
    degradation_start_ratio: float,
) -> float:
    if total_pcb_count <= 1:
        return 0.0

    production_progress = (
        (pcb_number - 1)
        / (total_pcb_count - 1)
    )

    if production_progress <= degradation_start_ratio:
        return 0.0

    remaining_ratio = (
        1.0 - degradation_start_ratio
    )

    degradation_score = (
        production_progress
        - degradation_start_ratio
    ) / remaining_ratio

    return round(
        min(max(degradation_score, 0.0), 1.0),
        4,
    )

def calculate_pcb_anomaly_probability(
    config: SimulationConfig,
    shift: ShiftType,
    uses_problematic_lot: bool,
    degradation_score: float = 0.0,
) -> float:
    probability = config.anomaly_probability

    if uses_problematic_lot:
        probability += (
            config.problematic_lot_anomaly_increase
        )

    if shift == ShiftType.NIGHT:
        probability += (
            config.night_anomaly_increase
        )

    probability += (
        degradation_score
        * config.degradation_anomaly_increase
    )

    return min(
        probability,
        0.95,
    )

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
        id=uuid4(),
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

def build_process_event_rows(
    pcb_unit_id,
    machine: Machine,
    stage_type: StageType,
    started_at: datetime,
    is_anomalous: bool,
    anomaly_result: ProcessEventResult,
    random_generator: Random,
    degradation_score: float = 0.0,
    is_degrading_stage: bool = False,
) -> tuple[
    dict[str, object],
    list[dict[str, object]],
]:
    observation = generate_stage_observation(
        random_generator,
        stage_type,
        is_anomalous=is_anomalous,
    )

    event_id = uuid4()
    completed_at = started_at + timedelta(
        minutes=5
    )

    result = (
        anomaly_result
        if is_anomalous
        else ProcessEventResult.PASSED
    )

    event_row: dict[str, object] = {
        "id": event_id,
        "pcb_unit_id": pcb_unit_id,
        "machine_id": machine.id,
        "result": result,
        "process_parameters": {
        **observation.process_parameters,
        "drift_score": observation.drift_score,
        "degradation_score": (
            degradation_score
            if is_degrading_stage
            else 0.0
        ),
        "is_simulated": True,
    },
        "notes": (
            "Synthetic FactoryPulse demo event"
        ),
        "started_at": started_at,
        "completed_at": completed_at,
        "created_at": completed_at,
        "updated_at": completed_at,
    }

    measurement_rows: list[
        dict[str, object]
    ] = []

    for measurement in observation.measurements:
        measurement_rows.append(
            {
                "id": uuid4(),
                "process_event_id": event_id,
                "metric_code": (
                    measurement.metric_code
                ),
                "value": measurement.value,
                "unit": measurement.unit,
                "lower_spec_limit": (
                    measurement.lower_spec_limit
                ),
                "upper_spec_limit": (
                    measurement.upper_spec_limit
                ),
                "is_within_spec": (
                    measurement.is_within_spec
                ),
                "measured_at": completed_at,
                "created_at": completed_at,
            }
        )

    return event_row, measurement_rows

def insert_simulation_batch(
    db: Session,
    pcb_rows: list[dict[str, object]],
    event_rows: list[dict[str, object]],
    measurement_rows: list[dict[str, object]],
) -> None:
    if not pcb_rows:
        return

    db.execute(
        insert(PCBUnit),
        pcb_rows,
    )
    db.execute(
        insert(ProcessEvent),
        event_rows,
    )
    db.execute(
        insert(QualityMeasurement),
        measurement_rows,
    )

    pcb_rows.clear()
    event_rows.clear()
    measurement_rows.clear()

def seed_demo_data(
    db: Session,
    config: SimulationConfig,
) -> SeedSummary:
    if demo_data_exists(db, config.data_prefix):
        raise DemoDataAlreadyExistsError(
            f"Data with prefix "
            f"'{config.data_prefix}' already exists"
        )

    random_generator = Random(
        config.random_seed
    )

    machines = create_demo_machines(
        db,
        config,
    )

    material_lots = create_demo_material_lots(
        db,
        config,
    )

    pcb_count = 0
    process_event_count = 0
    measurement_count = 0
    passed_pcb_count = 0
    failed_pcb_count = 0
    rework_pcb_count = 0
    day_shift_pcb_count = 0
    night_shift_pcb_count = 0
    problematic_lot_pcb_count = 0

    global_pcb_number = 1

    order_duration = timedelta(
        minutes=(
            (config.pcb_per_order - 1) * 7
            + len(STAGE_ORDER)
            * config.stage_duration_minutes
        )
    )

    order_spacing = (
        order_duration
        + timedelta(minutes=30)
    )

    pcb_rows: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []
    measurement_rows: list[
        dict[str, object]
    ] = []

    for order_number in range(
        1,
        config.order_count + 1,
    ):
        order_start = (
            config.simulation_start
            + order_spacing
            * (order_number - 1)
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
            status=(
                ProductionOrderStatus.COMPLETED
            ),
            planned_start_at=order_start,
            planned_end_at=(
                order_start + order_spacing
            ),
            actual_start_at=order_start,
            actual_end_at=(
                order_start + order_duration
            ),
        )

        db.add(production_order)
        db.flush()

        for pcb_index in range(
            config.pcb_per_order
        ):
            pcb_started_at = (
                order_start
                + timedelta(
                    minutes=pcb_index * 7
                )
            )

            shift = (
                ShiftType.NIGHT
                if random_generator.random()
                < config.night_shift_probability
                else ShiftType.DAY
            )

            (
                material_lot,
                uses_problematic_lot,
            ) = choose_material_lot(
                random_generator,
                material_lots,
                config.problematic_lot_probability,
            )

            if shift == ShiftType.NIGHT:
                night_shift_pcb_count += 1
            else:
                day_shift_pcb_count += 1

            if uses_problematic_lot:
                problematic_lot_pcb_count += 1

            pcb_id = uuid4()

            degradation_score = (
               calculate_degradation_score(
                   pcb_number=global_pcb_number,
                   total_pcb_count=config.total_pcb_count,
                   degradation_start_ratio=(
                       config.degradation_start_ratio
                   ),
               )
)           

            pcb_anomaly_probability = (
                calculate_pcb_anomaly_probability(
                    config=config,
                    shift=shift,
                    uses_problematic_lot=uses_problematic_lot,
                    degradation_score=degradation_score,
                )
            )

            pcb_is_anomalous = (
                random_generator.random()
                < pcb_anomaly_probability
            )

            if pcb_is_anomalous:
                degradation_stage_probability = (
                    degradation_score
                )

                if (
                    degradation_score > 0.0
                    and random_generator.random()
                    < degradation_stage_probability
                ):
                    anomaly_stage = config.degrading_stage
                else:
                    anomaly_stage = random_generator.choice(
                        STAGE_ORDER
                    )
            else:
                anomaly_stage = None


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

                (
                    event_row,
                    generated_measurement_rows,
                ) = build_process_event_rows(
                    pcb_unit_id=pcb_id,
                    machine=machines[stage_type],
                    stage_type=stage_type,
                    started_at=event_started_at,
                    is_anomalous=(
                        is_anomalous_stage
                    ),
                    anomaly_result=anomaly_result,
                    random_generator=random_generator,
                    degradation_score=degradation_score,
                    is_degrading_stage=(
                        stage_type == config.degrading_stage
                    ),
                )

                event_rows.append(event_row)
                measurement_rows.extend(
                    generated_measurement_rows
                )

                process_event_count += 1
                measurement_count += len(
                    generated_measurement_rows
                )

                if (
                    is_anomalous_stage
                    and anomaly_result
                    == ProcessEventResult.FAILED
                ):
                    break

            if not pcb_is_anomalous:
                pcb_status = PCBUnitStatus.PASSED
                passed_pcb_count += 1
            elif (
                anomaly_result
                == ProcessEventResult.WARNING
            ):
                pcb_status = PCBUnitStatus.REWORK
                rework_pcb_count += 1
            else:
                pcb_status = PCBUnitStatus.FAILED
                failed_pcb_count += 1

            pcb_rows.append(
                {
                    "id": pcb_id,
                    "serial_number": (
                        f"{config.data_prefix}-PCB-"
                        f"{global_pcb_number:06d}"
                    ),
                    "production_order_id": (
                        production_order.id
                    ),
                    "material_lot_id": (
                        material_lot.id
                    ),
                    "shift": shift,
                    "status": pcb_status,
                }
            )

            pcb_count += 1
            global_pcb_number += 1

            if (
                len(pcb_rows)
                >= config.flush_batch_size
            ):
                insert_simulation_batch(
                    db,
                    pcb_rows,
                    event_rows,
                    measurement_rows,
                )

    insert_simulation_batch(
        db,
        pcb_rows,
        event_rows,
        measurement_rows,
    )

    db.flush()

    return SeedSummary(
        machine_count=len(machines),
        material_lot_count=len(material_lots),
        production_order_count=config.order_count,
        pcb_count=pcb_count,
        process_event_count=process_event_count,
        measurement_count=measurement_count,
        passed_pcb_count=passed_pcb_count,
        failed_pcb_count=failed_pcb_count,
        rework_pcb_count=rework_pcb_count,
        day_shift_pcb_count=day_shift_pcb_count,
        night_shift_pcb_count=night_shift_pcb_count,
        problematic_lot_pcb_count=(
            problematic_lot_pcb_count
        ),
    )