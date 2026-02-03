from typing import List
import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.village.model import Village, VillageAsset
from app.domain.village.schema.request import VillageCreateRequest
from app.domain.village.schema.response import (
    VillageCreateResponse,
    CustomVillagesResponse,
    CustomVillageItem,
    VillageSummaryResponse,
    VillageSummary,
    VillageMetrics,
    VillageMetricsDisplay,
    VillageAssetsSection,
    VillageAssetItem,
    VillageDetailResponse,
    VillageDetailHeader,
    SummaryCards,
    SummaryCardsDisplay,
    MonthlyReturnTrend,
    MonthlyReturnItem,
    VillageOverview,
    VillageOverviewDisplay,
    HoldingsSection,
    HoldingItem,
    HoldingDisplay,
)
from app.domain.asset.model import Asset, AssetPrice, AssetPriceMonthly
from app.domain.portfolio.model import UserPortfolio
from app.services.market_data import get_market_context, get_usdkrw_rate
from app.services.village.ai import generate_village_one_liner

router = APIRouter()


def _categorize_asset(asset: Asset) -> str:
    name = (asset.name or "").lower()
    symbol = (asset.symbol or "").upper()
    if asset.country_code == "KR":
        return "한국주식" if asset.asset_type == "STOCK" else "국내 ETF"
    if symbol in {"NVDA"} or "엔비디아" in asset.name or "nvidia" in name or "ai" in name:
        return "AI주"
    if symbol in {"TSLA"} or "테슬라" in asset.name:
        return "성장주"
    if symbol in {"AAPL", "MSFT"} or "tech" in name or "기술" in asset.name:
        return "기술주"
    if asset.asset_type == "ETF":
        return "ETF"
    return "미국주식" if asset.country_code == "US" else "주식"


