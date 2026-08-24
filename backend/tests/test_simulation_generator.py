from random import Random

from app.simulation.generator import (
    generate_stage_observation,
)
from app.simulation.profiles import STAGE_ORDER


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