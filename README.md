# Instagram Reel Scraper

A powerful Instagram scraper that extracts reels with 100% accurate metrics (views, likes, comments) using human-like behavior to avoid detection.

## 🌟 Features

- ✅ **100% Accurate Metrics** - Views, likes, and comments extraction
- ✅ **Multi-Profile Scraping** - Scrape multiple Instagram profiles
- ✅ **Saved Posts Extraction** - Auto-finds "content" folder or "All Posts"
- ✅ **Smart Duplicate Detection** - Compares by post ID across all runs
- ✅ **Human-Like Behavior** - Random delays, hover actions, variable scrolling
- ✅ **Session Persistence** - Login once, reuse cookies for future runs
- ✅ **CSV Export** - Clean output with channel, link, views, likes, comments
- ✅ **Reel Downloader** - Bonus tool to download reels from URLs

## 🔒 Security Features

All sensitive data is protected by `.gitignore`:
- 🔐 Instagram cookies (session tokens)
- 🔐 Downloaded reels
- 🔐 CSV data files
- 🔐 Browser profiles
- 🔐 Log files

**⚠️ Never share your `instagram_cookies.json` file - it contains session tokens that can access your account!**

## 📋 Requirements

- Python 3.13+
- Playwright (Chromium browser automation)

## 🚀 Installation

\`\`\`bash
# Clone the repository
git clone https://github.com/yourusername/instagram-reel-scraper.git
cd instagram-reel-scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
\`\`\`

## 📖 Usage

### 1. Scrape Reels with Metrics

\`\`\`bash
source venv/bin/activate
python reel_saver.py
\`\`\`

**Workflow:**
1. **Login** - Uses saved cookies or manual login (first time)
2. **Profile Scraping** - Enter usernames to scrape (or press Enter to skip)
3. **Saved Posts** - Choose to scrape saved posts (automatically finds "content" folder)
4. **Metrics Extraction** - Extracts views from grid, visits each reel for likes/comments
5. **30-Second Timer** - Observe results before auto-close (press Enter to skip)

### 2. Download Reels (Optional)

\`\`\`bash
# Create a file with reel URLs (one per line)
echo "https://www.instagram.com/reel/ABC123/" > reels/content.txt

# Run downloader
python downloader.py
\`\`\`

Videos will be saved to `downloaded_reels/` folder.

## 📊 Output Format

**File:** `reels/reel_metrics.csv`

| Column   | Description              |
|----------|--------------------------|
| channel  | Profile name or "saved"  |
| link     | Full Instagram reel URL  |
| views    | View count               |
| likes    | Like count               |
| comments | Comment count            |

**Example:**
\`\`\`csv
channel,link,views,likes,comments
upsoraduo,https://www.instagram.com/reel/ABC123/,15.2K,1.2K,89
saved,https://www.instagram.com/reel/XYZ789/,8.5K,650,42
\`\`\`

## 🛡️ Anti-Ban Protection

The scraper mimics human behavior to avoid detection:

- **Random Delays** - 1.5-5 seconds between actions
- **Hover Actions** - Hovers before clicking (0.5-1s delay)
- **Variable Scrolling** - Different scroll speeds and distances
- **Gradual Navigation** - Step-by-step navigation (More → Saved → folder)
- **Smart Timing** - Proper wait times after page loads

## ⚠️ Important Notes

1. **Cookies Are Sensitive** - Keep `instagram_cookies.json` private (contains session tokens)
2. **Rate Limiting** - Human-like delays prevent Instagram rate limits
3. **First Run** - Browser will open for manual login, then saves session
4. **Duplicate Detection** - Automatically skips already-scraped reels
5. **Respect Instagram's ToS** - Use responsibly and respect privacy

## 📝 License

MIT License - See LICENSE file for details

## ⚠️ Disclaimer

This tool is for educational purposes only. Users are responsible for complying with Instagram's Terms of Service. The author is not responsible for any misuse or violations.

---

**⭐ If you find this useful, please star the repository!**
