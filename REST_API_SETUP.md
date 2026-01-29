# Zoho Mail REST API Setup Guide

Complete guide to setting up Zoho Mail REST API access for the Zoho Email skill.

## Why REST API?

**10x Performance Improvement:**
- ⚡ Faster searches (API-side filtering vs downloading all emails)
- 🔄 Connection pooling (persistent connections vs reconnecting every time)
- 📦 Batch operations (multiple actions in one request)
- ⏱️ Lower latency (REST vs IMAP protocol overhead)

**New Features:**
- 📧 Email threading/conversations
- 🏷️ Labels and tags
- 🔍 Advanced search filters
- 📁 Folder management (create/rename/delete)
- 🔔 Webhook support (real-time notifications)
- 📊 Better metadata (importance, flags, categories)

## Prerequisites

- Zoho Mail account (free or paid)
- Admin access to Zoho API Console
- 5-10 minutes to complete setup

## Step-by-Step Setup

### 1. Register Your Application

1. Go to [Zoho API Console](https://api-console.zoho.com/)
2. Click "Add Client" (or "Get Started")
3. Choose "Server-based Applications"
4. Fill in the details:
   - **Client Name:** `Clawdbot Zoho Email`
   - **Homepage URL:** `http://localhost` (or your domain)
   - **Authorized Redirect URIs:** `http://localhost:8080/callback`
5. Click "Create"
6. **Save your Client ID and Client Secret** (you'll need these later)

### 2. Generate Authorization Code

The authorization code is used to get your initial access token.

**Build the authorization URL:**

```
https://accounts.zoho.com/oauth/v2/auth?
  scope=ZohoMail.messages.ALL,ZohoMail.folders.ALL,ZohoMail.accounts.READ&
  client_id=YOUR_CLIENT_ID&
  response_type=code&
  access_type=offline&
  redirect_uri=http://localhost:8080/callback
```

**Replace `YOUR_CLIENT_ID`** with your actual Client ID.

**Steps:**
1. Open the URL in your browser
2. Log in to Zoho if needed
3. **Click "Accept"** to grant permissions
4. You'll be redirected to: `http://localhost:8080/callback?code=AUTHORIZATION_CODE`
5. **Copy the `code=...` value** (this is your authorization code)

⚠️ **Important:** The authorization code expires in 5 minutes! Use it immediately.

### 3. Exchange Authorization Code for Tokens

Use the authorization code to get your access token and refresh token:

```bash
curl -X POST https://accounts.zoho.com/oauth/v2/token \
  -d "code=YOUR_AUTHORIZATION_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=http://localhost:8080/callback" \
  -d "grant_type=authorization_code"
```

**Response:**
```json
{
  "access_token": "1000.abc123...",
  "refresh_token": "1000.def456...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

**Save both tokens!** The refresh token never expires (unless revoked).

### 4. Configure Environment Variables

Add these to your shell profile (`~/.bashrc`, `~/.zshrc`) or credentials file:

```bash
# Zoho REST API credentials
export ZOHO_EMAIL="your-email@domain.com"
export ZOHO_CLIENT_ID="1000.ABC123..."
export ZOHO_CLIENT_SECRET="xyz789..."
export ZOHO_ACCESS_TOKEN="1000.abc123..."
export ZOHO_REFRESH_TOKEN="1000.def456..."

# Optional: Custom API base URL (for self-hosted Zoho)
export ZOHO_API_BASE_URL="https://mail.zoho.com/api"
export ZOHO_ACCOUNTS_URL="https://accounts.zoho.com"
```

**Reload your shell:**
```bash
source ~/.bashrc  # or ~/.zshrc
```

### 5. Test REST API Access

```bash
python3 scripts/zoho-email.py api-status --api rest -v
```

**Expected output:**
```json
{
  "api_mode": "rest",
  "rest_api_available": true,
  "imap_smtp_available": true
}
```

**Test basic functionality:**
```bash
# List folders
python3 scripts/zoho-email.py folders --api rest

# Check unread count
python3 scripts/zoho-email.py unread --api rest

# Search emails
python3 scripts/zoho-email.py search "test" --api rest
```

## OAuth Token Management

### Access Token Lifetime

- **Access tokens** expire after 1 hour
- The script **auto-refreshes** them using the refresh token
- You only need to do the OAuth flow once

### Refresh Token Manually

If you need to manually refresh:

```bash
curl -X POST https://accounts.zoho.com/oauth/v2/token \
  -d "refresh_token=YOUR_REFRESH_TOKEN" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "grant_type=refresh_token"
```

### Revoking Tokens

If compromised, revoke tokens at:
[Zoho Accounts - Connected Apps](https://accounts.zoho.com/home#security/connectedapps)

Then repeat the setup process to generate new tokens.

## API Scopes

The script requires these scopes:

- `ZohoMail.messages.ALL` - Read, send, modify, delete messages
- `ZohoMail.folders.ALL` - Read, create, rename, delete folders
- `ZohoMail.accounts.READ` - Read account information

If you need fewer permissions, adjust the scope in the authorization URL.

## API Rate Limits

**Zoho Mail API Limits:**
- **Free tier:** 500 requests/day
- **Paid tier:** 2,500 requests/day
- **Enterprise:** Custom limits

**Built-in Rate Limiting:**
The script includes:
- 0.5 second delay between requests (configurable)
- Automatic retry on 429 (rate limit exceeded)
- Connection pooling to reduce overhead

**Configure rate limiting:**
```bash
export ZOHO_API_RATE_DELAY=0.5  # Seconds between requests
export ZOHO_MAX_RETRIES=3       # Max retries on failure
```

## Troubleshooting

### "401 Unauthorized"

**Cause:** Expired or invalid access token

**Fix:**
1. Check that `ZOHO_REFRESH_TOKEN` is set
2. The script will auto-refresh the token
3. If it fails, manually refresh (see above)
4. Worst case: Regenerate tokens from scratch

### "Invalid Client"

**Cause:** Wrong Client ID or Client Secret

**Fix:**
1. Verify credentials in Zoho API Console
2. Make sure no extra spaces in environment variables
3. Regenerate client credentials if needed

### "Scope Mismatch"

**Cause:** App doesn't have required permissions

**Fix:**
1. Go through OAuth flow again with correct scopes
2. Make sure authorization URL includes all required scopes

### "requests library not found"

**Cause:** Python `requests` module not installed

**Fix:**
```bash
pip3 install -r requirements.txt
```

### API is slow / timing out

**Possible causes:**
- Network issues
- Zoho API downtime
- Rate limiting

**Fix:**
1. Check Zoho Mail API status: https://status.zoho.com/
2. Increase timeout: `export ZOHO_API_TIMEOUT=60`
3. Fall back to IMAP: `--api imap`

## Security Best Practices

✅ **DO:**
- Store tokens in environment variables
- Keep credentials file (`~/.zoho-credentials`) with `chmod 600`
- Use separate OAuth app per deployment
- Rotate tokens regularly
- Revoke unused apps

❌ **DON'T:**
- Commit tokens to Git (add to `.gitignore`)
- Share tokens between users
- Use tokens in public logs
- Store tokens in plain text files with open permissions

## Multi-Account Setup

To manage multiple Zoho accounts:

**Option 1: Multiple credential files**
```bash
# Account 1
source ~/.zoho-account1.sh
python3 scripts/zoho-email.py unread

# Account 2
source ~/.zoho-account2.sh
python3 scripts/zoho-email.py unread
```

**Option 2: Python wrapper**
```python
import os
from scripts.zoho_email import ZohoEmail

# Account 1
os.environ['ZOHO_EMAIL'] = 'account1@domain.com'
os.environ['ZOHO_ACCESS_TOKEN'] = '...'
zoho1 = ZohoEmail(api_mode='rest')

# Account 2
os.environ['ZOHO_EMAIL'] = 'account2@domain.com'
os.environ['ZOHO_ACCESS_TOKEN'] = '...'
zoho2 = ZohoEmail(api_mode='rest')
```

## Migration from IMAP/SMTP

See [REST_API_MIGRATION.md](REST_API_MIGRATION.md) for detailed migration guide.

**Quick migration:**
1. Complete this setup guide
2. Set environment variables
3. Test with `--api rest` flag
4. Once working, it becomes default (auto mode)

**You can always fall back to IMAP:**
```bash
python3 scripts/zoho-email.py search "test" --api imap
```

## API Endpoints Reference

The script uses these Zoho Mail API endpoints:

- `GET /accounts/{accountId}/messages` - List messages
- `GET /accounts/{accountId}/messages/{messageId}` - Get message
- `POST /accounts/{accountId}/messages` - Send message
- `PATCH /accounts/{accountId}/messages/{messageId}` - Update message
- `DELETE /accounts/{accountId}/messages/{messageId}` - Delete message
- `GET /accounts/{accountId}/folders` - List folders
- `POST /accounts/{accountId}/folders` - Create folder
- `PUT /accounts/{accountId}/folders/{folderId}` - Rename folder
- `DELETE /accounts/{accountId}/folders/{folderId}` - Delete folder
- `GET /accounts/{accountId}/threads` - Get conversation threads

Full API documentation: https://www.zoho.com/mail/help/api/

## Support

**Issues with setup?**
- Check Zoho Mail API status: https://status.zoho.com/
- Review Zoho API documentation: https://www.zoho.com/mail/help/api/
- File an issue in the skill repository

**Need help with OAuth?**
- Zoho OAuth Guide: https://www.zoho.com/accounts/protocol/oauth.html
- Common OAuth errors: https://www.zoho.com/accounts/protocol/oauth/error-codes.html

---

**Setup Complete! 🎉**

You're now ready to use the REST API for 10x faster email operations!

Next steps:
- Read [REST_API_FEATURE.md](REST_API_FEATURE.md) for feature documentation
- Check [REST_API_MIGRATION.md](REST_API_MIGRATION.md) for migration tips
- Explore new features like threading and folder management
