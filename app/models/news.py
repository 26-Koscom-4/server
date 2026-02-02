from datetime import datetime
from typing import Optional
from sqlalchemy import CHAR, VARCHAR, DATETIME, TEXT, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class NewsItem(Base):
    __tablename__ = "news_items"
    __table_args__ = (Index("idx_news_published", "published_at"),)

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    title: Mapped[str] = mapped_column(VARCHAR(300), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(VARCHAR(80), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(VARCHAR(800), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DATETIME, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME, nullable=False, default=datetime.utcnow)

    # Relationships
    assets: Mapped[list["Asset"]] = relationship(
        "Asset", secondary="news_item_assets", back_populates="news_items"
    )
    briefings: Mapped[list["Briefing"]] = relationship(
        "Briefing", secondary="briefing_news_links", back_populates="news_items"
    )


class NewsItemAsset(Base):
    __tablename__ = "news_item_assets"
    __table_args__ = (Index("idx_news_item_assets_asset", "asset_id"),)

    news_item_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("news_items.id"), primary_key=True
    )
    asset_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("assets.id"), primary_key=True
    )
