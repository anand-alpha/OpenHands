#!/usr/bin/env python3
"""
Snowcode AI Assistant CLI
A company-specific AI assistant that uses OpenHands backend with Snowcode branding.
"""

import sys
import argparse
import asyncio
from typing import NoReturn, Optional

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import clear

from openhands.cli.utils import (
    store_snc_token,
    verify_snc_token,
    get_snc_auth_info,
    logout_snc,
    validate_snc_token,
)


def display_snowcode_banner() -> None:
    """Display the Snowcode company banner."""
    print_formatted_text(
        HTML(
            r"""<gold>
     ____                                   _
    / ___| _ __   _____      _____ ___   __| | ___
    \___ \| '_ \ / _ \ \ /\ / / __/ _ \ / _` |/ _ \
     ___) | | | | (_) \ V  V / (_| (_) | (_| |  __/
    |____/|_| |_|\___/ \_/\_/ \___\___/ \__,_|\___|

    Snowcode AI Assistant
    </gold>"""
        )
    )
    print_formatted_text('')
    print_formatted_text(HTML('<grey>Your intelligent AI-powered assistant</grey>'))
    print_formatted_text('')


def display_snowcode_help() -> None:
    """Display Snowcode help information."""
    print_formatted_text(HTML('<gold>Snowcode AI Assistant Commands:</gold>'))
    print_formatted_text('')
    print_formatted_text(
        HTML(
            '• <gold><b>snc --token &lt;token&gt;</b></gold> - Login and start AI assistant'
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


def display_login_success() -> None:
    """Display successful login message."""
    print_formatted_text('')
    print_formatted_text(
        HTML('<ansigreen>✓ Successfully authenticated with Snowcode!</ansigreen>')
    )
    print_formatted_text('')


def display_login_error() -> None:
    """Display login error message."""
    print_formatted_text('')
    print_formatted_text(HTML('<ansired>✗ Authentication failed</ansired>'))
    print_formatted_text(HTML('<grey>Please check your token and try again</grey>'))
    print_formatted_text('')


def display_logout_success() -> None:
    """Display successful logout message."""
    print_formatted_text('')
    print_formatted_text(
        HTML('<ansigreen>✓ Successfully logged out from Snowcode</ansigreen>')
    )
    print_formatted_text(
        HTML('<grey>Thank you for using Snowcode AI Assistant!</grey>')
    )
    print_formatted_text('')


def display_status(auth_info: dict) -> None:
    """Display authentication status."""
    print_formatted_text('')
    print_formatted_text(HTML('<gold>Snowcode Authentication Status:</gold>'))
    print_formatted_text('')

    if auth_info['authenticated']:
        print_formatted_text(HTML('<ansigreen>Status: Authenticated ✓</ansigreen>'))
        expires_in = auth_info.get('expires_in', 0)
        hours = int(expires_in // 3600)
        minutes = int((expires_in % 3600) // 60)
        print_formatted_text(HTML(f'<grey>Time remaining: {hours}h {minutes}m</grey>'))
    else:
        print_formatted_text(HTML('<ansired>Status: Not authenticated ✗</ansired>'))
        if auth_info.get('reason'):
            print_formatted_text(HTML(f'<grey>Reason: {auth_info["reason"]}</grey>'))
    print_formatted_text('')


def launch_openhands_chat() -> NoReturn:
    """Launch the actual OpenHands AI assistant chat interface."""
    # Set environment variable to indicate Snowcode branding
    import os

    os.environ['SNOWCODE_BRANDING'] = 'true'

    # Clear command line arguments to prevent conflicts
    original_argv = sys.argv.copy()
    sys.argv = ['openhands']  # Reset to just the program name

    # Import and run the main OpenHands CLI
    try:
        from openhands.cli.main import main

        main()
    finally:
        # Restore original argv in case of any issues
        sys.argv = original_argv
        # Clean up environment variable
        if 'SNOWCODE_BRANDING' in os.environ:
            del os.environ['SNOWCODE_BRANDING']

    sys.exit(0)


def handle_login_command(token: str) -> bool:
    """Handle login command and return success status."""
    if not token:
        print_formatted_text('')
        print_formatted_text(HTML('<ansired>Error: Token is required</ansired>'))
        print_formatted_text(HTML('<grey>Usage: snc --token &lt;your-token&gt;</grey>'))
        print_formatted_text('')
        return False

    # Validate token format
    if not validate_snc_token(token):
        print_formatted_text('')
        print_formatted_text(HTML('<ansired>Error: Invalid token format</ansired>'))
        print_formatted_text('')
        return False

    # Store the token
    if store_snc_token(token):
        display_login_success()
        return True
    else:
        display_login_error()
        return False


def handle_logout_command() -> None:
    """Handle logout command."""
    if logout_snc():
        display_logout_success()
    else:
        print_formatted_text('')
        print_formatted_text(HTML('<ansired>Error: Failed to logout</ansired>'))
        print_formatted_text('')


def handle_status_command() -> None:
    """Handle status command."""
    auth_info = get_snc_auth_info()
    display_status(auth_info)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Snowcode AI Assistant - Intelligent chat interface',
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
        help='Login with Snowcode authentication token and start chat',
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


def main() -> None:
    """Main entry point for Snowcode CLI."""
    try:
        args = parse_arguments()

        # Clear terminal and show banner
        clear()
        # display_snowcode_banner()

        # If no arguments provided, show help
        if not any([args.token, args.status, args.logout, args.chat]):
            display_snowcode_help()
            return

        # Handle commands
        if args.token:
            print_formatted_text(HTML(f'<grey>Authenticating with Snowcode...</grey>'))
            print_formatted_text('')

            if handle_login_command(args.token):
                # After successful login, automatically start chat
                print_formatted_text('')
                print_formatted_text(
                    HTML('<gold>🎉 Welcome to Snowcode AI Assistant!</gold>')
                )
                print_formatted_text(HTML('<grey>Starting AI chat interface...</grey>'))
                launch_openhands_chat()

        elif args.status:
            handle_status_command()

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
                    HTML('<gold>🎉 Welcome to Snowcode AI Assistant!</gold>')
                )
                launch_openhands_chat()
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
            handle_logout_command()

    except KeyboardInterrupt:
        print_formatted_text('')
        print_formatted_text(HTML('<grey>Operation cancelled.</grey>'))
        print_formatted_text('')
    except Exception as e:
        print_formatted_text('')
        print_formatted_text(HTML(f'<ansired>Error: {str(e)}</ansired>'))
        print_formatted_text('')
        sys.exit(1)


if __name__ == '__main__':
    main()
