from app.models.machine import StageType
from app.simulation.config import SimulationConfig
from app.simulation.profiles import (
    STAGE_ORDER,
    STAGE_PROFILES,
)


def test_all_machine_stages_have_profiles() -> None:
    assert set(STAGE_PROFILES) == set(StageType)
    assert set(STAGE_ORDER) == set(StageType)


def test_normal_means_are_inside_spec_limits() -> None:
    for stage_profile in STAGE_PROFILES.values():
        for metric in stage_profile.metrics:
            if metric.lower_spec_limit is not None:
                assert (
                    metric.normal_mean
                    >= metric.lower_spec_limit
                )

            if metric.upper_spec_limit is not None:
                assert (
                    metric.normal_mean
                    <= metric.upper_spec_limit
                )


def test_metric_codes_are_unique_in_each_stage() -> None:
    for stage_profile in STAGE_PROFILES.values():
        metric_codes = [
            metric.metric_code
            for metric in stage_profile.metrics
        ]

        assert len(metric_codes) == len(set(metric_codes))


def test_default_simulation_creates_150_pcbs() -> None:
    config = SimulationConfig()

    assert config.total_pcb_count == 150