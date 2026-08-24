from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.quality_measurement import QualityMeasurement
from app.repositories.process_event import (
    get_process_event_by_id,
)
from app.repositories.quality_measurement import (
    create_quality_measurement as repository_create,
)
from app.repositories.quality_measurement import (
    get_measurement_by_event_and_metric,
    get_quality_measurement_by_id,
    list_quality_measurements,
)
from app.schemas.quality_measurement import (
    QualityMeasurementCreate,
)
from app.services.process_event import (
    ProcessEventNotFoundError,
)


class QualityMeasurementNotFoundError(Exception):
    pass


class QualityMetricAlreadyExistsError(Exception):
    pass


def calculate_is_within_spec(
    value: float,
    lower_spec_limit: float | None,
    upper_spec_limit: float | None,
) -> bool | None:
    if (
        lower_spec_limit is None
        and upper_spec_limit is None
    ):
        return None

    if (
        lower_spec_limit is not None
        and value < lower_spec_limit
    ):
        return False

    if (
        upper_spec_limit is not None
        and value > upper_spec_limit
    ):
        return False

    return True


def create_quality_measurement(
    db: Session,
    data: QualityMeasurementCreate,
) -> QualityMeasurement:
    process_event = get_process_event_by_id(
        db,
        data.process_event_id,
    )

    if process_event is None:
        raise ProcessEventNotFoundError(
            f"Process event '{data.process_event_id}' was not found"
        )

    existing_measurement = get_measurement_by_event_and_metric(
        db,
        data.process_event_id,
        data.metric_code,
    )

    if existing_measurement is not None:
        raise QualityMetricAlreadyExistsError(
            f"Metric '{data.metric_code}' already exists "
            f"for process event '{data.process_event_id}'"
        )

    is_within_spec = calculate_is_within_spec(
        data.value,
        data.lower_spec_limit,
        data.upper_spec_limit,
    )

    try:
        return repository_create(
            db,
            data,
            is_within_spec,
        )
    except IntegrityError as error:
        db.rollback()

        existing_measurement = (
            get_measurement_by_event_and_metric(
                db,
                data.process_event_id,
                data.metric_code,
            )
        )

        if existing_measurement is not None:
            raise QualityMetricAlreadyExistsError(
                f"Metric '{data.metric_code}' already exists "
                f"for process event '{data.process_event_id}'"
            ) from error

        raise


def get_quality_measurement(
    db: Session,
    measurement_id: UUID,
) -> QualityMeasurement:
    measurement = get_quality_measurement_by_id(
        db,
        measurement_id,
    )

    if measurement is None:
        raise QualityMeasurementNotFoundError(
            f"Quality measurement '{measurement_id}' "
            "was not found"
        )

    return measurement


def get_quality_measurements(
    db: Session,
    process_event_id: UUID | None = None,
    metric_code: str | None = None,
) -> list[QualityMeasurement]:
    if process_event_id is not None:
        process_event = get_process_event_by_id(
            db,
            process_event_id,
        )

        if process_event is None:
            raise ProcessEventNotFoundError(
                f"Process event '{process_event_id}' was not found"
            )

    return list_quality_measurements(
        db,
        process_event_id,
        metric_code,
    )