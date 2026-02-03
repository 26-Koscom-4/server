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
    InvestmentProfile,
    ActionItem,
)
from app.domain.asset.model import Asset, AssetPrice
from app.domain.portfolio.model import UserPortfolio
from app.services.market_data import get_market_context, get_usdkrw_rate
from app.services.village.ai import generate_village_one_liner

router = APIRouter()


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

    market_ctx = asyncio.run(get_market_context([], news_per_ticker=0, price_tickers=price_tickers))
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
        if a.country_code == "KR" and symbol.isdigit() and len(symbol) == 6:
            yf_symbol = f"{symbol}.KS"
        else:
            yf_symbol = symbol
        price_tickers.append(yf_symbol)
        price_symbol_map[a.asset_id] = yf_symbol

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

    investment_profile = InvestmentProfile(
        investment_type=village.type or "",
        investment_goal=village.goal or "",
    )

    return VillageSummaryResponse(
        user_id=user_id,
        village=VillageSummary(
            id=village.village_id,
            name=village.name,
            icon=village.icon,
            metrics=metrics,
            assets=VillageAssetsSection(count=len(asset_items), items=asset_items),
            investment_profile=investment_profile,
        ),
        actions={
            "primary": ActionItem(label="마을로 이동", action="navigate", target=f"/villages/{village_id}"),
            "secondary": ActionItem(label="닫기", action="close"),
        },
    )
