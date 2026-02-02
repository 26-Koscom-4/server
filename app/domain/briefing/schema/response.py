from typing import Any, Dict, List

from pydantic import ConfigDict

from app.domain.briefing.schema.dto import BriefingCard, SelectedVillage, Selector
from app.domain.common.schema.dto import BaseSchema


class LatestBriefingResponse(BaseSchema):
    """GET /briefing 응답: 가장 최근에 생성된 브리핑 (한국어)."""

    summary: str
    generated_at: str
    news_count: int
    tickers: List[str]

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "summary": "오늘의 투자 포인트: 엔비디아 실적 기대감으로 반도체 섹터 상승. ...",
                    "generated_at": "2025-01-15T09:00:00",
                    "news_count": 12,
                    "tickers": ["AAPL", "NVDA"],
                }
            ]
        },
    )


class BriefingGenerateResponse(BaseSchema):
    """TTS용 스크립트 + 개미 아침 브리핑 카드 UI 구조."""

    voice_script: str  # TTS 엔진이 읽을 순수 텍스트 (음성으로 듣기)
    briefing_card: BriefingCard  # 화면 카드: 헤더, 마을 현황, 자산 분석, 전략, 조언, 체크리스트

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "voice_script": "주인님, 좋은 아침입니다! 미장마을의 현재 상황을 알려드립니다.",
                    "briefing_card": {
                        "header": {"title": "개미 아침 브리핑", "subtitle": "마을별 대표 개미를 선택하고 브리핑을 들어보세요"},
                        "village": {"id": "village-us", "name": "미장마을", "icon": "🇺🇸", "briefing_title": "미장마을 브리핑"},
                        "status": {
                            "intro_sentence": "주인님, 좋은 아침입니다! 미장마을의 현재 상황을 알려드립니다.",
                            "total_assets": 15000000,
                            "return_rate": 12.5,
                            "portfolio_weight": 32.3,
                        },
                        "asset_analysis": [
                            {"ticker": "AAPL", "type": "기술주", "status": "안정적으로 운영 중입니다."},
                        ],
                        "strategy": {"investment_type": "성장형", "investment_goal": "장기 투자"},
                        "advice": ["성장주는 장기적인 관점에서 접근하세요. 단기 변동성에 흔들리지 마세요.", "✓ 기술주 중심 포트폴리오입니다. 실적 발표 시즌을 주목하세요."],
                        "checklist": ["✓ 시장 변동성 모니터링", "✓ 주요 뉴스 확인", "✓ 리밸런싱 필요 여부 검토"],
                    },
                }
            ]
        },
    )


# 기존 fixture 기반 GET /briefing 응답 (유지)
class BriefingResponse(BaseSchema):
    selector: Selector
    typeTextMap: Dict[str, str]
    goalTextMap: Dict[str, str]
    adviceMap: Dict[str, str]
    marketAdviceMap: Dict[str, str]
    selectedVillage: SelectedVillage

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "selector": {
                        "villages": [
                            {
                                "id": "village-us",
                                "name": "US Village",
                                "icon": "US",
                                "returnRate": 12.5,
                            }
                        ]
                    },
                    "typeTextMap": {"growth": "Growth"},
                    "goalTextMap": {"long-term": "Long-term"},
                    "adviceMap": {"growth": "Stay the course."},
                    "marketAdviceMap": {"growth": "Tech momentum is strong."},
                    "selectedVillage": {
                        "id": "village-us",
                        "name": "US Village",
                        "icon": "US",
                        "totalValue": 15000000,
                        "returnRate": 12.5,
                        "allocation": 32.3,
                        "assets": [
                            {
                                "id": "AAPL",
                                "name": "AAPL",
                                "type": "Tech",
                                "ticker": "AAPL",
                            }
                        ],
                    },
                }
            ]
        },
    )
