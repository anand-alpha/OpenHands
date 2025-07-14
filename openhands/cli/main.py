import asyncio
import logging
import os
import sys
import time

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import clear

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
import openhands.cli.suppress_warnings  # noqa: F401
from openhands.cli.commands import (
    check_folder_security_agreement,
    handle_commands,
)
from openhands.cli.settings import modify_llm_settings_basic
from openhands.cli.tui import (
    UsageMetrics,
    display_agent_running_message,
    display_banner,
    display_event,
    display_initial_user_prompt,
    display_initialization_animation,
    display_runtime_initialization_message,
    display_welcome_message,
    read_confirmation_input,
    read_prompt_input,
    start_pause_listener,
    stop_pause_listener,
    update_streaming_output,
)
from openhands.cli.utils import (
    update_usage_metrics,
)
from openhands.controller import AgentController
from openhands.controller.agent import Agent
from openhands.core.config import (
    OpenHandsConfig,
    parse_arguments,
    setup_config_from_args,
)
from openhands.core.config.condenser_config import NoOpCondenserConfig
from openhands.core.config.mcp_config import OpenHandsMCPConfigImpl
from openhands.core.config.utils import finalize_config
from openhands.core.logger import openhands_logger as logger
from openhands.core.loop import run_agent_until_done
from openhands.core.schema import AgentState
from openhands.core.schema.exit_reason import ExitReason
from openhands.core.setup import (
    create_agent,
    create_controller,
    create_memory,
    create_runtime,
    generate_sid,
    initialize_repository_for_runtime,
)
from openhands.events import EventSource, EventStreamSubscriber
from openhands.events.action import (
    ChangeAgentStateAction,
    MessageAction,
)
from openhands.events.event import Event
from openhands.events.observation import (
    AgentStateChangedObservation,
)
from openhands.io import read_task
from openhands.mcp import add_mcp_tools_to_agent
from openhands.mcp.enhanced import enhanced_add_mcp_tools_to_agent
from openhands.memory.condenser.impl.llm_summarizing_condenser import (
    LLMSummarizingCondenserConfig,
)
from openhands.microagent.microagent import BaseMicroagent
from openhands.runtime.base import Runtime
from openhands.storage.settings.file_settings_store import FileSettingsStore


async def cleanup_session(
    loop: asyncio.AbstractEventLoop,
    agent: Agent,
    runtime: Runtime,
    controller: AgentController,
) -> None:
    """Clean up all resources from the current session."""
    event_stream = runtime.event_stream
    end_state = controller.get_state()
    end_state.save_to_session(
        event_stream.sid,
        event_stream.file_store,
        event_stream.user_id,
    )

    try:
        # Clean up MCP connections FIRST if they exist
        # This needs to happen before we cancel other tasks
        if hasattr(agent, 'mcp_tools') and agent.mcp_tools:
            try:
                # Clean up any MCP stdio processes
                logger.debug("Cleaning up MCP connections...")
                from openhands.mcp.utils import cleanup_all_mcp_clients

                await cleanup_all_mcp_clients()
            except Exception as e:
                logger.debug(f"Error during MCP cleanup: {e}")

        current_task = asyncio.current_task(loop)
        pending = [task for task in asyncio.all_tasks(loop) if task is not current_task]

        if pending:
            # Give tasks a short grace period to complete
            done, pending_set = await asyncio.wait(set(pending), timeout=2.0)
            pending = list(pending_set)

        for task in pending:
            if not task.done():
                task.cancel()

        # Wait for the tasks to be properly cancelled
        if pending:
            try:
                # Short timeout to ensure we don't hang during cleanup
                await asyncio.wait_for(
                    asyncio.gather(*pending, return_exceptions=True), timeout=1.0
                )
            except asyncio.TimeoutError:
                # Some tasks didn't finish in time, that's ok for cleanup
                pass
            except Exception:
                # Ignore any errors during final cleanup
                pass

        agent.reset()
        runtime.close()
        await controller.close()

    except Exception as e:
        logger.error(f'Error during session cleanup: {e}')


