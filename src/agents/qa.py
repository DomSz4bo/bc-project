from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.config import get_stream_writer
from langgraph.prebuilt import ToolNode
from langgraph.runtime import Runtime
from langgraph.types import Command
from loguru import logger
from pydantic import BaseModel, Field

from src.graph.node_names import Nodes
from src.graph.state import AgentState, GraphContext
from src.utils.llm import (
    build_fallback_chain,
    gemini_3p1_flash_lite,
    gemma_4_31b,
)
from src.utils.middleware import (
    LoggingMiddleware,
    ToolStreamingMiddleware,
    format_tool_error,
)
from src.utils.source_context import extract_project_context
from src.utils.streaming import CustomStreamData
from src.utils.tools import file_tools, run_tests_with_coverage

REJECT_IMPLEMENTATION = "reject_implementation"


class ImplementationFeedback(BaseModel):
    feedback: str = Field(
        description=("Detailed feedback about what tests are failingaand other issues ")
    )


@tool(REJECT_IMPLEMENTATION, args_schema=ImplementationFeedback)
async def reject_implementation(feedback: str) -> str:
    """
    Signals that the current implementation is inadequate and must be fixed by the Engineer.
    Call this when unit tests fail or there are significant code quality issues.
    Provide detailed feedback on what needs fixing.
    """
    return "Handoff to Engineer failed - called with other tools."


routing_tools = [reject_implementation]
action_tools = [run_tests_with_coverage]
all_tools = file_tools + routing_tools + action_tools

DEFAULT_REVISION_LIMIT = 3

logging_mw = LoggingMiddleware()
streaming_mw = ToolStreamingMiddleware()
llm_with_tools = build_fallback_chain(
    gemini_3p1_flash_lite,
    gemma_4_31b,
    tools=all_tools,
)


async def quality_assurance(
    state: AgentState, runtime: Runtime[GraphContext]
) -> Command[Literal[Nodes.FINISH_IMPLEMENTATION, Nodes.QA_TOOLS, Nodes.PREPARE_FIX]]:
    """
    The QA node logic.
    Identifies issues in the implementation and either rejects it (via tool) or finishes.
    """
    writer = get_stream_writer()
    writer(CustomStreamData("Evaluating the implementation", "start"))
    logger.info("QA node initiated.")

    revision_count = state["qa_revision_count"]
    revision_limit = runtime.context.get("max_code_revisions", DEFAULT_REVISION_LIMIT)

    if revision_count >= revision_limit:
        writer(
            CustomStreamData(
                "QA revision limit reached", "end", {"style": "italic red"}
            )
        )
        logger.info("QA node - revision limit hit.")
        return Command(
            update={"qa_feedback": "LIMIT"}, goto=Nodes.FINISH_IMPLEMENTATION
        )

    if state["qa_messages"]:
        messages = state["qa_messages"]
    else:
        working_dir = runtime.context.get("working_directory")
        project_context = extract_project_context(state, working_dir)
        messages = [
            SystemMessage(SYSTEM_PROMPT),
            HumanMessage(
                USER_PROMPT.format(
                    use_case=project_context.use_case,
                    sequence_diagram=project_context.sequence_diagram,
                    source_code_context=project_context.source_code_context,
                    tests_context=project_context.test_files_context,
                ),
            ),
        ]

    response = await llm_with_tools.ainvoke(messages)

    logger.info("QA agent has replied.")
    logger.debug(f"QA response: {response.pretty_repr()}")

    update = {"qa_messages": messages + [response]}

    if not response.tool_calls:
        writer(
            CustomStreamData("Implementation approved.", "end", {"style": "bold green"})
        )
        return Command(
            update=update,
            goto=Nodes.FINISH_IMPLEMENTATION,
        )

    tool_names = [tc["name"] for tc in response.tool_calls]

    if any(name != REJECT_IMPLEMENTATION for name in tool_names):
        return Command(
            update=update,
            goto=Nodes.QA_TOOLS,
        )

    writer(
        CustomStreamData(
            "Requested implementation changes.", "end", {"style": "italic orange1"}
        )
    )
    return Command(
        update=update,
        goto=Nodes.PREPARE_FIX,
    )


async def qa_tool_node(state: AgentState) -> AgentState:
    """
    Wraps a ToolNode to achieve custom state update behaviour.
    Executes the QA's tool calls.
    """
    logger.info("QA tool node initiated.")
    qa_messages = state.get("qa_messages")
    if not qa_messages:
        raise ValueError("There are no qa_messages")

    tool_node = ToolNode(
        all_tools,
        wrap_tool_call=lambda req, h: logging_mw.wrap_tool_call(
            req, lambda r: streaming_mw.wrap_tool_call(r, h)
        ),
        awrap_tool_call=lambda req, h: logging_mw.awrap_tool_call(
            req, lambda r: streaming_mw.awrap_tool_call(r, h)
        ),
        handle_tool_errors=format_tool_error,
    )
    response: list[ToolMessage] = await tool_node.ainvoke(qa_messages)

    if not isinstance(response[0], ToolMessage):
        raise ValueError("Unexpected value in QA agent")

    return {"qa_messages": qa_messages + response}


SYSTEM_PROMPT = """
You are the **Quality Assurance** agent. Your job is to verify that the implementation is complete, correct, and fully tested.

---

## YOUR MANDATE
1. **Audit for correctness**: Does the source code accurately implement the requirements from the Use Case and Sequence Diagram?
2. **Audit for test coverage**: Are all branches of the logic, including extensions and error states, covered by unit tests?
3. **Verify via execution**: Use the `run_tests_with_coverage` tool to get definitive proof.

---

## TOOL USAGE
- **Writing Tests**: You have access to filesystem tools. Use them to create or update files in the `tests/` directory to ensure full coverage.
- **Verification**: Always run `run_tests_with_coverage` after making changes or to verify the Engineer's work.
- **Rejection**: If tests fail or coverage is low and you cannot fix it yourself, call `reject_implementation(feedback)`.

---

## WHEN TO REJECT
If you find failing tests or clear logical deviations that require implementation changes, use the `reject_implementation` tool.
- **Provide detailed feedback**: Be surgical. Reference specific lines or missing coverage metrics.

---

## WHEN TO FINISH
If all tests pass, coverage is high (e.g., >85%), and the implementation is faithful to the design, simply finish your turn with a brief summary. **Do NOT call `reject_implementation` if everything is correct.**
"""

USER_PROMPT = """
Here is the project context for your audit:

**Use Case**:
<use_case>
{use_case}
</use_case>

**Sequence Diagram**:
<sequence_diagram>
{sequence_diagram}
</sequence_diagram>

**Current Source Code**:
<source_code>
{source_code_context}
</source_code>

**Current tests**:
<tests>
{tests_context}
</tests>
"""
