"""최신 브리핑 저장소 (서버 메모리). 스케줄 job이 저장, GET /briefing이 조회."""

from datetime import datetime
from typing import Any, Dict, Optional

_latest: Optional[Dict[str, Any]] = None


def set_latest(
    summary: str,
    news_count: int = 0,
    tickers: Optional[list] = None,
    generated_at: Optional[datetime] = None,
) -> None:
    """가장 최근 생성된 브리핑을 저장."""
    global _latest
    _latest = {
        "summary": summary,
        "news_count": news_count,
        "tickers": tickers or [],
        "generated_at": (generated_at or datetime.utcnow()).isoformat(),
    }


def get_latest() -> Optional[Dict[str, Any]]:
    """가장 최근 브리핑 반환. 없으면 None."""
    return _latest
