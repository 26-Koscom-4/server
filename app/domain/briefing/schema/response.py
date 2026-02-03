from typing import Literal

from pydantic import ConfigDict

from app.domain.briefing.schema.dto import (
    AIAdvice,
    AssetDailyChanges,
    AssetTotalReturns,
    LatestNews,
    PortfolioSummary,
    VillageDailyChange,
    VillageInfo,
)
from app.domain.common.schema.dto import BaseSchema


class BriefingGenerateResponse(BaseSchema):
    """개미 마을 브리핑 응답."""

    user_id: int
    time_slot: Literal["morning", "evening"]
    village: VillageInfo
    portfolio_summary: PortfolioSummary
    village_daily_change: VillageDailyChange
    asset_total_returns: AssetTotalReturns
    asset_daily_changes: AssetDailyChanges
    latest_news: LatestNews
    ai_advice: AIAdvice

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "user_id": 1,
                    "time_slot": "morning",
                    "village": {"id": "2f6f1c2c-5bdf-4e72-9e0a-0d9f2d1f2e11", "name": "배당마을", "icon": "💰"},
                    "portfolio_summary": {
                        "total_return_rate": 8.3,
                        "total_profit_value": 613112,
                        "total_assets_value": 8000000,
                        "display": {
                            "total_return_rate": "+8.3%",
                            "total_profit_value": "+613,112원",
                            "total_assets_value": "8,000,000원",
                        },
                    },
                    "village_daily_change": {"daily_change_rate": 0.69, "display": "+0.69%"},
                    "asset_total_returns": {
                        "title": "보유 종목별 총 수익률",
                        "items": [
                            {"ticker": "O", "name": "Realty Income", "total_return_rate": 0.71, "display": "+0.71%"},
                        ],
                    },
                    "asset_daily_changes": {
                        "title": "보유 종목별 전일대비 등락",
                        "items": [
                            {"ticker": "O", "name": "Realty Income", "daily_change_rate": 0.79, "display": "+0.79%"},
                        ],
                    },
                    "latest_news": {
                        "title": "마을 최신 뉴스",
                        "items": [
                            {
                                "news_id": "c1b2d3e4-1111-2222-3333-444444444444",
                                "title": "고배당 ETF 자금 유입 증가",
                                "summary": "금리 인하 기대감과 함께 고배당 ETF로의 자금 유입이 크게 증가하고 있습니다.",
                                "published_ago": "1시간 전",
                                "url": "https://finance.yahoo.com/news/dividend-etf-inflow",
                            }
                        ],
                    },
                    "ai_advice": {
                        "title": "오늘의 AI 조언",
                        "bullets": [
                            "배당주는 꾸준한 현금 흐름을 제공합니다. 배당락일을 체크하세요.",
                            "배당락일 3일 전입니다. 배당 수익 예상액을 확인하세요.",
                        ],
                    },
                }
            ]
        },
    )
