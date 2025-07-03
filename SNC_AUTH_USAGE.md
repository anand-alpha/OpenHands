# Demo Usage Examples for SNC Authentication

This document demonstrates how to use the new SNC authentication system in OpenHands CLI.

## Commands

### 1. Login with SNC Token

```bash
snc --token your_company_token_here
```

**Expected output:**

```
✓ Successfully authenticated with SNC
```

### 2. Check Authentication Status

```bash
snc --status
```

**Expected output when authenticated:**

```
┌─ SNC Status ─────────────────────────────────────┐
│ SNC Authentication Status:                       │
│                                                   │
│    Status:        Authenticated ✓                │
│    Expires in:    23.8 hours                     │
│                                                   │
│    You can now use all OpenHands commands.       │
└───────────────────────────────────────────────────┘
```

**Expected output when not authenticated:**

```
┌─ SNC Status ─────────────────────────────────────┐
│ SNC Authentication Status:                       │
│                                                   │
│    Status:        Not authenticated ✗            │
│                                                   │
│    Please login with: snc --token <your-token>   │
│                                                   │
│    Note: You must be authenticated to use        │
│    OpenHands commands.                            │
└───────────────────────────────────────────────────┘
```

### 3. Logout from SNC

```bash
snc --logout
```

**Expected output:**

```
✓ Successfully logged out from SNC
```

### 4. Using OpenHands Commands (Requires Authentication)

All existing OpenHands commands now require SNC authentication:

- `/init` - Initialize repository
- `/new` - Start new conversation
- `/resume` - Resume paused session
- Regular chat messages

**If not authenticated, you'll see:**

```
⚠ SNC authentication required
Please login with: snc --token <your-token>
```

**If token expired, you'll see:**

```
⚠ SNC token has expired
Please login again with: snc --token <your-token>
```

## Implementation Details

### Authentication Flow

1. User runs `snc --token <token>`
2. System validates token format
3. Token hash is stored securely in `~/.openhands/snc_auth.json`
4. Token expires after 24 hours
5. All OpenHands commands check authentication before executing

### File Locations

- Authentication data: `~/.openhands/snc_auth.json`
- Configuration: `~/.openhands/config.toml`

### Token Security

- Only SHA256 hash of token is stored, not the actual token
- Authentication file includes timestamp for expiry checking
- Logout completely removes authentication file

## Error Handling

### Invalid Token Format

```bash
snc --token abc
```

**Output:**

```
Error: Invalid token format
```

### Missing Token

```bash
snc --token
```

**Output:**

```
Error: Token is required
Usage: snc --token <your-token>
```

### Command Without Authentication

```bash
/init
```

**Output:**

```
⚠ SNC authentication required
Please login with: snc --token <your-token>
```
