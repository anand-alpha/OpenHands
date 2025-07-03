# Snowcell CLI - Complete Implementation

## Overview

The Snowcell CLI (`snc`) is a company-specific authentication wrapper for OpenHands AI Assistant. It provides Snowcell branding and requires user authentication before allowing access to the full AI assistant capabilities.

## Key Features

1. **Snowcell Branding**: All interfaces use Snowcell company branding and messaging
2. **Authentication Required**: Users must authenticate with a token before accessing the AI assistant
3. **Token Management**: Secure token storage with 24-hour expiration
4. **Real AI Chat**: After authentication, users access the full OpenHands AI assistant (not demo mode)
5. **No OpenHands Commands**: Only Snowcell-specific commands are exposed to users

## Installation

```bash
cd /path/to/OpenHands
poetry install
```

## Usage

### 1. Authentication (Login)

```bash
snc --token <your-token>
```

- Authenticates with Snowcell
- Stores token securely (hashed)
- Automatically launches AI chat interface after successful login

### 2. Check Status

```bash
snc --status
```

- Shows authentication status
- Displays time remaining before token expires
- Indicates if ready to start chat

### 3. Start Chat Session

```bash
snc --chat
```

- Starts AI chat interface (requires authentication)
- Launches full OpenHands AI assistant
- Provides real AI capabilities, not demo mode

### 4. Logout

```bash
snc --logout
```

- Clears authentication token
- Ends current session

### 5. Help

```bash
snc
```

- Shows available commands and usage information

## Implementation Details

### Core Files

1. **`openhands/cli/snowcell_cli.py`** - Main Snowcell CLI entry point

   - Handles command parsing and authentication flow
   - Provides Snowcell branding and messaging
   - Launches OpenHands AI assistant after authentication

2. **`openhands/cli/utils.py`** - Authentication utilities

   - Token storage and validation
   - Authentication status checking
   - Security functions (hashing, expiration)

3. **`pyproject.toml`** - Package configuration
   - Entry point: `snc = "openhands.cli.snowcell_cli:main"`
   - Dependencies and scripts

### Authentication System

- **Token Storage**: Tokens are hashed (SHA256) and stored in `~/.openhands/snc_auth.json`
- **Expiration**: Tokens expire after 24 hours
- **Security**: Only token hash is stored, not the actual token
- **Status Tracking**: Active/inactive status with timestamp

### User Experience Flow

1. User runs `snc --token <token>`
2. System validates and stores token
3. Shows "Successfully authenticated" message
4. Automatically launches "🚀 Starting Snowcell AI Assistant..."
5. User enters full OpenHands AI chat interface
6. All interaction is with real AI assistant, not demo mode

## Example Session

```bash
$ snc --token abc123token456

     ____                                    _ _
    / ___| _ __   _____      _____ ___ _ __ | | |
    \___ \| '_ \ / _ \ \ /\ / / __/ _ \ '_ \| | |
     ___) | | | | (_) \ V  V / (_|  __/ | | | | |
    |____/|_| |_|\___/ \_/\_/ \___\___|_| |_|_|_|

    Snowcell AI Assistant


Your intelligent AI-powered assistant

Authenticating with Snowcell...

✓ Successfully authenticated with Snowcell!

🎉 Welcome to Snowcell AI Assistant!
Starting AI chat interface...

🚀 Starting Snowcell AI Assistant...

[OpenHands AI interface launches with full capabilities]
```

## Key Benefits

1. **Company Branding**: Users see only Snowcell branding, not OpenHands
2. **Security**: Authentication required before access
3. **Real AI**: Full OpenHands AI assistant capabilities, not limited demo
4. **Simple UX**: One command authentication and chat launch
5. **Token Management**: Secure storage with automatic expiration

## Testing

```bash
# Test help
poetry run snc

# Test authentication
poetry run snc --token test123token456

# Test status
poetry run snc --status

# Test chat (after authentication)
poetry run snc --chat

# Test logout
poetry run snc --logout
```

## Comparison: Before vs After

### Before (OpenHands Direct)

- Users run `openhands` command
- No authentication required
- OpenHands branding everywhere
- Direct access to all OpenHands features

### After (Snowcell CLI)

- Users run `snc` command only
- Authentication required via `snc --token`
- Snowcell branding for auth flow
- Real OpenHands AI after authentication
- No OpenHands commands exposed to users

## Notes

- The AI assistant functionality is fully powered by OpenHands backend
- Authentication is Snowcell-specific wrapper layer
- Users get real AI capabilities, not demo/simulation
- All OpenHands features available after authentication
- Token security with 24-hour expiration policy
