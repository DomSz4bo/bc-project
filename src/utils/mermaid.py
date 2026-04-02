import asyncio
from functools import lru_cache
from pathlib import Path
from time import perf_counter
from typing import NamedTuple

from langchain_mcp_adapters.client import MultiServerMCPClient
from mcp.shared.exceptions import McpError

client = MultiServerMCPClient(
    {
        "mcp-mermaid": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "mcp-mermaid"],
        }
    }
)

rendering_tool = asyncio.run(client.get_tools())[0]


class ValidationResult(NamedTuple):
    is_valid: bool
    error_message: str | None = None


async def validate_mermaid(mermaid_code: str) -> ValidationResult:
    try:
        await rendering_tool.ainvoke({"mermaid": mermaid_code, "outputType": "mermaid"})
        return ValidationResult(True)
    except McpError as e:
        error_msg = e.error.message
        error_msg = error_msg[error_msg.find(": ") + 2 :]
        return ValidationResult(False, error_msg)


@lru_cache(maxsize=1)
def get_mermaid_reference() -> str:
    """
    Reads the Mermaid sequence diagram reference documentation.
    """
    mmd_reference_path = (
        Path(__file__).parents[2] / "files" / "mermaid_sqd_reference.md"
    )
    if mmd_reference_path.exists():
        return mmd_reference_path.read_text(encoding="utf-8")
    ## TODO
    raise FileNotFoundError("Mermaid reference file not found!")
    # return "Mermaid reference documentation not found."


if __name__ == "__main__":
    mmd_code = """sequenceDiagram
    Alice->>+John: Hello John, how are you?
    Alice->>+John: John, can you hear me?
    John-->>-Alice: Hi Alice, I can hear you!
    John-->>-Alice: I feel great!"""
    start = perf_counter()
    result = asyncio.run(validate_mermaid(mmd_code))
    end = perf_counter()
    print(f"Result: {result}, \t time: {end - start} s")
    print("\n", get_mermaid_reference())
