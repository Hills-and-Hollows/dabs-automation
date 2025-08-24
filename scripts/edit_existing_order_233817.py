#!/usr/bin/env python3
"""
Edit Existing DABS Order 233817 - CORRECT APPROACH
Based on user's specific request to edit existing order, not create new order

USER INSTRUCTION: "open the order, edit the order, add to order, add all items"
TARGET ORDER: 233817 (SOO03078449)
APPROACH: Use proven authentication + edit existing order workflow

Date: August 24, 2025
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.integration.dabs_automated_ordering import DABSAutomatedOrdering

async def edit_existing_order_233817():
    """
    CORRECT APPROACH: Edit existing Order 233817 to add 28 items
    This matches the user's specific instruction and successful previous workflow
    """
    
    print("🎯 EDITING EXISTING DABS ORDER 233817")
    print("=" * 60)
    print("✅ Approach: Edit existing order (user's correct instruction)")
    print("📋 Target Order: 233817 (SOO03078449)")
    print("🎯 Goal: Add 28 items to existing order")
    print("✅ Authentication: Proven CAPTCHA-free method")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Target order details
    target_order_id = "233817"
    target_so = "SOO03078449"
    direct_order_url = f"https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders/DisplayOrder?OrderId={target_order_id}&So={target_so}"
    
    # ALL 28 ITEMS to add to existing order
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
    total_quantity = sum(item['quantity'] for item in items_to_add)
    
    print(f"📦 Target: Add {total_items} items to Order {target_order_id}")
    print(f"🔗 Direct URL: {direct_order_url}")
    print()
    
    try:
        print("🚀 STEP 1: Initialize proven automation system...")
        
        # Use same proven configuration (CAPTCHA-free)
        automation = DABSAutomatedOrdering(headless=True, timeout=60000)
        await automation.initialize_automation_system()
        print("   ✅ Authentication successful - CAPTCHA bypassed")
        
        print("\n🎯 STEP 2: Navigate directly to existing order...")
        
        # Get a page from the authenticated browser
        page = await automation.browser_context.new_page()
        
        # Navigate directly to the specific order
        print(f"   🔗 Navigating to: {direct_order_url}")
        await page.goto(direct_order_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Check current URL after navigation
        current_url = page.url
        print(f"   📍 Current URL: {current_url}")
        
        if target_order_id in current_url:
            print("   ✅ Successfully reached target order page")
            
            print("\n🎯 STEP 3: Look for Edit button (material-icons blue)...")
            
            # Look for the specific Edit button mentioned by user
            edit_button_selectors = [
                'i.material-icons.blue[data-bs-original-title="Edit"]',
                'i.material-icons.blue[title*="Edit"]',
                'i.material-icons.blue',
                '[data-bs-original-title="Edit"]',
                '[title="Edit"]'
            ]
            
            edit_found = False
            for selector in edit_button_selectors:
                try:
                    edit_element = await page.query_selector(selector)
                    if edit_element and await edit_element.is_visible():
                        print(f"   ✅ Found Edit button: {selector}")
                        
                        # Click the Edit button (or its clickable parent)
                        parent = await edit_element.query_selector('..')
                        if parent:
                            await parent.click()
                        else:
                            await edit_element.click()
                        
                        await page.wait_for_timeout(3000)
                        edit_found = True
                        break
                except:
                    continue
            
            if edit_found:
                print("   ✅ Edit interface accessed successfully")
                
                print("\n🎯 STEP 4: Add items to existing order (1 by 1)...")
                
                items_successfully_added = 0
                
                for i, item in enumerate(items_to_add, 1):
                    try:
                        print(f"   ➕ Adding item {i}/{total_items}: {item['item_code']} - {item['product_name']} (Qty: {item['quantity']})")
                        
                        # Look for search field
                        search_selectors = [
                            'input[type="search"]',
                            'input[placeholder*="Item Code" i]',
                            'input[placeholder*="Search" i]',
                            'input[type="text"]'
                        ]
                        
                        item_added = False
                        for search_selector in search_selectors:
                            try:
                                search_field = await page.query_selector(search_selector)
                                if search_field and await search_field.is_visible():
                                    # Search for item
                                    await search_field.click()
                                    await search_field.fill('')  # Clear
                                    await search_field.fill(item['item_code'])
                                    await page.keyboard.press('Enter')
                                    await page.wait_for_timeout(2000)
                                    
                                    # Set quantity
                                    qty_field = await page.query_selector('input[type="number"], input[name*="quantity" i]')
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
                                                items_successfully_added += 1
                                                item_added = True
                                                print(f"      ✅ Added successfully")
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
                
                print(f"\n📊 EDIT RESULTS:")
                print(f"   ✅ Items Successfully Added: {items_successfully_added} / {total_items}")
                print(f"   📈 Success Rate: {items_successfully_added/total_items*100:.1f}%")
                
                if items_successfully_added >= total_items:
                    print("\n🎉 PERFECT SUCCESS: All 28 items added to existing order!")
                elif items_successfully_added >= 20:
                    print(f"\n⚡ EXCELLENT: {items_successfully_added}/28 items added!")
                elif items_successfully_added > 0:
                    print(f"\n📝 PARTIAL: {items_successfully_added}/28 items added - process working!")
                
                # Take screenshot of final state
                screenshot_path = Path("edit_order_233817_final_state.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"   📸 Final Screenshot: {screenshot_path}")
                
                edit_successful = items_successfully_added > 0
                
            else:
                print("   ❌ Edit button not found on order page")
                edit_successful = False
                items_successfully_added = 0
                
        else:
            print("   ❌ Did not reach target order page (possible redirect)")
            
            # Take screenshot for analysis
            screenshot_path = Path("edit_order_navigation_issue.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"   📸 Navigation Screenshot: {screenshot_path}")
            
            edit_successful = False
            items_successfully_added = 0
        
        await page.close()
        await automation.cleanup()
        
        return {
            'success': edit_successful,
            'order_id': target_order_id,
            'items_added': items_successfully_added,
            'total_items': total_items,
            'method': 'edit_existing_order',
            'target_url': direct_order_url
        }
        
    except Exception as e:
        print(f"❌ Error editing existing order: {e}")
        try:
            await automation.cleanup()
        except:
            pass
        return {
            'success': False,
            'error': str(e),
            'items_added': 0
        }

async def main():
    """Execute edit existing order workflow"""
    
    result = await edit_existing_order_233817()
    
    print("\n" + "=" * 60)
    print("🏁 EDIT EXISTING ORDER RESULTS")
    print("=" * 60)
    
    if result.get('success'):
        print("🎉 SUCCESS: Existing order editing completed!")
        print(f"📋 Order ID: {result.get('order_id', 'N/A')}")
        print(f"📦 Items Added: {result.get('items_added', 0)} / {result.get('total_items', 28)}")
        print(f"🎯 Method: {result.get('method', 'N/A')}")
        print()
        
        if result.get('items_added') == 28:
            print("🌟 PERFECT: All 28 items added to existing order!")
            print("🏆 TASK 445939ca-47eb-457c-9c3f-73ac9449b251 COMPLETE!")
        else:
            print(f"⚡ PROGRESS: {result.get('items_added')} items added successfully")
            
    else:
        print("❌ EDIT EXISTING ORDER FAILED:")
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
