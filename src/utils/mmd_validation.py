import asyncio
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
    error_message: str | None


async def validate_mermaid(mermaid_code: str) -> ValidationResult:
    try:
        await rendering_tool.ainvoke({"mermaid": mermaid_code, "outputType": "mermaid"})
        is_valid = True
    except McpError as e:
        is_valid = False
        error_msg = e.error.message
        error_msg = error_msg[error_msg.find(": ") + 2 :]

    return ValidationResult(is_valid, None if is_valid else error_msg)


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