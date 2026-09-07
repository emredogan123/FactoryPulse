from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class QualityAlert(Base):
    __tablename__ = "quality_alerts"

    __table_args__ = (
        UniqueConstraint(
            "rule_code",
            "dataset_prefix",
            "quality_date",
            name="uq_quality_alert_rule_dataset_date",
        ),
        CheckConstraint(
            "evaluated_count > 0",
            name="ck_quality_alert_evaluated_positive",
        ),
        CheckConstraint(
            "issue_count >= 0 AND issue_count <= evaluated_count",
            name="ck_quality_alert_issue_count",
        ),
        CheckConstraint(
            "threshold_percent >= 0 AND threshold_percent <= 100",
            name="ck_quality_alert_threshold",
        ),
        CheckConstraint(
            "minimum_count > 0",
            name="ck_quality_alert_minimum_positive",
        ),
        CheckConstraint(
            "acknowledged_by_id IS NULL OR acknowledged_at IS NOT NULL",
            name="ck_quality_alert_acknowledgement",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    rule_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Boş metin, tüm veri gruplarını ifade eder.
    # NULL kullanılmaması benzersizlik kontrolünü korur.
    dataset_prefix: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    quality_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    evaluated_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    issue_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    threshold_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    minimum_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    acknowledged_by_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )