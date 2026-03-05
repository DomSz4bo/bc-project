from typing import Annotated, Literal, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    next_step: Literal["DESIGN", "IMPLEMENT", "USER"] | None
    refined_intent: str | None

    # Design Lab outputs
    use_case: str | None
    sequence_diagram: str | None
    ## Critic validation
    critic_status: Literal["PASS", "FAIL"] | None
    critic_feedback: str | None
    iteration_count: int = 0

    # Implementation Lab outputs
    test_suite: str | None
    final_code: str | None


class GraphContext(TypedDict):
    max_iters: int
