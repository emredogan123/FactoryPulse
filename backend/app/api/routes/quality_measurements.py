from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.quality_measurement import (
    METRIC_CODE_PATTERN,
    QualityMeasurementCreate,
    QualityMeasurementResponse,
)
from app.services.process_event import (
    ProcessEventNotFoundError,
)
from app.services.quality_measurement import (
    QualityMeasurementNotFoundError,
    QualityMetricAlreadyExistsError,
    create_quality_measurement,
    get_quality_measurement,
    get_quality_measurements,
)


router = APIRouter(
    prefix="/api/v1/quality-measurements",
    tags=["Quality Measurements"],
)


@router.post(
    "",
    response_model=QualityMeasurementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_measurement_endpoint(
    data: QualityMeasurementCreate,
    db: Session = Depends(get_db),
) -> QualityMeasurementResponse:
    try:
        return create_quality_measurement(
            db,
            data,
        )
    except ProcessEventNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except QualityMetricAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=list[QualityMeasurementResponse],
)
def list_quality_measurements_endpoint(
    process_event_id: UUID | None = None,
    metric_code: str | None = Query(
        default=None,
        min_length=2,
        max_length=80,
        pattern=METRIC_CODE_PATTERN,
    ),
    db: Session = Depends(get_db),
) -> list[QualityMeasurementResponse]:
    try:
        return get_quality_measurements(
            db,
            process_event_id,
            metric_code,
        )
    except ProcessEventNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.get(
    "/{measurement_id}",
    response_model=QualityMeasurementResponse,
)
def get_quality_measurement_endpoint(
    measurement_id: UUID,
    db: Session = Depends(get_db),
) -> QualityMeasurementResponse:
    try:
        return get_quality_measurement(
            db,
            measurement_id,
        )
    except QualityMeasurementNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error