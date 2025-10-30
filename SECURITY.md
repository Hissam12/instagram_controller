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

```
instagram_cookies.json          # Session tokens
*.json                          # All JSON files
downloaded_reels/               # Downloaded videos
reels/*.csv                     # Scraped data
chrome_profile/                 # Browser session
playwright_profile/             # Browser session
*.log                          # Log files
```

---

## ✅ Safe to Share

These files **can** be shared publicly:
- `reel_saver.py` - Source code
- `downloader.py` - Source code
- `requirements.txt` - Dependencies
- `README.md` - Documentation
- `.gitignore` - Protection config

---

## 🔍 Before Pushing to GitHub

Run this security check:

```bash
# 1. Verify .gitignore is working
git status --ignored

# 2. Confirm sensitive files are NOT tracked
git ls-files | grep -E "cookies|\.csv|downloaded_reels"
# Should return NOTHING

# 3. Check what will be committed
git status
# Should NOT show cookies, CSV, or downloaded_reels
```

---

## 🚨 If You Accidentally Committed Sensitive Files

**DON'T JUST DELETE** - The history still contains them!

1. **Immediately:**
   - Change your Instagram password
   - Logout from all devices
   - Enable 2FA if not already enabled

2. **Clean Git history:**
   ```bash
   # Use git-filter-repo (recommended)
   pip install git-filter-repo
   git filter-repo --path instagram_cookies.json --invert-paths
   
   # Force push to overwrite remote
   git push --force
   ```

3. **Create new session:**
   - Delete `instagram_cookies.json`
   - Run scraper to create fresh session

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

**Example Attack Scenario:**
1. Attacker gets your `instagram_cookies.json`
2. They copy cookies to their browser
3. They visit instagram.com
4. **They're instantly logged in as YOU** - no password needed!

---

## 📋 Security Checklist

Before sharing your project:

- [ ] `.gitignore` exists and is complete
- [ ] `instagram_cookies.json` is NOT in Git
- [ ] No CSV files in Git
- [ ] No downloaded reels in Git
- [ ] Browser profiles excluded
- [ ] Ran `git status --ignored` to verify
- [ ] Tested clone in new directory

---

## 🛠️ Quick Security Test

Run this to verify protection:

```bash
# Should show NO sensitive files being tracked
git ls-files | grep -E "cookies|csv|downloaded|profile|\.log"

# Should be empty output - if you see files, they're NOT protected!
```

---

## 💡 Best Practices

1. **Session Rotation**
   - Delete cookies file every few weeks
   - Re-login to get fresh session

2. **Access Control**
   - Don't share your project folder
   - Use private repositories on GitHub

3. **Monitor Activity**
   - Check Instagram login sessions regularly
   - Look for unknown devices/locations

4. **Local Only**
   - Keep sensitive data on local machine only
   - Don't sync to cloud storage (Dropbox, iCloud, etc.)

---

## 📞 If Your Account Is Compromised

1. **Change password immediately**
2. **Logout all sessions** (Settings → Security → Active Sessions)
3. **Enable 2FA** (Settings → Security → Two-Factor Authentication)
4. **Review recent activity** (Settings → Security → Login Activity)
5. **Delete `instagram_cookies.json`** and create fresh session

---

## ⚖️ Legal & Ethical

- **Respect Privacy** - Don't scrape private accounts without permission
- **Follow Instagram ToS** - Use responsibly
- **Rate Limiting** - Don't abuse Instagram's servers
- **Copyright** - Downloaded content may be copyrighted

---

**Remember: Treat your `instagram_cookies.json` like you treat your password!**

🔒 **This file contains keys to your Instagram account.**
