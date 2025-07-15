#!/usr/bin/env python3
"""
Configuration Editor for OpenHands MCP Settings
Allows users to interactively manage MCP server configurations
"""

import os
import sys
import toml
from typing import Dict, List, Any, Optional
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import print_formatted_text, confirm
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.completion import WordCompleter


class MCPConfigEditor:
    """Interactive editor for MCP server configurations"""

    def __init__(self, config_file: str = "config.toml"):
        self.config_file = config_file
        self.config_data = {}
        self.load_config()

    def load_config(self):
        """Load configuration from TOML file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config_data = toml.load(f)
            else:
                # Create default config structure
                self.config_data = {
                    'core': {'debug': True},
                    'mcp': {'stdio_servers': []},
                }
        except Exception as e:
            print_formatted_text(
                HTML(f'<ansired>❌ Error loading config: {e}</ansired>')
            )
            sys.exit(1)

    def save_config(self):
        """Save configuration to TOML file"""
        try:
            with open(self.config_file, 'w') as f:
                toml.dump(self.config_data, f)
            print_formatted_text(
                HTML('<ansigreen>✅ Configuration saved successfully!</ansigreen>')
            )
        except Exception as e:
            print_formatted_text(
                HTML(f'<ansired>❌ Error saving config: {e}</ansired>')
            )

    def get_mcp_servers(self) -> List[Dict]:
        """Get current MCP stdio servers"""
        if 'mcp' not in self.config_data:
            self.config_data['mcp'] = {}
        if 'stdio_servers' not in self.config_data['mcp']:
            self.config_data['mcp']['stdio_servers'] = []
        return self.config_data['mcp']['stdio_servers']

    def validate_config(self) -> bool:
        """Validate the current configuration and show any errors"""
        errors = []

        # Check if mcp section exists
        if 'mcp' not in self.config_data:
            errors.append("Missing [mcp] section")
        else:
            mcp_config = self.config_data['mcp']

            # Check stdio_servers
            if 'stdio_servers' in mcp_config:
                servers = mcp_config['stdio_servers']
                if not isinstance(servers, list):
                    errors.append("stdio_servers must be a list")
                else:
                    for i, server in enumerate(servers):
                        if not isinstance(server, dict):
                            errors.append(f"Server {i+1} must be a dictionary")
                            continue

                        # Check required fields
                        if 'name' not in server:
                            errors.append(f"Server {i+1} missing 'name' field")
                        if 'command' not in server:
                            errors.append(f"Server {i+1} missing 'command' field")
                        if 'args' not in server:
                            errors.append(f"Server {i+1} missing 'args' field")
                        elif not isinstance(server['args'], list):
                            errors.append(f"Server {i+1} 'args' must be a list")

                        # Check optional env field
                        if 'env' in server and not isinstance(server['env'], dict):
                            errors.append(f"Server {i+1} 'env' must be a dictionary")

        if errors:
            print_formatted_text(
                HTML('<ansired>❌ Configuration errors found:</ansired>')
            )
            for error in errors:
                print_formatted_text(HTML(f'  • <ansired>{error}</ansired>'))
            return False
        else:
            print_formatted_text(
                HTML('<ansigreen>✅ Configuration is valid!</ansigreen>')
            )
            return True

    def test_server_connection(self, server_config: Dict) -> tuple[bool, str]:
        """Test if an MCP server can be reached and is working using robust package manager"""
        import asyncio

        name = server_config.get('name', 'unknown')
        print_formatted_text(
            HTML(f'<ansiyellow>🔍 Testing connection to {name}...</ansiyellow>')
        )

        try:
            # Convert dict to MCPStdioServerConfig
            from openhands.core.config.mcp_config import MCPStdioServerConfig
            from openhands.mcp.package_manager import MCPPackageManager

            server_obj = MCPStdioServerConfig(
                name=server_config['name'],
                command=server_config['command'],
                args=server_config['args'],
                env=server_config.get('env', {}),
            )

            # Use async context manager properly
            async def test_async():
                async with MCPPackageManager() as package_manager:
                    success, message = await package_manager.prepare_server(server_obj)
                    return success, message

            # Run the async test
            try:
                success, message = asyncio.run(test_async())
                return success, message
            except Exception as e:
                return False, f"Test failed: {str(e)}"

        except Exception as e:
            return False, f"Configuration error: {str(e)}"

    def test_all_servers(self):
        """Test all configured MCP servers"""
        servers = self.get_mcp_servers()
        if not servers:
            print_formatted_text(
                HTML('<ansiyellow>⚠️ No MCP servers configured</ansiyellow>')
            )
            return

        print_formatted_text(
            HTML('<ansiblue>🔍 Testing MCP Server Connections</ansiblue>')
        )
        print_formatted_text(
            HTML('<ansiyellow>This may take a few moments...</ansiyellow>')
        )
        print()

        working_servers = []
        failed_servers = []

        for i, server in enumerate(servers, 1):
            name = server.get('name', f'server_{i}')
            success, message = self.test_server_connection(server)

            if success:
                print_formatted_text(
                    HTML(f'  ✅ <ansigreen>{name}</ansigreen>: {message}')
                )
                working_servers.append(server)
            else:
                print_formatted_text(HTML(f'  ❌ <ansired>{name}</ansired>: {message}'))
                failed_servers.append((server, message))

        print()
        print_formatted_text(HTML(f'<ansiblue>Summary:</ansiblue>'))
        print_formatted_text(
            HTML(f'  ✅ Working servers: <ansigreen>{len(working_servers)}</ansigreen>')
        )
        print_formatted_text(
            HTML(f'  ❌ Failed servers: <ansired>{len(failed_servers)}</ansired>')
        )

        if failed_servers:
            print()
            print_formatted_text(
                HTML('<ansiyellow>💡 Troubleshooting suggestions:</ansiyellow>')
            )

            for server, error in failed_servers:
                name = server.get('name', 'unknown')
                print_formatted_text(HTML(f'  • <ansired>{name}</ansired>: {error}'))

                # Provide specific suggestions based on error type
                if 'not found' in error or 'E404' in error:
                    print_formatted_text(
                        HTML(
                            f'    💡 Try installing the package manually or check if it exists'
                        )
                    )
                elif 'npx' in error:
                    print_formatted_text(
                        HTML(f'    💡 Install Node.js and npm: https://nodejs.org/')
                    )
                elif 'timeout' in error:
                    print_formatted_text(
                        HTML(
                            f'    💡 The server may be slow to start, try increasing timeout'
                        )
                    )
                elif 'API' in error:
                    print_formatted_text(
                        HTML(f'    💡 Check if API keys are properly configured')
                    )

        # Offer to disable failed servers
        if failed_servers and confirm('\nDisable failed servers?'):
            self.disable_failed_servers([server for server, _ in failed_servers])

    def disable_failed_servers(self, failed_servers: List[Dict]):
        """Disable (comment out) failed servers in the config"""
        if not failed_servers:
            return

        print_formatted_text(
            HTML('<ansiyellow>🔧 Disabling failed servers...</ansiyellow>')
        )

        servers = self.get_mcp_servers()
        for failed_server in failed_servers:
            if failed_server in servers:
                servers.remove(failed_server)
                print_formatted_text(
                    HTML(f'  ✅ Disabled <ansired>{failed_server["name"]}</ansired>')
                )

        print_formatted_text(
            HTML('<ansigreen>✅ Failed servers have been disabled</ansigreen>')
        )
        print_formatted_text(
            HTML(
                '<ansiyellow>💡 You can re-enable them later after fixing the issues</ansiyellow>'
            )
        )

    def display_current_servers(self):
        """Display current MCP server configurations"""
        servers = self.get_mcp_servers()
        print_formatted_text(HTML('<ansiblue>📋 Current MCP Servers:</ansiblue>'))

        if not servers:
            print_formatted_text(
                HTML('<ansiyellow>  No MCP servers configured</ansiyellow>')
            )
        else:
            for i, server in enumerate(servers, 1):
                name = server.get('name', 'unnamed')
                command = server.get('command', '')
                args = ' '.join(server.get('args', []))
                env_count = len(server.get('env', {}))

                print_formatted_text(HTML(f'  <ansigreen>{i}. {name}</ansigreen>'))
                print_formatted_text(
                    HTML(f'     Command: <ansicyan>{command} {args}</ansicyan>')
                )
                if env_count > 0:
                    print_formatted_text(
                        HTML(
                            f'     Environment variables: <ansiyellow>{env_count} set</ansiyellow>'
                        )
                    )
        print()

    def add_server(self):
        """Add a new MCP server configuration"""
        print_formatted_text(HTML('<ansiblue>➕ Adding New MCP Server</ansiblue>'))

        # Server name
        name = prompt('Server name: ').strip()
        if not name:
            print_formatted_text(HTML('<ansired>❌ Server name is required</ansired>'))
            return

        # Command
        command_completer = WordCompleter(['npx', 'python', 'node', 'uvx', 'pip'])
        command = prompt('Command: ', completer=command_completer).strip()
        if not command:
            print_formatted_text(HTML('<ansired>❌ Command is required</ansired>'))
            return

        # Arguments
        print_formatted_text(
            HTML(
                '<ansiyellow>💡 Enter arguments one by one. Press Enter with empty input to finish.</ansiyellow>'
            )
        )
        args = []
        while True:
            arg = prompt(f'Argument {len(args) + 1} (or Enter to finish): ').strip()
            if not arg:
                break
            args.append(arg)

        # Environment variables
        env = {}
        if confirm('Add environment variables?'):
            print_formatted_text(
                HTML(
                    '<ansiyellow>💡 Enter environment variables. Press Enter with empty name to finish.</ansiyellow>'
                )
            )
            while True:
                env_name = prompt(
                    'Environment variable name (or Enter to finish): '
                ).strip()
                if not env_name:
                    break
                env_value = prompt(f'Value for {env_name}: ').strip()
                env[env_name] = env_value

        # Create server configuration
        server_config = {'name': name, 'command': command, 'args': args}
        if env:
            server_config['env'] = env

        # Add to servers list
        servers = self.get_mcp_servers()
        servers.append(server_config)

        print_formatted_text(
            HTML('<ansigreen>✅ Server added successfully!</ansigreen>')
        )

    def remove_server(self):
        """Remove an MCP server configuration"""
        servers = self.get_mcp_servers()
        if not servers:
            print_formatted_text(
                HTML('<ansiyellow>⚠️ No servers to remove</ansiyellow>')
            )
            return

        print_formatted_text(HTML('<ansiblue>🗑️ Remove MCP Server</ansiblue>'))
        self.display_current_servers()

        try:
            choice = int(prompt('Enter server number to remove: '))
            if 1 <= choice <= len(servers):
                removed_server = servers.pop(choice - 1)
                print_formatted_text(
                    HTML(
                        f'<ansigreen>✅ Removed server "{removed_server["name"]}"</ansigreen>'
                    )
                )
            else:
                print_formatted_text(
                    HTML('<ansired>❌ Invalid server number</ansired>')
                )
        except ValueError:
            print_formatted_text(
                HTML('<ansired>❌ Please enter a valid number</ansired>')
            )

    def edit_server(self):
        """Edit an existing MCP server configuration"""
        servers = self.get_mcp_servers()
        if not servers:
            print_formatted_text(HTML('<ansiyellow>⚠️ No servers to edit</ansiyellow>'))
            return

        print_formatted_text(HTML('<ansiblue>✏️ Edit MCP Server</ansiblue>'))
        self.display_current_servers()

        try:
            choice = int(prompt('Enter server number to edit: '))
            if 1 <= choice <= len(servers):
                server = servers[choice - 1]
                print_formatted_text(
                    HTML(f'<ansigreen>Editing server "{server["name"]}"</ansigreen>')
                )

                # Edit each field
                new_name = prompt(f'Server name [{server["name"]}]: ').strip()
                if new_name:
                    server['name'] = new_name

                new_command = prompt(f'Command [{server["command"]}]: ').strip()
                if new_command:
                    server['command'] = new_command

                # Edit args
                if confirm(f'Edit arguments? Current: {server.get("args", [])}'):
                    args = []
                    print_formatted_text(
                        HTML(
                            '<ansiyellow>💡 Enter new arguments. Press Enter with empty input to finish.</ansiyellow>'
                        )
                    )
                    while True:
                        arg = prompt(
                            f'Argument {len(args) + 1} (or Enter to finish): '
                        ).strip()
                        if not arg:
                            break
                        args.append(arg)
                    server['args'] = args

                # Edit environment variables
                if confirm(
                    f'Edit environment variables? Current: {list(server.get("env", {}).keys())}'
                ):
                    env = {}
                    print_formatted_text(
                        HTML(
                            '<ansiyellow>💡 Enter new environment variables. Press Enter with empty name to finish.</ansiyellow>'
                        )
                    )
                    while True:
                        env_name = prompt(
                            'Environment variable name (or Enter to finish): '
                        ).strip()
                        if not env_name:
                            break
                        env_value = prompt(f'Value for {env_name}: ').strip()
                        env[env_name] = env_value
                    server['env'] = env

                print_formatted_text(
                    HTML('<ansigreen>✅ Server updated successfully!</ansigreen>')
                )
            else:
                print_formatted_text(
                    HTML('<ansired>❌ Invalid server number</ansired>')
                )
        except ValueError:
            print_formatted_text(
                HTML('<ansired>❌ Please enter a valid number</ansired>')
            )

    def add_predefined_server(self):
        """Add a predefined MCP server from templates"""
        templates = {
            '1': {
                'name': 'weather',
                'command': 'npx',
                'args': ['-y', '@timlukahorstmann/mcp-weather'],
                'env': {'ACCUWEATHER_API_KEY': 'your_api_key_here'},
            },
            '2': {
                'name': 'playwright',
                'command': 'npx',
                'args': ['@playwright/mcp@latest', '--headless'],
            },
            '3': {
                'name': 'filesystem',
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-filesystem', '/tmp'],
            },
            '4': {
                'name': 'sqlite',
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-sqlite', 'database.db'],
            },
        }

        print_formatted_text(HTML('<ansiblue>📦 Add Predefined MCP Server</ansiblue>'))
        print_formatted_text(HTML('<ansiyellow>Available templates:</ansiyellow>'))
        print_formatted_text(HTML('  1. Weather Server (requires API key)'))
        print_formatted_text(HTML('  2. Playwright Browser Automation'))
        print_formatted_text(HTML('  3. Filesystem Server'))
        print_formatted_text(HTML('  4. SQLite Database Server'))
        print()

        choice = prompt('Select template (1-4): ').strip()
        if choice in templates:
            server_config = templates[choice].copy()

            # Allow customization
            if confirm(f'Add "{server_config["name"]}" server with default settings?'):
                servers = self.get_mcp_servers()
                servers.append(server_config)
                print_formatted_text(
                    HTML(
                        f'<ansigreen>✅ Added {server_config["name"]} server!</ansigreen>'
                    )
                )

                if choice == '1':  # Weather server
                    print_formatted_text(
                        HTML(
                            '<ansiyellow>💡 Don\'t forget to set your ACCUWEATHER_API_KEY!</ansiyellow>'
                        )
                    )
        else:
            print_formatted_text(HTML('<ansired>❌ Invalid template choice</ansired>'))

    def run(self):
        """Run the interactive configuration editor"""
        print_formatted_text(
            HTML('<ansiblue>🔧 OpenHands MCP Configuration Editor</ansiblue>')
        )
        print_formatted_text(
            HTML(
                '<ansiyellow>Manage your Model Context Protocol server configurations</ansiyellow>'
            )
        )
        print()

        while True:
            self.display_current_servers()

            print_formatted_text(HTML('<ansiblue>Options:</ansiblue>'))
            print_formatted_text(HTML('  1. Add new server'))
            print_formatted_text(HTML('  2. Remove server'))
            print_formatted_text(HTML('  3. Edit server'))
            print_formatted_text(HTML('  4. Add predefined server'))
            print_formatted_text(HTML('  5. Test server connections'))
            print_formatted_text(HTML('  6. Validate configuration'))
            print_formatted_text(HTML('  7. Save and exit'))
            print_formatted_text(HTML('  8. Exit without saving'))
            print()

            choice = prompt('Select option (1-8): ').strip()

            if choice == '1':
                self.add_server()
            elif choice == '2':
                self.remove_server()
            elif choice == '3':
                self.edit_server()
            elif choice == '4':
                self.add_predefined_server()
            elif choice == '5':
                self.test_all_servers()
            elif choice == '6':
                self.validate_config()
            elif choice == '7':
                if self.validate_config():
                    self.save_config()
                    break
                else:
                    if confirm('Save configuration anyway?'):
                        self.save_config()
                        break
            elif choice == '8':
                if confirm('Exit without saving changes?'):
                    break
            else:
                print_formatted_text(HTML('<ansired>❌ Invalid option</ansired>'))

            print()


def main():
    """Main entry point for the configuration editor"""
    import argparse

    parser = argparse.ArgumentParser(description='OpenHands MCP Configuration Editor')
    parser.add_argument(
        '--config',
        '-c',
        default='config.toml',
        help='Path to config.toml file (default: config.toml)',
    )

    args = parser.parse_args()

    editor = MCPConfigEditor(args.config)
    try:
        editor.run()
    except KeyboardInterrupt:
        print_formatted_text(
            HTML('\n<ansiyellow>👋 Configuration editor interrupted</ansiyellow>')
        )
    except Exception as e:
        print_formatted_text(HTML(f'\n<ansired>❌ Error: {e}</ansired>'))
        sys.exit(1)


if __name__ == '__main__':
    main()
