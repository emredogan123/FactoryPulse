import argparse

from app.db.session import SessionLocal
from app.simulation.config import SimulationConfig
from app.simulation.seeder import (
    DemoDataAlreadyExistsError,
    SeedSummary,
    seed_demo_data,
)


def positive_integer(value: str) -> int:
    parsed_value = int(value)

    if parsed_value <= 0:
        raise argparse.ArgumentTypeError(
            "value must be greater than zero"
        )

    return parsed_value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate synthetic FactoryPulse demo data"
        )
    )

    parser.add_argument(
        "--prefix",
        default="DEMO",
    )
    parser.add_argument(
        "--orders",
        type=positive_integer,
        default=3,
    )
    parser.add_argument(
        "--pcbs-per-order",
        type=positive_integer,
        default=50,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    return parser


def print_summary(summary: SeedSummary) -> None:
    print("FactoryPulse demo data created")
    print(f"Machines: {summary.machine_count}")
    print(
        "Production orders: "
        f"{summary.production_order_count}"
    )
    print(f"PCB units: {summary.pcb_count}")
    print(
        "Process events: "
        f"{summary.process_event_count}"
    )
    print(
        "Quality measurements: "
        f"{summary.measurement_count}"
    )
    print(f"Passed PCBs: {summary.passed_pcb_count}")
    print(f"Failed PCBs: {summary.failed_pcb_count}")
    print(f"Rework PCBs: {summary.rework_pcb_count}")


def main() -> None:
    arguments = build_parser().parse_args()

    config = SimulationConfig(
        data_prefix=arguments.prefix,
        random_seed=arguments.seed,
        order_count=arguments.orders,
        pcb_per_order=arguments.pcbs_per_order,
    )

    with SessionLocal() as db:
        try:
            summary = seed_demo_data(
                db,
                config,
            )
            db.commit()
        except DemoDataAlreadyExistsError as error:
            db.rollback()
            print(error)
            return
        except Exception:
            db.rollback()
            raise

    print_summary(summary)


if __name__ == "__main__":
    main()