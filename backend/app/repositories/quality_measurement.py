from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.quality_measurement import QualityMeasurement
from app.schemas.quality_measurement import (
    QualityMeasurementCreate,
)


def get_quality_measurement_by_id(
    db: Session,
    measurement_id: UUID,
) -> QualityMeasurement | None:
    return db.get(
        QualityMeasurement,
        measurement_id,
    )


def get_measurement_by_event_and_metric(
    db: Session,
    process_event_id: UUID,
    metric_code: str,
) -> QualityMeasurement | None:
    statement = select(QualityMeasurement).where(
        QualityMeasurement.process_event_id
        == process_event_id,
        QualityMeasurement.metric_code
        == metric_code,
    )

    return db.scalar(statement)


def list_quality_measurements(
    db: Session,
    process_event_id: UUID | None = None,
    metric_code: str | None = None,
) -> list[QualityMeasurement]:
    statement = select(QualityMeasurement)

    if process_event_id is not None:
        statement = statement.where(
            QualityMeasurement.process_event_id
            == process_event_id
        )

    if metric_code is not None:
        statement = statement.where(
            QualityMeasurement.metric_code
            == metric_code
        )

    statement = statement.order_by(
        QualityMeasurement.measured_at.desc()
    )

    return list(db.scalars(statement).all())


def create_quality_measurement(
    db: Session,
    data: QualityMeasurementCreate,
    is_within_spec: bool | None,
) -> QualityMeasurement:
    measurement = QualityMeasurement(
        **data.model_dump(exclude_none=True),
        is_within_spec=is_within_spec,
    )

    db.add(measurement)
    db.commit()
    db.refresh(measurement)

    return measurement