import argparse
import logging
import signal
from datetime import datetime, timedelta, timezone
from threading import Event

from sqlalchemy.orm import Session

from app.analytics.alerts import evaluate_daily_quality_alerts
from app.db.session import engine


logger = logging.getLogger("quality_alert_worker")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Periodically evaluate daily quality alerts"
    )

    parser.add_argument(
        "--prefix",
        action="append",
        help="Dataset prefix; repeat this option for multiple groups.",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=30,
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=3600,
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one cycle and exit.",
    )

    args = parser.parse_args()

    if not 1 <= args.lookback_days <= 366:
        parser.error("--lookback-days must be between 1 and 366")

    if args.interval_seconds < 60:
        parser.error("--interval-seconds must be at least 60")

    if args.prefix and any(
        not prefix or len(prefix) > 100
        for prefix in args.prefix
    ):
        parser.error("Prefixes must contain 1 to 100 characters")

    prefixes = list(dict.fromkeys(args.prefix or [None]))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    stop = Event()

    def request_stop(signum, frame) -> None:
        stop.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    try:
        while not stop.is_set():
            end_date = (
                datetime.now(timezone.utc).date()
                - timedelta(days=1)
            )
            start_date = end_date - timedelta(
                days=args.lookback_days - 1
            )

            failed = False

            for prefix in prefixes:
                if stop.is_set():
                    break

                try:
                    with Session(engine) as db:
                        with db.begin():
                            result = evaluate_daily_quality_alerts(
                                db=db,
                                start_date=start_date,
                                end_date=end_date,
                                prefix=prefix,
                            )

                    logger.info(
                        "dataset=%s range=%s..%s result=%s",
                        prefix or "ALL",
                        start_date,
                        end_date,
                        result,
                    )
                except Exception:
                    failed = True
                    logger.exception(
                        "Alert evaluation failed for dataset=%s",
                        prefix or "ALL",
                    )

            if args.once:
                if failed:
                    raise SystemExit(1)
                break

            # Bekleme, kapatma sinyali geldiğinde hemen sonlanır.
            stop.wait(args.interval_seconds)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()