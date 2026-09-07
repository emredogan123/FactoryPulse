from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field


class QualityAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_code: str
    dataset_prefix: str
    quality_date: date
    evaluated_count: int
    issue_count: int
    threshold_percent: float
    minimum_count: int
    created_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by_id: UUID | None

    @computed_field
    @property
    def issue_rate(self) -> float:
        return round(
            100 * self.issue_count / self.evaluated_count,
            2,
        )


class QualityAlertListResponse(BaseModel):
    items: list[QualityAlertResponse]
    limit: int
    offset: int