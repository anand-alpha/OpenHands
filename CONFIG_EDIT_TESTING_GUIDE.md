# How to Test the Config-Edit Command

This guide shows you exactly how to test the `--config-edit` command functionality.

## Quick Test Commands

### 1. Validate Current Configuration

```bash
cd /home/hac/code/OpenHands
poetry run snow --config-validate
```

### 2. Launch Interactive Editor

```bash
cd /home/hac/code/OpenHands
poetry run snow --config-edit
```

### 3. Test with Custom Config File

```bash
cd /home/hac/code/OpenHands
poetry run snow --config-edit  # Uses config.toml by default
```

## Step-by-Step Testing

### Test 1: Basic Validation

```bash
# This should show "✅ Configuration is valid!"
poetry run snow --config-validate
```

### Test 2: Interactive Editor Flow

```bash
# Launch the editor
poetry run snow --config-edit
```

When the editor opens, you'll see:

```
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

### Test 3: Add a New Server

1. Run the editor: `poetry run snow --config-edit`
2. Select option `1` (Add new server)
3. Enter server details:
   - Server name: `filesystem`
   - Command: `npx`
   - Arguments: `-y`, `@modelcontextprotocol/server-filesystem`, `/tmp`
   - Environment variables: (none - press Enter)
4. Select option `5` to validate
5. Select option `6` to save and exit

### Test 4: Add Predefined Server

1. Run the editor: `poetry run snow --config-edit`
2. Select option `4` (Add predefined server)
3. Choose from available templates:
   - `1` for Weather Server
   - `2` for Playwright
   - `3` for Filesystem
   - `4` for SQLite
4. Select option `5` to validate
5. Select option `6` to save and exit

### Test 5: Edit Existing Server

1. Run the editor: `poetry run snow --config-edit`
2. Select option `3` (Edit server)
3. Select server number to edit (e.g., `1` for weather)
4. Modify fields as needed
5. Select option `5` to validate
6. Select option `6` to save and exit

### Test 6: Validation with Errors

1. Edit `config.toml` manually to introduce an error:
   ```toml
   stdio_servers = [
       { name = "broken-server" }  # Missing required fields
   ]
   ```
2. Run validation: `poetry run snow --config-validate`
3. Should show error messages about missing fields

## Expected Outputs

### Successful Validation

```
✅ Configuration is valid!
```

### Validation with Errors

```
❌ Configuration errors found:
  • Server 1 missing 'command' field
  • Server 1 missing 'args' field
```

### Editor Interface

```
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
```

## Test Scenarios

### Scenario 1: Clean Installation

1. Start with minimal config
2. Add servers using templates
3. Validate configuration
4. Save changes

### Scenario 2: Modify Existing Config

1. Start with existing servers
2. Edit server configurations
3. Add new servers
4. Remove unwanted servers
5. Validate and save

### Scenario 3: Error Handling

1. Try to add server without required fields
2. Test validation with broken config
3. Verify error messages are helpful

## Command Line Options

| Option                   | Description               |
| ------------------------ | ------------------------- |
| `snow --config-edit`     | Launch interactive editor |
| `snow --config-validate` | Validate config and exit  |

## Files Created/Modified

- `config.toml` - Main configuration file
- `/tmp/test_config.toml` - Test configuration file
- Backup files (if any) created by the editor

## Troubleshooting

### If editor doesn't start:

- Check that prompt-toolkit is installed: `poetry install`
- Verify Python path and dependencies

### If validation fails:

- Check TOML syntax
- Verify required fields (name, command, args)
- Check file permissions

### If changes don't persist:

- Ensure you select "Save and exit" (option 6)
- Check file write permissions
- Verify config file path

## Clean Up

After testing, you can:

```bash
# Remove test config file
rm /tmp/test_config.toml

# Reset to original config if needed
git checkout config.toml
```

This completes the testing guide for the config-edit command!
