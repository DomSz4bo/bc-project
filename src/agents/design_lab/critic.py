from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime
from loguru import logger
from pydantic import BaseModel, Field

from src.graph.state import AgentState, GraphContext
from src.utils.llm import (
    build_fallback_chain,
    gemini_2p5_flash,
    gemini_3p1_flash_lite,
    gemma_4_31b,
)
from src.utils.streaming import CustomStreamData


class CriticOutput(BaseModel):
    analysis: str = Field(
        description="Step-by-step analysis of the sequence diagram against the Use Case. Go through the Audit Checklist sequentially."
    )
    verdict: Literal["PASS", "FAIL"] = Field(
        description="The final verdict. FAIL if the diagram misses requirements or has logical errors. PASS if it is a complete, faithful representation."
    )
    feedback: str = Field(
        description="If FAIL, provide a numbered list of concrete, surgical instructions for the Architect to fix the diagram. If PASS, provide a brief approval summary.",
    )


llm_with_structure = build_fallback_chain(
    gemini_2p5_flash, gemini_3p1_flash_lite, gemma_4_31b, schema=CriticOutput
)


DEFAULT_REVISION_LIMIT = 3


async def critic(state: AgentState, runtime: Runtime[GraphContext]) -> AgentState:
    writer = get_stream_writer()
    writer(
        CustomStreamData(
            "Checking design artifact consistency", "start", {"spinner": "triangle"}
        )
    )
    logger.info("Critic node initiated.")

    revision_count = state["revision_count"]
    revision_limit = runtime.context.get(
        "max_diagram_revisions", DEFAULT_REVISION_LIMIT
    )

    if revision_count >= revision_limit:
        writer(
            CustomStreamData(
                "Consistency revision limit hit.", "end", {"style": "italic red"}
            )
        )
        logger.info("Critic node - revision limit hit.")
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

    logger.info(f"Critic finished evalauting artifacts. Verdict: {response.verdict}")
    logger.debug(f"Critic response: {response}")

    if response.verdict == "PASS":
        msg = "Design artifacts passed consistency check."
    else:
        msg = "Design artifacts failed consistency check."
    writer(CustomStreamData(msg, "end"))



    return {
        "critic_verdict": response.verdict,
        "critic_feedback": response.feedback,
        "revision_count": revision_count
        if response.verdict == "PASS"
        else revision_count + 1,
    }


SYSTEM_PROMPT = """You are the Design Critic. Your role is to rigorously audit a Mermaid Sequence Diagram against a Cockburn Use Case.

### Core Mandate
The Use Case is the GROUND TRUTH. Your job is to identify semantic inconsistencies, logical gaps, and missing requirements in the Sequence Diagram. Do NOT critique or alter the Use Case.

### Audit Checklist
You must analyze the following points step-by-step:
1. **Actor Alignment**: Are all Primary/Secondary actors and internal systems from the Use Case present as participants? Are there any unmentioned actors?
2. **MSS Fidelity (Main Success Scenario)**: Is every numbered step in the MSS represented by chronological message arrows? Are there any missing state transitions or unexplained logical jumps?
3. **Extension Coverage**: Does every Extension (alternative flow) have a corresponding conditional block (e.g., `alt`, `opt`, `break`, `loop`)? Are the conditions accurately labeled based on the Use Case?
4. **Semantic Precision**: Do the message labels accurately reflect the actions described? Do arrow directions (Request `->>` vs Response `-->>`) correctly reflect the flow of data/control?
5. **Diagram Mechanics**: Are lifelines activated/deactivated properly if applicable? Are block structures nested correctly?

### Output Requirements
- Use the `analysis` field to document your step-by-step evaluation against the checklist.
- Render a `FAIL` verdict if ANY requirement from the Use Case is missing, misrepresented, or logically flawed.
- If `FAIL`, the `feedback` field MUST contain a precise, numbered list of required fixes referencing specific Use Case steps or extensions. 
- Render a `PASS` verdict ONLY if the diagram is a complete, faithful, and technically sound representation of the Use Case."""


HUMAN_MSG = """Please audit the following Sequence Diagram against the provided Use Case.

<use_case>
{use_case}
</use_case>

<sequence_diagram>
{sequence_diagram}
</sequence_diagram>
"""
