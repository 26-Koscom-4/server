from typing import List

from app.schemas.common.base import BaseSchema


class DailyAsset(BaseSchema):
    id: str
    name: str
    type: str
    value: int
    ticker: str


class DailyVillage(BaseSchema):
    id: str
    name: str
    icon: str
    type: str
    goal: str
    totalValue: int
    returnRate: float
    allocation: float
    assets: List[DailyAsset]
    lastBriefingRead: str


class BriefingItem(BaseSchema):
    label: str
    value: str


class BriefingSection(BaseSchema):
    title: str
    items: List[BriefingItem]
