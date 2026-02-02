from pydantic import ConfigDict

from app.domain.common.schema.dto import BaseSchema
from app.domain.user.schema.mypage.dto import (
    Activity,
    InvestmentTestSummary,
    MydataIntegration,
    Settings,
    Statistics,
    UserProfile,
)


class MypageResponse(BaseSchema):
    user_profile: UserProfile
    settings: Settings
    statistics: Statistics
    activity: Activity
    mydata_integration: MydataIntegration
    investment_test: InvestmentTestSummary

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "user_profile": {"name": "Demo User", "theme": "light"},
                    "settings": {"briefing_time": "08:00", "voice_speed": 1.0},
                    "statistics": {
                        "totalAssets": 46500000,
                        "villageCount": 6,
                        "avgReturn": 7.8,
                        "assetCount": 19,
                    },
                    "activity": {
                        "items": [
                            {
                                "id": "welcome",
                                "title": "Welcome",
                                "time": "just now",
                            }
                        ]
                    },
                    "mydata_integration": {
                        "is_integrated": False,
                        "last_integration_date": None,
                        "integrated_institutions": [],
                        "integration_count": 0,
                    },
                    "investment_test": {
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
                    },
                }
            ]
        },
    )
