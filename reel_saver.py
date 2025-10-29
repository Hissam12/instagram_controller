"""
Instagram Reel Scraper - Optimized Version
Scrapes reel links with metrics (views, likes, comments) from profiles and saved posts.
Includes automatic login, duplicate detection, and CSV export.
"""
import asyncio
import json
import os
import random
import logging
import re
import csv
from datetime import datetime
from playwright.async_api import async_playwright

# Configuration
COOKIES_FILE = 'instagram_cookies.json'
OUTPUT_DIR = 'reels'
OUTPUT_CSV = 'reels/reel_metrics.csv'  # Single CSV file
LOG_FILE = 'reel_saver.log'
HEADLESS_MODE = False
MAX_SCROLLS = 50
MAX_RETRIES = 3
FINAL_TIMER = 30  # 30 second observation at the end

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8')]
)
logger = logging.getLogger(__name__)

# Global for tracking existing URLs
EXISTING_URLS = set()

# ==================== UTILITY FUNCTIONS ====================

def extract_post_id(url):
    """Extract unique post ID from URL."""
    match = re.search(r'/(?:p|reel|tv)/([^/?]+)', url)
    return match.group(1) if match else None

async def human_like_delay(min_sec=1.5, max_sec=3.0):
    """Random delay to mimic human behavior."""
    await asyncio.sleep(min_sec + (max_sec - min_sec) * random.random())

