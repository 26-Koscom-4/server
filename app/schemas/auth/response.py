from pydantic import ConfigDict

from app.schemas.common.base import BaseSchema


class AuthUser(BaseSchema):
    name: str


class LoginResponse(BaseSchema):
    accessToken: str
    user: AuthUser

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "accessToken": "mock-token",
                    "user": {"name": "Demo User"},
                }
            ]
        },
    )

