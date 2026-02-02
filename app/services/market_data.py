"""실시간 시세·뉴스 수집 (yfinance). API 실패 시 빈/목 데이터 반환."""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TickerQuote:
    """종목별 현재가·전일대비 변동률."""

    ticker: str
    price: Optional[float] = None
    change_percent: Optional[float] = None
    previous_close: Optional[float] = None
    currency: Optional[str] = None


@dataclass
class MarketContext:
    """get_market_context 반환 타입."""

    ticker_quotes: List[TickerQuote] = field(default_factory=list)
    news_items: List[Dict[str, Any]] = field(default_factory=list)


def _fetch_ticker_quote(ticker: str) -> TickerQuote:
    """동기: yfinance로 한 종목 시세 조회. 실패 시 빈 TickerQuote."""
    try:
        import yfinance as yf

        t = yf.Ticker(ticker)
        hist = t.history(period="5d", interval="1d")
        if hist is None or hist.empty:
            return TickerQuote(ticker=ticker)
        closes = hist["Close"]
        if len(closes) < 2:
            price = float(closes.iloc[-1]) if len(closes) else None
            return TickerQuote(ticker=ticker, price=price, previous_close=price, change_percent=0.0)
        current = float(closes.iloc[-1])
        previous = float(closes.iloc[-2])
        change_pct = ((current - previous) / previous * 100.0) if previous else None
        info = t.info or {}
        currency = info.get("currency") or "USD"
        return TickerQuote(
            ticker=ticker,
            price=current,
            previous_close=previous,
            change_percent=round(change_pct, 2) if change_pct is not None else None,
            currency=currency,
        )
    except Exception as e:
        logger.warning("yfinance quote failed for %s: %s", ticker, e)
        return TickerQuote(ticker=ticker)


def _fetch_ticker_news(ticker: str, limit: int = 3) -> List[Dict[str, Any]]:
    """동기: yfinance로 한 종목 뉴스 최대 limit건. NewsItem 호환 필드."""
    try:
        import yfinance as yf

        t = yf.Ticker(ticker)
        raw = t.news or []
        out = []
        for n in raw[:limit]:
            out.append({
                "title": (n.get("title") or "").strip(),
                "summary": (n.get("summary") or n.get("title") or "").strip()[:500],
                "source": (n.get("publisher") or n.get("source") or "").strip(),
                "tickers": [ticker],
            })
        return out
    except Exception as e:
        logger.warning("yfinance news failed for %s: %s", ticker, e)
        return []


def _get_market_context_sync(tickers: List[str], news_per_ticker: int = 3) -> MarketContext:
    """동기: 모든 ticker에 대해 시세·뉴스 수집. 실패한 ticker는 건너뜀."""
    tickers = [t for t in tickers if t]
    if not tickers:
        return MarketContext()

    quotes: List[TickerQuote] = []
    news_by_key: Dict[str, Dict[str, Any]] = {}  # title -> item (중복 제거)

    for ticker in tickers:
        q = _fetch_ticker_quote(ticker)
        quotes.append(q)
        for item in _fetch_ticker_news(ticker, limit=news_per_ticker):
            key = item.get("title") or ""
            if key and key not in news_by_key:
                news_by_key[key] = item

    return MarketContext(
        ticker_quotes=quotes,
        news_items=list(news_by_key.values()),
    )


async def get_market_context(tickers: List[str], news_per_ticker: int = 3) -> MarketContext:
    """
    종목 코드 리스트에 대해 실시간 시세·최신 뉴스(종목당 최대 news_per_ticker건) 수집.
    비동기: yfinance 블로킹 호출을 스레드 풀에서 실행.
    API 호출 실패 시 해당 종목은 건너뛰고, 전체 실패 시 빈 MarketContext 반환.
    """
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: _get_market_context_sync(tickers, news_per_ticker),
        )
    except Exception as e:
        logger.warning("get_market_context failed: %s", e)
        return MarketContext()
