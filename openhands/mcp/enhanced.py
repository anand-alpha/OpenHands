"""Module for enhanced MCP client utilities."""

import json
import asyncio
from typing import TYPE_CHECKING, Any, List, Dict, Optional

if TYPE_CHECKING:
    from openhands.controller.agent import Agent

from openhands.core.config.mcp_config import (
    MCPConfig,
    MCPSHTTPServerConfig,
    MCPSSEServerConfig,
    MCPStdioServerConfig,
)
from openhands.core.logger import openhands_logger as logger
from openhands.mcp.client import MCPClient
from openhands.mcp.protocol import MCPClientProtocol
from openhands.mcp.registry import (
    register_mcp_client,
    unregister_mcp_client,
    get_active_mcp_clients_count,
    cleanup_all_mcp_clients,
)
from openhands.mcp.utils import fetch_mcp_tools_from_config


async def enhanced_add_mcp_tools_to_agent(
    agent: 'Agent',
    mcp_config: Optional[MCPConfig] = None,
    runtime: Any = None,
    memory: Any = None,
) -> None:
    """
    Enhanced version to add MCP tools to the agent.

    Args:
        agent: The agent to add MCP tools to
        mcp_config: Optional MCP configuration override. If not provided, the agent's runtime's config.mcp will be used.
        runtime: Optional runtime object (for backward compatibility)
        memory: Optional memory object (for backward compatibility)
    """
    import sys
    import anyio

    # Skip MCP integration on Windows
    if sys.platform == 'win32':
        logger.info('MCP functionality is disabled on Windows')
        return

    try:
        # Use provided config or get from runtime
        updated_mcp_config = mcp_config
        if not updated_mcp_config and runtime:
            updated_mcp_config = runtime.config.mcp
        elif not updated_mcp_config and hasattr(agent, 'runtime'):
            updated_mcp_config = agent.runtime.config.mcp

        if not updated_mcp_config:
            logger.warning('No MCP configuration found, skipping MCP tools')
            return

        # First log the MCP config details to help with debugging
        logger.debug(f"Adding MCP tools with config: {updated_mcp_config}")
        if hasattr(updated_mcp_config, 'stdio_servers'):
            logger.debug(
                f"stdio_servers count: {len(updated_mcp_config.stdio_servers)}"
            )
            for i, server in enumerate(updated_mcp_config.stdio_servers):
                logger.debug(
                    f"stdio server {i+1}: {server.name} - {server.command} {' '.join(server.args)}"
                )

        if hasattr(updated_mcp_config, 'sse_servers'):
            logger.debug(f"sse_servers count: {len(updated_mcp_config.sse_servers)}")
            for i, server in enumerate(updated_mcp_config.sse_servers):
                logger.debug(f"SSE server {i+1}: {server.url}")

        if hasattr(updated_mcp_config, 'shttp_servers'):
            logger.debug(
                f"shttp_servers count: {len(updated_mcp_config.shttp_servers)}"
            )
            for i, server in enumerate(updated_mcp_config.shttp_servers):
                logger.debug(f"SHTTP server {i+1}: {server.url}")

        # Fetch MCP tools with proper error handling
        mcp_tools = await fetch_mcp_tools_from_config(updated_mcp_config)

        # Add tools to agent if any were successfully fetched
        if mcp_tools:
            logger.info(f'Adding {len(mcp_tools)} MCP tools to agent')
            if not hasattr(agent, 'mcp_tools') or agent.mcp_tools is None:
                agent.mcp_tools = []
            elif isinstance(agent.mcp_tools, dict):
                # Convert dict to list if needed
                agent.mcp_tools = (
                    list(agent.mcp_tools.values()) if agent.mcp_tools else []
                )

            agent.mcp_tools.extend(mcp_tools)
            # Note: agent.register_tools() is not a standard method, so we just add to mcp_tools
        else:
            logger.warning('No MCP tools were successfully loaded')

    except anyio.ClosedResourceError as e:
        logger.warning(f'Stream closed unexpectedly during MCP tool setup: {e}')
    except asyncio.TimeoutError as e:
        logger.warning(f'MCP tool setup timed out: {e}')
    except Exception as e:
        logger.error(f'Error adding MCP tools to agent: {e}')
        logger.debug(f'MCP tools error details', exc_info=True)

    # Return the agent for fluent API use
    return agent
