#!/usr/bin/env python3
"""
Explore Main DABS Page - Find Order Navigation
Examine the main DABS page that we can successfully reach and find order navigation

Date: August 24, 2025
Goal: Find the correct path to order creation from the working main page
"""

import asyncio
import json
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

async def explore_main_dabs_page():
    """
    Explore the main DABS page that we can successfully access
    """
    
    print("🔍 EXPLORE MAIN DABS PAGE")
    print("=" * 60)
    print("Goal: Find order navigation from working main page")
    print("Focus: Locate correct path to order creation")
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
            headless=False,  # Visible for analysis
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🔄 Step 1: Authenticate with DABS...")
        
        # Navigate to DABS - the URL we know works
        await page.goto("https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/", 
                       wait_until="domcontentloaded", timeout=60000)
        
        # Authenticate
        username_field = await page.query_selector('input[name="UserName"]')
        if username_field:
            await page.fill('input[name="UserName"]', os.getenv('DABS_ORDERING_USERNAME', ''))
            await page.fill('input[name="Password"]', os.getenv('DABS_ORDERING_PASSWORD', ''))
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_timeout(5000)
        
        print(f"✅ Successfully reached: {page.url}")
        print(f"✅ Page title: {await page.title()}")
        
        # Take screenshot of main page
        main_screenshot = Path("main_dabs_page_exploration.png")
        await page.screenshot(path=main_screenshot, full_page=True)
        print(f"📸 Main page screenshot: {main_screenshot}")
        
        print("\n🔍 Step 2: Find all navigation links...")
        
        # Look for navigation elements
        nav_links = await page.query_selector_all('a[href]')
        
        print(f"📋 Found {len(nav_links)} navigation links:")
        
        order_links = []
        admin_links = []
        other_links = []
        
        for i, link in enumerate(nav_links):
            try:
                href = await link.get_attribute('href')
                text = await link.text_content()
                visible = await link.is_visible()
                
                if visible and text and text.strip() and href:
                    link_info = {
                        'index': i,
                        'text': text.strip()[:100],
                        'href': href,
                        'visible': visible
                    }
                    
                    # Categorize links
                    text_lower = text.lower()
                    href_lower = href.lower()
                    
                    if 'order' in text_lower or 'order' in href_lower:
                        order_links.append(link_info)
                    elif any(word in text_lower for word in ['admin', 'manage', 'create', 'new']):
                        admin_links.append(link_info)
                    else:
                        other_links.append(link_info)
                        
            except:
                continue
        
        print(f"\n📋 ORDER-RELATED LINKS ({len(order_links)}):")
        for link in order_links:
            print(f"   {link['index']:2d}. '{link['text']}' → {link['href']}")
        
        print(f"\n🔧 ADMIN/CREATE LINKS ({len(admin_links)}):")
        for link in admin_links:
            print(f"   {link['index']:2d}. '{link['text']}' → {link['href']}")
        
        print(f"\n🌐 OTHER NAVIGATION ({len(other_links[:10])}):")  # First 10 only
        for link in other_links[:10]:
            print(f"   {link['index']:2d}. '{link['text']}' → {link['href']}")
        
        print("\n🔍 Step 3: Look for specific UI elements...")
        
        # Look for buttons that might start order creation
        buttons = await page.query_selector_all('button, input[type="submit"], input[type="button"]')
        
        create_buttons = []
        for button in buttons:
            try:
                text = await button.text_content()
                onclick = await button.get_attribute('onclick')
                classes = await button.get_attribute('class')
                visible = await button.is_visible()
                
                if visible and text and text.strip():
                    button_text = text.strip().lower()
                    if 'create' in button_text or 'new' in button_text or 'order' in button_text:
                        create_buttons.append({
                            'text': text.strip(),
                            'onclick': onclick or '',
                            'classes': classes or ''
                        })
            except:
                continue
        
        print(f"🆕 CREATE/ORDER BUTTONS ({len(create_buttons)}):")
        for button in create_buttons:
            print(f"   • '{button['text']}' | onclick: '{button['onclick']}' | classes: '{button['classes']}'")
        
        print("\n🔍 Step 4: Test clicking first order-related link...")
        
        if order_links:
            try:
                first_order_link = order_links[0]
                print(f"🔄 Clicking: '{first_order_link['text']}'")
                
                # Find the actual link element and click it
                for link in nav_links:
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    if href == first_order_link['href'] and text and text.strip() == first_order_link['text']:
                        await link.click()
                        await page.wait_for_timeout(3000)
                        break
                
                print(f"✅ After click - URL: {page.url}")
                print(f"✅ After click - Title: {await page.title()}")
                
                # Take screenshot of orders page
                orders_screenshot = Path("orders_page_after_navigation.png")
                await page.screenshot(path=orders_screenshot, full_page=True)
                print(f"📸 Orders page screenshot: {orders_screenshot}")
                
                # Now look for Create New Order elements on this page
                print("\n🔍 Step 5: Search for Create New Order on orders page...")
                
                create_elements = await page.query_selector_all('*:has-text("Create"), *:has-text("New"), *:has-text("Order")')
                
                print(f"📋 Found {len(create_elements)} elements with Create/New/Order text:")
                
                for i, element in enumerate(create_elements[:10]):  # First 10 only
                    try:
                        text = await element.text_content()
                        tag = await element.get_attribute('tagName')
                        classes = await element.get_attribute('class')
                        visible = await element.is_visible()
                        
                        if visible and text and text.strip():
                            print(f"   {i:2d}. {tag}: '{text.strip()[:100]}' | Classes: '{classes or 'none'}'")
                    except:
                        continue
                
                return {
                    "success": True,
                    "main_page_accessible": True,
                    "orders_page_accessible": True,
                    "order_links_found": len(order_links),
                    "create_buttons_found": len(create_buttons),
                    "screenshots": [str(main_screenshot), str(orders_screenshot)]
                }
                
            except Exception as e:
                print(f"❌ Error clicking order link: {e}")
                
        print("\n💡 ANALYSIS COMPLETE")
        
        # Keep browser open for manual inspection
        await asyncio.sleep(15)
        
        await browser.close()
        await playwright.stop()
        
        return {
            "success": True,
            "main_page_accessible": True,
            "order_links_found": len(order_links),
            "create_buttons_found": len(create_buttons),
            "screenshots": [str(main_screenshot)]
        }
        
    except Exception as e:
        print(f"❌ Exploration error: {e}")
        return {"success": False, "error": str(e)}

async def main():
    """Execute main DABS page exploration"""
    
    result = await explore_main_dabs_page()
    
    print("\n" + "=" * 60)
    print("📊 EXPLORATION RESULTS")
    print("=" * 60)
    
    if result.get("success"):
        print("✅ Main DABS page exploration completed")
        print(f"🌐 Main page accessible: {result.get('main_page_accessible', False)}")
        print(f"📋 Orders page accessible: {result.get('orders_page_accessible', False)}")
        print(f"🔗 Order links found: {result.get('order_links_found', 0)}")
        print(f"🆕 Create buttons found: {result.get('create_buttons_found', 0)}")
        print(f"📸 Screenshots: {', '.join(result.get('screenshots', []))}")
        print()
        print("🔄 NEXT STEPS:")
        print("1. Review screenshots to identify order creation path")
        print("2. Test the discovered navigation elements")
        print("3. Execute order creation using correct path")
        
    else:
        print("❌ Exploration failed")
        print(f"Error: {result.get('error')}")
        
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
