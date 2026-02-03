from typing import Any, Dict, List, Optional

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


class VillageCreateResponse(BaseSchema):
    village_id: int


class CustomVillageItem(BaseSchema):
    id: int
    name: str
    icon: Optional[str] = None
    total_assets: float
    return_rate: float
    portfolio_weight: float
    asset_tickers: List[str]


class CustomVillagesResponse(BaseSchema):
    user_id: int
    filter: str
    villages: List[CustomVillageItem]


class VillageMetricsDisplay(BaseSchema):
    total_assets: str
    return_rate: str
    portfolio_weight: str


class VillageMetrics(BaseSchema):
    total_assets: float
    return_rate: float
    portfolio_weight: float
    display: VillageMetricsDisplay


class VillageAssetItem(BaseSchema):
    asset_id: int
    ticker: str
    name: str


class VillageAssetsSection(BaseSchema):
    count: int
    items: List[VillageAssetItem]


class InvestmentProfile(BaseSchema):
    investment_type: str
    investment_goal: str


class VillageSummary(BaseSchema):
    id: int
    name: str
    icon: Optional[str] = None
    metrics: VillageMetrics
    assets: VillageAssetsSection
    investment_profile: InvestmentProfile


class ActionItem(BaseSchema):
    label: str
    action: str
    target: Optional[str] = None


class VillageSummaryResponse(BaseSchema):
    user_id: int
    village: VillageSummary
    actions: Dict[str, ActionItem]


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
