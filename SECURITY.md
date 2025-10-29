# 🔒 Security & Privacy Guide

## ⚠️ CRITICAL - Never Share These Files

### `instagram_cookies.json` - **EXTREME DANGER**

**What it contains:**
- Instagram session tokens
- Authentication credentials
- Login bypass tokens

**If someone gets this file:**
- ✗ They can access your Instagram account **without password**
- ✗ They can post, view DMs, change settings
- ✗ They can stay logged in for weeks/months
- ✗ 2FA won't protect you (session is already authenticated)

**Protection:**
- ✅ Already in `.gitignore` (won't be committed to Git)
- ✅ NEVER share, upload, or email this file
- ✅ Delete if compromised and re-login

---

## 🛡️ Protected by .gitignore

The following are **automatically excluded** from Git:

\`\`\`
instagram_cookies.json          # Session tokens
*.json                          # All JSON files
downloaded_reels/               # Downloaded videos
reels/*.csv                     # Scraped data
chrome_profile/                 # Browser session
playwright_profile/             # Browser session
*.log                          # Log files
\`\`\`

---

## 🔐 Cookie Security Explained

**Why are cookies so dangerous?**

Instagram cookies contain session tokens that are **as powerful as your password**:

| Aspect | Password | Session Cookie |
|--------|----------|----------------|
| Requires password | ✅ Yes | ❌ No |
| Requires 2FA | ✅ Yes | ❌ No (already authenticated) |
| Works from any location | ⚠️ May trigger alerts | ✅ Yes, seamlessly |
| Expiration | ❌ Never | ⏰ Weeks/months |

---

## 🚨 If Your Account Is Compromised

1. **Change password immediately**
2. **Logout all sessions** (Settings → Security → Active Sessions)
3. **Enable 2FA** (Settings → Security → Two-Factor Authentication)
4. **Review recent activity** (Settings → Security → Login Activity)
5. **Delete `instagram_cookies.json`** and create fresh session

---

**Remember: Treat your `instagram_cookies.json` like you treat your password!**

🔒 **This file contains keys to your Instagram account.**
