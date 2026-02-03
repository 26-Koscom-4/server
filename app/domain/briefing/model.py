from sqlalchemy import BigInteger, Enum, JSON, Index, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.common.model import Base


class BriefingSnapshot(Base):
    __tablename__ = "briefing_snapshots"
    __table_args__ = (
        Index("idx_briefing_user", "user_id"),
        Index("idx_briefing_village", "village_id"),
        Index("idx_briefing_latest", "user_id", "village_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    village_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    time_slot: Mapped[str] = mapped_column(
        Enum("morning", "evening", name="briefing_time_slot"),
        nullable=False,
    )
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.current_timestamp()
    )


__all__ = ["BriefingSnapshot"]
