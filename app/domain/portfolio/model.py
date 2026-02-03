from sqlalchemy import BigInteger, DECIMAL, JSON, TIMESTAMP, func, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.common.model import Base


class UserPortfolio(Base):
    __tablename__ = "user_portfolio"
    __table_args__ = (
        Index("idx_user_portfolio_user", "user_id"),
        Index("idx_user_portfolio_asset", "asset_id"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    quantity: Mapped[float] = mapped_column(
        DECIMAL(24, 8), nullable=False, server_default=text("0")
    )
    avg_buy_price: Mapped[float] = mapped_column(
        DECIMAL(24, 8), nullable=False, server_default=text("0")
    )


class RebalancingSnapshot(Base):
    __tablename__ = "rebalancing_snapshots"
    __table_args__ = (
        Index("idx_rebalancing_user", "user_id"),
        Index("idx_rebalancing_latest", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.current_timestamp()
    )


__all__ = ["UserPortfolio", "RebalancingSnapshot"]
