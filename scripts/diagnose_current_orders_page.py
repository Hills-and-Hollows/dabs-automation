#!/usr/bin/env python3
"""
Diagnose Current Orders Page - Find Available Elements
Identify what elements are actually present on the current orders page

Date: August 24, 2025  
Goal: Find the correct path to the order creation workflow
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

async def diagnose_current_orders_page():
    """
    Diagnose the current orders page to find available elements
    """
    
    print("🔍 DIAGNOSE CURRENT ORDERS PAGE")
    print("=" * 60)
    print("Goal: Find available elements and navigation options")
    print("Focus: Locate order creation entry points")
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
            headless=False,  # Use visible for detailed diagnosis
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🔄 Step 1: Authenticate and reach orders page...")
        
        # Navigate to DABS
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
        
        # Navigate to Orders page
        await page.goto("https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders", 
                       wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)
        
        print(f"✅ Orders Page URL: {page.url}")
        print(f"✅ Orders Page Title: {await page.title()}")
        
        # Take screenshot for analysis
        screenshot_path = Path("current_orders_page_diagnosis.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 Screenshot: {screenshot_path}")
        
        print("\n🔍 Step 2: Analyze all clickable elements...")
        
        # Get all buttons, links, and potential action elements
        clickable_elements = await page.query_selector_all('button, a, input[type="submit"], input[type="button"], [onclick]')
        
        print(f"📋 Found {len(clickable_elements)} clickable elements:")
        
        create_related = []
        order_related = []
        other_actions = []
        
        for i, element in enumerate(clickable_elements):
            try:
                text = await element.text_content()
                classes = await element.get_attribute('class')
                href = await element.get_attribute('href')
                onclick = await element.get_attribute('onclick')
                title = await element.get_attribute('title')
                visible = await element.is_visible()
                
                if visible and text and text.strip():
                    element_info = {
                        'index': i,
                        'text': text.strip()[:100],
                        'classes': classes or '',
                        'href': href or '',
                        'onclick': onclick or '',
                        'title': title or ''
                    }
                    
                    # Categorize elements
                    text_lower = text.lower()
                    if 'create' in text_lower or 'new' in text_lower:
                        create_related.append(element_info)
                    elif 'order' in text_lower:
                        order_related.append(element_info)
                    else:
                        other_actions.append(element_info)
                        
            except:
                continue
        
        print(f"\n🆕 CREATE/NEW RELATED ELEMENTS ({len(create_related)}):")
        for elem in create_related:
            print(f"   {elem['index']:2d}. '{elem['text']}' | Classes: '{elem['classes']}' | Href: '{elem['href']}'")
        
        print(f"\n📋 ORDER RELATED ELEMENTS ({len(order_related)}):")
        for elem in order_related:
            print(f"   {elem['index']:2d}. '{elem['text']}' | Classes: '{elem['classes']}' | Href: '{elem['href']}'")
        
        print(f"\n🔧 OTHER ACTION ELEMENTS ({len(other_actions[:10])}):")  # First 10 only
        for elem in other_actions[:10]:
            print(f"   {elem['index']:2d}. '{elem['text']}' | Classes: '{elem['classes']}' | Href: '{elem['href']}'")
        
        print("\n🔍 Step 3: Look for specific validated selectors...")
        
        # Test the exact selectors from the validated workflow
        validated_selectors = {
            'create_order_button': 'a.btn.btn-orange.btn-lg[data-bs-toggle="modal"][data-bs-target="#paTypeModal"]',
            'alternative_create': 'a[data-bs-target="#paTypeModal"]',
            'orange_button': 'a.btn.btn-orange',
            'create_text': 'text=Create New Order',
            'modal_button': '[data-bs-toggle="modal"]'
        }
        
        for name, selector in validated_selectors.items():
            try:
                element = await page.query_selector(selector)
                if element:
                    visible = await element.is_visible()
                    text = await element.text_content()
                    print(f"   ✅ FOUND {name}: '{text}' - Visible: {visible}")
                else:
                    print(f"   ❌ NOT FOUND: {name}")
            except:
                print(f"   ❌ ERROR checking: {name}")
        
        print("\n🔍 Step 4: Check for tables and existing orders...")
        
        # Look for tables (might contain existing orders)
        tables = await page.query_selector_all('table')
        print(f"📋 Found {len(tables)} table(s)")
        
        for i, table in enumerate(tables):
            try:
                table_text = await table.text_content()
                if table_text and len(table_text) > 50:  # Only show substantial tables
                    print(f"   Table {i}: {table_text[:200]}...")
            except:
                continue
        
        print("\n💡 ANALYSIS COMPLETE - Browser left open for manual inspection...")
        
        # Keep browser open for manual analysis
        await asyncio.sleep(15)
        
        await browser.close()
        await playwright.stop()
        
        return {
            "success": True,
            "create_elements_found": len(create_related),
            "order_elements_found": len(order_related),
            "total_clickable_elements": len(clickable_elements),
            "screenshot_saved": str(screenshot_path)
        }
        
    except Exception as e:
        print(f"❌ Diagnosis error: {e}")
        return {"success": False, "error": str(e)}

async def main():
    """Execute orders page diagnosis"""
    
    result = await diagnose_current_orders_page()
    
    print("\n" + "=" * 60)
    print("📊 DIAGNOSIS RESULTS")
    print("=" * 60)
    
    if result.get("success"):
        print("✅ Orders page diagnosis completed")
        print(f"🆕 Create-related elements: {result.get('create_elements_found', 0)}")
        print(f"📋 Order-related elements: {result.get('order_elements_found', 0)}")  
        print(f"🔧 Total clickable elements: {result.get('total_clickable_elements', 0)}")
        print(f"📸 Screenshot: {result.get('screenshot_saved', 'N/A')}")
        print()
        print("🔄 NEXT STEPS:")
        print("1. Review screenshot for visual analysis")
        print("2. Identify correct path to order creation")
        print("3. Update selectors based on actual page structure")
        
    else:
        print("❌ Diagnosis failed")
        print(f"Error: {result.get('error')}")
        
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
