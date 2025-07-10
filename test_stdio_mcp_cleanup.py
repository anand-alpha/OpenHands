#!/usr/bin/env python
"""
Test script to verify that stdio MCP clients are properly cleaned up.
"""

import asyncio
import atexit
import sys
from typing import List

from openhands.core.config.mcp_config import (
    MCPConfig,
    MCPStdioServerConfig,
)
from openhands.mcp import (
    cleanup_all_mcp_clients,
    get_active_mcp_clients_count,
)
from openhands.mcp.stdio_client import create_stdio_mcp_clients
from openhands.core.logger import openhands_logger as logger


# Register cleanup function with atexit
def exit_cleanup():
    logger.info(
        f"Running exit cleanup, active clients: {get_active_mcp_clients_count()}"
    )
    cleanup_all_mcp_clients()
    logger.info(
        f"Cleanup complete, remaining clients: {get_active_mcp_clients_count()}"
    )


atexit.register(exit_cleanup)


async def main():
    # Create a test config with echo as a mock stdio server
    stdio_servers = [
        MCPStdioServerConfig(
            name="echo-test",
            command="echo",
            args=[
                "{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"serverInfo\":{\"name\":\"test\"}}}"
            ],
            env={},
        ),
    ]

    try:
        logger.info("Creating stdio MCP clients...")
        clients = await create_stdio_mcp_clients(stdio_servers)
        logger.info(f"Created {len(clients)} stdio MCP clients")
    except Exception as e:
        logger.error(f"Error creating stdio clients: {e}")

    # Display active clients count
    logger.info(f"Active MCP clients count: {get_active_mcp_clients_count()}")

    # Explicitly call cleanup for testing
    cleanup_all_mcp_clients()

    # Check count again
    logger.info(
        f"After cleanup, active MCP clients count: {get_active_mcp_clients_count()}"
    )


if __name__ == "__main__":
    logger.info("Starting stdio MCP cleanup test")
    asyncio.run(main())
    logger.info("stdio MCP cleanup test complete")
