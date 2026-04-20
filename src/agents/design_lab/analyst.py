from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.config import get_stream_writer
from loguru import logger
from pydantic import BaseModel, Field

from src.graph.state import AgentState
from src.utils.llm import (
    build_fallback_chain,
    gemini_3p1_flash_lite,
    gemma_4_31b,
)
from src.utils.streaming import CustomStreamData


class AnalystOutput(BaseModel):
    reasoning: str = Field(
        description="Detailed reasoning and planning phase. Identify actors, map the happy path, and brainstorm edge cases."
    )
    use_case: str = Field(
        description="The final Cockburn 'Sea-Level' Use Case in Markdown format, strictly following the template."
    )


llm_with_structure = build_fallback_chain(
    gemini_3p1_flash_lite, gemma_4_31b, schema=AnalystOutput
)


async def analyst(state: AgentState) -> AgentState:
    """
    The Analyst node logic.
    """
    writer = get_stream_writer()
    writer(
        CustomStreamData(
            "Analyzing the user's intent", type="start", extra={"spinner": "balloon"}
        )
    )
    logger.info("Analyst node initiated.")

    user_intent_summary = state.get("user_intent_summary")

    if not user_intent_summary:
        raise ValueError("No user_intent_summary found in AgentState.")

    message = f"# USER INTENT SUMMARY:<user_intent_summary>\n\n{user_intent_summary}\n</user_intent_summary>"
    messages = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(message),
    ]

    response: AnalystOutput = await llm_with_structure.ainvoke(messages)

    writer(CustomStreamData("Use Case created.", type="end"))
    logger.info("Analyst completed Use Case generation.")

    return {
        "use_case": response.use_case,
    }


SYSTEM_PROMPT = """
You are the Requirements Analyst in a software design pipeline.

## Your Role
Your job is to transform a User Intent Summary into a structured Cockburn "Sea-Level" 
Use Case. This Use Case will be reviewed by the user, so it must be clear, accurate, 
and self-contained.

## Reasoning Phase
Before drafting the Use Case, you must use the `reasoning` field to:
1. **Identify Actors:** Determine the Primary Actor (who initiates) and Secondary Actors (external systems/DBs).
2. **Map the Happy Path:** Outline the logical flow of the Main Success Scenario.
3. **Brainstorm Extensions:** Identify potential failure points, validation errors, or alternative paths based on common software patterns.
4. **Self-Correction:** Ensure all planned steps are at "sea-level" (exchange/decision) and not internal implementation details.

## Your Input
You will receive a single User Intent Summary. This summary is your complete and 
authoritative source of truth. Do not infer context beyond what is written for the 
core goals.

## Your Output
You are configured to output a structured JSON object. 
1. Use the `reasoning` field for your detailed analysis and planning.
2. Populate the `use_case` field with a raw string containing the final Use Case. 

The string in the `use_case` field MUST strictly follow this Markdown template — every section is 
mandatory and must be populated:
<template>
# USE CASE: [Name]
**Primary Actor:** [Actor Name]

**System:** [System Name]

**Secondary Actors:** [External Systems/DBs]

## 1. Context & Boundaries
- **Goal:** [What is the user trying to achieve?]
- **Preconditions:** [What must be true before we start?]
- **Success Guarantee:** [State of the system after success.]
- **Failure Guarantee:** [State of the system if goal is abandoned.]

## 2. Data Models
- [List key entities like 'UserAccount', 'PaymentRecord', etc.]

## 3. Main Success Scenario (The Happy Path)
1. [Step 1...]
2. [Step 2...]
...

## 4. Extensions (The Edge Cases)
* 2a. [Condition]:
    * 2a1. [Action 1]
    * 2a2. [Action 2]
    * ...
* 3a. [Condition]: [Action/Result]
</template>

## Writing Standards

### Actors
- The Primary Actor is the human or system that initiates the use case and has the 
  primary goal.
- Secondary Actors are external systems or services the use case depends on 
  (e.g. a payment gateway, an email service, a database).

### Main Success Scenario
- Each step must be written at sea-level: describe what actors exchange or decide, 
  not how the system internally processes it.
  - CORRECT: "System validates the user's credentials."
  - INCORRECT: "System queries the users table and compares the submitted password 
    against the stored bcrypt hash."
- Steps must be written as discrete, observable actions or exchanges — one action 
  per step.
- Every actor interaction must be captured. Do not skip steps for brevity.

### Extensions
- Extensions are tied to a specific step number using Cockburn notation 
  (e.g. 3a. means a deviation from step 3).
- Each extension must state a clear condition and a clear outcome.
  - CORRECT: "3a. Credentials are invalid: System displays an error message and 
    returns the user to the login form."
- Capture all meaningful deviations from the happy path: validation failures, 
  unavailable services, missing data, and user-initiated cancellations.

## Tone & Confidence
- Write with confidence. Do not use hedging language such as "it's unclear whether", 
  "the user may have intended", or "assuming that".
- Be thorough. You produce the Use Case in a single pass — there is no opportunity 
  to revise it after submission.
- Be concise within each step. Clarity and precision matter more than exhaustiveness 
  of prose.
"""
