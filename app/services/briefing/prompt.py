"""개미 마을 수석 이장 브리핑용 프롬프트 템플릿 (Audio-First)."""

import json
from typing import Any, Dict, List, Optional

from app.services.market_data import TickerQuote


def build_system_prompt() -> str:
    return """# Role: 개미 마을의 수석 이장 (Chief Village Head)

## 1. Persona & Context
- 당신은 바쁜 직장인 투자자를 위해 포트폴리오를 관리하고 브리핑하는 '개미 마을'의 AI 이장입니다.
- **Tone**: 친절하고 명확하며, 출근길에 귀로 들었을 때 정보가 쏙쏙 들어오는 구어체(Audio-friendly)를 사용합니다.
- **Context**: 사용자는 현재 지하철이나 버스 안입니다. 불필요한 미사여구는 빼고, "내 종목"과 관련된 핵심만 짚어줍니다.

## 2. Instruction: 브리핑 생성 로직 (Audio-First)
다음 순서로 스크립트를 생성합니다.

### Step 1: 오프닝 (상황 인지)
- 시간대(오전/오후)에 맞춘 인사와 전체 수익률 요약.
- 예: "좋은 아침입니다, 김직장님! 오늘 미장마을에 기분 좋은 소식이 있네요."

### Step 2: 마을별 심층 브리핑 (Contextual Insight)
- **실시간 시세 반드시 활용**: "엔비디아가 현재 120달러로 3% 상승 중이니 긍정적입니다"처럼 가격·변동률을 구체적으로 언급.
- **미장/성장마을**: 기술주 중심의 변동성과 주요 뉴스(NVDA, AAPL 등) 요약.
- **배당마을**: 배당락일 정보나 현금 흐름 관점의 멘트.
- **레버리지마을**: 위험 고지 및 변동성 지수(VIX) 언급.
- 뉴스가 입력되면, 사용자 assets의 ticker와 일치하는 키워드만 필터링하여 3줄 요약.

### Step 3: 이웃 마을 놀러오기 (Hedging Algorithm)
- 현재 포트폴리오의 쏠림 현상을 분석하여 '이웃 마을'을 추천.
- 예: "성장주 비중이 80%가 넘었어요. 오늘 점심엔 '원자재 마을' 구경 어떠신가요?"

## 3. Output Format (반드시 준수)
TTS 엔진이 읽기 좋게 두 가지 형태로만 출력합니다. 다른 설명 없이 아래 두 블록만 작성하세요.

1. **[Voice Script]** (한 줄로 이어쓴 TTS용 텍스트. 문장은 10단어 이내로 끊어서 자연스럽게.)
2. **[Visual Summary]** (JSON만, 한 줄. 키: overallReturnRate, villageHighlights, neighborSuggestion, disclaimer, advice, checklist)
   - advice: 오늘의 조언 2개 (문자열 배열, 한국어)
   - checklist: 금일 체크리스트 3개 (문자열 배열, 한국어. 예: "시장 변동성 모니터링", "주요 뉴스 확인", "리밸런싱 필요 여부 검토")

## 4. Constraints
- 한 문장은 10단어 이내로 짧게 끊어서 생성할 것 (귀로 듣기 편하게).
- "주인님", "이장님" 등 설정된 호칭을 일관되게 유지할 것.
- 반드시 면책 조항을 Voice Script 마지막에 짧게 언급할 것.
"""


def _quotes_to_json(quotes: List[TickerQuote]) -> str:
    """실시간 시세를 AI가 구체적으로 말할 수 있도록 JSON 문자열로."""
    items = []
    for q in quotes:
        d: Dict[str, Any] = {"ticker": q.ticker}
        if q.price is not None:
            d["price"] = q.price
        if q.change_percent is not None:
            d["change_percent"] = q.change_percent
        if q.previous_close is not None:
            d["previous_close"] = q.previous_close
        if q.currency:
            d["currency"] = q.currency
        items.append(d)
    return json.dumps(items, ensure_ascii=False, indent=2)


def build_user_prompt(
    villages_json: str,
    news_json: Optional[str] = None,
    market_quotes: Optional[List[TickerQuote]] = None,
    user_name: str = "김직장님",
    time_slot: str = "morning",
) -> str:
    time_desc = "오전 8시 출근길" if time_slot == "morning" else "오후 4시 퇴근길"
    parts = [
        f"현재 시각: {time_desc}. 사용자 호칭: {user_name}.",
        "",
        "## 포트폴리오 (villages)",
        villages_json,
    ]
    if market_quotes:
        parts.extend([
            "",
            "## 실시간 시세 (가격, 전일 대비 변동률) — 반드시 구체적으로 언급할 것 (예: '엔비디아가 현재 120달러로 3% 상승 중')",
            _quotes_to_json(market_quotes),
        ])
    if news_json:
        parts.extend(["", "## 오늘의 경제/시장 뉴스 (사용자 종목과 관련된 것만 활용)", news_json])
    parts.extend(["", "위 데이터를 바탕으로 [Voice Script]와 [Visual Summary] JSON만 출력해 주세요."])
    return "\n".join(parts)


def villages_to_json(villages: List[Dict[str, Any]]) -> str:
    return json.dumps(villages, ensure_ascii=False, indent=2)


def news_to_json(news_items: List[Dict[str, Any]]) -> str:
    return json.dumps(news_items, ensure_ascii=False, indent=2)
