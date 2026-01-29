# Batch Operations - Quick Reference Card

## CLI Commands

### Mark as Read
```bash
python3 scripts/zoho-email.py mark-read INBOX 1001 1002 1003
```

### Mark as Unread
```bash
python3 scripts/zoho-email.py mark-unread INBOX 1004 1005
```

### Delete (moves to Trash)
```bash
python3 scripts/zoho-email.py delete INBOX 2001 2002 2003
# Asks for confirmation
```

### Move to Folder
```bash
python3 scripts/zoho-email.py move INBOX "Archive/2024" 3001 3002
```

### Bulk Action
```bash
# Always dry-run first!
python3 scripts/zoho-email.py bulk-action \
  --folder INBOX \
  --search 'SUBJECT "newsletter"' \
  --action mark-read \
  --dry-run

# Then execute
python3 scripts/zoho-email.py bulk-action \
  --folder INBOX \
  --search 'SUBJECT "newsletter"' \
  --action mark-read
```

## Python API

```python
from scripts.zoho_email import ZohoEmail

zoho = ZohoEmail()

# Mark as read
result = zoho.mark_as_read(['1001', '1002', '1003'], 'INBOX')

# Mark as unread
result = zoho.mark_as_unread(['1004', '1005'], 'INBOX')

# Delete
result = zoho.delete_emails(['2001', '2002'], 'INBOX')

# Move
result = zoho.move_emails(['3001', '3002'], 'Archive/2024', 'INBOX')

# Bulk action
result = zoho.bulk_action(
    query='SUBJECT "newsletter"',
    action='mark-read',
    folder='INBOX',
    dry_run=True
)

# Check results
print(f"Success: {len(result['success'])}")
print(f"Failed: {len(result['failed'])}")
```

## Common Search Queries

```bash
# By subject
'SUBJECT "invoice"'

# By sender
'FROM "sender@example.com"'

# Unread
'UNSEEN'

# Read
'SEEN'

# Date range
'SINCE 01-Jan-2024'
'BEFORE 01-Jan-2024'

# Combined (AND)
'(SUBJECT "urgent" FROM "boss@company.com")'

# Combined (OR)
'OR SUBJECT "invoice" SUBJECT "receipt"'
```

## Safety Tips

1. ✅ Always use `--dry-run` first for bulk actions
2. ✅ Test on a test folder before production use
3. ✅ Delete moves to Trash (recoverable)
4. ✅ Check Trash folder to recover deleted emails
5. ✅ Result tracking shows success/failed for each operation

## Example Workflows

### Clean up newsletters
```bash
python3 scripts/zoho-email.py bulk-action \
  --folder INBOX \
  --search 'SUBJECT "newsletter"' \
  --action mark-read \
  --dry-run
```

### Archive old emails
```bash
python3 examples/batch-cleanup.py --old-emails --days 30 --execute
```

### Delete spam
```bash
python3 scripts/zoho-email.py bulk-action \
  --folder INBOX \
  --search 'FROM "spam@"' \
  --action delete
```

## Documentation

- `BATCH_FEATURE.md` - Complete feature documentation
- `SKILL.md` - Full usage guide with examples
- `examples/batch-cleanup.py` - Automated cleanup script
- `CHANGELOG.md` - Version history

## Support

All batch operations are part of v1.1.0+ of the Zoho Email skill.
