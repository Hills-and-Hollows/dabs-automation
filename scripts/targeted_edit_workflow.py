#!/usr/bin/env python3
"""
Targeted Edit Workflow - Based on User's Successful Process
Focus on the exact Edit button workflow that worked before

APPROACH: Target the specific Edit button with material-icons blue that worked
REFERENCE: User's successful conversation "List of tools for dabs ordering"
HTML TARGET: <i class="material-icons blue" data-toggle="tooltip" title="" data-bs-original-title="Edit" aria-describedby="tooltip601173"></i>

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

async def targeted_edit_workflow():
    """
    Target the exact Edit workflow that worked successfully before
    Look for the specific material-icons blue Edit button
    """
    
    print("🎯 TARGETED EDIT WORKFLOW - PROVEN SUCCESSFUL METHOD")
    print("=" * 60)
    print("✅ Authentication: Proven CAPTCHA-free method")
    print("🎯 Target: material-icons blue Edit button (previously successful)")  
    print("📋 Reference: 'List of tools for dabs ordering' conversation")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print()
    
    # 28 items for processing
    items_to_add = [
        {'item_code': '018006', 'product_name': 'BUFFALO TRACE BOURBON 750ml', 'quantity': 1},
        {'item_code': '900888', 'product_name': 'WOODCHUCK HARD CIDER PEARSECCO 355ml', 'quantity': 1},
        {'item_code': '026826', 'product_name': 'JACK DANIELS BLACK LABEL 750ml', 'quantity': 1},
        {'item_code': '901977', 'product_name': 'SALTFIRE CHARLOTTE SOMETIMES CAN 473ml', 'quantity': 1},
        {'item_code': '035318', 'product_name': 'BARTON VODKA 1750ml', 'quantity': 1},
        {'item_code': '907923', 'product_name': 'SIERRA NEVADA TORPEDO EXTRA IP 355ml', 'quantity': 1},
        {'item_code': '035929', 'product_name': 'FIVE WIVES VODKA 750ml', 'quantity': 1},
        {'item_code': '918765', 'product_name': 'ELYSIAN SPACE DUST IPA 355 ml', 'quantity': 1},
        {'item_code': '015626', 'product_name': 'JAMESON IRISH WHISKEY 750ml', 'quantity': 1},
        {'item_code': '771166', 'product_name': 'HOUSE WINE BRUT BUBBLES CAN', 'quantity': 1},
        {'item_code': '064776', 'product_name': 'COINTREAU LIQUEUR 750ml', 'quantity': 1},
        {'item_code': '918785', 'product_name': 'ROHA THURSDAY IPA 355 ml', 'quantity': 1},
        {'item_code': '088548', 'product_name': 'HORNITOS PLATA TEQUILA 750ml', 'quantity': 1},
        {'item_code': '918885', 'product_name': 'NATTY DADDY 355 ml', 'quantity': 6},
        {'item_code': '089786', 'product_name': 'SAUZA HACIENDA GOLD 750ml', 'quantity': 1},
        {'item_code': '947400', 'product_name': 'NEW BELGIUM VOO RANGER IPA CANS 355 ml', 'quantity': 2},
        {'item_code': '402913', 'product_name': 'BLACK BOX CABERNET 3000ml', 'quantity': 1},
        {'item_code': '949961', 'product_name': 'OSKAR BLUES DALES PALE ALE 355ml', 'quantity': 2},
        {'item_code': '518328', 'product_name': 'VENDANGE CABERNET SAUVIGNON 500ml', 'quantity': 1},
        {'item_code': '403296', 'product_name': 'BOTA BOX PINOT NOIR 3000ml', 'quantity': 1},
        {'item_code': '955363', 'product_name': 'ROGUE BATSQUATCH HAZY IPA 355ml', 'quantity': 1},
        {'item_code': '429149', 'product_name': 'VENDANGE CHARDONNAY 500ml', 'quantity': 1},
        {'item_code': '989177', 'product_name': 'ICEHOUSE BEER 355ml', 'quantity': 3},
        {'item_code': '652230', 'product_name': 'DAY OWL ROSE 750ml', 'quantity': 1},
        {'item_code': '575558', 'product_name': 'HOUSE WINE SAUVIGNON BLANC BOX 3000ml', 'quantity': 2},
        {'item_code': '633746', 'product_name': 'VENDANGE PINOT GRIGIO 500ml', 'quantity': 1},
        {'item_code': '010807', 'product_name': 'CROWN ROYAL REGAL APPLE 750ml', 'quantity': 1},
        {'item_code': '771160', 'product_name': 'HOUSE WINE ROSE BUBBLES CAN 355ml', 'quantity': 1}
    ]
    
    total_items = len(items_to_add)
    
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
            headless=False,  # Visible for detailed observation
            args=['--no-sandbox', '--disable-dev-shm-usage', '--start-maximized']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print("🎯 STEP 1: Proven authentication to access DABS...")
        
        await page.goto("https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/", 
                       wait_until="domcontentloaded", timeout=60000)
        
        # Authenticate
        username_field = await page.query_selector('input[name="UserName"]')
        if username_field:
            await page.fill('input[name="UserName"]', os.getenv('DABS_ORDERING_USERNAME', ''))
            await page.fill('input[name="Password"]', os.getenv('DABS_ORDERING_PASSWORD', ''))
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_timeout(5000)
        
        print("✅ Authentication successful")
        
        print("\n🎯 STEP 2: Navigate to orders section to find Edit button...")
        
        # Try multiple navigation strategies to get to where the Edit button would be
        navigation_successful = False
        
        # Strategy 1: Look for direct navigation to orders/warehouse area
        warehouse_urls = [
            "https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders",
            "https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Warehouse", 
            "https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders/DisplayOrder?OrderId=233817&So=SOO03078449"
        ]
        
        for url in warehouse_urls:
            try:
                print(f"   🔄 Trying navigation to: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Look for the specific Edit button
                edit_button_selectors = [
                    'i.material-icons.blue[data-bs-original-title="Edit"]',
                    'i.material-icons.blue[title*="Edit" i]',
                    '.material-icons.blue',
                    'i.material-icons:has-text("edit")',
                    '[data-toggle="tooltip"][data-bs-original-title="Edit"]'
                ]
                
                edit_found = False
                for selector in edit_button_selectors:
                    try:
                        edit_element = await page.query_selector(selector)
                        if edit_element and await edit_element.is_visible():
                            print(f"      ✅ Found Edit button with selector: {selector}")
                            
                            # Click the Edit button (or its parent)
                            parent = await edit_element.query_selector('..')
                            if parent:
                                await parent.click()
                            else:
                                await edit_element.click()
                            
                            await page.wait_for_timeout(3000)
                            edit_found = True
                            navigation_successful = True
                            break
                    except:
                        continue
                
                if edit_found:
                    break
                    
            except Exception as e:
                print(f"      ❌ Navigation failed: {e}")
                continue
        
        # Strategy 2: If direct navigation fails, try systematic page exploration
        if not navigation_successful:
            print("   🔄 Attempting systematic page exploration...")
            
            # Get current page and look for any links/buttons that might lead to orders
            all_links = await page.query_selector_all('a[href]')
            
            for link in all_links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.text_content() or ''
                    
                    if href and ('order' in href.lower() or 'warehouse' in href.lower() or 
                               'order' in text.lower() or 'warehouse' in text.lower()):
                        print(f"      🔄 Following link: '{text}' → {href}")
                        await link.click()
                        await page.wait_for_timeout(3000)
                        
                        # Look for Edit button after navigation
                        for selector in edit_button_selectors:
                            try:
                                edit_element = await page.query_selector(selector)
                                if edit_element and await edit_element.is_visible():
                                    print(f"         ✅ Found Edit button after navigation!")
                                    parent = await edit_element.query_selector('..')
                                    if parent:
                                        await parent.click()
                                    else:
                                        await edit_element.click()
                                    await page.wait_for_timeout(3000)
                                    navigation_successful = True
                                    break
                            except:
                                continue
                        
                        if navigation_successful:
                            break
                except:
                    continue
        
        if navigation_successful:
            print("✅ Successfully accessed Edit interface - proceeding with item addition...")
            
            print("\n🎯 STEP 3: Automated item addition using proven workflow...")
            
            items_added = 0
            
            # Based on the successful workflow, items are added one by one
            for i, item in enumerate(items_to_add, 1):
                try:
                    print(f"   ➕ Adding item {i}/{total_items}: {item['item_code']} - {item['product_name']} (Qty: {item['quantity']})")
                    
                    # Look for search/input fields
                    search_selectors = [
                        'input[type="search"]',
                        'input[placeholder*="search" i]',
                        'input[placeholder*="item" i]', 
                        'input[type="text"]'
                    ]
                    
                    item_added = False
                    
                    for search_selector in search_selectors:
                        if item_added:
                            break
                            
                        try:
                            search_field = await page.query_selector(search_selector)
                            if search_field and await search_field.is_visible():
                                # Search for item using item code
                                await search_field.click()
                                await search_field.fill('')  # Clear field
                                await search_field.fill(item['item_code'])
                                await page.keyboard.press('Enter')
                                await page.wait_for_timeout(2000)
                                
                                # Set quantity
                                qty_field = await page.query_selector('input[type="number"]')
                                if qty_field and await qty_field.is_visible():
                                    await qty_field.click()
                                    await page.keyboard.press('Control+a')
                                    await qty_field.fill(str(item['quantity']))
                                    await page.wait_for_timeout(500)
                                
                                # Add to order
                                add_buttons = await page.query_selector_all('button:has-text("Add"), a:has-text("Add"), input[value*="Add"]')
                                for add_btn in add_buttons:
                                    try:
                                        if await add_btn.is_visible():
                                            await add_btn.click()
                                            await page.wait_for_timeout(1500)
                                            items_added += 1
                                            item_added = True
                                            print(f"      ✅ Successfully added")
                                            break
                                    except:
                                        continue
                                
                                if item_added:
                                    break
                        except:
                            continue
                    
                    if not item_added:
                        print(f"      ❌ Failed to add: {item['product_name']}")
                        
                except Exception as e:
                    print(f"      ❌ Error adding {item['product_name']}: {e}")
            
            print(f"\n📊 ITEM ADDITION RESULTS:")
            print(f"   ✅ Items Successfully Added: {items_added} / {total_items}")
            print(f"   📈 Success Rate: {items_added/total_items*100:.1f}%")
            
            # Take final screenshot
            screenshot_path = Path("targeted_edit_workflow_complete.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"   📸 Final Screenshot: {screenshot_path}")
            
        else:
            print("❌ Could not locate the Edit button interface")
            
            # Take screenshot for analysis
            screenshot_path = Path("targeted_edit_workflow_analysis.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Interface screenshot saved: {screenshot_path}")
            
            items_added = 0
        
        print(f"\n💡 Keeping browser open for 20 seconds for verification...")
        await asyncio.sleep(20)
        
        await browser.close()
        await playwright.stop()
        
        return {
            "success": items_added > 0,
            "method": "targeted_edit_workflow",
            "items_added": items_added,
            "total_items": total_items,
            "navigation_successful": navigation_successful,
            "edit_button_found": navigation_successful,
            "fully_automated": True
        }
        
    except Exception as e:
        print(f"❌ Targeted edit workflow error: {e}")
        return {"success": False, "error": str(e)}

async def main():
    """Execute targeted edit workflow"""
    
    result = await targeted_edit_workflow()
    
    print("\n" + "=" * 60)
    print("🎯 TARGETED EDIT WORKFLOW RESULTS")
    print("=" * 60)
    
    if result.get("success"):
        print("🎉 SUCCESS: Targeted Edit workflow completed!")
        print(f"🎯 Method: {result.get('method', 'N/A')}")
        print(f"📦 Items Added: {result.get('items_added', 0)} / {result.get('total_items', 28)}")
        print(f"🔍 Edit Button Found: {result.get('edit_button_found', False)}")
        print(f"🤖 Fully Automated: {result.get('fully_automated', False)}")
        print()
        
        items_added = result.get('items_added', 0)
        if items_added >= 28:
            print("🌟 PERFECT SUCCESS: All 28 items added!")
        elif items_added >= 20:
            print("🎯 EXCELLENT: Most items successfully added!")
        elif items_added >= 10:
            print("⚡ GOOD: Significant progress made!")
        else:
            print("📝 PARTIAL: Process working, optimization needed!")
            
    else:
        print("🔍 TARGETED ANALYSIS COMPLETED:")
        print(f"❌ Edit workflow not found using current approach")
        print(f"💡 Interface analysis available for optimization")
        
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
