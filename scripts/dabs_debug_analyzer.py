#!/usr/bin/env python3
"""
DABS Debug Analyzer
Analyze DABS login issues and provide manual verification option
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright
import logging

sys.path.append(str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_dabs_login():
    """Analyze DABS login process in detail"""
    
    print("🔍 DABS Login Analysis - Interactive Debug Mode")
    print("=" * 60)
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,  # Visible browser for manual verification
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        # Load configuration
        config_path = Path(__file__).parent.parent / "config" / "dabs_ordering.env"
        if config_path.exists():
            from dotenv import load_dotenv
            load_dotenv(config_path)
            import os
            username = os.getenv("DABS_ORDERING_USERNAME")
            password = os.getenv("DABS_ORDERING_PASSWORD")
        else:
            print("❌ Configuration file not found")
            return
        
        print(f"🔑 Using credentials: {username} / {'*' * len(password) if password else 'NOT_SET'}")
        
        # Navigate to DABS
        print("\n1. Loading DABS login page...")
        await page.goto("https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/", 
                        wait_until="domcontentloaded", timeout=60000)
        
        print(f"   Current URL: {page.url}")
        print(f"   Page Title: {await page.title()}")
        
        # Check for login form
        print("\n2. Analyzing login form...")
        username_field = await page.query_selector('input[name="UserName"]')
        password_field = await page.query_selector('input[name="Password"]')
        submit_button = await page.query_selector('button[type="submit"], input[type="submit"]')
        
        if username_field and password_field and submit_button:
            print("   ✅ Login form elements found")
            
            # Fill form
            print("   🔑 Filling credentials...")
            await page.fill('input[name="UserName"]', username)
            await page.fill('input[name="Password"]', password)
            
            print("   📸 Taking pre-submit screenshot...")
            await page.screenshot(path="dabs_pre_submit.png")
            
            print("   📤 Submitting login (manual verification window will open)...")
            await page.click('button[type="submit"], input[type="submit"]')
            
            # Wait for manual verification
            print("\n🔍 MANUAL VERIFICATION MODE")
            print("=" * 40)
            print("A browser window is open with the DABS login attempt.")
            print("Please verify:")
            print("1. Did the login succeed?")
            print("2. Are there any error messages?")
            print("3. What page are you currently on?")
            print("4. Is there a CAPTCHA or additional security?")
            print("\nPress Enter to continue after manual review...")
            
            input()  # Wait for manual verification
            
            # Capture final state
            final_url = page.url
            final_title = await page.title()
            
            print(f"\n📊 FINAL STATE:")
            print(f"   URL: {final_url}")
            print(f"   Title: {final_title}")
            
            # Check for error messages
            error_selectors = [
                '.validation-summary-errors',
                '.alert-danger',
                '.error',
                '.field-validation-error',
                '[class*="error"]',
                '[class*="validation"]'
            ]
            
            print(f"\n🔍 Checking for error messages...")
            for selector in error_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    for element in elements:
                        text = await element.text_content()
                        if text and text.strip():
                            print(f"   ❌ Error found ({selector}): {text.strip()}")
            
            print(f"\n📸 Taking final screenshot...")
            await page.screenshot(path="dabs_final_state.png")
            
            # Check if we're on Orders page
            if "/Orders" in final_url:
                print("   ✅ Successfully reached Orders page!")
            else:
                print("   ⚠️ Still on login page or different page")
                
        else:
            print("   ❌ Login form elements not found")
        
        await browser.close()
        await playwright.stop()
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")

async def main():
    await analyze_dabs_login()

if __name__ == "__main__":
    asyncio.run(main())
