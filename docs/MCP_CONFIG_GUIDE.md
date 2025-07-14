# MCP Configuration Guide

This guide explains how to configure Model Context Protocol (MCP) servers in OpenHands.

## Quick Start

1. **Edit config.toml directly**: Open `config.toml` in your favorite text editor and modify the `[mcp]` section
2. **Use the interactive editor**: Run `poetry run snow --config-edit`
3. **Validate your changes**: Run `poetry run snow --config-validate`

## Configuration Structure

The MCP configuration is located in the `[mcp]` section of `config.toml`:

```toml
[mcp]
stdio_servers = [
    {
        name = "server_name",
        command = "command_to_run",
        args = ["arg1", "arg2", "arg3"],
        env = { "ENV_VAR" = "value" }  # Optional
    }
]
```

### Required Fields

- `name`: Unique identifier for the server
- `command`: Executable command (e.g., "npx", "python", "node")
- `args`: List of command arguments

### Optional Fields

- `env`: Environment variables as key-value pairs

## Example Servers

### Weather Server

```toml
{ name = "weather",
  command = "npx",
  args = ["-y", "@timlukahorstmann/mcp-weather"],
  env = { "ACCUWEATHER_API_KEY" = "your_api_key_here" } }
```

### Filesystem Server

```toml
{ name = "filesystem",
  command = "npx",
  args = ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"] }
```

### SQLite Database Server

```toml
{ name = "sqlite",
  command = "npx",
  args = ["-y", "@modelcontextprotocol/server-sqlite", "database.db"] }
```

### Playwright Browser Automation

```toml
{ name = "playwright",
  command = "npx",
  args = ["@playwright/mcp@latest", "--headless"] }
```

## CLI Commands

### Interactive Editor

```bash
poetry run snow --config-edit
```

Features:

- Add new servers
- Remove existing servers
- Edit server configurations
- Add predefined server templates
- Validate configuration
- Save changes

### Validation Only

```bash
poetry run snow --config-validate
```

Checks your configuration for errors without opening the editor.

## Tips

1. **Restart Required**: After making changes to `config.toml`, restart OpenHands for changes to take effect
2. **API Keys**: Don't forget to set required API keys in environment variables
3. **Validation**: Always validate your configuration before restarting OpenHands
4. **Backup**: Keep a backup of your working configuration before making changes

## Troubleshooting

- If a server fails to start, check the logs for error messages
- Ensure all required dependencies are installed (e.g., `npx` for npm packages)
- Verify API keys are correctly set in environment variables
- Use `--config-validate` to check for configuration errors
