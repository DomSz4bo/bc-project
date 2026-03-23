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

    context_parts = []
    for file_path in src_path.rglob("*.py"):
        rel_path = file_path.relative_to(root)
        try:
            content = file_path.read_text(encoding="utf-8")
            context_parts.append(f"--- File: {rel_path} ---\n{content}\n")
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")

    return "\n".join(context_parts)
