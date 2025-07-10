"""Fix circular imports in MCP modules."""

from openhands.mcp.registry import (
    register_mcp_client,
    unregister_mcp_client,
    get_active_mcp_clients_count,
    _active_mcp_clients,
)
