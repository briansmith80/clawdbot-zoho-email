# Security Advisory - Zoho Email Integration v2.2

## Security Fixes (2026-02-12)

This release addresses security issues identified in ClawHub security audit.

### Fixed Vulnerabilities

#### 1. Command Injection in JavaScript Handler (CRITICAL)

**Issue:** The original `email-command.js` used shell command interpolation with user-supplied arguments, allowing potential command injection attacks.

**Attack Example:**
```javascript
/email search "; rm -rf ~; echo "
```

**Fix:** New `email-command-SECURE.js` uses `spawn()` with argument arrays instead of shell interpolation. No shell metacharacters are processed.

**Migration:**
```bash
# Replace vulnerable handler
cp examples/clawdbot-extension/email-command-SECURE.js \
   examples/clawdbot-extension/email-command.js
```

#### 2. Metadata Mismatch (HIGH)

**Issue:** Registry metadata claimed "Required env vars: none" and "Primary credential: none" when ZOHO_EMAIL + ZOHO_PASSWORD or OAuth tokens are actually required.

**Fix:** Updated `clawhub.json` metadata to accurately declare:
- Required environment variables: `ZOHO_EMAIL`
- Primary credential: `oauth2` (with app-password fallback)

#### 3. Insufficient Input Validation (MEDIUM)

**Issue:** No validation of email addresses or search queries.

**Fix:** Added input sanitization:
- Email address format validation
- Shell metacharacter filtering
- Length limits (1000 char max)
- Newline/carriage return removal

#### 4. Token File Permission Enforcement (LOW)

**Issue:** Permissions recommended but not verified on existing token files.

**Fix:** Added automatic permission check and enforcement:
- Checks token file permissions on handler initialization
- Automatically corrects insecure permissions to 0600
- Logs security warnings for visibility

---

## Security Best Practices

### 1. Credential Management

**OAuth2 (Recommended):**
```bash
# Run interactive setup
python3 scripts/oauth-setup.py

# Verify token file permissions
ls -la ~/.clawdbot/zoho-mail-tokens.json  # Should show -rw------- (600)
```

**App Password (Simple):**
```bash
# Use app-specific password, NOT your main Zoho password
export ZOHO_EMAIL="your-email@domain.com"
export ZOHO_PASSWORD="app-specific-password-here"
```

### 2. File Permissions

**Critical files must be secured:**
```bash
# Token file (OAuth2)
chmod 600 ~/.clawdbot/zoho-mail-tokens.json

# Credentials file (app password)
chmod 600 ~/.clawdbot/zoho-credentials.sh
```

**Verify:**
```bash
stat -c "%a %n" ~/.clawdbot/zoho-*
# Output should be: 600 filename
```

### 3. Command Handler Security

**If exposing /email commands to untrusted users:**

1. **Use the secure handler:**
   ```bash
   cp examples/clawdbot-extension/email-command-SECURE.js YOUR_SKILL_PATH/
   ```

2. **Add rate limiting** (not included - implement at bot level)

3. **Restrict command access** to authorized users only

4. **Monitor for abuse:**
   ```javascript
   // Add logging to handler
   console.log(`[AUDIT] User ${userId} executed: /email ${command}`);
   ```

### 4. Network Security

**OAuth setup opens localhost callback:**
- Port: 8080 (or next available)
- Listens only on 127.0.0.1 (not externally accessible)
- Automatically closes after authorization
- Safe on single-user systems

**If running on shared/multi-user server:**
- Use SSH tunnel for OAuth setup
- Or run setup on local machine, then copy token file

---

## Vulnerability Disclosure

Found a security issue? Please report responsibly:

1. **DO NOT** open a public GitHub issue
2. Email: brian@creativestudio.co.za
3. Include: description, impact, proof-of-concept (if applicable)
4. Allow reasonable time for fix before public disclosure

---

## Security Checklist

Before deploying this skill:

- [ ] Using OAuth2 or app-specific password (not main password)
- [ ] Token/credential files have 0600 permissions
- [ ] Using secure command handler (email-command-SECURE.js)
- [ ] Command access restricted to authorized users
- [ ] Audit logging enabled for sensitive operations
- [ ] No hardcoded credentials in code or version control
- [ ] Regular credential rotation policy established

---

## Changelog

**v2.2.0 (2026-02-12)**
- Fixed command injection vulnerability in JS handler
- Added input sanitization and validation
- Added automatic token permission enforcement
- Updated metadata to accurately declare requirements
- Added comprehensive security documentation

**v2.1.0**
- Original release with security issues

---

## References

- [OWASP Command Injection](https://owasp.org/www-community/attacks/Command_Injection)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [OAuth2 Security Best Practices](https://datatracker.ietf.org/doc/html/rfc6819)
