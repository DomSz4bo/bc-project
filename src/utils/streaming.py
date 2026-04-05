from typing import Any, Literal, NamedTuple


class CustomStreamData(NamedTuple):
    message: str
    type: Literal["message", "start", "end"] = "message"
    extra: dict[str, Any] = dict()
