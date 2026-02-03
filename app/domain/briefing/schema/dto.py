from typing import List

from app.domain.common.schema.dto import BaseSchema


class VillageInfo(BaseSchema):
    id: str
    name: str
    icon: str


class PortfolioSummaryDisplay(BaseSchema):
    total_return_rate: str
    total_profit_value: str
    total_assets_value: str


class PortfolioSummary(BaseSchema):
    total_return_rate: float
    total_profit_value: float
    total_assets_value: float
    display: PortfolioSummaryDisplay


class VillageDailyChange(BaseSchema):
    daily_change_rate: float
    display: str


class AssetTotalReturnItem(BaseSchema):
    ticker: str
    name: str
    total_return_rate: float
    display: str


class AssetDailyChangeItem(BaseSchema):
    ticker: str
    name: str
    daily_change_rate: float
    display: str


class AssetTotalReturns(BaseSchema):
    title: str
    items: List[AssetTotalReturnItem]


class AssetDailyChanges(BaseSchema):
    title: str
    items: List[AssetDailyChangeItem]


class LatestNewsItem(BaseSchema):
    news_id: str
    title: str
    summary: str
    published_ago: str
    url: str


class LatestNews(BaseSchema):
    title: str
    items: List[LatestNewsItem]


class AIAdvice(BaseSchema):
    title: str
    bullets: List[str]
