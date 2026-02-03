from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.asset.schema.response import AvailableAssetItem, AvailableAssetsResponse
from app.domain.asset.model import Asset
from app.domain.portfolio.model import UserPortfolio

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


@router.get("/available", response_model=AvailableAssetsResponse)
def get_available_assets(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
) -> AvailableAssetsResponse:
    assets = (
        db.query(Asset)
        .join(UserPortfolio, UserPortfolio.asset_id == Asset.asset_id)
        .filter(UserPortfolio.user_id == user_id)
        .order_by(Asset.asset_id.asc())
        .all()
    )
    items = [
        AvailableAssetItem(
            asset_id=a.asset_id,
            ticker=a.symbol,
            name=a.name,
            category=_categorize_asset(a),
        )
        for a in assets
    ]
    return AvailableAssetsResponse(user_id=user_id, available_assets=items)
