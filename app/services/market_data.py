"""실시간 시세·뉴스 수집 (yfinance 시세 + RSS 뉴스). API 실패 시 빈/목 데이터 반환."""

import asyncio
import logging
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_USDKRW_CACHE: Dict[str, Any] = {"rate": None, "ts": 0.0}


def get_usdkrw_rate() -> float:
    """Fetch USD→KRW exchange rate with basic caching."""
    now = time.time()
    if _USDKRW_CACHE["rate"] and now - _USDKRW_CACHE["ts"] < 300:
        return float(_USDKRW_CACHE["rate"])
    try:
        import requests

        resp = requests.get(
            "https://api.exchangerate.host/latest?base=USD&symbols=KRW",
            timeout=5,
        )
        data = resp.json()
        rate = float(data["rates"]["KRW"])
        _USDKRW_CACHE["rate"] = rate
        _USDKRW_CACHE["ts"] = now
        return rate
    except Exception as e:
        logger.warning("USDKRW fetch failed: %s", e)
        return 1.0

# RSS 피드 URL 설정 (Google News)
RSS_FEEDS = {
    "google_news_kr": "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko",
}

# 주요 종목의 한글명 매핑 (Google News 검색용)
TICKER_KR_NAME = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "035720": "카카오",
    "207940": "삼성바이오로직스",
    "005380": "현대차",
    "AAPL": "애플",
    "NVDA": "엔비디아",
    "TSLA": "테슬라",
    "MSFT": "마이크로소프트",
    "GOOGL": "구글",
    "META": "메타",
    "AMZN": "아마존",
}

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


def _fetch_rss_feed(url: str, limit: int = 10) -> List[Dict[str, Any]]:
    """RSS 피드에서 뉴스 가져오기."""
    try:
        import feedparser

        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:limit]:
            title = (entry.get("title") or "").strip()
            summary = (entry.get("summary") or entry.get("description") or "").strip()
            if summary:
                import re

                summary = re.sub(r"<[^>]+>", "", summary)[:500]
            published_ts = None
            if entry.get("published_parsed"):
                published_ts = int(time.mktime(entry.published_parsed))
            items.append({
                "title": title,
                "summary": summary or title,
                "source": entry.get("source", {}).get("title", "") or feed.feed.get("title", ""),
                "link": entry.get("link", ""),
                "published": published_ts,
            })
        logger.warning("RSS fetched: url=%s count=%d", url, len(items))
        return items
    except Exception as e:
        logger.warning("RSS feed fetch failed for %s: %s", url, e)
        return []


def _fetch_ticker_news(ticker: str, query: Optional[str] = None, limit: int = 3) -> List[Dict[str, Any]]:
    """동기: RSS 기반으로 종목 관련 뉴스 수집 (Google News)."""
    try:
        search_term = (query or "").strip() or TICKER_KR_NAME.get(ticker, ticker)
        rss_url = RSS_FEEDS["google_news_kr"].format(query=urllib.parse.quote(search_term))
        news_items = _fetch_rss_feed(rss_url, limit=limit)
        out = []
        for item in news_items:
            item["tickers"] = [ticker]
            out.append(item)
        titles = [item.get("title") for item in out if item.get("title")]
        logger.warning("[%s] RSS 뉴스 %d개 수집 (검색어: %s) titles=%s", ticker, len(out), search_term, titles)
        return out
    except Exception as e:
        logger.warning("RSS news failed for %s: %s", ticker, e)
        return []

def _get_market_context_sync(
    tickers: List[str],
    news_per_ticker: int = 3,
    name_map: Optional[Dict[str, str]] = None,
    price_tickers: Optional[List[str]] = None,
) -> MarketContext:
    """동기: 모든 ticker에 대해 시세·뉴스 수집. 실패한 ticker는 건너뜀."""
    tickers = [t for t in tickers if t]
    if not tickers:
        return MarketContext()

    quotes: List[TickerQuote] = []
    news_by_key: Dict[str, Dict[str, Any]] = {}  # title -> item (중복 제거)

    quote_tickers = price_tickers or tickers
    for ticker in quote_tickers:
        q = _fetch_ticker_quote(ticker)
        quotes.append(q)
    for ticker in tickers:
        query = name_map.get(ticker) if name_map else None
        for item in _fetch_ticker_news(ticker, query=query, limit=news_per_ticker):
            key = item.get("title") or ""
            if key and key not in news_by_key:
                news_by_key[key] = item
        logger.warning("RSS aggregate: ticker=%s query=%s news_count=%d", ticker, query, len(news_by_key))

    return MarketContext(
        ticker_quotes=quotes,
        news_items=list(news_by_key.values()),
    )


async def get_market_context(
    tickers: List[str],
    news_per_ticker: int = 3,
    name_map: Optional[Dict[str, str]] = None,
    price_tickers: Optional[List[str]] = None,
) -> MarketContext:
    """
    종목 코드 리스트에 대해 실시간 시세·최신 뉴스(종목당 최대 news_per_ticker건) 수집.
    비동기: yfinance 블로킹 호출을 스레드 풀에서 실행.
    API 호출 실패 시 해당 종목은 건너뛰고, 전체 실패 시 빈 MarketContext 반환.
    """
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: _get_market_context_sync(tickers, news_per_ticker, name_map, price_tickers),
        )
    except Exception as e:
        logger.warning("get_market_context failed: %s", e)
        return MarketContext()
