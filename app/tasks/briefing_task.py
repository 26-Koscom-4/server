"""
매일 아침 8시 브리핑 생성 백그라운드 작업 엔트리 포인트.

- CLI: python -m app.tasks.briefing_task
- Celery: app.tasks.briefing_task.run_morning_briefing.delay()
- Cron: 0 8 * * * cd /path && python -m app.tasks.briefing_task
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from app.domain.briefing.schema.request import BriefingGenerateRequest
from app.domain.briefing.schema.response import BriefingGenerateResponse
from app.domain.village.schema.dto import Village, VillageAsset
from app.services.briefing import generate_briefing
from app.utils.fixtures import FixtureInvalid, FixtureNotFound, load_fixture

logger = logging.getLogger(__name__)


def _load_villages_from_fixture() -> Optional[list]:
    """fixture에서 villages 로드. 실패 시 None."""
    try:
        data = load_fixture("ui_state_villages.json")
        return data.get("villages") or []
    except (FixtureNotFound, FixtureInvalid) as e:
        logger.warning("Failed to load villages fixture: %s", e)
        return None


def _villages_dict_to_models(villages_raw: list) -> list:
    """dict 리스트를 Village Pydantic 모델 리스트로 변환."""
    out = []
    for v in villages_raw:
        assets = []
        for a in v.get("assets") or []:
            assets.append(
                VillageAsset(
                    id=a.get("id", ""),
                    name=a.get("name", ""),
                    type=a.get("type", ""),
                    ticker=a.get("ticker", ""),
                    value=a.get("value"),
                )
            )
        out.append(
            Village(
                id=v.get("id", ""),
                name=v.get("name", ""),
                icon=v.get("icon", ""),
                assets=assets,
                type=v.get("type"),
                goal=v.get("goal"),
                totalValue=v.get("totalValue"),
                returnRate=v.get("returnRate"),
                allocation=v.get("allocation"),
                lastBriefingRead=v.get("lastBriefingRead"),
            )
        )
    return out


async def _generate_briefing_async(
    user_name: str = "김직장님",
    time_slot: str = "morning",
    villages_override: Optional[list] = None,
) -> Optional[BriefingGenerateResponse]:
    """
    비동기 브리핑 생성. villages_override가 없으면 fixture에서 villages 로드.
    """
    villages_raw = villages_override or _load_villages_from_fixture()
    if not villages_raw:
        logger.warning("No villages data; skipping briefing generation.")
        return None

    villages = _villages_dict_to_models(villages_raw)
    req = BriefingGenerateRequest(
        villages=villages,
        news_items=None,
        user_name=user_name,
        time_slot=time_slot,
    )
    try:
        return await generate_briefing(req)
    except Exception as e:
        logger.exception("Briefing generation failed: %s", e)
        return None


def run_morning_briefing(
    user_name: str = "김직장님",
    time_slot: str = "morning",
    villages_override: Optional[list] = None,
) -> Optional[Dict[str, Any]]:
    """
    매일 아침 브리핑 생성 동기 엔트리 포인트.
    Celery/cron에서 호출 시 이 함수를 사용.

    Returns:
        생성된 브리핑의 voice_script, briefing_card를 담은 dict. 실패 시 None.
    """
    try:
        result = asyncio.run(
            _generate_briefing_async(
                user_name=user_name,
                time_slot=time_slot,
                villages_override=villages_override,
            )
        )
    except Exception as e:
        logger.exception("run_morning_briefing failed: %s", e)
        return None

    if result is None:
        return None
    return {
        "voice_script": result.voice_script,
        "briefing_card": result.briefing_card.model_dump(),
    }


def main() -> None:
    """CLI: python -m app.tasks.briefing_task"""
    logging.basicConfig(level=logging.INFO)
    out = run_morning_briefing(user_name="김직장님", time_slot="morning")
    if out:
        logger.info("Briefing generated. voice_script length=%d", len(out.get("voice_script", "")))
        # 실제 서비스에서는 여기서 DB 저장, 푸시 발송 등 연동
    else:
        logger.warning("Briefing generation returned nothing.")


if __name__ == "__main__":
    main()
