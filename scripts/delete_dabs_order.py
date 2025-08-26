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
        # Optional: target a specific order id for row-scoped operations
        self.target_order_id = os.getenv("DABS_ORDER_ID")
        # Artifacts directory
        self.artifacts_dir = Path("data/playwright_screenshots")
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

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
                
                # Navigate to DABS ordering system home
                logger.info(f"🌐 Navigating to DABS: {self.dabs_base_url}")
                await page.goto(self.dabs_base_url, wait_until='domcontentloaded')
                await page.wait_for_load_state('networkidle')
                
                # Check if we need to login
                if await self._needs_login(page):
                    logger.info("🔓 Performing DABS login...")
                    await self._perform_login(page)
                
                # Ensure we're on the Orders page
                logger.info("🧭 Opening Licensee Orders list...")
                await page.goto(f"{self.dabs_base_url}Orders", wait_until='domcontentloaded')
                # Try to wait for a recognizable heading or table; if it times out, still capture DOM for diagnostics
                try:
                    await page.wait_for_selector(
                        "div.tableOpen table tbody tr",
                        timeout=20000
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Orders page marker not found within timeout: {e}")
                    try:
                        await page.screenshot(path=str(self.artifacts_dir / "orders_list_headed.png"))
                        html_now = await page.content()
                        (self.artifacts_dir / "orders_list_headed.html").write_text(html_now, encoding='utf-8')
                    except Exception:
                        pass

                # Additional headless stabilization: wait for hooks and delete trigger to be available
                try:
                    await page.wait_for_function(
                        "() => document && document.querySelector('div.tableOpen tbody tr') !== null",
                        timeout=15000
                    )
                    await page.wait_for_function(
                        "() => document.querySelector('div.tableOpen tbody tr a.open-AddDialog.delete') !== null || document.querySelector('a[href=\"#DeleteOrder\"]') !== null",
                        timeout=15000
                    )
                except Exception:
                    # Not fatal; proceed with retries in finder
                    pass

                # Look for existing orders and perform deletion (or confirm none exist)
                logger.info("🔍 Checking for pending orders...")
                pending_cleared = await self._find_and_delete_pending_order(page)
                
                if pending_cleared:
                    logger.info("✅ Pending order state is clear (deleted or none present)")
                    return {"success": True, "message": "Pending order state clear"}
                else:
                    logger.error("❌ Pending order still present or page not ready. See artifacts.")
                    return {"success": False, "error": "pending_order_not_cleared"}
                    
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
            # If already on Orders page or title indicates Orders, skip login
            current_title = (await page.title() or "").strip().lower()
            if "/OnlineOrders/Orders" in page.url or current_title.startswith("licensee orders"):
                return False
            # Look for login form fields
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
            await page.wait_for_selector(username_selector, timeout=20000)
            await page.fill(username_selector, self.dabs_username)
            
            # Fill password  
            password_selector = "input[type='password']"
            await page.wait_for_selector(password_selector, timeout=20000)
            await page.fill(password_selector, self.dabs_password)
            
            # Click login button
            login_button = await page.wait_for_selector("input[type='submit'], button[type='submit'], button:has-text('Login')", timeout=20000)
            await login_button.click()
            # Wait for redirect/readiness after login
            try:
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector("#menu nav, a.nav-link, body", timeout=20000)
            except Exception:
                pass
            logger.info("✅ Login successful")
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            raise

    async def _find_and_delete_pending_order(self, page) -> bool:
        """Find and delete any pending orders"""
        try:
            # Take a screenshot for debugging
            await page.screenshot(path=str(self.artifacts_dir / "debug_dabs_interface.png"))
            logger.info("📷 Screenshot saved: debug_dabs_interface.png")
            
            # Print current page HTML for debugging
            page_html = await page.content()
            logger.info(f"🌐 Current page URL: {page.url}")
            logger.info(f"📄 Page title: {await page.title()}")
            
            # Ensure DOM is hydrated in headless before scanning
            try:
                await page.wait_for_function(
                    "() => document && document.querySelector('div.tableOpen tbody tr') !== null",
                    timeout=10000
                )
            except Exception:
                pass

            # Determine current open order row and id
            row = None
            current_order_id = None
            if self.target_order_id:
                row = await page.query_selector(f'div.tableOpen tbody tr:has(td:has-text("{self.target_order_id}"))')
                if row:
                    current_order_id = self.target_order_id
                    logger.info(f"🎯 Targeting order row with id {current_order_id}")
            if row is None:
                row = await page.query_selector('div.tableOpen tbody tr')
                if row:
                    first_td = await row.query_selector('td:nth-child(1)')
                    if first_td:
                        current_order_id = (await first_td.text_content() or '').strip()
                        logger.info(f"🎯 Discovered open order id from page: {current_order_id}")
            
            # Helper: click a button and confirm in modal (Delete/Yes/Confirm)
            async def click_and_confirm_delete():
                # Wait for Delete modal and click the input submit with value Delete
                await page.wait_for_selector('#DeleteOrder', timeout=10000)
                confirm_delete = await page.wait_for_selector(
                    "#DeleteOrder input[type='submit'][value='Delete']",
                    timeout=10000
                )
                await confirm_delete.click()
                await page.wait_for_load_state('networkidle')

            # Helper: short retry for a selector
            async def retry_query(selector: str, attempts: int = 3, delay_ms: int = 800):
                for i in range(attempts):
                    el = await page.query_selector(selector)
                    if el:
                        return el
                    await page.wait_for_timeout(delay_ms)
                return None

            # First attempt: main list row-scoped Delete
            if row:
                # The Delete action is an anchor with class 'open-AddDialog delete' that opens the #DeleteOrder modal
                delete_in_row = await row.query_selector("a.open-AddDialog.delete, a[href='#DeleteOrder']")
                if delete_in_row and await delete_in_row.is_visible():
                    logger.info("🗑️ Clicking row-scoped Delete on Orders list...")
                    await delete_in_row.click()
                    await click_and_confirm_delete()
                else:
                    # Fallback to Edit from the targeted row
                    edit_in_row = await row.query_selector(
                        "button:has-text('Edit'), a:has-text('Edit'), input[value*='Edit'], i[data-bs-original-title='Edit']"
                    )
                    if edit_in_row:
                        logger.info("✏️ Opening Edit page from targeted row...")
                        await edit_in_row.click()
                        await page.wait_for_load_state('networkidle')
                        # Try Delete on edit page (same modal trigger link may be present)
                        delete_on_edit_trigger = await page.wait_for_selector(
                            "a.open-AddDialog.delete, a[href='#DeleteOrder']",
                            timeout=10000
                        )
                        await delete_on_edit_trigger.click()
                        await click_and_confirm_delete()
                    else:
                        logger.info("ℹ️ Edit control not found in targeted row; will try global search")
            else:
                # No specific id; attempt to locate first pending row's Delete
                delete_trigger = await retry_query("div.tableOpen tbody tr a.open-AddDialog.delete, a[href='#DeleteOrder']")
                if delete_trigger:
                    logger.info("🗑️ Clicking Delete trigger in pending row...")
                    await delete_trigger.click()
                    await click_and_confirm_delete()
                else:
                    # Try Edit then Delete path
                    edit_buttons = await page.query_selector_all(
                        "tr:has-text('Pending') button:has-text('Edit'), tr:has-text('Pending') a:has-text('Edit'), i[data-bs-original-title='Edit']"
                    )
                    if edit_buttons:
                        logger.info("✏️ Opening Edit page from pending row...")
                        await edit_buttons[0].click()
                        await page.wait_for_load_state('networkidle')
                        delete_on_edit_trigger = await page.wait_for_selector(
                            "a.open-AddDialog.delete, a[href='#DeleteOrder']",
                            timeout=10000
                        )
                        await delete_on_edit_trigger.click()
                        await click_and_confirm_delete()
                    else:
                        logger.info("ℹ️ No Delete or Edit controls found on Orders list")
            
            # Post-condition verification: reload Orders list and assert
            await page.goto(f"{self.dabs_base_url}Orders")
            await page.wait_for_load_state('networkidle')
            # Save artifacts after action
            await page.screenshot(path=str(self.artifacts_dir / "debug_dabs_interface_after.png"))
            try:
                html_after = await page.content()
                (self.artifacts_dir / "orders_list_after.html").write_text(html_after, encoding='utf-8')
            except Exception:
                pass

            if current_order_id:
                remaining = await page.query_selector(f'div.tableOpen tbody tr:has(td:has-text("{current_order_id}"))')
                if remaining is not None:
                    logger.error("❌ Post-check: order row still present after deletion attempt")
                    return False

            banner = await page.query_selector("text=Pending order must be submitted or deleted before a new order can be created.")
            if banner is not None:
                logger.error("❌ Post-check: pending-order banner still present")
                return False

            logger.info("✅ Post-check passed: order removed and banner gone")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to find/delete pending order: {str(e)}")
            raise

async def main():
    """Main function to run order deletion"""
    print("🚀 DABS Order Deletion Tool")
    print("=" * 50)
    
    # Read headless mode from env (default true). Set DABS_HEADLESS=false to run headed diagnostics
    headless_env = os.getenv("DABS_HEADLESS", "true").lower() in ("1", "true", "yes", "on")
    deletor = DABSOrderDeletor(headless=headless_env)
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
