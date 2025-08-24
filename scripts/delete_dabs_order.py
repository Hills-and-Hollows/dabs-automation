#!/usr/bin/env python3
"""
DABS Order Deletion Script
Quick solution to delete pending DABS orders

This script provides a standalone solution for deleting pending DABS orders
when the MCP server is not available.

Usage: python3 scripts/delete_dabs_order.py

Author: DABS Automation System  
Date: August 24, 2025
"""

import asyncio
import logging
import os
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load DABS environment configuration
config_path = Path(__file__).parent.parent / "config" / "dabs_ordering.env"
load_dotenv(config_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DABSOrderDeletor:
    """Simple class to delete pending DABS orders"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.dabs_base_url = os.getenv("DABS_ORDERING_LOGIN_URL", 
                                     "https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/")
        self.dabs_username = os.getenv("DABS_ORDERING_USERNAME")
        self.dabs_password = os.getenv("DABS_ORDERING_PASSWORD")
        self.auth_storage_path = Path("dabs_auth.json")

    async def delete_pending_order(self):
        """Delete the current pending DABS order"""
        logger.info("🚀 Starting DABS order deletion process...")
        
        async with async_playwright() as playwright:
            # Launch browser
            browser = await playwright.chromium.launch(headless=self.headless)
            
            # Use persistent context if auth exists, otherwise create new
            if self.auth_storage_path.exists():
                logger.info("🔐 Using stored authentication...")
                context = await browser.new_context(storage_state=str(self.auth_storage_path))
            else:
                logger.info("🔑 Creating new authentication session...")
                context = await browser.new_context()
            
            try:
                page = await context.new_page()
                
                # Navigate to DABS ordering system
                logger.info(f"🌐 Navigating to DABS: {self.dabs_base_url}")
                await page.goto(self.dabs_base_url)
                await page.wait_for_load_state('networkidle')
                
                # Check if we need to login
                if await self._needs_login(page):
                    logger.info("🔓 Performing DABS login...")
                    await self._perform_login(page)
                
                # Look for existing orders
                logger.info("🔍 Checking for pending orders...")
                pending_deleted = await self._find_and_delete_pending_order(page)
                
                if pending_deleted:
                    logger.info("✅ Successfully deleted pending DABS order")
                    return {"success": True, "message": "Pending order deleted successfully"}
                else:
                    logger.info("ℹ️ No pending orders found to delete")
                    return {"success": True, "message": "No pending orders found"}
                    
            except Exception as e:
                logger.error(f"❌ Failed to delete DABS order: {str(e)}")
                return {"success": False, "error": str(e)}
                
            finally:
                # Save authentication state if successful
                if self.auth_storage_path.parent.exists():
                    await context.storage_state(path=str(self.auth_storage_path))
                await browser.close()

    async def _needs_login(self, page) -> bool:
        """Check if login is required"""
        try:
            # Look for login form elements
            username_field = await page.query_selector("input[type='text'], input[name*='user'], input[id*='user']")
            password_field = await page.query_selector("input[type='password']")
            return username_field is not None and password_field is not None
        except:
            return True

    async def _perform_login(self, page):
        """Perform DABS login"""
        try:
            # Fill username
            username_selector = "input[type='text'], input[name*='user'], input[id*='user']"
            await page.fill(username_selector, self.dabs_username)
            
            # Fill password  
            password_selector = "input[type='password']"
            await page.fill(password_selector, self.dabs_password)
            
            # Click login button
            login_button = await page.query_selector("input[type='submit'], button[type='submit'], button:has-text('Login')")
            if login_button:
                await login_button.click()
                await page.wait_for_load_state('networkidle')
                logger.info("✅ Login successful")
            else:
                raise Exception("Could not find login button")
                
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            raise

    async def _find_and_delete_pending_order(self, page) -> bool:
        """Find and delete any pending orders"""
        try:
            # Take a screenshot for debugging
            await page.screenshot(path="debug_dabs_interface.png")
            logger.info("📷 Screenshot saved as debug_dabs_interface.png")
            
            # Print current page HTML for debugging
            page_html = await page.content()
            logger.info(f"🌐 Current page URL: {page.url}")
            logger.info(f"📄 Page title: {await page.title()}")
            
            # Look for pending order indicators first
            pending_indicators = await page.query_selector_all("text=pending")
            if pending_indicators:
                logger.info(f"⏳ Found {len(pending_indicators)} 'pending' text elements")
            
            # Look for order management elements - try Edit button first (based on successful pattern)
            edit_buttons = await page.query_selector_all("button:has-text('Edit'), a:has-text('Edit'), input[value*='Edit'], i[data-bs-original-title='Edit']")
            if edit_buttons:
                logger.info(f"✏️ Found {len(edit_buttons)} edit option(s)")
                
                # Click Edit button first (this is required for DABS order management)
                edit_button = edit_buttons[0]
                is_edit_visible = await edit_button.is_visible()
                logger.info(f"👁️ Edit button visible: {is_edit_visible}")
                
                if is_edit_visible:
                    logger.info("📝 Clicking Edit button to access order management...")
                    await edit_button.click()
                    await page.wait_for_load_state('networkidle')
                    
                    # Now look for delete options on the edit page
                    await page.wait_for_timeout(2000)
                    delete_buttons_edit = await page.query_selector_all("button:has-text('Delete'), a:has-text('Delete'), input[value*='Delete']")
                    
                    if delete_buttons_edit:
                        logger.info(f"🗑️ Found {len(delete_buttons_edit)} delete option(s) on edit page")
                        delete_button = delete_buttons_edit[0]
                        is_delete_visible = await delete_button.is_visible()
                        logger.info(f"👁️ Delete button on edit page visible: {is_delete_visible}")
                        
                        if is_delete_visible:
                            logger.info("🗑️ Clicking Delete button...")
                            await delete_button.click()
                            await page.wait_for_timeout(1000)
                            
                            # Handle confirmation
                            confirmation = await page.query_selector("button:has-text('Yes'), button:has-text('Confirm'), button:has-text('OK')")
                            if confirmation:
                                logger.info("✔️ Confirming deletion...")
                                await confirmation.click()
                                await page.wait_for_load_state('networkidle')
                                
                            return True
                    else:
                        logger.info("ℹ️ No delete buttons found on edit page, trying cancel approach...")
                        
                        # Look for Cancel buttons (DABS may use cancel instead of delete)
                        cancel_buttons_edit = await page.query_selector_all("button:has-text('Cancel'), a:has-text('Cancel'), input[value*='Cancel']")
                        
                        if cancel_buttons_edit:
                            logger.info(f"❌ Found {len(cancel_buttons_edit)} cancel option(s) on edit page")
                            cancel_button = cancel_buttons_edit[0]
                            is_cancel_visible = await cancel_button.is_visible()
                            logger.info(f"👁️ Cancel button visible: {is_cancel_visible}")
                            
                            if is_cancel_visible:
                                logger.info("❌ Clicking Cancel button to delete order...")
                                await cancel_button.click()
                                await page.wait_for_timeout(1000)
                                
                                # Handle confirmation dialog
                                confirmation = await page.query_selector("button:has-text('Yes'), button:has-text('Confirm'), button:has-text('OK'), button:has-text('Delete')")
                                if confirmation:
                                    logger.info("✔️ Confirming order cancellation...")
                                    await confirmation.click()
                                    await page.wait_for_load_state('networkidle')
                                    
                                return True
                        
                        logger.info("ℹ️ No cancel buttons found either")
            
            # Fallback: Look for common DABS order interface elements on main page
            delete_buttons = await page.query_selector_all("button:has-text('Delete'), a:has-text('Delete'), input[value*='Delete']")
            
            if delete_buttons:
                logger.info(f"🗑️ Found {len(delete_buttons)} delete option(s) on main page")
                # Try the original delete approach
                await delete_buttons[0].click()
                await page.wait_for_timeout(1000)
                
                confirmation = await page.query_selector("button:has-text('Yes'), button:has-text('Confirm'), button:has-text('OK')")
                if confirmation:
                    logger.info("✔️ Confirming deletion...")
                    await confirmation.click()
                    await page.wait_for_load_state('networkidle')
                
                return True
                
            # Alternative: Look for "Cancel Order" or similar options
            cancel_buttons = await page.query_selector_all("button:has-text('Cancel'), a:has-text('Cancel'), input[value*='Cancel']")
            
            if cancel_buttons:
                logger.info(f"❌ Found {len(cancel_buttons)} cancel option(s)")
                await cancel_buttons[0].click()
                await page.wait_for_timeout(1000)
                
                # Handle confirmation
                confirmation = await page.query_selector("button:has-text('Yes'), button:has-text('Confirm'), button:has-text('OK')")
                if confirmation:
                    logger.info("✔️ Confirming cancellation...")
                    await confirmation.click()
                    await page.wait_for_load_state('networkidle')
                
                return True
                
            logger.info("ℹ️ No delete or cancel options found")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to find/delete pending order: {str(e)}")
            raise

async def main():
    """Main function to run order deletion"""
    print("🚀 DABS Order Deletion Tool")
    print("=" * 50)
    
    deletor = DABSOrderDeletor(headless=False)  # Run visible for debugging
    result = await deletor.delete_pending_order()
    
    print("\n" + "=" * 50)
    if result["success"]:
        print(f"✅ SUCCESS: {result.get('message', 'Order deletion completed')}")
    else:
        print(f"❌ FAILED: {result.get('error', 'Unknown error occurred')}")
    print("=" * 50)
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result["success"] else 1)
