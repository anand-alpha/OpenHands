import asyncio
import json
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from openhands.controller.agent import Agent


from openhands.core.config.mcp_config import (
    MCPConfig,
    MCPSHTTPServerConfig,
    MCPSSEServerConfig,
    MCPStdioServerConfig,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events.action.mcp import MCPAction
from openhands.events.observation.mcp import MCPObservation
from openhands.events.observation.observation import Observation
from openhands.mcp.client import MCPClient
from openhands.memory.memory import Memory
from openhands.runtime.base import Runtime

# Import registry functions for client management
from openhands.mcp.registry import (
    register_mcp_client,
    unregister_mcp_client,
    get_active_mcp_clients_count,
    _active_mcp_clients,
)

# Import stdio client functions
from openhands.mcp.stdio_client import create_stdio_mcp_clients


def convert_mcp_clients_to_tools(mcp_clients: list[MCPClient] | None) -> list[dict]:
    """
    Converts a list of MCPClient instances to ChatCompletionToolParam format
    that can be used by CodeActAgent.

    Args:
        mcp_clients: List of MCPClient instances or None

    Returns:
        List of dicts of tools ready to be used by CodeActAgent
    """
    if mcp_clients is None:
        logger.warning('mcp_clients is None, returning empty list')
        return []

    all_mcp_tools = []
    try:
        for client in mcp_clients:
            # Each MCPClient has an mcp_clients property that is a ToolCollection
            # The ToolCollection has a to_params method that converts tools to ChatCompletionToolParam format
            for tool in client.tools:
                mcp_tools = tool.to_param()
                all_mcp_tools.append(mcp_tools)
    except Exception as e:
        logger.error(f'Error in convert_mcp_clients_to_tools: {e}')
        return []
    return all_mcp_tools


async def create_mcp_clients(
    sse_servers: list[MCPSSEServerConfig],
    shttp_servers: list[MCPSHTTPServerConfig],
    conversation_id: str | None = None,
) -> list[MCPClient]:
    """Create MCP clients for SSE and SHTTP servers"""
    import sys
    import anyio

    # Skip MCP clients on Windows
    if sys.platform == 'win32':
        logger.info(
            'MCP functionality is disabled on Windows, skipping HTTP/SSE client creation'
        )
        return []

    all_servers = []
    for server in sse_servers:
        all_servers.append((server, False))  # False = SSE
    for server in shttp_servers:
        all_servers.append((server, True))  # True = SHTTP

    if not all_servers:
        return []

    mcp_clients = []

    for server, is_shttp in all_servers:
        connection_type = 'SHTTP' if is_shttp else 'SSE'
        logger.info(
            f'Initializing MCP agent for {server} with {connection_type} connection...'
        )
        client = MCPClient()

        try:
            # Add timeout for HTTP/SSE connections
            await asyncio.wait_for(
                client.connect_http(server, conversation_id=conversation_id),
                timeout=5.0,  # Reduced from 10 to 5 second timeout per server
            )

            # Only add the client to the list after a successful connection
            mcp_clients.append(client)
            # Register client for cleanup
            register_mcp_client(client)

        except asyncio.TimeoutError:
            logger.warning(f'Connection to {server} timed out after 5 seconds')
        except anyio.ClosedResourceError as e:
            # Specifically handle ClosedResourceError more gracefully
            logger.warning(f'Stream closed unexpectedly during connection to {server}')
            logger.debug(f'ClosedResourceError details: {e}')
        except Exception as e:
            # Log less verbosely for common connection issues
            if isinstance(e, (ConnectionError, ConnectionRefusedError, OSError)):
                logger.warning(
                    f'Connection failed to {server}: {type(e).__name__}: {str(e)}'
                )
            else:
                logger.error(f'Failed to connect to {server}: {str(e)}')
                logger.debug(f'Connection error details', exc_info=True)

    return mcp_clients


async def fetch_mcp_tools_from_config(
    mcp_config: MCPConfig, conversation_id: str | None = None
) -> list[dict]:
    """
    Retrieves the list of MCP tools from the MCP clients.

    Args:
        mcp_config: The MCP configuration
        conversation_id: Optional conversation ID to associate with the MCP clients

    Returns:
        A list of tool dictionaries. Returns an empty list if no connections could be established.
    """
    import sys
    import anyio

    # Skip MCP tools on Windows
    if sys.platform == 'win32':
        logger.info('MCP functionality is disabled on Windows, skipping tool fetching')
        return []

    mcp_clients = []
    mcp_tools = []
    try:
        logger.info(f'Creating MCP clients with config: {mcp_config}')
        logger.info(f'SSE servers: {mcp_config.sse_servers}')
        logger.info(f'SHTTP servers: {mcp_config.shttp_servers}')
        logger.info(f'Stdio servers: {mcp_config.stdio_servers}')

        # Create HTTP/SSE clients
        # Create HTTP/SSE clients
        mcp_clients = await create_mcp_clients(
            mcp_config.sse_servers, mcp_config.shttp_servers, conversation_id
        )
        logger.info(f'Successfully created {len(mcp_clients)} HTTP/SSE MCP clients')

        # Create stdio clients
        stdio_clients = await create_stdio_mcp_clients(
            mcp_config.stdio_servers, conversation_id
        )
        logger.info(f'Successfully created {len(stdio_clients)} stdio MCP clients')

        # Combine all clients
        mcp_clients.extend(stdio_clients)

        if not mcp_clients:
            logger.warning('No MCP clients were successfully connected')
            return []

        # Convert tools to the format expected by the agent
        mcp_tools = convert_mcp_clients_to_tools(mcp_clients)
        logger.info(f'Converted {len(mcp_tools)} MCP tools from clients')

    except anyio.ClosedResourceError as e:
        logger.warning(f'Stream closed unexpectedly during MCP tool initialization')
        logger.debug(f'ClosedResourceError details: {e}')
        # Return tools from any clients that were successfully initialized
        if mcp_clients:
            mcp_tools = convert_mcp_clients_to_tools(mcp_clients)
            logger.info(
                f'Recovered {len(mcp_tools)} MCP tools from partial initialization'
            )
    except Exception as e:
        logger.error(f'Error fetching MCP tools: {str(e)}')
        logger.debug(f'MCP tool fetch error details', exc_info=True)
        # Try to get any tools from clients that were successfully initialized
        if mcp_clients:
            try:
                mcp_tools = convert_mcp_clients_to_tools(mcp_clients)
                logger.info(
                    f'Recovered {len(mcp_tools)} MCP tools from partial initialization'
                )
            except Exception:
                return []
        else:
            return []

    logger.info(f'Final MCP tools: {mcp_tools}')
    return mcp_tools


async def call_tool_mcp(mcp_clients: list[MCPClient], action: MCPAction) -> Observation:
    """
    Call a tool on an MCP server and return the observation.

    Args:
        mcp_clients: The list of MCP clients to execute the action on
        action: The MCP action to execute

    Returns:
        The observation from the MCP server
    """
    import sys

    from openhands.events.observation import ErrorObservation

    # Skip MCP tools on Windows
    if sys.platform == 'win32':
        logger.info('MCP functionality is disabled on Windows')
        return ErrorObservation('MCP functionality is not available on Windows')

    if not mcp_clients:
        raise ValueError('No MCP clients found')

    logger.debug(f'MCP action received: {action}')

    # Find the MCP client that has the matching tool name
    matching_client = None
    logger.debug(f'MCP clients: {mcp_clients}')
    logger.debug(f'MCP action name: {action.name}')

    for client in mcp_clients:
        logger.debug(f'MCP client tools: {client.tools}')
        if action.name in [tool.name for tool in client.tools]:
            matching_client = client
            break

    if matching_client is None:
        raise ValueError(f'No matching MCP agent found for tool name: {action.name}')

    logger.debug(f'Matching client: {matching_client}')

    # Call the tool - this will create a new connection internally
    response = await matching_client.call_tool(action.name, action.arguments)
    logger.debug(f'MCP response: {response}')

    # Handle both Pydantic model responses and dict responses
    if hasattr(response, 'model_dump'):
        content = json.dumps(response.model_dump(mode='json'))
    else:
        content = json.dumps(response)

    return MCPObservation(
        content=content,
        name=action.name,
        arguments=action.arguments,
    )


async def add_mcp_tools_to_agent(agent: 'Agent', runtime: Runtime, memory: 'Memory'):
    """
    Add MCP tools to an agent.
    """
    import sys

    # Skip MCP tools on Windows
    if sys.platform == 'win32':
        logger.info('MCP functionality is disabled on Windows, skipping MCP tools')
        agent.set_mcp_tools([])
        return

    assert (
        runtime.runtime_initialized
    ), 'Runtime must be initialized before adding MCP tools'

    extra_stdio_servers = []

    # Add microagent MCP tools if available
    microagent_mcp_configs = memory.get_microagent_mcp_tools()
    for mcp_config in microagent_mcp_configs:
        if mcp_config.sse_servers:
            logger.warning(
                'Microagent MCP config contains SSE servers, it is not yet supported.'
            )

        if mcp_config.stdio_servers:
            for stdio_server in mcp_config.stdio_servers:
                # Check if this stdio server is already in the config
                if stdio_server not in extra_stdio_servers:
                    extra_stdio_servers.append(stdio_server)
                    logger.info(f'Added microagent stdio server: {stdio_server.name}')

    # Add the runtime as another MCP server
    updated_mcp_config = runtime.get_mcp_config(extra_stdio_servers)

    # Fetch the MCP tools
    logger.info(f"Fetching MCP tools from config: {updated_mcp_config}")
    mcp_tools = await fetch_mcp_tools_from_config(updated_mcp_config)

    logger.info(
        f'Loaded {len(mcp_tools)} MCP tools: {[tool["function"]["name"] for tool in mcp_tools]}'
    )

    # Set the MCP tools on the agent
    logger.info(f"Setting {len(mcp_tools)} MCP tools on the agent")
    agent.set_mcp_tools(mcp_tools)
    logger.info("MCP tools have been set on the agent")


async def cleanup_all_mcp_clients(force_kill: bool = False) -> None:
    """Clean up all registered MCP clients

    Args:
        force_kill: If True, immediately kill processes without graceful termination
    """
    # Import asyncio here to avoid issues with module teardown order
    import asyncio

    clients_to_cleanup = list(_active_mcp_clients)
    logger.debug(f"Cleaning up {len(clients_to_cleanup)} MCP clients...")

    # Phase 1: Initial cleanup attempt
    for client in clients_to_cleanup:
        try:
            if hasattr(client, 'close'):
                client.close()
        except Exception as e:
            logger.debug(f"Error during initial MCP client cleanup: {e}")

    # If force_kill is True, immediately kill all processes
    if force_kill:
        logger.debug("Force killing all MCP processes")
        # Re-get the list of active clients
        for client in list(_active_mcp_clients):
            try:
                if hasattr(client, 'process') and client.process:
                    process = client.process
                    client.process = None  # Clear reference first

                    try:
                        logger.debug(
                            f"Force killing process for {client.server_info if hasattr(client, 'server_info') else 'unknown'}"
                        )
                        if process and process.returncode is None:
                            process.kill()
                    except Exception:
                        pass

                # Remove from tracking list
                unregister_mcp_client(client)
            except Exception as e:
                logger.debug(f"Error during forced MCP client cleanup: {e}")

        # Clear the registry
        _active_mcp_clients.clear()
        return

    # After initial cleanup, give a short grace period for processes to terminate
    await asyncio.sleep(0.5)

    # Phase 2: Check if any clients still have active processes and force terminate
    remaining_clients = list(_active_mcp_clients)
    if remaining_clients:
        logger.debug(f"Force killing {len(remaining_clients)} remaining processes")

        # Forcefully terminate any remaining processes
        for client in remaining_clients:
            try:
                if hasattr(client, 'process') and client.process:
                    try:
                        process = client.process  # Get a reference before clearing
                        logger.debug(
                            f"Force killing process for {client.server_config.name}"
                        )
                        # Clear the reference first to prevent other code from using it
                        client.process = None

                        # Kill the process
                        if process and process.returncode is None:
                            process.kill()
                            # Wait briefly for process to terminate
                            try:
                                await asyncio.wait_for(process.wait(), timeout=0.5)
                            except (asyncio.TimeoutError, AttributeError):
                                pass
                    except Exception as e:
                        logger.debug(f"Error killing process: {e}")

                # Remove from tracking list regardless of errors
                unregister_mcp_client(client)
            except Exception as e:
                logger.debug(f"Error during forced MCP client cleanup: {e}")

    # Phase 3: Final cleanup of the registry
    _active_mcp_clients.clear()

    # Phase 4: Run garbage collection to help clean up any references
    import gc

    gc.collect()

    logger.debug("MCP client cleanup completed")
