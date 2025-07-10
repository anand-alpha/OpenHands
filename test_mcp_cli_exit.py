#!/usr/bin/env python
"""
Test script to verify that the Snow CLI properly initializes and cleans up MCP clients.
"""

import atexit
import os
import signal
import subprocess
import sys
import time

from openhands.mcp import get_active_mcp_clients_count, cleanup_all_mcp_clients
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


def main():
    logger.info("Starting Snow CLI test")

    # Start the CLI process
    process = subprocess.Popen(
        ["poetry", "run", "snow", "--chat"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Give it some time to initialize
    time.sleep(2)

    # Check active clients count
    client_count = get_active_mcp_clients_count()
    logger.info(f"Active MCP clients after CLI start: {client_count}")

    # Send SIGINT to the process to simulate Ctrl+C
    process.send_signal(signal.SIGINT)

    # Give it some time to clean up
    time.sleep(1)

    # Check active clients count again
    client_count = get_active_mcp_clients_count()
    logger.info(f"Active MCP clients after CLI shutdown: {client_count}")

    # Make sure process is terminated
    try:
        process.terminate()
        process.wait(timeout=1)
    except:
        process.kill()

    logger.info("Snow CLI test complete")


if __name__ == "__main__":
    main()
