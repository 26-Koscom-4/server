from typing import List, Optional

from pydantic import ConfigDict

from app.schemas.common.base import BaseSchema
from app.schemas.mydata.models import IntegratedInstitution


class MydataCompleteRequest(BaseSchema):
    is_integrated: Optional[bool] = None
    last_integration_date: Optional[str] = None
    integrated_institutions: Optional[List[IntegratedInstitution]] = None
    integration_count: Optional[int] = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "is_integrated": True,
                    "last_integration_date": "2026-02-01T08:00:00.000Z",
                    "integrated_institutions": [
                        {"id": "kb", "name": "KB증권", "icon": "🏦"},
                        {"id": "mirae", "name": "미래에셋증권", "icon": "🏢"},
                    ],
                    "integration_count": 2,
                }
            ]
        },
    )
