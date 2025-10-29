"""
Download Instagram Reels using snapinsta.to
Reads URLs from reels/content.txt and automates the download process.
"""

import asyncio
import os
import time
from playwright.async_api import async_playwright

# Configuration
CONTENT_FILE = 'reels/content.txt'
DOWNLOAD_DIR = 'downloaded_reels'
SNAPINSTA_URL = 'https://snapinsta.to/en/instagram-reels-downloader'
DELAY_BETWEEN_DOWNLOADS = 3  # seconds

async def download_reel(page, url, index, total):
    """Download a single reel using snapinsta.to"""
    try:
        print(f"\n[{index}/{total}] Processing: {url}")
        
        # Navigate to snapinsta
        print("  → Loading snapinsta.to...")
        await page.goto(SNAPINSTA_URL, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(2)
        
        # Find and fill the input field
        print("  → Pasting URL...")
        input_selectors = [
            'input[type="text"]',
            'input[placeholder*="URL"]',
            'input[placeholder*="url"]',
            'input[name="url"]',
            '#url',
        ]
        
        input_field = None
        for selector in input_selectors:
            try:
                input_field = await page.wait_for_selector(selector, timeout=5000)
                if input_field:
                    break
            except:
                continue
        
        if not input_field:
            print("  ✗ Could not find input field")
            return False
        
        # Clear and type the URL
        await input_field.click()
        await input_field.fill('')
        await input_field.type(url, delay=50)
        await asyncio.sleep(1)
        
        # Find and click download/submit button
        print("  → Clicking download button...")
        button_selectors = [
            'button[type="submit"]',
            'button:has-text("Download")',
            'button:has-text("download")',
            'input[type="submit"]',
            '.download-btn',
            '#download-btn',
        ]
        
        button = None
        for selector in button_selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=5000)
                if button:
                    await button.click()
                    break
            except:
                continue
        
        if not button:
            print("  ✗ Could not find download button")
            return False
        
        # Wait for download link to appear
        print("  → Waiting for download link...")
        await asyncio.sleep(5)  # Give time for processing
        
        # Look for download link
        download_link = None
        download_selectors = [
            'a[download]',
            'a:has-text("Download")',
            'a:has-text("download")',
            'a[href*=".mp4"]',
            '.download-link',
        ]
        
        for selector in download_selectors:
            try:
                download_link = await page.wait_for_selector(selector, timeout=10000)
                if download_link:
                    print(f"  ✓ Found download link with selector: {selector}")
                    break
            except:
                continue
        
        if download_link:
            # Click download link
            print("  → Initiating download...")
            
            # Set up download handling
            async with page.expect_download() as download_info:
                await download_link.click()
            
            download = await download_info.value
            
            # Save with a meaningful filename
            post_id = url.split('/')[-2] if '/' in url else f"reel_{index}"
            filename = f"{post_id}.mp4"
            save_path = os.path.join(DOWNLOAD_DIR, filename)
            
            await download.save_as(save_path)
            print(f"  ✓ Downloaded: {filename}")
            return True
        else:
            print("  ✗ Could not find download link")
            # Take screenshot for debugging
            await page.screenshot(path=f'debug_download_{index}.png')
            print(f"  📸 Saved debug screenshot: debug_download_{index}.png")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


async def main():
    """Main function to download all reels from content.txt"""
    
    # Create download directory
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # Read URLs from content.txt
    if not os.path.exists(CONTENT_FILE):
        print(f"✗ Content file not found: {CONTENT_FILE}")
        return
    
    urls = []
    with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                # Extract just the URL (before the pipe |)
                if '|' in line:
                    url = line.split('|')[0].strip()
                else:
                    url = line
                if 'instagram.com' in url:
                    urls.append(url)
    
    if not urls:
        print("✗ No URLs found in content file")
        return
    
    print("="*70)
    print(f"Instagram Reel Downloader - snapinsta.to")
    print("="*70)
    print(f"Found {len(urls)} URLs to download")
    print(f"Download directory: {DOWNLOAD_DIR}")
    print("="*70)
    
    # Ask user confirmation
    response = input(f"\nDownload {len(urls)} reels? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    async with async_playwright() as p:
        # Launch browser
        print("\n→ Launching browser...")
        browser = await p.chromium.launch(headless=False)  # Set to True for background mode
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()
        
        # Download each reel
        successful = 0
        failed = 0
        
        for i, url in enumerate(urls, 1):
            success = await download_reel(page, url, i, len(urls))
            
            if success:
                successful += 1
            else:
                failed += 1
            
            # Delay between downloads to avoid rate limiting
            if i < len(urls):
                print(f"  ⏱ Waiting {DELAY_BETWEEN_DOWNLOADS}s before next download...")
                await asyncio.sleep(DELAY_BETWEEN_DOWNLOADS)
        
        await browser.close()
        
        # Summary
        print("\n" + "="*70)
        print("DOWNLOAD SUMMARY")
        print("="*70)
        print(f"Total URLs: {len(urls)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Download location: {os.path.abspath(DOWNLOAD_DIR)}")
        print("="*70)


if __name__ == "__main__":
    print("\n🎬 Instagram Reel Downloader (snapinsta.to)")
    print("This script will download reels from your content.txt file\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✗ Download cancelled by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
