"""LLM 출력에서 [Voice Script]와 [Visual Summary] JSON 추출."""

import json
import logging
import re
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


def parse_briefing_response(raw: str) -> Tuple[str, Dict[str, Any]]:
    """
    raw 텍스트에서 [Voice Script] 블록과 [Visual Summary] JSON을 파싱.
    실패 시 기본값 반환.
    """
    if not raw:
        logger.warning("parse_briefing_response: empty raw")
    voice_script = _extract_voice_script(raw)
    visual_summary = _extract_visual_summary(raw)
    return voice_script, visual_summary


def _extract_voice_script(raw: str) -> str:
    m = re.search(r"\*{0,2}\[Voice Script\]\*{0,2}\s*(.+?)(?=\s*\*{0,2}\[Visual Summary\]\*{0,2}|$)", raw, re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1).strip()
        return " ".join(text.split())
    if raw:
        logger.warning("No [Voice Script] section found. raw=%s", raw)
    return "좋은 아침입니다. 오늘도 개미 마을 브리핑을 확인해 주세요. 본 내용은 투자 조언이 아니며, 투자 결정은 본인 판단과 책임입니다."


def _extract_visual_summary(raw: str) -> Dict[str, Any]:
    m = re.search(r"\*{0,2}\[Visual Summary\]\*{0,2}\s*(?:```json)?\s*(\{.+?\})\s*(?:```)?\s*$", raw, re.DOTALL | re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            logger.warning("Failed to parse [Visual Summary] JSON. raw=%s", raw)
    if raw:
        logger.warning("No [Visual Summary] section found. raw=%s", raw)
    return {
        "overallReturnRate": None,
        "villageHighlights": [],
        "neighborSuggestion": None,
        "disclaimer": "본 브리핑은 투자 조언이 아니며, 투자 결정은 본인 판단과 책임입니다.",
        "advice": None,
        "checklist": None,
    }
