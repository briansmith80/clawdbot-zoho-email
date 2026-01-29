# Running App Password Tests

## Quick Start

### 1. Set Your Credentials

```bash
export ZOHO_EMAIL="brian@creativestudio.co.za"
export ZOHO_PASSWORD="your-app-password-here"
```

**Get your app password from Zoho:**
1. Login to [Zoho Mail](https://mail.zoho.com)
2. Settings → Security → App Passwords
3. Generate new password for "Clawdbot"
4. Copy the generated password

### 2. Run the Full Test Suite

```bash
cd /root/clawd/molthub-skills/zoho-email-integration
./test-app-password.sh
```

This will test:
- ✅ Unread count
- ✅ Search inbox
- ✅ Search sent folder
- ✅ Send plain text email
- ✅ Send with verbose mode
- ✅ Send with attachment
- ✅ Authentication status
- ✅ Folder access

All test emails will be sent to: `brian@creativestudio.co.za`

### 3. Manual Testing (Individual Commands)

If you prefer to test each command manually:

```bash
# 1. Check unread count
python3 scripts/zoho-email.py unread --auth password --api-mode imap

# 2. Search emails
python3 scripts/zoho-email.py search "test" --auth password --api-mode imap

# 3. Send test email
python3 scripts/zoho-email.py send \
  brian@creativestudio.co.za \
  "Manual Test" \
  "Testing app password authentication manually" \
  --auth password \
  --api-mode imap

# 4. Send with attachment
echo "Test attachment content" > /tmp/test.txt
python3 scripts/zoho-email.py send \
  brian@creativestudio.co.za \
  "Test with Attachment" \
  "Email with test attachment" \
  --attach /tmp/test.txt \
  --auth password \
  --api-mode imap

# 5. Check authentication status
python3 scripts/zoho-email.py oauth-status --auth password
```

## Expected Results

### Success Output Example

```
=== App Password Authentication Test ===

✓ Credentials detected
  Email: brian@creativestudio.co.za
  Password: abcd****

Running tests...

Testing: Get unread count
Command: python3 'scripts/zoho-email.py' unread --auth password --api-mode imap
Unread: 5
✓ PASSED

Testing: Search emails in inbox
Command: python3 'scripts/zoho-email.py' search 'test' --auth password --api-mode imap
[Search results...]
✓ PASSED

[... more tests ...]

=== Test Results ===
Passed: 8
Failed: 0

🎉 All tests passed! App password authentication is working perfectly.

✓ You can now use app password authentication with:
  --auth password --api-mode imap

✓ Test emails sent to: brian@creativestudio.co.za
```

## Troubleshooting

### "ZOHO_EMAIL environment variable not set"

**Solution:**
```bash
export ZOHO_EMAIL="brian@creativestudio.co.za"
export ZOHO_PASSWORD="your-app-password"
```

### "Authentication failed"

**Possible causes:**
1. Wrong app password
2. IMAP not enabled in Zoho account

**Solution:**
1. Verify app password in Zoho Mail settings
2. Check Settings → Mail Accounts → POP/IMAP Access → Enable IMAP
3. Generate a new app password and try again

### "Connection timeout"

**Solution:**
```bash
export ZOHO_TIMEOUT=60
./test-app-password.sh
```

### Tests pass but no emails received

**Possible causes:**
1. Emails in spam folder
2. Wrong recipient email address
3. Sending delay (check after a few minutes)

**Solution:**
1. Check spam/junk folder in recipient inbox
2. Verify `TEST_EMAIL` or default recipient is correct
3. Send test email to yourself first:
   ```bash
   export TEST_EMAIL="$ZOHO_EMAIL"
   ./test-app-password.sh
   ```

## Custom Test Recipient

To send test emails to a different address:

```bash
export TEST_EMAIL="another-email@example.com"
./test-app-password.sh
```

## Documentation

For complete documentation, see:
- **[APP_PASSWORD_TEST.md](APP_PASSWORD_TEST.md)** - Full guide with troubleshooting
- **[SKILL.md](SKILL.md)** - Complete skill documentation
- **[README.md](README.md)** - Overview and quick start

## Next Steps

Once tests pass:
1. ✅ App password authentication is confirmed working
2. ✅ You can use all commands with `--auth password --api-mode imap`
3. 📚 Review APP_PASSWORD_TEST.md for usage examples
4. 🚀 Consider OAuth2 for better performance (see OAUTH2_SETUP.md)

---

**Ready to test?** Just set your credentials and run `./test-app-password.sh`!
