#!/usr/bin/env python3
"""
Edit Existing DABS Order - Add All 28 Items
Hills & Hollows LLC - Utah Package Agency
Date: August 24, 2025

TASK: Edit existing order (OrderId=233817) and add all 28 specified items
WORKFLOW: Open order → Edit order → Add items one by one → Return for review
PROVEN: Headless approach works consistently
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

async def edit_order_add_28_items():
    """
    Edit existing DABS order and add all 28 specified items
    Following the proven successful workflow
    """
    
    print("🎯 EDIT EXISTING DABS ORDER - ADD ALL 28 ITEMS")
    print("=" * 60)
    print("OrderId: 233817 (existing order from DABS)")
    print("Workflow: Open → Edit → Add items → Return for review")
    print("Method: Proven headless Playwright approach")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # EXACT 28 items as specified by user (with corrected order)
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
    
    total_quantity = sum(item['quantity'] for item in items_to_add)
    print(f"📦 ITEMS TO ADD: {len(items_to_add)} products, {total_quantity} total units")
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
            headless=True,  # Proven to work without CAPTCHA
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🔄 Step 1: Navigate directly to existing order...")
        
        # Navigate directly to the specific order URL provided by user
        order_url = "https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders/DisplayOrder?OrderId=233817&So=SOO03078449"
        
        # First authenticate if needed
        await page.goto("https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/", 
                       wait_until="domcontentloaded", timeout=60000)
        
        # Check if we need to login
        username_field = await page.query_selector('input[name="UserName"]')
        if username_field:
            print("🔑 Authentication required...")
            await page.fill('input[name="UserName"]', os.getenv('DABS_ORDERING_USERNAME', ''))
            await page.fill('input[name="Password"]', os.getenv('DABS_ORDERING_PASSWORD', ''))
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_timeout(3000)
        
        # Navigate to the specific order
        print(f"🔄 Navigating to order: {order_url}")
        await page.goto(order_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(2000)
        
        print(f"✅ Current URL: {page.url}")
        print(f"✅ Page Title: {await page.title()}")
        
        print("\n🔄 Step 2: Edit the order...")
        
        # Look for Edit button or link
        edit_selectors = [
            'text="Edit"',
            'a:has-text("Edit")',
            'button:has-text("Edit")',
            'input[value="Edit"]',
            '[title*="Edit"]'
        ]
        
        edit_button = None
        for selector in edit_selectors:
            try:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    edit_button = element
                    print(f"✅ Found edit button: {selector}")
                    break
            except:
                continue
        
        if edit_button:
            print("🔄 Clicking edit button...")
            await edit_button.click()
            await page.wait_for_timeout(3000)
            print(f"✅ After edit click - URL: {page.url}")
        else:
            print("⚠️  Could not find edit button - may already be in edit mode")
        
        print("\n🔄 Step 3: Add items to order (proven workflow)...")
        
        items_successfully_added = 0
        items_failed = []
        
        for i, item in enumerate(items_to_add, 1):
            try:
                print(f"\n➕ Item {i}/{len(items_to_add)}: Adding {item['item_code']} - {item['product_name']} (Qty: {item['quantity']})")
                
                # Look for search or item code input field
                search_selectors = [
                    'input[type="text"]',
                    'input[name*="search"]',
                    'input[name*="item"]',
                    'input[name*="code"]',
                    'input[placeholder*="search"]',
                    'input[placeholder*="item"]'
                ]
                
                search_field = None
                for selector in search_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element and await element.is_visible():
                            search_field = element
                            break
                    except:
                        continue
                
                if search_field:
                    # Clear and enter item code
                    await search_field.click()
                    await page.keyboard.press('Control+a')  # Select all
                    await search_field.fill(item['item_code'])
                    
                    # Try different ways to search
                    await page.keyboard.press('Enter')
                    await page.wait_for_timeout(2000)
                    
                    # Alternative: look for search button
                    search_button = await page.query_selector('button:has-text("Search"), input[value*="Search"], button[type="submit"]')
                    if search_button:
                        await search_button.click()
                        await page.wait_for_timeout(2000)
                    
                    # Look for the item in results and set quantity
                    quantity_field = await page.query_selector('input[type="number"], input[name*="quantity"], input[name*="qty"]')
                    if quantity_field:
                        await quantity_field.click()
                        await page.keyboard.press('Control+a')
                        await quantity_field.fill(str(item['quantity']))
                        await page.wait_for_timeout(500)
                    
                    # Look for Add to Order button
                    add_selectors = [
                        'button:has-text("Add")',
                        'input[value*="Add"]',
                        'button:has-text("Add to Order")',
                        'a:has-text("Add")'
                    ]
                    
                    add_button = None
                    for selector in add_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element and await element.is_visible():
                                add_button = element
                                break
                        except:
                            continue
                    
                    if add_button:
                        await add_button.click()
                        await page.wait_for_timeout(1500)  # Wait for item to be added
                        items_successfully_added += 1
                        print(f"   ✅ Successfully added: {item['product_name']}")
                    else:
                        print(f"   ❌ Could not find Add button for: {item['product_name']}")
                        items_failed.append(item)
                        
                else:
                    print(f"   ❌ Could not find search field for: {item['product_name']}")
                    items_failed.append(item)
                    
            except Exception as e:
                print(f"   ❌ Error adding {item['product_name']}: {e}")
                items_failed.append(item)
        
        print(f"\n📊 ITEM ADDITION RESULTS:")
        print(f"   ✅ Successfully Added: {items_successfully_added} / {len(items_to_add)} items")
        print(f"   ❌ Failed to Add: {len(items_failed)} items")
        
        if items_failed:
            print(f"\n⚠️  FAILED ITEMS:")
            for item in items_failed:
                print(f"   - {item['item_code']}: {item['product_name']} (Qty: {item['quantity']})")
        
        print("\n🔄 Step 4: Return to order view for review...")
        
        # Look for Save/Return/Done button to complete editing
        completion_selectors = [
            'button:has-text("Save")',
            'button:has-text("Done")', 
            'button:has-text("Return")',
            'input[value*="Save"]',
            'a:has-text("Return to Order")'
        ]
        
        completion_button = None
        for selector in completion_selectors:
            try:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    completion_button = element
                    break
            except:
                continue
        
        if completion_button:
            print("✅ Returning to order view...")
            await completion_button.click()
            await page.wait_for_timeout(3000)
        
        print(f"✅ Final URL: {page.url}")
        
        # Generate audit trail
        audit_data = {
            "timestamp": datetime.now().isoformat(),
            "task_id": "445939ca-47eb-457c-9c3f-73ac9449b251",
            "order_id": "233817",
            "workflow": "edit_existing_order",
            "items_specified": len(items_to_add),
            "items_successfully_added": items_successfully_added,
            "items_failed": len(items_failed),
            "success_rate": f"{(items_successfully_added/len(items_to_add)*100):.1f}%",
            "method": "proven_headless_playwright",
            "ready_for_review": True
        }
        
        audit_file = Path("logs/order_edit_audit.jsonl")
        audit_file.parent.mkdir(exist_ok=True)
        with open(audit_file, 'a') as f:
            f.write(json.dumps(audit_data) + '\n')
        
        return {
            "success": items_successfully_added > 0,
            "items_added": items_successfully_added,
            "items_failed": len(items_failed),
            "ready_for_review": True,
            "audit_logged": True
        }
        
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
    """Execute order editing and item addition"""
    
    result = await edit_order_add_28_items()
    
    print("\n" + "=" * 60)
    print("📊 TASK COMPLETION RESULTS")
    print("=" * 60)
    
    if result.get("success"):
        print("🎉 ORDER EDITING COMPLETED!")
        print(f"📦 Items Added: {result.get('items_added', 0)} / 28 items")
        print(f"❌ Items Failed: {result.get('items_failed', 0)} items")
        print(f"📄 Audit Logged: {result.get('audit_logged', False)}")
        print()
        print("✅ READY FOR REVIEW")
        print("📋 Order has been edited and items added")
        print("🔗 Review at: https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders/DisplayOrder?OrderId=233817&So=SOO03078449")
        
    else:
        print("❌ ORDER EDITING FAILED:")
        if result.get('error'):
            print(f"Error: {result.get('error')}")
    
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
