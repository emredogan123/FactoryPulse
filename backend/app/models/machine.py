from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class MachineStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"


class StageType(str, Enum):
    SOLDER_PASTE_PRINTING = "SOLDER_PASTE_PRINTING"
    COMPONENT_PLACEMENT = "COMPONENT_PLACEMENT"
    REFLOW_SOLDERING = "REFLOW_SOLDERING"
    AOI_INSPECTION = "AOI_INSPECTION"
    FUNCTIONAL_TESTING = "FUNCTIONAL_TESTING"


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    machine_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    stage_type: Mapped[StageType] = mapped_column(
        SqlEnum(StageType, name="stage_type"),
        nullable=False,
    )

    status: Mapped[MachineStatus] = mapped_column(
        SqlEnum(MachineStatus, name="machine_status"),
        default=MachineStatus.ACTIVE,
        nullable=False,
    )

    commissioned_at: Mapped[datetime | None] = mapped_column(
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