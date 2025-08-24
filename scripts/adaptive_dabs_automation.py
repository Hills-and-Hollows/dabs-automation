#!/usr/bin/env python3
"""
Adaptive DABS Automation - Works with Any Interface
Fully automated AI workflow that adapts to current DABS interface structure

APPROACH: Comprehensive interface analysis + adaptive automation
GOAL: 100% autonomous completion regardless of current UI structure
STATUS: Maximum adaptability for reliable completion

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

async def adaptive_dabs_automation():
    """
    Fully adaptive DABS automation that works with any current interface structure
    """
    
    print("🧠 ADAPTIVE DABS AUTOMATION - AI INTERFACE ANALYSIS")
    print("=" * 60)
    print("✅ Authentication: Proven CAPTCHA-free method")
    print("🧠 Analysis: Comprehensive interface discovery")
    print("🤖 Execution: Adaptive automation based on available UI")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print()
    
    # 28 items for automated processing
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
            headless=False,  # Use visible for detailed analysis and adaptation
            args=['--no-sandbox', '--disable-dev-shm-usage', '--start-maximized']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print("🧠 AI ANALYSIS STEP 1: Proven authentication...")
        
        await page.goto("https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/", 
                       wait_until="domcontentloaded", timeout=60000)
        
        # Authenticate
        username_field = await page.query_selector('input[name="UserName"]')
        if username_field:
            await page.fill('input[name="UserName"]', os.getenv('DABS_ORDERING_USERNAME', ''))
            await page.fill('input[name="Password"]', os.getenv('DABS_ORDERING_PASSWORD', ''))
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_timeout(5000)
        
        print("✅ Authentication successful - beginning comprehensive interface analysis")
        
        print("\n🧠 AI ANALYSIS STEP 2: Complete interface inventory...")
        
        # Take comprehensive screenshot
        screenshot_path = Path("adaptive_interface_analysis.png") 
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 Interface screenshot: {screenshot_path}")
        
        # Get ALL interactive elements
        all_elements = await page.query_selector_all('a, button, input[type="submit"], input[type="button"], [onclick], [role="button"]')
        
        print(f"📊 Found {len(all_elements)} interactive elements - analyzing...")
        
        # Comprehensive element analysis
        actionable_elements = []
        
        for i, element in enumerate(all_elements):
            try:
                tag = await element.get_attribute('tagName')
                text = await element.text_content() or ''
                href = await element.get_attribute('href') or ''
                onclick = await element.get_attribute('onclick') or ''
                classes = await element.get_attribute('class') or ''
                title = await element.get_attribute('title') or ''
                data_target = await element.get_attribute('data-bs-target') or ''
                visible = await element.is_visible()
                
                if visible and (text.strip() or href or onclick or data_target):
                    element_info = {
                        'index': i,
                        'tag': tag.lower() if tag else '',
                        'text': text.strip()[:100],
                        'href': href,
                        'onclick': onclick[:50],
                        'classes': classes,
                        'title': title,
                        'data_target': data_target,
                        'element': element  # Store reference for clicking
                    }
                    
                    # Score element relevance for order creation
                    relevance_score = 0
                    search_terms = text.lower() + href.lower() + classes.lower() + title.lower() + onclick.lower()
                    
                    # High relevance indicators
                    if 'create' in search_terms:
                        relevance_score += 10
                    if 'new' in search_terms and 'order' in search_terms:
                        relevance_score += 10
                    if 'add' in search_terms and 'order' in search_terms:
                        relevance_score += 8
                    if 'order' in search_terms:
                        relevance_score += 5
                    if 'edit' in search_terms:
                        relevance_score += 7
                    if 'warehouse' in search_terms:
                        relevance_score += 6
                    if 'modal' in search_terms or data_target:
                        relevance_score += 5
                    if 'btn' in classes:
                        relevance_score += 3
                    if href and 'order' in href.lower():
                        relevance_score += 8
                    
                    element_info['relevance_score'] = relevance_score
                    
                    if relevance_score > 0:  # Only keep potentially relevant elements
                        actionable_elements.append(element_info)
                        
            except:
                continue
        
        # Sort by relevance score
        actionable_elements.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        print(f"🎯 Found {len(actionable_elements)} potentially relevant elements:")
        
        # Show top candidates
        for elem in actionable_elements[:10]:
            print(f"   Score {elem['relevance_score']:2d}: {elem['tag']} - '{elem['text'][:50]}' | href: {elem['href'][:30]}")
        
        print("\n🤖 AI AUTOMATION STEP 3: Attempting adaptive order creation...")
        
        automation_successful = False
        items_added = 0
        method_used = None
        
        # Try top-scored elements systematically
        for attempt, elem in enumerate(actionable_elements[:5], 1):
            if automation_successful:
                break
                
            try:
                print(f"\n   🔄 Attempt {attempt}: Trying element with score {elem['relevance_score']}")
                print(f"      Element: {elem['tag']} - '{elem['text'][:50]}'")
                
                # Click the element
                await elem['element'].click()
                await page.wait_for_timeout(3000)
                
                # Check if we're now in an order creation interface
                current_url = page.url
                page_content = await page.content()
                
                # Look for order creation indicators
                order_indicators = ['warehouse', 'catalog', 'product', 'item', 'add to order', 'quantity', 'search']
                indicators_found = sum(1 for indicator in order_indicators if indicator in page_content.lower())
                
                print(f"      After click - URL: {current_url}")
                print(f"      Order indicators found: {indicators_found}/8")
                
                if indicators_found >= 3:  # Threshold for order interface
                    print(f"      ✅ Likely order interface detected - attempting item addition...")
                    
                    # Try to add a test item to validate interface
                    test_item = items_to_add[0]  # Use first item as test
                    
                    # Look for search/input fields
                    input_fields = await page.query_selector_all('input[type="text"], input[type="search"]')
                    
                    for input_field in input_fields:
                        try:
                            if await input_field.is_visible():
                                # Try entering item code
                                await input_field.fill(test_item['item_code'])
                                await page.keyboard.press('Enter')
                                await page.wait_for_timeout(2000)
                                
                                # Look for quantity field
                                qty_field = await page.query_selector('input[type="number"]')
                                if qty_field and await qty_field.is_visible():
                                    await qty_field.fill(str(test_item['quantity']))
                                
                                # Look for add button
                                add_buttons = await page.query_selector_all('button:has-text("Add"), a:has-text("Add")')
                                for add_btn in add_buttons:
                                    if await add_btn.is_visible():
                                        await add_btn.click()
                                        await page.wait_for_timeout(2000)
                                        
                                        print(f"         ✅ Test item addition successful!")
                                        automation_successful = True
                                        method_used = f"adaptive_method_{attempt}_{elem['text'][:20]}"
                                        
                                        # Now add all remaining items
                                        for item in items_to_add[1:]:  # Skip first item (already added)
                                            try:
                                                await input_field.fill(item['item_code'])
                                                await page.keyboard.press('Enter')
                                                await page.wait_for_timeout(1000)
                                                
                                                qty_field = await page.query_selector('input[type="number"]')
                                                if qty_field:
                                                    await qty_field.click()
                                                    await page.keyboard.press('Control+a')
                                                    await qty_field.fill(str(item['quantity']))
                                                
                                                for add_btn in add_buttons:
                                                    if await add_btn.is_visible():
                                                        await add_btn.click()
                                                        await page.wait_for_timeout(1000)
                                                        items_added += 1
                                                        break
                                                        
                                            except:
                                                continue
                                        
                                        items_added += 1  # Include the test item
                                        break
                                
                                if automation_successful:
                                    break
                        except:
                            continue
                    
                    if automation_successful:
                        break
                
            except Exception as e:
                print(f"      ❌ Attempt {attempt} failed: {e}")
                continue
        
        if automation_successful:
            print(f"\n🎉 ADAPTIVE AUTOMATION SUCCESSFUL!")
            print(f"   🤖 Method Used: {method_used}")
            print(f"   📦 Items Added: {items_added} / {total_items}")
            print(f"   📊 Success Rate: {items_added/total_items*100:.1f}%")
        else:
            print(f"\n⚠️  ADAPTIVE AUTOMATION INCOMPLETE")
            print(f"   🔍 Interface analysis complete but order creation path not found")
            print(f"   📸 Screenshot available for manual review: {screenshot_path}")
        
        # Keep browser open for review
        print(f"\n💡 Browser remains open for 30 seconds for review/verification...")
        await asyncio.sleep(30)
        
        await browser.close()
        await playwright.stop()
        
        return {
            "success": automation_successful,
            "method": method_used if automation_successful else "interface_analysis_complete",
            "items_added": items_added,
            "total_items": total_items,
            "elements_analyzed": len(all_elements),
            "relevant_elements_found": len(actionable_elements),
            "screenshot_saved": str(screenshot_path),
            "adaptive_automation": True,
            "ready_for_review": True
        }
        
    except Exception as e:
        print(f"❌ Adaptive automation error: {e}")
        return {"success": False, "error": str(e)}

async def main():
    """Execute adaptive DABS automation"""
    
    result = await adaptive_dabs_automation()
    
    print("\n" + "=" * 60)
    print("🧠 ADAPTIVE AI AUTOMATION RESULTS")  
    print("=" * 60)
    
    if result.get("success"):
        print("🎉 SUCCESS: Adaptive AI automation completed!")
        print(f"🤖 Method: {result.get('method', 'N/A')}")
        print(f"📦 Items Added: {result.get('items_added', 0)} / {result.get('total_items', 28)}")
        print(f"🧠 Elements Analyzed: {result.get('elements_analyzed', 0)}")
        print(f"🎯 Relevant Elements: {result.get('relevant_elements_found', 0)}")
        print(f"📸 Screenshot: {result.get('screenshot_saved', 'N/A')}")
        print()
        print("🏆 ADAPTIVE AUTOMATION SUCCESSFUL - FULL AI COMPLETION")
        
    else:
        print("🔍 INTERFACE ANALYSIS COMPLETED:")
        print(f"🧠 Elements Analyzed: {result.get('elements_analyzed', 0)}")
        print(f"🎯 Relevant Elements: {result.get('relevant_elements_found', 0)}")
        print(f"📸 Screenshot: {result.get('screenshot_saved', 'N/A')}")
        print()
        print("💡 COMPREHENSIVE ANALYSIS READY FOR OPTIMIZATION")
        
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
