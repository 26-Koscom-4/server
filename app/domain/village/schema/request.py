from typing import List, Optional

from app.domain.common.schema.dto import BaseSchema


class VillageAssetRef(BaseSchema):
    asset_id: int


class VillageCreateRequest(BaseSchema):
    user_id: int
    name: str
    icon: Optional[str] = None
    type: Optional[str] = None
    goal: Optional[str] = None
    assets: List[VillageAssetRef]
    strategy_items: List[str]
