from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Enum, Index, String, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, CreatedUpdatedMixin


class Village(Base, CreatedUpdatedMixin):
    __tablename__ = "villages"
    __table_args__ = (
        Index("idx_villages_user", "user_id"),
        Index("idx_villages_user_type", "user_id", "village_type"),
    )

    village_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    village_type: Mapped[str] = mapped_column(
        Enum("SYSTEM", "CUSTOM", name="village_type"),
        nullable=False,
        server_default=text("'SYSTEM'"),
    )
    ai_one_liner: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    as_of: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)


class VillageAsset(Base, CreatedAtMixin):
    __tablename__ = "village_assets"
    __table_args__ = (Index("idx_village_assets_asset", "asset_id"),)

    village_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
