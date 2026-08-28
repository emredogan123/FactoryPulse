import argparse
import csv
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.models.pcb_unit import (
    PCBUnit,
    PCBUnitStatus,
)
from app.models.process_event import ProcessEvent


DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parents[2]
    / "ml"
    / "data"
    / "factorypulse_dataset.csv"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export FactoryPulse PCB data "
            "as a machine learning dataset"
        )
    )

    parser.add_argument(
        "--prefix",
        required=True,
        help="PCB serial-number prefix",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output CSV path",
    )

    return parser


def normalize_feature_name(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def convert_feature_value(value: Any) -> Any:
    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (str, int, float)) or value is None:
        return value

    return str(value)


def build_pcb_row(pcb: PCBUnit) -> dict[str, Any]:
    row: dict[str, Any] = {
        "pcb_id": str(pcb.id),
        "serial_number": pcb.serial_number,
        "shift": pcb.shift.value,
        "material_lot_code": (
            pcb.material_lot.lot_code
            if pcb.material_lot
            else ""
        ),
        "material_type": (
            pcb.material_lot.material_type
            if pcb.material_lot
            else ""
        ),
        "supplier_code": (
            pcb.material_lot.supplier_code
            if pcb.material_lot
            else ""
        ),
        "target_issue": int(
            pcb.status
            in {
                PCBUnitStatus.FAILED,
                PCBUnitStatus.REWORK,
            }
        ),
    }

    for event in pcb.process_events:
        stage = normalize_feature_name(
            event.machine.stage_type.value
        )

        for parameter_name, value in (
            event.process_parameters.items()
        ):
            feature_name = normalize_feature_name(
                parameter_name
            )

            row[
                f"{stage}__param__{feature_name}"
            ] = convert_feature_value(value)

        if (
            event.started_at is not None
            and event.completed_at is not None
        ):
            duration_seconds = (
                event.completed_at
                - event.started_at
            ).total_seconds()

            row[
                f"{stage}__duration_seconds"
            ] = round(duration_seconds, 4)

        for measurement in event.quality_measurements:
            metric = normalize_feature_name(
                measurement.metric_code
            )

            row[
                f"{stage}__metric__{metric}"
            ] = measurement.value

    return row


def load_pcb_rows(prefix: str) -> list[dict[str, Any]]:
    statement = (
        select(PCBUnit)
        .options(
            selectinload(PCBUnit.material_lot),
            selectinload(
                PCBUnit.process_events
            ).selectinload(
                ProcessEvent.machine
            ),
            selectinload(
                PCBUnit.process_events
            ).selectinload(
                ProcessEvent.quality_measurements
            ),
        )
        .where(
            PCBUnit.serial_number.like(
                f"{prefix}-%"
            ),
            PCBUnit.status.in_(
                (
                    PCBUnitStatus.PASSED,
                    PCBUnitStatus.FAILED,
                    PCBUnitStatus.REWORK,
                )
            ),
        )
        .order_by(PCBUnit.serial_number)
    )

    with SessionLocal() as db:
        pcbs = db.scalars(statement).all()

        return [
            build_pcb_row(pcb)
            for pcb in pcbs
        ]


def write_dataset(
    rows: list[dict[str, Any]],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    identifier_columns = [
        "pcb_id",
        "serial_number",
    ]

    context_columns = [
        "shift",
        "material_lot_code",
        "material_type",
        "supplier_code",
    ]

    target_columns = [
        "target_issue",
    ]

    fixed_columns = (
        identifier_columns
        + context_columns
        + target_columns
    )

    dynamic_columns = sorted(
        {
            column
            for row in rows
            for column in row
            if column not in fixed_columns
        }
    )

    fieldnames = (
        identifier_columns
        + context_columns
        + dynamic_columns
        + target_columns
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    arguments = build_parser().parse_args()

    rows = load_pcb_rows(arguments.prefix)

    if not rows:
        raise SystemExit(
            "No completed PCB data found "
            f"for prefix: {arguments.prefix}"
        )

    write_dataset(
        rows,
        arguments.output,
    )

    issue_count = sum(
        int(row["target_issue"])
        for row in rows
    )

    passed_count = len(rows) - issue_count

    print("FactoryPulse ML dataset exported")
    print(f"Prefix: {arguments.prefix}")
    print(f"Rows: {len(rows)}")
    print(f"Passed: {passed_count}")
    print(f"Issues: {issue_count}")
    print(
        "Issue rate: "
        f"{round(issue_count / len(rows) * 100, 2)}%"
    )
    print(
        f"Output: {arguments.output.resolve()}"
    )


if __name__ == "__main__":
    main()