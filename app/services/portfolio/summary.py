"""Portfolio summary builder."""

from __future__ import annotations

from collections import defaultdict
import logging
from datetime import datetime
from typing import Dict, List, Tuple
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.domain.asset.model import Asset, AssetPrice
from app.domain.portfolio.model import UserPortfolio
from app.domain.village.model import Village, VillageAsset
from app.domain.portfolio.schema.response import (
    AssetTypeDistributionItem,
    ExportLinks,
    PortfolioSummaryResponse,
    RankedReturnItem,
    RebalancingRecommendation,
    SummarySection,
    VillageReturnRate,
)
from app.domain.portfolio.model import RebalancingSnapshot
from app.services.briefing.llm import call_llm
from app.services.market_data import MarketContext, TickerQuote, get_market_context

logger = logging.getLogger(__name__)


def _format_as_of() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat()


def _extract_quotes_map(quotes: List[TickerQuote]) -> Dict[str, TickerQuote]:
    return {q.ticker: q for q in quotes if q and q.ticker}


def _build_price_tickers(rows: List[Tuple[UserPortfolio, Asset]]) -> Tuple[List[str], Dict[int, str]]:
    price_tickers: List[str] = []
    mapping: Dict[int, str] = {}
    for _p, asset in rows:
        symbol = asset.symbol
        if asset.country_code == "KR" and symbol.isdigit() and len(symbol) == 6:
            yf_symbol = f"{symbol}.KS"
        else:
            yf_symbol = symbol
        price_tickers.append(yf_symbol)
        mapping[asset.asset_id] = yf_symbol
    return price_tickers, mapping


def _upsert_asset_prices(db: Session, price_map: Dict[int, float]) -> None:
    if not price_map:
        return
    from sqlalchemy.dialects.mysql import insert as mysql_insert

    now = datetime.utcnow()
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


def _classify_bucket(asset: Asset) -> List[str]:
    keys: List[str] = []
    name = (asset.name or "").lower()
    symbol = (asset.symbol or "").upper()
    if asset.asset_type == "ETF":
        if "lever" in name or symbol in {"TQQQ", "UPRO", "SOXL"}:
            keys.append("leveraged_etf")
        elif "배당" in asset.name or symbol in {"SCHD", "VYM", "HDV"}:
            keys.append("dividend_etf")
        elif "나스닥" in asset.name or "nasdaq" in name:
            keys.append("growth_etf")
        else:
            keys.append("etf")
    if asset.asset_type == "STOCK":
        if asset.country_code == "US":
            keys.append("us_stocks")
        if asset.country_code == "KR":
            keys.append("kr_stocks")
    if any(k in name for k in ["테크", "반도체", "tech", "ai"]):
        keys.append("tech")
    if "성장" in asset.name or "growth" in name:
        keys.append("growth")
    return keys or ["other"]


def _weighted_daily_change(items: List[Tuple[float, float]]) -> float:
    total_value = sum(v for _r, v in items if v > 0)
    if total_value > 0:
        return sum(r * v for r, v in items if v > 0) / total_value
    rates = [r for r, _v in items]
    return sum(rates) / len(rates) if rates else 0.0


def _rebalancing_keys(
    total_return_rate: float,
    bucket_values: Dict[str, float],
) -> List[str]:
    keys: List[str] = []
    if bucket_values.get("leveraged_etf", 0.0) > 0:
        keys.append("risk_balance")
    if total_return_rate < 0:
        keys.append("improve_return")
    if bucket_values.get("dividend_etf", 0.0) == 0:
        keys.append("strengthen_dividend")
    return keys or ["risk_balance"]


