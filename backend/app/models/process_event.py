from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.machine import Machine
    from app.models.pcb_unit import PCBUnit
    from app.models.quality_measurement import QualityMeasurement

class ProcessEventResult(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"


class ProcessEvent(Base):
    __tablename__ = "process_events"

    __table_args__ = (
        Index(
            "ix_process_events_pcb_started_at",
            "pcb_unit_id",
            "started_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    pcb_unit_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "pcb_units.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    machine_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "machines.id",
            ondelete="RESTRICT",
        ),
        index=True,
        nullable=False,
    )

    result: Mapped[ProcessEventResult] = mapped_column(
        SqlEnum(
            ProcessEventResult,
            name="process_event_result",
        ),
        default=ProcessEventResult.PENDING,
        nullable=False,
    )

    process_parameters: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
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

    pcb_unit: Mapped["PCBUnit"] = relationship(
        back_populates="process_events",
    )

    machine: Mapped["Machine"] = relationship(
        back_populates="process_events",
    )

    quality_measurements: Mapped[
        list["QualityMeasurement"]] = relationship(
        back_populates="process_event",
        cascade="all, delete-orphan",
    )