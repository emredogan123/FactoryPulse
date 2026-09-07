import argparse
import json
from datetime import date

from sqlalchemy.orm import Session

from app.analytics.alerts import evaluate_daily_quality_alerts
from app.db.session import engine


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate daily FactoryPulse quality alerts"
    )

    parser.add_argument(
        "--start-date",
        type=date.fromisoformat,
        required=True,
    )
    parser.add_argument(
        "--end-date",
        type=date.fromisoformat,
        required=True,
    )
    parser.add_argument("--prefix", default=None)

    args = parser.parse_args()

    try:
        with Session(engine) as db:
            with db.begin():
                result = evaluate_daily_quality_alerts(
                    db=db,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    prefix=args.prefix,
                )
    except ValueError as error:
        parser.error(str(error))

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()