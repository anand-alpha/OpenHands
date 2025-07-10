#!/usr/bin/env python3

"""
Simplified test script to verify subprocess cleanup.
This script launches a subprocess and tests proper cleanup.
"""

import asyncio
import subprocess
import os
import sys
import time


async def run_process():
    """Run a simple process and ensure it's properly cleaned up"""
    print("Starting subprocess...")

    # Start a simple subprocess that just sleeps
    process = await asyncio.create_subprocess_exec(
        "sleep",
        "10",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    print(f"Process started with PID: {process.pid}")

    # Wait a moment
    await asyncio.sleep(1)

    print("Terminating process...")
    process.terminate()

    # Store the process in a variable to prevent premature GC
    proc_ref = process

    # Set process to None to simulate the condition in our actual code
    process = None

    print("Process variable set to None")

    # Create a task to wait for termination
    async def wait_for_termination(proc):
        if proc and proc.returncode is None:
            try:
                await asyncio.wait_for(proc.wait(), timeout=1.0)
                print("Process terminated gracefully")
            except asyncio.TimeoutError:
                print("Process termination timed out, force killing")
                if proc.returncode is None:
                    proc.kill()
                    await proc.wait()
            except Exception as e:
                print(f"Error waiting for process: {e}")

    # Run the termination task
    try:
        await wait_for_termination(proc_ref)
    except Exception as e:
        print(f"Termination error: {e}")

    # Wait a moment before cleanup
    await asyncio.sleep(0.5)

    print("Test completed")


async def main():
    """Run the test"""
    try:
        await run_process()
    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        print("\nVerification complete. No asyncio warnings should appear after this.")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main())
    finally:
        # Additional cleanup to prevent warnings
        pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
        if pending:
            print(f"Cancelling {len(pending)} pending tasks...")
            for task in pending:
                task.cancel()

            try:
                loop.run_until_complete(
                    asyncio.wait_for(
                        asyncio.gather(*pending, return_exceptions=True), timeout=1.0
                    )
                )
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass

        # Short sleep before closing loop
        try:
            loop.run_until_complete(asyncio.sleep(0.1))
        except:
            pass

        # Close the loop
        loop.close()

        print("Test script completed.")
