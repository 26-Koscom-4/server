from datetime import datetime
from sqlalchemy import CHAR, VARCHAR, DATETIME, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (Index("idx_assets_ticker", "ticker"),)

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(80), nullable=False)
    ticker: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    market: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    asset_type: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    currency: Mapped[str] = mapped_column(VARCHAR(10), nullable=False, default="KRW")
    created_at: Mapped[datetime] = mapped_column(DATETIME, nullable=False, default=datetime.utcnow)

    # Relationships
    village_assets: Mapped[list["VillageAsset"]] = relationship("VillageAsset", back_populates="asset")
    news_items: Mapped[list["NewsItem"]] = relationship(
        "NewsItem", secondary="news_item_assets", back_populates="assets"
    )
    neighbor_items: Mapped[list["NeighborRecommendationItem"]] = relationship(
        "NeighborRecommendationItem", secondary="neighbor_item_assets", back_populates="assets"
    )
