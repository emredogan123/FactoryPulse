from uuid import UUID
from app.analytics.quality import get_production_quality

from app.analytics.stage_quality import get_stage_quality

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    AnalyticsOverview,
    PCBRiskPredictionResponse,
    PCBRiskListResponse,
    ModelPerformanceResponse,
    ProductionQualityResponse,
    StageQualityResponse,
    DailyQualityResponse
)
from app.analytics.service import (
    get_analytics_overview,
    get_pcb_risk_prediction,
    get_pcb_risk_predictions,
)
from app.auth.dependencies import require_roles
from app.core.config import settings
from app.db.session import get_db
from app.ml.inference import ModelUnavailableError
from app.models.user import User, UserRole
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from app.ml.reporting import (
    ModelReportUnavailableError,
    load_model_performance_report,
)
from datetime import date

from app.analytics.daily_quality import get_daily_quality


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)


@router.get(
    "/overview",
    response_model=AnalyticsOverview,
)
def read_analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.QUALITY_ENGINEER,
            UserRole.VIEWER,
        )
    ),
) -> AnalyticsOverview:
    return get_analytics_overview(db)
@router.get(
    "/pcbs/{pcb_id}/risk",
    response_model=PCBRiskPredictionResponse,
)

def read_pcb_risk_prediction(
    pcb_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.QUALITY_ENGINEER,
            UserRole.VIEWER,
        )
    ),
) -> PCBRiskPredictionResponse:
    try:
        prediction = get_pcb_risk_prediction(
            db,
            pcb_id,
            settings.ml_model_path,
        )
    except ModelUnavailableError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail="ML model is unavailable",
        ) from error

    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PCB unit not found",
        )

    return prediction


@router.get(
    "/pcb-risks",
    response_model=PCBRiskListResponse,
)
def read_pcb_risk_predictions(
    prefix: str | None = None,
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.QUALITY_ENGINEER,
            UserRole.VIEWER,
        )
    ),
) -> PCBRiskListResponse:
    try:
        return get_pcb_risk_predictions(
            db,
            settings.ml_model_path,
            prefix,
            limit,
        )
    except ModelUnavailableError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail="ML model is unavailable",
        ) from error

@router.get(
    "/model-performance",
    response_model=ModelPerformanceResponse,
)
def read_model_performance(
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.QUALITY_ENGINEER,
            UserRole.VIEWER,
        )
    ),
) -> ModelPerformanceResponse:
    try:
        return load_model_performance_report(
            settings.ml_report_path
        )
    except ModelReportUnavailableError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "ML performance report "
                "is unavailable"
            ),
        ) from error


@router.get(
    "/production-quality",
    response_model=ProductionQualityResponse,
)
def read_production_quality(
    prefix: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.QUALITY_ENGINEER,
            UserRole.VIEWER,
        )
    ),
) -> ProductionQualityResponse:
    return get_production_quality(db, prefix)

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

@router.get(
    "/stage-quality",
    response_model=StageQualityResponse,
)
def read_stage_quality(
    prefix: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.QUALITY_ENGINEER,
            UserRole.VIEWER,
        )
    ),
) -> StageQualityResponse:
    return get_stage_quality(db, prefix)

@router.get(
    "/daily-quality",
    response_model=DailyQualityResponse,
)
def read_daily_quality(
    start_date: date = Query(...),
    end_date: date = Query(...),
    prefix: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.QUALITY_ENGINEER,
            UserRole.VIEWER,
        )
    ),
) -> DailyQualityResponse:
    number_of_days = (end_date - start_date).days + 1

    if not 1 <= number_of_days <= 366:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "Date range must contain between 1 and 366 days. "
                "end_date must not be earlier than start_date."
            ),
        )

    return get_daily_quality(
        db=db,
        start_date=start_date,
        end_date=end_date,
        prefix=prefix,
    )