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


class VillageSummary(BaseSchema):
    id: int
    name: str
    icon: Optional[str] = None
    metrics: VillageMetrics
    assets: VillageAssetsSection
    ai_one_liner: Optional[str] = None


class ActionItem(BaseSchema):
    label: str
    action: str
    target: Optional[str] = None


class VillageSummaryResponse(BaseSchema):
    user_id: int
    village: VillageSummary


class SummaryCardsDisplay(BaseSchema):
    total_assets: str
    current_return_rate: str
    holding_count: str


class SummaryCards(BaseSchema):
    total_assets: float
    current_return_rate: float
    holding_count: int
    display: SummaryCardsDisplay


class MonthlyReturnItem(BaseSchema):
    month: int
    return_rate: float


class MonthlyReturnTrend(BaseSchema):
    title: str
    unit: str
    items: List[MonthlyReturnItem]


class VillageOverviewDisplay(BaseSchema):
    total_assets: str
    return_rate: str
    portfolio_weight: str


class VillageOverview(BaseSchema):
    title: str
    total_assets: float
    return_rate: float
    portfolio_weight: float
    display: VillageOverviewDisplay


class HoldingDisplay(BaseSchema):
    value: str
    daily_change_rate: str


class HoldingItem(BaseSchema):
    asset_id: int
    ticker: str
    name: str
    category: str
    value: float
    daily_change_rate: float
    display: HoldingDisplay


class HoldingsSection(BaseSchema):
    title: str
    items: List[HoldingItem]


class VillageDetailHeader(BaseSchema):
    id: int
    name: str
    icon: Optional[str] = None


class VillageDetailResponse(BaseSchema):
    user_id: int
    village: VillageDetailHeader
    summary_cards: SummaryCards
    monthly_return_trend: MonthlyReturnTrend
    village_overview: VillageOverview
    holdings: HoldingsSection
    ai_one_liner: Optional[str] = None


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
