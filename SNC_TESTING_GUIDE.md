# SNC Authentication CLI - Testing Guide

## Overview

The SNC (ServiceNow Company) authentication system has been successfully implemented. Users must now authenticate before accessing OpenHands functionality.

## CLI Commands

### 1. SNC Authentication CLI

The `snc` command handles all authentication operations:

```bash
# Show help and available commands
snc

# Login with authentication token
snc --token <your-company-token>

# Check authentication status
snc --status

# Logout and clear authentication
snc --logout
```

### 2. OpenHands Main CLI

The `openhands` command starts the main CLI (requires authentication):

```bash
# Start OpenHands (requires prior authentication)
openhands
```

## Testing Workflow

### Step 1: Test Help System

```bash
# Show SNC help
poetry run snc
```

**Expected Output:**

```
     ____    _   _    ____
    / ___|  | \ | |  / ___|
    \___ \  |  \| | | |
     ___) | | |\  | | |___
    |____/  |_| \_|  \____|

    ServiceNow Company Authentication

You must authenticate before using OpenHands

SNC Authentication Commands:

• snc --token <token> - Login with your authentication token
• snc --status - Check your authentication status
• snc --logout - Logout and clear authentication

After authentication, you can use: openhands to start the main CLI
```

### Step 2: Test Unauthenticated Status

```bash
# Check status when not authenticated
poetry run snc --status
```

**Expected Output:**

```
[SNC Banner]

┌─────────────────────| SNC Status |─────────────────────┐
│SNC Authentication Status:                             │
│                                                       │
│   Status:        Not authenticated ✗                  │
│                                                       │
│   Please login with: snc --token <your-token>         │
│                                                       │
│   Note: You must be authenticated to use OpenHands    │
│   commands.                                           │
└───────────────────────────────────────────────────────┘
```

### Step 3: Test Authentication

```bash
# Login with a token
poetry run snc --token "company_auth_token_12345"
```

**Expected Output:**

```
[SNC Banner]

Authenticating with token...

✓ Successfully authenticated with SNC

Type openhands to start the main CLI, or run snc --status to check your authentication.
```

### Step 4: Test Authenticated Status

```bash
# Check status after authentication
poetry run snc --status
```

**Expected Output:**

```
[SNC Banner]

┌─────────────────────| SNC Status |─────────────────────┐
│SNC Authentication Status:                             │
│                                                       │
│   Status:        Authenticated ✓                      │
│   Expires in:    24.0 hours                          │
│                                                       │
│   You can now use all OpenHands commands.            │
└───────────────────────────────────────────────────────┘

Type openhands to start the main CLI.
```

### Step 5: Test OpenHands Access (Unauthenticated)

```bash
# First logout
poetry run snc --logout

# Then try to access OpenHands without authentication
poetry run openhands
```

**Expected Output:**

```
[SNC Banner]

⚠ SNC authentication required
Please login with: snc --token <your-token>

Please authenticate first using: snc --token <your-token>
```

### Step 6: Test OpenHands Access (Authenticated)

```bash
# First authenticate
poetry run snc --token "test_token_123"

# Then access OpenHands (this should work and start the main CLI)
poetry run openhands
```

**Expected Output:**

```
[OpenHands CLI starts normally with all functionality available]
```

### Step 7: Test Logout

```bash
# Logout from SNC
poetry run snc --logout
```

**Expected Output:**

```
[SNC Banner]

✓ Successfully logged out from SNC
```

## Installation and Setup

### For Development Testing:

```bash
# Install in development mode
cd /home/hac/code/OpenHands
poetry install

# Test the CLI commands
poetry run snc --help
poetry run snc --token "test123"
poetry run snc --status
poetry run openhands
poetry run snc --logout
```

### For Production Installation:

```bash
# Install the package
pip install openhands-ai

# Use the CLI commands
snc --token <your-company-token>
snc --status
openhands
snc --logout
```

## Security Features

1. **Token Validation**: Only tokens with minimum length and format are accepted
2. **Secure Storage**: Only SHA256 hash of token is stored, never the actual token
3. **Automatic Expiry**: Tokens expire after 24 hours
4. **Clean Logout**: Complete removal of authentication data
5. **Access Control**: All OpenHands commands require valid authentication

## Error Handling

### Invalid Token Format:

```bash
snc --token "abc"
```

Output: `Error: Invalid token format`

### Empty Token:

```bash
snc --token ""
```

Output: `Error: Token is required`

### Expired Token:

When token expires after 24 hours:

```
⚠ SNC token has expired
Please login again with: snc --token <your-token>
```

## File Locations

- **Authentication data**: `~/.openhands/snc_auth.json`
- **Configuration**: `~/.openhands/config.toml`

## Integration Points

The SNC authentication integrates with:

- OpenHands main CLI entry point
- All existing OpenHands commands (`/init`, `/new`, `/resume`, etc.)
- Settings and configuration system
- Help system and command completion

## Success Criteria

✅ **Authentication Required**: Users cannot access OpenHands without authentication
✅ **Token Validation**: Invalid tokens are rejected with clear error messages
✅ **Status Checking**: Users can check their authentication status anytime
✅ **Secure Storage**: Tokens are stored securely with SHA256 hashing
✅ **Automatic Expiry**: Tokens expire after 24 hours
✅ **Clean Logout**: Users can logout and clear authentication
✅ **Clear UX**: Intuitive command structure and helpful error messages
✅ **Backward Compatibility**: Existing OpenHands functionality works after authentication
