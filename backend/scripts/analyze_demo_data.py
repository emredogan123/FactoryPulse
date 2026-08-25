import argparse

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.material_lot import MaterialLot
from app.models.pcb_unit import (
    PCBUnit,
    PCBUnitStatus,
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


if __name__ == "__main__":
    main()