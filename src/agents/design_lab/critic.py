from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.runtime import Runtime
from pydantic import BaseModel, Field
from loguru import logger

from src.graph.state import AgentState, GraphContext
from src.utils.llm import gemini_2p5_flash as llm


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


llm_with_structure = llm.with_structured_output(CriticOutput)


async def critic(state: AgentState, runtime: Runtime[GraphContext]) -> AgentState:
    logger.debug("Critic node initiated.")

    revision_count = state["revision_count"]
    if revision_count >= runtime.context["max_diagram_revisions"]:
        logger.debug("Critic node - revision limit hit.")
        return {
            "critic_verdict": "LIMIT",
            "critic_feedback": None,
        }

    messages = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(
            HUMAN_MSG.format(
                use_case=state["use_case"], sequence_diagram=state["sequence_diagram"]
            )
        ),
    ]
    response: CriticOutput = await llm_with_structure.ainvoke(messages)
    logger.debug("Critic finished evalauting artifacts.")
    return {
        "critic_verdict": response.verdict,
        "critic_feedback": response.feedback,
        "revision_count": revision_count
        if response.verdict == "PASS"
        else revision_count + 1,
    }


SYSTEM_PROMPT = """You are the Design Critic. Your role is to audit a Mermaid Sequence Diagram against a Cockburn Use Case.

### Core Mandate
The Use Case is the GROUND TRUTH. Your job is to identify semantic inconsistencies, logical gaps, and missing requirements in the Sequence Diagram. Do not critique the Use Case.

### Audit Checklist
1. **Actor Alignment**: Ensure all Primary/Secondary actors from the Use Case are present as participants. Verify no essential internal systems are missing.
2. **MSS Fidelity**: Every numbered step in the Main Success Scenario must be represented by chronological message arrows. Identify any "logical holes" where the system jumps between states without a transition.
3. **Extension Coverage**: Every Extension in the Use Case has a corresponding conditional or flow-control block (alt, opt, break, loop) in the diagram, and the chosen block type is appropriate for the nature of that extension.
4. **Semantic Precision**: Message labels must be descriptive and technically accurate. Arrow directions must reflect the correct request/response flow.
5. **Architectural Clarity**: Suggest improvements for readability or technical depth where the current modeling is ambiguous or over-simplified.

### Output Requirements
- Provide a `PASS` verdict only if the diagram is a complete and faithful representation.
- On `FAIL`, provide surgical, numbered feedback referencing specific Use Case steps or extensions.
- Syntax is pre-validated; focus exclusively on semantic alignment and logical completeness."""


HUMAN_MSG = """Please audit the following Sequence Diagram against the provided Use Case.

[GROUND TRUTH USE CASE]
{use_case}

[CANDIDATE MERMAID DIAGRAM]
{sequence_diagram}
"""
