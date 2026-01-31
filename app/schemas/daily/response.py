from pydantic import ConfigDict

from app.schemas.common.base import BaseSchema
from app.schemas.daily.models import BriefingSection, DailyVillage


class DailyResponse(BaseSchema):
    selectedVillage: DailyVillage
    briefingSections: list[BriefingSection]
    fallbackStaticContentHtml: str

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "selectedVillage": {
                        "id": "village-dividend",
                        "name": "Dividend Village",
                        "icon": "D",
                        "type": "dividend",
                        "goal": "passive-income",
                        "totalValue": 8000000,
                        "returnRate": 8.3,
                        "allocation": 17.2,
                        "assets": [
                            {
                                "id": "SCHD",
                                "name": "SCHD",
                                "type": "Dividend ETF",
                                "value": 3000000,
                                "ticker": "SCHD",
                            }
                        ],
                        "lastBriefingRead": "2026-02-01",
                    },
                    "briefingSections": [
                        {
                            "title": "Summary",
                            "items": [
                                {"label": "Total Assets", "value": "8,000,000"},
                                {"label": "Return", "value": "+8.3%"},
                            ],
                        }
                    ],
                    "fallbackStaticContentHtml": "<div>Daily briefing</div>",
                }
            ]
        },
    )
