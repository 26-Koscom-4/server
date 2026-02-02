from pydantic import ConfigDict

from app.domain.common.schema.dto import BaseSchema


class ErrorDetail(BaseSchema):
    code: str
    message: str


class ErrorResponse(BaseSchema):
    error: ErrorDetail

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "error": {
                        "code": "FIXTURE_NOT_FOUND",
                        "message": "Fixture not found: ui_state_main.json",
                    }
                }
            ]
        },
    )