async def run_session(
    loop: asyncio.AbstractEventLoop,
    config: OpenHandsConfig,
    settings_store: FileSettingsStore,
    current_dir: str,
    task_content: str | None = None,
    conversation_instructions: str | None = None,
    session_name: str | None = None,
    skip_banner: bool = False,
) -> bool:
    reload_microagents = False
    new_session_requested = False
    exit_reason = ExitReason.INTENTIONAL

    sid = generate_sid(config, session_name)
    is_loaded = asyncio.Event()
    is_paused = asyncio.Event()  # Event to track agent pause requests
    always_confirm_mode = False  # Flag to enable always confirm mode

    # Show runtime initialization message
    display_runtime_initialization_message(config.runtime)

    # Show Initialization loader
    loop.run_in_executor(
        None, display_initialization_animation, 'Initializing...', is_loaded
    )

    agent = create_agent(config)
    runtime = create_runtime(
        config,
        sid=sid,
        headless_mode=True,
        agent=agent,
    )
    logger.info("Runtime created successfully")

    def stream_to_console(output: str) -> None:
        # Instead of printing to stdout, pass the string to the TUI module
        update_streaming_output(output)

    runtime.subscribe_to_shell_stream(stream_to_console)

    controller, initial_state = create_controller(agent, runtime, config)

    event_stream = runtime.event_stream

    usage_metrics = UsageMetrics()

    async def prompt_for_next_task(agent_state: str) -> None:
        nonlocal reload_microagents, new_session_requested, exit_reason
        while True:
            next_message = await read_prompt_input(
                config, agent_state, multiline=config.cli_multiline_input
            )

            if not next_message.strip():
                continue

            (
                close_repl,
                reload_microagents,
                new_session_requested,
                exit_reason,
            ) = await handle_commands(
                next_message,
                event_stream,
                usage_metrics,
                sid,
                config,
                current_dir,
                settings_store,
            )

            if close_repl:
                return

    async def on_event_async(event: Event) -> None:
        nonlocal reload_microagents, is_paused, always_confirm_mode
        display_event(event, config)
        update_usage_metrics(event, usage_metrics)

        if isinstance(event, AgentStateChangedObservation):
            if event.agent_state not in [AgentState.RUNNING, AgentState.PAUSED]:
                await stop_pause_listener()

        if isinstance(event, AgentStateChangedObservation):
            if event.agent_state in [
                AgentState.AWAITING_USER_INPUT,
                AgentState.FINISHED,
            ]:
                # If the agent is paused, do not prompt for input as it's already handled by PAUSED state change
                if is_paused.is_set():
                    return

                # Reload microagents after initialization of repo.md
                if reload_microagents:
                    microagents: list[BaseMicroagent] = (
                        runtime.get_microagents_from_selected_repo(None)
                    )
                    memory.load_user_workspace_microagents(microagents)
                    reload_microagents = False
                await prompt_for_next_task(event.agent_state)

            if event.agent_state == AgentState.AWAITING_USER_CONFIRMATION:
                # If the agent is paused, do not prompt for confirmation
                # The confirmation step will re-run after the agent has been resumed
                if is_paused.is_set():
                    return

                if always_confirm_mode:
                    event_stream.add_event(
                        ChangeAgentStateAction(AgentState.USER_CONFIRMED),
                        EventSource.USER,
                    )
                    return

                confirmation_status = await read_confirmation_input(config)
                if confirmation_status == 'yes' or confirmation_status == 'always':
                    event_stream.add_event(
                        ChangeAgentStateAction(AgentState.USER_CONFIRMED),
                        EventSource.USER,
                    )
                else:
                    event_stream.add_event(
                        ChangeAgentStateAction(AgentState.USER_REJECTED),
                        EventSource.USER,
                    )

                # Set the always_confirm_mode flag if the user wants to always confirm
                if confirmation_status == 'always':
                    always_confirm_mode = True

            if event.agent_state == AgentState.PAUSED:
                is_paused.clear()  # Revert the event state before prompting for user input
                await prompt_for_next_task(event.agent_state)

            if event.agent_state == AgentState.RUNNING:
                display_agent_running_message()
                start_pause_listener(loop, is_paused, event_stream)

    def on_event(event: Event) -> None:
        loop.create_task(on_event_async(event))

    event_stream.subscribe(EventStreamSubscriber.MAIN, on_event, sid)

    await runtime.connect()

    # Initialize repository if needed
    repo_directory = None
    if config.sandbox.selected_repo:
        repo_directory = initialize_repository_for_runtime(
            runtime,
            selected_repository=config.sandbox.selected_repo,
        )

    # when memory is created, it will load the microagents from the selected repository
    memory = create_memory(
        runtime=runtime,
        event_stream=event_stream,
        sid=sid,
        selected_repository=config.sandbox.selected_repo,
        repo_directory=repo_directory,
        conversation_instructions=conversation_instructions,
    )

    # Add MCP tools to the agent IMMEDIATELY after memory creation
    # This ensures MCP tools are available from the start of the chat
    # clear()
    if agent.config.enable_mcp:
        logger.info("Initializing MCP tools for chat session...")
        print_formatted_text(HTML('<ansiblue>🔧 Initializing MCP tools...</ansiblue>'))
        logger.info(f"Runtime MCP config: {runtime.config.mcp}")

        try:
            # Add shorter timeout to MCP initialization to prevent hanging
            await asyncio.wait_for(
                enhanced_add_mcp_tools_to_agent(agent, runtime=runtime, memory=memory),
                timeout=45.0,  # Increased from 25 to 45 seconds to accommodate remote servers
            )

            # Log MCP tool availability for debugging
            mcp_tool_count = len(agent.mcp_tools) if agent.mcp_tools else 0
            if mcp_tool_count > 0:
                # agent.mcp_tools can be a dict or a list
                if isinstance(agent.mcp_tools, dict):
                    mcp_tool_names = list(agent.mcp_tools.keys())
                elif isinstance(agent.mcp_tools, list):
                    mcp_tool_names = []
                    for tool in agent.mcp_tools:
                        if hasattr(tool, 'name'):
                            mcp_tool_names.append(tool.name)
                        elif isinstance(tool, dict):
                            # Handle tool dict format: {'type': 'function', 'function': {'name': '...'}}
                            if 'function' in tool and 'name' in tool['function']:
                                mcp_tool_names.append(tool['function']['name'])
                            elif 'name' in tool:
                                mcp_tool_names.append(tool['name'])
                            else:
                                mcp_tool_names.append('unknown_tool')
                        else:
                            mcp_tool_names.append(str(tool))
                else:
                    mcp_tool_names = ["unknown"]

                logger.info(
                    f"✅ MCP configured successfully: {mcp_tool_count} tools available: {mcp_tool_names}"
                )
                print_formatted_text(
                    HTML(
                        f'<ansigreen>✅ MCP tools loaded: {", ".join(mcp_tool_names)}</ansigreen>'
                    )
                )
            else:
                logger.warning("⚠️ MCP enabled but no tools were loaded")
                print_formatted_text(
                    HTML(
                        '<ansiyellow>⚠️ MCP enabled but no tools were loaded</ansiyellow>'
                    )
                )
        except asyncio.TimeoutError:
            logger.warning(
                "⚠️ MCP initialization timed out after 45 seconds - continuing without MCP tools"
            )
            print_formatted_text(
                HTML(
                    '<ansiyellow>⚠️ MCP initialization timed out - continuing without MCP tools</ansiyellow>'
                )
            )
            # Set empty MCP tools to prevent further errors
            agent.mcp_tools = []
        except Exception as e:
            logger.error(
                f"❌ MCP initialization failed: {e} - continuing without MCP tools"
            )
            print_formatted_text(
                HTML(f'<ansired>⚠️ MCP initialization failed: {e}</ansired>')
            )
    else:
        logger.warning("MCP is disabled in agent configuration")

    # Clear loading animation
    is_loaded.set()

    # Clear the terminal
    clear()

    # Show OpenHands banner and session ID if not skipped
    if not skip_banner:
        display_banner(session_id=sid)

    # Customize welcome message to show MCP tools availability
    welcome_message = 'What do you want to build?'
    # if agent.config.enable_mcp and agent.mcp_tools:
    #     # agent.mcp_tools is a dict, so get tool names from the keys
    #     mcp_tool_names = (
    #         list(agent.mcp_tools.keys())
    #         if hasattr(agent.mcp_tools, 'keys')
    #         else [tool["function"]["name"] for tool in agent.mcp_tools.values()]
    #     )
    #     welcome_message += f'\n\n🔧 MCP Tools Available: {", ".join(mcp_tool_names)}'

    initial_message = ''  # from the user

    # if task_content:
    #     initial_message = task_content

    # If we loaded a state, we are resuming a previous session
    # if initial_state is not None:
    #     logger.info(f'Resuming session: {sid}')

    #     if initial_state.last_error:
    #         # If the last session ended in an error, provide a message.
    #         initial_message = (
    #             'NOTE: the last session ended with an error.'
    #             "Let's get back on track. Do NOT resume your task. Ask me about it."
    #         )
    #     else:
    #         # If we are resuming, we already have a task
    #         initial_message = ''
    #         welcome_message += '\nLoading previous conversation.'

    # # Show OpenHands welcome
    display_welcome_message(welcome_message)

    # The prompt_for_next_task will be triggered if the agent enters AWAITING_USER_INPUT.
    # If the restored state is already AWAITING_USER_INPUT, on_event_async will handle it.

    if initial_message:
        display_initial_user_prompt(initial_message)
        event_stream.add_event(MessageAction(content=initial_message), EventSource.USER)
    else:
        # No session restored, no initial action: prompt for the user's first message
        asyncio.create_task(prompt_for_next_task(''))

    await run_agent_until_done(
        controller, runtime, memory, [AgentState.STOPPED, AgentState.ERROR]
    )

    await cleanup_session(loop, agent, runtime, controller)

    if exit_reason == ExitReason.INTENTIONAL:
        print_formatted_text('✅ Session terminated successfully.\n')
    else:
        print_formatted_text(f'⚠️ Session was interrupted: {exit_reason.value}\n')

    return new_session_requested


