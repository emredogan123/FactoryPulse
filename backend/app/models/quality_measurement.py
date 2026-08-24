from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.process_event import ProcessEvent


class QualityMeasurement(Base):
    __tablename__ = "quality_measurements"

    __table_args__ = (
        UniqueConstraint(
            "process_event_id",
            "metric_code",
            name="uq_quality_measurements_event_metric",
        ),
        CheckConstraint(
            """
            lower_spec_limit IS NULL
            OR upper_spec_limit IS NULL
            OR lower_spec_limit <= upper_spec_limit
            """,
            name="ck_quality_measurements_spec_limits",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    process_event_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "process_events.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    metric_code: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    lower_spec_limit: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    upper_spec_limit: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    is_within_spec: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    process_event: Mapped["ProcessEvent"] = relationship(
        back_populates="quality_measurements",
    )