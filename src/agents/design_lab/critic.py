from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.runtime import Runtime
from pydantic import BaseModel, Field

from src.graph.state import AgentState, GraphContext
from src.utils.llm import gemini_flash


class CriticOutput(BaseModel):
    verdict: Literal["PASS", "FAIL"] = Field(
        description=("The verdict, FAIL if the diagram needs fixing else PASS.")
    )
    feedback: str | None = Field(
        default=None,
        description=(
            "If the verdict is FAIL, give concrete instructions on how to fix the problems. "
            "Else omit this field."
        ),
    )


llm_with_structure = gemini_flash.with_structured_output(CriticOutput)


async def critic(state: AgentState, runtime: Runtime[GraphContext]) -> AgentState:
    revision_count = state["revision_count"]
    if revision_count >= runtime.context["max_revisions"]:
        return {
            "critic_verdict": "LIMIT",
            "supervisor_phase": "APPROVAL",
            "critic_feedback": None,
        }

    messages = [
        SystemMessage(SYSTEM_PROMPT),  # TODO
        HumanMessage(
            HUMAN_MSG.format(
                use_case=state["use_case"], sequence_diagram=state["sequence_diagram"]
            )
        ),
    ]
    response: CriticOutput = await llm_with_structure.ainvoke(messages)

    return {
        "critic_verdict": response.verdict,
        "critic_feedback": response.feedback,
        "supervisor_phase": "APPROVAL",
        "revision_count": revision_count
        if response.verdict == "PASS"
        else revision_count + 1,
    }


SYSTEM_PROMPT = """
"""


HUMAN_MSG = """
<use_case>
{use_case}
</use_case>

<mermaid_sequence_diagram>
{sequence_diagram}
</mermaid_sequence_diagram>
"""
