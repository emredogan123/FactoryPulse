from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.analytics.daily_quality import get_daily_quality
from app.models.quality_alert import QualityAlert


RULE_CODE = "DAILY_ISSUE_RATE_V1"
THRESHOLD_PERCENT = Decimal("5.00")
MINIMUM_COUNT = 100


def evaluate_daily_quality_alerts(
    db: Session,
    start_date: date,
    end_date: date,
    prefix: str | None = None,
) -> dict[str, int]:
    number_of_days = (end_date - start_date).days + 1

    if not 1 <= number_of_days <= 366:
        raise ValueError(
            "Date range must contain between 1 and 366 days."
        )

    today_utc = datetime.now(timezone.utc).date()

    if end_date >= today_utc:
        raise ValueError(
            "Only completed UTC days can be evaluated."
        )

    dataset_prefix = prefix or ""

    if len(dataset_prefix) > 100:
        raise ValueError(
            "Dataset prefix must not exceed 100 characters."
        )

    report = get_daily_quality(
        db=db,
        start_date=start_date,
        end_date=end_date,
        prefix=dataset_prefix or None,
    )

    candidates = []

    for day in report.days:
        if day.evaluated_count < MINIMUM_COUNT:
            continue

        # Yuvarlanmış issue_rate yerine gerçek sayaçları kullanır.
        exceeds_threshold = (
            Decimal(day.issue_count) * 100
            > THRESHOLD_PERCENT * day.evaluated_count
        )

        if not exceeds_threshold:
            continue

        candidates.append(
            {
                "id": uuid4(),
                "rule_code": RULE_CODE,
                "dataset_prefix": dataset_prefix,
                "quality_date": day.date,
                "evaluated_count": day.evaluated_count,
                "issue_count": day.issue_count,
                "threshold_percent": THRESHOLD_PERCENT,
                "minimum_count": MINIMUM_COUNT,
            }
        )

    created_count = 0

    if candidates:
        statement = (
            insert(QualityAlert)
            .values(candidates)
            .on_conflict_do_nothing(
                constraint="uq_quality_alert_rule_dataset_date"
            )
            .returning(QualityAlert.id)
        )

        created_count = len(
            db.execute(statement).scalars().all()
        )

    # Commit işlemini çağıran endpoint veya görev yapacak.
    return {
        "checked_days": len(report.days),
        "matching_days": len(candidates),
        "created_count": created_count,
        "existing_count": len(candidates) - created_count,
    }