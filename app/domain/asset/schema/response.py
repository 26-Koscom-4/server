from typing import List

from pydantic import ConfigDict

from app.domain.common.schema.dto import BaseSchema


class AvailableAssetItem(BaseSchema):
    asset_id: int
    ticker: str
    name: str
    category: str


class AvailableAssetsResponse(BaseSchema):
    user_id: int
    available_assets: List[AvailableAssetItem]

    model_config = ConfigDict(extra="forbid")
