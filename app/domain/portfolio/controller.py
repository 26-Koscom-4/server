from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.portfolio.schema.response import PortfolioSummaryResponse
from app.domain.portfolio.schema.response import RebalancingRecommendation
from app.services.portfolio.summary import build_portfolio_summary, generate_rebalancing_snapshot, get_latest_rebalancing

router = APIRouter()


@router.get("/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
) -> PortfolioSummaryResponse:
    return await build_portfolio_summary(user_id=user_id, db=db)


@router.post("/rebalancing/generate", response_model=list[RebalancingRecommendation])
async def generate_rebalancing(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
) -> list[RebalancingRecommendation]:
    return await generate_rebalancing_snapshot(user_id=user_id, db=db)


@router.get("/rebalancing/latest", response_model=list[RebalancingRecommendation])
def latest_rebalancing(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
) -> list[RebalancingRecommendation]:
    latest = get_latest_rebalancing(user_id=user_id, db=db)
    if latest is None:
        raise HTTPException(status_code=404, detail="No rebalancing snapshot found.")
    return latest
