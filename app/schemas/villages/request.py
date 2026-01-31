from typing import Optional

from pydantic import ConfigDict

from app.schemas.common.base import BaseSchema


class CreateVillageRequest(BaseSchema):
    villageId: Optional[str] = None
    name: Optional[str] = None
    icon: Optional[str] = None
    type: Optional[str] = None
    goal: Optional[str] = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"villageId": "village-commodities"},
                {"name": "Commodities Village", "icon": "C", "type": "commodities"},
            ]
        },
    )
