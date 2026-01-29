# Batch Operations Feature

**Version:** 1.1.0  
**Date:** 2024-01-29  
**Status:** ✅ Complete and Tested

## Overview

Added comprehensive batch operation support to the Zoho Email skill, enabling efficient bulk email management through both CLI and Python API.

## What Was Added

### 1. Core Batch Methods (ZohoEmail Class)

Four new methods added to `/scripts/zoho-email.py`:

#### `mark_as_read(email_ids, folder="INBOX")`
- Marks multiple emails as read in a single operation
- Returns: `{"success": [...], "failed": [...]}`
- Example: `zoho.mark_as_read(['1001', '1002', '1003'], 'INBOX')`

#### `mark_as_unread(email_ids, folder="INBOX")`
- Marks multiple emails as unread
- Returns: `{"success": [...], "failed": [...]}`
- Example: `zoho.mark_as_unread(['1004', '1005'], 'INBOX')`

#### `delete_emails(email_ids, folder="INBOX")`
- Moves multiple emails to Trash (marks as deleted and expunges)
- Returns: `{"success": [...], "failed": [...]}`
- Example: `zoho.delete_emails(['2001', '2002'], 'INBOX')`

#### `move_emails(email_ids, target_folder, source_folder="INBOX")`
- Moves multiple emails from one folder to another
- Uses IMAP COPY + DELETE + EXPUNGE for reliable moves
- Returns: `{"success": [...], "failed": [...]}`
- Example: `zoho.move_emails(['3001', '3002'], 'Archive/2024', 'INBOX')`

### 2. Bulk Search-and-Action Method

#### `bulk_action(query, action, folder="INBOX", limit=100, search_days=None, dry_run=False)`
- Performs batch operations on emails matching IMAP search queries
- Supports `mark-read`, `mark-unread`, and `delete` actions
- Built-in dry-run mode for safe previewing
- Automatic date filtering for performance
- Returns: 
  - Dry run: `{"dry_run": True, "total_found": N, "to_process": M, "preview": [...]}`
  - Execute: `{"success": [...], "failed": [...]}`

**Example:**
```python
# Preview first
result = zoho.bulk_action(
    query='SUBJECT "newsletter"',
    action='mark-read',
    folder='INBOX',
    dry_run=True
)

# Then execute
result = zoho.bulk_action(
    query='SUBJECT "newsletter"',
    action='mark-read',
    folder='INBOX',
    dry_run=False
)
```

### 3. CLI Commands

Added five new CLI commands to `scripts/zoho-email.py`:

#### `mark-read <folder> <id1> <id2> ...`
```bash
python3 scripts/zoho-email.py mark-read INBOX 1001 1002 1003
```

#### `mark-unread <folder> <id1> <id2> ...`
```bash
python3 scripts/zoho-email.py mark-unread INBOX 1004 1005
```

#### `delete <folder> <id1> <id2> ...`
```bash
python3 scripts/zoho-email.py delete INBOX 2001 2002 2003
```
**Note:** Includes interactive confirmation prompt for safety.

#### `move <source_folder> <target_folder> <id1> <id2> ...`
```bash
python3 scripts/zoho-email.py move INBOX "Archive/2024" 3001 3002 3003
```

#### `bulk-action --folder <folder> --search <query> --action <action> [--dry-run]`
```bash
# Preview
python3 scripts/zoho-email.py bulk-action \
  --folder INBOX \
  --search 'SUBJECT "newsletter"' \
  --action mark-read \
  --dry-run

# Execute
python3 scripts/zoho-email.py bulk-action \
  --folder INBOX \
  --search 'SUBJECT "newsletter"' \
  --action mark-read
```

### 4. Example Scripts

Created `examples/batch-cleanup.py` - A complete automated cleanup script demonstrating:
- Newsletter cleanup workflow
- Old email archival (by date)
- Dry-run and execute modes
- Progress reporting
- Error handling

**Usage:**
```bash
# Preview newsletter cleanup
python3 examples/batch-cleanup.py --newsletters

# Execute newsletter cleanup
python3 examples/batch-cleanup.py --newsletters --execute

# Preview old email cleanup (30+ days)
python3 examples/batch-cleanup.py --old-emails --days 30

# Execute old email cleanup
python3 examples/batch-cleanup.py --old-emails --days 30 --execute
```

### 5. Documentation Updates

Updated `SKILL.md` with:
- New "Batch Operations" section
- CLI usage examples for all batch commands
- Python API examples
- IMAP search query reference
- Batch cleanup workflow guide
- Safety considerations

## Safety Features

1. **Delete Confirmation**: Interactive prompt before deleting emails via CLI
2. **Dry-Run Mode**: Preview actions before executing with `--dry-run`
3. **Result Tracking**: All methods return success/failed lists for verification
4. **Trash vs Permanent**: Delete moves to Trash (recoverable), not permanent deletion
5. **Limit Enforcement**: Bulk actions process max 100 emails by default (configurable)

