from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import CHAR, VARCHAR, DATETIME, TEXT, BIGINT, DECIMAL, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class NeighborRecommendation(Base):
    __tablename__ = "neighbor_recommendations"
    __table_args__ = (Index("idx_neighbor_reco_user", "user_id"),)

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DATETIME, nullable=False, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="neighbor_recommendations")
    items: Mapped[list["NeighborRecommendationItem"]] = relationship(
        "NeighborRecommendationItem", back_populates="recommendation"
    )


class NeighborRecommendationItem(Base):
    __tablename__ = "neighbor_recommendation_items"
    __table_args__ = (Index("idx_neighbor_items_reco", "recommendation_id"),)

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    recommendation_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("neighbor_recommendations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(VARCHAR(60), nullable=False)
    icon: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(VARCHAR(200), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    correlation: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME, nullable=False, default=datetime.utcnow)

    # Relationships
    recommendation: Mapped["NeighborRecommendation"] = relationship(
        "NeighborRecommendation", back_populates="items"
    )
    assets: Mapped[list["Asset"]] = relationship(
        "Asset", secondary="neighbor_item_assets", back_populates="neighbor_items"
    )


class NeighborItemAsset(Base):
    __tablename__ = "neighbor_item_assets"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    recommendation_item_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("neighbor_recommendation_items.id"), nullable=False
    )
    asset_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("assets.id"), nullable=False)
