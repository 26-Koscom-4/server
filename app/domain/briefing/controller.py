from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.domain.briefing.schema.request import BriefingGenerateRequest
from app.domain.briefing.schema.response import BriefingGenerateResponse
from app.core.database import get_db
from app.domain.briefing.model import BriefingSnapshot
from app.services.briefing import generate_briefing

router = APIRouter()


@router.post("/generate", response_model=BriefingGenerateResponse)
async def post_briefing_generate(
    payload: BriefingGenerateRequest,
    db: Session = Depends(get_db),
) -> BriefingGenerateResponse:
    """브리핑 생성 API."""
    try:
        return await generate_briefing(payload, db=db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/latest", response_model=BriefingGenerateResponse)
def get_latest_briefing(
    user_id: int = Query(...),
    village_id: int = Query(...),
    db: Session = Depends(get_db),
) -> BriefingGenerateResponse:
    """가장 최신 브리핑 스냅샷 조회."""
    latest = (
        db.query(BriefingSnapshot)
        .filter(BriefingSnapshot.user_id == user_id, BriefingSnapshot.village_id == village_id)
        .order_by(desc(BriefingSnapshot.created_at))
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No briefing snapshot found.")
    return BriefingGenerateResponse(**latest.payload_json)
