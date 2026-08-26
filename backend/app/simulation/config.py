from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.machine import StageType


@dataclass(frozen=True)
class SimulationConfig:
    data_prefix: str = "DEMO"
    random_seed: int = 42
    order_count: int = 3
    pcb_per_order: int = 50

    anomaly_probability: float = 0.12
    warning_probability: float = 0.60

    night_shift_probability: float = 0.25
    problematic_lot_probability: float = 0.15

    night_anomaly_increase: float = 0.04
    problematic_lot_anomaly_increase: float = 0.18

    degradation_start_ratio: float = 0.60
    degradation_anomaly_increase: float = 0.16
    degrading_stage: StageType = (
        StageType.REFLOW_SOLDERING
    )

    stage_duration_minutes: int = 5
    flush_batch_size: int = 500

    simulation_start: datetime = datetime(
        2026,
        8,
        1,
        6,
        0,
        tzinfo=timezone.utc,
    )

    @property
    def total_pcb_count(self) -> int:
        return (
            self.order_count
            * self.pcb_per_order
        )