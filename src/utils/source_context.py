from pathlib import Path
from typing import Any, NamedTuple
from loguru import logger


class SourceContext(NamedTuple):
    use_case: str
    sequence_diagram: str
    source_code_context: str
    test_files_context: str


def extract_project_context(state: dict[str, Any], working_dir: Path):
    """
    Extract design artifacts (UC and Sequence Diagram) from the state and
    attempts to read source code and test files.
    """
    use_case = state.get("use_case")
    sequence_diagram = state.get("sequence_diagram")
    if not use_case:
        raise KeyError("No use_case found in state.")
    if not sequence_diagram:
        raise KeyError("No sequence_diagram found in state.")
    if not working_dir:
        raise ValueError("Working directory can NOT be None.")
    source_code_context = read_source_files(working_dir)
    test_files_context = read_test_files(working_dir)
    return SourceContext(
        use_case, sequence_diagram, source_code_context, test_files_context
    )


def read_source_files(root: Path) -> str:
    """
    Reads all Python files in the src/ directory to provide context to the LLM.
    Returns a formatted string.
    """
    src_path = root / "src"
    if not src_path.exists():
        return "(No source files found in src/)"

    source_files = _read_python_files(src_path, root)
    return source_files


def read_test_files(root: Path) -> str:
    """
    Reads all Python files in the tests/ directory to provide context to the LLM.
    Returns a formatted string.
    """
    tests_path = root / "tests"
    if not tests_path.exists():
        return "(No test files found in tests/)"

    test_files = _read_python_files(tests_path, root)
    return test_files


def _read_python_files(path: Path, root: Path) -> str:
    file_contents = []
    for file_path in path.rglob("*.py"):
        rel_path = file_path.relative_to(root)
        try:
            content = file_path.read_text(encoding="utf-8")
            file_contents.append(f"--- File: {rel_path} ---\n{content}\n")
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")

    return "\n".join(file_contents)
