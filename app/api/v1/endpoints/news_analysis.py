"""뉴스 분석 API: 사용자 보유 주식 기반 뉴스 분석."""

import asyncio
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.user import User
from app.models.village import Village as VillageModel, VillageAsset as VillageAssetModel
from app.services.briefing.agents.news_agent import analyze_news_data
from app.services.market_data import get_market_context

logger = logging.getLogger(__name__)
router = APIRouter()


class NewsAnalysisRequest(BaseModel):
    """뉴스 분석 요청."""

    user_id: str = Field(..., description="사용자 ID")
    time_slot: str = Field("morning", description="시간대 (morning/evening)")
    news_limit_per_ticker: int = Field(3, ge=1, le=10, description="종목당 뉴스 개수")


class NewsHeadline(BaseModel):
    """주요 뉴스 헤드라인."""

    title: str
    summary: str


class NewsAnalysisResponse(BaseModel):
    """뉴스 분석 결과."""

    market_sentiment: str = Field(..., description="시장 심리 (긍정적/부정적/중립적)")
    key_headlines: List[NewsHeadline] = Field(..., description="주요 헤드라인 3개")
    ticker_specific: Dict[str, str] = Field(..., description="종목별 뉴스 요약")
    risk_alerts: List[str] = Field(..., description="리스크 알림")
    total_news_count: int = Field(..., description="분석된 총 뉴스 개수")
    tickers: List[str] = Field(..., description="분석 대상 종목 목록")


@router.post("/analyze", response_model=NewsAnalysisResponse)
async def analyze_user_news(
    payload: NewsAnalysisRequest,
    db: Session = Depends(get_db),
) -> NewsAnalysisResponse:
    """
    사용자 ID 기반으로 보유 주식 관련 뉴스를 수집하고 AI로 분석합니다.

    ## 기능
    - 사용자의 모든 마을(포트폴리오)에서 보유 종목 추출
    - RSS 기반으로 종목별 최신 뉴스 수집
    - News Agent로 시장 심리, 주요 이슈, 리스크 분석
    - 종목별 뉴스 요약 제공

    ## 응답
    - market_sentiment: 전체 시장 분위기
    - key_headlines: 가장 중요한 뉴스 3개
    - ticker_specific: 각 종목별 뉴스 요약
    - risk_alerts: 주의해야 할 리스크 요인
    """
    # 1. 사용자 조회
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 2. 사용자의 모든 마을(포트폴리오) 조회
    db_villages = (
        db.query(VillageModel)
        .filter(VillageModel.user_id == payload.user_id)
        .options(joinedload(VillageModel.assets).joinedload(VillageAssetModel.asset))
        .all()
    )

    if not db_villages:
        raise HTTPException(status_code=404, detail="사용자의 마을(포트폴리오)이 없습니다.")

    # 3. 모든 종목의 ticker 수집
    tickers = []
    ticker_names = {}  # ticker -> name 매핑
    for village in db_villages:
        for va in village.assets:
            symbol = va.asset.yahoo_symbol or va.asset.ticker
            if symbol and symbol not in tickers:
                tickers.append(symbol)
                ticker_names[symbol] = va.asset.name

    if not tickers:
        raise HTTPException(status_code=404, detail="보유 종목이 없습니다.")

    logger.info(f"Analyzing news for user {payload.user_id}: {len(tickers)} tickers")

    # 4. RSS 기반 뉴스 수집
    market_ctx = await get_market_context(
        tickers,
        news_per_ticker=payload.news_limit_per_ticker,
        include_general_news=True,
    )

    news_items = market_ctx.news_items or []
    if not news_items:
        raise HTTPException(
            status_code=404,
            detail="현재 수집된 뉴스가 없습니다. 잠시 후 다시 시도해 주세요.",
        )

    logger.info(f"Collected {len(news_items)} news items for analysis")

    # 5. News Agent로 분석
    analysis_result = await asyncio.to_thread(
        analyze_news_data,
        news_items,
        tickers,
        user.name,
        payload.time_slot,
    )

    if not analysis_result:
        raise HTTPException(
            status_code=500,
            detail="뉴스 분석에 실패했습니다. API 키를 확인하거나 잠시 후 다시 시도해 주세요.",
        )

    # 6. 응답 생성
    key_headlines = []
    for headline in analysis_result.get("key_headlines", [])[:3]:
        if isinstance(headline, dict):
            key_headlines.append(
                NewsHeadline(
                    title=headline.get("title", ""),
                    summary=headline.get("summary", ""),
                )
            )

    return NewsAnalysisResponse(
        market_sentiment=analysis_result.get("market_sentiment", "정보 없음"),
        key_headlines=key_headlines,
        ticker_specific=analysis_result.get("ticker_specific", {}),
        risk_alerts=analysis_result.get("risk_alerts", []),
        total_news_count=len(news_items),
        tickers=tickers,
    )


@router.get("/headlines", response_model=Dict[str, List[Dict[str, str]]])
async def get_user_news_headlines(
    user_id: str = Query(..., description="사용자 ID"),
    limit_per_ticker: int = Query(3, ge=1, le=10, description="종목당 뉴스 개수"),
    db: Session = Depends(get_db),
) -> Dict[str, List[Dict[str, str]]]:
    """
    사용자 보유 종목의 최신 뉴스 헤드라인만 간단히 조회 (AI 분석 없이).

    ## 응답
    - 종목별로 그룹화된 뉴스 헤드라인 목록
    - AI 분석을 원하면 POST /analyze 사용
    """
    # 1. 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 2. 종목 수집
    db_villages = (
        db.query(VillageModel)
        .filter(VillageModel.user_id == user_id)
        .options(joinedload(VillageModel.assets).joinedload(VillageAssetModel.asset))
        .all()
    )

    if not db_villages:
        raise HTTPException(status_code=404, detail="사용자의 마을(포트폴리오)이 없습니다.")

    tickers = []
    ticker_names = {}
    for village in db_villages:
        for va in village.assets:
            symbol = va.asset.yahoo_symbol or va.asset.ticker
            if symbol and symbol not in tickers:
                tickers.append(symbol)
                ticker_names[symbol] = va.asset.name

    if not tickers:
        raise HTTPException(status_code=404, detail="보유 종목이 없습니다.")

    # 3. 뉴스 수집
    market_ctx = await get_market_context(tickers, news_per_ticker=limit_per_ticker)
    news_items = market_ctx.news_items or []

    # 4. 종목별로 그룹화
    result = {}
    for item in news_items:
        item_tickers = item.get("tickers", [])
        for ticker in item_tickers:
            if ticker in tickers:
                if ticker not in result:
                    result[ticker] = []
                result[ticker].append({
                    "title": item.get("title", ""),
                    "summary": item.get("summary", ""),
                    "source": item.get("source", ""),
                    "link": item.get("link", ""),
                    "published": item.get("published", ""),
                })

    return result
