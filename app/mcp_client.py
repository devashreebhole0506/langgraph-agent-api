import sys
from pathlib import Path

from langchain.mcp import MCPAdapter


PROJECT_ROOT = Path(__file__).resolve().parent.parent


async def load_tools():
    """Load tools from this project's local MCP server over stdio."""
    config = {
        "mcpServers": {
            "project": {
                "command": sys.executable,
                "args": ["-m", "mcp_server.server"],
                "cwd": str(PROJECT_ROOT),
            }
        }
    }
    async with MCPAdapter(config) as adapter:
        tools = await adapter.list_tools()
    if not tools:
        raise RuntimeError("The configured MCP server did not expose any tools.")
    return tools
