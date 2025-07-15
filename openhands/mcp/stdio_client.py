"""Module for creating MCP stdio clients with robust package management."""

import asyncio
import sys
from typing import List

from openhands.core.config.mcp_config import MCPStdioServerConfig
from openhands.core.logger import openhands_logger as logger
from openhands.mcp.client import MCPClient
from openhands.mcp.stdio import StdioMCPClient
from openhands.mcp.package_manager import MCPPackageManager


async def create_stdio_mcp_clients(
    stdio_servers: list[MCPStdioServerConfig],
    conversation_id: str | None = None,
) -> List[MCPClient]:
    """Create MCP clients for stdio servers with robust error handling and package management"""

    # Skip MCP clients on Windows
    if sys.platform == 'win32':
        logger.info(
            'MCP functionality is disabled on Windows, skipping stdio client creation'
        )
        return []

    if not stdio_servers:
        return []

    mcp_clients = []
    successful_connections = 0
    total_servers = len(stdio_servers)

    async with MCPPackageManager() as package_manager:
        # Check prerequisites
        prerequisites = package_manager.check_prerequisites()
        missing_tools = [
            tool for tool, available in prerequisites.items() if not available
        ]

        if missing_tools:
            logger.warning(f"⚠️ Missing tools: {', '.join(missing_tools)}")
            logger.warning("Some MCP servers may not work without these tools")

        for server in stdio_servers:
            logger.info(f'🔧 Preparing MCP server: {server.name}')

            # Prepare server (validate and install if needed)
            success, message = await package_manager.prepare_server(server)

            if not success:
                logger.error(f'❌ Failed to prepare {server.name}: {message}')
                continue

            logger.info(f'✅ {server.name}: {message}')

            # Create and connect client
            client = StdioMCPClient(server_config=server)

            try:
                # Determine timeout based on server type
                timeout = _get_server_timeout(server)

                logger.info(
                    f"🔌 Connecting to {server.name} with command: {server.command} {' '.join(server.args)}"
                )

                await asyncio.wait_for(
                    client.connect_stdio(),
                    timeout=timeout,
                )

                mcp_clients.append(client)
                successful_connections += 1
                logger.info(
                    f"✅ Successfully connected to stdio MCP server {server.name}"
                )

            except asyncio.TimeoutError:
                logger.warning(
                    f"⚠️ Connection to stdio MCP server {server.name} timed out after {timeout} seconds"
                )
            except Exception as e:
                logger.error(
                    f'❌ Failed to connect to stdio MCP server {server.name}: {str(e)}',
                    exc_info=False,  # Reduce noise in logs
                )

    # Log summary
    if successful_connections > 0:
        logger.info(
            f"✅ Successfully connected to {successful_connections}/{total_servers} MCP servers"
        )
    else:
        logger.warning(f"⚠️ No MCP servers connected (0/{total_servers})")

    return mcp_clients


def _get_server_timeout(server: MCPStdioServerConfig) -> float:
    """Determine appropriate timeout for server type"""
    # Base timeout for stdio connections
    timeout = 45.0  # Increased base timeout significantly for package downloads

    # Check for indicators that might need more time
    args_str = " ".join(server.args)

    if "remote" in args_str.lower():
        timeout = 60.0  # Remote servers need more time
        logger.info(f"Using {timeout}s timeout for remote MCP server {server.name}")
    elif "@" in args_str and server.command == "npx":
        # NPM packages might need download time on first run
        timeout = 60.0  # Increased timeout for npm packages
        logger.info(f"Using {timeout}s timeout for npm package {server.name}")
    elif server.command == "docker":
        # Docker images might need pull time
        timeout = 90.0  # Docker needs more time for image pulls
        logger.info(f"Using {timeout}s timeout for docker image {server.name}")

    return timeout
