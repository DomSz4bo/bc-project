from pathlib import Path
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime
from loguru import logger
from pydantic import BaseModel, Field

from src.graph.state import AgentState, GraphContext
from src.utils.llm import (
    build_fallback_chain,
    gemini_3_flash,
    gemini_3p1_flash_lite,
    gemma_4_31b,
)
from src.utils.source_context import extract_project_context
from src.utils.streaming import CustomStreamData


class FileChange(BaseModel):
    path: str = Field(
        description="Relative path to the file (e.g., tests/test_foo.py, src/foo.py)"
    )
    content: str = Field(description="The complete content of the file")


class TDDPlan(BaseModel):
    thinking: str = Field(
        description="Your thought process and reasoning behind the tests and interfaces that you are going to write."
    )
    files: List[FileChange] = Field(description="List of files to create or update")


llm_with_structure = build_fallback_chain(
    gemini_3_flash,
    gemini_3p1_flash_lite,
    gemma_4_31b,
    schema=TDDPlan,
)


async def tdd_lead(state: AgentState, runtime: Runtime[GraphContext]) -> AgentState:
    """
    The TDD Lead node logic.
    Generates a test suite and updates source code stubs based on the Use Case and Sequence Diagram.
    """
    writer = get_stream_writer()
    writer(CustomStreamData("Writing tests", "start"))
    logger.info("TDD Lead initiated.")

    working_dir = runtime.context.get("working_directory")
    project_context = extract_project_context(state, working_dir)

    messages = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(
            USER_PROMPT.format(
                use_case=project_context.use_case,
                sequence_diagram=project_context.sequence_diagram,
                source_code_context=project_context.source_code_context,
            ),
        ),
    ]

    plan: TDDPlan = await llm_with_structure.ainvoke(messages)
    logger.debug(f"TDD Lead plan: {len(plan.files)} files to write.")

    write_tests_to_disk(plan, working_dir)

    writer(CustomStreamData("Initial tests written.", "end"))
    logger.info("TDD plan written to disk.")

    return {}


def write_tests_to_disk(plan: TDDPlan, working_dir: Path) -> None:
    for file_change in plan.files:
        clean_path = file_change.path.lstrip("/\\")
        full_path = working_dir / clean_path

        logger.info(f"Writing file: {full_path}")
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(file_change.content)


SYSTEM_PROMPT = """
You are the TDD Lead agent in a Python software development pipeline. Your goal is to write a comprehensive Pytest test suite and update the source code with necessary method stubs based strictly on the provided design documents.

<rules>
### 1. Interface Traceability (CRITICAL)
- You MUST derive class interfaces (methods) directly from the messages defined in the Sequence Diagram.
- Do NOT invent public methods that do not correspond to an interaction in the diagram.
- **Stubs**: Update existing source files to include these method signatures (name, arguments, type hints). The body must be `pass` or `return None`.

### 2. Dependency Injection & Interfaces (Protocols)
- Internal components must NOT tightly couple to External Dependencies (Secondary Actors like APIs, Databases).
- You MUST define interfaces for all external dependencies using `typing.Protocol` (e.g., `class BankPort(Protocol): ...`). Define these Protocols in their own separate files.
- Use **Dependency Injection**: The internal classes must accept these Protocol types via their `__init__` constructor type hints.
- In your tests, you MUST restrict your mocks using the `spec` argument (e.g., `mock_bank = MagicMock(spec=BankPort)`).

### 3. Test Generation (TDD)
- Write `tests/conftest.py` for fixtures derived from **Preconditions** and **Actors**.
- Write `tests/test_*.py` files to cover:
    - **Main Success Scenario**: Verify the happy path.
    - **Extensions**: Verify edge cases and failure modes.
    - **Sequence Diagram Interactions**: Verify message passing and logic flow.

### 4. Output Format
- Ensure the code is syntactically correct and importable.
- Return the COMPLETE content for both new test files and updated source files. Do not use diffs or placeholders like `# ... rest of class`.
</rules>
"""

USER_PROMPT = """
Please generate the tests and stubs based on the following context:

**Use Case**:
{use_case}

**Sequence Diagram**:
{sequence_diagram}

**Current Source Code**:
{source_code_context}
"""
