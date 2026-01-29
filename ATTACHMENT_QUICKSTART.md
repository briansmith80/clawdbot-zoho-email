# Attachment Quick Reference

> **New in v1.1.0:** Full attachment support - send and receive attachments with ease!

## 📤 Sending Attachments

### CLI
```bash
# Single attachment
python3 scripts/zoho-email.py send \
  "client@example.com" \
  "Invoice #123" \
  "Please find your invoice attached" \
  --attach invoice.pdf

# Multiple attachments
python3 scripts/zoho-email.py send \
  "client@example.com" \
  "Monthly Report" \
  "Report and charts attached" \
  --attach report.pdf \
  --attach chart1.png \
  --attach chart2.png
```

### Python
```python
from scripts.zoho_email import ZohoEmail

zoho = ZohoEmail()
zoho.send_email_with_attachment(
    to="client@example.com",
    subject="Invoice",
    body="Please see attached",
    attachments=["invoice.pdf", "receipt.jpg"]
)
```

---

## 📥 Receiving Attachments

### Step 1: List attachments
```bash
python3 scripts/zoho-email.py list-attachments Inbox 4590
```

**Output:**
```json
[
  {
    "index": 0,
    "filename": "invoice.pdf",
    "content_type": "application/pdf",
    "size": 52341
  }
]
```

### Step 2: Download attachment
```bash
# Download with original filename
python3 scripts/zoho-email.py download-attachment Inbox 4590 0

# Download with custom filename
python3 scripts/zoho-email.py download-attachment Inbox 4590 0 my-invoice.pdf
```

---

## 🤖 Automation Examples

### Download all PDFs from inbox
```bash
#!/bin/bash
EMAILS=$(python3 scripts/zoho-email.py search "invoice")

echo "$EMAILS" | jq -r '.[].id' | while read EMAIL_ID; do
  ATTACHMENTS=$(python3 scripts/zoho-email.py list-attachments Inbox "$EMAIL_ID")
  
  echo "$ATTACHMENTS" | jq -r '.[] | select(.content_type == "application/pdf") | .index' | while read INDEX; do
    python3 scripts/zoho-email.py download-attachment Inbox "$EMAIL_ID" "$INDEX"
  done
done
```

### Send daily report with attachments
```bash
#!/bin/bash
# Generate report
./generate_report.sh > report.txt

# Send with attachment
python3 scripts/zoho-email.py send \
  "manager@example.com" \
  "Daily Report - $(date +%Y-%m-%d)" \
  "Please find today's report attached" \
  --attach report.txt \
  --attach chart.png
```

---

## 🐍 Python Automation

```python
from scripts.zoho_email import ZohoEmail

zoho = ZohoEmail()

# Download all attachments from an email
email_id = "4590"
attachments = zoho.get_attachments(folder="INBOX", email_id=email_id)

for att in attachments:
    print(f"Downloading {att['filename']}...")
    zoho.download_attachment(
        folder="INBOX",
        email_id=email_id,
        attachment_index=att['index'],
        output_path=f"downloads/{att['filename']}"
    )
```

---

## 💡 Pro Tips

1. **Use `list-attachments` first** to see what's available before downloading
2. **Attachment index starts at 0** (first attachment is index 0)
3. **Multiple `--attach` flags** for multiple files when sending
4. **Original filename preserved** unless you specify output_path
5. **Works with all file types** - PDFs, images, documents, etc.

---

## 🎯 Common Use Cases

### Invoice Management
```bash
# Download invoices automatically
python3 scripts/zoho-email.py search "invoice" | \
  jq -r '.[].id' | \
  xargs -I {} python3 scripts/zoho-email.py list-attachments Inbox {}
```

### Document Collection
```python
# Collect all attachments from recent emails
emails = zoho.search_emails(folder="INBOX", limit=20)
for email in emails:
    attachments = zoho.get_attachments("INBOX", email['id'])
    for att in attachments:
        zoho.download_attachment("INBOX", email['id'], att['index'])
```

### Automated Responses with Files
```bash
# Send confirmation with attachment
python3 scripts/zoho-email.py send \
  "$CLIENT_EMAIL" \
  "Order Confirmation" \
  "Thank you! Your receipt is attached." \
  --attach "receipt_$ORDER_ID.pdf"
```

---

## 🧪 Testing

Run the interactive demo:
```bash
cd examples/
python3 attachment-demo.py
```

Choose:
1. Send email with attachments
2. List and download attachments from inbox
3. Both demos

---

## 📚 Full Documentation

- **Feature details:** `ATTACHMENT_FEATURE.md`
- **Complete guide:** `SKILL.md`
- **Implementation:** `IMPLEMENTATION_SUMMARY.md`

---

**Quick Help:**
```bash
python3 scripts/zoho-email.py
```

Shows all commands including attachment commands.
