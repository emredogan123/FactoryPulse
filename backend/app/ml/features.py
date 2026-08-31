from typing import Any

from app.models.pcb_unit import PCBUnit


def normalize_feature_name(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def convert_feature_value(value: Any) -> Any:
    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (str, int, float)) or value is None:
        return value

    return str(value)


def build_pcb_feature_row(
    pcb: PCBUnit,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "pcb_id": str(pcb.id),
        "serial_number": pcb.serial_number,
        "shift": pcb.shift.value,
        "material_lot_code": (
            pcb.material_lot.lot_code
            if pcb.material_lot
            else ""
        ),
        "material_type": (
            pcb.material_lot.material_type
            if pcb.material_lot
            else ""
        ),
        "supplier_code": (
            pcb.material_lot.supplier_code
            if pcb.material_lot
            else ""
        ),
    }

    for event in pcb.process_events:
        stage = normalize_feature_name(
            event.machine.stage_type.value
        )

        for parameter_name, value in (
            event.process_parameters.items()
        ):
            parameter = normalize_feature_name(
                parameter_name
            )

            row[
                f"{stage}__param__{parameter}"
            ] = convert_feature_value(value)

    return row