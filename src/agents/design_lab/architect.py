from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.runtime import Runtime
from loguru import logger

from src.graph.state import AgentState, GraphContext
from src.utils.errors import MermaidValidationLimitExceeded
from src.utils.llm import gemma_3_27b as llm
from src.utils.markdown import extract_block
from src.utils.mermaid import get_mermaid_reference, validate_mermaid


async def architect(state: AgentState, runtime: Runtime[GraphContext]) -> AgentState:
    """
    The Architect node logic.
    Translates a Use Case into a Mermaid.js Sequence Diagram.
    """
    logger.debug("Architect node initiated.")

    use_case = state.get("use_case")
    if not use_case:
        raise ValueError("No use_case found in AgentState.")

    mmd_docs = get_mermaid_reference()
    system_prompt = SYSTEM_PROMPT.format(mmd_docs=mmd_docs)

    messages = [SystemMessage(system_prompt), HumanMessage(use_case)]

    critic_verdict = state.get("critic_verdict")
    if critic_verdict is not None and critic_verdict == "FAIL":
        logger.debug("Architect is in FIX mode based on Critic feedback.")
        critic_feedback = state.get("critic_feedback")
        previous_diagram = state.get("sequence_diagram")
        messages += [
            AIMessage(previous_diagram),
            HumanMessage(critic_feedback),
        ]

    FIX_LIMIT_DEFAULT = 3
    validation_limit = runtime.context.get(
        "mmd_syntax_validation_limit", FIX_LIMIT_DEFAULT
    )

    for i in range(validation_limit):
        response = await llm.ainvoke(messages)
        text_response = response.text
        mmd_code = extract_block(text_response, "mermaid")

        validation_result = await validate_mermaid(mmd_code)
        if validation_result.is_valid:
            break

        logger.debug(f"Architect - invalid syntax for check n.{i+1}")

        messages += [
            AIMessage(text_response),
            HumanMessage(
                DIAGRAM_FIX_PROMPT.format(error=validation_result.error_message)
            ),
        ]

    if validation_result.is_valid:
        logger.debug("Architect completed Sequence Diagram generation.")
        return {"sequence_diagram": text_response}
    else:
        raise MermaidValidationLimitExceeded(
            f"Architect failed to generate a valid Mermaid diagram in {validation_limit} tries."
        )


SYSTEM_PROMPT = """
You are the System Architect in a software design pipeline. Your sole responsibility is to translate a structured Use Case into a Mermaid.js Sequence Diagram.

---

## Your Input
You will receive a Cockburn Use Case. It contains:
- Primary and Secondary Actors.
- A Main Success Scenario (numbered steps).
- Extensions (deviations from the main scenario, e.g., 2a, 3a).

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
