import asyncio
import base64
import json
import zlib
from functools import lru_cache
from pathlib import Path
from string import whitespace
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


def extract_mermaid_code(markdown_mermaid: str) -> str:
    return markdown_mermaid.strip(whitespace + "`").removeprefix("mermaid").strip()


def generate_mermaid_url(graph_code: str, theme="default") -> str:
    """
    Encodes the mermaid graph into a "pako:" string.
    Useful for visualizing diagram on mermaid.ink or using importing to mermaid editors.
    Handles graph code wrapped in markdown mermaid block correctly.
    """
    if graph_code.startswith("```"):
        mmd_code = extract_mermaid_code(graph_code)
    state = {"code": mmd_code, "mermaid": {"theme": theme}}

    json_str = json.dumps(state)
    compressed = zlib.compress(json_str.encode("utf-8"), level=9)
    base64_str = base64.urlsafe_b64encode(compressed).decode("utf-8").replace("=", "")

    return f"pako:{base64_str}"


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
    return "Mermaid reference documentation not found."


if __name__ == "__main__":
    mmd_code = """sequenceDiagram
    Alice->>+John: Hello John, how are you?
    Alice->>+John: John, can you hear me?
    John-->>-Alice: Hi Alice, I can hear you!
    John-->>-Alice: I feel great!"""
    result = asyncio.run(validate_mermaid(mmd_code))

    my_code = """sequenceDiagram
    Alice->>+John: Hello John, how are you?
    Alice->>+John: John, can you hear me?
    John-->>-Alice: Hi Alice, I can hear you!
    John-->>-Alice: I feel great!"""
    img_url = "https://mermaid.ink/img/" + generate_mermaid_url(my_code, "base")
    print(img_url)
