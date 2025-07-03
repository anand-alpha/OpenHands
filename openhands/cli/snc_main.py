#!/usr/bin/env python3
"""
Snowcell CLI - Company Authentication and Chat Interface
This is the main CLI for Snowcell company's AI assistant.
"""

import sys
import argparse
from typing import NoReturn
import asyncio

from prompt_toolkit import print_formatted_text, PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import clear

from openhands.cli.commands import (
    handle_snc_login_command,
    handle_snc_logout_command,
    handle_snc_status_command,
)
from openhands.cli.utils import verify_snc_token


def display_snc_banner() -> None:
    """Display the Snowcell company banner."""
    print_formatted_text(
        HTML(
            r"""<gold>
███████ ███    ██  ██████  ██     ██  ██████ ███████ ██      ██
██      ████   ██ ██    ██ ██     ██ ██      ██      ██      ██
███████ ██ ██  ██ ██    ██ ██  █  ██ ██      █████   ██      ██
     ██ ██  ██ ██ ██    ██ ██ ███ ██ ██      ██      ██      ██
███████ ██   ████  ██████   ███ ███   ██████ ███████ ███████ ███████

    Snowcell AI Assistant
    </gold>"""
        )
    )
    print_formatted_text('')
    print_formatted_text(
        HTML('<grey>Welcome to Snowcell\'s AI-powered assistant</grey>')
    )
    print_formatted_text('')


def display_snc_help() -> None:
    """Display Snowcell help information."""
    print_formatted_text(HTML('<gold>Snowcell AI Assistant Commands:</gold>'))
    print_formatted_text('')
    print_formatted_text(
        HTML(
            '• <gold><b>snc --token &lt;token&gt;</b></gold> - Login and start chat with AI assistant'
        )
    )
    print_formatted_text(
        HTML('• <gold><b>snc --status</b></gold> - Check your authentication status')
    )
    print_formatted_text(
        HTML('• <gold><b>snc --chat</b></gold> - Start chat session (if authenticated)')
    )
    print_formatted_text(
        HTML('• <gold><b>snc --logout</b></gold> - Logout and end session')
    )
    print_formatted_text('')
    print_formatted_text(
        HTML(
            '<grey>After authentication, you will automatically enter the chat interface.</grey>'
        )
    )
    print_formatted_text('')


def parse_snc_arguments() -> argparse.Namespace:
    """Parse Snowcell command line arguments."""
    parser = argparse.ArgumentParser(
        description='Snowcell Authentication CLI for OpenHands AI Assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Disable default help to handle it ourselves
        epilog='''
Examples:
  snc --token abc123xyz789       Login with token and start chat
  snc --status                   Check authentication status
  snc --chat                     Start chat session (if authenticated)
  snc --logout                   Logout
        ''',
    )

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--token',
        type=str,
        help='Login with Snowcell authentication token and start chat',
    )
    group.add_argument(
        '--status', action='store_true', help='Check authentication status'
    )
    group.add_argument(
        '--logout', action='store_true', help='Logout and clear authentication'
    )
    group.add_argument(
        '--chat',
        action='store_true',
        help='Start chat session (requires authentication)',
    )

    return parser.parse_args()


def launch_openhands() -> NoReturn:
    """Launch the OpenHands AI Assistant chat interface after authentication."""
    print_formatted_text('')
    print_formatted_text(HTML('<gold>🚀 Launching Snowcell AI Assistant...</gold>'))
    print_formatted_text('')

    # Clear command line arguments to prevent conflicts
    import sys

    original_argv = sys.argv.copy()
    sys.argv = ['openhands']  # Reset to just the program name

    # Import and run the main OpenHands CLI
    try:
        from openhands.cli.main import main

        main()
    finally:
        # Restore original argv in case of any issues
        sys.argv = original_argv

    sys.exit(0)


def snc_main() -> None:
    """Main entry point for Snowcell authentication CLI."""
    args = parse_snc_arguments()

    # Clear terminal and show banner
    clear()
    display_snc_banner()

    # If no arguments provided, show help
    if not any([args.token, args.status, args.logout, args.chat]):
        display_snc_help()
        return

    # Handle commands
    if args.token:
        print_formatted_text(HTML(f'<grey>Authenticating with Snowcell...</grey>'))
        print_formatted_text('')
        handle_snc_login_command(args.token)

        # After successful login, automatically start chat
        if verify_snc_token():
            print_formatted_text('')
            print_formatted_text(
                HTML('<gold>🎉 Welcome to Snowcell AI Assistant!</gold>')
            )
            print_formatted_text(HTML('<grey>Starting chat interface...</grey>'))
            print_formatted_text('')
            launch_openhands()

    elif args.status:
        handle_snc_status_command()

        # If authenticated, offer to start chat
        if verify_snc_token():
            print_formatted_text(
                HTML(
                    '<grey>Ready to chat! Use <gold>snc --chat</gold> to start the AI assistant.</grey>'
                )
            )
            print_formatted_text('')

    elif args.chat:
        # Check authentication before starting chat
        if verify_snc_token():
            print_formatted_text('')
            print_formatted_text(
                HTML('<gold>🎉 Welcome to Snowcell AI Assistant!</gold>')
            )
            print_formatted_text(HTML('<grey>Starting chat interface...</grey>'))
            print_formatted_text('')
            launch_openhands()
        else:
            print_formatted_text('')
            print_formatted_text(
                HTML('<ansired>⚠ Authentication required to start chat</ansired>')
            )
            print_formatted_text(
                HTML(
                    '<grey>Please login first: <gold>snc --token &lt;your-token&gt;</gold></grey>'
                )
            )
            print_formatted_text('')

    elif args.logout:
        handle_snc_logout_command()


def openhands_main() -> None:
    """Entry point for the OpenHands AI Assistant (after authentication check)."""
    # Check if user is authenticated
    if not verify_snc_token():
        clear()
        display_snc_banner()
        print_formatted_text('')
        print_formatted_text(
            HTML('<ansired>⚠ Snowcell authentication required</ansired>')
        )
        print_formatted_text(
            HTML(
                '<grey>Please authenticate first: <gold>snc --token &lt;your-token&gt;</gold></grey>'
            )
        )
        print_formatted_text(
            HTML(
                '<grey>Or start a chat session: <gold>snc --chat</gold> (after login)</grey>'
            )
        )
        print_formatted_text('')
        sys.exit(1)

    # User is authenticated, show welcome and proceed with OpenHands CLI
    print_formatted_text('')
    print_formatted_text(HTML('<gold>🎉 Welcome back to Snowcell AI Assistant!</gold>'))
    print_formatted_text('')

    # Clear command line arguments to prevent conflicts
    original_argv = sys.argv.copy()
    sys.argv = ['openhands']  # Reset to just the program name

    try:
        from openhands.cli.main import main

        main()
    finally:
        # Restore original argv in case of any issues
        sys.argv = original_argv


if __name__ == '__main__':
    snc_main()
