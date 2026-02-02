"""개미 마을 수석 이장 브리핑 생성 API."""

from fastapi import APIRouter, HTTPException

from app.core.briefing_store import get_latest
from app.schemas.briefing.request import BriefingGenerateRequest
from app.schemas.briefing.response import BriefingGenerateResponse, LatestBriefingResponse
from app.services.briefing import generate_briefing

router = APIRouter()


@router.get("", response_model=LatestBriefingResponse)
def get_latest_briefing() -> LatestBriefingResponse:
    """
    가장 최근에 생성된 브리핑을 반환합니다.
    스케줄(매일 9시·17시)로 생성된 '오늘의 투자 포인트' 요약(한국어)입니다.
    아직 한 번도 생성되지 않았으면 404를 반환합니다.
    """
    latest = get_latest()
    if not latest:
        raise HTTPException(status_code=404, detail="아직 생성된 브리핑이 없습니다. 스케줄(9시/17시) 실행 후 조회해 주세요.")
    return LatestBriefingResponse(
        summary=latest["summary"],
        generated_at=latest["generated_at"],
        news_count=latest["news_count"],
        tickers=latest.get("tickers") or [],
    )


@router.post("/generate", response_model=BriefingGenerateResponse)
async def post_briefing_generate(payload: BriefingGenerateRequest) -> BriefingGenerateResponse:
    """
    포트폴리오(villages) 기준으로 실시간 시세·뉴스를 수집한 뒤 TTS용 스크립트 + UI용 요약을 생성합니다.
    시세/뉴스 API 실패 시 빈 데이터로 진행하며, LLM 키가 없으면 목(mock) 브리핑을 반환합니다.
    """
    return await generate_briefing(payload)
