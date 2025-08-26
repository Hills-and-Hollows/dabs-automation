#!/usr/bin/env python3
"""
Manual DABS Order Deletion Script
Simplified approach with better error handling and debugging
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

async def delete_dabs_order():
    """Delete the pending DABS order with manual verification"""
    
    # DABS credentials from environment
    username = os.getenv('DABS_ORDERING_USERNAME', 'tessakbarkan@gmail.com')
    password = os.getenv('DABS_ORDERING_PASSWORD', 'Tessa2024!')
    base_url = 'https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/'
    
    logger.info("🚀 Starting manual DABS order deletion...")
    
    async with async_playwright() as p:
        # Launch browser in headed mode for manual verification
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000,  # Slow down for visibility
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # Step 1: Navigate to DABS
            logger.info("🌐 Navigating to DABS...")
            await page.goto(base_url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(2000)
            
            # Take screenshot of initial page
            await page.screenshot(path='data/playwright_screenshots/manual_delete_step1_initial.png')
            logger.info("📷 Screenshot saved: manual_delete_step1_initial.png")
            
            # Step 2: Login
            logger.info("🔐 Attempting login...")
            await page.fill('input[name="Email"]', username)
            await page.fill('input[name="Password"]', password)
            
            # Handle CAPTCHA if present
            captcha_present = await page.locator('iframe[src*="recaptcha"]').count() > 0
            if captcha_present:
                logger.info("🤖 CAPTCHA detected - please solve manually...")
                input("Press Enter after solving CAPTCHA...")
            
            await page.click('input[type="submit"][value="Log in"]')
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            # Take screenshot after login
            await page.screenshot(path='data/playwright_screenshots/manual_delete_step2_logged_in.png')
            logger.info("📷 Screenshot saved: manual_delete_step2_logged_in.png")
            
            # Step 3: Navigate to Orders
            logger.info("📋 Navigating to Orders page...")
            await page.goto(base_url + 'Orders', wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Take screenshot of orders page
            await page.screenshot(path='data/playwright_screenshots/manual_delete_step3_orders_page.png')
            logger.info("📷 Screenshot saved: manual_delete_step3_orders_page.png")
            
            # Step 4: Find and analyze the pending order
            logger.info("🔍 Looking for pending order...")
            
            # Check for pending order message
            pending_message = await page.locator('text=Pending order must be submitted or deleted').count()
            if pending_message > 0:
                logger.info("✅ Confirmed: Pending order exists")
            else:
                logger.info("❌ No pending order message found")
                return False
            
            # Look for order rows in the open order table
            order_rows = await page.locator('div.tableOpen tbody tr').count()
            logger.info(f"📊 Found {order_rows} order row(s)")
            
            if order_rows == 0:
                logger.error("❌ No order rows found in open orders table")
                return False
            
            # Get order details from the first (and should be only) row
            order_id = await page.locator('div.tableOpen tbody tr td').first.inner_text()
            logger.info(f"🎯 Found order ID: {order_id}")
            
            # Step 5: Attempt deletion
            logger.info("🗑️ Attempting to delete order...")
            
            # Click the delete icon (trash can)
            delete_button = page.locator('div.tableOpen tbody tr a.delete i.material-icons')
            if await delete_button.count() > 0:
                logger.info("🎯 Found delete button, clicking...")
                await delete_button.click()
                await page.wait_for_timeout(2000)
                
                # Take screenshot of delete modal
                await page.screenshot(path='data/playwright_screenshots/manual_delete_step4_modal.png')
                logger.info("📷 Screenshot saved: manual_delete_step4_modal.png")
                
                # Look for the confirmation modal and click Delete button
                delete_confirm = page.locator('input[type="submit"][value="Delete"].btn.btn-red')
                if await delete_confirm.count() > 0:
                    logger.info("✅ Found Delete confirmation button, clicking...")
                    await delete_confirm.click()
                    await page.wait_for_timeout(3000)
                    
                    # Wait for page to reload
                    await page.wait_for_load_state('networkidle', timeout=30000)
                    
                    # Take final screenshot
                    await page.screenshot(path='data/playwright_screenshots/manual_delete_step5_final.png')
                    logger.info("📷 Screenshot saved: manual_delete_step5_final.png")
                    
                    # Verify deletion
                    pending_message_after = await page.locator('text=Pending order must be submitted or deleted').count()
                    if pending_message_after == 0:
                        logger.info("🎉 SUCCESS: Pending order deleted successfully!")
                        return True
                    else:
                        logger.error("❌ FAILED: Pending order message still present")
                        return False
                else:
                    logger.error("❌ Delete confirmation button not found")
                    return False
            else:
                logger.error("❌ Delete button not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during deletion: {str(e)}")
            await page.screenshot(path='data/playwright_screenshots/manual_delete_error.png')
            return False
        
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(delete_dabs_order())
    if result:
        print("✅ Order deletion completed successfully")
        sys.exit(0)
    else:
        print("❌ Order deletion failed")
        sys.exit(1)
