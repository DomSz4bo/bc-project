from typing import Any, Literal, NamedTuple


class CustomStreamData(NamedTuple):
    message: str
    type: Literal["message", "start", "end", "node_name"] = "message"
    extra: dict[str, Any] = dict()
