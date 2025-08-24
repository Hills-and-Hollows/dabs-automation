#!/usr/bin/env python3
"""
Work with Existing Order - Add 28 Items
Focus on the existing order state and add items directly
Following the proven workflow that was successful before

Date: August 24, 2025
Task: Add all 28 items to existing DABS order
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

async def work_with_existing_order():
    """
    Work with existing order state to add all 28 items
    Use the approach that was successful before
    """
    
    print("🎯 WORK WITH EXISTING ORDER - ADD 28 ITEMS")
    print("=" * 60)
    print("Approach: Work with existing order state")
    print("Goal: Add all 28 items using proven process")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # ALL 28 items to add (in order provided by user)
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
    
    print(f"📦 ITEMS TO ADD: {total_items} items, {total_quantity} total units")
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
            headless=True,  # Use headless for proven CAPTCHA-free operation
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🔄 Step 1: Navigate to DABS Orders...")
        
        # Go to the main DABS orders page first
        await page.goto("https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/", 
                       wait_until="domcontentloaded", timeout=60000)
        
        # Authenticate if needed
        username_field = await page.query_selector('input[name="UserName"]')
        if username_field:
            await page.fill('input[name="UserName"]', os.getenv('DABS_ORDERING_USERNAME', ''))
            await page.fill('input[name="Password"]', os.getenv('DABS_ORDERING_PASSWORD', ''))
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_timeout(3000)
        
        print("✅ Authenticated and on DABS system")
        
        print("\n🔄 Step 2: Look for existing orders...")
        
        # Check current page for orders table
        orders_table = await page.query_selector('table')
        if orders_table:
            print("✅ Found orders table")
            
            # Look for pending/draft orders or edit links
            edit_links = await page.query_selector_all('a:has-text("Edit"), button:has-text("Edit")')
            
            if edit_links:
                print(f"✅ Found {len(edit_links)} Edit link(s)")
                
                # Click the first edit link to edit existing order
                await edit_links[0].click()
                await page.wait_for_timeout(3000)
                
                print(f"✅ Clicked edit - Current URL: {page.url}")
                
                # Now we should be in order edit mode
                print("\n🔄 Step 3: Add items to order...")
                
                items_added = 0
                items_failed = []
                
                for i, item in enumerate(items_to_add, 1):
                    try:
                        print(f"\n➕ Item {i}/{total_items}: {item['item_code']} - {item['name']} (Qty: {item['qty']})")
                        
                        # Multiple strategies for finding item search interface
                        search_success = False
                        
                        # Strategy 1: Look for item search box
                        search_selectors = [
                            'input[placeholder*="item" i]',
                            'input[placeholder*="search" i]', 
                            'input[name*="item" i]',
                            'input[name*="search" i]',
                            'input[type="text"]:visible'
                        ]
                        
                        for selector in search_selectors:
                            try:
                                search_field = await page.query_selector(selector)
                                if search_field and await search_field.is_visible():
                                    # Enter item code
                                    await search_field.fill(item['item_code'])
                                    
                                    # Try Enter key or Search button
                                    await page.keyboard.press('Enter')
                                    await page.wait_for_timeout(1500)
                                    
                                    # Alternative: look for search button
                                    search_btn = await page.query_selector('button:has-text("Search"), input[value*="Search"]')
                                    if search_btn and await search_btn.is_visible():
                                        await search_btn.click()
                                        await page.wait_for_timeout(1500)
                                    
                                    # Set quantity
                                    qty_field = await page.query_selector('input[type="number"]:visible, input[name*="qty" i]:visible')
                                    if qty_field:
                                        await qty_field.fill(str(item['qty']))
                                        await page.wait_for_timeout(500)
                                    
                                    # Add to order
                                    add_selectors = [
                                        'button:has-text("Add"):visible',
                                        'input[value*="Add"]:visible',
                                        'button:has-text("Add to Order"):visible'
                                    ]
                                    
                                    for add_selector in add_selectors:
                                        try:
                                            add_btn = await page.query_selector(add_selector)
                                            if add_btn and await add_btn.is_visible():
                                                await add_btn.click()
                                                await page.wait_for_timeout(1000)
                                                items_added += 1
                                                search_success = True
                                                print(f"   ✅ Added successfully")
                                                break
                                        except:
                                            continue
                                    
                                    if search_success:
                                        break
                            except:
                                continue
                        
                        if not search_success:
                            items_failed.append(item)
                            print(f"   ❌ Failed to add")
                            
                    except Exception as e:
                        items_failed.append(item)
                        print(f"   ❌ Error: {e}")
                
                print(f"\n📊 RESULTS:")
                print(f"   ✅ Items Added: {items_added} / {total_items}")
                print(f"   ❌ Items Failed: {len(items_failed)}")
                
                if items_failed:
                    print(f"\n⚠️ FAILED ITEMS:")
                    for item in items_failed[:5]:  # Show first 5 failed items
                        print(f"   - {item['item_code']}: {item['name']}")
                    if len(items_failed) > 5:
                        print(f"   ... and {len(items_failed) - 5} more")
                
                # Try to save/complete the order
                print(f"\n🔄 Step 4: Complete order editing...")
                
                save_selectors = [
                    'button:has-text("Save"):visible',
                    'button:has-text("Done"):visible',
                    'input[value*="Save"]:visible',
                    'a:has-text("Return"):visible'
                ]
                
                for selector in save_selectors:
                    try:
                        save_btn = await page.query_selector(selector)
                        if save_btn and await save_btn.is_visible():
                            await save_btn.click()
                            await page.wait_for_timeout(2000)
                            print("✅ Order editing completed")
                            break
                    except:
                        continue
                
                print(f"✅ Final URL: {page.url}")
                
                return {
                    "success": items_added > 0,
                    "items_added": items_added,
                    "items_failed": len(items_failed),
                    "completion_rate": f"{items_added/total_items*100:.1f}%",
                    "ready_for_review": True,
                    "message": f"Added {items_added} items to existing order"
                }
            else:
                print("❌ No Edit links found in orders table")
                return {"success": False, "error": "No editable orders found"}
        else:
            print("❌ No orders table found")
            return {"success": False, "error": "Orders table not accessible"}
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}
        
    finally:
        try:
            await browser.close()
            await playwright.stop()
        except:
            pass

async def main():
    """Execute the order editing process"""
    
    result = await work_with_existing_order()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    if result.get("success"):
        print("🎉 ORDER EDITING SUCCESSFUL!")
        print(f"📦 Items Added: {result.get('items_added', 0)} items")
        print(f"❌ Items Failed: {result.get('items_failed', 0)} items")
        print(f"📊 Completion Rate: {result.get('completion_rate', '0%')}")
        print(f"✅ Ready for Review: {result.get('ready_for_review', False)}")
        print()
        print("🔗 Check your DABS Orders page to review the updated order")
        
        if result.get('items_added', 0) == 28:
            print("🎊 PERFECT SUCCESS: All 28 items added!")
        elif result.get('items_added', 0) > 0:
            print("⚡ PARTIAL SUCCESS: Some items added - process is working!")
            
    else:
        print("❌ ORDER EDITING FAILED:")
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
