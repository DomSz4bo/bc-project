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


class ValidationResult(NamedTuple):
    is_valid: bool
    message: str | None


async def validate_mermaid(mermaid_code: str) -> ValidationResult:
    rendering_tool = (await client.get_tools())[0]

    try:
        await rendering_tool.ainvoke({"mermaid": mermaid_code})
        is_valid = True
    except McpError as e:
        is_valid = False
        error_msg = e.error.message
        error_msg = error_msg[error_msg.find(": ") + 2 :]

    return ValidationResult(is_valid, None if is_valid else error_msg)
