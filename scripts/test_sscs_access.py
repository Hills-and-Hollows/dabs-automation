#!/usr/bin/env python3
"""
SSCS Access Test Script - Quick validation
Test SSCS login and basic navigation for Tessa's automation

Author: DABS Automation System
Created: 2024-12-19
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Load environment variables
load_dotenv()

async def test_sscs_login():
    """Quick test of SSCS login functionality"""
    
    print("🔍 Testing SSCS Access for Tessa's Automation")
    print("=" * 50)
    
    # Validate credentials
    username = os.getenv('SSCS_USERNAME')
    password = os.getenv('SSCS_PASSWORD') 
    url = os.getenv('SSCS_LOGIN_URL')
    
    if not all([username, password, url]):
        print("❌ Error: SSCS credentials missing from environment")
        print("📋 Please check .env file has SSCS credentials")
        return False
    
    print(f"✅ Credentials loaded for user: {username}")
    print(f"🌐 Target URL: {url}")
    
    try:
        async with async_playwright() as p:
            print("🚀 Launching browser...")
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            print("🌐 Navigating to SSCS...")
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            
            print("📷 Taking screenshot of login page...")
            await page.screenshot(path='sscs_login_page.png')
            
            # Check page title and content
            title = await page.title()
            print(f"📄 Page title: {title}")
            
            # Look for login elements
            login_elements = await page.locator('input[type="text"], input[type="email"], input[name*="user"]').all()
            password_elements = await page.locator('input[type="password"]').all()
            
            print(f"🔑 Login fields found: {len(login_elements)}")
            print(f"🔒 Password fields found: {len(password_elements)}")
            
            if login_elements and password_elements:
                print("✅ Login form detected - attempting authentication...")
                
                # Fill credentials
                await login_elements[0].fill(username)
                await password_elements[0].fill(password)
                
                # Look for submit button
                submit_buttons = await page.locator('button[type="submit"], input[type="submit"], .login-btn, .submit-btn').all()
                
                if submit_buttons:
                    print("🔘 Submit button found - logging in...")
                    await submit_buttons[0].click()
                    await page.wait_for_load_state('networkidle')
                    
                    # Check for successful login
                    current_url = page.url
                    new_title = await page.title()
                    
                    print(f"🌐 Post-login URL: {current_url}")
                    print(f"📄 Post-login title: {new_title}")
                    
                    # Take screenshot of logged-in state
                    await page.screenshot(path='sscs_logged_in.png')
                    
                    # Look for main navigation
                    nav_elements = await page.locator('nav a, .nav-link, .menu-item').all()
                    nav_text = [await el.text_content() for el in nav_elements[:10]]
                    
                    print(f"🧭 Navigation options found: {nav_text}")
                    
                    if 'login' not in current_url.lower() and len(nav_elements) > 0:
                        print("✅ LOGIN SUCCESSFUL!")
                        
                        # Look for price book or vendor options
                        price_elements = await page.locator('text=price, text=vendor, text=import, text=book').all()
                        price_text = [await el.text_content() for el in price_elements[:5]]
                        print(f"💰 Price/Vendor options: {price_text}")
                        
                        success = True
                    else:
                        print("⚠️ Login may have failed - still on login page")
                        success = False
                else:
                    print("❌ No submit button found")
                    success = False
            else:
                print("❌ Login form not found")
                success = False
            
            await browser.close()
            return success
            
    except Exception as e:
        print(f"❌ Error during SSCS access test: {str(e)}")
        return False

async def main():
    """Main test execution"""
    success = await test_sscs_login()
    
    if success:
        print("\n🎉 SSCS ACCESS TEST SUCCESSFUL!")
        print("✅ Ready to proceed with full discovery")
        print("🚀 Next: Run python scripts/sscs_discovery.py")
    else:
        print("\n❌ SSCS ACCESS TEST FAILED")
        print("🔧 Check credentials and network connection")
        print("📋 Review screenshots for debugging")

if __name__ == "__main__":
    asyncio.run(main())
