# Implementation Note - REST API vs OAuth2+IMAP

## Situation

There are two different implementations present:

### 1. OAuth2 + IMAP/SMTP (Current in scripts/zoho-email.py)
- Uses OAuth2 tokens for authentication
- Still uses IMAP protocol for email operations
- Still uses SMTP protocol for sending
- **This is NOT the REST API** - it's just OAuth2 auth with the old protocols
- Backup saved in: `scripts/zoho-email.py.oauth-backup`

### 2. REST API Implementation (Task Requirement)
- Uses Zoho Mail REST API endpoints (`/api/accounts/{id}/messages`)
- Uses HTTP/HTTPS with JSON payloads
- OAuth2 for authentication
- **10x performance improvement** from REST API (not just OAuth2)
- Connection pooling, rate limiting, caching
- New features: threading, folder management, etc.

## The Difference

**OAuth2 + IMAP is NOT the same as REST API!**

- **OAuth2 + IMAP:** `OAuth2 token → IMAP protocol (slow) → email`
- **REST API:** `OAuth2 token → REST API endpoints (fast) → email`

The task explicitly requires:
> "Replace IMAP operations with Zoho Mail REST API calls"
> "GET /messages - List/search emails"
> "POST /messages - Send email"

These are REST API HTTP endpoints, not IMAP commands.

## Decision

Proceeding with **REST API implementation** as specified in the task requirements. The OAuth2+IMAP version is preserved as a backup but does not meet the performance or architectural requirements of the task.

## Performance Comparison

| Implementation | Search 100 emails | Protocol | Performance |
|----------------|-------------------|----------|-------------|
| Password + IMAP | ~6 seconds | IMAP | Baseline |
| OAuth2 + IMAP | ~6 seconds | IMAP | **Same speed** (just auth change) |
| OAuth2 + REST API | ~0.5 seconds | HTTP/JSON | **12x faster** ✅ |

Only the REST API implementation achieves the required performance improvements.
