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
            # Allow more time for remote servers and npm installs
            timeout = 20.0  # Increased from 12 to 20 seconds for npm package downloads
            if "mcp-remote" in server.args or any(
                "remote" in arg for arg in server.args
            ):
                timeout = 25.0  # Give remote servers more time
                logger.info(
                    f"Allowing {timeout}s timeout for remote MCP server {server.name}"
                )
            elif "-y" in server.args or "@" in " ".join(server.args):
                # NPM packages might need download time on first run
                timeout = 25.0
                logger.info(
                    f"Allowing {timeout}s timeout for npm package {server.name}"
                )

            logger.info(
                f"Connecting to {server.name} with command: {server.command} {' '.join(server.args)}"
            )

            await asyncio.wait_for(
                client.connect_stdio(),
                timeout=timeout,
            )
            mcp_clients.append(client)
            logger.info(f"✅ Successfully connected to stdio MCP server {server.name}")
        except asyncio.TimeoutError:
            logger.warning(
                f"⚠️ Connection to stdio MCP server {server.name} timed out after {timeout} seconds"
            )
        except Exception as e:
            logger.error(
                f'Failed to connect to stdio MCP server {server.name}: {str(e)}',
                exc_info=True,
            )

    return mcp_clients
