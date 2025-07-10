"""Module for creating MCP stdio clients."""

import asyncio
import json
import os
from typing import List

from openhands.core.config.mcp_config import MCPStdioServerConfig
from openhands.core.logger import openhands_logger as logger
from openhands.mcp.client import MCPClient
from openhands.mcp.stdio import StdioMCPClient


async def create_stdio_mcp_clients(
    stdio_servers: list[MCPStdioServerConfig],
    conversation_id: str | None = None,
) -> List[MCPClient]:
    """Create MCP clients for stdio servers"""
    import sys
    import anyio

    # Skip MCP clients on Windows
    if sys.platform == 'win32':
        logger.info(
            'MCP functionality is disabled on Windows, skipping stdio client creation'
        )
        return []

    if not stdio_servers:
        return []

    mcp_clients = []

    for server in stdio_servers:
        logger.info(f'Initializing stdio MCP client for {server.name}...')
        client = StdioMCPClient(server_config=server)

        try:
            # Add timeout for stdio connections
            await asyncio.wait_for(
                client.connect_stdio(),
                timeout=5.0,  # Reduced from 10 to 5 second timeout per server
            )
            mcp_clients.append(client)
        except asyncio.TimeoutError:
            logger.warning(
                f'Connection to stdio MCP server {server.name} timed out after 5 seconds'
            )
        except Exception as e:
            logger.error(
                f'Failed to connect to stdio MCP server {server.name}: {str(e)}',
                exc_info=True,
            )

    return mcp_clients
