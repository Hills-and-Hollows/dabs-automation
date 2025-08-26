#!/usr/bin/env python3
"""
Final DABS Order Deletion Script
Uses the proven authentication method from memory and documentation
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

async def final_delete_order():
    """Final deletion attempt using proven authentication method"""
    
    # Use the proven authentication approach
    base_url = 'https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/'
    username = os.getenv('DABS_ORDERING_USERNAME', 'tessakbarkan@gmail.com')
    password = os.getenv('DABS_ORDERING_PASSWORD', 'Tessa2024!')
    
    logger.info("🚀 Final DABS order deletion attempt...")
    
    async with async_playwright() as p:
        # Launch browser in headed mode for manual verification
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1500,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        
        page = await context.new_page()
        
        try:
            # Step 1: Navigate to main DABS page (not /Login endpoint)
            logger.info("🌐 Navigating to main DABS page...")
            await page.goto(base_url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(2000)
            
            # Take screenshot
            await page.screenshot(path='data/playwright_screenshots/final_delete_step1_main.png')
            logger.info("📷 Screenshot saved: final_delete_step1_main.png")
            
            # Step 2: Handle authentication
            logger.info("🔐 Handling authentication...")
            
            # Look for email field
            email_field = await page.locator('input[name="Email"]').count()
            if email_field > 0:
                logger.info("📧 Email field found, filling credentials...")
                await page.fill('input[name="Email"]', username)
                await page.fill('input[name="Password"]', password)
                
                # Handle CAPTCHA if present
                captcha_present = await page.locator('iframe[src*="recaptcha"]').count() > 0
                if captcha_present:
                    logger.info("🤖 CAPTCHA detected - please solve manually...")
                    input("Press Enter after solving CAPTCHA...")
                
                # Click login
                await page.click('input[type="submit"][value="Log in"]')
                await page.wait_for_load_state('networkidle', timeout=30000)
                
                # Take screenshot after login
                await page.screenshot(path='data/playwright_screenshots/final_delete_step2_logged_in.png')
                logger.info("📷 Screenshot saved: final_delete_step2_logged_in.png")
            else:
                logger.info("✅ Already authenticated or different page structure")
            
            # Step 3: Navigate to Orders using menu/links (not direct URL)
            logger.info("📋 Looking for Orders navigation...")
            
            # Look for Orders link in navigation
            orders_link = await page.locator('a[href*="Orders"], text="Orders"').count()
            if orders_link > 0:
                logger.info("🔗 Found Orders link, clicking...")
                await page.click('a[href*="Orders"], text="Orders"')
                await page.wait_for_load_state('networkidle', timeout=30000)
            else:
                # Try alternative navigation
                logger.info("🔍 Looking for alternative navigation...")
                # Look for any link that might lead to orders
                nav_links = await page.locator('nav a, .nav a, .navbar a').all()
                for link in nav_links:
                    text = await link.inner_text()
                    href = await link.get_attribute('href')
                    logger.info(f"🔗 Found nav link: '{text}' -> {href}")
                    if 'order' in text.lower() or 'order' in (href or '').lower():
                        logger.info(f"🎯 Clicking Orders link: {text}")
                        await link.click()
                        await page.wait_for_load_state('networkidle', timeout=30000)
                        break
            
            # Take screenshot of orders page
            await page.screenshot(path='data/playwright_screenshots/final_delete_step3_orders.png')
            logger.info("📷 Screenshot saved: final_delete_step3_orders.png")
            
            # Step 4: Check for pending order
            logger.info("🔍 Checking for pending order...")
            
            # Look for the pending order message
            pending_msg = await page.locator('text=Pending order must be submitted or deleted').count()
            if pending_msg == 0:
                logger.info("✅ SUCCESS: No pending order found - already deleted!")
                return True
            
            logger.info("📋 Pending order confirmed, proceeding with deletion...")
            
            # Step 5: Find order details
            # Look for order ID in the table
            order_cells = await page.locator('div.tableOpen tbody tr td').all()
            order_id = None
            if order_cells:
                order_id = await order_cells[0].inner_text()
                logger.info(f"🎯 Found order ID: {order_id}")
            
            # Step 6: Click delete button
            delete_icon = page.locator('div.tableOpen tbody tr a.delete i.material-icons')
            delete_count = await delete_icon.count()
            
            logger.info(f"🗑️ Found {delete_count} delete button(s)")
            
            if delete_count > 0:
                logger.info("🗑️ Clicking delete icon...")
                await delete_icon.first.click()
                await page.wait_for_timeout(3000)
                
                # Take screenshot of modal
                await page.screenshot(path='data/playwright_screenshots/final_delete_step4_modal.png')
                logger.info("📷 Screenshot saved: final_delete_step4_modal.png")
                
                # Step 7: Confirm deletion
                confirm_delete = page.locator('input[type="submit"][value="Delete"].btn.btn-red')
                confirm_count = await confirm_delete.count()
                
                logger.info(f"🔴 Found {confirm_count} Delete confirmation button(s)")
                
                if confirm_count > 0:
                    logger.info("🔴 Clicking Delete confirmation...")
                    await confirm_delete.click()
                    await page.wait_for_timeout(5000)
                    
                    # Wait for page to reload
                    await page.wait_for_load_state('networkidle', timeout=30000)
                    
                    # Take final screenshot
                    await page.screenshot(path='data/playwright_screenshots/final_delete_step5_success.png')
                    logger.info("📷 Screenshot saved: final_delete_step5_success.png")
                    
                    # Step 8: Verify deletion
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
            await page.screenshot(path='data/playwright_screenshots/final_delete_error.png')
            return False
        
        finally:
            # Keep browser open for inspection
            logger.info("🔍 Task complete. Review screenshots for verification.")
            input("Press Enter to close browser...")
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(final_delete_order())
    if result:
        print("✅ Order deletion completed successfully")
        sys.exit(0)
    else:
        print("❌ Order deletion failed - check screenshots")
        sys.exit(1)