def _build_rebalancing_recos(
    keys: List[str],
    village_allocations: Dict[int, float],
    village_map: Dict[int, str],
    village_returns: Dict[int, float],
    bucket_values: Dict[str, float],
    total_assets_value: float,
) -> List[RebalancingRecommendation]:
    recos: List[RebalancingRecommendation] = []

    # 가장 비중 큰 마을
    top_village_id = None
    top_alloc = 0.0
    for vid, val in village_allocations.items():
        if val > top_alloc:
            top_alloc = val
            top_village_id = vid

    # 가장 성과 낮은 마을
    worst_village_id = None
    worst_rate = 0.0
    for vid, rate in village_returns.items():
        if worst_village_id is None or rate < worst_rate:
            worst_rate = rate
            worst_village_id = vid

    for key in keys:
        if key == "risk_balance":
            name = village_map.get(top_village_id, "특정 마을")
            pct = (top_alloc / total_assets_value * 100.0) if total_assets_value > 0 else 0.0
            recos.append(
                RebalancingRecommendation(
                    id="risk_balance",
                    title="포트폴리오 균형 조정",
                    description=f"{name}의 비중이 {pct:.1f}%로 높습니다. 다른 마을로 일부 분산하여 리스크를 줄이는 것을 추천합니다.",
                    solution="분산 투자 고려",
                )
            )
        elif key == "improve_return":
            name = village_map.get(worst_village_id, "특정 마을")
            recos.append(
                RebalancingRecommendation(
                    id="improve_return",
                    title="수익률 개선 기회",
                    description=f"{name}이(가) {worst_rate:.1f}% 수준입니다. 시장 상황을 고려해 비중 조정이 필요할 수 있습니다.",
                    solution="비중 조정 점검",
                )
            )
        elif key == "strengthen_dividend":
            dividend_value = bucket_values.get("dividend_etf", 0.0)
            dividend_pct = (dividend_value / total_assets_value * 100.0) if total_assets_value > 0 else 0.0
            recos.append(
                RebalancingRecommendation(
                    id="strengthen_dividend",
                    title="배당 수익 강화",
                    description=f"배당/방어 비중이 {dividend_pct:.1f}%로 낮습니다. 안정적인 현금 흐름을 위해 배당 비중을 늘리는 것을 고려해보세요.",
                    solution="배당마을 확대",
                )
            )
        else:
            recos.append(
                RebalancingRecommendation(
                    id=key,
                    title="리밸런싱 점검",
                    description="포트폴리오 구성을 점검해 리스크를 관리하세요.",
                    solution="구성 점검",
                )
            )
    return recos


def get_latest_rebalancing(user_id: int, db: Session) -> List[RebalancingRecommendation] | None:
    latest = (
        db.query(RebalancingSnapshot)
        .filter(RebalancingSnapshot.user_id == user_id)
        .order_by(RebalancingSnapshot.created_at.desc())
        .first()
    )
    if not latest:
        return None
    return [RebalancingRecommendation(**item) for item in latest.payload_json]


async def generate_rebalancing_snapshot(user_id: int, db: Session) -> List[RebalancingRecommendation]:
    summary = await build_portfolio_summary(user_id=user_id, db=db, include_rebalancing=False)
    recos = summary.rebalancing_recommendations
    snapshot = RebalancingSnapshot(user_id=user_id, payload_json=[r.model_dump() for r in recos])
    db.add(snapshot)
    db.commit()
    return recos


