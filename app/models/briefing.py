from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import CHAR, VARCHAR, DATETIME, TEXT, DECIMAL, Index, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TimeSlot(str, PyEnum):
    MORNING = "morning"
    EVENING = "evening"


class TargetScope(str, PyEnum):
    ALL_VILLAGES = "all_villages"
    SINGLE_VILLAGE = "single_village"


class Briefing(Base):
    __tablename__ = "briefings"
    __table_args__ = (
        Index("idx_briefings_user_time", "user_id", "time_slot"),
        Index("idx_briefings_village", "village_id"),
    )

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id"), nullable=False)
    time_slot: Mapped[TimeSlot] = mapped_column(
        Enum(TimeSlot, native_enum=False, length=20), nullable=False
    )
    target_scope: Mapped[TargetScope] = mapped_column(
        Enum(TargetScope, native_enum=False, length=20), nullable=False, default=TargetScope.ALL_VILLAGES
    )
    village_id: Mapped[Optional[str]] = mapped_column(CHAR(36), ForeignKey("villages.id"), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(VARCHAR(100), nullable=True)
    content: Mapped[str] = mapped_column(TEXT, nullable=False)
    tts_audio_url: Mapped[Optional[str]] = mapped_column(VARCHAR(500), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DATETIME, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DATETIME, nullable=False, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="briefings")
    village: Mapped["Village"] = relationship("Village", back_populates="briefings")
    news_items: Mapped[list["NewsItem"]] = relationship(
        "NewsItem", secondary="briefing_news_links", back_populates="briefings"
    )


class BriefingNewsLink(Base):
    __tablename__ = "briefing_news_links"
    __table_args__ = (Index("idx_briefing_news_news", "news_item_id"),)

    briefing_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("briefings.id"), primary_key=True
    )
    news_item_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("news_items.id"), primary_key=True
    )
    relevance_score: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(4, 3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME, nullable=False, default=datetime.utcnow)
