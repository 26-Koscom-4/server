"""Orchestrator: 여러 Agent의 결과를 통합하여 최종 브리핑 생성."""

import logging
from typing import Any, Dict, List, Optional

from app.services.briefing.llm import call_llm

logger = logging.getLogger(__name__)

ORCHESTRATOR_SYSTEM_PROMPT = """# Role: 시니어 퀀트 애널리스트 겸 브리핑 에디터

당신은 주식 분석과 뉴스 분석 결과를 받아 **일관된 톤**과 **명확한 근거**로 브리핑을 통합합니다.
목표는 **정확성**, **논리성**, **데이터 구체성**, **리스크 인지**, **가독성**을 동시에 만족하는 결과입니다.

## 출력 형식
반드시 두 섹션으로 출력:

**[Voice Script]**
TTS가 읽을 음성 스크립트. 한 문장은 10단어 이내로 짧게 끊어서 작성.

**[Visual Summary]**
JSON 형식:
```json
{
  "advice": ["조언 1", "조언 2"],
  "checklist": ["체크리스트 1", "체크리스트 2", "체크리스트 3"],
  "stock_rationales": ["종목별 근거 1", "종목별 근거 2"]
}
```

## 스크립트 구조
1. 인사 + 시장 현황 (주식 분석 활용, 수치 포함)
2. 포트폴리오 성과 (주식 분석 활용, 수치 포함)
3. 주요 뉴스 요약 (뉴스 분석 활용)
4. 리스크 및 체크사항
5. 면책 조항

## 작성 규칙
- 한국어로만 작성
- 문장당 10단어 이내
- 전문 용어는 쉬운 표현으로
- 데이터 부족 시 '데이터 부족' 명시
- 투자 조언처럼 들리지 않게 주의
- 종목 언급 시 **근거를 함께 말하기** (예: "등락률 -2.9%로 하락했습니다")
- Visual Summary의 stock_rationales에 **종목별 근거**를 간결히 정리
- advice는 **뉴스 요약 내용을 최대한 반영** (핵심 헤드라인/리스크 포함)

## Few-shot 예시
입력(요약):
stock_analysis: {"market_summary":"혼조","portfolio_performance":"AAPL +1.2%, TSLA -3.5%","key_movers":["TSLA -3.5%"],"technical_insights":"변동성 확대"}
news_analysis: {"market_sentiment":"혼조","key_headlines":[{"title":"NVDA 실적 상향","summary":"수요 개선"}],"risk_alerts":["리콜 확대"]}

출력:
**[Voice Script]**
좋은 아침입니다.
시장은 혼조입니다.
AAPL은 +1.2%입니다.
TSLA는 -3.5%입니다.
NVDA 실적 상향 소식이 있습니다.
리콜 확대 리스크를 주의하세요.
본 내용은 투자 조언이 아닙니다.

**[Visual Summary]**
```json
{
  "advice": ["변동성 확대에 유의하세요.", "리스크 뉴스를 확인하세요."],
  "checklist": ["주요 뉴스 확인", "포트폴리오 점검", "리스크 모니터링"]
}
```
"""


def _build_orchestrator_prompt(
    stock_analysis: Optional[Dict[str, Any]],
    news_analysis: Optional[Dict[str, Any]],
    villages_data: List[Dict[str, Any]],
    user_name: str,
    time_slot: str,
) -> str:
    """통합 브리핑 생성 프롬프트."""
    import json

    time_desc = "아침" if time_slot == "morning" else "저녁"
    slot_greeting = "좋은 아침입니다" if time_slot == "morning" else "오늘 하루 수고하셨습니다"

    prompt_parts = [
        f"## 브리핑 생성 요청",
        f"",
        f"사용자: {user_name}",
        f"시간대: {time_desc} ({slot_greeting})",
        f"",
    ]

    if stock_analysis:
        prompt_parts.extend([
            "### 주식 시세 분석 결과",
            json.dumps(stock_analysis, ensure_ascii=False, indent=2),
            "",
        ])

    if news_analysis:
        prompt_parts.extend([
            "### 뉴스 분석 결과",
            json.dumps(news_analysis, ensure_ascii=False, indent=2),
            "",
        ])

    if villages_data:
        first_village = villages_data[0] if villages_data else {}
        village_name = first_village.get("name", "마을")
        village_profile = first_village.get("profile")
        prompt_parts.extend([
            f"### 포트폴리오 정보",
            f"주요 마을: {village_name}",
            f"마을 개수: {len(villages_data)}개",
            f"마을 전략/성향: {village_profile}" if village_profile else "마을 전략/성향: 없음",
            "",
        ])

    prompt_parts.append(
        "위 분석 결과들을 바탕으로 [Voice Script]와 [Visual Summary]를 생성해 주세요."
    )

    return "\n".join(prompt_parts)


def orchestrate_briefing(
    stock_analysis: Optional[Dict[str, Any]],
    news_analysis: Optional[Dict[str, Any]],
    villages_data: List[Dict[str, Any]],
    user_name: str = "주인님",
    time_slot: str = "morning",
) -> tuple[str, Dict[str, Any]]:
    """
    여러 Agent의 분석 결과를 통합하여 최종 브리핑 생성.

    Returns:
        (voice_script, visual_summary)
    """
    try:
        prompt = _build_orchestrator_prompt(
            stock_analysis, news_analysis, villages_data, user_name, time_slot
        )
        raw_response = call_llm(ORCHESTRATOR_SYSTEM_PROMPT, prompt)

        if not raw_response:
            logger.warning("Orchestrator returned empty response, using fallback")
            return _fallback_briefing(stock_analysis, news_analysis, user_name, time_slot)

        # Parse response
        from app.services.briefing.parser import parse_briefing_response

        voice_script, visual_summary = parse_briefing_response(raw_response)
        if not voice_script or not isinstance(visual_summary, dict):
            logger.warning("Orchestrator parse result invalid. raw=%s", raw_response)
        logger.info("Orchestration completed successfully")
        return voice_script, visual_summary

    except Exception as e:
        logger.exception("Orchestration failed. raw=%s err=%s", raw_response, e)
        return _fallback_briefing(stock_analysis, news_analysis, user_name, time_slot)


def _fallback_briefing(
    stock_analysis: Optional[Dict[str, Any]],
    news_analysis: Optional[Dict[str, Any]],
    user_name: str,
    time_slot: str,
) -> tuple[str, Dict[str, Any]]:
    """Agent 실패 시 대체 브리핑."""
    slot = "아침" if time_slot == "morning" else "저녁"
    greeting = "좋은 아침입니다" if time_slot == "morning" else "오늘 하루 수고하셨습니다"

    script_parts = [f"{greeting}, {user_name}."]

    if stock_analysis:
        if stock_analysis.get("market_summary"):
            script_parts.append(stock_analysis["market_summary"])
        if stock_analysis.get("portfolio_performance"):
            script_parts.append(stock_analysis["portfolio_performance"])

    if news_analysis:
        if news_analysis.get("market_sentiment"):
            script_parts.append(f"뉴스로 본 시장 분위기는 {news_analysis['market_sentiment']}입니다.")

    script_parts.append("본 내용은 투자 조언이 아니며, 투자 결정은 본인 판단과 책임입니다.")

    voice_script = " ".join(script_parts)

    visual_summary = {
        "advice": ["시장 변동성을 주의 깊게 모니터링하세요.", "포트폴리오 리밸런싱을 고려해 보세요."],
        "checklist": ["시장 뉴스 확인", "포트폴리오 점검", "투자 계획 검토"],
    }

    return voice_script, visual_summary
