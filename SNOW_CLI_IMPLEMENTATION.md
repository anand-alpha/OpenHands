# Snow CLI Config Commands Implementation

## Summary

Successfully implemented the `poetry run snow --config-edit` and `poetry run snow --config-validate` commands as requested.

## Changes Made

### 1. Modified `openhands/cli/snowcode_cli.py`

- Added `--config-edit` and `--config-validate` arguments to the argument parser
- Added `handle_config_edit_command()` function to launch the interactive editor
- Added `handle_config_validate_command()` function for validation
- Updated the main function to handle these new commands
- Updated help display to show the new configuration management commands
- Updated the argument parser epilog with usage examples

### 2. Updated Configuration Files

- **config.toml**: Updated help comments to use the new shorter commands
- **docs/MCP_CONFIG_GUIDE.md**: Updated all command references
- **README.md**: Updated MCP configuration section
- **CONFIG_EDIT_TESTING_GUIDE.md**: Updated all test commands

## New Commands Available

### Configuration Management Commands

```bash
# Interactive configuration editor
poetry run snow --config-edit

# Validate configuration
poetry run snow --config-validate
```

### Command Output Examples

#### Help Display

```bash
$ poetry run snow

Snowcode AI Assistant Commands:

• snow --token <token> - Login and start AI assistant
• snow --status - Check your authentication status
• snow --chat - Start chat session (if authenticated)
• snow --logout - Logout and end session

Configuration Management:
• snow --config-edit - Edit MCP server configuration
• snow --config-validate - Validate MCP server configuration
```

#### Validation

```bash
$ poetry run snow --config-validate

🔍 Validating MCP Configuration...

✅ Configuration is valid!
✅ Configuration is ready to use!
```

#### Interactive Editor

```bash
$ poetry run snow --config-edit

🔧 Launching MCP Configuration Editor...

🔧 OpenHands MCP Configuration Editor
Manage your Model Context Protocol server configurations

📋 Current MCP Servers:
  1. weather
     Command: npx -y @timlukahorstmann/mcp-weather
     Environment variables: 1 set

Options:
  1. Add new server
  2. Remove server
  3. Edit server
  4. Add predefined server
  5. Validate configuration
  6. Save and exit
  7. Exit without saving

Select option (1-7):
```

## Benefits

1. **Shorter commands**: `poetry run snow --config-edit` vs `poetry run python -m openhands.cli.main --config-edit`
2. **Consistent branding**: Uses the "snow" command that's already established in the project
3. **Integrated help**: Commands show up in the main snow help display
4. **Same functionality**: All existing config editor features remain intact
5. **Better UX**: Cleaner, more professional command structure

## Testing

All commands have been tested and work correctly:

- ✅ `poetry run snow --config-validate` - Validates configuration
- ✅ `poetry run snow --config-edit` - Launches interactive editor
- ✅ `poetry run snow` - Shows updated help with new commands
- ✅ All documentation updated to reflect new commands

The implementation is complete and ready for use!
