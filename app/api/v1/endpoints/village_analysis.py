"""마을 단위 주식 분석 API: 시세 + 뉴스 통합 분석."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.user import User
from app.models.village import Village as VillageModel, VillageAsset as VillageAssetModel, VillageMetricsDaily
from app.services.briefing.agents.news_agent import analyze_news_data
from app.services.briefing.agents.orchestrator import orchestrate_briefing
from app.services.briefing.agents.stock_agent import analyze_stock_data
from app.services.market_data import get_market_context

logger = logging.getLogger(__name__)
router = APIRouter()


class VillageAnalysisRequest(BaseModel):
    """마을 분석 요청."""

    user_id: str = Field(..., description="사용자 ID")
    village_ids: Optional[List[str]] = Field(None, description="분석할 마을 ID 목록 (없으면 전체)")
    time_slot: str = Field("morning", description="시간대 (morning/evening)")
    news_per_ticker: int = Field(3, ge=1, le=10, description="종목당 뉴스 개수")


class AssetInfo(BaseModel):
    """자산 정보."""

    name: str
    ticker: str
    current_price: float
    return_rate: float
    change_percent: float


class VillageAnalysis(BaseModel):
    """마을별 분석 결과."""

    village_id: str
    village_name: str
    village_icon: str
    village_type: str
    village_goal: str

    # 마을 현황
    total_value: int = Field(..., description="총 자산")
    return_rate: float = Field(..., description="수익률")
    allocation: float = Field(..., description="포트폴리오 비중")

    # 보유 자산
    assets: List[AssetInfo] = Field(..., description="보유 자산 목록")

    # 주식 시세 분석
    stock_analysis: Optional[Dict[str, Any]] = Field(None, description="Stock Agent 분석 결과")

    # 뉴스 분석
    news_analysis: Optional[Dict[str, Any]] = Field(None, description="News Agent 분석 결과")

    # 통합 브리핑
    voice_script: str = Field(..., description="음성 브리핑 스크립트")
    advice: List[str] = Field(..., description="투자 조언")
    checklist: List[str] = Field(..., description="체크리스트")


class VillageAnalysisResponse(BaseModel):
    """마을 분석 응답."""

    user_name: str
    total_villages: int
    villages: List[VillageAnalysis]


async def _analyze_single_village(
    village: VillageModel,
    user_name: str,
    time_slot: str,
    news_per_ticker: int,
    db: Session,
) -> VillageAnalysis:
    """단일 마을 분석."""
    village_id = village.id
    logger.info(f"Analyzing village: {village.name} ({village_id})")

    # 1. 마을의 모든 자산 ticker 수집
    tickers = []
    assets_data = []
    for va in village.assets:
        symbol = va.asset.yahoo_symbol or va.asset.ticker
        if symbol:
            tickers.append(symbol)
            assets_data.append({
                "id": va.id,
                "name": va.asset.name,
                "ticker": va.asset.ticker,
                "type": va.asset.asset_type,
                "yahoo_symbol": va.asset.yahoo_symbol,
                "value": va.value,
                "quantity": float(va.quantity) if va.quantity else 0,
                "avg_price": float(va.avg_price) if va.avg_price else 0,
            })

    if not tickers:
        raise HTTPException(status_code=400, detail=f"마을 '{village.name}'에 보유 종목이 없습니다.")

    # 2. 실시간 시세 + 뉴스 수집
    market_ctx = await get_market_context(
        tickers,
        news_per_ticker=news_per_ticker,
        include_general_news=False,  # 마을별 분석이므로 일반 뉴스는 제외
    )

    ticker_quotes = market_ctx.ticker_quotes or []
    news_items = market_ctx.news_items or []

    logger.info(f"Village {village.name}: {len(ticker_quotes)} quotes, {len(news_items)} news")

    # 3. 마을 메트릭 조회
    latest_metric = (
        db.query(VillageMetricsDaily)
        .filter(VillageMetricsDaily.village_id == village_id)
        .order_by(desc(VillageMetricsDaily.metric_date))
        .first()
    )

    total_value = int(latest_metric.total_value) if latest_metric else 0
    return_rate = float(latest_metric.return_rate) if latest_metric and latest_metric.return_rate else 0.0
    allocation = float(latest_metric.allocation) if latest_metric and latest_metric.allocation else 0.0

    # 4. 자산별 현재가 및 수익률 계산
    ticker_prices = {q.ticker: q for q in ticker_quotes}
    assets_info = []

    for asset in assets_data:
        symbol = asset.get("yahoo_symbol") or asset.get("ticker")
        quote = ticker_prices.get(symbol)

        current_price = quote.price if quote and quote.price else 0.0
        change_percent = quote.change_percent if quote and quote.change_percent else 0.0

        # 수익률 계산
        return_rate_asset = 0.0
        avg_price = asset.get("avg_price", 0)
        if avg_price and current_price > 0:
            return_rate_asset = ((current_price - avg_price) / avg_price) * 100

        assets_info.append(
            AssetInfo(
                name=asset["name"],
                ticker=asset["ticker"],
                current_price=current_price,
                return_rate=return_rate_asset,
                change_percent=change_percent,
            )
        )

    # 5. 마을 데이터 구성
    village_data = {
        "id": village_id,
        "name": village.name,
        "icon": village.icon,
        "type": village.type or "growth",
        "goal": village.goal or "long-term",
        "totalValue": total_value,
        "returnRate": return_rate,
        "allocation": allocation,
        "assets": [
            {
                "name": a.name,
                "ticker": a.ticker,
                "current_price": a.current_price,
                "return_rate": a.return_rate,
            }
            for a in assets_info
        ],
    }

    # 6. Agent 병렬 실행
    stock_task = asyncio.create_task(
        asyncio.to_thread(
            analyze_stock_data,
            ticker_quotes,
            [village_data],
            user_name,
            time_slot,
        )
    )

    news_task = asyncio.create_task(
        asyncio.to_thread(
            analyze_news_data,
            news_items,
            tickers,
            user_name,
            time_slot,
        )
    )

    stock_analysis, news_analysis = await asyncio.gather(
        stock_task, news_task, return_exceptions=True
    )

    # Exception 처리
    if isinstance(stock_analysis, Exception):
        logger.error(f"Stock analysis failed for village {village.name}: {stock_analysis}")
        stock_analysis = None
    if isinstance(news_analysis, Exception):
        logger.error(f"News analysis failed for village {village.name}: {news_analysis}")
        news_analysis = None

    # 7. Orchestrator로 통합 브리핑 생성
    voice_script, visual_summary = orchestrate_briefing(
        stock_analysis,
        news_analysis,
        [village_data],
        user_name,
        time_slot,
    )

    advice = visual_summary.get("advice", [])
    checklist = visual_summary.get("checklist", [])

    return VillageAnalysis(
        village_id=village_id,
        village_name=village.name,
        village_icon=village.icon,
        village_type=village.type or "growth",
        village_goal=village.goal or "long-term",
        total_value=total_value,
        return_rate=return_rate,
        allocation=allocation,
        assets=assets_info,
        stock_analysis=stock_analysis,
        news_analysis=news_analysis,
        voice_script=voice_script,
        advice=advice if isinstance(advice, list) else [],
        checklist=checklist if isinstance(checklist, list) else [],
    )


@router.post("/analyze", response_model=VillageAnalysisResponse)
async def analyze_villages(
    payload: VillageAnalysisRequest,
    db: Session = Depends(get_db),
) -> VillageAnalysisResponse:
    """
    사용자의 마을(포트폴리오)별로 시세 + 뉴스 통합 분석.

    ## 기능
    - 마을별 독립적인 분석 (각 마을의 투자 전략/목표에 맞춤)
    - 실시간 시세 분석 (Stock Agent)
    - 뉴스 분석 (News Agent)
    - 통합 브리핑 (Orchestrator)
    - 마을별 음성 스크립트 + 조언 + 체크리스트

    ## 마을별 분석의 장점
    - 각 마을의 투자 전략에 맞는 맞춤 분석
    - 마을별 리스크 평가
    - 독립적인 의사결정 지원
    """
    # 1. 사용자 조회
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 2. 마을 조회
    query = db.query(VillageModel).filter(VillageModel.user_id == payload.user_id)

    if payload.village_ids:
        query = query.filter(VillageModel.id.in_(payload.village_ids))

    db_villages = query.options(
        joinedload(VillageModel.assets).joinedload(VillageAssetModel.asset)
    ).all()

    if not db_villages:
        raise HTTPException(status_code=404, detail="분석할 마을이 없습니다.")

    logger.info(f"Analyzing {len(db_villages)} villages for user {user.name}")

    # 3. 마을별 병렬 분석
    analysis_tasks = [
        _analyze_single_village(
            village,
            user.name,
            payload.time_slot,
            payload.news_per_ticker,
            db,
        )
        for village in db_villages
    ]

    village_analyses = await asyncio.gather(*analysis_tasks, return_exceptions=True)

    # Exception 처리
    successful_analyses = []
    for i, result in enumerate(village_analyses):
        if isinstance(result, Exception):
            logger.error(f"Village analysis failed: {result}")
            # 실패한 마을은 건너뛰기
        else:
            successful_analyses.append(result)

    if not successful_analyses:
        raise HTTPException(status_code=500, detail="모든 마을 분석에 실패했습니다.")

    return VillageAnalysisResponse(
        user_name=user.name,
        total_villages=len(successful_analyses),
        villages=successful_analyses,
    )


@router.get("/{village_id}/summary")
async def get_village_summary(
    village_id: str,
    user_id: str = Query(..., description="사용자 ID"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    특정 마을의 간단한 요약 정보 조회 (AI 분석 없이).

    ## 응답
    - 마을 기본 정보
    - 보유 자산 목록
    - 총 자산 / 수익률
    """
    # 사용자 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 마을 조회
    village = (
        db.query(VillageModel)
        .filter(VillageModel.id == village_id, VillageModel.user_id == user_id)
        .options(joinedload(VillageModel.assets).joinedload(VillageAssetModel.asset))
        .first()
    )

    if not village:
        raise HTTPException(status_code=404, detail="마을을 찾을 수 없습니다.")

    # 최근 메트릭
    latest_metric = (
        db.query(VillageMetricsDaily)
        .filter(VillageMetricsDaily.village_id == village_id)
        .order_by(desc(VillageMetricsDaily.metric_date))
        .first()
    )

    return {
        "village_id": village.id,
        "name": village.name,
        "icon": village.icon,
        "type": village.type,
        "goal": village.goal,
        "total_value": int(latest_metric.total_value) if latest_metric else 0,
        "return_rate": float(latest_metric.return_rate) if latest_metric and latest_metric.return_rate else 0.0,
        "allocation": float(latest_metric.allocation) if latest_metric and latest_metric.allocation else 0.0,
        "assets": [
            {
                "name": va.asset.name,
                "ticker": va.asset.ticker,
                "type": va.asset.asset_type,
                "value": va.value,
                "quantity": float(va.quantity) if va.quantity else 0,
                "avg_price": float(va.avg_price) if va.avg_price else 0,
            }
            for va in village.assets
        ],
    }