async def run_setup_flow(config: OpenHandsConfig, settings_store: FileSettingsStore):
    """Run the setup flow to configure initial settings.

    Returns:
        bool: True if settings were successfully configured, False otherwise.
    """
    # Display the banner with ASCII art first
    display_banner(session_id='setup')

    print_formatted_text(
        HTML('<grey>No settings found. Starting initial setup...</grey>\n')
    )

    # Use the existing settings modification function for basic setup
    await modify_llm_settings_basic(config, settings_store)


async def main_with_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Runs the agent in CLI mode."""
    args = parse_arguments()

    # Handle config editor options
    if args.config_edit or args.config_validate:
        try:
            from openhands.cli.config_editor import MCPConfigEditor

            editor = MCPConfigEditor(args.config_file)

            if args.config_validate:
                # Just validate and exit
                is_valid = editor.validate_config()
                exit_code = 0 if is_valid else 1
                import sys

                sys.exit(exit_code)
            else:
                # Run interactive editor
                editor.run()
        except KeyboardInterrupt:
            print_formatted_text(
                HTML('\n<ansiyellow>👋 Configuration editor interrupted</ansiyellow>')
            )
        except Exception as e:
            print_formatted_text(HTML(f'\n<ansired>❌ Error: {e}</ansired>'))
        return

    logger.setLevel(logging.WARNING)

    # Load config from toml and override with command line arguments
    config: OpenHandsConfig = setup_config_from_args(args)

    # Load settings from Settings Store
    # TODO: Make this generic?
    settings_store = await FileSettingsStore.get_instance(config=config, user_id=None)
    settings = await settings_store.load()

    # Track if we've shown the banner during setup
    banner_shown = False

    # If settings don't exist, automatically enter the setup flow
    if not settings:
        # Clear the terminal before showing the banner
        clear()

        await run_setup_flow(config, settings_store)
        banner_shown = True

        settings = await settings_store.load()

    # Use settings from settings store if available and override with command line arguments
    if settings:
        if args.agent_cls:
            config.default_agent = str(args.agent_cls)
        else:
            # settings.agent is not None because we check for it in setup_config_from_args
            assert settings.agent is not None
            config.default_agent = settings.agent
        if not args.llm_config and settings.llm_model and settings.llm_api_key:
            llm_config = config.get_llm_config()
            llm_config.model = settings.llm_model
            llm_config.api_key = settings.llm_api_key
            llm_config.base_url = settings.llm_base_url
            config.set_llm_config(llm_config)
        config.security.confirmation_mode = (
            settings.confirmation_mode if settings.confirmation_mode else False
        )

        if settings.enable_default_condenser:
            # TODO: Make this generic?
            llm_config = config.get_llm_config()
            agent_config = config.get_agent_config(config.default_agent)
            agent_config.condenser = LLMSummarizingCondenserConfig(
                llm_config=llm_config,
                type='llm',
            )
            config.set_agent_config(agent_config)
            config.enable_default_condenser = True
        else:
            agent_config = config.get_agent_config(config.default_agent)
            agent_config.condenser = NoOpCondenserConfig(type='noop')
            config.set_agent_config(agent_config)
            config.enable_default_condenser = False

    # Determine if CLI defaults should be overridden
    val_override = args.override_cli_mode
    should_override_cli_defaults = (
        val_override is True
        or (isinstance(val_override, str) and val_override.lower() in ('true', '1'))
        or (isinstance(val_override, int) and val_override == 1)
    )

    if not should_override_cli_defaults:
        config.runtime = 'cli'
        if not config.workspace_base:
            config.workspace_base = os.getcwd()
        config.security.confirmation_mode = True

        # Need to finalize config again after setting runtime to 'cli'
        # This ensures Jupyter plugin is disabled for CLI runtime
        finalize_config(config)

    # TODO: Set working directory from config or use current working directory?
    current_dir = config.workspace_base

    if not current_dir:
        raise ValueError('Workspace base directory not specified')

    if not check_folder_security_agreement(config, current_dir):
        # User rejected, exit application
        return

    # Read task from file, CLI args, or stdin
    if args.file:
        # For CLI usage, we want to enhance the file content with a prompt
        # that instructs the agent to read and understand the file first
        with open(args.file, 'r', encoding='utf-8') as file:
            file_content = file.read()

        # Create a prompt that instructs the agent to read and understand the file first
        task_str = f"""The user has tagged a file '{args.file}'.
