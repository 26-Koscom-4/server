from typing import List, Optional

from app.schemas.common.base import BaseSchema


class Institution(BaseSchema):
    id: str
    name: str
    icon: str
    description: str


class Consent(BaseSchema):
    consent1: bool
    consent2: bool
    consent3: bool
    consentAll: bool


class Loading(BaseSchema):
    progress: int
    message: str


class CompletionItem(BaseSchema):
    id: str
    name: str
    icon: str
    status: str


class MydataIntegration(BaseSchema):
    is_integrated: bool
    last_integration_date: Optional[str]
    integrated_institutions: List[str]
    integration_count: int
