from pydantic import ConfigDict

from app.schemas.common.base import BaseSchema


class OkResponse(BaseSchema):
    ok: bool

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"ok": True}]},
    )
