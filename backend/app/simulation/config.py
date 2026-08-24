from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class SimulationConfig:
    data_prefix: str = "DEMO"
    random_seed: int = 42
    order_count: int = 3
    pcb_per_order: int = 50
    anomaly_probability: float = 0.12
    warning_probability: float = 0.60
    stage_duration_minutes: int = 5
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
        return self.order_count * self.pcb_per_order