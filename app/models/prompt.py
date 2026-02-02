from sqlalchemy import BigInteger, Boolean, Index, String, Text, Integer, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, CreatedUpdatedMixin


class Prompt(Base, CreatedUpdatedMixin):
    __tablename__ = "prompts"
    __table_args__ = (
        Index("uk_prompts_key", "key", unique=True),
        Index("idx_prompts_active", "is_active"),
    )

    prompt_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    prompt_key: Mapped[str] = mapped_column("key", String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("1")
    )


class VillagePrompt(Base, CreatedAtMixin):
    __tablename__ = "village_prompts"
    __table_args__ = (
        Index("idx_village_prompts_prompt", "prompt_id"),
        Index("idx_village_prompts_order", "village_id", "sort_order"),
    )

    village_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    prompt_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("1")
    )
