#!/usr/bin/env python3
"""
Find and Edit Existing Order - Replicate Successful Workflow
Navigate to existing order first, then find the material-icons Edit button

CRITICAL INSIGHT: The Edit button is on the ORDER page, not the main DABS page
Workflow: Navigate to Orders → Find existing order → Enter order → Find Edit button → Add items

Date: August 24, 2025
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

async def find_and_edit_existing_order():
    """
    Find existing order first, then locate the Edit button for item addition
    """
    
    print("🎯 FIND AND EDIT EXISTING ORDER")
    print("=" * 60)
    print("Strategy: Navigate to Orders → Find existing order → Look for Edit button")
    print("Goal: Locate the material-icons Edit button from successful workflow")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # 28 items specification
    items_to_add = [
        {'item_code': '018006', 'name': 'BUFFALO TRACE BOURBON 750ml', 'qty': 1},
        {'item_code': '900888', 'name': 'WOODCHUCK HARD CIDER PEARSECCO 355ml', 'qty': 1},
        {'item_code': '026826', 'name': 'JACK DANIELS BLACK LABEL 750ml', 'qty': 1},
        {'item_code': '901977', 'name': 'SALTFIRE CHARLOTTE SOMETIMES CAN 473ml', 'qty': 1},
        {'item_code': '035318', 'name': 'BARTON VODKA 1750ml', 'qty': 1},
        {'item_code': '907923', 'name': 'SIERRA NEVADA TORPEDO EXTRA IP 355ml', 'qty': 1},
        {'item_code': '035929', 'name': 'FIVE WIVES VODKA 750ml', 'qty': 1},
        {'item_code': '918765', 'name': 'ELYSIAN SPACE DUST IPA 355 ml', 'qty': 1},
        {'item_code': '015626', 'name': 'JAMESON IRISH WHISKEY 750ml', 'qty': 1},
        {'item_code': '771166', 'name': 'HOUSE WINE BRUT BUBBLES CAN', 'qty': 1},
        {'item_code': '064776', 'name': 'COINTREAU LIQUEUR 750ml', 'qty': 1},
        {'item_code': '918785', 'name': 'ROHA THURSDAY IPA 355 ml', 'qty': 1},
        {'item_code': '088548', 'name': 'HORNITOS PLATA TEQUILA 750ml', 'qty': 1},
        {'item_code': '918885', 'name': 'NATTY DADDY 355 ml', 'qty': 6},
        {'item_code': '089786', 'name': 'SAUZA HACIENDA GOLD 750ml', 'qty': 1},
        {'item_code': '947400', 'name': 'NEW BELGIUM VOO RANGER IPA CANS 355 ml', 'qty': 2},
        {'item_code': '402913', 'name': 'BLACK BOX CABERNET 3000ml', 'qty': 1},
        {'item_code': '949961', 'name': 'OSKAR BLUES DALES PALE ALE 355ml', 'qty': 2},
        {'item_code': '518328', 'name': 'VENDANGE CABERNET SAUVIGNON 500ml', 'qty': 1},
        {'item_code': '403296', 'name': 'BOTA BOX PINOT NOIR 3000ml', 'qty': 1},
        {'item_code': '955363', 'name': 'ROGUE BATSQUATCH HAZY IPA 355ml', 'qty': 1},
        {'item_code': '429149', 'name': 'VENDANGE CHARDONNAY 500ml', 'qty': 1},
        {'item_code': '989177', 'name': 'ICEHOUSE BEER 355ml', 'qty': 3},
        {'item_code': '652230', 'name': 'DAY OWL ROSE 750ml', 'qty': 1},
        {'item_code': '575558', 'name': 'HOUSE WINE SAUVIGNON BLANC BOX 3000ml', 'qty': 2},
        {'item_code': '633746', 'name': 'VENDANGE PINOT GRIGIO 500ml', 'qty': 1},
        {'item_code': '010807', 'name': 'CROWN ROYAL REGAL APPLE 750ml', 'qty': 1},
        {'item_code': '771160', 'name': 'HOUSE WINE ROSE BUBBLES CAN 355ml', 'qty': 1}
    ]
    
    total_items = len(items_to_add)
    total_quantity = sum(item['qty'] for item in items_to_add)
    
    print(f"📦 TARGET: {total_items} items, {total_quantity} total units")
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
            headless=False,  # Use visible for detailed investigation
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🔄 Step 1: Authenticate with DABS...")
        
        await page.goto("https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/", 
                       wait_until="domcontentloaded", timeout=60000)
        
        # Authenticate
        username_field = await page.query_selector('input[name="UserName"]')
        if username_field:
            await page.fill('input[name="UserName"]', os.getenv('DABS_ORDERING_USERNAME', ''))
            await page.fill('input[name="Password"]', os.getenv('DABS_ORDERING_PASSWORD', ''))
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_timeout(5000)
        
        print(f"✅ Current URL: {page.url}")
        print(f"✅ Page Title: {await page.title()}")
        
        print("\n🔄 Step 2: Navigate to Orders section...")
        
        # Look for Orders navigation
        orders_links = await page.query_selector_all('a:has-text("Order"), a:has-text("order"), [href*="order" i]')
        
        print(f"📋 Found {len(orders_links)} potential order links")
        
        for i, link in enumerate(orders_links):
            try:
                text = await link.text_content()
                href = await link.get_attribute('href')
                visible = await link.is_visible()
                if visible and text:
                    print(f"   {i}: '{text}' - href: {href}")
            except:
                pass
        
        # Try to click an Orders link
        if orders_links:
            for link in orders_links:
                try:
                    text = await link.text_content() or ""
                    if await link.is_visible() and ('order' in text.lower() or 'Order' in text):
                        await link.click()
                        await page.wait_for_timeout(3000)
                        print(f"✅ Clicked orders link: '{text}'")
                        print(f"✅ New URL: {page.url}")
                        break
                except:
                    continue
        
        print("\n🔄 Step 3: Look for existing orders...")
        
        # Take screenshot for analysis
        screenshot_path = Path("orders_page_analysis.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 Screenshot: {screenshot_path}")
        
        # Look for orders table or list
        tables = await page.query_selector_all('table')
        print(f"📋 Found {len(tables)} table(s)")
        
        order_found = False
        
        if tables:
            for i, table in enumerate(tables):
                try:
                    table_text = await table.text_content()
                    if table_text and ('order' in table_text.lower() or 'Order' in table_text):
                        print(f"✅ Found orders table {i}")
                        
                        # Look for Edit links/buttons in this table
                        edit_elements = await table.query_selector_all('a, button, i.material-icons')
                        
                        print(f"   📝 Found {len(edit_elements)} potential action elements in table")
                        
                        for j, element in enumerate(edit_elements):
                            try:
                                # Check for Edit-related attributes
                                title = await element.get_attribute('title') or await element.get_attribute('data-bs-original-title')
                                text = await element.text_content()
                                classes = await element.get_attribute('class')
                                
                                if title and 'edit' in title.lower():
                                    print(f"   ✅ FOUND EDIT ELEMENT {j}: title='{title}', classes='{classes}'")
                                    
                                    # This could be our target Edit button
                                    await element.click()
                                    await page.wait_for_timeout(3000)
                                    order_found = True
                                    
                                    print(f"✅ Clicked Edit element - New URL: {page.url}")
                                    break
                                    
                                elif text and 'edit' in text.lower():
                                    print(f"   ✅ FOUND EDIT TEXT {j}: '{text}', classes='{classes}'")
                                    
                                elif classes and 'material-icons' in classes:
                                    print(f"   🎯 Material icon {j}: text='{text}', classes='{classes}', title='{title}'")
                                    
                            except Exception as e:
                                logger.debug(f"Error checking element {j}: {e}")
                                continue
                        
                        if order_found:
                            break
                except:
                    continue
        
        if order_found:
            print("\n🎉 SUCCESS: Found and accessed order editing interface!")
            print(f"✅ Current URL: {page.url}")
            
            # Take screenshot of edit interface
            edit_screenshot_path = Path("order_edit_interface.png")
            await page.screenshot(path=edit_screenshot_path, full_page=True)
            print(f"📸 Edit Interface Screenshot: {edit_screenshot_path}")
            
            print("\n🔄 Step 4: Ready to add items...")
            print("🎯 NEXT: Implement item addition workflow")
            
            return {
                "success": True,
                "order_edit_interface_found": True,
                "current_url": page.url,
                "ready_for_item_addition": True,
                "screenshots": [str(screenshot_path), str(edit_screenshot_path)]
            }
        else:
            print("❌ Could not locate order editing interface")
            
            return {
                "success": False,
                "issue": "order_edit_interface_not_found",
                "current_url": page.url,
                "screenshots": [str(screenshot_path)]
            }
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}
        
    finally:
        try:
            # Keep browser open for analysis
            print("\n💡 Browser left open for manual inspection...")
            await asyncio.sleep(10)  # Give time to analyze
            await browser.close()
            await playwright.stop()
        except:
            pass

async def main():
    """Execute order finding and editing workflow"""
    
    result = await find_and_edit_existing_order()
    
    print("\n" + "=" * 60)
    print("📊 ORDER LOCATION RESULTS")
    print("=" * 60)
    
    if result.get("success"):
        print("🎉 SUCCESS: Order editing interface located!")
        print(f"✅ Edit Interface Found: {result.get('order_edit_interface_found', False)}")
        print(f"🔗 Current URL: {result.get('current_url', 'N/A')}")
        print(f"📸 Screenshots: {', '.join(result.get('screenshots', []))}")
        print(f"🚀 Ready for Item Addition: {result.get('ready_for_item_addition', False)}")
        print()
        print("🔄 NEXT STEPS:")
        print("1. Analyze edit interface screenshots")
        print("2. Implement item addition workflow") 
        print("3. Add all 28 items")
        
    else:
        print("❌ ORDER LOCATION FAILED:")
        print(f"❌ Issue: {result.get('issue', 'Unknown')}")
        if result.get('error'):
            print(f"❌ Error: {result.get('error')}")
        print(f"🔗 Last URL: {result.get('current_url', 'N/A')}")
    
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
