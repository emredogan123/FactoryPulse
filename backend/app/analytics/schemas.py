from pydantic import BaseModel


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