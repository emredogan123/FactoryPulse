from uuid import UUID

from sqlalchemy.orm import Session

from app.models.material_lot import MaterialLot


def get_material_lot_by_id(
    db: Session,
    material_lot_id: UUID,
) -> MaterialLot | None:
    return db.get(
        MaterialLot,
        material_lot_id,
    )