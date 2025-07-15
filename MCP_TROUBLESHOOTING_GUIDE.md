# MCP Connection Troubleshooting Guide

## 🚨 Quick Fix for MCP Connection Issues

If you're experiencing MCP server connection failures, here's how to resolve them:

### 1. Run Health Check First

```bash
poetry run snow --config-health
```

This will:

- ✅ Check if Node.js/npm are installed
- ✅ Validate your configuration
- ✅ Test each MCP server connection
- ✅ Provide specific troubleshooting advice

### 2. Common Issues & Solutions

#### Weather Server Timeout

```
Error: Timeout waiting for response from stdio MCP server weather
```

**Solution**: The weather server needs a valid API key:

1. Get an API key from [AccuWeather Developer Portal](https://developer.accuweather.com/)
2. Set it in your environment: `export ACCUWEATHER_API_KEY="your_key_here"`
3. Or edit config.toml to update the key

#### Filesystem Server Access Denied

```
Error: Allowed directories: [ '/tmp' ]
```

**Solution**: The filesystem server is restricted to /tmp by default:

1. Either use /tmp directory only
2. Or change the path in config.toml to a directory you own
3. Make sure the directory exists and is readable

#### SQLite Server E404 Error

```
Error: npm ERR! code E404
```

**Solution**: Package not found or network issue:

1. Check your internet connection
2. Try running: `npx @modelcontextprotocol/server-sqlite --help`
3. If it fails, the package might not exist or have a different name

#### Playwright Server Fails

```
Error: Browser binaries not found
```

**Solution**: Install browser binaries:

```bash
npx playwright install
```

### 3. Use the Interactive Config Editor

```bash
poetry run snow --config-edit
```

New features:

- **Option 5: Test server connections** - Tests all servers and disables failed ones
- **Smart troubleshooting** - Provides specific advice for each error
- **Automatic cleanup** - Disables servers that can't connect

### 4. Safe Configuration Strategy

Start with minimal config and add servers one by one:

#### Step 1: Minimal Config (Always Works)

```toml
[mcp]
stdio_servers = [
    # Start with just the weather server
    { name = "weather",
      command = "npx",
      args = ["-y", "@timlukahorstmann/mcp-weather"],
      env = { "ACCUWEATHER_API_KEY" = "your_api_key_here" } }
]
```

#### Step 2: Test Each Addition

Before adding a new server:

1. Add it to config.toml
2. Run: `poetry run snow --config-health`
3. If it works, keep it. If not, comment it out and fix the issue first

#### Step 3: Common Working Servers

```toml
# These usually work without issues:
{ name = "echo-test", command = "echo", args = ["test"] }  # Always works
{ name = "filesystem", command = "npx", args = ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"] }  # Usually works
```

### 5. Environment Setup

Make sure you have the prerequisites:

```bash
# Check Node.js
node --version  # Should be v16+

# Check npm
npm --version

# Check npx
npx --version

# Install if missing (Ubuntu/Debian):
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 6. Debug Mode

For detailed error information:

1. Set `debug = true` in config.toml (already enabled)
2. Check logs in the `logs/` directory
3. Run commands with verbose output

### 7. Working Configuration Example

Here's a tested configuration that should work:

```toml
[core]
debug = true

[mcp]
stdio_servers = [
    # Weather server (test with valid API key)
    { name = "weather",
      command = "npx",
      args = ["-y", "@timlukahorstmann/mcp-weather"],
      env = { "ACCUWEATHER_API_KEY" = "your_actual_api_key_here" } },

    # Filesystem server (usually works)
    # { name = "filesystem",
    #   command = "npx",
    #   args = ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"] },
]
```

### 8. Available Commands

- `poetry run snow --config-health` - Full health check and troubleshooting
- `poetry run snow --config-edit` - Interactive configuration editor
- `poetry run snow --config-validate` - Quick validation check
- `poetry run snow --chat` - Start chat (after fixing MCP issues)

### 9. Getting Help

If you're still having issues:

1. Run the health check for specific error messages
2. Check the troubleshooting suggestions it provides
3. Use the interactive config editor to test and fix servers
4. Start with a minimal configuration and add servers gradually

The system now handles MCP connection failures gracefully and provides specific guidance for each type of error!
