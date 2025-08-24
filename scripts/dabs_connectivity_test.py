#!/usr/bin/env python3
"""
DABS Connectivity and Authentication Test
Hills & Hollows LLC - Utah Package Agency
Date: August 24, 2025

Test script to verify DABS website connectivity and authentication capabilities.
"""

import asyncio
import requests
import logging
import sys
import os
from pathlib import Path
from playwright.async_api import async_playwright
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_dabs_connectivity():
    """Test DABS website connectivity with various methods"""
    
    dabs_url = "https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/"
    
    print("🔍 DABS Connectivity Test Results")
    print("=" * 60)
    
    # Test 1: HTTP Request Test
    print("\n1. HTTP Connectivity Test...")
    try:
        response = requests.get(dabs_url, timeout=15, allow_redirects=True)
        print(f"   ✅ HTTP Status: {response.status_code}")
        print(f"   ✅ Response Size: {len(response.content)} bytes")
        print(f"   ✅ Server Headers: {response.headers.get('Server', 'Unknown')}")
    except requests.exceptions.Timeout:
        print("   ❌ HTTP Request Timeout (15s)")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ HTTP Request Failed: {str(e)}")
    
    # Test 2: Playwright Connectivity Test
    print("\n2. Playwright Browser Test...")
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Set longer timeout
        page.set_default_timeout(60000)  # 60 seconds
        
        print("   🌐 Navigating to DABS website...")
        await page.goto(dabs_url, wait_until="domcontentloaded", timeout=60000)
        
        title = await page.title()
        print(f"   ✅ Page Title: {title}")
        
        # Check for login form
        login_form = await page.query_selector('input[name="UserName"]')
        if login_form:
            print("   ✅ Login form detected")
        else:
            print("   ⚠️ Login form not found")
        
        await browser.close()
        await playwright.stop()
        
    except Exception as e:
        print(f"   ❌ Playwright Test Failed: {str(e)}")
    
    # Test 3: Network Connectivity Test
    print("\n3. Network Infrastructure Test...")
    try:
        import socket
        host = "webapps2.abc.utah.gov"
        port = 443  # HTTPS
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        
        if result == 0:
            print(f"   ✅ TCP Connection to {host}:{port} successful")
        else:
            print(f"   ❌ TCP Connection failed (error: {result})")
        
        sock.close()
        
    except Exception as e:
        print(f"   ❌ Network test failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 Test Complete")

async def test_dabs_authentication():
    """Test DABS authentication with improved error handling"""
    
    print("\n🔐 DABS Authentication Test")
    print("=" * 60)
    
    # Load credentials
    config_path = Path(__file__).parent.parent / "config" / "dabs_ordering.env"
    if config_path.exists():
        from dotenv import load_dotenv
        load_dotenv(config_path)
        
        username = os.getenv("DABS_ORDERING_USERNAME")
        password = os.getenv("DABS_ORDERING_PASSWORD")
        
        if username and password:
            print(f"   ✅ Credentials loaded for user: {username}")
        else:
            print("   ❌ Credentials not found in environment")
            return
    else:
        print("   ❌ Configuration file not found")
        return
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,  # Run visible for debugging
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        # Set extended timeout for slow connections
        page.set_default_timeout(90000)  # 90 seconds
        
        print("   🌐 Loading DABS login page...")
        await page.goto("https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/", 
                        wait_until="domcontentloaded", timeout=90000)
        
        print("   ⏳ Waiting for login form...")
        await page.wait_for_selector('input[name="UserName"]', timeout=30000)
        
        print("   🔑 Filling credentials...")
        await page.fill('input[name="UserName"]', username)
        await page.fill('input[name="Password"]', password)
        
        print("   📤 Submitting login...")
        await page.click('button[type="submit"], input[type="submit"]')
        
        # Wait for either success or error
        try:
            await page.wait_for_url("**/Orders", timeout=30000)
            print("   ✅ Login successful - redirected to Orders page")
        except:
            # Check for error messages
            error_elements = await page.query_selector_all('.validation-summary-errors, .alert-danger, .error')
            if error_elements:
                error_text = await error_elements[0].text_content()
                print(f"   ❌ Login failed: {error_text}")
            else:
                print("   ⚠️ Login status unclear - no clear success/error indicators")
        
        print("   💾 Taking screenshot for debugging...")
        await page.screenshot(path="dabs_login_test.png")
        
        await browser.close()
        await playwright.stop()
        
    except Exception as e:
        print(f"   ❌ Authentication test failed: {str(e)}")

async def main():
    """Run all DABS connectivity and authentication tests"""
    print(f"🚀 DABS System Test Suite - {datetime.utcnow().isoformat()}")
    
    await test_dabs_connectivity()
    await test_dabs_authentication()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
