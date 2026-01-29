# Bulk Action REST API Fix

## Problem
The `bulk-action` command was always falling back to IMAP even when `--api-mode rest` was specified. This caused authentication failures when IMAP credentials weren't available.

## Root Cause
The `bulk_action()` method in the ZohoEmail class (around line 1455) was not checking for REST API mode. It always started with `self.connect_imap()` regardless of the `api_mode` setting.

## Solution
Added REST API support to `bulk_action()` method:

### 1. Created IMAP-to-REST Query Converter
Added `_convert_imap_search_to_rest()` method to translate IMAP search queries to Zoho REST API search syntax:
- `SUBJECT "test"` → `subject:test`
- `FROM "user@example.com"` → `from:user@example.com`
- `BODY "keyword"` → `entire:keyword`
- etc.

### 2. Updated bulk_action() Flow
Modified the method to:
1. Check if `self.api_mode == 'rest'`
2. If REST mode:
   - Convert IMAP query to REST API search syntax
   - Use `self.rest_client.list_messages()` with search query
   - Extract message IDs from REST API results
   - Call appropriate action method (mark_as_read, mark_as_unread, delete)
3. If REST fails or not in REST mode, fall back to IMAP

### 3. Enhanced Dry-Run Output
Added `api_used` field to dry-run results to show which API was used (REST or IMAP).

## Testing

### Dry-Run Test (Successful)
```bash
python3 scripts/zoho-email.py bulk-action --folder INBOX --search 'SUBJECT "test"' --action mark-read --dry-run --api-mode rest --verbose
```
**Result:** ✅ Found 100 emails using REST API, no IMAP fallback

### Live Action Test (Successful)
```bash
python3 scripts/zoho-email.py bulk-action --folder INBOX --search 'SUBJECT "HTML"' --action mark-read --api-mode rest --verbose
```
**Result:** ✅ Marked 7 emails as read using REST API, no IMAP fallback

## Verification
Check verbose output for these indicators of REST API usage:
- "Using REST API for bulk action"
- "Converted search query: ..."
- "Found X emails via REST API"
- "Processing X message IDs via REST API"
- REST API GET/PUT requests shown

## Files Modified
- `/root/clawd/molthub-skills/zoho-email-integration/scripts/zoho-email.py`
  - Added `_convert_imap_search_to_rest()` method
  - Updated `bulk_action()` method to support REST API

## Commit Date
2025-01-XX (subagent fix-bulk-action)
