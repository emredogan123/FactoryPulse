from datetime import (
    date,
    datetime,
    time,
    timedelta,
    timezone,
)

from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    DailyQualityItem,
    DailyQualityResponse,
)
from app.models.pcb_unit import PCBUnit
from app.models.process_event import (
    ProcessEvent,
    ProcessEventResult,
)


def get_daily_quality(
    db: Session,
    start_date: date,
    end_date: date,
    prefix: str | None = None,
) -> DailyQualityResponse:
    number_of_days = (end_date - start_date).days + 1

    if not 1 <= number_of_days <= 366:
        raise ValueError(
            "Date range must contain between 1 and 366 days."
        )

    start_at = datetime.combine(
        start_date,
        time.min,
        tzinfo=timezone.utc,
    )

    end_before = datetime.combine(
        end_date + timedelta(days=1),
        time.min,
        tzinfo=timezone.utc,
    )

    # PostgreSQL oturumunun saat diliminden bağımsız UTC günü.
    event_day = cast(
        func.timezone(
            "UTC",
            ProcessEvent.completed_at,
        ),
        Date,
    )

    evaluated_results = (
        ProcessEventResult.PASSED,
        ProcessEventResult.WARNING,
        ProcessEventResult.FAILED,
    )

    statement = (
        select(
            event_day.label("event_day"),
            ProcessEvent.result,
            func.count(ProcessEvent.id),
        )
        .select_from(ProcessEvent)
        .join(
            PCBUnit,
            PCBUnit.id == ProcessEvent.pcb_unit_id,
        )
        .where(
            ProcessEvent.completed_at >= start_at,
            ProcessEvent.completed_at < end_before,
            ProcessEvent.result.in_(evaluated_results),
        )
        .group_by(
            event_day,
            ProcessEvent.result,
        )
    )

    if prefix:
        statement = statement.where(
            PCBUnit.serial_number.startswith(
                f"{prefix}-",
                autoescape=True,
            )
        )

    counts = {
        start_date + timedelta(days=offset): {
            result: 0
            for result in evaluated_results
        }
        for offset in range(number_of_days)
    }

    for day, result, count in db.execute(statement):
        counts[day][result] += count

    items = []

    for day, day_counts in counts.items():
        passed = day_counts[ProcessEventResult.PASSED]
        warning = day_counts[ProcessEventResult.WARNING]
        failed = day_counts[ProcessEventResult.FAILED]

        evaluated = passed + warning + failed
        issues = warning + failed

        items.append(
            DailyQualityItem(
                date=day,
                evaluated_count=evaluated,
                passed_count=passed,
                warning_count=warning,
                failed_count=failed,
                issue_count=issues,
                issue_rate=(
                    round(100 * issues / evaluated, 2)
                    if evaluated
                    else None
                ),
            )
        )

    return DailyQualityResponse(
        prefix=prefix,
        start_date=start_date,
        end_date=end_date,
        timezone="UTC",
        days=items,
    )