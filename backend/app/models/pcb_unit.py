from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.material_lot import MaterialLot
    from app.models.process_event import ProcessEvent
    from app.models.production_order import ProductionOrder

class ShiftType(str, Enum):
    DAY = "DAY"
    NIGHT = "NIGHT"

class PCBUnitStatus(str, Enum):
    QUEUED = "QUEUED"
    IN_PRODUCTION = "IN_PRODUCTION"
    PASSED = "PASSED"
    FAILED = "FAILED"
    REWORK = "REWORK"


class PCBUnit(Base):
    __tablename__ = "pcb_units"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    serial_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    production_order_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "production_orders.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    material_lot_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "material_lots.id",
            ondelete="SET NULL",
        ),
        index=True,
        nullable=True,
    )

    shift: Mapped[ShiftType] = mapped_column(
        SqlEnum(
            ShiftType,
            name="shift_type",
        ),
        default=ShiftType.DAY,
        server_default=ShiftType.DAY.value,
        nullable=False,
    )    

    status: Mapped[PCBUnitStatus] = mapped_column(
        SqlEnum(
            PCBUnitStatus,
            name="pcb_unit_status",
        ),
        default=PCBUnitStatus.QUEUED,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    production_order: Mapped["ProductionOrder"] = relationship(
        back_populates="pcb_units",
    )

    material_lot: Mapped[
        "MaterialLot | None"
    ] = relationship(
        back_populates="pcb_units",
    )    

    process_events: Mapped[list["ProcessEvent"]] = relationship(
        back_populates="pcb_unit",
        cascade="all, delete-orphan",
    )