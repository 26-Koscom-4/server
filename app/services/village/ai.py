"""Village AI one-liner generation."""

from __future__ import annotations

from typing import Optional
import logging
import time

from app.core.database import SessionLocal
from app.domain.village.model import Village
from app.services.briefing.llm import call_llm
from app.domain.village.model import VillageAsset
from app.domain.asset.model import Asset


FALLBACK_ONE_LINER = "마을 특징을 요약 중입니다."

logger = logging.getLogger(__name__)


def _build_prompt(
    name: str,
    vtype: Optional[str],
    goal: Optional[str],
    profile: Optional[str],
    assets: list[str],
) -> str:
    assets_text = ", ".join(assets) if assets else "없음"
    return f"""다음 마을 정보를 바탕으로 한 줄 평가를 작성해 주세요.
요구사항:
- 한국어 존댓말
- 100자 이내
- 투자 조언처럼 들리지 않게
- 특징 요약 + 평가를 한 문장으로 종합

마을명: {name}
유형: {vtype or '없음'}
목표: {goal or '없음'}
전략: {profile or '없음'}
선택 종목: {assets_text}
"""


def generate_village_one_liner(village_id: int) -> None:
    """백그라운드에서 마을 한줄평 생성 후 저장."""
    start = time.time()
    logger.warning("Village one-liner start: village_id=%s", village_id)
    db = SessionLocal()
    try:
        village = db.query(Village).filter(Village.village_id == village_id).first()
        if not village:
            logger.warning("Village one-liner abort: village not found village_id=%s", village_id)
            return
        asset_rows = (
            db.query(Asset)
            .join(VillageAsset, VillageAsset.asset_id == Asset.asset_id)
            .filter(VillageAsset.village_id == village_id)
            .all()
        )
        assets = [a.name for a in asset_rows if a.name] or [a.symbol for a in asset_rows if a.symbol]
        prompt = _build_prompt(
            village.name,
            village.type,
            village.goal,
            village.village_profile,
            assets,
        )
        raw = call_llm("마을 한줄평 생성기", prompt)
        text = (raw or "").strip()
        if not text:
            text = FALLBACK_ONE_LINER
        if len(text) > 100:
            text = text[:100]
        village.ai_one_liner = text
        db.add(village)
        db.commit()
        elapsed = time.time() - start
        logger.warning("Village one-liner done: village_id=%s elapsed=%.3fs text=%s", village_id, elapsed, text)
    finally:
        if 'elapsed' not in locals():
            elapsed = time.time() - start
            logger.warning("Village one-liner end: village_id=%s elapsed=%.3fs", village_id, elapsed)
        db.close()
