from langchain_mcp_adapters.client import MultiServerMCPClient
from pathlib import Path


def get_filesystem_client(allowed_dir: Path):
    return MultiServerMCPClient(
        {
            "filesystem": {
                "transport": "stdio",
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    str(allowed_dir),
                ],
            }
        }
    )
