from uuid import UUID

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