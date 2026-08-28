from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.pcb_unit import PCBUnit, PCBUnitStatus
from app.models.process_event import ProcessEvent
from app.models.production_order import ProductionOrder
from app.models.quality_measurement import QualityMeasurement
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import selectinload

from app.analytics.schemas import (
    AnalyticsOverview,
    PCBRiskPredictionResponse,
    PCBStatusCounts,
    RiskLevel,
    PCBRiskListResponse
)
from app.ml.features import build_pcb_feature_row
from app.ml.inference import (
    predict_issue_probability,predict_issue_probabilities
)

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
def determine_risk_level(
    probability: float,
    decision_threshold: float,
) -> RiskLevel:
    if probability >= decision_threshold:
        return RiskLevel.HIGH

    if probability >= decision_threshold / 2:
        return RiskLevel.MEDIUM

    return RiskLevel.LOW

def get_pcb_risk_prediction(
    db: Session,
    pcb_id: UUID,
    model_path: Path,
) -> PCBRiskPredictionResponse | None:
    statement = (
        select(PCBUnit)
        .options(
            selectinload(PCBUnit.material_lot),
            selectinload(
                PCBUnit.process_events
            ).selectinload(
                ProcessEvent.machine
            ),
        )
        .where(PCBUnit.id == pcb_id)
    )

    pcb = db.scalar(statement)

    if pcb is None:
        return None

    feature_row = build_pcb_feature_row(
        pcb
    )

    (
        probability,
        decision_threshold,
        predicted_issue,
        model_type,
    ) = predict_issue_probability(
        feature_row,
        model_path,
    )

    return PCBRiskPredictionResponse(
        pcb_id=pcb.id,
        serial_number=pcb.serial_number,
        actual_status=pcb.status,
        issue_probability=probability,
        decision_threshold=decision_threshold,
        predicted_issue=predicted_issue,
        risk_level=determine_risk_level(
            probability,
            decision_threshold,
        ),
        model_type=model_type,
    )

def get_pcb_risk_predictions(
    db: Session,
    model_path: Path,
    prefix: str | None,
    limit: int,
) -> PCBRiskListResponse:
    statement = (
        select(PCBUnit)
        .options(
            selectinload(PCBUnit.material_lot),
            selectinload(
                PCBUnit.process_events
            ).selectinload(
                ProcessEvent.machine
            ),
        )
        .where(
            PCBUnit.status.in_(
                (
                    PCBUnitStatus.PASSED,
                    PCBUnitStatus.FAILED,
                    PCBUnitStatus.REWORK,
                )
            )
        )
        .order_by(
            PCBUnit.updated_at.desc()
        )
        .limit(limit)
    )

    if prefix:
        statement = statement.where(
            PCBUnit.serial_number.like(
                f"{prefix}-%"
            )
        )

    pcbs = list(
        db.scalars(statement).all()
    )

    feature_rows = [
        build_pcb_feature_row(pcb)
        for pcb in pcbs
    ]

    raw_predictions = (
        predict_issue_probabilities(
            feature_rows,
            model_path,
        )
    )

    items: list[
        PCBRiskPredictionResponse
    ] = []

    for pcb, raw_prediction in zip(
        pcbs,
        raw_predictions,
    ):
        (
            probability,
            decision_threshold,
            predicted_issue,
            model_type,
        ) = raw_prediction

        items.append(
            PCBRiskPredictionResponse(
                pcb_id=pcb.id,
                serial_number=pcb.serial_number,
                actual_status=pcb.status,
                issue_probability=probability,
                decision_threshold=(
                    decision_threshold
                ),
                predicted_issue=predicted_issue,
                risk_level=determine_risk_level(
                    probability,
                    decision_threshold,
                ),
                model_type=model_type,
            )
        )

    return PCBRiskListResponse(
        total_analyzed=len(items),
        high_risk_count=sum(
            item.risk_level
            == RiskLevel.HIGH
            for item in items
        ),
        medium_risk_count=sum(
            item.risk_level
            == RiskLevel.MEDIUM
            for item in items
        ),
        low_risk_count=sum(
            item.risk_level
            == RiskLevel.LOW
            for item in items
        ),
        items=items,
    )