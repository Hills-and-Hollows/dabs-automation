#!/usr/bin/env python3
"""
Analyze Order Page Interface - Understand current state
Check what's actually on Order 233817 page to find the Edit button

Date: August 24, 2025
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path  
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.integration.dabs_automated_ordering import DABSAutomatedOrdering

async def analyze_order_page():
    """
    Analyze what's actually on Order 233817 page
    """
    
    print("🔍 ANALYZING ORDER 233817 PAGE INTERFACE")
    print("=" * 60)
    
    target_order_url = "https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders/DisplayOrder?OrderId=233817&So=SOO03078449"
    
    try:
        # Initialize with proven authentication
        automation = DABSAutomatedOrdering(headless=False, timeout=60000)  # Visible for analysis
        await automation.initialize_automation_system()
        print("✅ Authentication successful")
        
        # Navigate to target order
        page = await automation.browser_context.new_page()
        await page.goto(target_order_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)
        
        print(f"📍 Current URL: {page.url}")
        print(f"📄 Page Title: {await page.title()}")
        
        # Take comprehensive screenshot
        screenshot_path = Path("order_233817_interface_analysis.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 Screenshot saved: {screenshot_path}")
        
        # Analyze ALL interactive elements
        all_elements = await page.query_selector_all('a, button, input, [onclick], [role="button"]')
        
        print(f"\n🔍 Found {len(all_elements)} interactive elements:")
        
        interactive_elements = []
        for i, element in enumerate(all_elements[:20]):  # Show first 20
            try:
                tag = await element.get_attribute('tagName')
                text = await element.text_content() or ''
                href = await element.get_attribute('href') or ''
                onclick = await element.get_attribute('onclick') or ''
                classes = await element.get_attribute('class') or ''
                title = await element.get_attribute('title') or ''
                visible = await element.is_visible()
                
                if visible and (text.strip() or href or onclick):
                    element_info = {
                        'index': i,
                        'tag': tag.lower(),
                        'text': text.strip()[:80],
                        'href': href[:80],
                        'classes': classes[:80],
                        'title': title[:80],
                        'onclick': onclick[:80]
                    }
                    
                    interactive_elements.append(element_info)
                    print(f"  {i:2d}. {tag:8} | Text: '{text[:40]:40}' | Class: '{classes[:30]:30}' | Href: '{href[:30]:30}'")
                    
            except:
                continue
        
        # Look specifically for Edit-related elements
        print(f"\n🎯 SEARCHING FOR EDIT-RELATED ELEMENTS:")
        
        edit_searches = [
            'Edit',
            'material-icons', 
            'blue',
            'tooltip',
            'edit',
            'pencil',
            'modify'
        ]
        
        found_edit_related = []
        page_content = await page.content()
        
        for search_term in edit_searches:
            if search_term.lower() in page_content.lower():
                print(f"  ✅ Found '{search_term}' in page content")
                found_edit_related.append(search_term)
            else:
                print(f"  ❌ '{search_term}' not found in page content")
        
        # Check for specific selectors
        print(f"\n🔍 CHECKING SPECIFIC SELECTORS:")
        
        selectors_to_check = [
            'i.material-icons.blue',
            '[data-bs-original-title="Edit"]',
            '[title="Edit"]',
            'a:has-text("Edit")',
            'button:has-text("Edit")',
            '.edit-button',
            '.btn-edit'
        ]
        
        for selector in selectors_to_check:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"  ✅ Found {len(elements)} elements with selector: {selector}")
                    for elem in elements[:3]:
                        try:
                            text = await elem.text_content() or ''
                            visible = await elem.is_visible()
                            print(f"     - Text: '{text[:50]}' | Visible: {visible}")
                        except:
                            continue
                else:
                    print(f"  ❌ No elements found: {selector}")
            except:
                print(f"  ❓ Selector error: {selector}")
        
        # Check current page state
        print(f"\n📊 PAGE STATE ANALYSIS:")
        
        # Look for order status indicators
        status_indicators = ['pending', 'submitted', 'completed', 'cancelled']
        for status in status_indicators:
            if status in page_content.lower():
                print(f"  🏷️  Status '{status}' found in page")
        
        # Look for order total or item count
        import re
        price_matches = re.findall(r'\$[\d,]+\.?\d*', page_content)
        if price_matches:
            print(f"  💰 Found prices: {price_matches[:5]}")
        
        item_count_matches = re.findall(r'(\d+)\s*(item|product)', page_content.lower())
        if item_count_matches:
            print(f"  📦 Found item counts: {item_count_matches[:3]}")
        
        print(f"\n💡 Keeping browser open for 30 seconds for manual analysis...")
        await asyncio.sleep(30)
        
        await page.close()
        await automation.cleanup()
        
        return {
            'success': True,
            'url_reached': target_order_url in page.url,
            'interactive_elements_found': len(interactive_elements),
            'edit_related_terms': found_edit_related,
            'screenshot_path': str(screenshot_path)
        }
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return {'success': False, 'error': str(e)}

async def main():
    result = await analyze_order_page()
    
    print("\n" + "=" * 60)
    print("🔍 ORDER PAGE ANALYSIS COMPLETE")
    print("=" * 60)
    
    if result.get('success'):
        print("✅ Analysis completed successfully")
        print(f"🎯 URL Reached: {result.get('url_reached', False)}")
        print(f"🔍 Interactive Elements: {result.get('interactive_elements_found', 0)}")
        print(f"✏️  Edit Terms Found: {result.get('edit_related_terms', [])}")
        print(f"📸 Screenshot: {result.get('screenshot_path', 'N/A')}")
    else:
        print(f"❌ Analysis failed: {result.get('error', 'Unknown')}")
        
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
