from langchain_core.messages import ToolMessage
from langgraph.config import get_stream_writer
from loguru import logger

from src.agents.supervisor import DESIGN_HANDOFF
from src.graph.state import AgentState
from src.utils.llm import gemma_3_27b
from src.utils.streaming import CustomStreamData


async def prepare_design_node(state: AgentState) -> AgentState:
    """
    Extracts the user intent summary and optional instructions from the
    handoff tool call to prepare the state for the Design Lab.
    Adds an initial ToolMessage that will be overwritten later.
    """
    last_msg = state["messages"][-1]
    handoff_call = next(
        (tc for tc in last_msg.tool_calls if tc["name"] == DESIGN_HANDOFF), None
    )
    if not handoff_call:
        raise RuntimeError("Expected last message to contain design handoff tool call.")

    writer = get_stream_writer()
    writer(CustomStreamData("Handed off to design team.", "message"))

    tool_call_id = handoff_call["id"]
    return {
        "user_intent_summary": handoff_call["args"]["user_intent_summary"],
        "design_notes": handoff_call["args"].get("instructions"),
        "messages": [
            ToolMessage(
                content="Design Lab initiated. The team is now processing the requirements.",
                tool_call_id=tool_call_id,
                id=f"design_handoff_res_{tool_call_id}",
            )
        ],
        "sequence_diagram": None,
        "critic_verdict": None,
        "critic_feedback": None,
        "revision_count": 0,
    }


async def finish_design_node(state: AgentState) -> AgentState:
    """
    Summarizes the results of the Design Lab using gemma_3_27b and
    overwrites the initial ToolMessage with the final technical briefing.
    """
    use_case = state.get("use_case", "")
    diagram = state.get("sequence_diagram", "")

    last_msg = state["messages"][-1]
    if not isinstance(last_msg, ToolMessage):
        raise RuntimeError(
            f"Expected ToolMessage as last message, got {type(last_msg)}"
        )

    tool_call_id = last_msg.tool_call_id
    tool_msg_id = f"design_handoff_res_{tool_call_id}"
    assert tool_msg_id == last_msg.id

    prompt = f"""You are the Lead Architect in a 'Visual-First' engineering pipeline. You have finalized a design consisting of a Cockburn Use Case (Intent) and a Mermaid Sequence Diagram (Logic).

Deliver a dense, high-signal technical briefing for Axiom, the Principal Systems Engineer. Axiom is allergic to ambiguity; your summary must verify the architectural integrity of this 'Dual-Truth' contract.

CONTENT REQUIREMENTS:
1. Core Workflow: Define the primary state transition and actor boundaries.
2. Edge Cases: Identify 2-3 specific error boundaries or conditional flows (Extensions) handled.

STYLE RULES:
- NO preamble, NO greetings ("Hello Axiom"), NO conversational filler.
- Use precise engineering terminology (e.g., idempotency, post-conditions, asynchronous callbacks).
- Limit: ~60 words of high-density technical prose.

[USE CASE]
{use_case}

[SEQUENCE DIAGRAM]
{diagram}
"""
    try:
        response = await gemma_3_27b.ainvoke(prompt)
        summary = response.text
    except Exception as error:
        logger.warning("Failed to summarize design output.")
        logger.debug(f"Error ({type(error).__name__}) w/ message: {str(error)}")
        summary = "The design team successfully produced a Use case and Mermaid Sequence diagram."

    return {
        "messages": [
            ToolMessage(
                content=summary,
                tool_call_id=tool_call_id,
                id=tool_msg_id,
            )
        ],
        "supervisor_phase": "APPROVAL",
    }
