from random import Random

from app.simulation.generator import (
    calculate_reflow_thermal_stress_index,
    generate_stage_observation,
)
from app.simulation.profiles import STAGE_ORDER
from app.models.machine import StageType

def test_normal_observations_are_inside_spec() -> None:
    random_generator = Random(42)

    for stage_type in STAGE_ORDER:
        for _ in range(20):
            observation = generate_stage_observation(
                random_generator,
                stage_type,
                is_anomalous=False,
            )

            assert all(
                measurement.is_within_spec
                for measurement in observation.measurements
            )


def test_anomalous_observations_have_out_of_spec_metric() -> None:
    random_generator = Random(42)

    for stage_type in STAGE_ORDER:
        observation = generate_stage_observation(
            random_generator,
            stage_type,
            is_anomalous=True,
        )

        assert any(
            not measurement.is_within_spec
            for measurement in observation.measurements
        )


def test_generation_is_reproducible() -> None:
    first_generator = Random(42)
    second_generator = Random(42)

    first_observation = generate_stage_observation(
        first_generator,
        STAGE_ORDER[0],
        is_anomalous=True,
    )

    second_observation = generate_stage_observation(
        second_generator,
        STAGE_ORDER[0],
        is_anomalous=True,
    )

    assert first_observation == second_observation

def test_reflow_interaction_requires_both_parameters() -> None:
    normal_score = (
        calculate_reflow_thermal_stress_index(
            {
                "oven_setpoint_c": 243.0,
                "conveyor_speed_m_min": 0.9,
            }
        )
    )

    temperature_only_score = (
        calculate_reflow_thermal_stress_index(
            {
                "oven_setpoint_c": 248.0,
                "conveyor_speed_m_min": 0.9,
            }
        )
    )

    combined_score = (
        calculate_reflow_thermal_stress_index(
            {
                "oven_setpoint_c": 248.0,
                "conveyor_speed_m_min": 1.0,
            }
        )
    )

    assert normal_score == 0.0
    assert temperature_only_score == 0.0
    assert combined_score == 4.0


def test_anomalous_reflow_has_higher_thermal_stress() -> None:
    normal_observation = generate_stage_observation(
        Random(42),
        StageType.REFLOW_SOLDERING,
        is_anomalous=False,
    )

    anomalous_observation = generate_stage_observation(
        Random(42),
        StageType.REFLOW_SOLDERING,
        is_anomalous=True,
    )

    normal_score = (
        normal_observation.process_parameters[
            "thermal_stress_index"
        ]
    )

    anomalous_score = (
        anomalous_observation.process_parameters[
            "thermal_stress_index"
        ]
    )

    assert anomalous_score > normal_score