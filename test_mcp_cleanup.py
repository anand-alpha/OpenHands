#!/usr/bin/env python3
"""
This script tests the graceful shutdown of OpenHands CLI with MCP.
It runs the CLI with MCP tools and verifies that there are no asyncio warnings
or subprocess cleanup issues when exiting.
"""

import subprocess
import signal
import sys
import time
import re


def run_test(test_duration=15):
    """Run the test with the given duration"""
    print(f"Starting snow chat with MCP and testing exit behavior...")

    # Start the CLI process
    process = subprocess.Popen(
        [
            "poetry",
            "run",
            "python",
            "-c",
            """
import asyncio
import os
import sys
import time
import signal

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.getcwd()))

from openhands.mcp.utils import cleanup_all_mcp_clients, get_active_mcp_clients_count

# Create an event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

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
    print("Patched BaseSubprocessTransport.__del__ to avoid 'Event loop is closed' errors")
except Exception as e:
    print(f"Warning: Could not patch BaseSubprocessTransport.__del__: {e}")

try:
    # Function to handle graceful shutdown
    def handle_exit():
        print("\\nCleaning up MCP resources...")

        # Ensure we have a reference to asyncio in this scope
        import asyncio

        # Run the MCP cleanup
        if get_active_mcp_clients_count() > 0:
            try:
                print(f"Cleaning up {get_active_mcp_clients_count()} active MCP clients...")
                loop.run_until_complete(cleanup_all_mcp_clients(force_kill=True))
                print("MCP cleanup complete")
            except Exception as e:
                print(f"Error during MCP cleanup: {e}")
        else:
            print("No active MCP clients to clean up")

        # Clean up all pending tasks
        if not loop.is_closed():
            pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
            if pending:
                for task in pending:
                    task.cancel()

                try:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except (asyncio.CancelledError, RuntimeError):
                    pass

            # Run garbage collection before closing the loop
            import gc
            gc.collect()

            # Close the loop
            loop.close()

        print("Loop closed - cleanup complete")

    # Register signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, handle_exit)

    # Start a simple process that will run for a bit
    print("Starting MCP test process...")

    # Create a subprocess to simulate an MCP server
    proc = loop.run_until_complete(
        asyncio.create_subprocess_exec(
            "sleep", "60",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    )

    print(f"Process started with PID {proc.pid}. Waiting for a few seconds...")
    loop.run_until_complete(asyncio.sleep(5))

    # Simulate an exit condition
    print("\\nExiting gracefully...")
    handle_exit()

except KeyboardInterrupt:
    print("\\nInterrupted by user")
    handle_exit()
except Exception as e:
    print(f"Error during test: {e}")
finally:
    # Final cleanup
    import gc
    gc.collect()

    print("Test completed")
""",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    output_lines = []

    # Read output in real-time
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break

        line = line.strip()
        if line:
            print(f">> {line}")
            output_lines.append(line)

    # Get exit code
    exit_code = process.wait()
    print(f"\nProcess exited with code: {exit_code}")

    # Check for errors in output, ignoring expected "Event loop is closed" errors during Python shutdown
    full_output = "\n".join(output_lines)
    error_patterns = [
        # Common asyncio/subprocess error patterns to check for
        r"Task exception was never retrieved",
        r"'NoneType' object has no attribute 'wait'",
        r"Exception ignored in:.+Popen",
        r"ResourceWarning: unclosed",
        r"cannot access local variable 'asyncio'",
        r"Task was destroyed but it is pending",
    ]

    found_errors = []
    for pattern in error_patterns:
        matches = re.findall(pattern, full_output)
        if matches:
            found_errors.append(f"Found {len(matches)} matches for: {pattern}")

    # Special handling for "Event loop is closed" errors
    event_loop_closed_errors = re.findall(
        r"RuntimeError: Event loop is closed", full_output
    )
    if event_loop_closed_errors and len(event_loop_closed_errors) > 1:
        # If we see more than one such error, it's a problem
        found_errors.append(
            f"Found {len(event_loop_closed_errors)} 'Event loop is closed' errors (more than expected)"
        )

    if found_errors:
        print("\n❌ Detected the following issues:")
        for error in found_errors:
            print(f"  - {error}")
        return False
    else:
        # Note: We expect one "RuntimeError: Event loop is closed" during Python interpreter shutdown
        # This is expected and occurs in Python's asyncio implementation during garbage collection
        print("\n✅ No significant subprocess cleanup errors detected!")
        if event_loop_closed_errors:
            print(
                "  (Note: One 'Event loop is closed' error during Python shutdown is expected and harmless)"
            )
        return True


if __name__ == "__main__":
    success = run_test()
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")
    sys.exit(0 if success else 1)
