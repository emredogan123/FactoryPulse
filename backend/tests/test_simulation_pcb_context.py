from random import Random

from app.models.pcb_unit import ShiftType
from app.simulation.config import SimulationConfig
from app.simulation.pcb_context import (
    PROBLEMATIC_MATERIAL_LOT_CODE,
    calculate_anomaly_probability,
    generate_pcb_context,
)


def test_day_normal_lot_uses_base_probability() -> None:
    config = SimulationConfig()

    probability = calculate_anomaly_probability(
        shift=ShiftType.DAY,
        material_lot_code="LP-101",
        config=config,
    )

    assert probability == 0.12


def test_night_problematic_lot_increases_probability() -> None:
    config = SimulationConfig()

    probability = calculate_anomaly_probability(
        shift=ShiftType.NIGHT,
        material_lot_code=(
            PROBLEMATIC_MATERIAL_LOT_CODE
        ),
        config=config,
    )

    assert probability == 0.34


def test_context_generation_is_reproducible() -> None:
    first_generator = Random(42)
    second_generator = Random(42)
    config = SimulationConfig()

    first_contexts = [
        generate_pcb_context(
            first_generator,
            config,
        )
        for _ in range(20)
    ]

    second_contexts = [
        generate_pcb_context(
            second_generator,
            config,
        )
        for _ in range(20)
    ]

    assert first_contexts == second_contexts


def test_forced_probabilities_generate_expected_context() -> None:
    config = SimulationConfig(
        night_shift_probability=1.0,
        problematic_lot_probability=1.0,
    )

    context = generate_pcb_context(
        Random(42),
        config,
    )

    assert context.shift == ShiftType.NIGHT
    assert (
        context.material_lot_code
        == PROBLEMATIC_MATERIAL_LOT_CODE
    )
    assert context.anomaly_probability == 0.34