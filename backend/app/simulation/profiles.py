from dataclasses import dataclass
from typing import Literal

from app.models.machine import StageType


AnomalyDirection = Literal["LOW", "HIGH"]


@dataclass(frozen=True)
class MetricProfile:
    metric_code: str
    unit: str
    normal_mean: float
    normal_standard_deviation: float
    lower_spec_limit: float | None
    upper_spec_limit: float | None
    anomaly_direction: AnomalyDirection


@dataclass(frozen=True)
class StageProfile:
    stage_type: StageType
    metrics: tuple[MetricProfile, ...]


STAGE_ORDER: tuple[StageType, ...] = (
    StageType.SOLDER_PASTE_PRINTING,
    StageType.COMPONENT_PLACEMENT,
    StageType.REFLOW_SOLDERING,
    StageType.AOI_INSPECTION,
    StageType.FUNCTIONAL_TESTING,
)


STAGE_PROFILES: dict[StageType, StageProfile] = {
    StageType.SOLDER_PASTE_PRINTING: StageProfile(
        stage_type=StageType.SOLDER_PASTE_PRINTING,
        metrics=(
            MetricProfile(
                metric_code="PASTE_THICKNESS",
                unit="MICROMETER",
                normal_mean=125.0,
                normal_standard_deviation=6.0,
                lower_spec_limit=105.0,
                upper_spec_limit=145.0,
                anomaly_direction="LOW",
            ),
            MetricProfile(
                metric_code="PASTE_COVERAGE",
                unit="PERCENT",
                normal_mean=96.0,
                normal_standard_deviation=1.5,
                lower_spec_limit=90.0,
                upper_spec_limit=100.0,
                anomaly_direction="LOW",
            ),
        ),
    ),
    StageType.COMPONENT_PLACEMENT: StageProfile(
        stage_type=StageType.COMPONENT_PLACEMENT,
        metrics=(
            MetricProfile(
                metric_code="PLACEMENT_OFFSET_X",
                unit="MILLIMETER",
                normal_mean=0.0,
                normal_standard_deviation=0.03,
                lower_spec_limit=-0.10,
                upper_spec_limit=0.10,
                anomaly_direction="HIGH",
            ),
            MetricProfile(
                metric_code="PLACEMENT_OFFSET_Y",
                unit="MILLIMETER",
                normal_mean=0.0,
                normal_standard_deviation=0.03,
                lower_spec_limit=-0.10,
                upper_spec_limit=0.10,
                anomaly_direction="LOW",
            ),
        ),
    ),
    StageType.REFLOW_SOLDERING: StageProfile(
        stage_type=StageType.REFLOW_SOLDERING,
        metrics=(
            MetricProfile(
                metric_code="PEAK_TEMPERATURE",
                unit="CELSIUS",
                normal_mean=243.0,
                normal_standard_deviation=2.5,
                lower_spec_limit=235.0,
                upper_spec_limit=250.0,
                anomaly_direction="HIGH",
            ),
            MetricProfile(
                metric_code="TIME_ABOVE_LIQUIDUS",
                unit="SECOND",
                normal_mean=60.0,
                normal_standard_deviation=5.0,
                lower_spec_limit=45.0,
                upper_spec_limit=75.0,
                anomaly_direction="LOW",
            ),
        ),
    ),
    StageType.AOI_INSPECTION: StageProfile(
        stage_type=StageType.AOI_INSPECTION,
        metrics=(
            MetricProfile(
                metric_code="DEFECT_SCORE",
                unit="SCORE",
                normal_mean=0.10,
                normal_standard_deviation=0.05,
                lower_spec_limit=0.0,
                upper_spec_limit=0.35,
                anomaly_direction="HIGH",
            ),
            MetricProfile(
                metric_code="SOLDER_JOINT_COVERAGE",
                unit="PERCENT",
                normal_mean=96.0,
                normal_standard_deviation=1.5,
                lower_spec_limit=90.0,
                upper_spec_limit=100.0,
                anomaly_direction="LOW",
            ),
        ),
    ),
    StageType.FUNCTIONAL_TESTING: StageProfile(
        stage_type=StageType.FUNCTIONAL_TESTING,
        metrics=(
            MetricProfile(
                metric_code="OUTPUT_VOLTAGE",
                unit="VOLT",
                normal_mean=5.0,
                normal_standard_deviation=0.04,
                lower_spec_limit=4.85,
                upper_spec_limit=5.15,
                anomaly_direction="LOW",
            ),
            MetricProfile(
                metric_code="CURRENT_DRAW",
                unit="MILLIAMPERE",
                normal_mean=100.0,
                normal_standard_deviation=4.0,
                lower_spec_limit=90.0,
                upper_spec_limit=110.0,
                anomaly_direction="HIGH",
            ),
        ),
    ),
}