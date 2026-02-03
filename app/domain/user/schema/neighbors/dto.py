from typing import List

from app.domain.common.schema.dto import BaseSchema


class RecommendationAsset(BaseSchema):
    id: str
    ticker: str
    label: str


class Recommendation(BaseSchema):
    id: str
    villageId: str
    name: str
    subtitle: str
    reason: str
    assets: List[RecommendationAsset]
    correlation: float
    correlationNote: str
    addVillageName: str
    addVillageId: str
