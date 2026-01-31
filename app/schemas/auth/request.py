from pydantic import ConfigDict

from app.schemas.common.base import BaseSchema


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
