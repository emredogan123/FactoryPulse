import argparse

from sqlalchemy import Float, case, cast, func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.material_lot import MaterialLot
from app.models.pcb_unit import (
    PCBUnit,
    PCBUnitStatus,
)
from app.models.machine import Machine, StageType
from app.models.process_event import (
    ProcessEvent,
    ProcessEventResult,
)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze FactoryPulse synthetic data"
        )
    )

    parser.add_argument(
        "--prefix",
        required=True,
    )

    return parser


def issue_count_expression():
    return func.sum(
        case(
            (
                PCBUnit.status
                != PCBUnitStatus.PASSED,
                1,
            ),
            else_=0,
        )
    )


def calculate_rate(
    issue_count: int,
    total_count: int,
) -> float:
    if total_count == 0:
        return 0.0

    return round(
        issue_count / total_count * 100,
        2,
    )


def print_shift_analysis(
    db: Session,
    prefix: str,
) -> None:
    statement = (
        select(
            PCBUnit.shift,
            func.count(),
            issue_count_expression(),
        )
        .where(
            PCBUnit.serial_number.like(
                f"{prefix}-%"
            )
        )
        .group_by(PCBUnit.shift)
        .order_by(PCBUnit.shift)
    )

    rows = db.execute(statement).all()

    print("\nShift analysis")

    for shift, total, issue_count in rows:
        issue_count = int(issue_count or 0)

        print(
            f"{shift.value}: "
            f"{total} PCBs, "
            f"{issue_count} issues, "
            f"{calculate_rate(issue_count, total)}%"
        )


def print_material_lot_analysis(
    db: Session,
    prefix: str,
) -> None:
    statement = (
        select(
            MaterialLot.lot_code,
            func.count(),
            issue_count_expression(),
        )
        .join(
            PCBUnit,
            PCBUnit.material_lot_id
            == MaterialLot.id,
        )
        .where(
            PCBUnit.serial_number.like(
                f"{prefix}-%"
            )
        )
        .group_by(MaterialLot.lot_code)
        .order_by(MaterialLot.lot_code)
    )

    rows = db.execute(statement).all()

    print("\nMaterial lot analysis")

    for lot_code, total, issue_count in rows:
        issue_count = int(issue_count or 0)

        print(
            f"{lot_code}: "
            f"{total} PCBs, "
            f"{issue_count} issues, "
            f"{calculate_rate(issue_count, total)}%"
        )

def print_machine_degradation_analysis(
    db: Session,
    prefix: str,
) -> None:
    degradation_score = cast(
        ProcessEvent.process_parameters[
            "degradation_score"
        ].astext,
        Float,
    )

    machine_period = case(
        (
            degradation_score <= 0.0,
            "HEALTHY",
        ),
        else_="DEGRADED",
    ).label("machine_period")

    issue_count = func.sum(
        case(
            (
                ProcessEvent.result.in_(
                    (
                        ProcessEventResult.WARNING,
                        ProcessEventResult.FAILED,
                    )
                ),
                1,
            ),
            else_=0,
        )
    )



    statement = (
        select(
            machine_period,
            func.count(),
            issue_count,
            func.avg(degradation_score),
        )
        .join(
            PCBUnit,
            PCBUnit.id
            == ProcessEvent.pcb_unit_id,
        )
        .join(
            Machine,
            Machine.id
            == ProcessEvent.machine_id,
        )
        .where(
            PCBUnit.serial_number.like(
                f"{prefix}-%"
            ),
            Machine.stage_type
            == StageType.REFLOW_SOLDERING,
            degradation_score.is_not(None),
        )
        .group_by(machine_period)
        .order_by(machine_period)
    )

    rows = db.execute(statement).all()

    print("\nMachine degradation analysis")

    if not rows:
        print(
            "No degradation data found "
            "for this prefix"
        )
        return

    for (
        period,
        total,
        issues,
        average_score,
    ) in rows:
        issues = int(issues or 0)

        print(
            f"{period}: "
            f"{total} events, "
            f"{issues} issues, "
            f"{calculate_rate(issues, total)}%, "
            f"average score "
            f"{round(float(average_score or 0), 4)}"
        )

def print_parameter_interaction_analysis(
    db: Session,
    prefix: str,
) -> None:
    thermal_stress = cast(
        ProcessEvent.process_parameters[
            "thermal_stress_index"
        ].astext,
        Float,
    )

    result_group = case(
        (
            ProcessEvent.result.in_(
                (
                    ProcessEventResult.WARNING,
                    ProcessEventResult.FAILED,
                )
            ),
            "ISSUE",
        ),
        else_="PASSED",
    ).label("result_group")

    statement = (
        select(
            result_group,
            func.count(),
            func.avg(thermal_stress),
            func.max(thermal_stress),
        )
        .join(
            PCBUnit,
            PCBUnit.id
            == ProcessEvent.pcb_unit_id,
        )
        .join(
            Machine,
            Machine.id
            == ProcessEvent.machine_id,
        )
        .where(
            PCBUnit.serial_number.like(
                f"{prefix}-%"
            ),
            Machine.stage_type
            == StageType.REFLOW_SOLDERING,
            thermal_stress.is_not(None),
        )
        .group_by(result_group)
        .order_by(result_group)
    )

    rows = db.execute(statement).all()

    print("\nReflow parameter interaction analysis")

    if not rows:
        print(
            "No parameter interaction data "
            "found for this prefix"
        )
        return

    for (
        group,
        total,
        average_stress,
        maximum_stress,
    ) in rows:
        print(
            f"{group}: "
            f"{total} events, "
            f"average stress "
            f"{round(float(average_stress or 0), 4)}, "
            f"maximum stress "
            f"{round(float(maximum_stress or 0), 4)}"
        )

def main() -> None:
    arguments = build_parser().parse_args()

    with SessionLocal() as db:
        print(
            "FactoryPulse synthetic data analysis"
        )
        print(f"Prefix: {arguments.prefix}")

        print_shift_analysis(
            db,
            arguments.prefix,
        )
        print_material_lot_analysis(
            db,
            arguments.prefix,
        )
        print_machine_degradation_analysis(
            db,
            arguments.prefix,
        )
        print_parameter_interaction_analysis(
            db,
            arguments.prefix,
)


if __name__ == "__main__":
    main()