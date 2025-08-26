#!/usr/bin/env python3
"""
Simple DABS Order Deletion - Direct approach
Uses the existing session or handles authentication more robustly
"""

import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def simple_delete_order():
    """Simple deletion approach with better error handling"""
    
    base_url = 'https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/'
    orders_url = base_url + 'Orders'
    
    logger.info("🚀 Starting simple DABS order deletion...")
    
    async with async_playwright() as p:
        # Launch browser in headed mode
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=2000,  # Very slow for manual observation
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        
        page = await context.new_page()
        
        try:
            # Step 1: Go directly to Orders page
            logger.info("🌐 Navigating directly to Orders page...")
            await page.goto(orders_url, wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Take screenshot
            await page.screenshot(path='data/playwright_screenshots/simple_delete_step1.png')
            logger.info("📷 Screenshot saved: simple_delete_step1.png")
            
            # Check if we're on login page or orders page
            page_title = await page.title()
            logger.info(f"📄 Page title: {page_title}")
            
            # If we see a login form, handle it
            email_field = await page.locator('input[name="Email"]').count()
            if email_field > 0:
                logger.info("🔐 Login form detected, attempting login...")
                
                username = os.getenv('DABS_ORDERING_USERNAME', 'tessakbarkan@gmail.com')
                password = os.getenv('DABS_ORDERING_PASSWORD', 'Tessa2024!')
                
                await page.fill('input[name="Email"]', username)
                await page.fill('input[name="Password"]', password)
                
                # Check for CAPTCHA
                captcha_present = await page.locator('iframe[src*="recaptcha"]').count() > 0
                if captcha_present:
                    logger.info("🤖 CAPTCHA detected - waiting for manual solve...")
                    input("Press Enter after solving CAPTCHA...")
                
                await page.click('input[type="submit"][value="Log in"]')
                await page.wait_for_load_state('domcontentloaded', timeout=30000)
                
                # Navigate to orders after login
                await page.goto(orders_url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(2000)
            
            # Take screenshot of orders page
            await page.screenshot(path='data/playwright_screenshots/simple_delete_step2.png')
            logger.info("📷 Screenshot saved: simple_delete_step2.png")
            
            # Step 2: Look for pending order
            logger.info("🔍 Looking for pending order...")
            
            # Check for the pending order message
            pending_msg = await page.locator('text=Pending order must be submitted or deleted').count()
            if pending_msg == 0:
                logger.info("✅ No pending order found - task already complete!")
                return True
            
            logger.info("📋 Pending order confirmed, proceeding with deletion...")
            
            # Step 3: Find and click delete button
            # Look for the delete icon in the open orders table
            delete_icon = page.locator('div.tableOpen tbody tr a.delete i.material-icons')
            delete_count = await delete_icon.count()
            
            logger.info(f"🎯 Found {delete_count} delete button(s)")
            
            if delete_count > 0:
                logger.info("🗑️ Clicking delete icon...")
                await delete_icon.first.click()
                await page.wait_for_timeout(2000)
                
                # Take screenshot of modal
                await page.screenshot(path='data/playwright_screenshots/simple_delete_step3_modal.png')
                logger.info("📷 Screenshot saved: simple_delete_step3_modal.png")
                
                # Step 4: Confirm deletion
                # Look for the red Delete button in the modal
                confirm_delete = page.locator('input[type="submit"][value="Delete"].btn.btn-red')
                confirm_count = await confirm_delete.count()
                
                logger.info(f"✅ Found {confirm_count} confirmation button(s)")
                
                if confirm_count > 0:
                    logger.info("🔴 Clicking Delete confirmation...")
                    await confirm_delete.click()
                    await page.wait_for_timeout(5000)
                    
                    # Wait for page to reload
                    await page.wait_for_load_state('domcontentloaded', timeout=30000)
                    
                    # Take final screenshot
                    await page.screenshot(path='data/playwright_screenshots/simple_delete_step4_final.png')
                    logger.info("📷 Screenshot saved: simple_delete_step4_final.png")
                    
                    # Step 5: Verify deletion
                    pending_msg_after = await page.locator('text=Pending order must be submitted or deleted').count()
                    
                    if pending_msg_after == 0:
                        logger.info("🎉 SUCCESS: Order deleted successfully!")
                        return True
                    else:
                        logger.error("❌ FAILED: Pending order message still present")
                        return False
                else:
                    logger.error("❌ Delete confirmation button not found")
                    return False
            else:
                logger.error("❌ Delete icon not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            await page.screenshot(path='data/playwright_screenshots/simple_delete_error.png')
            return False
        
        finally:
            # Keep browser open for manual inspection
            logger.info("🔍 Keeping browser open for manual inspection...")
            input("Press Enter to close browser...")
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(simple_delete_order())
    if result:
        print("✅ Order deletion completed successfully")
        sys.exit(0)
    else:
        print("❌ Order deletion failed")
        sys.exit(1)
