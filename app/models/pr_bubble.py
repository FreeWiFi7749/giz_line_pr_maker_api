import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TagType(str, enum.Enum):
    GIZMART = "gizmart"
    CUSTOM = "custom"


class PRStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"


class PRBubble(Base):
    __tablename__ = "pr_bubbles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    link_url: Mapped[str] = mapped_column(String(500), nullable=False)

    tag_type: Mapped[TagType] = mapped_column(
        Enum(TagType, native_enum=False),
        default=TagType.GIZMART,
        nullable=False,
    )
    tag_text: Mapped[str] = mapped_column(String(50), default="GIZMART", nullable=False)
    tag_color: Mapped[str] = mapped_column(String(7), default="#FF1BE8", nullable=False)

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    priority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    status: Mapped[PRStatus] = mapped_column(
        Enum(PRStatus, native_enum=False),
        default=PRStatus.DRAFT,
        nullable=False,
    )

    utm_campaign: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    click_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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

    __table_args__ = (
        Index("idx_status_dates", "status", "start_date", "end_date"),
        Index("idx_priority", "priority"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<PRBubble(id={self.id}, title={self.title}, status={self.status})>"
