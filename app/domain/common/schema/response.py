from pydantic import ConfigDict

from app.domain.common.schema.dto import BaseSchema


class OkResponse(BaseSchema):
    ok: bool

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"ok": True}]},
    )
