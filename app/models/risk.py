from datetime import datetime
from typing import Optional
from sqlalchemy import CHAR, VARCHAR, DATETIME, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id"), primary_key=True)
    risk_type: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DATETIME, nullable=False, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="risk_profile")
