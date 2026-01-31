from typing import List, Optional

from app.schemas.common.base import BaseSchema


class SelectorVillage(BaseSchema):
    id: str
    name: str
    icon: str
    returnRate: float


class Selector(BaseSchema):
    villages: List[SelectorVillage]


class BriefingAsset(BaseSchema):
    id: str
    name: str
    type: str
    ticker: str
    value: Optional[int] = None


class SelectedVillage(BaseSchema):
    id: str
    name: str
    icon: str
    totalValue: int
    returnRate: float
    allocation: float
    assets: List[BriefingAsset]

