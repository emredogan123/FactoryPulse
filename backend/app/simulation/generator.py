from dataclasses import dataclass
from random import Random

from app.models.machine import StageType
from app.simulation.profiles import (
    MetricProfile,
    STAGE_PROFILES,
)


@dataclass(frozen=True)
class ParameterProfile:
    parameter_name: str
    normal_mean: float
    normal_standard_deviation: float
    drift_sensitivity: float


@dataclass(frozen=True)
class GeneratedMetric:
    metric_code: str
    unit: str
    value: float
    lower_spec_limit: float | None
    upper_spec_limit: float | None
    is_within_spec: bool


@dataclass(frozen=True)
class GeneratedStageObservation:
    stage_type: StageType
    drift_score: float
    is_anomalous: bool
    process_parameters: dict[str, float]
    measurements: tuple[GeneratedMetric, ...]


PARAMETER_PROFILES: dict[
    StageType,
    tuple[ParameterProfile, ...],
] = {
    StageType.SOLDER_PASTE_PRINTING: (
        ParameterProfile(
            "squeegee_pressure_n",
            40.0,
            2.0,
            -1.0,
        ),
        ParameterProfile(
            "print_speed_mm_s",
            50.0,
            3.0,
            1.0,
        ),
    ),
    StageType.COMPONENT_PLACEMENT: (
        ParameterProfile(
            "placement_speed_cph",
            20000.0,
            1000.0,
            1.0,
        ),
        ParameterProfile(
            "nozzle_vacuum_kpa",
            70.0,
            3.0,
            -1.0,
        ),
    ),
    StageType.REFLOW_SOLDERING: (
        ParameterProfile(
            "oven_setpoint_c",
            243.0,
            2.5,
            1.0,
        ),
        ParameterProfile(
            "conveyor_speed_m_min",
            0.9,
            0.05,
            1.0,
        ),
    ),
    StageType.AOI_INSPECTION: (
        ParameterProfile(
            "camera_exposure_ms",
            8.0,
            0.5,
            -1.0,
        ),
        ParameterProfile(
            "inspection_speed_mm_s",
            100.0,
            5.0,
            1.0,
        ),
    ),
    StageType.FUNCTIONAL_TESTING: (
        ParameterProfile(
            "supply_voltage_v",
            5.0,
            0.04,
            -1.0,
        ),
        ParameterProfile(
            "test_load_ma",
            100.0,
            4.0,
            1.0,
        ),
    ),
}

def calculate_reflow_thermal_stress_index(
    process_parameters: dict[str, float],
) -> float:
    oven_setpoint = process_parameters[
        "oven_setpoint_c"
    ]

    conveyor_speed = process_parameters[
        "conveyor_speed_m_min"
    ]

    temperature_deviation = max(
        0.0,
        (oven_setpoint - 243.0) / 2.5,
    )

    conveyor_deviation = max(
        0.0,
        (conveyor_speed - 0.9) / 0.05,
    )

    return round(
        temperature_deviation
        * conveyor_deviation,
        4,
    )

def is_within_spec(
    value: float,
    lower_spec_limit: float | None,
    upper_spec_limit: float | None,
) -> bool:
    if (
        lower_spec_limit is not None
        and value < lower_spec_limit
    ):
        return False

    if (
        upper_spec_limit is not None
        and value > upper_spec_limit
    ):
        return False

    return True


def generate_process_parameters(
    random_generator: Random,
    stage_type: StageType,
    drift_score: float,
) -> dict[str, float]:
    generated_parameters: dict[str, float] = {}

    for profile in PARAMETER_PROFILES[stage_type]:
        noise = random_generator.gauss(0.0, 0.25)

        value = profile.normal_mean + (
            profile.normal_standard_deviation
            * (
                profile.drift_sensitivity * drift_score
                + noise
            )
        )

        generated_parameters[profile.parameter_name] = round(
            value,
            4,
        )
    if stage_type == StageType.REFLOW_SOLDERING:
        generated_parameters[
            "thermal_stress_index"
        ] = calculate_reflow_thermal_stress_index(
            generated_parameters
        )
    return generated_parameters


def generate_metric(
    random_generator: Random,
    profile: MetricProfile,
    drift_score: float,
) -> GeneratedMetric:
    direction = (
        1.0
        if profile.anomaly_direction == "HIGH"
        else -1.0
    )

    noise = random_generator.gauss(0.0, 0.25)

    value = profile.normal_mean + (
        profile.normal_standard_deviation
        * (
            direction * drift_score
            + noise
        )
    )

    value = round(value, 4)

    return GeneratedMetric(
        metric_code=profile.metric_code,
        unit=profile.unit,
        value=value,
        lower_spec_limit=profile.lower_spec_limit,
        upper_spec_limit=profile.upper_spec_limit,
        is_within_spec=is_within_spec(
            value,
            profile.lower_spec_limit,
            profile.upper_spec_limit,
        ),
    )


def force_metric_outside_spec(
    profile: MetricProfile,
) -> GeneratedMetric:
    distance = max(
        profile.normal_standard_deviation,
        0.01,
    )

    if (
        profile.anomaly_direction == "HIGH"
        and profile.upper_spec_limit is not None
    ):
        value = profile.upper_spec_limit + distance
    elif (
        profile.anomaly_direction == "LOW"
        and profile.lower_spec_limit is not None
    ):
        value = profile.lower_spec_limit - distance
    else:
        raise ValueError(
            f"Metric '{profile.metric_code}' does not have "
            "a suitable specification limit"
        )

    return GeneratedMetric(
        metric_code=profile.metric_code,
        unit=profile.unit,
        value=round(value, 4),
        lower_spec_limit=profile.lower_spec_limit,
        upper_spec_limit=profile.upper_spec_limit,
        is_within_spec=False,
    )


def generate_stage_observation(
    random_generator: Random,
    stage_type: StageType,
    is_anomalous: bool,
) -> GeneratedStageObservation:
    if is_anomalous:
        drift_score = random_generator.uniform(
            3.3,
            4.2,
        )
    else:
        drift_score = random_generator.gauss(
            0.0,
            0.35,
        )

    process_parameters = generate_process_parameters(
        random_generator,
        stage_type,
        drift_score,
    )

    stage_profile = STAGE_PROFILES[stage_type]

    measurements = [
        generate_metric(
            random_generator,
            metric_profile,
            drift_score,
        )
        for metric_profile in stage_profile.metrics
    ]

    if (
        is_anomalous
        and all(
            measurement.is_within_spec
            for measurement in measurements
        )
    ):
        measurements[0] = force_metric_outside_spec(
            stage_profile.metrics[0]
        )

    return GeneratedStageObservation(
    stage_type=stage_type,
    drift_score=round(drift_score, 4),
    is_anomalous=is_anomalous,
    process_parameters=process_parameters,
    measurements=tuple(measurements),
)