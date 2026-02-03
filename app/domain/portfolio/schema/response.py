"""portfolio response schemas."""

from typing import List

from pydantic import ConfigDict

from app.domain.common.schema.dto import BaseSchema


class SummarySection(BaseSchema):
    total_assets_value: float
    total_profit_value: float
    total_profit_rate: float
    total_return_rate: float
    daily_return_rate_point: float
    village_count: int
    owned_asset_count: int


class VillageReturnRate(BaseSchema):
    village_id: int
    return_rate: float


class AssetTypeDistributionItem(BaseSchema):
    key: str
    label: str
    value: float


class RankedReturnItem(BaseSchema):
    rank: int
    symbol: str
    name: str
    return_rate: float
    village_ids: List[int]
    village_names: List[str]


class RebalancingRecommendation(BaseSchema):
    id: str
    title: str
    description: str
    solution: str


class ExportLinks(BaseSchema):
    excel_url: str
    pdf_url: str


class PortfolioSummaryResponse(BaseSchema):
    as_of: str
    summary: SummarySection
    village_return_rates: List[VillageReturnRate]
    asset_type_distribution: List[AssetTypeDistributionItem]
    top5_returns: List[RankedReturnItem]
    bottom5_returns: List[RankedReturnItem]
    rebalancing_recommendations: List[RebalancingRecommendation]
    export: ExportLinks

    model_config = ConfigDict(extra="forbid")
