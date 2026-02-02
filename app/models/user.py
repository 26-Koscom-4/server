from datetime import datetime, time
from decimal import Decimal
from typing import Optional
from sqlalchemy import CHAR, VARCHAR, DATETIME, TIME, DECIMAL, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    profile_image_url: Mapped[Optional[str]] = mapped_column(VARCHAR(500), nullable=True)
    theme: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, default="light")

    # Relationships
    settings: Mapped["UserSettings"] = relationship("UserSettings", back_populates="user", uselist=False)
    villages: Mapped[list["Village"]] = relationship("Village", back_populates="user")
    briefings: Mapped[list["Briefing"]] = relationship("Briefing", back_populates="user")
    risk_profile: Mapped["RiskProfile"] = relationship("RiskProfile", back_populates="user", uselist=False)
    neighbor_recommendations: Mapped[list["NeighborRecommendation"]] = relationship(
        "NeighborRecommendation", back_populates="user"
    )


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    briefing_time: Mapped[time] = mapped_column(TIME, nullable=False, default=time(8, 0, 0))
    tts_speed: Mapped[Decimal] = mapped_column(DECIMAL(3, 2), nullable=False)
    timezone: Mapped[str] = mapped_column(VARCHAR(50), nullable=False, default="Asia/Seoul")
    updated_at: Mapped[datetime] = mapped_column(DATETIME, nullable=False, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="settings")
