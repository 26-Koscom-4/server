from pydantic import ConfigDict

from app.domain.common.schema.dto import BaseSchema
from app.domain.user.schema.mydata.dto import CompletionItem, Consent, Institution, Loading, MydataIntegration


class MydataResponse(BaseSchema):
    mockInstitutions: list[Institution]
    consent: Consent
    selectedInstitutions: list[str]
    loadingMessages: list[str]
    loading: Loading
    completionSummary: list[CompletionItem]
    mydata_integration: MydataIntegration

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "mockInstitutions": [
                        {
                            "id": "kb",
                            "name": "KB Securities",
                            "icon": "KB",
                            "description": "3 stock holdings",
                        }
                    ],
                    "consent": {
                        "consent1": True,
                        "consent2": True,
                        "consent3": True,
                        "consentAll": True,
                    },
                    "selectedInstitutions": ["kb"],
                    "loadingMessages": ["Connecting to institutions..."],
                    "loading": {"progress": 40, "message": "Connecting..."},
                    "completionSummary": [
                        {
                            "id": "kb",
                            "name": "KB Securities",
                            "icon": "KB",
                            "status": "completed",
                        }
                    ],
                    "mydata_integration": {
                        "is_integrated": False,
                        "last_integration_date": None,
                        "integrated_institutions": [],
                        "integration_count": 0,
                    },
                }
            ]
        },
    )
