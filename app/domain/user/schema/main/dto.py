from typing import Any, Dict, List, Optional

from app.domain.common.schema.dto import BaseSchema


class HeroCta(BaseSchema):
    label: str
    targetPage: str


class Hero(BaseSchema):
    title: str
    subtitle: str
    cta: HeroCta


class Recommendation(BaseSchema):
    hasNewRecommendation: bool
    lastCheckedDate: Optional[str]
    recommendedVillages: List[str]
    bannerVisible: bool


class MapHotspot(BaseSchema):
    id: str
    villageName: str
    badgeId: str
    unreadBadgeVisible: bool
    villageId: str


class MapInfo(BaseSchema):
    title: str
    hotspots: List[MapHotspot]


class ChartDataset(BaseSchema):
    data: List[int]
    backgroundColor: List[str]
    borderWidth: int
    borderColor: str
    hoverOffset: int


class ChartData(BaseSchema):
    labels: List[str]
    datasets: List[ChartDataset]


class AssetChart(BaseSchema):
    type: str
    data: ChartData
    options: Dict[str, Any]


class AssetLegendItem(BaseSchema):
    label: str
    value: int
    percentage: float
    icon: str
    color: str


class AssetLegend(BaseSchema):
    totalAssets: int
    items: List[AssetLegendItem]
