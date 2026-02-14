# Security Best Practices for Future Development

This document outlines recommended security practices for ongoing development of the BirdQuiz project.

## Git Configuration for Privacy

### Protecting Your Email Address in Future Commits

If you prefer to keep your email address private in future commits:

1. **Enable GitHub Email Privacy:**
   - Go to GitHub Settings → Emails
   - Check "Keep my email addresses private"
   - Check "Block command line pushes that expose my email"

2. **Update Git Configuration:**
   ```bash
   git config --global user.email "username@users.noreply.github.com"
   ```
   Replace `username` with your GitHub username.

3. **For This Repository Only:**
   ```bash
   git config user.email "username@users.noreply.github.com"
   ```

### Note on Existing Commits
- Existing commits will retain the current email address
- This is normal and acceptable for public repositories
- Changing historical commits would require rewriting git history (not recommended)

---

## Environment Variables Checklist

Before committing, always verify:

- [ ] No `.env` file is committed
- [ ] `.env.example` contains only placeholders
- [ ] All sensitive values use `os.getenv()` or similar
- [ ] `.gitignore` includes `.env`, `.env.local`, etc.

---

## Pre-Commit Security Checks

Consider adding a pre-commit hook to catch potential issues:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for potential secrets
if git diff --cached --name-only | xargs grep -E -i "(password|api_key|secret|token|private_key).*=.*['\"].*['\"]"; then
    echo "⚠️  Potential secret detected! Please review before committing."
    exit 1
fi

# Check for .env files
if git diff --cached --name-only | grep -E "^\.env$"; then
    echo "⚠️  .env file detected! This should not be committed."
    exit 1
fi

exit 0
```

To install:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Recommended Tools

### 1. git-secrets
Prevents committing secrets and credentials:
```bash
# Install
brew install git-secrets  # macOS
# or download from: https://github.com/awslabs/git-secrets

# Setup for this repo
git secrets --install
git secrets --register-aws
```

### 2. detect-secrets
Baseline secret scanning:
```bash
pip install detect-secrets
detect-secrets scan > .secrets.baseline
```

### 3. GitHub Secret Scanning
- Already enabled for public repositories
- Automatically detects common credential patterns
- Will alert you if secrets are detected

---

## Production Deployment Checklist

Before deploying to production:

- [ ] Set `debug=False` in Flask app
- [ ] Use production-grade WSGI server (Gunicorn, uWSGI)
- [ ] Enable HTTPS/TLS
- [ ] Implement rate limiting
- [ ] Set up monitoring and logging
- [ ] Review Azure OpenAI usage limits and costs
- [ ] Configure proper CORS policies if needed
- [ ] Set secure session cookies (if using sessions)
- [ ] Keep dependencies updated (use Dependabot)

---

## Code Review Guidelines

When reviewing code changes, check for:

1. **Credentials:** No hardcoded passwords, keys, or tokens
2. **File Paths:** Validate and sanitize user-provided paths
3. **API Endpoints:** No internal/private URLs
4. **Error Messages:** Don't expose sensitive system information
5. **Logging:** Don't log sensitive data (tokens, passwords, PII)

---

## Incident Response

If a secret is accidentally committed:

1. **Immediately rotate the compromised credential**
2. **Remove from current code** (if still present)
3. **Consider rewriting history** for recent commits (within 24 hours)
4. **For older commits:** Document in security audit and rotate credentials
5. **Enable GitHub secret scanning alerts**

### Quick Secret Rotation:
- Azure OpenAI: Regenerate API key in Azure Portal (if using key-based auth)
- Or: Revoke Azure AD permissions temporarily

---

## Additional Resources

- [GitHub Security Best Practices](https://docs.github.com/en/code-security/getting-started/securing-your-repository)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Azure Security Best Practices](https://learn.microsoft.com/en-us/azure/security/fundamentals/best-practices-and-patterns)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

## Current Security Status

✅ **All security best practices currently implemented:**
- Environment variables for configuration
- Azure AD authentication (no API keys)
- Proper .gitignore configuration
- No hardcoded secrets
- Public APIs only
- Clear documentation

**Keep up the good work!** 🎉
