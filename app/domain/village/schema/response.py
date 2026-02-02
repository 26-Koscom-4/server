from typing import Any, Dict, List

from pydantic import ConfigDict

from app.domain.common.schema.dto import BaseSchema
from app.domain.village.schema.dto import Village


class VillagesResponse(BaseSchema):
    villages: List[Village]

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "villages": [
                        {
                            "id": "village-us",
                            "name": "US Village",
                            "icon": "US",
                            "assets": [
                                {
                                    "id": "AAPL",
                                    "name": "AAPL",
                                    "type": "Tech",
                                    "value": 4000000,
                                    "ticker": "AAPL",
                                }
                            ],
                            "type": "growth",
                            "goal": "long-term",
                            "totalValue": 15000000,
                            "returnRate": 12.5,
                            "allocation": 32.3,
                            "lastBriefingRead": None,
                        }
                    ]
                }
            ]
        },
    )


class VillageModalResponse(BaseSchema):
    village: Village
    typeTextMap: Dict[str, str]
    goalTextMap: Dict[str, str]

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "village": {
                        "id": "village-us",
                        "name": "US Village",
                        "icon": "US",
                        "assets": [
                            {
                                "id": "AAPL",
                                "name": "AAPL",
                                "type": "Tech",
                                "ticker": "AAPL",
                            }
                        ],
                        "totalValue": 15000000,
                        "returnRate": 12.5,
                        "allocation": 32.3,
                        "type": "growth",
                        "goal": "long-term",
                    },
                    "typeTextMap": {"growth": "Growth"},
                    "goalTextMap": {"long-term": "Long-term"},
                }
            ]
        },
    )


class CreateVillageResponse(BaseSchema):
    status: str
    payload: Dict[str, Any]

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "status": "created",
                    "payload": {"villageId": "village-commodities"},
                }
            ]
        },
    )
