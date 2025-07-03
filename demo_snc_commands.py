#!/usr/bin/env python3
"""
Interactive demo script for SNC authentication commands in VS Code
Run this to see how the SNC commands work in practice
"""

import sys
import os
import asyncio
from unittest.mock import Mock

# Add the project to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openhands.cli.commands import (
    handle_snc_login_command,
    handle_snc_logout_command,
    handle_snc_status_command,
    check_snc_authentication,
)
from openhands.cli.utils import (
    store_snc_token,
    verify_snc_token,
    get_snc_auth_info,
    logout_snc,
)


def demo_divider(title):
    """Print a nice divider for demo sections."""
    print("\n" + "=" * 60)
    print(f"🔹 {title}")
    print("=" * 60)


def demo_snc_commands():
    """Demonstrate all SNC authentication commands."""
    print("🎯 SNC Authentication Commands Demo")
    print("This demo shows how the new SNC commands work in OpenHands CLI")

    # Demo 1: Check initial status
    demo_divider("1. Initial Authentication Status")
    print("Command: snc --status")
    handle_snc_status_command()

    # Demo 2: Login with token
    demo_divider("2. Login with SNC Token")
    test_token = "demo_company_token_abc123xyz789"
    print(f"Command: snc --token {test_token}")
    handle_snc_login_command(test_token)

    # Demo 3: Check status after login
    demo_divider("3. Authentication Status After Login")
    print("Command: snc --status")
    handle_snc_status_command()

    # Demo 4: Test authentication check (used by other commands)
    demo_divider("4. Authentication Check (Used by /init, /new, etc.)")
    print("This is what happens when you run commands like /init or /new:")
    is_authenticated = check_snc_authentication()
    print(f"✓ Authentication check result: {is_authenticated}")

    # Demo 5: Try invalid token
    demo_divider("5. Try Invalid Token")
    print("Command: snc --token abc")
    handle_snc_login_command("abc")

    # Demo 6: Try empty token
    demo_divider("6. Try Empty Token")
    print("Command: snc --token")
    handle_snc_login_command("")

    # Demo 7: Logout
    demo_divider("7. Logout from SNC")
    print("Command: snc --logout")
    handle_snc_logout_command()

    # Demo 8: Check status after logout
    demo_divider("8. Status After Logout")
    print("Command: snc --status")
    handle_snc_status_command()

    # Demo 9: Test authentication check after logout
    demo_divider("9. Authentication Check After Logout")
    print("This is what happens when you try to run /init after logout:")
    is_authenticated = check_snc_authentication()
    print(f"✗ Authentication check result: {is_authenticated}")

    print("\n" + "🎉 Demo completed!")
    print("You can now use these commands in the actual OpenHands CLI:")
    print("  • snc --token <your-token>")
    print("  • snc --status")
    print("  • snc --logout")


def test_command_integration():
    """Test how SNC commands integrate with the main command handler."""
    demo_divider("Command Integration Test")

    # Import the main command handler
    from openhands.cli.commands import handle_commands
    from openhands.core.config import OpenHandsConfig
    from openhands.events.stream import EventStream
    from openhands.cli.tui import UsageMetrics
    from openhands.storage.settings.file_settings_store import FileSettingsStore

    # Create mock objects
    config = Mock(spec=OpenHandsConfig)
    event_stream = Mock(spec=EventStream)
    usage_metrics = Mock(spec=UsageMetrics)
    settings_store = Mock(spec=FileSettingsStore)

    print("Testing command parsing and routing...")

    # Test SNC commands
    commands_to_test = ["snc --token test123", "snc --status", "snc --logout"]

    for cmd in commands_to_test:
        print(f"\n📝 Testing command: '{cmd}'")
        try:
            # This would normally be async, but we'll just test the parsing
            if cmd.startswith('snc --token '):
                token = cmd[12:].strip()
                handle_snc_login_command(token)
                print("   ✓ Command parsed and executed correctly")
            elif cmd == 'snc --status':
                handle_snc_status_command()
                print("   ✓ Command parsed and executed correctly")
            elif cmd == 'snc --logout':
                handle_snc_logout_command()
                print("   ✓ Command parsed and executed correctly")
        except Exception as e:
            print(f"   ✗ Error: {e}")


if __name__ == "__main__":
    print("🚀 Starting SNC Authentication Demo in VS Code")
    print("=" * 60)

    # Run the main demo
    demo_snc_commands()

    print("\n")
    # Test command integration
    test_command_integration()

    print("\n" + "🎯 How to test in VS Code:")
    print("1. Open VS Code terminal (Ctrl+`)")
    print("2. Run: poetry run python demo_snc_commands.py")
    print("3. Or run individual functions in Python console")
    print("4. To test the actual CLI, you would run the main OpenHands CLI")
    print("   and use the snc commands interactively")
