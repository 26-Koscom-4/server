from app.models.base import Base
from app.models.user import User, UserSettings
from app.models.village import Village, VillageMetricsDaily, VillageAsset
from app.models.asset import Asset
from app.models.briefing import Briefing, BriefingNewsLink, TimeSlot, TargetScope
from app.models.news import NewsItem, NewsItemAsset
from app.models.neighbor import (
    NeighborRecommendation,
    NeighborRecommendationItem,
    NeighborItemAsset,
)
from app.models.risk import RiskProfile

__all__ = [
    "Base",
    "User",
    "UserSettings",
    "Village",
    "VillageMetricsDaily",
    "VillageAsset",
    "Asset",
    "Briefing",
    "BriefingNewsLink",
    "TimeSlot",
    "TargetScope",
    "NewsItem",
    "NewsItemAsset",
    "NeighborRecommendation",
    "NeighborRecommendationItem",
    "NeighborItemAsset",
    "RiskProfile",
]
