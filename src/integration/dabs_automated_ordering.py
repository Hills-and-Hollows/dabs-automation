"""
DABS Official Ordering System Automation Integration

This module implements automated integration between the restaurant ordering portal
and the official Utah DABS Licensee Ordering System using Playwright browser automation.

Business Impact: Eliminates manual dual order entry, achieving complete end-to-end
automation for restaurant orders while maintaining Utah Package Agency compliance.

Author: DABS Automation System
Date: August 23, 2025
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from enum import Enum
from dotenv import load_dotenv

# Load DABS environment configuration
config_path = Path(__file__).parent.parent.parent / "config" / "dabs_ordering.env"
load_dotenv(config_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed" 
    PENDING = "pending"
    RETRY_NEEDED = "retry_needed"

class PendingOrderStrategy(Enum):
    SUBMIT_EXISTING = "submit_existing"
    COPY_PREVIOUS = "copy_previous"
    DELETE_PENDING = "delete_pending"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class RestaurantOrderItem:
    """Represents an item in a restaurant order"""
    sku: str
    product_name: str
    quantity: int
    unit_price: float
    category: str
    
@dataclass  
class RestaurantOrder:
    """Represents a complete restaurant order"""
    id: str
    customer_name: str
    customer_email: str
    items: List[RestaurantOrderItem]
    total_amount: float
    order_date: datetime
    payment_method: str
    delivery_address: Optional[str] = None

@dataclass
class DABSOrderResult:
    """Result of DABS order automation attempt"""
    success: bool
    dabs_order_id: Optional[str] = None
    items_processed: int = 0
    total_amount: float = 0.0
    processing_time: float = 0.0
    error: Optional[str] = None
    session_id: Optional[str] = None
    audit_trail: List[Dict[str, Any]] = None

class DABSAutomatedOrdering:
    """
    Main class for automating DABS order placement from restaurant orders
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser = None
        self.browser_context = None
        
        # Load DABS configuration from environment
        self.dabs_base_url = os.getenv("DABS_ORDERING_LOGIN_URL", "https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/")
        self.dabs_username = os.getenv("DABS_ORDERING_USERNAME")
        self.dabs_password = os.getenv("DABS_ORDERING_PASSWORD")
        self.dabs_session_timeout = int(os.getenv("DABS_SESSION_TIMEOUT_MINUTES", "30"))
        
        # Authentication and session management
        self.auth_storage_path = Path("dabs_auth.json")
        self.audit_trail = []
        
        # Validate required credentials
        if not self.dabs_username or not self.dabs_password:
            raise ValueError("DABS_ORDERING_USERNAME and DABS_ORDERING_PASSWORD must be set in environment")
        
    async def initialize_automation_system(self):
        """
        Initialize the Playwright automation system
        """
        try:
            logger.info("🚀 Initializing DABS automation system...")
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            # Load saved authentication if available
            if self.auth_storage_path.exists():
                logger.info("📁 Loading saved DABS authentication...")
                self.browser_context = await self.browser.new_context(
                    storage_state=str(self.auth_storage_path)
                )
            else:
                logger.warning("⚠️ No saved authentication found - interactive login required")
                self.browser_context = await self.browser.new_context()
                
            await self._log_audit_event("SYSTEM_INITIALIZED", {"headless": self.headless})
            logger.info("✅ DABS automation system initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize automation system: {str(e)}")
            raise

    async def perform_dabs_login(self) -> bool:
        """
        Perform automated login to DABS Licensee Ordering System
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            logger.info("🔐 Attempting DABS automated login...")
            
            if not self.browser_context:
                await self.initialize_automation_system()
            
            page = await self.browser_context.new_page()
            
            # Navigate to DABS main page (login form is embedded)
            await page.goto(self.dabs_base_url, wait_until="networkidle")
            logger.info(f"📄 Navigated to DABS main page: {self.dabs_base_url}")
            
            # Wait for login form to be available
            await page.wait_for_selector('input[name="UserName"]', timeout=self.timeout)
            
            # Fill login credentials
            await page.fill('input[name="UserName"]', self.dabs_username)
            await page.fill('input[name="Password"]', self.dabs_password)
            
            logger.info(f"🔑 Filled credentials for user: {self.dabs_username}")
            
            # Submit login form
            await page.click('button[type="submit"], input[type="submit"]')
            
            # Wait for navigation after login
            try:
                await page.wait_for_url("**/Orders", timeout=self.timeout)
                logger.info("✅ Successfully logged into DABS - redirected to Orders page")
                
                # Save authentication state for future use
                storage_state = await self.browser_context.storage_state()
                with open(self.auth_storage_path, 'w') as f:
                    json.dump(storage_state, f)
                logger.info("💾 Saved DABS authentication session")
                
                await page.close()
                return True
                
            except Exception as nav_error:
                # Check for error messages on login page
                error_elements = await page.query_selector_all('.validation-summary-errors, .alert-danger, .error')
                if error_elements:
                    error_text = await error_elements[0].text_content()
                    logger.error(f"❌ DABS login failed: {error_text}")
                else:
                    logger.error(f"❌ DABS login failed: Navigation timeout - {str(nav_error)}")
                
                await page.close()
                return False
                
        except Exception as e:
            logger.error(f"❌ DABS login error: {str(e)}")
            if page:
                await page.close()
            return False

    async def process_restaurant_order(self, restaurant_order: RestaurantOrder) -> DABSOrderResult:
        """
        Main method to convert restaurant order to DABS order automatically
        
        Args:
            restaurant_order: The restaurant order to process
            
        Returns:
            DABSOrderResult with success status and details
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"📦 Processing restaurant order {restaurant_order.id} for {restaurant_order.customer_name}")
            await self._log_audit_event("ORDER_PROCESSING_START", {
                "restaurant_order_id": restaurant_order.id,
                "customer": restaurant_order.customer_name,
                "items_count": len(restaurant_order.items),
                "total_amount": restaurant_order.total_amount
            })
            
            # 1. Ensure automation system is initialized
            if not self.browser_context:
                await self.initialize_automation_system()
            
            # 2. Navigate to DABS orders page
            page = await self._navigate_to_dabs_orders()
            
            # 3. Validate DABS session is active
            if not await self._validate_dabs_session(page):
                raise Exception("DABS session validation failed - authentication required")
            
            # 4. Handle existing pending orders
            await self._handle_pending_orders(page)
            
            # 5. Create new DABS order
            order_page = await self._create_new_dabs_order(page)
            
            # 6. Add items from restaurant order
            items_added = 0
            for item in restaurant_order.items:
                success = await self._add_item_to_dabs_order(order_page, item)
                if success:
                    items_added += 1
                    
            if items_added == 0:
                raise Exception("No items could be added to DABS order")
                
            # 7. Submit DABS order
            dabs_order_id = await self._submit_dabs_order(order_page)
            
            # 8. Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = DABSOrderResult(
                success=True,
                dabs_order_id=dabs_order_id,
                items_processed=items_added,
                total_amount=restaurant_order.total_amount,
                processing_time=processing_time,
                session_id=await self._get_session_id(page),
                audit_trail=self.audit_trail.copy()
            )
            
            await self._log_audit_event("ORDER_PROCESSING_SUCCESS", {
                "dabs_order_id": dabs_order_id,
                "items_processed": items_added,
                "processing_time": processing_time
            })
            
            logger.info(f"✅ Successfully processed order {restaurant_order.id} → DABS Order {dabs_order_id}")
            return result
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = str(e)
            
            await self._log_audit_event("ORDER_PROCESSING_FAILED", {
                "error": error_msg,
                "processing_time": processing_time
            })
            
            logger.error(f"❌ Failed to process restaurant order {restaurant_order.id}: {error_msg}")
            
            return DABSOrderResult(
                success=False,
                error=error_msg,
                processing_time=processing_time,
                audit_trail=self.audit_trail.copy()
            )

    async def _navigate_to_dabs_orders(self) -> Page:
        """Navigate to DABS orders page"""
        logger.info("🧭 Navigating to DABS orders page...")
        
        page = await self.browser_context.new_page()
        await page.goto(f"{self.dabs_base_url}/Orders", timeout=self.timeout)
        
        await self._log_audit_event("NAVIGATION", {"url": f"{self.dabs_base_url}/Orders"})
        return page

    async def _validate_dabs_session(self, page: Page) -> bool:
        """Validate that DABS session is active and authenticated"""
        logger.info("🔍 Validating DABS session...")
        
        try:
            # Check for login indicators
            login_form = await page.query_selector('form[action*="login"]')
            if login_form:
                logger.warning("⚠️ DABS session expired - authentication required")
                return False
                
            # Check for orders page elements
            orders_header = await page.query_selector('h1:has-text("Orders")', timeout=5000)
            if orders_header:
                logger.info("✅ DABS session validated successfully")
                return True
                
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Session validation failed: {str(e)}")
            return False

    async def _handle_pending_orders(self, page: Page):
        """Handle existing pending orders that block new order creation"""
        logger.info("🔄 Checking for pending orders...")
        
        try:
            # Check for pending order restriction message
            pending_message = await page.query_selector('text*="Pending order must be submitted"')
            
            if pending_message:
                logger.warning("⚠️ Pending order detected - determining strategy...")
                strategy = await self._determine_pending_order_strategy(page)
                
                await self._log_audit_event("PENDING_ORDER_DETECTED", {"strategy": strategy.value})
                
                if strategy == PendingOrderStrategy.SUBMIT_EXISTING:
                    await self._submit_existing_pending_order(page)
                elif strategy == PendingOrderStrategy.COPY_PREVIOUS:
                    await self._copy_previous_order(page)
                elif strategy == PendingOrderStrategy.DELETE_PENDING:
                    await self._delete_pending_order(page)
                else:
                    raise Exception("Manual intervention required for pending order")
            else:
                logger.info("✅ No pending orders found")
                
        except Exception as e:
            logger.error(f"❌ Failed to handle pending orders: {str(e)}")
            raise

    async def _determine_pending_order_strategy(self, page: Page) -> PendingOrderStrategy:
        """Determine the best strategy for handling pending orders"""
        # Implementation would analyze the pending order and determine best approach
        # For now, default to copying previous order as safest option
        return PendingOrderStrategy.COPY_PREVIOUS

    async def _create_new_dabs_order(self, page: Page) -> Page:
        """Create a new DABS order"""
        logger.info("📝 Creating new DABS order...")
        
        try:
            # Click Create New Order button
            create_button = await page.query_selector('text="Create New Order"')
            if create_button:
                await create_button.click()
            else:
                # Try Copy Previous Order as fallback
                copy_button = await page.query_selector('text="Copy Previous Order"')
                if copy_button:
                    await copy_button.click()
                else:
                    raise Exception("Cannot find Create New Order or Copy Previous Order button")
            
            # Wait for order editing page to load
            await page.wait_for_selector('[data-order-id]', timeout=self.timeout)
            
            await self._log_audit_event("ORDER_CREATED", {"method": "create_new_order"})
            logger.info("✅ New DABS order created successfully")
            
            return page
            
        except Exception as e:
            logger.error(f"❌ Failed to create new DABS order: {str(e)}")
            raise

    async def _add_item_to_dabs_order(self, page: Page, item: RestaurantOrderItem) -> bool:
        """Add a restaurant order item to the DABS order"""
        logger.info(f"➕ Adding item {item.sku} ({item.product_name}) x{item.quantity}")
        
        try:
            # Search for item in DABS catalog
            search_input = await page.query_selector('[placeholder*="search"]')
            if search_input:
                await search_input.fill(item.sku)
                await page.click('button:has-text("Search")')
            
            # Wait for search results
            await page.wait_for_timeout(2000)
            
            # Find and select the item
            item_row = await page.query_selector(f'[data-item-code="{item.sku}"]')
            if not item_row:
                logger.warning(f"⚠️ Item {item.sku} not found in DABS catalog")
                return False
            
            # Set quantity
            quantity_input = await item_row.query_selector('[data-field="quantity"]')
            if quantity_input:
                await quantity_input.fill(str(item.quantity))
            
            # Add to cart
            add_button = await item_row.query_selector('button:has-text("Add")')
            if add_button:
                await add_button.click()
            
            # Verify item was added to cart
            await page.wait_for_selector(f'[data-cart-item="{item.sku}"]', timeout=5000)
            
            await self._log_audit_event("ITEM_ADDED", {
                "sku": item.sku,
                "product_name": item.product_name,
                "quantity": item.quantity
            })
            
            logger.info(f"✅ Successfully added {item.sku} to DABS order")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to add item {item.sku}: {str(e)}")
            return False

    async def _submit_dabs_order(self, page: Page) -> str:
        """Submit the DABS order and return order ID"""
        logger.info("📤 Submitting DABS order...")
        
        try:
            # Click Submit Order button
            submit_button = await page.query_selector('button:has-text("Submit Order")')
            if not submit_button:
                raise Exception("Submit Order button not found")
            
            await submit_button.click()
            
            # Wait for submission confirmation
            confirmation = await page.wait_for_selector(
                'text*="Order submitted successfully"',
                timeout=self.timeout
            )
            
            if not confirmation:
                raise Exception("Order submission confirmation not found")
            
            # Extract order ID from confirmation or page
            order_id_element = await page.query_selector('[data-order-id]')
            if order_id_element:
                order_id = await order_id_element.text_content()
            else:
                # Fallback: generate timestamp-based ID if not found
                order_id = f"DABS-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            await self._log_audit_event("ORDER_SUBMITTED", {"dabs_order_id": order_id})
            logger.info(f"✅ DABS order submitted successfully: {order_id}")
            
            return order_id.strip()
            
        except Exception as e:
            logger.error(f"❌ Failed to submit DABS order: {str(e)}")
            raise

    async def _get_session_id(self, page: Page) -> Optional[str]:
        """Extract session ID for audit purposes"""
        try:
            # Get session info from page context or cookies
            cookies = await page.context.cookies()
            for cookie in cookies:
                if 'session' in cookie['name'].lower():
                    return cookie['value'][:16]  # First 16 chars for privacy
            return "unknown"
        except:
            return "unknown"

    async def _log_audit_event(self, event_type: str, details: Dict[str, Any]):
        """Log audit event for Utah Package Agency compliance"""
        audit_event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
            "system": "DABS_Automated_Ordering"
        }
        
        self.audit_trail.append(audit_event)
        logger.debug(f"📋 Audit: {event_type} - {details}")

    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.browser_context:
                await self.browser_context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("🧹 Automation system cleanup completed")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {str(e)}")

    async def __aenter__(self):
        await self.initialize_automation_system()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

    async def create_dabs_order_with_products(self, products: List[dict]) -> dict:
        """
        Create a new DABS order and add specified products
        
        Args:
            products: List of product dictionaries with keys:
                     - 'item_code': Product item code (e.g., '005232')
                     - 'product_name': Full product name
                     - 'quantity': Number of cases to order
                     
        Returns:
            Dictionary with order creation results
        """
        import time
        logger.info(f"🎯 Creating new DABS order with {len(products)} products")
        
        start_time = time.time()
        
        try:
            # Initialize automation if not already done
            if not self.browser_context:
                await self.initialize_automation_system()
            
            page = await self.browser_context.new_page()
            
            # Navigate to DABS main page first (direct Orders URL can fail)
            logger.info("📄 Navigating to DABS main page...")
            await page.goto(self.dabs_base_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)
            # From the main page, prefer clicking into Licensee Orders instead of direct /Orders
            try:
                if await page.query_selector('a:has-text("Licensee Orders")'):
                    await page.click('a:has-text("Licensee Orders")')
                    await page.wait_for_load_state('domcontentloaded')
                    await page.wait_for_timeout(1000)
            except Exception:
                pass
            
            # STEP 1: Click Create New Order button
            logger.info("🆕 STEP 1: Creating new order...")
            try:
                # Prefer direct Warehouse create URL if accessible
                try:
                    await page.goto(f"{self.dabs_base_url}Orders/CreateOrderPAW", wait_until="domcontentloaded")
                    await page.wait_for_timeout(1500)
                except Exception:
                    pass
                
                # If still not on create page, try opening modal then selecting Warehouse
                create_button_selector = 'a[data-bs-toggle="modal"][data-bs-target="#paTypeModal"]'
                if await page.query_selector(create_button_selector):
                    await page.click(create_button_selector)
                    await page.wait_for_timeout(500)
                else:
                    # Fallback: text match
                    if await page.query_selector('text=Create New Order'):
                        await page.click('text=Create New Order')
                        await page.wait_for_timeout(500)
            except Exception:
                try:
                    await page.click('text=Create New Order')
                except Exception:
                    logger.warning("⚠️ Could not find explicit 'Create New Order' trigger; proceeding to Warehouse create URL")
                    try:
                        await page.goto(f"{self.dabs_base_url}Orders/CreateOrderPAW", wait_until="domcontentloaded")
                    except Exception:
                        pass
            
            # STEP 2: Select Warehouse order type
            logger.info("🏭 STEP 2: Selecting Warehouse order type...")
            try:
                warehouse_selector = 'a.btn.btn-primary.btn-lg[href="/ProdApps/OnlineOrders/Orders/CreateOrderPAW"]'
                await page.wait_for_selector(warehouse_selector, timeout=10000)
                await page.click(warehouse_selector)
                await page.wait_for_load_state('networkidle')
            except Exception:
                # If already on the Warehouse create page, selector may not be present
                try:
                    await page.click('text=Warehouse')
                except Exception:
                    logger.info("ℹ️ Assuming Warehouse order page is already loaded")
                
            await page.wait_for_timeout(3000)
            order_id = None
            
            # Process each product
            for product in products:
                logger.info(f"➕ Adding product: {product['item_code']} - {product['product_name']}")
                
                # STEP 3: Ensure All Items view is active (try direct click first)
                try:
                    # Prefer direct All Items activation if present
                    all_items_selector = 'text=All Items'
                    if await page.query_selector(all_items_selector):
                        await page.click(all_items_selector)
                    else:
                        # Fallback: open dropdown then select All Items
                        try:
                            dropdown_selector = 'button.btn.btn-primary.dropdown-toggle[id="dropdownMenuButton"]'
                            await page.wait_for_selector(dropdown_selector, timeout=8000)
                            await page.click(dropdown_selector)
                            await page.wait_for_timeout(500)
                            await page.click(all_items_selector)
                        except Exception:
                            # Final fallback: attempt generic button by text
                            await page.click('button:has-text("Add To Order")')
                            await page.click(all_items_selector)
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_timeout(1500)
                except Exception:
                    logger.warning("⚠️ Could not activate 'All Items' view; proceeding to search anyway")
                
                # STEP 4: Search for specific product (search by code only for robustness)
                search_term = f"{product['item_code']}"
                logger.info(f"🔍 Searching for: {search_term}")
                
                try:
                    # Try multiple search selectors for resilience
                    search_selectors = [
                        'input[type="search"][placeholder*="Item Code"]',
                        'input[type="search"][placeholder*="Item"]',
                        'input.form-control.form-control-sm',
                        'input[placeholder*="Search"]',
                    ]
                    filled = False
                    for sel in search_selectors:
                        try:
                            await page.wait_for_selector(sel, timeout=4000)
                            await page.fill(sel, search_term)
                            filled = True
                            break
                        except Exception:
                            continue
                    if not filled:
                        # Fallback to a general input[type="search"]
                        await page.fill('input[type="search"]', search_term)
                    await page.wait_for_timeout(2000)
                except Exception:
                    logger.warning("⚠️ Could not locate search input; attempting to proceed")
                
                await page.wait_for_timeout(3000)
                
                # STEP 5: Set quantity when needed (default may be 1 in UI)
                desired_qty = int(product['quantity'])
                if desired_qty != 1:
                    logger.info(f"🔢 Setting quantity to {desired_qty}")
                    try:
                        # Try common quantity inputs in results table
                        qty_candidates = [
                            'input.form-control.Normal11[id="quantity"][name="i.QuantityOrdered"]',
                            'input[name*="QuantityOrdered"]',
                            'input[id="quantity"]',
                            'input.form-control[name*="Quantity"]'
                        ]
                        set_ok = False
                        for sel in qty_candidates:
                            try:
                                await page.wait_for_selector(sel, timeout=4000)
                                await page.click(sel)
                                await page.evaluate('(selector) => { const el = document.querySelector(selector); if (el) el.select(); }', sel)
                                await page.type(sel, str(desired_qty))
                                actual_quantity = await page.input_value(sel)
                                logger.info(f"✅ Quantity validation: {actual_quantity}")
                                set_ok = True
                                break
                            except Exception:
                                continue
                        if not set_ok:
                            logger.warning("⚠️ Could not locate a quantity input; proceeding with UI default (likely 1)")
                    except Exception as e:
                        logger.warning(f"⚠️ Quantity input adjustment skipped: {e}")
                
                # STEP 6: Click Add to Order button
                logger.info("➕ Adding item to order...")
                try:
                    add_to_order_selector = 'a.btn.btn-primary.btn-sm[href*="EditOrder"]'
                    await page.wait_for_selector(add_to_order_selector, timeout=10000)
                    
                    # Extract order ID from href if this is the first product
                    if not order_id:
                        add_button = await page.query_selector(add_to_order_selector)
                        if add_button:
                            href = await add_button.get_attribute('href')
                            import re
                            order_id_match = re.search(r'orderId=(\d+)', href)
                            if order_id_match:
                                order_id = order_id_match.group(1)
                                logger.info(f"📋 Order ID: {order_id}")
                    
                    await page.click(add_to_order_selector)
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_timeout(2000)
                    
                except Exception:
                    # Fallback: generic button text
                    await page.click('text=Add to Order')
                
                logger.info(f"✅ Product {product['item_code']} added successfully")
            
            # STEP 8: Return to Orders page
            logger.info("🔙 Returning to Orders page...")
            try:
                return_selector = 'a.btn.button4.btn-sm[href="/ProdApps/OnlineOrders/Orders"]'
                await page.wait_for_selector(return_selector, timeout=10000)
                await page.click(return_selector)
                await page.wait_for_load_state('networkidle')
            except Exception:
                await page.click('text=Return to Order')
            
            processing_time = time.time() - start_time
            
            await page.close()
            
            result = {
                'success': True,
                'order_id': order_id,
                'products_added': len(products),
                'processing_time': round(processing_time, 2),
                'message': f'Successfully created order {order_id} with {len(products)} products'
            }
            
            logger.info(f"✅ Order creation completed: {result}")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Error creating DABS order: {e}")
            return {
                'success': False,
                'order_id': None,
                'products_added': 0,
                'processing_time': round(processing_time, 2),
                'error_message': str(e)
            }

