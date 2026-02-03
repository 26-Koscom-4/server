"""Monthly asset price loader."""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.domain.asset.model import Asset, AssetPriceMonthly
from app.services.market_data import get_usdkrw_rate


def _to_yf_symbol(asset: Asset) -> str:
    symbol = asset.symbol
    if symbol.isdigit() and len(symbol) == 6:
        return f"{symbol}.KS"
    return symbol


def _month_end(d: date) -> date:
    # use the date from yfinance index (already month-end for 1mo interval)
    return d


def load_monthly_prices_for_year(db: Session, year: int) -> Dict[str, int]:
    """
    Fetch monthly close prices for all assets in the given year and upsert into asset_price_monthly.
    Returns counts: {"assets": N, "rows": M}
    """
    import yfinance as yf
    from sqlalchemy.dialects.mysql import insert as mysql_insert

    start = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    usdkrw = get_usdkrw_rate()

    assets = db.query(Asset).order_by(Asset.asset_id.asc()).all()
    total_rows = 0

    for asset in assets:
        yf_symbol = _to_yf_symbol(asset)
        hist = yf.Ticker(yf_symbol).history(start=start, end=end, interval="1mo")
        if hist is None or hist.empty:
            continue
        rows: List[Dict] = []
        for idx, row in hist.iterrows():
            close_price = float(row["Close"])
            if asset.country_code == "US":
                close_price *= usdkrw
            month_date = _month_end(idx.date())
            rows.append(
                {
                    "asset_id": asset.asset_id,
                    "month": month_date,
                    "close_price": close_price,
                }
            )
        if not rows:
            continue
        stmt = mysql_insert(AssetPriceMonthly).values(rows)
        stmt = stmt.on_duplicate_key_update(
            close_price=stmt.inserted.close_price,
        )
        db.execute(stmt)
        db.commit()
        total_rows += len(rows)

    return {"assets": len(assets), "rows": total_rows}
