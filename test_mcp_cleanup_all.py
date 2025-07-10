#!/usr/bin/env python
"""
Test script to verify that all MCP clients are properly cleaned up on exit.
"""

import asyncio
import atexit
import sys
from typing import List

from openhands.core.config.mcp_config import (
    MCPConfig,
    MCPSSEServerConfig,
    MCPSHTTPServerConfig,
    MCPStdioServerConfig,
)
from openhands.mcp import (
    cleanup_all_mcp_clients,
    get_active_mcp_clients_count,
)
from openhands.mcp.utils import (
    create_mcp_clients,
    fetch_mcp_tools_from_config,
)
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
    # Create a test config
    config = MCPConfig(
        sse_servers=[
            MCPSSEServerConfig(url="https://example.com/mcp", api_key="test"),
        ],
        shttp_servers=[
            MCPSHTTPServerConfig(url="https://example.com/mcp2", api_key="test"),
        ],
        stdio_servers=[],
    )

    # Create some clients
    try:
        logger.info("Fetching MCP tools from config...")
        tools = await fetch_mcp_tools_from_config(config)
        logger.info(f"MCP tools fetched: {tools}")
    except Exception as e:
        logger.error(f"Error fetching tools: {e}")

    # Display active clients count
    logger.info(f"Active MCP clients count: {get_active_mcp_clients_count()}")

    # Explicitly call cleanup for testing
    cleanup_all_mcp_clients()

    # Check count again
    logger.info(
        f"After cleanup, active MCP clients count: {get_active_mcp_clients_count()}"
    )


if __name__ == "__main__":
    logger.info("Starting MCP cleanup test")
    asyncio.run(main())
    logger.info("MCP cleanup test complete")
