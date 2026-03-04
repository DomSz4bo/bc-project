from operator import add
from typing import Annotated, TypedDict


class AgentState(TypedDict):
    messages: Annotated[list[str], add]

