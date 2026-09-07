from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    StageQualityItem,
    StageQualityResponse,
)
from app.models.machine import Machine, StageType
from app.models.pcb_unit import PCBUnit
from app.models.process_event import (
    ProcessEvent,
    ProcessEventResult,
)


def get_stage_quality(
    db: Session,
    prefix: str | None = None,
) -> StageQualityResponse:
    statement = (
        select(
            Machine.stage_type,
            ProcessEvent.result,
            func.count(ProcessEvent.id),
        )
        .select_from(ProcessEvent)
        .join(
            Machine,
            Machine.id == ProcessEvent.machine_id,
        )
        .join(
            PCBUnit,
            PCBUnit.id == ProcessEvent.pcb_unit_id,
        )
        .group_by(
            Machine.stage_type,
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
        stage: {
            result: 0
            for result in ProcessEventResult
        }
        for stage in StageType
    }

    for stage, result, count in db.execute(statement):
        counts[stage][result] += count

    items = []

    for stage in StageType:
        stage_counts = counts[stage]

        passed = stage_counts[
            ProcessEventResult.PASSED
        ]
        warning = stage_counts[
            ProcessEventResult.WARNING
        ]
        failed = stage_counts[
            ProcessEventResult.FAILED
        ]
        pending = stage_counts[
            ProcessEventResult.PENDING
        ]

        evaluated = passed + warning + failed
        issues = warning + failed

        items.append(
            StageQualityItem(
                stage_type=stage.value,
                total_count=evaluated + pending,
                evaluated_count=evaluated,
                pending_count=pending,
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

    return StageQualityResponse(
        prefix=prefix,
        stages=items,
    )