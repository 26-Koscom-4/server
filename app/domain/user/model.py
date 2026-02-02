from sqlalchemy import BigInteger, Enum, text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.common.model import Base, CreatedUpdatedMixin


class User(Base, CreatedUpdatedMixin):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    mda_mode: Mapped[str] = mapped_column(
        Enum("PRE", "POST", name="mda_mode"),
        nullable=False,
        server_default=text("'PRE'"),
    )


__all__ = ["User"]
