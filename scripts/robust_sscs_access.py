#!/usr/bin/env python3
"""
Robust SSCS Access Script - Hills & Hollows LLC
Enhanced SSCS login with better SPA navigation handling

Author: DABS Automation System
Created: 2024-12-19
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Browser

# Load environment variables
load_dotenv()

class RobustSSCSAccess:
    """Enhanced SSCS access with SPA navigation handling"""
    
    def __init__(self):
        self.username = os.getenv('SSCS_USERNAME')
        self.password = os.getenv('SSCS_PASSWORD')
        self.base_url = os.getenv('SSCS_LOGIN_URL')
        self.results_dir = Path('data/sscs_discovery')
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    async def enhanced_sscs_login(self):
        """Enhanced SSCS login with better SPA handling"""
        
        print("🔍 Enhanced SSCS Access Test")
        print("=" * 40)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=1000,  # Slow down for better SPA handling
                args=['--disable-web-security', '--no-sandbox']
            )
            
            try:
                page = await browser.new_page()
                
                # Set longer timeouts for SPA
                page.set_default_timeout(30000)  # 30 seconds
                
                print(f"🌐 Navigating to: {self.base_url}")
                await page.goto(self.base_url)
                
                # Wait for initial SPA load
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(3)  # Additional wait for SPA
                
                # Take screenshot of initial page
                await page.screenshot(path='sscs_initial_page.png')
                print("📷 Initial page screenshot saved")
                
                # Check current URL and title
                current_url = page.url
                title = await page.title()
                print(f"📄 Current URL: {current_url}")
                print(f"📄 Page title: {title}")
                
                # Extract page content for analysis
                page_text = await page.evaluate('() => document.body.innerText')
                print(f"📝 Page content preview: {page_text[:200]}...")
                
                # Look for various login element patterns
                login_selectors = [
                    'input[name="username"]',
                    'input[name="user"]', 
                    'input[name="email"]',
                    'input[id="username"]',
                    'input[id="user"]',
                    'input[type="text"]',
                    'input[placeholder*="user"]',
                    'input[placeholder*="name"]'
                ]
                
                password_selectors = [
                    'input[name="password"]',
                    'input[id="password"]',
                    'input[type="password"]',
                    'input[placeholder*="password"]'
                ]
                
                # Find login elements
                username_field = None
                password_field = None
                
                for selector in login_selectors:
                    try:
                        element = page.locator(selector)
                        if await element.is_visible():
                            username_field = element
                            print(f"🔑 Username field found: {selector}")
                            break
                    except:
                        continue
                
                for selector in password_selectors:
                    try:
                        element = page.locator(selector)
                        if await element.is_visible():
                            password_field = element
                            print(f"🔒 Password field found: {selector}")
                            break
                    except:
                        continue
                
                if username_field and password_field:
                    print("✅ Login form detected - attempting authentication...")
                    
                    # Fill credentials
                    await username_field.fill(self.username)
                    await password_field.fill(self.password)
                    
                    # Look for submit button
                    submit_selectors = [
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button:has-text("login")',
                        'button:has-text("Login")',
                        'button:has-text("Sign In")',
                        '.login-btn',
                        '.submit-btn',
                        '.btn-primary'
                    ]
                    
                    submit_button = None
                    for selector in submit_selectors:
                        try:
                            element = page.locator(selector)
                            if await element.is_visible():
                                submit_button = element
                                print(f"🔘 Submit button found: {selector}")
                                break
                        except:
                            continue
                    
                    if submit_button:
                        # Take screenshot before submit
                        await page.screenshot(path='sscs_before_login.png')
                        
                        print("🚀 Submitting login...")
                        await submit_button.click()
                        
                        # Wait for navigation with multiple strategies
                        try:
                            # Wait for URL change or specific elements
                            await page.wait_for_url(lambda url: 'login' not in url.lower(), timeout=15000)
                        except:
                            try:
                                await page.wait_for_selector('.dashboard, .main-content, .nav-menu', timeout=10000)
                            except:
                                # Wait additional time for SPA load
                                await asyncio.sleep(5)
                        
                        # Take screenshot after login attempt
                        await page.screenshot(path='sscs_after_login.png')
                        
                        # Check login results
                        final_url = page.url
                        final_title = await page.title()
                        
                        print(f"🌐 Final URL: {final_url}")
                        print(f"📄 Final title: {final_title}")
                        
                        # Look for indicators of successful login
                        success_indicators = [
                            'dashboard', 'menu', 'logout', 'profile', 'settings',
                            'transaction', 'analysis', 'merchandise', 'sales'
                        ]
                        
                        page_content = await page.content()
                        success_found = any(indicator in page_content.lower() for indicator in success_indicators)
                        
                        if success_found or 'login' not in final_url.lower():
                            print("✅ LOGIN APPEARS SUCCESSFUL!")
                            
                            # Extract navigation options
                            nav_elements = await page.locator('a, .nav-link, .menu-item').all()
                            nav_options = []
                            
                            for element in nav_elements[:20]:  # Limit to first 20
                                try:
                                    text = await element.text_content()
                                    href = await element.get_attribute('href')
                                    if text and text.strip():
                                        nav_options.append({
                                            'text': text.strip(),
                                            'href': href
                                        })
                                except:
                                    continue
                            
                            print(f"🧭 Navigation options: {[opt['text'] for opt in nav_options[:10]]}")
                            
                            # Save navigation data
                            with open('sscs_navigation_options.json', 'w') as f:
                                json.dump(nav_options, f, indent=2)
                            
                            return True
                        else:
                            print("❌ Login failed - still on login page")
                            return False
                    else:
                        print("❌ No submit button found")
                        return False
                else:
                    print("❌ Login form incomplete")
                    return False
            
            except Exception as e:
                print(f"❌ Error during SSCS access: {str(e)}")
                return False
            
            finally:
                await browser.close()

async def main():
    """Main execution"""
    access = RobustSSCSAccess()
    success = await access.enhanced_sscs_login()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SSCS ACCESS SUCCESSFUL!")
        print("✅ Ready for CPB discovery and configuration")
        print("🚀 Next: Run full SSCS discovery script")
        print("📄 Check: sscs_navigation_options.json")
    else:
        print("❌ SSCS ACCESS FAILED")
        print("📷 Check screenshots: sscs_*.png")
        print("🔧 Debug credentials or network issues")

if __name__ == "__main__":
    asyncio.run(main())