async def build_portfolio_summary(
    user_id: int,
    db: Session,
    include_rebalancing: bool = True,
) -> PortfolioSummaryResponse:
    rows = (
        db.query(UserPortfolio, Asset)
        .join(Asset, Asset.asset_id == UserPortfolio.asset_id)
        .filter(UserPortfolio.user_id == user_id)
        .all()
    )
    asset_ids = [asset.asset_id for _p, asset in rows]
    tickers = [asset.symbol for _p, asset in rows if asset.symbol]
    price_tickers, price_symbol_map = _build_price_tickers(rows)

    market_ctx: MarketContext = await get_market_context(
        [],
        news_per_ticker=0,
        price_tickers=price_tickers,
    )
    quotes_map = _extract_quotes_map(market_ctx.ticker_quotes or [])
    price_updates: Dict[int, float] = {}
    for _p, asset in rows:
        quote_symbol = price_symbol_map.get(asset.asset_id, asset.symbol)
        quote = quotes_map.get(quote_symbol)
        if quote and quote.price is not None:
            price_updates[asset.asset_id] = float(quote.price)
    _upsert_asset_prices(db, price_updates)
    price_map = _load_asset_prices(db, asset_ids)

    total_assets_value = 0.0
    total_cost_value = 0.0
    weighted_daily_items: List[Tuple[float, float]] = []
    return_items: List[Tuple[int, str, str, str, float]] = []
    bucket_values: Dict[str, float] = defaultdict(float)

    for portfolio, asset in rows:
        quantity = float(portfolio.quantity or 0)
        avg_buy = float(portfolio.avg_buy_price or 0)
        current_price = price_map.get(asset.asset_id, 0.0)
        current_value = quantity * current_price
        cost_value = quantity * avg_buy

        total_assets_value += current_value
        total_cost_value += cost_value

        quote_symbol = price_symbol_map.get(asset.asset_id, asset.symbol)
        quote = quotes_map.get(quote_symbol)
        daily_change = float(quote.change_percent) if quote and quote.change_percent is not None else 0.0
        weighted_daily_items.append((daily_change, current_value))

        total_return_rate = ((current_price - avg_buy) / avg_buy * 100.0) if avg_buy > 0 else 0.0
        return_items.append((asset.asset_id, asset.symbol, asset.name, asset.country_code, total_return_rate))

        for key in _classify_bucket(asset):
            bucket_values[key] += current_value

    total_profit_value = total_assets_value - total_cost_value
    total_profit_rate = (total_profit_value / total_cost_value * 100.0) if total_cost_value > 0 else 0.0
    total_return_rate = total_profit_rate
    daily_return_rate_point = _weighted_daily_change(weighted_daily_items)

    villages = db.query(Village).filter(Village.user_id == user_id).all()
    village_map = {v.village_id: v.name for v in villages}
    asset_villages: Dict[int, List[int]] = defaultdict(list)
    va_rows = (
        db.query(VillageAsset)
        .join(Village, Village.village_id == VillageAsset.village_id)
        .filter(Village.user_id == user_id)
        .all()
    )
    for va in va_rows:
        asset_villages[va.asset_id].append(va.village_id)
    village_returns: List[VillageReturnRate] = []
    village_returns_map: Dict[int, float] = {}
    village_allocations: Dict[int, float] = {}
    for v in villages:
        v_rows = (
            db.query(UserPortfolio, Asset)
            .join(Asset, Asset.asset_id == UserPortfolio.asset_id)
            .join(VillageAsset, VillageAsset.asset_id == Asset.asset_id)
            .filter(
                UserPortfolio.user_id == user_id,
                VillageAsset.village_id == v.village_id,
            )
            .all()
        )
        v_total = 0.0
        v_cost = 0.0
        for p, a in v_rows:
            qty = float(p.quantity or 0)
            avg = float(p.avg_buy_price or 0)
            cur = price_map.get(a.asset_id, 0.0)
            v_total += qty * cur
            v_cost += qty * avg
        v_rate = (v_total - v_cost) / v_cost * 100.0 if v_cost > 0 else 0.0
        village_returns.append(VillageReturnRate(village_id=v.village_id, return_rate=round(v_rate, 2)))
        village_returns_map[v.village_id] = v_rate
        village_allocations[v.village_id] = v_total

    asset_type_distribution = [
        AssetTypeDistributionItem(key=k, value=round(v, 0)) for k, v in bucket_values.items()
    ]

    sorted_returns = sorted(return_items, key=lambda x: x[4], reverse=True)
    top5 = [
        RankedReturnItem(
            rank=i + 1,
            symbol=(name if country_code == "KR" else symbol),
            name=name,
            return_rate=round(rate, 2),
            village_ids=asset_villages.get(asset_id, []),
            village_names=[village_map.get(vid, str(vid)) for vid in asset_villages.get(asset_id, [])],
        )
        for i, (asset_id, symbol, name, country_code, rate) in enumerate(sorted_returns[:5])
    ]
    bottom5 = [
        RankedReturnItem(
            rank=i + 1,
            symbol=(name if country_code == "KR" else symbol),
            name=name,
            return_rate=round(rate, 2),
            village_ids=asset_villages.get(asset_id, []),
            village_names=[village_map.get(vid, str(vid)) for vid in asset_villages.get(asset_id, [])],
        )
        for i, (asset_id, symbol, name, country_code, rate) in enumerate(sorted_returns[-5:][::-1])
    ]

    keys = _rebalancing_keys(total_return_rate, bucket_values)

    # Optional LLM refinement (fallback to keys if disabled)
    llm_keys = None
    prompt = f"""다음 포트폴리오 요약을 보고 리밸런싱 키를 3개까지 추천해 주세요.
키 후보: risk_balance, improve_return, strengthen_dividend
요약: total_return_rate={total_return_rate:.2f}, buckets={dict(bucket_values)}"""
    raw = call_llm("리밸런싱 추천 전문가", prompt)
    if raw and "risk_balance" in raw:
        llm_keys = [k for k in ["risk_balance", "improve_return", "strengthen_dividend"] if k in raw]

    recos = llm_keys or keys
    rebalancing_items = _build_rebalancing_recos(
        recos,
        village_allocations=village_allocations,
        village_map=village_map,
        village_returns=village_returns_map,
        bucket_values=bucket_values,
        total_assets_value=total_assets_value,
    )
    if include_rebalancing:
        latest = get_latest_rebalancing(user_id=user_id, db=db)
        if latest:
            logger.warning("Rebalancing snapshot used: user_id=%s", user_id)
            rebalancing_items = latest
        else:
            logger.warning("Rebalancing snapshot missing; generating: user_id=%s", user_id)
            rebalancing_items = await generate_rebalancing_snapshot(user_id=user_id, db=db)

    return PortfolioSummaryResponse(
        as_of=_format_as_of(),
        summary=SummarySection(
            total_assets_value=round(total_assets_value, 0),
            total_profit_value=round(total_profit_value, 0),
            total_profit_rate=round(total_profit_rate, 2),
            total_return_rate=round(total_return_rate, 2),
            daily_return_rate_point=round(daily_return_rate_point, 2),
            village_count=len(villages),
            owned_asset_count=len({asset.asset_id for _p, asset in rows}),
        ),
        village_return_rates=village_returns,
        asset_type_distribution=asset_type_distribution,
        top5_returns=top5,
        bottom5_returns=bottom5,
        rebalancing_recommendations=rebalancing_items,
        export=ExportLinks(
            excel_url="/api/portfolio/export?format=xlsx",
            pdf_url="/api/portfolio/export?format=pdf",
        ),
    )
