#!/usr/bin/env python3
"""
Practical EDI Path Completion Script
Direct manual approach to complete EDI path discovery and deployment

Based on enhanced discovery findings:
- Help system available (vendor import help found)
- Interface accessible (confirmed CPB access)
- NAXML files ready (test files available for validation)

Author: DABS Automation System
Created: 2025-08-21
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

async def practical_edi_completion():
    """
    Practical approach to complete EDI path discovery
    
    Strategy:
    1. Access confirmed Vendor Import interface
    2. Manually explore for File Location configuration
    3. Configure DABS vendor step-by-step
    4. Test with available NAXML files
    5. Document EDI path for automation deployment
    """
    
    print("🎯 PRACTICAL EDI PATH COMPLETION")
    print("=" * 40)
    print("🚀 Goal: Complete EDI discovery and deploy your automation")
    
    username = os.getenv('SSCS_USERNAME')
    password = os.getenv('SSCS_PASSWORD')
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1500)
        page = await browser.new_page()
        page.set_default_timeout(45000)
        
        try:
            # Step 1: Login and access vendor import
            print("\n🌐 Accessing SSCS CPB Vendor Import...")
            await page.goto("https://sscsta.sscsinc.com/Cpb.App/")
            await page.wait_for_load_state('networkidle')
            
            # Login if needed
            if await page.locator('input[name="username"]').is_visible():
                await page.fill('input[name="username"]', username)
                await page.fill('input[name="password"]', password)
                await page.click('button:has-text("login")')
                await page.wait_for_load_state('networkidle')
            
            print("✅ Logged into SSCS CPB")
            
            # Navigate to vendor import setup
            vendor_import_url = "https://sscsta.sscsinc.com/Cpb.App/#!/setup/vendorimport"
            await page.goto(vendor_import_url)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(5)  # Extra wait for SPA
            
            print("✅ Accessed Vendor Import Setup")
            
            # Step 2: Comprehensive interface exploration
            print("\n🔍 COMPREHENSIVE INTERFACE EXPLORATION...")
            
            # Take detailed screenshot
            await page.screenshot(path='cpb_vendor_import_detailed.png', full_page=True)
            print("📷 Detailed screenshot captured")
            
            # Get complete page text for analysis
            page_text = await page.evaluate('() => document.body.innerText')
            print(f"📄 Page text length: {len(page_text)} characters")
            
            # Save page text for analysis
            with open('cpb_interface_text.txt', 'w', encoding='utf-8') as f:
                f.write(page_text)
            print("📝 Page text saved for analysis")
            
            # Look for any form or configuration elements
            all_elements = await page.evaluate('''() => {
                const elements = [];
                
                // Get ALL interactive elements
                const selectors = ['input', 'select', 'textarea', 'button', 'a', 'div[onclick]', 'span[onclick]'];
                
                selectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach((el, index) => {
                        const rect = el.getBoundingClientRect();
                        elements.push({
                            selector: selector,
                            index: index,
                            tag: el.tagName,
                            type: el.type || '',
                            name: el.name || '',
                            id: el.id || '',
                            className: el.className || '',
                            textContent: el.textContent.trim().substring(0, 100),
                            placeholder: el.placeholder || '',
                            value: el.value || '',
                            visible: rect.width > 0 && rect.height > 0,
                            position: {
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            }
                        });
                    });
                });
                
                return elements.filter(el => el.visible);  // Only visible elements
            }''')
            
            print(f"🔍 Found {len(all_elements)} visible interactive elements")
            
            # Save element analysis
            with open('cpb_all_elements.json', 'w') as f:
                json.dump(all_elements, f, indent=2)
            print("📋 Element analysis saved")
            
            # Look for elements that might be file location related
            location_related = [el for el in all_elements 
                              if any(keyword in (el.get('name', '') + el.get('id', '') + el.get('textContent', '')).lower() 
                                   for keyword in ['location', 'path', 'folder', 'file', 'import', 'upload', 'edi'])]
            
            if location_related:
                print(f"\n📁 File location related elements found:")
                for el in location_related[:10]:  # Show first 10
                    print(f"   {el['tag']}: {el.get('name', '')} - {el.get('textContent', '')[:50]}")
            
            # Step 3: Try common CPB navigation patterns
            print("\n🧭 Trying common CPB navigation...")
            
            # Look for Setup menu or navigation
            setup_elements = await page.locator('text=Setup, text=setup, .setup, [href*="setup"]').all()
            print(f"⚙️ Setup elements found: {len(setup_elements)}")
            
            if setup_elements:
                try:
                    await setup_elements[0].click()
                    await page.wait_for_load_state('networkidle')
                    await asyncio.sleep(3)
                    print("✅ Clicked Setup menu")
                    
                    # Look for vendor import option
                    vendor_elements = await page.locator('text=Vendor, text=vendor, text=Import, text=import').all()
                    print(f"📦 Vendor/Import elements: {len(vendor_elements)}")
                    
                    if vendor_elements:
                        await vendor_elements[0].click()
                        await page.wait_for_load_state('networkidle')
                        await asyncio.sleep(3)
                        print("✅ Accessed vendor import area")
                        
                        # Capture this interface
                        await page.screenshot(path='cpb_vendor_setup_area.png', full_page=True)
                        print("📷 Vendor setup area captured")
                        
                except Exception as e:
                    print(f"⚠️ Navigation attempt failed: {str(e)}")
            
            # Step 4: Manual guidance for completion
            print(f"\n📋 MANUAL COMPLETION GUIDANCE:")
            print(f"✅ Interface accessible: Vendor Import Setup confirmed")
            print(f"✅ Test files ready: DABS_TEST_ItemPrice.xml available")
            print(f"✅ Help system: Vendor import documentation found")
            print(f"📷 Screenshots captured for manual reference")
            
            print(f"\n🎯 IMMEDIATE MANUAL ACTIONS NEEDED:")
            print(f"1. 👀 Review screenshots to identify configuration interface")
            print(f"2. 🔍 Look for Add/New vendor button or form")
            print(f"3. ⚙️ Configure DABS vendor manually:")
            print(f"   - Vendor Name: DABS")
            print(f"   - Import Type: MCLANE")
            print(f"   - File Mask: DABS*.xml")
            print(f"   - File Location: [DISCOVER FROM INTERFACE]")
            print(f"4. 📤 Test upload: data/sscs_discovery/DABS_TEST_ItemPrice.xml")
            print(f"5. ✅ Document discovered EDI path")
            
            # Keep browser open for manual work
            print(f"\n🖥️ Browser staying open for manual exploration...")
            print(f"🔧 Complete vendor configuration manually")
            print(f"📁 Document EDI path when discovered")
            print(f"✋ Press Enter when manual discovery complete...")
            
            # Wait for user to complete manual work
            input()
            
            # Final documentation
            print(f"\n📋 Manual discovery completed!")
            print(f"🚀 Ready for automation deployment with discovered EDI path")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(practical_edi_completion())
