from pydantic import BaseModel
from enum import Enum
from uuid import UUID
from app.models.pcb_unit import PCBUnitStatus

class PCBStatusCounts(BaseModel):
    passed: int
    failed: int
    rework: int
    queued: int


class AnalyticsOverview(BaseModel):
    production_order_count: int
    pcb_count: int
    pcb_status_counts: PCBStatusCounts
    pass_rate: float
    failure_rate: float
    rework_rate: float
    process_event_count: int
    quality_measurement_count: int
    out_of_spec_measurement_count: int

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class PCBRiskPredictionResponse(BaseModel):
    pcb_id: UUID
    serial_number: str
    actual_status: PCBUnitStatus
    issue_probability: float
    decision_threshold: float
    predicted_issue: bool
    risk_level: RiskLevel
    model_type: str

class PCBRiskListResponse(BaseModel):
    total_analyzed: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    items: list[PCBRiskPredictionResponse]