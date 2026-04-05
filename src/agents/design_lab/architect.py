from typing import Literal

from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime
from langgraph.types import Command, StreamWriter
from loguru import logger

from src.graph.node_names import Nodes
from src.graph.state import AgentState, GraphContext
from src.utils.llm import build_fallback_chain, gemini_3_flash, gemini_3p1_flash_lite
from src.utils.markdown import extract_block
from src.utils.mermaid import get_mermaid_reference, validate_mermaid
from src.utils.streaming import CustomStreamData

llm = build_fallback_chain(gemini_3_flash, gemini_3p1_flash_lite)


async def architect(
    state: AgentState, runtime: Runtime[GraphContext]
) -> Command[Literal[Nodes.SUPERVISOR, Nodes.CRITIC]]:
    """
    The Architect node logic.
    Translates a Use Case into a Mermaid.js Sequence Diagram.
    """
    writer = get_stream_writer()
    logger.info("Architect node initiated.")

    messages = _build_messages(state)

    FIX_LIMIT_DEFAULT = 3
    validation_limit = runtime.context.get(
        "mmd_syntax_validation_limit", FIX_LIMIT_DEFAULT
    )

    diagram, is_valid = await _run_validation_cycle(messages, validation_limit, writer)

    if is_valid:
        logger.info("Architect completed Sequence Diagram generation.")
        writer(CustomStreamData("Sequence diagram successfully created.", "end"))
        return Command(
            goto=Nodes.CRITIC,
            update={"sequence_diagram": diagram},
        )

    logger.info(
        f"Architect failed to generate valid diagram within validation limit: {validation_limit}."
    )
    writer(CustomStreamData("Failed to create a valid sequence diagram.", "end"))

    last_msg = state["messages"][-1]
    updated_message = _update_failure_tool_message(last_msg)

    return Command(
        goto=Nodes.SUPERVISOR,
        update={
            "messages": [updated_message],
        },
    )


def _update_failure_tool_message(tool_message: ToolMessage):
    if not isinstance(tool_message, ToolMessage):
        raise RuntimeError(
            f"Expected last message to be ToolMessage, got {type(tool_message)}"
        )

    tool_call_id = tool_message.tool_call_id
    tool_msg_id = f"design_handoff_res_{tool_call_id}"
    assert tool_msg_id == tool_message.id

    return ToolMessage(
        content="Design team failed. Exceeded mermaid syntax validation limit. Inform user and try later.",
        tool_call_id=tool_call_id,
        id=tool_msg_id,
    )


def _build_messages(state: AgentState) -> list[AnyMessage]:
    use_case = state.get("use_case")
    design_notes = state.get("design_notes")

    if not use_case:
        raise ValueError("No use_case found in AgentState.")

    mmd_docs = get_mermaid_reference()
    system_prompt = SYSTEM_PROMPT.format(mmd_docs=mmd_docs)

    message = f"# Use case\n<use_case>\n{use_case}\n</use_case>\n"
    if design_notes:
        message += f"\n## Additional instructions\n{design_notes}"

    messages = [SystemMessage(system_prompt), HumanMessage(message)]

    critic_verdict = state.get("critic_verdict")
    if critic_verdict is not None and critic_verdict == "FAIL":
        logger.info("Architect is in FIX mode based on Critic feedback.")
        critic_feedback = state.get("critic_feedback")
        previous_diagram = state.get("sequence_diagram")
        messages += [
            AIMessage(previous_diagram),
            HumanMessage(critic_feedback),
        ]

    return messages


async def _run_validation_cycle(
    messages: list[AnyMessage], validation_limit: int, writer: StreamWriter
):
    for generation_n in range(validation_limit):
        response = await _generate_diagram(messages, generation_n, writer)
        text_response = response.text
        mmd_code = extract_block(text_response, "mermaid")

        writer(CustomStreamData("Checking diagram syntax validity", "start"))
        validation_result = await validate_mermaid(mmd_code)
        if validation_result.is_valid:
            break

        logger.info(f"Architect - invalid syntax for check n.{generation_n + 1}")

        messages += [
            AIMessage(text_response),
            HumanMessage(
                DIAGRAM_FIX_PROMPT.format(error=validation_result.error_message)
            ),
        ]

    return text_response, validation_result.is_valid


async def _generate_diagram(
    messages: list[AnyMessage], try_number: int, writer: StreamWriter
) -> AIMessage:
    if try_number > 0:
        writer(
            CustomStreamData(
                "Fixing Mermaid syntax",
                type="start",
                extra={"spinner": "monkey"},
            )
        )
    else:
        writer(
            CustomStreamData(
                "Drafting Mermaid sequence diagram",
                type="start",
                extra={"spinner": "arrow"},
            )
        )

    response = await llm.ainvoke(messages)
    return response


SYSTEM_PROMPT = """
You are the System Architect in a software design pipeline. Your sole responsibility is to translate a structured Use Case into a Mermaid.js Sequence Diagram.

---

## Your Input
You will receive a Cockburn Use Case. It contains:
- Primary and Secondary Actors.
- A Main Success Scenario (numbered steps).
- Extensions (deviations from the main scenario, e.g., 2a, 3a).

You may also receive additional instructions (e.g. diagramming guidance, required elements, etc.).
Ignore instructions that are irrelevant to your task.

---

## OUTPUT

Return only the raw Mermaid code block. No preamble, no explanation, no commentary before or after.

Example of the required format:
```mermaid
sequenceDiagram
  ...
```

---

## DIAGRAMMING RULES

### Participants
- Participant names must match the Use Case Actors verbatim where possible.
- Minor abbreviations are acceptable only when verbatim names would severely hurt readability.
- Do not invent participant names that have no counterpart in the Use Case.

### Arrow Conventions
- `->>` solid arrowhead: synchronous call.
- `-->>` dashed line: reply message.
- `--)` open arrowhead: asynchronous message.

### Feature Usage
- All Mermaid Sequence Diagram features are available (`alt`, `opt`, `loop`, `par`, `note`, etc.).
- Use whichever features most faithfully represent the Use Case logic.
- Do not use features decoratively — every construct must be justified by the Use Case.
- Use activation bars to show that objects are active using `activate` and `deactivate`. You can also use the shortcut notation by appending `+` or `-` suffix to a message arrow.

### Faithfulness vs. Comprehensibility
When these two goals conflict, faithfulness wins. An accurate diagram that is slightly harder to read is preferable to a clean diagram that misrepresents the Use Case.

Here is a summarized reference of the Mermaid Sequence diagram documentation:
<docs>
{mmd_docs}
</docs>
"""

DIAGRAM_FIX_PROMPT = """
❌ MERMAID VALIDATION FAILED:
{error}

**REQUIRED ACTIONS:**
1. **ANALYZE the error message** above from Mermaid's parser
2. **GENERATE CORRECTED Mermaid code** that fixes the identified problem

**COMMON FIXES for Mermaid errors:**
- Check for missing arrows
- Verify node syntax and quotes
- Ensure proper diagram type declaration
- Fix special character escaping
- Check for proper indentation
- Validate connection syntax
"""
