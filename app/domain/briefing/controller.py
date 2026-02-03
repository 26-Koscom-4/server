from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domain.briefing.schema.request import BriefingGenerateRequest
from app.domain.briefing.schema.response import BriefingGenerateResponse
from app.core.database import get_db
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
