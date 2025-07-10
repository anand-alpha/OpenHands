"""
MCP (Model Context Protocol) module.

This module provides tools for integrating with MCP servers.
"""

# First import registry which has no dependencies
from openhands.mcp.registry import (
    register_mcp_client,
    unregister_mcp_client,
    get_active_mcp_clients_count,
    cleanup_all_mcp_clients,
)

# Expose the main add_mcp_tools_to_agent function for external use
from openhands.mcp.utils import add_mcp_tools_to_agent

# Protocol definitions have minimal dependencies
from openhands.mcp.protocol import MCPClientProtocol


# Avoid eagerly importing these as they can cause circular dependencies
# Instead import them when needed
def get_mcp_client():
    from openhands.mcp.client import MCPClient

    return MCPClient


def get_mcp_tool():
    from openhands.mcp.tool import MCPClientTool

    return MCPClientTool


__all__ = [
    "add_mcp_tools_to_agent",
    "register_mcp_client",
    "unregister_mcp_client",
    "get_active_mcp_clients_count",
    "cleanup_all_mcp_clients",
    "MCPClientProtocol",
    "get_mcp_client",
    "get_mcp_tool",
]
