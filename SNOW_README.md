# Snowcode CLI (snow) - Complete Documentation

A secure, company-branded command-line interface for authentication and access to the Snowcode AI Assistant. Built as a wrapper around OpenHands backend with pure Snowcode branding and user experience.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands Reference](#commands-reference)
- [Usage Examples](#usage-examples)
- [Implementation Details](#implementation-details)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

---

## Features

✅ **Pure Snowcode Branding**: All banners, help text, and user interfaces use Snowcode identity only
✅ **Secure Authentication**: Token-based login with SHA256 hashing and 24-hour expiration
✅ **Real AI Assistant**: Full OpenHands AI capabilities with Snowcode branding
✅ **Zero OpenHands Exposure**: No OpenHands commands or branding visible to users
✅ **Session Management**: Status checking, secure logout, and token validation
✅ **Auto-Launch Chat**: Seamless transition from login to AI chat interface

---

## Installation

### Prerequisites

- Python 3.12+
- Poetry (for dependency management)

### Install

```bash
cd /path/to/OpenHands
poetry install
```

### Verify Installation

```bash
poetry run snow
```

---

## Quick Start

1. **Login and start chatting**:

   ```bash
   snow --token your-token-here
   ```

2. **Check if you're authenticated**:

   ```bash
   snow --status
   ```

3. **Start chat (if already logged in)**:
   ```bash
   snow --chat
   ```

---

## Commands Reference

### `snow` (No arguments)

**Purpose**: Display help and available commands
**Output**: Shows Snowcell banner and command list

```bash
snow
```

### `snow --token <token>`

**Purpose**: Authenticate with Snowcode and launch AI chat
**Behavior**:

- Validates and stores token securely
- Shows success/error message
- Automatically launches AI chat interface
- Token expires in 24 hours

```bash
snow --token abc123xyz789
```

### `snow --status`

**Purpose**: Check authentication status and remaining time
**Output**:

- Authentication status (✓ or ✗)
- Time remaining before expiration
- Ready status for chat

```bash
snow --status
```

### `snow --chat`

**Purpose**: Start AI chat session (requires authentication)
**Behavior**:

- Checks if user is authenticated
- Launches full AI assistant with Snowcode branding
- Shows error if not authenticated

```bash
snow --chat
```
### `snow --logout`

**Purpose**: End session and clear authentication
**Behavior**:

- Removes stored token
- Shows logout confirmation
- Requires re-authentication for future use

```bash
snow --logout
```

---

## Usage Examples

### Example 1: First-time Login

```bash
$ snow --token mycompanytoken123

     ____                                   _
    / ___| _ __   _____      _____ ___   __| | ___
    \___ \| '_ \ / _ \ \ /\ / / __/ _ \ / _  |/ _ \
     ___) | | | | (_) \ V  V / (_| (_) | (_| |  __/
    |____/|_| |_|\___/ \_/\_/ \___\___/ \____|\___/

    Snowcell AI Assistant

Your intelligent AI-powered assistant

Authenticating with Snowcell...

✓ Successfully authenticated with Snowcell!

🎉 Welcome to Snowcell AI Assistant!
Starting AI chat interface...

🚀 Starting Snowcell AI Assistant...

[AI chat interface launches with Snowcell branding]
```

### Example 2: Check Status

```bash
$ snow --status

     ____                                   _
    / ___| _ __   _____      _____ ___   __| | ___
    \___ \| '_ \ / _ \ \ /\ / / __/ _ \ / _  |/ _ \
     ___) | | | | (_) \ V  V / (_| (_) | (_| |  __/
    |____/|_| |_|\___/ \_/\_/ \___\___/ \____|\___/

    Snowcell AI Assistant

Your intelligent AI-powered assistant

Snowcell Authentication Status:

Status: Authenticated ✓
Time remaining: 23h 45m

Ready to chat! Use snow --chat to start the AI assistant.
```

### Example 3: Start Chat (Already Authenticated)

```bash
$ snow --chat

     ____                                   _
    / ___| _ __   _____      _____ ___   __| | ___
    \___ \| '_ \ / _ \ \ /\ / / __/ _ \ / _  |/ _ \
     ___) | | | | (_) \ V  V / (_| (_) | (_| |  __/
    |____/|_| |_|\___/ \_/\_/ \___\___/ \____|\___/

    Snowcell AI Assistant

Your intelligent AI-powered assistant

🎉 Welcome to Snowcell AI Assistant!
Starting AI chat interface...

[AI chat launches]
```

### Example 4: Logout

```bash
$ snow --logout

     ____                                   _
    / ___| _ __   _____      _____ ___   __| | ___
    \___ \| '_ \ / _ \ \ /\ / / __/ _ \ / _  |/ _ \
     ___) | | | | (_) \ V  V / (_| (_) | (_| |  __/
    |____/|_| |_|\___/ \_/\_/ \___\___/ \____|\___/

    Snowcell AI Assistant

Your intelligent AI-powered assistant

✓ Successfully logged out from Snowcell
Thank you for using Snowcell AI Assistant!
```

---

## Implementation Details

### File Structure

```
openhands/
├── cli/
│   ├── snowcode_cli.py     # Main Snowcell CLI entry point
│   ├── tui.py              # Modified for Snowcell branding
│   ├── utils.py            # Authentication utilities
│   └── main.py             # OpenHands main CLI (unchanged)
└── pyproject.toml          # Entry point configuration
```

### Key Components

#### 1. Main CLI (`snowcode_cli.py`)

- **Purpose**: Snowcell-branded authentication wrapper
- **Functions**:
  - `display_snowcell_banner()` - Shows Snowcell ASCII art
  - `handle_login_command()` - Processes authentication
  - `launch_openhands_chat()` - Starts AI chat with branding
  - `parse_arguments()` - Handles command-line arguments

#### 2. Authentication System (`utils.py`)

- **Token Storage**: `~/.openhands/snow_auth.json`
- **Security**: SHA256 hashing, 24-hour expiration
- **Functions**:
  - `store_snow_token()` - Secure token storage
  - `verify_snow_token()` - Authentication checking
  - `get_snow_auth_info()` - Status information
  - `logout_snow()` - Session cleanup

#### 3. Branding System (`tui.py`)

- **Environment Variable**: `SNOWCELL_BRANDING=true`
- **Dynamic Branding**:
  - `display_banner()` - Snowcell vs OpenHands banners
  - `display_welcome_message()` - Custom welcome text
  - `display_help()` - Branded help content

#### 4. Entry Point (`pyproject.toml`)

```toml
[tool.poetry.scripts]
snow = "openhands.cli.snowcell_cli:main"
openhands = "openhands.cli.main:main"
```

### Authentication Flow

1. User runs `snow --token <token>`
2. Token validated and hashed with SHA256
3. Stored in `~/.openhands/snow_auth.json` with timestamp
4. Environment variable `SNOWCELL_BRANDING=true` set
5. OpenHands main CLI launched with custom branding
6. User sees Snowcell AI Assistant interface

### Branding Mechanism

```python
# In snowcode_cli.py
os.environ['SNOWCELL_BRANDING'] = 'true'

# In tui.py
if os.environ.get('SNOWCELL_BRANDING') == 'true':
    # Show Snowcell branding
else:
    # Show OpenHands branding
```

---

## Security

### Token Security

- **No Plaintext Storage**: Tokens are hashed with SHA256
- **Automatic Expiration**: 24-hour session timeout
- **Secure Location**: Stored in user's home directory (`~/.openhands/`)
- **Session Isolation**: Each session is independent

### Token Storage Format

```json
{
  "token_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
  "timestamp": 1704326400.0,
  "status": "active"
}
```

### Best Practices

- Use strong, unique tokens
- Regular token rotation (24h automatic)
- Logout when session complete
- Monitor authentication status

---

## Troubleshooting

### Common Issues

#### 1. "Authentication required" error

**Problem**: Trying to use `--chat` without being logged in
**Solution**:

```bash
snow --token your-token-here
```

#### 2. "Invalid token format" error

**Problem**: Token doesn't meet validation requirements
**Solution**: Check token length (minimum 10 characters) and format

#### 3. "Token expired" message

**Problem**: Session has exceeded 24-hour limit
**Solution**: Re-authenticate with fresh token

```bash
snow --token your-new-token
```

#### 4. Chat interface shows OpenHands branding

**Problem**: Environment variable not properly set
**Solution**: Restart CLI and ensure using `snow --token` or `snow --chat`

#### 5. Permission errors with token storage

**Problem**: Cannot write to `~/.openhands/` directory
**Solution**: Check directory permissions

```bash
mkdir -p ~/.openhands
chmod 755 ~/.openhands
```

### Debug Commands

```bash
# Check if token file exists
ls -la ~/.openhands/snow_auth.json

# View token storage (hashed, safe to check)
cat ~/.openhands/snow_auth.json

# Check authentication status
snow --status

# Force logout and re-login
snow --logout
snow --token your-token
```

### Getting Help

1. Run `snow` for command help
2. Check authentication with `snow --status`
3. Verify installation with `poetry run snow`
4. Review this documentation for usage patterns

---

## Developer Information

### Testing the CLI

```bash
# Test help display
poetry run snow

# Test authentication
poetry run snow --token test123token456

# Test status checking
poetry run snow --status

# Test chat launch
poetry run snow --chat

# Test logout
poetry run snow --logout
```

### Extending the CLI

The CLI is designed for extensibility:

- Add new commands in `parse_arguments()`
- Implement handlers in main `snow_main()` function
- Extend authentication in `utils.py`
- Customize branding in `tui.py`

### Architecture Benefits

- **Separation of Concerns**: Authentication wrapper vs AI backend
- **Brand Flexibility**: Easy to modify company branding
- **Security Layer**: Centralized token management
- **User Experience**: Simplified command structure

---

## License

MIT License - See LICENSE file for details

---

_This documentation covers the complete Snowcell CLI implementation. For technical support or feature requests, contact your development team._
