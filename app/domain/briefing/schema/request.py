from typing import Literal

from app.domain.common.schema.dto import BaseSchema


class BriefingGenerateRequest(BaseSchema):
    """개미 마을 브리핑 생성 요청."""

    user_id: int
    village_id: int
    time_slot: Literal["morning", "evening"] = "morning"