async def retry_operation(operation, max_retries=MAX_RETRIES, operation_name="operation"):
    """Retry an async operation with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed {operation_name} after {max_retries} attempts: {e}")
                raise
            wait_time = 2 ** attempt
            logger.warning(f"{operation_name} attempt {attempt + 1} failed, retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)

async def handle_popups(page):
    """Close common Instagram popups."""
    try:
        close_buttons = [
            'button:has-text("Not Now")',
            'button:has-text("Not now")',
            'button:has-text("Cancel")',
            'svg[aria-label="Close"]'
        ]
        for selector in close_buttons:
            try:
                btn = page.locator(selector).first
                if await btn.count() > 0:
                    await btn.click(timeout=2000)
                    await asyncio.sleep(0.5)
            except:
                pass
    except:
        pass

# ==================== COOKIE MANAGEMENT ====================

async def save_cookies(context, path):
    """Save browser cookies to file."""
    try:
        cookies = await context.cookies()
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, 'w') as f:
            json.dump(cookies, f, indent=2)
        logger.info(f"Saved session to {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save cookies: {e}")
        return False

async def load_cookies(context, path):
    """Load cookies from file."""
    try:
        if not os.path.exists(path):
            return False
        with open(path, 'r') as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        logger.info(f"Loaded session from {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to load cookies: {e}")
        return False

# ==================== LOGIN ====================

async def perform_login(page, context):
    """Handle manual login and save session."""
    print("\n" + "="*70)
    print("MANUAL LOGIN REQUIRED")
    print("="*70)
    print("A browser window has opened. Please log in to Instagram.")
    print("After successful login, press ENTER here to continue...")
    print("="*70)
    
    async def navigate():
        await page.goto('https://www.instagram.com', timeout=30000)
    
    await retry_operation(navigate, operation_name="Instagram navigation")
    
    input()  # Wait for user
    
    if "login" in page.url.lower():
        print("⚠ Still on login page. Please ensure you're logged in.")
        return False
    
    if await save_cookies(context, COOKIES_FILE):
        print("✓ Login successful! Session saved.\n")
        return True
    
    print("⚠ Login appeared successful but couldn't save session.\n")
    return False

# ==================== METRIC EXTRACTION ====================

async def extract_views_from_grid(link_element):
    """Extract views from grid using aria-label (100% accurate)."""
    try:
        spans = await link_element.locator('span').all()
        for span in spans:
            text = await span.text_content()
            if not text or not re.search(r'\d', text.strip()):
                continue
            
            current = span
            for _ in range(4):  # Check up to 4 parent levels
                try:
                    html = await current.evaluate('el => el.outerHTML')
                    html_lower = html.lower()
                    
                    if 'view' in html_lower and 'aria-label' in html_lower:
                        match = re.search(r'aria-label="([^"]*)"', html, re.IGNORECASE)
                        if match and 'view' in match.group(1).lower():
                            num_match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)', text.strip())
                            if num_match:
                                return num_match.group(1)
                    current = current.locator('xpath=..')
                except:
                    break
    except:
        pass
    return "N/A"

async def extract_metrics_from_meta(page):
    """Extract likes/comments from meta tags (100% accurate)."""
    result = {'likes': 'N/A', 'comments': 'N/A'}
    try:
        meta = page.locator('meta[property="og:description"]').first
        if await meta.count() > 0:
            content = await meta.get_attribute('content')
            if content:
                likes_match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)\s+likes?', content, re.IGNORECASE)
                comments_match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)\s+comments?', content, re.IGNORECASE)
                
                if likes_match:
                    result['likes'] = likes_match.group(1)
                    logger.info(f"Found likes: {result['likes']}")
                if comments_match:
                    result['comments'] = comments_match.group(1)
                    logger.info(f"Found comments: {result['comments']}")
    except Exception as e:
        logger.debug(f"Meta tag extraction failed: {e}")
    return result

# ==================== SCROLLING & COLLECTION ====================

async def scroll_and_collect_links(page, is_saved_posts=False):
    """
    Dynamically scrapes reels by alternating between scraping and scrolling.
    Uses human-like delays to avoid detection.
    """
    global EXISTING_URLS
    
    print("   → Dynamically scraping reels (with human-like delays)...")
    
    all_reels = []
    processed_urls = set()
    consecutive_no_new_reels = 0
    scroll_count = 0
    
    # Build set of existing post IDs for better duplicate detection
    existing_post_ids = set()
    for url in EXISTING_URLS:
        post_id = extract_post_id(url)
        if post_id:
            existing_post_ids.add(post_id)
    
    print(f"   📊 Loaded {len(existing_post_ids)} existing post IDs for duplicate detection")
    
    while scroll_count < MAX_SCROLLS and consecutive_no_new_reels < 3:
        # Human delay before checking for reels
        await human_like_delay(1.5, 2.5)
        
        # Get current reel links on page
        link_elements = await page.locator('a[href*="/reel/"], a[href*="/p/"], a[href*="/tv/"]').all()
        
        new_reels_found = 0
        duplicates_found = 0
        
        # Process current batch of links
        for link in link_elements:
            try:
                href = await link.get_attribute('href')
                if not href or href in processed_urls:
                    continue
                
                processed_urls.add(href)
                
                reel_id = extract_post_id(href)
                if not reel_id:
                    continue
                
                url = f"https://www.instagram.com{href}" if href.startswith('/') else href
                
                # Check for duplicates using post ID (more reliable than URL)
                if reel_id in existing_post_ids or url in EXISTING_URLS:
                    duplicates_found += 1
                    logger.debug(f"Skipping duplicate: {reel_id}")
                    continue
                
                # Extract views from grid
                views = await extract_views_from_grid(link)
                
                all_reels.append({
                    'reel_id': reel_id,
                    'url': url,
                    'views': views
                })
                new_reels_found += 1
                
            except Exception as e:
                logger.debug(f"Error collecting reel: {e}")
                continue
        
        # Report batch progress
        if new_reels_found > 0:
            print(f"      Batch {scroll_count + 1}: +{new_reels_found} new reels (Total: {len(all_reels)}) | Skipped: {duplicates_found} duplicates")
            consecutive_no_new_reels = 0
        elif duplicates_found > 0:
            print(f"      Batch {scroll_count + 1}: Found {duplicates_found} duplicates, no new reels")
            consecutive_no_new_reels += 1
        else:
            consecutive_no_new_reels += 1
        
        # Check stopping conditions
        if consecutive_no_new_reels >= 3:
            print("      No new reels in last 3 batches, stopping")
            break
        
        # Scroll down with human-like behavior
        scroll_count += 1
        
        # Human randomly scrolls at different speeds
        scroll_distance = random.choice([
            'window.scrollTo(0, document.body.scrollHeight)',  # Fast scroll to bottom
            'window.scrollBy(0, window.innerHeight * 2)',      # Medium scroll
            'window.scrollBy(0, window.innerHeight * 1.5)'     # Slower scroll
        ])
        
        last_height = await page.evaluate('document.body.scrollHeight')
        await page.evaluate(scroll_distance)
        
        # Variable delay after scrolling (humans don't scroll at fixed intervals)
        await human_like_delay(2.5, 4)  # Longer delays between scrolls
        
        # Check if page actually scrolled
        new_height = await page.evaluate('document.body.scrollHeight')
        if new_height == last_height:
            print("      Reached end of page")
            break
    
    print(f"   ✓ Found {len(all_reels)} new reels in {scroll_count} batches")
    return all_reels

# ==================== PROFILE SCRAPING ====================

async def scrape_reels_from_profile(page, username):
    """Scrape all reels from a profile with metrics."""
    print(f"\n{'='*70}")
    print(f"SCRAPING PROFILE: @{username}")
    print('='*70)
    
    await page.goto(f'https://www.instagram.com/{username}/', wait_until='domcontentloaded')
    await human_like_delay(2, 3)
    await handle_popups(page)
    
    # Click Reels tab
    print("   → Finding Reels tab...")
    reels_tab = page.locator('a[href*="/reels"]').first
    if await reels_tab.count() > 0:
        await reels_tab.click()
        await human_like_delay(2, 3)
        print("   ✓ Reels tab clicked")
    
    # Scroll and collect with views
    reels_data = await scroll_and_collect_links(page)
    
    if not reels_data:
        print("   ✗ No reels found\n")
        return []
    
    # Visit each reel for likes/comments
    print(f"   → Extracting metrics from {len(reels_data)} reels (with human-like delays)...")
    results = []
    
    for idx, reel in enumerate(reels_data, 1):
        try:
            # Human-like delay before navigating to next reel
            await human_like_delay(1.5, 3)
            
            await page.goto(reel['url'], wait_until='domcontentloaded', timeout=15000)
            await human_like_delay(2, 3)  # Wait for page to fully load like a human
            
            meta_data = await extract_metrics_from_meta(page)
            
            results.append({
                'profile': username,
                'reel_id': reel['reel_id'],
                'url': reel['url'],
                'views': reel['views'],
                'likes': meta_data['likes'],
                'comments': meta_data['comments'],
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            if idx % 10 == 0:
                print(f"      {idx}/{len(reels_data)} processed...", end='\r', flush=True)
            
        except Exception as e:
            logger.warning(f"Error extracting metrics for {reel['reel_id']}: {e}")
            results.append({
                'profile': username,
                'reel_id': reel['reel_id'],
                'url': reel['url'],
                'views': reel['views'],
                'likes': 'N/A',
                'comments': 'N/A',
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    
    print(f"      {len(results)}/{len(reels_data)} processed      ")
    
    # Summary
    views_count = sum(1 for r in results if r['views'] != 'N/A')
    likes_count = sum(1 for r in results if r['likes'] != 'N/A')
    comments_count = sum(1 for r in results if r['comments'] != 'N/A')
    
    print(f"   ✓ Metrics: {views_count} views, {likes_count} likes, {comments_count} comments\n")
    
    return results

# ==================== SAVED POSTS SCRAPING ====================

async def scrape_saved_reels(page):
    """Scrape reels from saved posts with human-like behavior."""
    print(f"\n{'='*70}")
    print(f"SCRAPING SAVED POSTS")
    print('='*70)
    
    # First, navigate to Instagram home to ensure we're logged in
    print("   → Navigating to Instagram home...")
    await page.goto('https://www.instagram.com/', wait_until='domcontentloaded')
    await human_like_delay(3, 5)  # Wait like a human would
    await handle_popups(page)
    
    # STEP 1: Look for and hover over More button (human behavior)
    print("   → Looking for More button in left sidebar...")
    await human_like_delay(1.5, 2.5)  # Human thinks before clicking
    
    more_selectors = [
        'a[href="#"]:has-text("More")',
        'div[role="button"]:has-text("More")',
        'span:has-text("More")',
        'div:has-text("More")'
    ]
    
    more_clicked = False
    for selector in more_selectors:
        try:
            more_btn = page.locator(selector).first
            if await more_btn.count() > 0:
                # Hover first (human behavior)
                print("   → Hovering over More button...")
                await more_btn.hover()
                await human_like_delay(0.5, 1)  # Small delay after hover
                
                # Then click
                print("   → Clicking More button...")
                await more_btn.click()
                await human_like_delay(2, 3)  # Wait for menu to appear
                more_clicked = True
                print("   ✓ More menu opened")
                break
        except Exception as e:
            logger.debug(f"Failed to click More button with selector {selector}: {e}")
            continue
    
    if not more_clicked:
        print("   ✗ Could not find More button")
        print("   ℹ  Please manually navigate to your saved posts and press ENTER when ready")
        input("   Press ENTER when you're on the saved posts page: ")
        await human_like_delay(2, 3)
    else:
        # STEP 2: Click Saved option from the menu
        print("   → Looking for Saved option in menu...")
        await human_like_delay(1, 2)  # Human reads the menu
        
        saved_selectors = [
            'a:has-text("Saved")',
            'div[role="button"]:has-text("Saved")',
            'span:has-text("Saved")'
        ]
        
        saved_clicked = False
        for selector in saved_selectors:
            try:
                saved_btn = page.locator(selector).first
                if await saved_btn.count() > 0:
                    # Hover first
                    print("   → Hovering over Saved option...")
                    await saved_btn.hover()
                    await human_like_delay(0.5, 1)
                    
                    # Click
                    print("   → Clicking Saved...")
                    await saved_btn.click()
                    await human_like_delay(3, 5)  # Wait for page to load
                    saved_clicked = True
                    print("   ✓ Saved page opened")
                    break
            except Exception as e:
                logger.debug(f"Failed to click Saved with selector {selector}: {e}")
                continue
        
        if not saved_clicked:
            print("   ✗ Could not find Saved option")
            print("   ℹ  Please manually click Saved and press ENTER when ready")
            input("   Press ENTER when you're on the saved posts page: ")
            await human_like_delay(2, 3)
    
    # STEP 3: Automatically search for 'content' folder, fallback to 'All Posts'
    print("   → Looking at saved collections...")
    await human_like_delay(2, 3)  # Human looks at the folders
    
    # First, try to find 'content' folder
    print("   → Searching for 'content' collection...")
    await human_like_delay(1, 2)
    
    content_elem = page.locator('a:has-text("content")').first
    
    if await content_elem.count() > 0:
        # Found 'content' folder - use it
        print("   ✓ Found 'content' collection")
        print("   → Hovering over 'content'...")
        await content_elem.hover()
        await human_like_delay(0.5, 1)
        
        print("   → Clicking 'content'...")
        await content_elem.click()
        await human_like_delay(3, 5)  # Wait for folder to open
        print("   ✓ Opened 'content' collection")
    else:
        # 'content' not found - fallback to 'All Posts'
        print("   ⚠ 'content' collection not found")
        print("   → Falling back to 'All Posts'...")
        await human_like_delay(1, 2)
        
        all_elem = page.locator('a:has-text("All Posts")').first
        if await all_elem.count() > 0:
            print("   → Hovering over 'All Posts'...")
            await all_elem.hover()
            await human_like_delay(0.5, 1)
            
            print("   → Clicking 'All Posts'...")
            await all_elem.click()
            await human_like_delay(3, 5)
            print("   ✓ Opened 'All Posts'")
        else:
            print("   ✗ Could not find 'All Posts'")
            print("   ℹ  Please manually open the folder and press ENTER when ready")
            input("   Press ENTER when you're inside the saved folder: ")
            await human_like_delay(2, 3)
    
    # Start scraping immediately (removed indefinite wait)
    print("\n   ✓ Ready to scrape - starting immediately...\n")
    await human_like_delay(1, 2)
    
    # Scroll and collect
    reels_data = await scroll_and_collect_links(page, is_saved_posts=True)
    
    if not reels_data:
        print("   ✗ No reels found in saved posts\n")
        return []
    
    # Visit each reel for likes/comments
    print(f"   → Extracting metrics from {len(reels_data)} reels (with human-like delays)...")
    results = []
    
    for idx, reel in enumerate(reels_data, 1):
        try:
            # Human-like delay before navigating
            await human_like_delay(1.5, 3)
            
            await page.goto(reel['url'], wait_until='domcontentloaded', timeout=15000)
            await human_like_delay(2, 3)  # Wait like a human
            
            meta_data = await extract_metrics_from_meta(page)
            
            results.append({
                'profile': 'saved',
                'reel_id': reel['reel_id'],
                'url': reel['url'],
                'views': reel['views'],
                'likes': meta_data['likes'],
                'comments': meta_data['comments'],
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            if idx % 10 == 0:
                print(f"      {idx}/{len(reels_data)} processed...", end='\r', flush=True)
            
        except Exception as e:
            logger.warning(f"Error extracting metrics for {reel['reel_id']}: {e}")
            results.append({
                'profile': 'saved',
                'reel_id': reel['reel_id'],
                'url': reel['url'],
                'views': reel['views'],
                'likes': 'N/A',
                'comments': 'N/A',
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    
    print(f"      {len(results)}/{len(reels_data)} processed      ")
    
    # Summary
    views_count = sum(1 for r in results if r['views'] != 'N/A')
    likes_count = sum(1 for r in results if r['likes'] != 'N/A')
    comments_count = sum(1 for r in results if r['comments'] != 'N/A')
    
    print(f"   ✓ Metrics: {views_count} views, {likes_count} likes, {comments_count} comments\n")
    
    return results

# ==================== CSV MANAGEMENT ====================

def load_existing_urls():
    """Load existing URLs from CSV to avoid duplicates."""
    existing = set()
    if os.path.exists(OUTPUT_CSV):
        try:
            with open(OUTPUT_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'link' in row:
                        existing.add(row['link'])
        except Exception as e:
            logger.error(f"Error loading existing URLs: {e}")
    return existing

def save_to_csv(results):
    """Save results to single CSV with proper columns: channel, link, views, likes, comments."""
    if not results:
        print("   ⚠ No results to save")
        return
    
    # Ensure directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load existing
    existing_urls = load_existing_urls()
    
    # Filter new results
    new_results = [r for r in results if r['url'] not in existing_urls]
    
    if not new_results:
        print(f"   ⚠ All {len(results)} reels already in CSV")
        return
    
    # Check if file exists to determine if we need headers
    file_exists = os.path.exists(OUTPUT_CSV)
    
    # Append to single CSV file
    with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8') as f:
        # Column order: channel, link, views, likes, comments
        fieldnames = ['channel', 'link', 'views', 'likes', 'comments']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        # Transform data to match column names
        for r in new_results:
            writer.writerow({
                'channel': r['profile'],
                'link': r['url'],
                'views': r['views'],
                'likes': r['likes'],
                'comments': r['comments']
            })
    
    print(f"   ✓ Saved {len(new_results)} new reels to {OUTPUT_CSV}")
    print(f"   (Skipped {len(results) - len(new_results)} duplicates)")
    logger.info(f"Saved {len(new_results)} new reels, skipped {len(results) - len(new_results)} duplicates")

# ==================== MAIN ====================

async def main():
    global EXISTING_URLS
    
    print("\n" + "="*70)
    print("INSTAGRAM REEL SCRAPER WITH METRICS")
    print("="*70)
    print("Features:")
    print("  • Automatic login with session persistence")
    print("  • Multi-profile reel scraping")
    print("  • Saved posts extraction")
    print("  • 100% accurate metrics (views, likes, comments)")
    print("  • Duplicate detection and CSV export")
    print("="*70)
    
    print(f"\nOutput file: {OUTPUT_CSV}")
    
    # Load existing URLs
    EXISTING_URLS = load_existing_urls()
    print(f"Loaded {len(EXISTING_URLS)} existing URLs from previous runs")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS_MODE,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()
        page.set_default_timeout(30000)
        
        # Login
        if not await load_cookies(context, COOKIES_FILE):
            if not await perform_login(page, context):
                print("\n✗ Login failed. Exiting.\n")
                await browser.close()
                return
        else:
            print("\n✓ Session loaded from cookies")
            await page.goto('https://www.instagram.com')
            await human_like_delay(2, 3)
            
            if "login" in page.url.lower():
                print("⚠ Session expired, re-login required")
                if not await perform_login(page, context):
                    await browser.close()
                    return
        
        await handle_popups(page)
        
        # Collect all results for this run
        all_results = []
        
        # Scrape profiles
        print("\n" + "="*70)
        print("PROFILE SCRAPING")
        print("="*70)
        print("Enter Instagram usernames (press Enter with no input to finish):\n")
        
        profile_count = 1
        while True:
            username = input(f"Profile #{profile_count} (or Enter to continue): ").strip()
            
            if not username:
                break
            
            try:
                results = await scrape_reels_from_profile(page, username)
                if results:
                    all_results.extend(results)
                    EXISTING_URLS.update(r['url'] for r in results)
                profile_count += 1
            except Exception as e:
                print(f"   ✗ Error scraping @{username}: {e}\n")
                logger.error(f"Error scraping profile {username}: {e}")
        
        # Scrape saved posts
        print("\n" + "="*70)
        print("SAVED POSTS")
        print("="*70)
        scrape_saved = input("Scrape saved posts? (y/n): ").strip().lower()
        
        if scrape_saved == 'y':
            try:
                results = await scrape_saved_reels(page)
                if results:
                    all_results.extend(results)
            except Exception as e:
                print(f"   ✗ Error scraping saved posts: {e}\n")
                logger.error(f"Error scraping saved posts: {e}")
        
        # Save all results to CSV
        if all_results:
            save_to_csv(all_results)
        
        # Final summary with 30-second timer
        print("\n" + "="*70)
        print("SCRAPING COMPLETE")
        print("="*70)
        print(f"Results saved to: {OUTPUT_CSV}")
        print(f"Log file: {LOG_FILE}")
        print("="*70)
        
        # 30-second observation timer with skip option
        print("\n" + "="*70)
        print(f"⏱  FINAL OBSERVATION: {FINAL_TIMER} seconds")
        print("="*70)
        print("Browser will stay open for 30 seconds for final observation.")
        print("Press ENTER to skip and close immediately...")
        print("="*70)
        
        # Non-blocking timer with skip option
        skip_timer = False
        async def wait_for_input():
            nonlocal skip_timer
            await asyncio.to_thread(input)
            skip_timer = True
        
        input_task = asyncio.create_task(wait_for_input())
        
        for remaining in range(FINAL_TIMER, 0, -1):
            if skip_timer:
                print("\n✓ Timer skipped - closing browser...")
                break
            print(f"   ⏱  {remaining}s remaining... (Press ENTER to skip)", end='\r', flush=True)
            await asyncio.sleep(1)
        
        if not skip_timer:
            print("\n✓ Timer complete - closing browser...         ")
        
        # Cancel input task if still running
        if not input_task.done():
            input_task.cancel()
            try:
                await input_task
            except asyncio.CancelledError:
                pass
        
        print("\n" + "="*70 + "\n")
        
        await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Scraping interrupted by user\n")
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}\n")
        logger.error(f"Fatal error: {e}")