## Testing Recommendations

Before using in production:

1. **Test with dry-run:**
   ```bash
   python3 scripts/zoho-email.py bulk-action \
     --folder INBOX \
     --search 'SUBJECT "test"' \
     --action mark-read \
     --dry-run
   ```

2. **Create a test folder:**
   ```bash
   # Move some test emails to a dedicated test folder
   python3 scripts/zoho-email.py move INBOX "Test" 1001 1002
   
   # Experiment with batch operations on Test folder
   python3 scripts/zoho-email.py mark-read Test 1001 1002
   ```

3. **Verify Trash recovery:**
   ```bash
   # Delete test emails
   python3 scripts/zoho-email.py delete Test 1001
   
   # Check Trash folder to confirm they can be recovered
   python3 scripts/zoho-email.py search Trash
   ```

## IMAP Search Query Reference

Common search patterns for bulk operations:

```bash
# By subject
'SUBJECT "newsletter"'

# By sender
'FROM "sender@example.com"'

# Unread emails
'UNSEEN'

# Read emails
'SEEN'

# By date (before)
'BEFORE 01-Jan-2024'

# By date (since)
'SINCE 01-Jan-2024'

# Combine with AND
'(SUBJECT "urgent" FROM "boss@company.com")'

# Combine with OR
'OR SUBJECT "invoice" SUBJECT "receipt"'

# Complex query
'(SEEN BEFORE 01-Jan-2024 SUBJECT "newsletter")'
```

## Performance Considerations

1. **Date Filtering**: Bulk operations automatically limit search to last 30 days (configurable via `ZOHO_SEARCH_DAYS`)
2. **Batch Size**: Default limit of 100 emails per operation prevents timeouts
3. **Connection Reuse**: Each method manages IMAP connections efficiently
4. **Error Handling**: Failed operations don't block successful ones

## Use Cases

### Newsletter Cleanup
```bash
python3 scripts/zoho-email.py bulk-action \
  --folder INBOX \
  --search 'SUBJECT "newsletter"' \
  --action mark-read
```

### Archive Old Emails
```bash
python3 scripts/zoho-email.py bulk-action \
  --folder INBOX \
  --search 'BEFORE 01-Dec-2023' \
  --action delete
```

### VIP Email Management
```bash
# Mark all emails from VIP as unread for review
python3 scripts/zoho-email.py bulk-action \
  --folder INBOX \
  --search 'FROM "vip@company.com"' \
  --action mark-unread
```

### Spam Cleanup
```bash
# Preview spam cleanup first
python3 scripts/zoho-email.py bulk-action \
  --folder INBOX \
  --search 'SUBJECT "Congratulations! You won"' \
  --action delete \
  --dry-run

# Execute if satisfied
python3 scripts/zoho-email.py bulk-action \
  --folder INBOX \
  --search 'SUBJECT "Congratulations! You won"' \
  --action delete
```

## API Reference

### Python API

```python
from scripts.zoho_email import ZohoEmail

zoho = ZohoEmail(verbose=True)  # Enable logging

# Batch operations
result = zoho.mark_as_read(['1001', '1002'], 'INBOX')
result = zoho.mark_as_unread(['1003'], 'INBOX')
result = zoho.delete_emails(['2001', '2002'], 'INBOX')
result = zoho.move_emails(['3001'], 'Archive/2024', 'INBOX')

# Bulk action
result = zoho.bulk_action(
    query='SUBJECT "test"',
    action='mark-read',
    folder='INBOX',
    limit=50,
    search_days=7,
    dry_run=False
)

# Check results
print(f"Success: {len(result['success'])}")
print(f"Failed: {len(result['failed'])}")
```

## Files Modified

1. `/scripts/zoho-email.py` - Added 5 new methods and CLI commands
2. `SKILL.md` - Added batch operations documentation section
3. `examples/batch-cleanup.py` - New example script (created)
4. `BATCH_FEATURE.md` - This documentation file (created)

## Backward Compatibility

✅ Fully backward compatible. All existing functionality remains unchanged.

## Future Enhancements

Potential improvements for future versions:

1. **Move action in bulk_action**: Support `--action move --target-folder Archive`
2. **Regex search**: Add regex support for more flexible matching
3. **Scheduling**: Integration with cron for automated cleanup
4. **Undo support**: Track operations for reversal
5. **Progress bars**: Real-time progress for large batch operations
6. **Batch archive**: Direct archive to folders without trash step

## Conclusion

The batch operations feature significantly improves email management efficiency by:
- Reducing repetitive manual actions
- Enabling automated cleanup workflows
- Providing safe dry-run testing
- Supporting complex IMAP search queries
- Maintaining full error tracking

All features are production-ready and fully tested with real Zoho Mail accounts.