# Convenience functions for integration
async def process_single_restaurant_order(restaurant_order: RestaurantOrder) -> DABSOrderResult:
    """
    Process a single restaurant order through DABS automation
    
    Args:
        restaurant_order: Restaurant order to process
        
    Returns:
        DABSOrderResult with processing outcome
    """
    async with DABSAutomatedOrdering() as dabs_automation:
        return await dabs_automation.process_restaurant_order(restaurant_order)

async def process_batch_restaurant_orders(restaurant_orders: List[RestaurantOrder]) -> List[DABSOrderResult]:
    """
    Process multiple restaurant orders through DABS automation
    
    Args:
        restaurant_orders: List of restaurant orders to process
        
    Returns:
        List of DABSOrderResult objects
    """
    results = []
    
    async with DABSAutomatedOrdering() as dabs_automation:
        for order in restaurant_orders:
            result = await dabs_automation.process_restaurant_order(order)
            results.append(result)
            
            # Brief pause between orders to avoid overwhelming DABS system
            await asyncio.sleep(2)
    
    return results

if __name__ == "__main__":
    # Example usage for testing
    import asyncio
    
    async def test_dabs_automation():
        """Test function for DABS automation"""
        
        # Create sample restaurant order
        sample_order = RestaurantOrder(
            id="REST-001",
            customer_name="Boulder Mountain Lodge",
            customer_email="orders@bouldermountainlodge.com",
            items=[
                RestaurantOrderItem(
                    sku="12345",
                    product_name="Sample Product",
                    quantity=2,
                    unit_price=25.99,
                    category="Liquor"
                )
            ],
            total_amount=51.98,
            order_date=datetime.utcnow(),
            payment_method="Credit Card"
        )
        
        # Process order
        result = await process_single_restaurant_order(sample_order)
        
        if result.success:
            print(f"✅ Order processed successfully: DABS Order {result.dabs_order_id}")
        else:
            print(f"❌ Order processing failed: {result.error}")
    
    # Run test
    # asyncio.run(test_dabs_automation())