from typing import List, Literal, Optional

from app.domain.common.schema.dto import BaseSchema
from app.domain.village.schema.dto import Village


class NewsItem(BaseSchema):
    """경제/시장 뉴스 한 건. assets ticker와 매칭해 필터링에 사용."""

    title: str
    summary: Optional[str] = None
    source: Optional[str] = None
    tickers: Optional[List[str]] = None  # 관련 종목 코드 (AAPL, NVDA 등)


class BriefingGenerateRequest(BaseSchema):
    """개미 마을 수석 이장 브리핑 생성 요청."""

    villages: List[Village]
    news_items: Optional[List[NewsItem]] = None
    user_name: Optional[str] = "김직장님"
    time_slot: Literal["morning", "evening"] = "morning"
