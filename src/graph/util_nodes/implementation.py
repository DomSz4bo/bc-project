from langchain_core.messages import ToolMessage

from src.agents.qa import REJECT_IMPLEMENTATION
from src.agents.supervisor import IMPLEMENT_HANDOFF
from src.graph.state import AgentState


async def prepare_implementation_node(state: AgentState) -> AgentState:
    """
    Acknowledges the implementation handoff tool call.
    """
    last_msg = state["messages"][-1]
    handoff_call = next(
        (tc for tc in last_msg.tool_calls if tc["name"] == IMPLEMENT_HANDOFF), None
    )

    if not handoff_call:
        return {}

    tool_call_id = handoff_call["id"]
    return {
        "messages": [
            ToolMessage(
                content="Implementation phase initiated...",
                tool_call_id=tool_call_id,
                id=f"implementation_handoff_res_{tool_call_id}",
            )
        ],
        "qa_revision_count": 0,
        "qa_feedback": None,
        "qa_messages": None,
    }


async def finish_implementation_node(state: AgentState) -> AgentState:
    """
    Transitions the state to POST_IMPLEMENTATION phase.
    """
    last_msg = state["messages"][-1]
    if not isinstance(last_msg, ToolMessage):
        raise RuntimeError(
            f"Expected ToolMessage as last message, got {type(last_msg)}"
        )

    tool_call_id = last_msg.tool_call_id
    tool_msg_id = f"implementation_handoff_res_{tool_call_id}"
    assert tool_msg_id == last_msg.id

    return {
        "supervisor_phase": "POST_IMPLEMENTATION",
        "messages": [
            ToolMessage(
                content="Implementation phase is complete. All tests have passed.",
                tool_call_id=tool_call_id,
                id=tool_msg_id,
            )
        ],
    }


async def prepare_fix_node(state: AgentState) -> AgentState:
    """
    Extracts feedback from the rejection tool call and
    deletes the QA agent message history.
    """
    last_msg = state["messages"][-1]
    reject_call = next(
        (tc for tc in last_msg.tool_calls if tc["name"] == REJECT_IMPLEMENTATION), None
    )

    if not reject_call:
        raise RuntimeError("No feedback tool call found: QA --!-> Engineer.")

    return {
        "qa_feedback": reject_call["args"]["feedback"],
        "qa_revision_count": state.get("qa_revision_count", 0) + 1,
        "qa_messages": None,
    }
