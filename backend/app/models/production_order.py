from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Integer
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.session import Base
if TYPE_CHECKING:
    from app.models.pcb_unit import PCBUnit

class ProductionOrderStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ProductionOrder(Base):
    __tablename__ = "production_orders"

    __table_args__ = (
        CheckConstraint(
            "target_quantity > 0",
            name="ck_production_orders_target_quantity_positive",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    order_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    product_code: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )

    target_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[ProductionOrderStatus] = mapped_column(
        SqlEnum(
            ProductionOrderStatus,
            name="production_order_status",
        ),
        default=ProductionOrderStatus.PLANNED,
        nullable=False,
    )

    planned_start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    planned_end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    actual_start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    actual_end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    pcb_units: Mapped[list["PCBUnit"]] = relationship(
        back_populates="production_order",
        cascade="all, delete-orphan",
    )