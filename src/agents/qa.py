from pathlib import Path
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.runtime import Runtime
from loguru import logger
from pydantic import BaseModel, Field

from src.graph.state import AgentState, GraphContext
from src.utils.llm import gemini_3_flash as llm


class FileChange(BaseModel):
    path: str = Field(
        description="Relative path to the file (e.g., tests/test_foo.py, src/foo.py)"
    )
    content: str = Field(description="The complete content of the file")


class QAPlan(BaseModel):
    files: List[FileChange] = Field(description="List of files to create or update")


structured_llm = llm.with_structured_output(QAPlan)


async def quality_assurance(
    state: AgentState, runtime: Runtime[GraphContext]
) -> AgentState:
    """
    The QA Agent node logic.
    Generates a test suite and updates source code stubs based on the Use Case and Sequence Diagram.
    """
    logger.debug("QA Agent node initiated.")

    use_case = state.get("use_case", None)
    sequence_diagram = state.get("sequence_diagram", None)
    working_dir = runtime.context.get("working_directory", None)

    if not use_case or not sequence_diagram:
        raise ValueError("Missing use_case or sequence_diagram in AgentState.")
    if not working_dir:
        raise ValueError("Missing working_directory in GraphContext.")

    source_code_context = _read_source_files(working_dir)

    messages = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(
            USER_PROMPT.format(
                use_case=use_case,
                sequence_diagram=sequence_diagram,
                source_code_context=source_code_context,
            ),
        ),
    ]

    plan: QAPlan = await structured_llm.ainvoke(messages)
    logger.debug(f"QA Agent plan: {len(plan.files)} files to write.")

    for file_change in plan.files:
        clean_path = file_change.path.lstrip("/\\")
        full_path = working_dir / clean_path

        logger.info(f"Writing file: {full_path}")
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(file_change.content)

    return state


def _read_source_files(root: Path) -> str:
    """
    Reads all Python files in the src/ directory to provide context to the LLM.
    Returns a formatted string.
    """
    src_path = root / "src"
    if not src_path.exists():
        return "(No source files found in src/)"

    context_parts = []
    for file_path in src_path.rglob("*.py"):
        rel_path = file_path.relative_to(root)
        try:
            content = file_path.read_text(encoding="utf-8")
            context_parts.append(f"--- File: {rel_path} ---\n{content}\n")
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")

    return "\n".join(context_parts)


SYSTEM_PROMPT = """
You are the QA Agent (Quality Assurance) in a software development pipeline. Your goal is to write a comprehensive Pytest test suite and update the source code with necessary method stubs.

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
- The current source code likely contains empty classes (e.g., `class VendingMachine: pass`).
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
