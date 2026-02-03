"""
매일 아침 8시 브리핑 생성 백그라운드 작업 엔트리 포인트.

- CLI: python -m app.tasks.briefing_task
- Celery: app.tasks.briefing_task.run_morning_briefing.delay()
- Cron: 0 8 * * * cd /path && python -m app.tasks.briefing_task
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from app.core.database import SessionLocal
from app.domain.briefing.schema.request import BriefingGenerateRequest
from app.domain.briefing.schema.response import BriefingGenerateResponse
from app.services.briefing import generate_briefing

logger = logging.getLogger(__name__)


async def _generate_briefing_async(
    user_id: int,
    village_id: int,
    time_slot: str = "morning",
) -> Optional[BriefingGenerateResponse]:
    """
    비동기 브리핑 생성.
    """
    req = BriefingGenerateRequest(user_id=user_id, village_id=village_id, time_slot=time_slot)
    db = SessionLocal()
    try:
        return await generate_briefing(req, db=db)
    except Exception as e:
        logger.exception("Briefing generation failed: %s", e)
        return None
    finally:
        db.close()


def run_morning_briefing(
    user_id: int,
    village_id: int,
    time_slot: str = "morning",
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
                user_id=user_id,
                village_id=village_id,
                time_slot=time_slot,
            )
        )
    except Exception as e:
        logger.exception("run_morning_briefing failed: %s", e)
        return None

    if result is None:
        return None
    return result.model_dump()


def main() -> None:
    """CLI: python -m app.tasks.briefing_task"""
    logging.basicConfig(level=logging.INFO)
    out = run_morning_briefing(user_id=1, village_id=101, time_slot="morning")
    if out:
        logger.info("Briefing generated. keys=%s", list(out.keys()))
    else:
        logger.warning("Briefing generation returned nothing.")


if __name__ == "__main__":
    main()
