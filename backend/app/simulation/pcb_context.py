from dataclasses import dataclass
from random import Random

from app.models.pcb_unit import ShiftType
from app.simulation.config import SimulationConfig


NORMAL_MATERIAL_LOT_CODES: tuple[str, ...] = (
    "LP-101",
    "LP-202",
    "LP-401",
)

PROBLEMATIC_MATERIAL_LOT_CODE = "LP-302"


@dataclass(frozen=True)
class GeneratedPCBContext:
    shift: ShiftType
    material_lot_code: str
    anomaly_probability: float


def choose_shift(
    random_generator: Random,
    config: SimulationConfig,
) -> ShiftType:
    if (
        random_generator.random()
        < config.night_shift_probability
    ):
        return ShiftType.NIGHT

    return ShiftType.DAY


def choose_material_lot_code(
    random_generator: Random,
    config: SimulationConfig,
) -> str:
    if (
        random_generator.random()
        < config.problematic_lot_probability
    ):
        return PROBLEMATIC_MATERIAL_LOT_CODE

    return random_generator.choice(
        NORMAL_MATERIAL_LOT_CODES
    )


def calculate_anomaly_probability(
    shift: ShiftType,
    material_lot_code: str,
    config: SimulationConfig,
) -> float:
    probability = config.anomaly_probability

    if shift == ShiftType.NIGHT:
        probability += (
            config.night_anomaly_increase
        )

    if (
        material_lot_code
        == PROBLEMATIC_MATERIAL_LOT_CODE
    ):
        probability += (
            config.problematic_lot_anomaly_increase
        )

    return round(
        min(max(probability, 0.0), 1.0),
        4,
    )


def generate_pcb_context(
    random_generator: Random,
    config: SimulationConfig,
) -> GeneratedPCBContext:
    shift = choose_shift(
        random_generator,
        config,
    )

    material_lot_code = (
        choose_material_lot_code(
            random_generator,
            config,
        )
    )

    anomaly_probability = (
        calculate_anomaly_probability(
            shift,
            material_lot_code,
            config,
        )
    )

    return GeneratedPCBContext(
        shift=shift,
        material_lot_code=material_lot_code,
        anomaly_probability=anomaly_probability,
    )