from typing import Dict, List, Optional

from app.schemas.common.base import BaseSchema
from app.schemas.mydata.models import IntegratedInstitution


class UserProfile(BaseSchema):
    name: str
    theme: str


class Settings(BaseSchema):
    briefing_time: str
    voice_speed: float


class Statistics(BaseSchema):
    totalAssets: int
    villageCount: int
    avgReturn: float
    assetCount: int


class ActivityItem(BaseSchema):
    id: str
    title: str
    time: str


class Activity(BaseSchema):
    items: List[ActivityItem]


class MydataIntegration(BaseSchema):
    is_integrated: bool
    last_integration_date: Optional[str]
    integrated_institutions: List[IntegratedInstitution]
    integration_count: int


class InvestmentTestSummary(BaseSchema):
    completed: bool
    date: Optional[str]
    mainType: str
    percentages: Dict[str, str]
