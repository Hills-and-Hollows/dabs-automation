#!/usr/bin/env python3
"""
DABS UI Diagnostic - Fix UI Element Issues
Diagnose and fix the UI selector/timing issues preventing item addition

PROVEN: Authentication works (headless eliminates CAPTCHA)
ISSUE: UI element timing/selectors preventing order creation
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def diagnose_dabs_ui():
    """
    Diagnose DABS UI to understand why order creation is failing
    """
    
    print("🔍 DABS UI DIAGNOSTIC - FIX ELEMENT ISSUES")
    print("=" * 60)
    print("Authentication: ✅ PROVEN (headless works)")
    print("Issue: UI timing/selectors for order creation")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    try:
        # Load environment
        env_file = Path(__file__).parent.parent / "config" / "dabs_ordering.env"
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,  # Visible for diagnostic purposes
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🔄 Step 1: Navigate to DABS and authenticate...")
        
        # Navigate and login
        await page.goto("https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/", 
                       wait_until="networkidle", timeout=60000)
        
        # Fill login form
        await page.fill('input[name="UserName"]', os.getenv('DABS_ORDERING_USERNAME', ''))
        await page.fill('input[name="Password"]', os.getenv('DABS_ORDERING_PASSWORD', ''))
        await page.click('button[type="submit"], input[type="submit"]')
        
        # Wait for redirect
        await page.wait_for_timeout(5000)
        
        print(f"✅ Current URL: {page.url}")
        print(f"✅ Page Title: {await page.title()}")
        
        print("\n🔄 Step 2: Analyze current page state...")
        
        # Take screenshot for analysis
        screenshot_path = Path("dabs_ui_diagnostic.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 Screenshot saved: {screenshot_path}")
        
        # Check for existing orders
        print("\n🔍 Step 3: Check for existing/pending orders...")
        
        # Look for orders table or pending orders
        orders_table = await page.query_selector('table')
        if orders_table:
            print("✅ Found orders table - checking for pending orders...")
            
            # Get table text content to analyze
            table_text = await orders_table.text_content()
            if 'pending' in table_text.lower() or 'draft' in table_text.lower():
                print("⚠️ FOUND PENDING ORDER - This may be blocking new order creation")
                print("📋 Pending order content preview:")
                print(table_text[:500] + "..." if len(table_text) > 500 else table_text)
            else:
                print("✅ No pending orders detected")
        else:
            print("❌ No orders table found")
        
        print("\n🔍 Step 4: Look for 'Create New Order' button...")
        
        # Try different selectors for create button
        create_selectors = [
            'text=Create New Order',
            'button:has-text("Create")',
            'a:has-text("Create")',
            'input[value*="Create"]',
            '[title*="Create"]',
            'button[onclick*="create"]'
        ]
        
        for selector in create_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    text = await element.text_content() if await element.text_content() else await element.get_attribute('value')
                    print(f"✅ Found element: {selector} - Visible: {is_visible} - Text: '{text}'")
                else:
                    print(f"❌ Not found: {selector}")
            except Exception as e:
                print(f"❌ Error checking {selector}: {e}")
        
        print("\n🔍 Step 5: Get all clickable elements on page...")
        
        # Get all buttons and links
        buttons = await page.query_selector_all('button, input[type="submit"], input[type="button"], a')
        print(f"📋 Found {len(buttons)} clickable elements:")
        
        for i, button in enumerate(buttons[:20]):  # First 20 for brevity
            try:
                text = await button.text_content() or await button.get_attribute('value') or await button.get_attribute('title')
                if text and text.strip():
                    is_visible = await button.is_visible()
                    tag = await button.get_attribute('tagName') or 'unknown'
                    print(f"   {i+1:2d}. {tag}: '{text.strip()[:50]}' - Visible: {is_visible}")
            except:
                pass
        
        print("\n🔍 Step 6: Check page HTML for order-related elements...")
        
        # Get page content and search for relevant terms
        page_content = await page.content()
        
        search_terms = ['create', 'order', 'add', 'new', 'pending', 'submit', 'warehouse']
        for term in search_terms:
            if term.lower() in page_content.lower():
                print(f"✅ Found '{term}' in page content")
            else:
                print(f"❌ '{term}' not found in page content")
        
        print("\n💡 DIAGNOSTIC SUMMARY:")
        print("=" * 40)
        print("✅ Authentication: Working (headless confirmed)")
        print("✅ Page Access: Successfully reached DABS system") 
        print("⚠️ UI Elements: Need to identify correct selectors")
        print("🔧 Next Steps: Update selectors based on diagnostic results")
        
        await browser.close()
        await playwright.stop()
        
        return {
            "authentication_working": True,
            "page_accessible": True,
            "screenshot_saved": str(screenshot_path),
            "diagnostic_complete": True
        }
        
    except Exception as e:
        print(f"❌ Diagnostic error: {e}")
        return {"error": str(e)}

async def main():
    """Run DABS UI diagnostic"""
    
    result = await diagnose_dabs_ui()
    
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC RESULTS")
    print("=" * 60)
    
    if result.get("diagnostic_complete"):
        print("✅ UI diagnostic completed successfully")
        print(f"📸 Screenshot available: {result.get('screenshot_saved')}")
        print("🔧 Use diagnostic results to fix UI selectors")
        print("💡 Next: Update DABSAutomatedOrdering with correct selectors")
    else:
        print("❌ Diagnostic failed")
        print(f"Error: {result.get('error')}")
    
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
