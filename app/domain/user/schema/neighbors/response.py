from pydantic import ConfigDict

from app.domain.common.schema.dto import BaseSchema
from app.domain.user.schema.neighbors.dto import Recommendation


class NeighborsResponse(BaseSchema):
    recommendations: list[Recommendation]

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "recommendations": [
                        {
                            "id": "commodities",
                            "villageId": "village-commodities",
                            "name": "Commodities Village",
                            "subtitle": "Gold, Silver, Oil",
                            "reason": "Diversify away from tech.",
                            "assets": [
                                {"id": "GLD", "ticker": "GLD", "label": "Gold ETF"}
                            ],
                            "correlation": -0.23,
                            "correlationNote": "Low correlation",
                            "addVillageName": "Commodities Village",
                            "addVillageId": "village-commodities",
                        }
                    ]
                }
            ]
        },
    )
