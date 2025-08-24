#!/usr/bin/env python3
"""
Simple EDI Documentation Script
Just navigate to CPB and capture interface for manual analysis

Author: DABS Automation System
Created: 2025-08-21
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

async def document_cpb_interface():
    """Simple interface documentation for manual analysis"""
    
    print("📋 SSCS CPB Interface Documentation")
    print("=" * 40)
    print("🎯 Goal: Capture interface for manual EDI path discovery")
    
    username = os.getenv('SSCS_USERNAME')
    password = os.getenv('SSCS_PASSWORD')
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Login to CPB
            print("🌐 Logging into SSCS CPB...")
            await page.goto("https://sscsta.sscsinc.com/Cpb.App/")
            await page.wait_for_load_state('networkidle')
            
            if await page.locator('input[name="username"]').is_visible():
                await page.fill('input[name="username"]', username)
                await page.fill('input[name="password"]', password)
                await page.click('button:has-text("login")')
                await page.wait_for_load_state('networkidle')
            
            print("✅ Logged into SSCS CPB")
            
            # Navigate directly to vendor import
            print("🧭 Navigating to Vendor Import Setup...")
            await page.goto("https://sscsta.sscsinc.com/Cpb.App/#!/setup/vendorimport")
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)  # Wait for interface load
            
            print("✅ Vendor Import Setup interface loaded")
            
            # Capture detailed screenshots
            await page.screenshot(path='sscs_vendor_import_full.png', full_page=True)
            print("📷 Full page screenshot captured: sscs_vendor_import_full.png")
            
            # Get page HTML for analysis
            page_html = await page.content()
            with open('sscs_vendor_import_html.html', 'w', encoding='utf-8') as f:
                f.write(page_html)
            print("📄 Page HTML saved: sscs_vendor_import_html.html")
            
            # Extract all form elements
            form_elements = await page.evaluate('''() => {
                const elements = [];
                
                // Get all form elements
                document.querySelectorAll('input, select, textarea, button').forEach(el => {
                    elements.push({
                        tag: el.tagName,
                        type: el.type || '',
                        name: el.name || '',
                        id: el.id || '',
                        placeholder: el.placeholder || '',
                        value: el.value || '',
                        text: el.textContent.trim()
                    });
                });
                
                return elements;
            }''')
            
            # Save form analysis
            import json
            with open('sscs_form_elements.json', 'w') as f:
                json.dump(form_elements, f, indent=2)
            
            print(f"📋 Form elements extracted: {len(form_elements)} elements")
            print("💾 Saved to: sscs_form_elements.json")
            
            # Look for File Location related elements
            file_location_elements = [el for el in form_elements 
                                    if 'location' in el.get('name', '').lower() or 
                                       'location' in el.get('placeholder', '').lower() or
                                       'path' in el.get('name', '').lower()]
            
            if file_location_elements:
                print(f"\n📁 File Location elements found:")
                for el in file_location_elements:
                    print(f"   {el['tag']} - {el['name']} - {el['placeholder']}")
            else:
                print("\n⚠️ No obvious File Location elements found")
                print("📋 Manual interface exploration needed")
            
            print(f"\n✅ Interface documentation complete!")
            print(f"📷 Screenshot: sscs_vendor_import_full.png")
            print(f"📄 HTML: sscs_vendor_import_html.html") 
            print(f"📋 Elements: sscs_form_elements.json")
            
            print(f"\n🎯 NEXT MANUAL STEPS:")
            print(f"1. 👀 Review screenshot to identify File Location field")
            print(f"2. ⚙️ Configure DABS vendor manually in interface")
            print(f"3. 📁 Document discovered EDI path")
            print(f"4. 🚀 Deploy your automation with discovered path")
            
            # Keep browser open for manual exploration
            print(f"\n🖥️ Browser will remain open for manual exploration...")
            print(f"✋ Press Enter when manual discovery complete...")
            input()
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(document_cpb_interface())
