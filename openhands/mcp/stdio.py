"""Model Context Protocol StdioMCPClient implementation."""

import asyncio
import json
import os
import time
import threading
import weakref
from typing import Any, Optional, Dict, List

from pydantic import BaseModel, Field, ConfigDict

from openhands.core.config.mcp_config import MCPStdioServerConfig
from openhands.core.logger import openhands_logger as logger
from openhands.mcp.tool import MCPClientTool
from openhands.mcp.registry import register_mcp_client, unregister_mcp_client


class StdioMCPClient(BaseModel):
    """MCP Client that connects to stdio-based MCP servers via subprocess"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    server_config: MCPStdioServerConfig
    process: Any = None
    description: str = 'Stdio MCP client tools for server interaction'
    tools: List[MCPClientTool] = Field(default_factory=list)
    tool_map: Dict[str, MCPClientTool] = Field(default_factory=dict)
    server_info: str = "unknown"  # Server name for logging

    def __init__(self, server_config: MCPStdioServerConfig, **kwargs):
        super().__init__(server_config=server_config, process=None, **kwargs)
        # Add a field to store a weak reference to the cleanup task
        self._cleanup_task_ref = None
        # Set server info for better logging
        self.server_info = f"stdio:{server_config.name}"
        # Register this client for cleanup tracking
        register_mcp_client(self)

    async def connect_stdio(self, timeout: float = 30.0):
        """Connect to MCP server via stdio subprocess"""
        try:
            # Start the subprocess
            env = dict(os.environ)
            env.update(self.server_config.env)

            cmd = [self.server_config.command] + self.server_config.args
            logger.info(f'Starting stdio MCP server: {" ".join(cmd)}')

            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            # First send initialize request as per MCP protocol
            initialize_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "openhands", "version": "0.48.0"},
                },
            }

            # Send initialize request
            request_data = json.dumps(initialize_request) + '\n'
            self.process.stdin.write(request_data.encode())
            await self.process.stdin.drain()

            # Read initialize response
            response_data = await self.process.stdout.readline()
            if not response_data:
                raise RuntimeError(
                    "No response from stdio MCP server during initialization"
                )

            init_response = json.loads(response_data.decode().strip())

            if 'error' in init_response:
                raise RuntimeError(
                    f"MCP server initialization error: {init_response['error']}"
                )

            # Send initialized notification (required after initialize)
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            }

            notification_data = json.dumps(initialized_notification) + '\n'
            self.process.stdin.write(notification_data.encode())
            await self.process.stdin.drain()

            # Now send tools/list request to get available tools
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            }

            # Send request
            request_data = json.dumps(request) + '\n'
            self.process.stdin.write(request_data.encode())
            await self.process.stdin.drain()

            # Read response
            response_data = await self.process.stdout.readline()
            if not response_data:
                raise RuntimeError("No response from stdio MCP server")

            response = json.loads(response_data.decode().strip())

            if 'error' in response:
                raise RuntimeError(f"MCP server error: {response['error']}")

            if 'result' not in response or 'tools' not in response['result']:
                raise RuntimeError("Invalid response format from MCP server")

            # Create tool objects
            tools = response['result']['tools']
            self.tools = []
            for tool in tools:
                server_tool = MCPClientTool(
                    name=tool['name'],
                    description=tool['description'],
                    inputSchema=tool['inputSchema'],
                )
                self.tool_map[tool['name']] = server_tool
                self.tools.append(server_tool)

            logger.info(
                f'Connected to stdio MCP server "{self.server_config.name}" with tools: {[tool.name for tool in self.tools]}'
            )

        except Exception as e:
            logger.error(
                f'Failed to connect to stdio MCP server "{self.server_config.name}": {e}'
            )
            if self.process:
                self.process.terminate()
                await self.process.wait()
            raise

    async def call_tool_mcp(self, name: str, arguments: dict):
        """Call a tool on the stdio MCP server"""
        if not self.process:
            raise RuntimeError("Not connected to stdio MCP server")

        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
            },
        }

        # Send request
        request_data = json.dumps(request) + '\n'
        self.process.stdin.write(request_data.encode())
        await self.process.stdin.drain()

        # Read response
        response_data = await self.process.stdout.readline()
        if not response_data:
            raise RuntimeError("No response from stdio MCP server")

        response = json.loads(response_data.decode().strip())

        if 'error' in response:
            raise RuntimeError(f"MCP server error: {response['error']}")

        return response['result']

    async def call_tool(self, tool_name: str, args: dict):
        """Call a tool on the stdio MCP server (interface compatibility method)"""
        return await self.call_tool_mcp(tool_name, args)

    def close(self):
        """Close the stdio connection"""
        # Store the process reference before we set it to None
        # This avoids race conditions where the process is cleared during cleanup
        process = self.process

        # Early return if no process to clean up
        if not process:
            # Just ensure we're unregistered
            from openhands.mcp.registry import unregister_mcp_client

            unregister_mcp_client(self)
            return

        # Mark the process as already being cleaned up by setting it to None immediately
        # This prevents other cleanup operations from attempting to clean up this process
        self.process = None

        try:
            logger.debug(f"Closing stdio MCP server: {self.server_config.name}")

            # Try graceful termination first
            try:
                process.terminate()
            except Exception:
                # Process might already be terminated
                pass

            # Use asyncio to wait for termination if we're in an event loop
            try:
                import asyncio

                # Check if we have an active event loop
                loop = None
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No running loop, just wait synchronously
                    pass

                if loop and not loop.is_closed():
                    # If we have an active loop, schedule the wait
                    # Use a function that captures the process by value,
                    # not by reference to self.process (which is now None)
                    async def wait_for_termination(proc):
                        if not proc:
                            return

                        try:
                            if proc.returncode is None:
                                await asyncio.wait_for(proc.wait(), timeout=1.5)
                        except asyncio.TimeoutError:
                            logger.debug(
                                f"Timeout waiting for {self.server_config.name} to terminate, force killing"
                            )
                            try:
                                if proc.returncode is None:
                                    proc.kill()
                                    await proc.wait()
                            except Exception:
                                pass
                        except Exception as e:
                            logger.debug(f"Error waiting for process termination: {e}")

                    # Try to schedule the cleanup, but don't fail if we can't
                    try:
                        # Use a weak reference to avoid keeping the task alive forever
                        # if the event loop is closed
                        import weakref

                        task = loop.create_task(wait_for_termination(process))
                        # Store a weak reference to the task to avoid circular references
                        self._cleanup_task_ref = weakref.ref(task)
                    except Exception:
                        # Fallback to force kill if scheduling fails
                        try:
                            if process.returncode is None:
                                process.kill()
                        except Exception:
                            pass
                else:
                    # No active loop, use sync approach with short timeout
                    import time
                    import threading

                    def force_kill_after_delay(proc):
                        if not proc:
                            return

                        time.sleep(1.0)  # Give 1 second for graceful shutdown
                        try:
                            if proc and proc.returncode is None:
                                proc.kill()
                        except Exception:
                            pass

                    # Start force-kill thread with the captured process
                    threading.Thread(
                        target=force_kill_after_delay, args=(process,), daemon=True
                    ).start()

            except Exception:
                # If anything fails, force kill immediately
                try:
                    if process.returncode is None:
                        process.kill()
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Error during MCP client cleanup: {e}")
        finally:
            # Unregister from cleanup tracking
            unregister_mcp_client(self)
