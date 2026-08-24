from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics.schemas import AnalyticsOverview
from app.analytics.service import get_analytics_overview
from app.db.session import get_db


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
) -> AnalyticsOverview:
    return get_analytics_overview(db)