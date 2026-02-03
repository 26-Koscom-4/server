"""News Analysis Agent: 뉴스 데이터 분석."""

import json
import logging
from typing import Any, Dict, List, Optional

from app.services.briefing.llm import call_llm

logger = logging.getLogger(__name__)

NEWS_SYSTEM_PROMPT = """# Role: 거시/종목 뉴스 분석가

당신은 금융/경제 뉴스를 분석하여 핵심 정보를 추출하는 전문가입니다.
목표는 정확성, 논리성, 데이터 구체성, 리스크 인지, 가독성입니다.

## 매우 중요한 원칙
- 추측 금지: 제공된 뉴스(title/summary) 내용에 근거하지 않으면 '데이터 부족'이라고 명시하세요.
- 과장 금지: 객관적 서술만 사용하세요.
- 투자 조언 금지: 매수/매도/추천/전망 단정 금지.
- 근거 필수: 모든 요약/리스크는 반드시 어떤 뉴스에 근거했는지 index로 표시하세요.

## 분석 항목
1. 시장 심리: 뉴스 전반 분위기(긍정/부정/중립). 근거 키워드를 1~2개 수준으로 summary에 녹여 설명하세요.
2. 주요 헤드라인: 중요도 높은 뉴스 최대 3개. 각 항목에 news_index 포함.
3. 종목별 뉴스: 입력된 보유 종목(tickers/asset_names)에 대해 관련 뉴스가 있으면 요약하고, 근거 news_indices 포함.
4. 리스크 알림: 부정적 신호/주의사항을 최대 3개. 각 항목에 근거 news_indices 포함.

## 출력 형식 (JSON만)
반드시 아래 JSON 스키마로만 출력하세요. 다른 텍스트 금지.

```json
{
  "market_sentiment": "시장 심리 요약 (긍정/부정/중립 또는 데이터 부족)",
  "key_headlines": [
    {"title": "뉴스 제목", "summary": "핵심 요약 (1-2문장)", "news_index": 0}
  ],
  "ticker_specific": {
    "TICKER": {"summary": "해당 종목 관련 요약(1-2문장)", "news_indices": [0, 2]}
  },
  "risk_alerts": [
    {"text": "주의사항(1문장)", "news_indices": [1]}
  ]
}
```
"""

NEWS_RELEVANCE_SYSTEM_PROMPT = """# Role: 뉴스 관련성 판별 전문가

당신은 뉴스가 특정 자산과 관련이 있는지 판단하는 전문가입니다.

## 작업
- 입력된 뉴스 목록 중, 자산명과 실질적으로 관련된 기사만 골라주세요.
- 단순 키워드 일치가 아니라, 문맥상 관련성이 있는지 판단하세요.

## 출력 형식
반드시 JSON만 출력하세요:
```json
{
  "relevant_indices": [0, 2, 5]
}
```

## 제약 사항
- 한국어로만 작성
- 결과가 없으면 빈 배열 반환
"""


def filter_relevant_news_with_llm(
    news_items: List[Dict[str, Any]],
    asset_names: List[str],
    max_items: int = 15,
) -> List[Dict[str, Any]]:
    """LLM으로 자산 관련 뉴스만 필터링."""
    if not news_items or not asset_names:
        return []

    candidates = news_items[:max_items]
    asset_str = ", ".join(asset_names)
    news_json = json.dumps(
        [
            {
                "index": idx,
                "title": item.get("title"),
                "summary": item.get("summary"),
                "source": item.get("source"),
                "link": item.get("link"),
            }
            for idx, item in enumerate(candidates)
        ],
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""## 판단 요청

자산명: {asset_str}

### 뉴스 목록
{news_json}

위 뉴스 중 자산명과 실질적으로 관련된 기사 인덱스를 JSON으로 반환해 주세요."""

    raw_response = call_llm(NEWS_RELEVANCE_SYSTEM_PROMPT, prompt)
    if not raw_response:
        return []

    try:
        import re

        json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_response, re.DOTALL)
        json_str = json_match.group(1) if json_match else raw_response.strip()
        result = json.loads(json_str)
        indices = result.get("relevant_indices") or []
        filtered: List[Dict[str, Any]] = []
        for i in indices:
            if isinstance(i, int) and 0 <= i < len(candidates):
                filtered.append(candidates[i])
        return filtered
    except Exception:
        logger.exception("Failed to parse relevance filter response")
        return []


def _build_news_prompt(
    news_items: List[Dict[str, Any]],
    tickers: List[str],
    user_name: str,
    time_slot: str,
) -> str:
    """뉴스 분석 Agent용 프롬프트 생성."""
    time_desc = "오전 8시 출근길" if time_slot == "morning" else "오후 4시 퇴근길"

    news_json = json.dumps(news_items, ensure_ascii=False, indent=2)
    tickers_str = ", ".join(tickers)

    return f"""## 분석 요청

현재 시각: {time_desc}
사용자: {user_name}
보유 종목: {tickers_str}

### 뉴스 데이터
{news_json}

위 뉴스들을 분석하여 결과를 JSON 형식으로 출력해 주세요.
특히 보유 종목({tickers_str}) 관련 뉴스는 상세히 분석해 주세요."""


def analyze_news_data(
    news_items: List[Dict[str, Any]],
    tickers: List[str],
    user_name: str = "주인님",
    time_slot: str = "morning",
) -> Optional[Dict[str, Any]]:
    """
    뉴스 데이터를 분석하여 인사이트 생성.

    Returns:
        {
            "market_sentiment": str,
            "key_headlines": List[Dict],
            "ticker_specific": Dict[str, str],
            "risk_alerts": List[str]
        }
    """
    if not news_items:
        logger.warning("No news items provided for news analysis")
        return None

    try:
        prompt = _build_news_prompt(news_items, tickers, user_name, time_slot)
        raw_response = call_llm(NEWS_SYSTEM_PROMPT, prompt)

        if not raw_response:
            logger.warning("News agent returned empty response")
            return None

        # JSON 파싱
        import re
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = raw_response.strip()

        result = json.loads(json_str)
        logger.info("News analysis completed successfully")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse news analysis JSON: {e}")
        logger.debug(f"Raw response: {raw_response}")
        return None
    except Exception as e:
        logger.exception(f"News analysis failed: {e}")
        return None
