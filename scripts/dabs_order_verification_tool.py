#!/usr/bin/env python3
"""
DABS Order Verification Tool - Critical Verification System
Creates comprehensive verification tools for DABS order state checking

Features:
- Check current pending orders
- Get detailed order information
- Screenshot capture for verification
- Implement "only 1 pending order" constraint check
- Verify order contents and status

Author: DABS Automation System
Created: 2025-08-25
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright, Page, BrowserContext
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DABS_VERIFY - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/logs/dabs_verification.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class DABSOrderInfo:
    """Information about a DABS order"""
    order_id: str
    order_type: str
    status: str
    licensee: str
    items_count: int
    total_amount: Optional[float] = None
    created_date: Optional[str] = None
    items: List[Dict[str, Any]] = None

class DABSOrderVerificationTool:
    """
    Comprehensive DABS order verification and state checking tool
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.browser_context = None
        
        # Load DABS configuration
        self.dabs_base_url = os.getenv("DABS_ORDERING_LOGIN_URL", "https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/")
        self.dabs_username = os.getenv("DABS_ORDERING_USERNAME")
        self.dabs_password = os.getenv("DABS_ORDERING_PASSWORD")
        
        # Screenshot directory
        self.screenshot_dir = Path("data/playwright_screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Authentication storage
        self.auth_storage_path = Path("dabs_auth.json")
        
        if not self.dabs_username or not self.dabs_password:
            raise ValueError("DABS_ORDERING_USERNAME and DABS_ORDERING_PASSWORD must be set")

    async def initialize_system(self):
        """Initialize the verification system"""
        try:
            logger.info("🚀 Initializing DABS verification system...")
            
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
                logger.warning("⚠️ No saved authentication found")
                self.browser_context = await self.browser.new_context()
                
            logger.info("✅ DABS verification system initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize verification system: {str(e)}")
            raise

    async def capture_screenshot(self, page: Page, name: str, description: str = "") -> str:
        """Capture and save a screenshot with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = self.screenshot_dir / filename
        
        await page.screenshot(path=str(filepath), full_page=True)
        logger.info(f"📸 Screenshot captured: {filename} - {description}")
        
        return str(filepath)

    async def get_current_pending_orders(self) -> List[DABSOrderInfo]:
        """Get all current pending orders from DABS"""
        logger.info("🔍 Checking current pending orders...")
        
        page = await self.browser_context.new_page()
        pending_orders = []
        
        try:
            # Navigate to DABS orders page
            await page.goto(f"{self.dabs_base_url}Orders", wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # Capture initial state
            await self.capture_screenshot(page, "orders_list_initial", "Initial orders page state")
            
            # Look for pending/open orders
            # Check for order rows in the table
            order_rows = await page.query_selector_all('tr[data-order-id], .order-row, tbody tr')
            
            logger.info(f"📋 Found {len(order_rows)} potential order rows")
            
            for i, row in enumerate(order_rows):
                try:
                    # Extract order information from the row
                    order_info = await self._extract_order_info_from_row(page, row, i)
                    if order_info and order_info.status.lower() in ['open', 'pending']:
                        pending_orders.append(order_info)
                        logger.info(f"📦 Found pending order: {order_info.order_id} - {order_info.status}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Could not extract info from row {i}: {str(e)}")
                    continue
            
            # Capture final state
            await self.capture_screenshot(page, "orders_list_analyzed", f"Found {len(pending_orders)} pending orders")
            
        except Exception as e:
            logger.error(f"❌ Error checking pending orders: {str(e)}")
            await self.capture_screenshot(page, "orders_list_error", f"Error: {str(e)}")
            
        finally:
            await page.close()
            
        return pending_orders

    async def _extract_order_info_from_row(self, page: Page, row, row_index: int) -> Optional[DABSOrderInfo]:
        """Extract order information from a table row"""
        try:
            # Get all cells in the row
            cells = await row.query_selector_all('td, th')
            
            if len(cells) < 3:  # Need at least order ID, status, type
                return None
                
            # Extract text from cells
            cell_texts = []
            for cell in cells:
                text = await cell.inner_text()
                cell_texts.append(text.strip())
            
            # Look for order ID pattern
            order_id = None
            for text in cell_texts:
                if text.isdigit() and len(text) >= 6:  # Order IDs are typically 6+ digits
                    order_id = text
                    break
            
            if not order_id:
                return None
                
            # Extract other information
            status = "Unknown"
            order_type = "Unknown"
            licensee = "Unknown"
            
            for text in cell_texts:
                text_lower = text.lower()
                if any(status_word in text_lower for status_word in ['open', 'pending', 'closed', 'submitted']):
                    status = text
                elif any(type_word in text_lower for type_word in ['warehouse', 'special', 'licensee']):
                    order_type = text
                elif 'hills' in text_lower or 'hollows' in text_lower:
                    licensee = text
            
            return DABSOrderInfo(
                order_id=order_id,
                order_type=order_type,
                status=status,
                licensee=licensee,
                items_count=0  # Will be populated by get_order_details
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting order info from row {row_index}: {str(e)}")
            return None

    async def get_order_details(self, order_id: str) -> Optional[DABSOrderInfo]:
        """Get detailed information about a specific order"""
        logger.info(f"🔍 Getting details for order {order_id}...")
        
        page = await self.browser_context.new_page()
        
        try:
            # Navigate to order details page
            order_url = f"{self.dabs_base_url}Orders/GetItemsForWarehouse?OrderId={order_id}"
            await page.goto(order_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # Capture order details page
            await self.capture_screenshot(page, f"order_details_{order_id}", f"Order {order_id} details page")
            
            # Extract order header information
            order_info = await self._extract_order_header_info(page, order_id)
            
            # Extract order items
            items = await self._extract_order_items(page)
            if order_info:
                order_info.items = items
                order_info.items_count = len(items)
                
            logger.info(f"📦 Order {order_id}: {len(items)} items, Status: {order_info.status if order_info else 'Unknown'}")
            
            return order_info
            
        except Exception as e:
            logger.error(f"❌ Error getting order details for {order_id}: {str(e)}")
            await self.capture_screenshot(page, f"order_details_error_{order_id}", f"Error: {str(e)}")
            return None
            
        finally:
            await page.close()

    async def _extract_order_header_info(self, page: Page, order_id: str) -> Optional[DABSOrderInfo]:
        """Extract order header information from order details page"""
        try:
            # Look for order type
            order_type = "Unknown"
            type_element = await page.query_selector('text=Warehouse')
            if type_element:
                order_type = "Warehouse"
            
            # Look for status
            status = "Unknown"
            status_element = await page.query_selector('text=Open')
            if status_element:
                status = "Open"
            
            # Look for licensee information
            licensee = "Unknown"
            licensee_elements = await page.query_selector_all('text=/HILLS.*HOLLOWS/i')
            if licensee_elements:
                licensee = "HILLS AND HOLLOWS"
            
            return DABSOrderInfo(
                order_id=order_id,
                order_type=order_type,
                status=status,
                licensee=licensee,
                items_count=0
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting header info: {str(e)}")
            return DABSOrderInfo(
                order_id=order_id,
                order_type="Unknown",
                status="Unknown",
                licensee="Unknown",
                items_count=0
            )

    async def _extract_order_items(self, page: Page) -> List[Dict[str, Any]]:
        """Extract items from order details page"""
        items = []
        
        try:
            # Look for item rows in tables
            item_rows = await page.query_selector_all('tbody tr, .item-row')
            
            for i, row in enumerate(item_rows):
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 3:  # Need at least item code, description, quantity
                        cell_texts = []
                        for cell in cells:
                            text = await cell.inner_text()
                            cell_texts.append(text.strip())
                        
                        # Extract item information
                        item_info = {
                            'row_index': i,
                            'cells': cell_texts,
                            'item_code': None,
                            'description': None,
                            'quantity': None,
                            'price': None
                        }
                        
                        # Try to identify item code (6-digit number)
                        for text in cell_texts:
                            if text.isdigit() and len(text) == 6:
                                item_info['item_code'] = text
                                break
                        
                        # Try to identify quantity (small number)
                        for text in cell_texts:
                            if text.isdigit() and len(text) <= 3:
                                item_info['quantity'] = int(text)
                                break
                        
                        # Try to identify price (contains $ or decimal)
                        for text in cell_texts:
                            if '$' in text or ('.' in text and any(c.isdigit() for c in text)):
                                item_info['price'] = text
                                break
                        
                        # Description is usually the longest text field
                        longest_text = max(cell_texts, key=len) if cell_texts else ""
                        if len(longest_text) > 10:  # Reasonable description length
                            item_info['description'] = longest_text
                        
                        items.append(item_info)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error extracting item {i}: {str(e)}")
                    continue
            
            logger.info(f"📋 Extracted {len(items)} items from order")
            
        except Exception as e:
            logger.error(f"❌ Error extracting order items: {str(e)}")
            
        return items

    async def check_pending_order_constraint(self) -> Dict[str, Any]:
        """Check the critical 'only 1 pending order' constraint"""
        logger.info("🚨 Checking pending order constraint...")
        
        pending_orders = await self.get_current_pending_orders()
        
        constraint_result = {
            'constraint_satisfied': len(pending_orders) <= 1,
            'pending_orders_count': len(pending_orders),
            'pending_orders': [
                {
                    'order_id': order.order_id,
                    'status': order.status,
                    'order_type': order.order_type,
                    'licensee': order.licensee
                }
                for order in pending_orders
            ],
            'can_create_new_order': len(pending_orders) == 0,
            'must_handle_existing_order': len(pending_orders) > 0,
            'constraint_violation': len(pending_orders) > 1
        }
        
        if constraint_result['constraint_violation']:
            logger.error(f"🚨 CONSTRAINT VIOLATION: {len(pending_orders)} pending orders found (max 1 allowed)")
        elif constraint_result['must_handle_existing_order']:
            logger.warning(f"⚠️ Existing pending order found: {pending_orders[0].order_id}")
        else:
            logger.info("✅ No pending orders - safe to create new order")
            
        return constraint_result

    async def comprehensive_verification_report(self) -> Dict[str, Any]:
        """Generate comprehensive verification report"""
        logger.info("📊 Generating comprehensive verification report...")
        
        timestamp = datetime.now().isoformat()
        
        # Check pending order constraint
        constraint_check = await self.check_pending_order_constraint()
        
        # Get detailed information for each pending order
        detailed_orders = []
        for order_summary in constraint_check['pending_orders']:
            order_details = await self.get_order_details(order_summary['order_id'])
            if order_details:
                detailed_orders.append({
                    'order_id': order_details.order_id,
                    'status': order_details.status,
                    'order_type': order_details.order_type,
                    'licensee': order_details.licensee,
                    'items_count': order_details.items_count,
                    'items': order_details.items
                })
        
        report = {
            'timestamp': timestamp,
            'verification_type': 'comprehensive_dabs_order_verification',
            'constraint_check': constraint_check,
            'detailed_orders': detailed_orders,
            'system_status': {
                'authentication_available': self.auth_storage_path.exists(),
                'screenshot_directory': str(self.screenshot_dir),
                'total_screenshots_captured': len(list(self.screenshot_dir.glob('*.png')))
            },
            'recommendations': self._generate_recommendations(constraint_check, detailed_orders)
        }
        
        # Save report
        report_file = Path(f"data/dabs_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"📋 Verification report saved: {report_file}")
        
        return report

    def _generate_recommendations(self, constraint_check: Dict, detailed_orders: List[Dict]) -> List[str]:
        """Generate actionable recommendations based on verification results"""
        recommendations = []
        
        if constraint_check['constraint_violation']:
            recommendations.append("🚨 CRITICAL: Multiple pending orders detected - resolve immediately")
            recommendations.append("Delete or submit excess pending orders before creating new orders")
            
        elif constraint_check['must_handle_existing_order']:
            existing_order = detailed_orders[0] if detailed_orders else {}
            order_id = existing_order.get('order_id', 'Unknown')
            items_count = existing_order.get('items_count', 0)
            
            recommendations.append(f"⚠️ Existing pending order {order_id} with {items_count} items")
            recommendations.append("Options: 1) Edit existing order, 2) Submit existing order, 3) Delete existing order")
            
            if items_count > 50:
                recommendations.append("Large order detected - verify contents before submission")
                
        else:
            recommendations.append("✅ Safe to create new order - no pending orders found")
            
        recommendations.append("Always verify order contents with screenshots before submission")
        recommendations.append("Implement proper verification in automation scripts")
        
        return recommendations

    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.browser_context:
                await self.browser_context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("🧹 Verification system cleanup completed")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}")

async def main():
    """Main verification function"""
    print("🔍 DABS Order Verification Tool")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    verifier = None
    try:
        verifier = DABSOrderVerificationTool(headless=True)
        await verifier.initialize_system()
        
        # Generate comprehensive verification report
        report = await verifier.comprehensive_verification_report()
        
        print("\n" + "=" * 50)
        print("📊 VERIFICATION REPORT SUMMARY")
        print("=" * 50)
        
        constraint_check = report['constraint_check']
        print(f"Pending Orders Count: {constraint_check['pending_orders_count']}")
        print(f"Constraint Satisfied: {constraint_check['constraint_satisfied']}")
        print(f"Can Create New Order: {constraint_check['can_create_new_order']}")
        
        if constraint_check['pending_orders']:
            print("\nPending Orders:")
            for order in constraint_check['pending_orders']:
                print(f"  - Order {order['order_id']}: {order['status']} ({order['order_type']})")
        
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        print(f"\nFull report saved to: data/dabs_verification_report_*.json")
        print(f"Screenshots saved to: {verifier.screenshot_dir}")
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return 1
        
    finally:
        if verifier:
            await verifier.cleanup()
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
