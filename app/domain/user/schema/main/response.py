from pydantic import ConfigDict

from app.domain.common.schema.dto import BaseSchema
from app.domain.user.schema.main.dto import AssetChart, AssetLegend, Hero, MapInfo, Recommendation


class MainResponse(BaseSchema):
    hero: Hero
    recommendation: Recommendation
    map: MapInfo
    assetChart: AssetChart
    assetLegend: AssetLegend

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "hero": {
                        "title": "Ant Village",
                        "subtitle": "Wake up your portfolio.",
                        "cta": {"label": "Start", "targetPage": "villages"},
                    },
                    "recommendation": {
                        "hasNewRecommendation": True,
                        "lastCheckedDate": None,
                        "recommendedVillages": ["Commodities Village"],
                        "bannerVisible": True,
                    },
                    "map": {
                        "title": "My Investment Map",
                        "hotspots": [
                            {
                                "id": "hotspot-korea",
                                "villageName": "Korea Village",
                                "badgeId": "badge-korea",
                                "unreadBadgeVisible": True,
                                "villageId": "village-korea",
                            }
                        ],
                    },
                    "assetChart": {
                        "type": "doughnut",
                        "data": {
                            "labels": ["Tech", "Dividend"],
                            "datasets": [
                                {
                                    "data": [11500000, 8000000],
                                    "backgroundColor": [
                                        "rgba(78, 205, 196, 0.8)",
                                        "rgba(255, 107, 53, 0.8)",
                                    ],
                                    "borderWidth": 3,
                                    "borderColor": "#fff",
                                    "hoverOffset": 15,
                                }
                            ],
                        },
                        "options": {"responsive": True, "cutout": "60%"},
                    },
                    "assetLegend": {
                        "totalAssets": 46500000,
                        "items": [
                            {
                                "label": "Tech",
                                "value": 11500000,
                                "percentage": 24.7,
                                "icon": "T",
                                "color": "rgba(78, 205, 196, 0.8)",
                            }
                        ],
                    },
                }
            ]
        },
    )
