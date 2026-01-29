# App Password Quick Start Guide

**⚡ Get started in 5 minutes!**

---

## 1️⃣ Get App Password from Zoho (2 minutes)

1. Login to **[Zoho Mail](https://mail.zoho.com)**
2. Click **Settings** (⚙️) → **Security**
3. Scroll to **App Passwords**
4. Click **Generate New Password**
5. Name it: `Clawdbot` or `Email Automation`
6. **Copy the password** (looks like: `abcd1234efgh5678ijkl9012mnop3456`)

⚠️ **Save it now!** You won't see it again.

---

## 2️⃣ Set Credentials (1 minute)

```bash
export ZOHO_EMAIL="brian@creativestudio.co.za"
export ZOHO_PASSWORD="paste-your-app-password-here"
```

**Verify it's set:**
```bash
echo $ZOHO_EMAIL
# Should show: brian@creativestudio.co.za
```

---

## 3️⃣ Run Tests (2 minutes)

```bash
cd /root/clawd/molthub-skills/zoho-email-integration
./test-app-password.sh
```

**Expected result:**
```
✓ All tests passed! 🎉
```

Check **brian@creativestudio.co.za** inbox for 3 test emails.

---

## 4️⃣ Start Using It!

```bash
# Check unread emails
python3 scripts/zoho-email.py unread --auth password --api-mode imap

# Search emails
python3 scripts/zoho-email.py search "keyword" --auth password --api-mode imap

# Send email
python3 scripts/zoho-email.py send \
  recipient@example.com \
  "Subject" \
  "Message body" \
  --auth password \
  --api-mode imap
```

---

## 💡 Remember

**Always include these flags with app password:**
- `--auth password` ← Use password authentication
- `--api-mode imap` ← Use IMAP protocol (app passwords don't support REST API)

---

## 📚 Need More Help?

- **Complete guide:** [APP_PASSWORD_TEST.md](APP_PASSWORD_TEST.md)
- **Run tests:** [RUN_APP_PASSWORD_TESTS.md](RUN_APP_PASSWORD_TESTS.md)
- **Full documentation:** [SKILL.md](SKILL.md)

---

## ❓ Troubleshooting

**"Authentication failed"**
- Check app password is correct
- Verify IMAP is enabled: Zoho Mail → Settings → Mail Accounts → Enable IMAP

**"Connection timeout"**
- Increase timeout: `export ZOHO_TIMEOUT=60`
- Check network connectivity

**"Command not found"**
- Make sure you're in the right directory
- Use full path: `python3 /root/clawd/molthub-skills/zoho-email-integration/scripts/zoho-email.py`

---

## 🎯 Quick Command Reference

```bash
# Unread count
python3 scripts/zoho-email.py unread --auth password --api-mode imap

# Search
python3 scripts/zoho-email.py search "keyword" --auth password --api-mode imap

# Send
python3 scripts/zoho-email.py send to@example.com "Subject" "Body" --auth password --api-mode imap

# Send with attachment
python3 scripts/zoho-email.py send to@example.com "Subject" "Body" \
  --attach file.pdf --auth password --api-mode imap

# Get specific email
python3 scripts/zoho-email.py get INBOX 12345 --auth password --api-mode imap
```

---

**Ready to go!** 🚀

Just get your app password, set the environment variables, and run the test script.

**Total time:** ~5 minutes
