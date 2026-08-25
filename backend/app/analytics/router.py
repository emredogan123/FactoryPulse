from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics.schemas import AnalyticsOverview
from app.analytics.service import get_analytics_overview
from app.auth.dependencies import require_roles
from app.db.session import get_db
from app.models.user import User, UserRole


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