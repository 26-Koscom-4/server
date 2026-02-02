from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Enum, Index, String, TIMESTAMP, DECIMAL, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.common.model import Base, CreatedUpdatedMixin


class Asset(Base, CreatedUpdatedMixin):
    __tablename__ = "assets"
    __table_args__ = (
        Index("uk_assets_symbol", "symbol", unique=True),
        Index("idx_assets_country", "country_code"),
        Index("idx_assets_type", "asset_type"),
    )

    asset_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    asset_type: Mapped[str] = mapped_column(
        Enum("STOCK", "ETF", name="asset_type"),
        nullable=False,
    )


class AssetPrice(Base):
    __tablename__ = "asset_price"
    __table_args__ = (Index("idx_asset_price_asof", "as_of"),)

    asset_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    price: Mapped[Decimal] = mapped_column(DECIMAL(24, 8), nullable=False)
    as_of: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.current_timestamp()
    )


__all__ = ["Asset", "AssetPrice"]
