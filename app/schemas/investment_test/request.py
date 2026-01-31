from typing import Dict, Optional

from pydantic import ConfigDict

from app.schemas.common.base import BaseSchema


class InvestmentTestResultRequest(BaseSchema):
    completed: Optional[bool] = None
    date: Optional[str] = None
    mainType: Optional[str] = None
    percentages: Optional[Dict[str, str]] = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "completed": True,
                    "date": "2026-02-01T08:00:00.000Z",
                    "mainType": "moderate",
                    "percentages": {
                        "conservative": "18.0",
                        "moderateConservative": "22.0",
                        "moderate": "30.0",
                        "moderateAggressive": "20.0",
                        "aggressive": "10.0",
                    },
                }
            ]
        },
    )
