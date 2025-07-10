"""Module for shared utilities for MCP client management."""

import weakref
from typing import Any, List, TypeVar, Set

# Type variable for MCPClient to avoid circular imports
MCPClientT = TypeVar('MCPClientT')

from openhands.core.logger import openhands_logger as logger

# Global registry to track active MCP clients for cleanup
_active_mcp_clients: List[Any] = []


def register_mcp_client(client: Any) -> None:
    """Register an MCP client for cleanup tracking"""
    global _active_mcp_clients

    if client not in _active_mcp_clients:
        _active_mcp_clients.append(client)
        logger.debug(
            f"Registered MCP client: {client.server_info if hasattr(client, 'server_info') else 'unknown'}"
        )
        logger.debug(f"Active MCP clients count: {len(_active_mcp_clients)}")


def unregister_mcp_client(client: Any) -> None:
    """Unregister an MCP client from cleanup tracking"""
    global _active_mcp_clients

    try:
        if client in _active_mcp_clients:
            _active_mcp_clients.remove(client)
            logger.debug(
                f"Unregistered MCP client: {client.server_info if hasattr(client, 'server_info') else 'unknown'}"
            )
            logger.debug(f"Active MCP clients count: {len(_active_mcp_clients)}")
    except (ValueError, KeyError):
        pass  # Client not in list


def get_active_mcp_clients_count() -> int:
    """Return the current count of active MCP clients"""
    return len(_active_mcp_clients)


def cleanup_all_mcp_clients() -> None:
    """Close all active MCP clients"""
    global _active_mcp_clients

    # Make a copy of the set to avoid modification during iteration
    clients = list(_active_mcp_clients)

    for client in clients:
        try:
            logger.debug(
                f"Cleaning up MCP client: {client.server_info if hasattr(client, 'server_info') else 'unknown'}"
            )
            if hasattr(client, 'close') and callable(client.close):
                client.close()
            # Client's close method should call unregister_mcp_client
        except Exception as e:
            logger.debug(f"Error during MCP client cleanup: {e}")
            # Make sure client is unregistered even if close fails
            unregister_mcp_client(client)

    # Final check to ensure registry is empty
    if _active_mcp_clients:
        logger.warning(
            f"Some MCP clients ({len(_active_mcp_clients)}) failed to unregister during cleanup"
        )
        _active_mcp_clients.clear()
