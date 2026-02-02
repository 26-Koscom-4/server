from decimal import Decimal

from sqlalchemy import BigInteger, DECIMAL, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedUpdatedMixin


class UserPortfolio(Base, CreatedUpdatedMixin):
    __tablename__ = "user_portfolio"
    __table_args__ = (
        Index("idx_user_portfolio_user", "user_id"),
        Index("idx_user_portfolio_asset", "asset_id"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    quantity: Mapped[Decimal] = mapped_column(
        DECIMAL(24, 8), nullable=False, server_default=text("0")
    )
    avg_buy_price: Mapped[Decimal] = mapped_column(
        DECIMAL(24, 8), nullable=False, server_default=text("0")
    )
