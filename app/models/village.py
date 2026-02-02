from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import CHAR, VARCHAR, DATETIME, DATE, BIGINT, DECIMAL, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Village(Base, TimestampMixin):
    __tablename__ = "villages"
    __table_args__ = (Index("idx_villages_user", "user_id"),)

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    icon: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    type: Mapped[Optional[str]] = mapped_column(VARCHAR(30), nullable=True)
    goal: Mapped[Optional[str]] = mapped_column(VARCHAR(200), nullable=True)
    last_briefing_read: Mapped[Optional[datetime]] = mapped_column(DATETIME, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="villages")
    metrics: Mapped[list["VillageMetricsDaily"]] = relationship("VillageMetricsDaily", back_populates="village")
    assets: Mapped[list["VillageAsset"]] = relationship("VillageAsset", back_populates="village")
    briefings: Mapped[list["Briefing"]] = relationship("Briefing", back_populates="village")


class VillageMetricsDaily(Base):
    __tablename__ = "village_metrics_daily"
    __table_args__ = (Index("idx_village_metrics_date", "village_id", "metric_date"),)

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    village_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("villages.id"), nullable=False)
    metric_date: Mapped[date] = mapped_column(DATE, nullable=False)
    total_value: Mapped[int] = mapped_column(BIGINT, nullable=False)
    return_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 2), nullable=True)
    allocation: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME, nullable=False, default=datetime.utcnow)

    # Relationships
    village: Mapped["Village"] = relationship("Village", back_populates="metrics")


class VillageAsset(Base, TimestampMixin):
    __tablename__ = "village_assets"
    __table_args__ = (
        Index("idx_village_assets_village", "village_id"),
        Index("idx_village_assets_asset", "asset_id"),
    )

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    village_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("villages.id"), nullable=False)
    asset_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("assets.id"), nullable=False)
    value: Mapped[Optional[int]] = mapped_column(BIGINT, nullable=True)
    quantity: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 6), nullable=True)
    avg_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 6), nullable=True)

    # Relationships
    village: Mapped["Village"] = relationship("Village", back_populates="assets")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="village_assets")
