# Robust MCP Server Management System

This document describes the enhanced MCP (Model Context Protocol) server management system inspired by VS Code Copilot Chat's implementation.

## Key Features

### 🔧 Robust Package Management

- **Multi-package support**: npm, pip, docker, and binary packages
- **Automatic installation**: Attempts to install missing packages
- **Fallback mechanisms**: Uses npx for on-demand package execution
- **Registry validation**: Validates packages against official registries
- **Error recovery**: Graceful handling of installation failures

### 🛡️ Error Handling

- **Prerequisite checking**: Validates required tools (npm, python, docker)
- **Timeout management**: Configurable timeouts for different package types
- **Graceful degradation**: Skips failed servers, continues with working ones
- **Detailed logging**: Comprehensive error messages and troubleshooting hints

### 🔍 Health Checking

- **Pre-flight validation**: Checks server configuration before connection
- **Connection testing**: Verifies server can be reached and responds
- **Interactive troubleshooting**: Guided resolution of common issues
- **Automated fixes**: Can disable failing servers automatically

## Architecture

### Core Components

1. **MCPPackageManager** (`openhands/mcp/package_manager.py`)

   - Handles package detection, validation, and installation
   - Supports npm, pip, docker, and binary packages
   - Async-first design with proper resource management

2. **Enhanced stdio_client** (`openhands/mcp/stdio_client.py`)

   - Uses the package manager for robust server preparation
   - Improved timeout handling and error recovery
   - Better logging and user feedback

3. **Updated config editor** (`openhands/cli/config_editor.py`)

   - Uses package manager for server testing
   - Simplified connection testing logic
   - Better error reporting

4. **Health check utility** (`mcp_health_check.py`)
   - Comprehensive system validation
   - Interactive troubleshooting
   - Server management capabilities

## Package Type Support

### NPM Packages

```toml
{ name = "weather",
  command = "npx",
  args = ["-y", "@timlukahorstmann/mcp-weather"],
  env = { "API_KEY" = "your_key" } }
```

**Features:**

- Registry validation via npmjs.org API
- On-demand installation via npx
- Fallback to global installation
- Version checking and publisher validation

### Python/Pip Packages

```toml
{ name = "python-server",
  command = "python",
  args = ["-m", "your_mcp_package"],
  env = { "CONFIG_VAR" = "value" } }
```

**Features:**

- PyPI registry validation
- Automatic pip installation
- Python version compatibility
- Virtual environment support

### Docker Images

```toml
{ name = "docker-server",
  command = "docker",
  args = ["run", "--rm", "-i", "your-mcp-image"],
  env = { "DOCKER_VAR" = "value" } }
```

**Features:**

- Docker Hub registry validation
- Automatic image pulling
- Container lifecycle management
- Security considerations

### Binary Commands

```toml
{ name = "binary-server",
  command = "/path/to/binary",
  args = ["--config", "file.json"],
  env = { "PATH_VAR" = "value" } }
```

**Features:**

- PATH resolution
- Version checking
- Dependency validation
- Permission handling

## Usage

### Basic Commands

```bash
# Interactive configuration
poetry run snow --config-edit

# Validate configuration
poetry run snow --config-validate

# Health check with troubleshooting
poetry run snow --config-health

# Start chat with MCP servers
poetry run snow --chat
```

### Configuration Management

The system provides several ways to manage MCP servers:

1. **Manual editing**: Edit `config.toml` directly
2. **Interactive editor**: Use `--config-edit` for guided setup
3. **Health checking**: Use `--config-health` for validation and troubleshooting
4. **Automated fixes**: System can disable failing servers automatically

### Troubleshooting Workflow

1. **Prerequisites check**: Validates npm, python, docker availability
2. **Configuration validation**: Checks TOML syntax and required fields
3. **Package validation**: Verifies packages exist in registries
4. **Installation attempt**: Tries to install missing packages
5. **Connection test**: Attempts to connect to server
6. **Error reporting**: Provides specific error messages and suggestions

## Error Handling

### Common Issues and Solutions

**Package not found (E404)**

- Check package name spelling
- Verify package exists in registry
- Try alternative package names

**Permission denied (EACCES)**

- System falls back to npx for npm packages
- Consider using user-local installations
- Check file permissions for binaries

**Connection timeout**

- Increase timeout values for slow networks
- Check network connectivity
- Verify server is responding

**Missing dependencies**

- Install required tools (npm, python, docker)
- Update package managers
- Check system PATH

### Recovery Mechanisms

1. **Automatic retry**: Commands are retried with different parameters
2. **Graceful degradation**: Failed servers are skipped, working ones continue
3. **Fallback options**: Alternative installation methods are attempted
4. **User guidance**: Interactive prompts help resolve issues

## Performance Optimizations

### Caching

- Package validation results are cached
- Installation status is tracked
- Repeated operations are optimized

### Timeouts

- Adaptive timeouts based on package type
- Network-aware timeout adjustments
- Graceful timeout handling

### Parallel Processing

- Multiple servers can be processed concurrently
- Async operations throughout the system
- Resource-efficient subprocess management

## Security Considerations

### Package Validation

- Packages are validated against official registries
- Publisher information is checked
- Version constraints are enforced

### Execution Safety

- Subprocess isolation
- Environment variable scoping
- Resource cleanup on errors

### Network Security

- HTTPS-only registry communication
- Timeout protection against hanging requests
- Input validation for package names

## Development

### Adding New Package Types

1. Add new enum value to `PackageType`
2. Implement detection logic in `detect_package_type()`
3. Add package name extraction in `extract_package_name()`
4. Implement validation in `validate_package()`
5. Add installation logic in `install_package()`

### Testing

```bash
# Run package manager tests
poetry run python test_package_manager.py

# Run health check
poetry run python mcp_health_check.py

# Test individual servers
poetry run snow --config-edit  # Use "Test connections" option
```

## Best Practices

### Configuration

- Start with simple servers (filesystem, echo)
- Add API keys for external services
- Test servers individually before adding multiple
- Use health check before production deployment

### Monitoring

- Check logs for detailed error messages
- Monitor server connection success rates
- Track package installation failures
- Review timeout patterns

### Maintenance

- Update packages regularly
- Validate configuration after changes
- Monitor registry availability
- Keep documentation current

## Future Enhancements

### Planned Features

- GUI configuration interface
- Advanced caching strategies
- Package dependency resolution
- Monitoring dashboard
- Performance metrics

### Integration Points

- CI/CD pipeline integration
- Configuration management systems
- External monitoring tools
- Package registries

This robust MCP system provides a production-ready foundation for managing Model Context Protocol servers with enterprise-grade reliability and user-friendly troubleshooting capabilities.