@router.post("", response_model=VillageCreateResponse)
def create_village(
    payload: VillageCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> VillageCreateResponse:
    village = Village(
        user_id=payload.user_id,
        name=payload.name,
        icon=payload.icon,
        type=payload.type,
        goal=payload.goal,
        village_type="CUSTOM",
        village_profile=". ".join(payload.strategy_items).strip() if payload.strategy_items else None,
    )
    db.add(village)
    db.flush()

    if not payload.assets:
        raise HTTPException(status_code=400, detail="assets must not be empty.")
    for a in payload.assets:
        db.add(VillageAsset(village_id=village.village_id, asset_id=a.asset_id))
    db.commit()
    background_tasks.add_task(generate_village_one_liner, village.village_id)
    return VillageCreateResponse(village_id=village.village_id)


@router.get("/custom", response_model=CustomVillagesResponse)
def get_custom_villages(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
) -> CustomVillagesResponse:
    villages = (
        db.query(Village)
        .filter(Village.user_id == user_id, Village.village_type == "CUSTOM")
        .order_by(Village.village_id.asc())
        .all()
    )
    items: List[CustomVillageItem] = []
    total_assets_all = 0.0

    # Refresh prices (KRW 기준)
    all_assets = db.query(Asset).all()
    tickers = [a.symbol for a in all_assets if a.symbol]
    price_tickers = []
    price_symbol_map = {}
    for a in all_assets:
        symbol = a.symbol
        if a.country_code == "KR" and symbol.isdigit() and len(symbol) == 6:
            yf_symbol = f"{symbol}.KS"
        else:
            yf_symbol = symbol
        price_tickers.append(yf_symbol)
        price_symbol_map[a.asset_id] = yf_symbol

    market_ctx = asyncio.run(get_market_context(price_tickers, news_per_ticker=0, price_tickers=price_tickers))
    usdkrw_rate = get_usdkrw_rate()
    quotes_map = {q.ticker: q for q in market_ctx.ticker_quotes or [] if q and q.ticker}
    price_updates = {}
    for a in all_assets:
        quote = quotes_map.get(price_symbol_map.get(a.asset_id, a.symbol))
        if quote and quote.price is not None:
            price = float(quote.price)
            if a.country_code == "US":
                price *= usdkrw_rate
            price_updates[a.asset_id] = price
    if price_updates:
        from sqlalchemy.dialects.mysql import insert as mysql_insert
        now = datetime.utcnow()
        rows = [{"asset_id": aid, "price": p, "as_of": now} for aid, p in price_updates.items()]
        stmt = mysql_insert(AssetPrice).values(rows)
        stmt = stmt.on_duplicate_key_update(price=stmt.inserted.price, as_of=stmt.inserted.as_of)
        db.execute(stmt)
        db.commit()

    asset_prices = {row.asset_id: float(row.price) for row in db.query(AssetPrice).all()}
    normalize_updates = {}
    for a in all_assets:
        price = asset_prices.get(a.asset_id)
        if price is None:
            continue
        if (a.country_code or "").upper() == "US":
            price *= 1450.0
            asset_prices[a.asset_id] = price
            normalize_updates[a.asset_id] = price
    if normalize_updates:
        from sqlalchemy.dialects.mysql import insert as mysql_insert
        now = datetime.utcnow()
        rows = [{"asset_id": aid, "price": p, "as_of": now} for aid, p in normalize_updates.items()]
        stmt = mysql_insert(AssetPrice).values(rows)
        stmt = stmt.on_duplicate_key_update(price=stmt.inserted.price, as_of=stmt.inserted.as_of)
        db.execute(stmt)
        db.commit()
    # normalize USD prices in DB if needed
    normalize_updates = {}
    for a in assets:
        price = asset_prices.get(a.asset_id)
        if price is None:
            continue
        if (a.country_code or "").upper() == "US":
            logger = __import__("logging").getLogger(__name__)
            logger.warning("Normalize price: asset_id=%s symbol=%s country=%s price=%s", a.asset_id, a.symbol, a.country_code, price)
            price *= 1450.0
            asset_prices[a.asset_id] = price
            normalize_updates[a.asset_id] = price
    if normalize_updates:
        from sqlalchemy.dialects.mysql import insert as mysql_insert
        now = datetime.utcnow()
        rows = [{"asset_id": aid, "price": p, "as_of": now} for aid, p in normalize_updates.items()]
        stmt = mysql_insert(AssetPrice).values(rows)
        stmt = stmt.on_duplicate_key_update(price=stmt.inserted.price, as_of=stmt.inserted.as_of)
        db.execute(stmt)
        db.commit()

    for v in villages:
        va_rows = db.query(VillageAsset).filter(VillageAsset.village_id == v.village_id).all()
        asset_ids = [va.asset_id for va in va_rows]
        assets = db.query(Asset).filter(Asset.asset_id.in_(asset_ids)).all() if asset_ids else []
        tickers = [a.symbol for a in assets if a.symbol]

        total_assets = 0.0
        total_cost = 0.0
        for asset in assets:
            up = (
                db.query(UserPortfolio)
                .filter(UserPortfolio.user_id == user_id, UserPortfolio.asset_id == asset.asset_id)
                .first()
            )
            if not up:
                continue
            qty = float(up.quantity or 0)
            avg = float(up.avg_buy_price or 0)
            price = asset_prices.get(asset.asset_id, 0.0)
            total_assets += qty * price
            total_cost += qty * avg

        total_assets_all += total_assets
        return_rate = (total_assets - total_cost) / total_cost * 100.0 if total_cost > 0 else 0.0

        items.append(
            CustomVillageItem(
                id=v.village_id,
                name=v.name,
                icon=v.icon,
                total_assets=round(total_assets, 0),
                return_rate=round(return_rate, 2),
                portfolio_weight=0.0,
                asset_tickers=tickers,
            )
        )

    # update portfolio weights
    for item in items:
        if total_assets_all > 0:
            item.portfolio_weight = round(item.total_assets / total_assets_all * 100.0, 1)

    return CustomVillagesResponse(
        user_id=user_id,
        filter="custom",
        villages=items,
    )


@router.get("/{village_id}/summary", response_model=VillageSummaryResponse)
def get_village_summary(
    village_id: int,
    user_id: int = Query(...),
    db: Session = Depends(get_db),
) -> VillageSummaryResponse:
    village = (
        db.query(Village)
        .filter(Village.user_id == user_id, Village.village_id == village_id)
        .first()
    )
    if not village:
        raise HTTPException(status_code=404, detail="Village not found.")

    va_rows = db.query(VillageAsset).filter(VillageAsset.village_id == village_id).all()
    asset_ids = [va.asset_id for va in va_rows]
    assets = db.query(Asset).filter(Asset.asset_id.in_(asset_ids)).all() if asset_ids else []
    asset_items = [
        VillageAssetItem(asset_id=a.asset_id, ticker=a.symbol, name=a.name) for a in assets
    ]

    # refresh prices (KRW 기준)
    tickers = [a.symbol for a in assets if a.symbol]
    price_tickers = []
    price_symbol_map = {}
    for a in assets:
        symbol = a.symbol
        if symbol.isdigit() and len(symbol) == 6:
            yf_symbol = f"{symbol}.KS"
        else:
            yf_symbol = symbol
        price_tickers.append(yf_symbol)
        price_symbol_map[a.asset_id] = yf_symbol
    __import__("logging").getLogger(__name__).warning(
        "Village detail price_tickers: village_id=%s count=%d tickers=%s",
        village_id,
        len(price_tickers),
        price_tickers,
    )

    market_ctx = asyncio.run(get_market_context([], news_per_ticker=0, price_tickers=price_tickers))
    usdkrw_rate = get_usdkrw_rate()
    quotes_map = {q.ticker: q for q in market_ctx.ticker_quotes or [] if q and q.ticker}
    price_updates = {}
    for a in assets:
        quote = quotes_map.get(price_symbol_map.get(a.asset_id, a.symbol))
        if quote and quote.price is not None:
            price = float(quote.price)
            if a.country_code == "US":
                price *= usdkrw_rate
            price_updates[a.asset_id] = price
    if price_updates:
        from sqlalchemy.dialects.mysql import insert as mysql_insert

        now = datetime.utcnow()
        rows = [{"asset_id": aid, "price": p, "as_of": now} for aid, p in price_updates.items()]
        stmt = mysql_insert(AssetPrice).values(rows)
        stmt = stmt.on_duplicate_key_update(price=stmt.inserted.price, as_of=stmt.inserted.as_of)
        db.execute(stmt)
        db.commit()

    asset_prices = {row.asset_id: float(row.price) for row in db.query(AssetPrice).all()}

    total_assets = 0.0
    total_cost = 0.0
    for asset in assets:
        up = (
            db.query(UserPortfolio)
            .filter(UserPortfolio.user_id == user_id, UserPortfolio.asset_id == asset.asset_id)
            .first()
        )
        if not up:
            continue
        qty = float(up.quantity or 0)
        avg = float(up.avg_buy_price or 0)
        price = asset_prices.get(asset.asset_id, 0.0)
        total_assets += qty * price
        total_cost += qty * avg

    return_rate = (total_assets - total_cost) / total_cost * 100.0 if total_cost > 0 else 0.0

    # portfolio weight (vs all user assets)
    total_assets_all = 0.0
    all_assets = (
        db.query(UserPortfolio, Asset)
        .join(Asset, Asset.asset_id == UserPortfolio.asset_id)
        .filter(UserPortfolio.user_id == user_id)
        .all()
    )
    for p, a in all_assets:
        qty = float(p.quantity or 0)
        avg = float(p.avg_buy_price or 0)
        price = asset_prices.get(a.asset_id, 0.0)
        total_assets_all += qty * price

    portfolio_weight = (total_assets / total_assets_all * 100.0) if total_assets_all > 0 else 0.0

    metrics = VillageMetrics(
        total_assets=round(total_assets, 0),
        return_rate=round(return_rate, 2),
        portfolio_weight=round(portfolio_weight, 1),
        display=VillageMetricsDisplay(
            total_assets=f"{total_assets:,.0f}원",
            return_rate=f"{return_rate:+.1f}%",
            portfolio_weight=f"{portfolio_weight:.1f}%",
        ),
    )

    return VillageSummaryResponse(
        user_id=user_id,
        village=VillageSummary(
            id=village.village_id,
            name=village.name,
            icon=village.icon,
            metrics=metrics,
            assets=VillageAssetsSection(count=len(asset_items), items=asset_items),
            ai_one_liner=village.ai_one_liner,
        ),
    )


@router.get("/{village_id}/detail", response_model=VillageDetailResponse)
def get_village_detail(
    village_id: int,
    user_id: int = Query(...),
    db: Session = Depends(get_db),
) -> VillageDetailResponse:
    logger = __import__("logging").getLogger(__name__)
    logger.warning("Village detail start: user_id=%s village_id=%s", user_id, village_id)
    village = (
        db.query(Village)
        .filter(Village.user_id == user_id, Village.village_id == village_id)
        .first()
    )
    if not village:
        raise HTTPException(status_code=404, detail="Village not found.")
    logger.warning("Village detail village: id=%s name=%s icon=%s", village.village_id, village.name, village.icon)

    va_rows = db.query(VillageAsset).filter(VillageAsset.village_id == village_id).all()
    logger.warning("Village detail assets mapping count=%d", len(va_rows))
    asset_ids = [va.asset_id for va in va_rows]
    assets = db.query(Asset).filter(Asset.asset_id.in_(asset_ids)).all() if asset_ids else []
    logger.warning("Village detail assets loaded count=%d ids=%s", len(assets), asset_ids)

    # refresh prices (KRW 기준)
    tickers = [a.symbol for a in assets if a.symbol]
    price_tickers = []
    price_symbol_map = {}
    for a in assets:
        symbol = a.symbol
        if a.country_code == "KR" and symbol.isdigit() and len(symbol) == 6:
            yf_symbol = f"{symbol}.KS"
        else:
            yf_symbol = symbol
        price_tickers.append(yf_symbol)
        price_symbol_map[a.asset_id] = yf_symbol

    market_ctx = asyncio.run(get_market_context([], news_per_ticker=0, price_tickers=price_tickers))
    logger.warning("Village detail quotes received: count=%d", len(market_ctx.ticker_quotes or []))
    usdkrw_rate = get_usdkrw_rate()
    quotes_map = {q.ticker: q for q in market_ctx.ticker_quotes or [] if q and q.ticker}
    price_updates = {}
    for a in assets:
        quote = quotes_map.get(price_symbol_map.get(a.asset_id, a.symbol))
        if quote and quote.price is not None:
            price = float(quote.price)
            if a.country_code == "US":
                price *= usdkrw_rate
            price_updates[a.asset_id] = price
    if price_updates:
        from sqlalchemy.dialects.mysql import insert as mysql_insert
        now = datetime.utcnow()
        rows = [{"asset_id": aid, "price": p, "as_of": now} for aid, p in price_updates.items()]
        stmt = mysql_insert(AssetPrice).values(rows)
        stmt = stmt.on_duplicate_key_update(price=stmt.inserted.price, as_of=stmt.inserted.as_of)
        db.execute(stmt)
        db.commit()
    logger.warning("Village detail price_updates count=%d keys=%s", len(price_updates), list(price_updates.keys()))

    asset_prices = {row.asset_id: float(row.price) for row in db.query(AssetPrice).all()}

    total_assets = 0.0
    total_cost = 0.0
    holding_items: List[HoldingItem] = []
    for asset in assets:
        up = (
            db.query(UserPortfolio)
            .filter(UserPortfolio.user_id == user_id, UserPortfolio.asset_id == asset.asset_id)
            .first()
        )
        if not up:
            continue
        qty = float(up.quantity or 0)
        avg = float(up.avg_buy_price or 0)
        price = asset_prices.get(asset.asset_id, 0.0)
        value = qty * price
        total_assets += value
        total_cost += qty * avg

        quote = quotes_map.get(price_symbol_map.get(asset.asset_id, asset.symbol))
        daily_change = float(quote.change_percent) if quote and quote.change_percent is not None else 0.0

        holding_items.append(
            HoldingItem(
                asset_id=asset.asset_id,
                ticker=asset.symbol,
                name=asset.name,
                category=_categorize_asset(asset),
                value=round(value, 0),
                daily_change_rate=round(daily_change, 2),
                display=HoldingDisplay(
                    value=f"{value:,.0f}원",
                    daily_change_rate=f"{daily_change:+.2f}%",
                ),
            )
        )
    logger.warning("Village detail holdings count=%d", len(holding_items))

    return_rate = (total_assets - total_cost) / total_cost * 100.0 if total_cost > 0 else 0.0

    # portfolio weight (vs all user assets)
    total_assets_all = 0.0
    all_assets = (
        db.query(UserPortfolio, Asset)
        .join(Asset, Asset.asset_id == UserPortfolio.asset_id)
        .filter(UserPortfolio.user_id == user_id)
        .all()
    )
    for p, a in all_assets:
        qty = float(p.quantity or 0)
        avg = float(p.avg_buy_price or 0)
        price = asset_prices.get(a.asset_id, 0.0)
        total_assets_all += qty * price
    portfolio_weight = (total_assets / total_assets_all * 100.0) if total_assets_all > 0 else 0.0

    summary_cards = SummaryCards(
        total_assets=round(total_assets, 0),
        current_return_rate=round(return_rate, 2),
        holding_count=len(holding_items),
        display=SummaryCardsDisplay(
            total_assets=f"{total_assets:,.0f}원",
            current_return_rate=f"{return_rate:+.1f}%",
            holding_count=f"{len(holding_items)}개",
        ),
    )

    # monthly return trend (asset_price_monthly 기반)
    qty_map = {
        p.asset_id: float(p.quantity or 0)
        for p, _a in db.query(UserPortfolio, Asset)
        .join(Asset, Asset.asset_id == UserPortfolio.asset_id)
        .filter(UserPortfolio.user_id == user_id, UserPortfolio.asset_id.in_(asset_ids))
        .all()
    }
    monthly_rows = (
        db.query(AssetPriceMonthly)
        .filter(AssetPriceMonthly.asset_id.in_(asset_ids))
        .order_by(AssetPriceMonthly.month.asc())
        .all()
    )
    month_list = sorted({row.month for row in monthly_rows})
    price_map = {(row.asset_id, row.month): float(row.close_price) for row in monthly_rows}

    monthly_items: List[MonthlyReturnItem] = []
    for i in range(1, len(month_list)):
        month = month_list[i]
        prev_month = month_list[i - 1]
        # 가중치 계산
        total_value = 0.0
        weighted_return = 0.0
        for aid in asset_ids:
            qty = qty_map.get(aid, 0.0)
            cur_price = price_map.get((aid, month))
            prev_price = price_map.get((aid, prev_month))
            if qty <= 0 or cur_price is None or prev_price is None or prev_price == 0:
                continue
            value = qty * cur_price
            total_value += value
            asset_return = (cur_price - prev_price) / prev_price * 100.0
            weighted_return += asset_return * value
        rate = weighted_return / total_value if total_value > 0 else 0.0
        monthly_items.append(MonthlyReturnItem(month=month.month, return_rate=round(rate, 2)))

    monthly_trend = MonthlyReturnTrend(title="월별 수익률 추이", unit="percent", items=monthly_items)

    village_overview = VillageOverview(
        title=f"{village.name} 요약",
        total_assets=round(total_assets, 0),
        return_rate=round(return_rate, 2),
        portfolio_weight=round(portfolio_weight, 1),
        display=VillageOverviewDisplay(
            total_assets=f"{total_assets:,.0f}원",
            return_rate=f"{return_rate:+.1f}%",
            portfolio_weight=f"{portfolio_weight:.1f}%",
        ),
    )

    return VillageDetailResponse(
        user_id=user_id,
        village=VillageDetailHeader(id=village.village_id, name=village.name, icon=village.icon),
        summary_cards=summary_cards,
        monthly_return_trend=monthly_trend,
        village_overview=village_overview,
        holdings=HoldingsSection(title="보유 자산", items=holding_items),
        ai_one_liner=village.ai_one_liner,
    )
