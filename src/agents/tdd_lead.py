from pathlib import Path
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.runtime import Runtime
from loguru import logger
from pydantic import BaseModel, Field

from src.graph.state import AgentState, GraphContext
from src.utils.llm import build_fallback_chain, gemini_3_flash, gemini_3p1_flash_lite
from src.utils.source_context import extract_project_context


class FileChange(BaseModel):
    path: str = Field(
        description="Relative path to the file (e.g., tests/test_foo.py, src/foo.py)"
    )
    content: str = Field(description="The complete content of the file")


class TDDPlan(BaseModel):
    thinking: str = Field(
        description="Your thought process and reasoning behind the tests that you are going to write."
    )
    files: List[FileChange] = Field(description="List of files to create or update")


llm_with_structure = build_fallback_chain(
    gemini_3_flash.with_structured_output(TDDPlan),
    gemini_3p1_flash_lite.with_structured_output(TDDPlan),
)


async def tdd_lead(state: AgentState, runtime: Runtime[GraphContext]) -> AgentState:
    """
    The TDD Lead node logic.
    Generates a test suite and updates source code stubs based on the Use Case and Sequence Diagram.
    """
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
You are the TDD Lead agent in a software development pipeline. Your goal is to write a comprehensive Pytest test suite and update the source code with necessary method stubs.

---

## INPUTS
You will be provided with:
1. **Use Case**: The business requirements defining the "what".
2. **Sequence Diagram**: The architectural logic defining the "how" (interactions).
3. **Current Source Code**: The existing project structure (mostly empty class shells).

---

## RESPONSIBILITIES

### 1. Test Generation (TDD)
- Write `tests/conftest.py` for fixtures derived from **Preconditions** and **Actors**.
- Write `tests/test_*.py` files to cover:
    - **Main Success Scenario**: Verify the happy path.
    - **Extensions**: Verify edge cases and failure modes.
    - **Sequence Diagram Interactions**: Verify message passing and logic flow.
- Use `unittest.mock` or `pytest-mock` for external dependencies (Secondary Actors).

### 2. Interface Definition (Stubs)
- The current source code likely contains empty classes (e.g., `class PaymentProcessor: pass`).
- You MUST update these source files to include **method stubs** for every method called in your tests.
- **Rules for Stubs**:
    - Add the method signature (name, arguments, type hints if possible).
    - Body should be `pass` or `return None` (do NOT implement business logic yet).
    - Ensure the code is syntactically correct and importable.
    - Do not remove existing classes, just expand them.

---

## OUTPUT FORMAT
Return a list of `FileChange` objects.
- `path`: The relative path to the file (e.g., `tests/test_core.py`, `src/core.py`).
- `content`: The COMPLETE content of the file.

**CRITICAL**: You must return the FULL content for both new test files and updated source files. Do not use diffs or placeholders.
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
