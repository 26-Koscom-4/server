from typing import List, Literal

from app.domain.common.schema.dto import BaseSchema


class MdaInfo(BaseSchema):
    mode: Literal["PRE", "POST"]
    dataOn: bool


class AllocationItem(BaseSchema):
    key: str
    label: str
    marketValue: int
    weight: float


class AllocationGroup(BaseSchema):
    items: List[AllocationItem]


class Allocation(BaseSchema):
    country: AllocationGroup
    assetType: AllocationGroup


class DashboardResponse(BaseSchema):
    userId: int
    mda: MdaInfo
    hasRecommendation: bool
    totalMarketValue: int
    allocation: Allocation