Please read and understand the following file content first:

```
{file_content}
```

After reviewing the file, please ask the user what they would like to do with it."""
    else:
        task_str = read_task(args, config.cli_multiline_input)

    # Run the first session
    new_session_requested = await run_session(
        loop,
        config,
        settings_store,
        current_dir,
        task_str,
        session_name=args.name,
        skip_banner=banner_shown,
    )

    # If a new session was requested, run it
    while new_session_requested:
        new_session_requested = await run_session(
            loop, config, settings_store, current_dir, None
        )


def main():
    # Patch BaseSubprocessTransport.__del__ to prevent "RuntimeError: Event loop is closed"
    try:
        import asyncio.base_subprocess

        # Save original __del__ method
        original_del = asyncio.base_subprocess.BaseSubprocessTransport.__del__

        # Define a safe __del__ method that doesn't use the event loop
        def safe_del(self):
            if not hasattr(self, '_proc') or self._proc is None:
                return
            try:
                self._proc.kill()
            except ProcessLookupError:
                pass
            except OSError:
                pass
            self._proc = None

        # Replace the __del__ method
        asyncio.base_subprocess.BaseSubprocessTransport.__del__ = safe_del
        logger.debug(
            "Patched BaseSubprocessTransport.__del__ to avoid 'Event loop is closed' errors"
        )
    except Exception as e:
        logger.debug(f"Could not patch BaseSubprocessTransport.__del__: {e}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Flag to track if we're shutting down
    shutting_down = False

    # Improved signal handling for graceful shutdown
    def signal_handler():
        nonlocal shutting_down
        if shutting_down:
            # Second interrupt - force exit
            print_formatted_text('\n⚠️ Forceful shutdown initiated...')
            import os

            os._exit(1)

        shutting_down = True
        print_formatted_text(
            '\n⚠️ Received interrupt signal. Shutting down gracefully...'
        )

        # Cancel all running tasks
        for task in asyncio.all_tasks(loop):
            if not task.done():
                task.cancel()

    try:
        # Set up signal handlers for graceful shutdown
        import signal

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except (NotImplementedError, RuntimeError):
                # Windows doesn't support signal handlers in event loops
                pass

        loop.run_until_complete(main_with_loop(loop))
    except KeyboardInterrupt:
        print_formatted_text('\n⚠️ Chat session interrupted. Goodbye!')
    except ConnectionRefusedError as e:
        print_formatted_text(f'\n❌ Connection refused: {e}')
        sys.exit(1)
    except Exception as e:
        print_formatted_text(f'\n❌ An error occurred: {e}')
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            # Clean up MCP clients first, before event loop cleanup
            try:
                from openhands.mcp.utils import (
                    cleanup_all_mcp_clients,
                    get_active_mcp_clients_count,
                )
                import asyncio  # Make sure asyncio is imported in this scope

                # Only attempt cleanup if there are active MCP clients
                if not loop.is_closed() and get_active_mcp_clients_count() > 0:
                    # Run synchronously with a short timeout to ensure it completes
                    try:
                        # First try to close any stdioprocess (synchronously)
                        print_formatted_text('Cleaning up MCP resources...')
                        cleanup_task = asyncio.ensure_future(
                            cleanup_all_mcp_clients(force_kill=True), loop=loop
                        )
                        loop.run_until_complete(
                            asyncio.wait_for(cleanup_task, timeout=2.0)
                        )
                    except asyncio.TimeoutError:
                        print_formatted_text(
                            'Warning: MCP cleanup timed out - some processes may remain'
                        )
                    except Exception as e:
                        print_formatted_text(f'Warning: MCP cleanup error: {e}')
            except Exception as e:
                print_formatted_text(f'Warning: MCP cleanup import error: {e}')

            # Manually terminate any remaining subprocess (using os.kill if needed)
            # This helps prevent "Event loop is closed" errors during __del__ methods
            try:
                import os
                import signal
                import psutil

                current_process = psutil.Process()
                # Check for any child processes that might be MCP related
                for child in current_process.children(recursive=False):
                    try:
                        # Skip very short-lived processes (they're probably already exiting)
                        if (time.time() - child.create_time()) < 2:
                            continue

                        print_formatted_text(f'Terminating child process: {child.pid}')
                        child.terminate()  # Send SIGTERM

                        # Give it a moment to terminate gracefully
                        try:
                            child.wait(timeout=0.5)
                        except psutil.TimeoutExpired:
                            # If it didn't terminate, force kill it
                            print_formatted_text(f'Force killing process: {child.pid}')
                            child.kill()  # Send SIGKILL
                    except psutil.NoSuchProcess:
                        pass  # Process already gone
                    except Exception as e:
                        print_formatted_text(
                            f'Warning: Error terminating process {child.pid}: {e}'
                        )
            except ImportError:
                # psutil might not be available
                print_formatted_text(
                    'Warning: psutil not available for advanced process cleanup'
                )
            except Exception as e:
                print_formatted_text(f'Warning: Error during process cleanup: {e}')

            # Small delay before continuing with loop cleanup
            time.sleep(
                0.2
            )  # Use time.sleep instead of asyncio.sleep to avoid loop issues

            # Graceful cleanup with timeout
            if not loop.is_closed():
                pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
                if pending:
                    # Cancel all pending tasks
                    for task in pending:
                        if not task.done():
                            task.cancel()

                    # Wait for cancellation with timeout
                    try:
                        loop.run_until_complete(
                            asyncio.wait_for(
                                asyncio.gather(*pending, return_exceptions=True),
                                timeout=1.0,  # Shorter timeout to avoid hanging
                            )
                        )
                    except (asyncio.TimeoutError, asyncio.CancelledError, RuntimeError):
                        pass  # Some tasks didn't finish in time, that's ok
                    except Exception:
                        pass  # Ignore cleanup errors

                try:
                    # First run GC to clean up any references that could trigger __del__ with loop calls
                    import gc

                    gc.collect()

                    # Make sure we're not holding references to any transports
                    for obj in gc.get_objects():
                        if hasattr(obj, "_loop") and hasattr(obj, "close"):
                            try:
                                if not hasattr(obj, "_closed") or not obj._closed:
                                    obj.close()
                            except Exception:
                                pass
                except Exception:
                    pass

                # Finally close the loop
                loop.close()

                # Suppress the RuntimeError warnings from BaseSubprocessTransport.__del__
                # by patching the low-level asyncio implementation before exit
                try:
                    # Create a safer __del__ that doesn't try to use the loop
                    def safe_del(self):
                        try:
                            if hasattr(self, "_proc") and self._proc:
                                try:
                                    self._proc.kill()
                                except Exception:
                                    pass
                                self._proc = None
                        except Exception:
                            pass

                    # If possible, patch BaseSubprocessTransport.__del__ with our safe version
                    import sys

                    if 'asyncio.base_subprocess' in sys.modules:
                        sys.modules[
                            'asyncio.base_subprocess'
                        ].BaseSubprocessTransport.__del__ = safe_del
                except Exception:
                    pass
        except Exception as e:
            # Ignore cleanup errors but log them for debugging
            print_formatted_text(f'Warning: Final cleanup error: {e}')


if __name__ == '__main__':
    main()
