from typing import Dict

from pydantic import ConfigDict

from app.schemas.briefing.models import SelectedVillage, Selector
from app.schemas.common.base import BaseSchema


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
