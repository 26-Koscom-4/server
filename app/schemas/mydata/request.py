from typing import List, Optional

from pydantic import ConfigDict

from app.schemas.common.base import BaseSchema


class MydataCompleteRequest(BaseSchema):
    is_integrated: Optional[bool] = None
    last_integration_date: Optional[str] = None
    integrated_institutions: Optional[List[str]] = None
    integration_count: Optional[int] = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "is_integrated": True,
                    "last_integration_date": "2026-02-01T08:00:00.000Z",
                    "integrated_institutions": ["kb", "mirae"],
                    "integration_count": 2,
                }
            ]
        },
    )
