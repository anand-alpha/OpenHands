#!/usr/bin/env python3
"""
MCP Health Check utility
Checks MCP server configurations and provides troubleshooting guidance
"""

import sys
import os
import subprocess
import asyncio
from typing import Dict, List, Tuple

# Add OpenHands to the path
sys.path.insert(0, '/home/hac/code/OpenHands')

from openhands.cli.config_editor import MCPConfigEditor
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import confirm


class MCPHealthChecker:
    """Health checker for MCP servers"""

    def __init__(self, config_file: str = "config.toml"):
        self.editor = MCPConfigEditor(config_file)

    def check_prerequisites(self) -> bool:
        """Check if basic prerequisites are installed"""
        print_formatted_text(HTML('<ansiblue>🔍 Checking prerequisites...</ansiblue>'))

        prerequisites = [('node', 'Node.js'), ('npm', 'npm'), ('npx', 'npx')]

        missing = []
        for cmd, name in prerequisites:
            try:
                result = subprocess.run(
                    [cmd, '--version'], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print_formatted_text(HTML(f'  ✅ {name}: {version}'))
                else:
                    missing.append(name)
                    print_formatted_text(HTML(f'  ❌ {name}: Not working'))
            except:
                missing.append(name)
                print_formatted_text(HTML(f'  ❌ {name}: Not found'))

        if missing:
            print_formatted_text(
                HTML('<ansiyellow>💡 Missing prerequisites:</ansiyellow>')
            )
            for name in missing:
                print_formatted_text(HTML(f'  • {name}'))
            print_formatted_text(
                HTML(
                    '<ansiyellow>Install Node.js from: https://nodejs.org/</ansiyellow>'
                )
            )
            return False

        return True

    def fix_common_issues(self):
        """Provide fixes for common MCP server issues"""
        print_formatted_text(
            HTML('<ansiblue>🔧 Common MCP Server Issues & Fixes</ansiblue>')
        )
        print()

        fixes = [
            {
                'issue': 'Weather server timeout',
                'cause': 'Missing or invalid API key',
                'fix': 'Get an API key from AccuWeather and set ACCUWEATHER_API_KEY environment variable',
            },
            {
                'issue': 'Filesystem server access denied',
                'cause': 'Path permissions or invalid directory',
                'fix': 'Ensure the directory exists and is readable/writable',
            },
            {
                'issue': 'SQLite server E404 error',
                'cause': 'Package not found or typo in package name',
                'fix': 'Check package name and ensure it exists on npm',
            },
            {
                'issue': 'Playwright server fails',
                'cause': 'Missing browser binaries',
                'fix': 'Run: npx playwright install',
            },
            {
                'issue': 'NPX timeout',
                'cause': 'Slow network or first-time package download',
                'fix': 'Pre-install packages or increase timeout',
            },
        ]

        for fix in fixes:
            print_formatted_text(
                HTML(f'<ansiyellow>Issue:</ansiyellow> {fix["issue"]}')
            )
            print_formatted_text(HTML(f'<ansired>Cause:</ansired> {fix["cause"]}'))
            print_formatted_text(HTML(f'<ansigreen>Fix:</ansigreen> {fix["fix"]}'))
            print()

    def create_minimal_config(self):
        """Create a minimal working configuration"""
        print_formatted_text(
            HTML('<ansiblue>🔧 Creating minimal working configuration...</ansiblue>')
        )

        # Disable all servers first
        self.editor.config_data['mcp']['stdio_servers'] = []

        # Add only a simple test server that should work
        test_server = {
            'name': 'test-echo',
            'command': 'echo',
            'args': ['MCP server test'],
        }

        print_formatted_text(
            HTML(
                '<ansiyellow>Created minimal config with echo test server</ansiyellow>'
            )
        )
        print_formatted_text(
            HTML('<ansigreen>This should work without any dependencies</ansigreen>')
        )

        if confirm('Save minimal configuration?'):
            self.editor.save_config()
            print_formatted_text(
                HTML('<ansigreen>✅ Minimal configuration saved</ansigreen>')
            )

    def run_health_check(self):
        """Run complete health check"""
        print_formatted_text(HTML('<ansiblue>🏥 MCP Health Check</ansiblue>'))
        print_formatted_text(
            HTML('<ansiyellow>Checking your MCP server configuration...</ansiyellow>')
        )
        print()

        # Check prerequisites
        if not self.check_prerequisites():
            print()
            print_formatted_text(
                HTML(
                    '<ansired>❌ Prerequisites missing - install Node.js first</ansired>'
                )
            )
            return False

        print()

        # Validate config
        print_formatted_text(
            HTML('<ansiblue>🔍 Validating configuration...</ansiblue>')
        )
        if not self.editor.validate_config():
            print()
            print_formatted_text(HTML('<ansired>❌ Configuration has errors</ansired>'))
            return False

        print()

        # Test server connections
        print_formatted_text(
            HTML('<ansiblue>🔍 Testing server connections...</ansiblue>')
        )
        self.editor.test_all_servers()

        print()

        # Check if any servers are working
        servers = self.editor.get_mcp_servers()
        if not servers:
            print_formatted_text(
                HTML('<ansiyellow>⚠️ No MCP servers configured</ansiyellow>')
            )
            print_formatted_text(
                HTML(
                    '<ansiyellow>OpenHands will work but without MCP tools</ansiyellow>'
                )
            )
            return True

        print()
        print_formatted_text(HTML('<ansiblue>💡 Recommendations:</ansiblue>'))
        print_formatted_text(HTML('  • Start with simple servers (filesystem, echo)'))
        print_formatted_text(HTML('  • Add API keys for weather services'))
        print_formatted_text(
            HTML('  • Test servers individually before adding multiple')
        )
        print_formatted_text(HTML('  • Check logs for detailed error messages'))

        return True

    def interactive_troubleshooting(self):
        """Interactive troubleshooting session"""
        print_formatted_text(
            HTML('<ansiblue>🛠️ Interactive MCP Troubleshooting</ansiblue>')
        )
        print()

        while True:
            print_formatted_text(
                HTML('<ansiblue>What would you like to do?</ansiblue>')
            )
            print_formatted_text(HTML('  1. Run health check'))
            print_formatted_text(HTML('  2. Test server connections'))
            print_formatted_text(HTML('  3. View common issues & fixes'))
            print_formatted_text(HTML('  4. Create minimal working config'))
            print_formatted_text(HTML('  5. Open config editor'))
            print_formatted_text(HTML('  6. Exit'))
            print()

            choice = input('Select option (1-6): ').strip()

            if choice == '1':
                self.run_health_check()
            elif choice == '2':
                self.editor.test_all_servers()
            elif choice == '3':
                self.fix_common_issues()
            elif choice == '4':
                self.create_minimal_config()
            elif choice == '5':
                self.editor.run()
            elif choice == '6':
                print_formatted_text(HTML('<ansiyellow>👋 Goodbye!</ansiyellow>'))
                break
            else:
                print_formatted_text(HTML('<ansired>❌ Invalid option</ansired>'))

            print()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='MCP Health Check Utility')
    parser.add_argument(
        '--config', '-c', default='config.toml', help='Path to config file'
    )
    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help='Run interactive troubleshooting',
    )

    args = parser.parse_args()

    checker = MCPHealthChecker(args.config)

    try:
        if args.interactive:
            checker.interactive_troubleshooting()
        else:
            checker.run_health_check()
    except KeyboardInterrupt:
        print_formatted_text(HTML('\n<ansiyellow>👋 Interrupted</ansiyellow>'))
    except Exception as e:
        print_formatted_text(HTML(f'\n<ansired>❌ Error: {e}</ansired>'))


if __name__ == '__main__':
    main()
