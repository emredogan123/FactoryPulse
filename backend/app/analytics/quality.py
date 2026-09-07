from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    MaterialLotQualityItem,
    ProductionQualityResponse,
    QualityCounts,
    ShiftQualityItem,
)
from app.models.material_lot import MaterialLot
from app.models.pcb_unit import (
    PCBUnit,
    PCBUnitStatus,
    ShiftType,
)


def build_quality_counts(
    total: int,
    passed: int,
    failed: int,
    rework: int,
) -> QualityCounts:
    evaluated = passed + failed + rework
    issues = failed + rework

    return QualityCounts(
        total_count=total,
        evaluated_count=evaluated,
        pending_count=total - evaluated,
        passed_count=passed,
        failed_count=failed,
        rework_count=rework,
        issue_count=issues,
        issue_rate=(
            round(100 * issues / evaluated, 2)
            if evaluated
            else None
        ),
    )


def get_production_quality(
    db: Session,
    prefix: str | None = None,
) -> ProductionQualityResponse:
    statement = (
        select(
            PCBUnit.shift,
            PCBUnit.material_lot_id,
            MaterialLot.lot_code,
            PCBUnit.status,
            func.count(PCBUnit.id),
        )
        .select_from(PCBUnit)
        .outerjoin(
            MaterialLot,
            MaterialLot.id == PCBUnit.material_lot_id,
        )
        .group_by(
            PCBUnit.shift,
            PCBUnit.material_lot_id,
            MaterialLot.lot_code,
            PCBUnit.status,
        )
    )

    if prefix:
        statement = statement.where(
            PCBUnit.serial_number.startswith(
                f"{prefix}-",
                autoescape=True,
            )
        )

    rows = db.execute(statement).all()

    # Each bucket contains: total, passed, failed, rework.
    summary = [0, 0, 0, 0]
    shifts = {
        shift: [0, 0, 0, 0]
        for shift in ShiftType
    }
    lots = {}

    status_positions = {
        PCBUnitStatus.PASSED: 1,
        PCBUnitStatus.FAILED: 2,
        PCBUnitStatus.REWORK: 3,
    }

    for shift, lot_id, lot_code, pcb_status, count in rows:
        lot_key = (lot_id, lot_code)
        lot_counts = lots.setdefault(
            lot_key,
            [0, 0, 0, 0],
        )

        for bucket in (summary, shifts[shift], lot_counts):
            bucket[0] += count

            position = status_positions.get(pcb_status)
            if position is not None:
                bucket[position] += count

    shift_items = [
        ShiftQualityItem(
            shift=shift.value,
            **build_quality_counts(*counts).model_dump(),
        )
        for shift, counts in shifts.items()
    ]

    lot_items = [
        MaterialLotQualityItem(
            material_lot_id=lot_id,
            lot_code=lot_code,
            **build_quality_counts(*counts).model_dump(),
        )
        for (lot_id, lot_code), counts in lots.items()
    ]

    # Highest issue rate first; groups without results last.
    lot_items.sort(
        key=lambda item: (
            item.issue_rate is None,
            -(item.issue_rate or 0),
            item.lot_code or "",
        )
    )

    return ProductionQualityResponse(
        prefix=prefix,
        summary=build_quality_counts(*summary),
        shifts=shift_items,
        material_lots=lot_items,
    )