from pathlib import Path
from typing import Annotated, Literal, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_intent_summary: str | None
    supervisor_phase: Literal["INTAKE", "APPROVAL"]

    # Design Lab outputs
    use_case: str | None
    sequence_diagram: str | None
    ## Critic validation
    critic_verdict: Literal["PASS", "FAIL", "LIMIT"] | None
    critic_feedback: str | None
    revision_count: int


class GraphContext(TypedDict):
    max_revisions: int
    working_directory: Path
    mmd_syntax_validation_limit: int
