"""Module for MCP client protocol definitions."""

from typing import Any, Dict, List, Protocol

from openhands.mcp.tool import MCPClientTool


class MCPClientProtocol(Protocol):
    """Protocol defining the interface for MCP clients."""

    tools: List[MCPClientTool]
    tool_map: Dict[str, MCPClientTool]
    server_info: str

    def close(self) -> None:
        """Close any connections."""
        ...

    async def call_tool(self, tool_name: str, args: Dict) -> Any:
        """Call a tool on the MCP server."""
        ...
