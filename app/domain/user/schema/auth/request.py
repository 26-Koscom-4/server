from pydantic import ConfigDict

from app.domain.common.schema.dto import BaseSchema


class LoginRequest(BaseSchema):
    username: str
    password: str

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "username": "demo-user",
                    "password": "demo-pass",
                }
            ]
        },
    )
