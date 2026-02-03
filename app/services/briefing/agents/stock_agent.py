"""Stock Analysis Agent: 주식 시세 데이터 분석."""

import json
import logging
from typing import Any, Dict, List, Optional

from app.services.briefing.llm import call_llm
from app.services.market_data import TickerQuote

logger = logging.getLogger(__name__)

STOCK_SYSTEM_PROMPT = """# Role: 시니어 퀀트 애널리스트 (Portfolio Market Briefing Engine)

당신은 포트폴리오 시세 데이터와 뉴스 데이터를 결합해,
"정량적 근거 기반 브리핑"을 생성하는 시니어 퀀트 애널리스트입니다.

목표는 단순 요약이 아니라,
수치 기반으로 시장 흐름과 포트폴리오 변동 요인을 연결하는 것입니다.

---

## 입력 데이터
- 종목별 가격 및 등락률
- 포트폴리오 구성 비중(있을 경우)
- 관련 뉴스 제목/요약(있을 경우)

---

## 핵심 원칙 (매우 중요)

1. **추측 금지**
   - 제공된 데이터 외의 원인 해석 금지
   - 뉴스가 없으면 "데이터 부족" 명시

2. **투자 조언 금지**
   - 매수/매도/추천 표현 금지

3. **정량성 강화**
   - 반드시 수치(등락률, 변동폭)를 포함해 설명

4. **리스크 인지**
   - 변동성이 크거나 손실 종목이 있으면 반드시 언급

5. **가독성**
   - 문장은 간결하게 (2~3문장 단위)

---

## Step-by-Step 분석 프로세스 (Chain-of-Thought 적용)

### Step 1. 시장 현황 요약
- 전체 종목 중 상승/하락 비중 계산
- 평균 등락률로 시장 분위기 판단

### Step 2. 포트폴리오 성과 요약
- 전체 평균 수익률
- 손익 기여도가 큰 종목 강조

### Step 3. 주요 변동 종목 추출
- 가장 큰 상승/하락 종목 1~2개
- 뉴스가 연결되면 "데이터 기반"으로만 언급

### Step 4. 기술적 인사이트 (정량 기반)
- 변동성 확대 여부 (등락폭 기준)
- 단기 추세: 상승 종목 우세 vs 하락 종목 우세

---

## 출력 형식 (JSON만 출력)

반드시 아래 JSON 구조를 그대로 유지하세요.

```json
{
  "market_summary": "시장 전반 요약 (2-3문장, 상승/하락 비중 및 평균 등락률 포함)",
  "portfolio_performance": "포트폴리오 성과 요약 (2-3문장, 평균 수익률 및 손실 기여 종목 포함)",
  "key_movers": [
    "가장 큰 상승 종목: 수치 기반 설명",
    "가장 큰 하락 종목: 수치 기반 설명"
  ],
  "technical_insights": "변동성·추세 관점 요약 (2-3문장, 등락폭 기반)"
}
```
"""


def _build_stock_prompt(
    ticker_quotes: List[TickerQuote],
    villages_data: List[Dict[str, Any]],
    user_name: str,
    time_slot: str,
) -> str:
    """주식 분석 Agent용 프롬프트 생성."""
    time_desc = "오전 8시 출근길" if time_slot == "morning" else "오후 4시 퇴근길"

    quotes_json = json.dumps(
        [
            {
                "ticker": q.ticker,
                "price": q.price,
                "change_percent": q.change_percent,
                "previous_close": q.previous_close,
                "currency": q.currency,
            }
            for q in ticker_quotes
        ],
        ensure_ascii=False,
        indent=2,
    )

    villages_json = json.dumps(villages_data, ensure_ascii=False, indent=2)

    return f"""## 분석 요청

현재 시각: {time_desc}
사용자: {user_name}

### 실시간 시세 데이터
{quotes_json}

### 포트폴리오 정보 (마을 프로필 포함)
{villages_json}

위 데이터를 바탕으로 시세 분석 결과를 JSON 형식으로 출력해 주세요."""


def analyze_stock_data(
    ticker_quotes: List[TickerQuote],
    villages_data: List[Dict[str, Any]],
    user_name: str = "주인님",
    time_slot: str = "morning",
) -> Optional[Dict[str, Any]]:
    """
    주식 시세 데이터를 분석하여 인사이트 생성.

    Returns:
        {
            "market_summary": str,
            "portfolio_performance": str,
            "key_movers": List[str],
            "technical_insights": str
        }
    """
    if not ticker_quotes:
        logger.warning("No ticker quotes provided for stock analysis")
        return None

    try:
        prompt = _build_stock_prompt(ticker_quotes, villages_data, user_name, time_slot)
        raw_response = call_llm(STOCK_SYSTEM_PROMPT, prompt)

        if not raw_response:
            logger.warning("Stock agent returned empty response")
            return None

        # JSON 파싱
        # LLM이 ```json ... ``` 형식으로 반환할 수 있으므로 처리
        import re
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 전체가 JSON인 경우
            json_str = raw_response.strip()

        result = json.loads(json_str)
        logger.info("Stock analysis completed successfully")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse stock analysis JSON: {e}")
        logger.debug(f"Raw response: {raw_response}")
        return None
    except Exception as e:
        logger.exception(f"Stock analysis failed: {e}")
        return None
