from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.domain.asset.model import Asset, AssetPrice
from app.domain.dashboard.schema.response import (
    Allocation,
    AllocationGroup,
    AllocationItem,
    DashboardResponse,
    MdaInfo,
)
from app.domain.portfolio.model import UserPortfolio
from app.domain.user.model import User


def _decimal_to_int(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_HALF_UP))


def _build_items(
    totals: Dict[str, Decimal],
    total_value: Decimal,
    label_map: Dict[str, str],
) -> List[AllocationItem]:
    items: List[Tuple[str, Decimal]] = sorted(
        totals.items(),
        key=lambda item: item[1],
        reverse=True,
    )
    out: List[AllocationItem] = []
    for key, value in items:
        weight = round(float(value / total_value), 5) if total_value > 0 else 0.0
        label = label_map.get(key.upper(), key)
        out.append(
            AllocationItem(
                key=key,
                label=label,
                marketValue=_decimal_to_int(value),
                weight=weight,
            )
        )
    return out


def get_dashboard(user_id: int, db: Session) -> DashboardResponse | None:
    user = db.get(User, user_id)
    if user is None:
        return None

    latest_price_subq = (
        select(
            AssetPrice.asset_id.label("asset_id"),
            func.max(AssetPrice.as_of).label("max_as_of"),
        )
        .group_by(AssetPrice.asset_id)
        .subquery()
    )

    price_subq = (
        select(
            AssetPrice.asset_id.label("asset_id"),
            AssetPrice.price.label("price"),
        )
        .join(
            latest_price_subq,
            and_(
                AssetPrice.asset_id == latest_price_subq.c.asset_id,
                AssetPrice.as_of == latest_price_subq.c.max_as_of,
            ),
        )
        .subquery()
    )

    price_expr = func.coalesce(price_subq.c.price, UserPortfolio.avg_buy_price, 0)
    stmt = (
        select(
            UserPortfolio.quantity.label("quantity"),
            price_expr.label("price"),
            Asset.country_code.label("country"),
            Asset.asset_type.label("asset_type"),
        )
        .join(Asset, Asset.asset_id == UserPortfolio.asset_id)
        .outerjoin(price_subq, price_subq.c.asset_id == UserPortfolio.asset_id)
        .where(UserPortfolio.user_id == user_id)
    )

    rows = db.execute(stmt).all()
    total_value = Decimal("0")
    country_totals: Dict[str, Decimal] = {}
    type_totals: Dict[str, Decimal] = {}

    for row in rows:
        quantity = Decimal(str(row.quantity or 0))
        price = Decimal(str(row.price or 0))
        market_value = quantity * price
        total_value += market_value

        country_totals[row.country] = country_totals.get(row.country, Decimal("0")) + market_value
        type_totals[row.asset_type] = type_totals.get(row.asset_type, Decimal("0")) + market_value

    total_market_value = _decimal_to_int(total_value)

    country_label_map = {
        "US": "미장",
        "KR": "국장",
    }
    asset_label_map = {
        "STOCK": "주식",
        "ETF": "ETF",
    }

    return DashboardResponse(
        userId=user.user_id,
        mda=MdaInfo(mode=user.mda_mode, dataOn=(user.mda_mode == "POST")),
        hasRecommendation=True,
        totalMarketValue=total_market_value,
        allocation=Allocation(
            country=AllocationGroup(
                items=_build_items(country_totals, total_value, country_label_map)
            ),
            assetType=AllocationGroup(
                items=_build_items(type_totals, total_value, asset_label_map)
            ),
        ),
    )
