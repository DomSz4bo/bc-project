from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.runtime import Runtime
from loguru import logger

from src.graph.state import AgentState, GraphContext
from src.utils.llm import gemini_3_flash as llm
from src.utils.mcp_clients import get_filesystem_client
from src.utils.source_context import read_source_files
from src.utils.tools import run_tests_with_coverage


async def quality_assurance(
    state: AgentState, runtime: Runtime[GraphContext]
) -> AgentState:
    """
    The QA node logic.
    Checks code coverage and writes additional unit tests.
    """
    logger.debug("QA node initiated.")

    use_case = state.get("use_case")
    sequence_diagram = state.get("sequence_diagram")
    working_dir = runtime.context.get("working_directory")

    if not use_case or not sequence_diagram:
        raise ValueError("Missing use_case or sequence_diagram in AgentState.")
    if not working_dir:
        raise ValueError("Missing working_directory in GraphContext.")

    source_code_context = read_source_files(working_dir)

    input_message = HumanMessage(
        USER_PROMPT.format(
            use_case=use_case,
            sequence_diagram=sequence_diagram,
            source_code_context=source_code_context,
        ),
    )

    filesystem_client = get_filesystem_client(working_dir)

    async with filesystem_client.session("filesystem") as session:
        file_tools = await load_mcp_tools(session)
        all_tools = file_tools + [run_tests_with_coverage]

        qa = create_agent(
            llm,
            tools=all_tools,
            system_prompt=SYSTEM_PROMPT,
            context_schema=GraphContext,
        )
        await qa.ainvoke({"messages": [input_message]})

    return {}


SYSTEM_PROMPT = """
You are the Quality Assurance agent in a software development pipeline.
Your goal is to evaluate Pytest test suite and update the source code with necessary method stubs.

---

## INPUTS
You will be provided with:
1. **Use Case**: The business requirements defining the "what".
2. **Sequence Diagram**: The architectural logic defining the "how" (interactions).
3. **Current Source Code**: The current implementation.

---

## RESPONSIBILITIES

### 1. Test Generation (TDD)
- Write `tests/conftest.py` for fixtures derived from **Preconditions** and **Actors**.
- Write `tests/test_*.py` files to cover:
    - **Main Success Scenario**: Verify the happy path.
    - **Extensions**: Verify edge cases and failure modes.
    - **Sequence Diagram Interactions**: Verify message passing and logic flow.
- Use `unittest.mock` or `pytest-mock` for external dependencies (Secondary Actors).

"""

USER_PROMPT = """
Here is the project context:

**Use Case**:
{use_case}

**Sequence Diagram**:
{sequence_diagram}

**Current Source Code**:
{source_code_context}
"""
