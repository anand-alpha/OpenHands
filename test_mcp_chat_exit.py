#!/usr/bin/env python3

"""
Test script to run a basic chat with MCP and verify clean exit
This will launch the chat and terminate it after a few seconds
"""

import subprocess
import time
import signal
import sys
import os
import re


def test_mcp_chat_exit():
    print("Starting snow --chat with MCP and testing exit behavior...")

    # Start the snow command in chat mode
    process = subprocess.Popen(
        ["poetry", "run", "snow", "--chat"],
        cwd="/home/hac/code/OpenHands",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # Line buffered
    )

    output_lines = []

    def read_output():
        """Read any available output from the process"""
        while True:
            line = process.stdout.readline()
            if not line:
                break
            line = line.rstrip()
            if line:
                print(f">> {line}")
                output_lines.append(line)

    try:
        print("Waiting 15 seconds for chat to initialize...")

        # Wait for initialization
        for i in range(15):
            time.sleep(1)
            print(".", end="", flush=True)
            read_output()  # Read any available output

            # If we see MCP tools loaded in the output, we can exit early
            if any("MCP tools loaded" in line for line in output_lines):
                print("\nMCP tools detected, ready to test exit!")
                break

        print("\nSending Ctrl+C to terminate chat...")
        process.send_signal(signal.SIGINT)

        # Wait for graceful shutdown
        print("Waiting for process to exit...")
        exit_timeout = 10  # 10 seconds timeout

        # Poll until the process exits or timeout
        start_time = time.time()
        while process.poll() is None and (time.time() - start_time) < exit_timeout:
            time.sleep(0.1)
            read_output()  # Continue reading output

        # Check if process exited
        if process.poll() is None:
            print("❌ Process didn't terminate within timeout, force killing")
            process.kill()
            process.wait()
            return False

        # Read any remaining output
        remaining_output = process.stdout.read()
        if remaining_output:
            print(f"Remaining output: {remaining_output}")
            output_lines.extend(remaining_output.splitlines())

        print(f"Process exited with code: {process.returncode}")

        # Join all output lines to search for errors
        full_output = "\n".join(output_lines)

        # Check for common asyncio/subprocess error patterns
        error_patterns = [
            r"RuntimeError: Event loop is closed",
            r"Task exception was never retrieved",
            r"'NoneType' object has no attribute 'wait'",
            r"Exception ignored in:.+asyncio",
            r"Exception in thread.+asyncio",
            r"Task was destroyed but it is pending",
            r"Exception ignored.+Popen",
            r"ResourceWarning: unclosed",
        ]

        found_errors = []
        for pattern in error_patterns:
            matches = re.findall(pattern, full_output)
            if matches:
                found_errors.append(f"Found {len(matches)} matches for: {pattern}")

        if found_errors:
            print("❌ Detected the following issues:")
            for error in found_errors:
                print(f"  - {error}")
            return False
        else:
            print("✅ No subprocess cleanup errors detected in output!")
            return True

    except Exception as e:
        print(f"❌ Error during test: {e}")
        if process.poll() is None:
            process.kill()
            process.wait()
        return False


if __name__ == "__main__":
    success = test_mcp_chat_exit()
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")
    sys.exit(0 if success else 1)
