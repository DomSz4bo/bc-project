from pathlib import Path

from loguru import logger


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
