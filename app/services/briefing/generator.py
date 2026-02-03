"""브리핑 생성: 포트폴리오/시세/뉴스/AI 분석을 통합."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import uuid5, NAMESPACE_URL

from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert as mysql_insert

from app.domain.asset.model import Asset, AssetPrice
from app.domain.briefing.model import BriefingSnapshot
from app.domain.briefing.schema.dto import (
    AIAdvice,
    AssetDailyChangeItem,
    AssetDailyChanges,
    AssetTotalReturnItem,
    AssetTotalReturns,
    LatestNews,
    LatestNewsItem,
    PortfolioSummary,
    PortfolioSummaryDisplay,
    VillageDailyChange,
    VillageInfo,
)
from app.domain.briefing.schema.request import BriefingGenerateRequest
from app.domain.briefing.schema.response import BriefingGenerateResponse
from app.domain.portfolio.model import UserPortfolio
from app.domain.village.model import Village, VillageAsset
from app.services.briefing.agents.news_agent import (
    analyze_news_data,
    filter_relevant_news_with_llm,
)
from app.services.briefing.agents.orchestrator import orchestrate_briefing
from app.services.briefing.agents.stock_agent import analyze_stock_data
from app.services.market_data import MarketContext, TickerQuote, get_market_context

logger = logging.getLogger(__name__)


def _format_percent(value: float) -> str:
    return f"{value:+.2f}%"


def _format_currency_krw(value: float) -> str:
    sign = "+" if value > 0 else "-" if value < 0 else ""
    return f"{sign}{abs(value):,.0f}원"


def _published_ago(published_ts: Optional[int]) -> str:
    if not published_ts:
        return "방금 전"
    now = datetime.now(timezone.utc)
    published = datetime.fromtimestamp(published_ts, tz=timezone.utc)
    delta = now - published
    minutes = max(int(delta.total_seconds() // 60), 0)
    if minutes < 60:
        return f"{minutes}분 전"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}시간 전"
    days = hours // 24
    return f"{days}일 전"


def _make_news_id(url: str, title: str) -> str:
    seed = url or title or "news"
    return str(uuid5(NAMESPACE_URL, seed))


def _compute_weighted_daily_change(
    items: List[Tuple[float, float]],
) -> float:
    """items: (daily_change_rate, current_value)."""
    total_value = sum(v for _r, v in items if v > 0)
    if total_value > 0:
        return sum(r * v for r, v in items if v > 0) / total_value
    rates = [r for r, _v in items]
    return sum(rates) / len(rates) if rates else 0.0


def _extract_quotes_map(quotes: List[TickerQuote]) -> Dict[str, TickerQuote]:
    return {q.ticker: q for q in quotes if q and q.ticker}


def _upsert_asset_prices(db: Session, price_map: Dict[int, float]) -> None:
    """asset_price에 현재가 upsert."""
    if not price_map:
        return
    now = datetime.now(timezone.utc)
    rows = [{"asset_id": asset_id, "price": price, "as_of": now} for asset_id, price in price_map.items()]
    stmt = mysql_insert(AssetPrice).values(rows)
    stmt = stmt.on_duplicate_key_update(
        price=stmt.inserted.price,
        as_of=stmt.inserted.as_of,
    )
    db.execute(stmt)
    db.commit()


def _load_asset_prices(db: Session, asset_ids: List[int]) -> Dict[int, float]:
    if not asset_ids:
        return {}
    rows = db.query(AssetPrice).filter(AssetPrice.asset_id.in_(asset_ids)).all()
    return {row.asset_id: float(row.price) for row in rows if row and row.price is not None}


async def generate_briefing(
    req: BriefingGenerateRequest,
    db: Session,
) -> BriefingGenerateResponse:
    user_id = int(req.user_id)

    # 기본 마을 정보 (없으면 폴백)
    village_row = (
        db.query(Village)
        .filter(Village.user_id == user_id, Village.village_id == req.village_id)
        .first()
    )
    if not village_row:
        logger.warning("No village found for user_id=%s village_id=%s", user_id, req.village_id)
    if village_row:
        village_profile = getattr(village_row, "village_profile", None)
        village = VillageInfo(
            id=str(getattr(village_row, "village_id", "")),
            name=getattr(village_row, "name", "") or "내 포트폴리오",
            icon="🐜",
        )
    else:
        village_profile = None
        village = VillageInfo(id=str(req.village_id), name="내 포트폴리오", icon="🐜")

    portfolio_rows = (
        db.query(UserPortfolio, Asset)
        .join(Asset, Asset.asset_id == UserPortfolio.asset_id)
        .join(VillageAsset, VillageAsset.asset_id == Asset.asset_id)
        .filter(
            UserPortfolio.user_id == user_id,
            VillageAsset.village_id == req.village_id,
        )
        .all()
    )
    logger.warning(
        "Village assets loaded: user_id=%s village_id=%s assets=%s",
        user_id,
        req.village_id,
        [
            {"asset_id": asset.asset_id, "symbol": asset.symbol, "name": asset.name}
            for _p, asset in portfolio_rows
        ],
    )
    if not portfolio_rows:
        logger.warning("No portfolio rows for user_id=%s", user_id)

    tickers = [asset.symbol for _p, asset in portfolio_rows if asset.symbol]
    asset_names = [asset.name for _p, asset in portfolio_rows if asset.name]
    price_tickers = []
    asset_price_symbol_map: Dict[int, str] = {}
    for _p, asset in portfolio_rows:
        symbol = asset.symbol
        if asset.country_code == "KR" and symbol.isdigit() and len(symbol) == 6:
            yf_symbol = f"{symbol}.KS"
        else:
            yf_symbol = symbol
        price_tickers.append(yf_symbol)
        asset_price_symbol_map[asset.asset_id] = yf_symbol

    name_map = {asset.symbol: asset.name for _p, asset in portfolio_rows if asset.symbol and asset.name}
    market_ctx: MarketContext = await get_market_context(
        tickers,
        news_per_ticker=3,
        name_map=name_map,
        price_tickers=price_tickers,
    )
    quotes_map = _extract_quotes_map(market_ctx.ticker_quotes or [])
    price_updates: Dict[int, float] = {}

    for _portfolio, asset in portfolio_rows:
        quote_symbol = asset_price_symbol_map.get(asset.asset_id, asset.symbol)
        quote = quotes_map.get(quote_symbol)
        if quote and quote.price is not None:
            price_updates[asset.asset_id] = float(quote.price)
    _upsert_asset_prices(db, price_updates)

    asset_price_map = _load_asset_prices(db, [asset.asset_id for _p, asset in portfolio_rows])

    asset_total_return_items: List[AssetTotalReturnItem] = []
    asset_daily_change_items: List[AssetDailyChangeItem] = []
    weighted_daily_items: List[Tuple[float, float]] = []

    total_assets_value = 0.0
    total_cost_value = 0.0

    for portfolio, asset in portfolio_rows:
        ticker = asset.symbol
        name = asset.name
        quantity = float(portfolio.quantity or 0)
        avg_buy_price = float(portfolio.avg_buy_price or 0)
        quote_symbol = asset_price_symbol_map.get(asset.asset_id, ticker)
        quote = quotes_map.get(quote_symbol)
        current_price = asset_price_map.get(asset.asset_id, 0.0)
        daily_change_rate = float(quote.change_percent) if quote and quote.change_percent is not None else 0.0

        current_value = quantity * current_price
        cost_value = quantity * avg_buy_price
        total_assets_value += current_value
        total_cost_value += cost_value

        total_return_rate = 0.0
        if avg_buy_price > 0:
            total_return_rate = ((current_price - avg_buy_price) / avg_buy_price) * 100.0

        asset_total_return_items.append(
            AssetTotalReturnItem(
                ticker=ticker,
                name=name,
                total_return_rate=round(total_return_rate, 2),
                display=_format_percent(total_return_rate),
            )
        )

        asset_daily_change_items.append(
            AssetDailyChangeItem(
                ticker=ticker,
                name=name,
                daily_change_rate=round(daily_change_rate, 2),
                display=_format_percent(daily_change_rate),
            )
        )

        weighted_daily_items.append((daily_change_rate, current_value))

    total_profit_value = total_assets_value - total_cost_value
    total_return_rate = (
        (total_profit_value / total_cost_value * 100.0) if total_cost_value > 0 else 0.0
    )

    portfolio_summary = PortfolioSummary(
        total_return_rate=round(total_return_rate, 2),
        total_profit_value=round(total_profit_value, 0),
        total_assets_value=round(total_assets_value, 0),
        display=PortfolioSummaryDisplay(
            total_return_rate=_format_percent(total_return_rate),
            total_profit_value=_format_currency_krw(total_profit_value),
            total_assets_value=_format_currency_krw(total_assets_value).lstrip("+"),
        ),
    )

    village_daily_change_rate = _compute_weighted_daily_change(weighted_daily_items)
    village_daily_change = VillageDailyChange(
        daily_change_rate=round(village_daily_change_rate, 2),
        display=_format_percent(village_daily_change_rate),
    )

    # 뉴스 필터링 (LLM 관련성 판단)
    news_items = market_ctx.news_items or []
    news_by_ticker: Dict[str, List[Dict[str, Any]]] = {}
    for item in news_items:
        for t in item.get("tickers") or []:
            news_by_ticker.setdefault(t, []).append(item)
    if news_items and asset_names:
        filtered = filter_relevant_news_with_llm(news_items, asset_names)
        if filtered:
            news_items = filtered

    # 최소 종목당 1개 확보
    selected_news: List[Dict[str, Any]] = []
    selected_keys = set()
    for t in tickers:
        candidates = news_by_ticker.get(t) or []
        if candidates:
            item = candidates[0]
            key = item.get("title") or ""
            if key and key not in selected_keys:
                selected_news.append(item)
                selected_keys.add(key)
    for item in news_items:
        key = item.get("title") or ""
        if key and key not in selected_keys:
            selected_news.append(item)
            selected_keys.add(key)

    latest_news_items: List[LatestNewsItem] = []
    for item in selected_news[: max(3, len(tickers))]:
        title = (item.get("title") or "").strip()
        summary = (item.get("summary") or title).strip()
        url = item.get("link") or item.get("url") or ""
        published = item.get("published")
        latest_news_items.append(
            LatestNewsItem(
                news_id=_make_news_id(url, title),
                title=title,
                summary=summary,
                published_ago=_published_ago(published),
                url=url,
            )
        )

    latest_news = LatestNews(title="마을 최신 뉴스", items=latest_news_items)

    # AI 분석: 주식/뉴스 → 통합 조언
    stock_analysis = analyze_stock_data(
        market_ctx.ticker_quotes or [],
        [{
            "name": village.name,
            "profile": village_profile,
            "assets": [{"ticker": t, "name": n} for t, n in zip(tickers, asset_names)],
        }],
        user_name="김직장님",
        time_slot=req.time_slot,
    )
    news_analysis = analyze_news_data(
        news_items,
        tickers,
        user_name="김직장님",
        time_slot=req.time_slot,
    )

    _voice_script, visual_summary = orchestrate_briefing(
        stock_analysis,
        news_analysis,
        [{"name": village.name, "profile": village_profile}],
        user_name="김직장님",
        time_slot=req.time_slot,
    )

    bullets = visual_summary.get("advice") if isinstance(visual_summary, dict) else None
    stock_rationales = visual_summary.get("stock_rationales") if isinstance(visual_summary, dict) else None
    if not isinstance(bullets, list) or not bullets:
        bullets = [
            "시장 변동성을 주의 깊게 모니터링하세요.",
            "포트폴리오 리밸런싱을 고려해 보세요.",
        ]
    if isinstance(stock_rationales, list) and stock_rationales:
        bullets = [str(b) for b in bullets] + [str(r) for r in stock_rationales]

    ai_advice = AIAdvice(title="오늘의 AI 조언", bullets=[str(b) for b in bullets])

    response = BriefingGenerateResponse(
        user_id=user_id,
        time_slot=req.time_slot,
        village=village,
        portfolio_summary=portfolio_summary,
        village_daily_change=village_daily_change,
        asset_total_returns=AssetTotalReturns(
            title="보유 종목별 총 수익률",
            items=asset_total_return_items,
        ),
        asset_daily_changes=AssetDailyChanges(
            title="보유 종목별 전일대비 등락",
            items=asset_daily_change_items,
        ),
        latest_news=latest_news,
        ai_advice=ai_advice,
    )
    snapshot = BriefingSnapshot(
        user_id=user_id,
        village_id=req.village_id,
        time_slot=req.time_slot,
        payload_json=response.model_dump(),
    )
    db.add(snapshot)
    db.commit()
    return response
