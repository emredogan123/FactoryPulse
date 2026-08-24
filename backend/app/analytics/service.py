from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    AnalyticsOverview,
    PCBStatusCounts,
)
from app.models.pcb_unit import PCBUnit, PCBUnitStatus
from app.models.process_event import ProcessEvent
from app.models.production_order import ProductionOrder
from app.models.quality_measurement import QualityMeasurement


def count_records(
    db: Session,
    model: type,
) -> int:
    result = db.scalar(
        select(func.count()).select_from(model)
    )

    return int(result or 0)


def count_pcbs_by_status(
    db: Session,
    status: PCBUnitStatus,
) -> int:
    result = db.scalar(
        select(func.count())
        .select_from(PCBUnit)
        .where(PCBUnit.status == status)
    )

    return int(result or 0)


def calculate_rate(
    count: int,
    total: int,
) -> float:
    if total == 0:
        return 0.0

    return round(count / total * 100, 2)


def get_analytics_overview(
    db: Session,
) -> AnalyticsOverview:
    production_order_count = count_records(
        db,
        ProductionOrder,
    )
    pcb_count = count_records(
        db,
        PCBUnit,
    )
    process_event_count = count_records(
        db,
        ProcessEvent,
    )
    quality_measurement_count = count_records(
        db,
        QualityMeasurement,
    )

    passed_count = count_pcbs_by_status(
        db,
        PCBUnitStatus.PASSED,
    )
    failed_count = count_pcbs_by_status(
        db,
        PCBUnitStatus.FAILED,
    )
    rework_count = count_pcbs_by_status(
        db,
        PCBUnitStatus.REWORK,
    )
    queued_count = count_pcbs_by_status(
        db,
        PCBUnitStatus.QUEUED,
    )

    out_of_spec_count = db.scalar(
        select(func.count())
        .select_from(QualityMeasurement)
        .where(
            QualityMeasurement.is_within_spec.is_(False)
        )
    )

    return AnalyticsOverview(
        production_order_count=production_order_count,
        pcb_count=pcb_count,
        pcb_status_counts=PCBStatusCounts(
            passed=passed_count,
            failed=failed_count,
            rework=rework_count,
            queued=queued_count,
        ),
        pass_rate=calculate_rate(
            passed_count,
            pcb_count,
        ),
        failure_rate=calculate_rate(
            failed_count,
            pcb_count,
        ),
        rework_rate=calculate_rate(
            rework_count,
            pcb_count,
        ),
        process_event_count=process_event_count,
        quality_measurement_count=(
            quality_measurement_count
        ),
        out_of_spec_measurement_count=int(
            out_of_spec_count or 0
        ),
    )