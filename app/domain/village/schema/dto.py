from typing import List, Optional

from app.domain.common.schema.dto import BaseSchema


class VillageAsset(BaseSchema):
    id: str
    name: str
    type: str
    ticker: str
    value: Optional[int] = None


class Village(BaseSchema):
    id: str
    name: str
    icon: str
    assets: List[VillageAsset]
    type: Optional[str] = None
    goal: Optional[str] = None
    totalValue: Optional[int] = None
    returnRate: Optional[float] = None
    allocation: Optional[float] = None
    lastBriefingRead: Optional[str] = None
