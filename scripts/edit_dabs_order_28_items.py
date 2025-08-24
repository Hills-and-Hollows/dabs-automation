#!/usr/bin/env python3
"""
Edit Existing DABS Order - Add 28 Specific Restaurant Items
Automated script to add the specific 28 restaurant items to the current pending DABS order.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.dabs_automated_ordering import DABSAutomatedOrdering

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - EDIT_DABS_ORDER - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the 28 restaurant items to add
RESTAURANT_ITEMS = [
    # SPIRITS (9 items)
    {"item_code": "018006", "product_name": "BUFFALO TRACE BOURBON 750ml", "quantity": 1},
    {"item_code": "026826", "product_name": "JACK DANIELS BLACK LABEL 750ml", "quantity": 1},
    {"item_code": "035318", "product_name": "BARTON VODKA 1750ml", "quantity": 1},
    {"item_code": "035929", "product_name": "FIVE WIVES VODKA 750ml", "quantity": 1},
    {"item_code": "015626", "product_name": "JAMESON IRISH WHISKEY 750ml", "quantity": 1},
    {"item_code": "064776", "product_name": "COINTREAU LIQUEUR 750ml", "quantity": 1},
    {"item_code": "088548", "product_name": "HORNITOS PLATA TEQUILA 750ml", "quantity": 1},
    {"item_code": "089786", "product_name": "SAUZA HACIENDA GOLD 750ml", "quantity": 1},
    {"item_code": "010807", "product_name": "CROWN ROYAL REGAL APPLE 750ml", "quantity": 1},
    
    # WINE (9 items) 
    {"item_code": "771166", "product_name": "HOUSE WINE BRUT BUBBLES CAN 3", "quantity": 1},
    {"item_code": "402913", "product_name": "BLACK BOX CABERNET 3000ml", "quantity": 1},
    {"item_code": "518328", "product_name": "VENDANGE CABERNET SAUVIGNON 500ml", "quantity": 1},
    {"item_code": "403296", "product_name": "BOTA BOX PINOT NOIR 3000ml", "quantity": 1},
    {"item_code": "429149", "product_name": "VENDANGE CHARDONNAY 500ml", "quantity": 1},
    {"item_code": "652230", "product_name": "DAY OWL ROSE 750ml", "quantity": 1},
    {"item_code": "575558", "product_name": "HOUSE WINE SAUVIGNON BLANC BOX 3000ml", "quantity": 2},
    {"item_code": "633746", "product_name": "VENDANGE PINOT GRIGIO 500ml", "quantity": 1},
    {"item_code": "771160", "product_name": "HOUSE WINE ROSE BUBBLES CAN 355ml", "quantity": 1},
    
    # BEER (10 items)
    {"item_code": "900888", "product_name": "WOODCHUCK HARD CIDER PEARSECCO 355ml", "quantity": 1},
    {"item_code": "901977", "product_name": "SALTFIRE CHARLOTTE SOMETIMES CAN 473ml", "quantity": 1},
    {"item_code": "907923", "product_name": "SIERRA NEVADA TORPEDO EXTRA IP 355ml", "quantity": 1},
    {"item_code": "918765", "product_name": "ELYSIAN SPACE DUST IPA 355 ml", "quantity": 1},
    {"item_code": "918785", "product_name": "ROHA THURSDAY IPA 355 ml", "quantity": 1},
    {"item_code": "918885", "product_name": "NATTY DADDY 355 ml", "quantity": 6},
    {"item_code": "947400", "product_name": "NEW BELGIUM VOO RANGER IPA CANS 355 ml", "quantity": 2},
    {"item_code": "949961", "product_name": "OSKAR BLUES DALES PALE ALE 355ml", "quantity": 2},
    {"item_code": "955363", "product_name": "ROGUE BATSQUATCH HAZY IPA 355ml", "quantity": 1},
    {"item_code": "989177", "product_name": "ICEHOUSE BEER 355ml", "quantity": 3},
]

class DABSOrderEditor:
    """Extended DABS automation for editing existing orders"""
    
    def __init__(self):
        self.dabs_automation = None
        self.results = {
            'success': False,
            'items_added': 0,
            'items_failed': 0,
            'total_items': len(RESTAURANT_ITEMS),
            'processing_time': 0.0,
            'order_details': {},
            'errors': []
        }
    
    async def edit_existing_order_with_items(self) -> Dict[str, Any]:
        """
        Edit the existing pending DABS order by adding the 28 restaurant items
        """
        start_time = time.time()
        logger.info(f"🎯 Starting to edit existing DABS order with {len(RESTAURANT_ITEMS)} items")
        
        try:
            # Initialize DABS automation system
            self.dabs_automation = DABSAutomatedOrdering(headless=False, timeout=30000)
            await self.dabs_automation.initialize_automation_system()
            
            # Authenticate if needed
            auth_success = await self.dabs_automation.perform_dabs_login()
            if not auth_success:
                raise Exception("DABS authentication failed")
            
            # Navigate to the orders page
            page = await self.dabs_automation.browser_context.new_page()
            await page.goto(f"{self.dabs_automation.dabs_base_url}Orders", wait_until="networkidle")
            await page.wait_for_timeout(3000)
            
            logger.info("📄 Navigated to DABS Orders page")
            
            # Look for and click Edit button on pending order
            await self._click_edit_pending_order(page)
            
            # Add each item to the order
            items_added = 0
            items_failed = 0
            
            for item in RESTAURANT_ITEMS:
                try:
                    success = await self._add_item_to_existing_order(page, item)
                    if success:
                        items_added += 1
                        logger.info(f"✅ Added: {item['item_code']} - {item['product_name']} (Qty: {item['quantity']})")
                    else:
                        items_failed += 1
                        logger.warning(f"⚠️ Failed to add: {item['item_code']} - {item['product_name']}")
                        
                except Exception as e:
                    items_failed += 1
                    error_msg = f"Error adding {item['item_code']}: {str(e)}"
                    self.results['errors'].append(error_msg)
                    logger.error(f"❌ {error_msg}")
                
                # Brief pause between items
                await page.wait_for_timeout(1000)
            
            # Update results
            processing_time = time.time() - start_time
            self.results.update({
                'success': items_added > 0,
                'items_added': items_added,
                'items_failed': items_failed,
                'processing_time': round(processing_time, 2)
            })
            
            # Final summary
            logger.info(f"✅ Order editing completed!")
            logger.info(f"📊 Items successfully added: {items_added}/{len(RESTAURANT_ITEMS)}")
            logger.info(f"⏱️ Processing time: {processing_time:.2f} seconds")
            
            if items_failed > 0:
                logger.warning(f"⚠️ Items that failed: {items_failed}")
            
            await page.close()
            return self.results
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"DABS order editing failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            self.results.update({
                'success': False,
                'processing_time': round(processing_time, 2),
                'errors': [error_msg]
            })
            
            return self.results
        
        finally:
            if self.dabs_automation:
                await self.dabs_automation.cleanup()

    async def _click_edit_pending_order(self, page):
        """Find and click the Edit button for the pending order"""
        logger.info("🔍 Looking for pending order Edit button...")
        
        try:
            # Wait for orders table to load
            await page.wait_for_selector('table', timeout=10000)
            
            # Look for Edit button or link
            edit_selectors = [
                'a:has-text("Edit")',
                'button:has-text("Edit")', 
                'i.material-icons:has-text("edit")',
                '[title="Edit"]',
                'a[href*="EditOrder"]'
            ]
            
            edit_clicked = False
            for selector in edit_selectors:
                try:
                    if await page.locator(selector).is_visible():
                        await page.click(selector)
                        await page.wait_for_load_state('networkidle')
                        edit_clicked = True
                        logger.info(f"✅ Clicked Edit button: {selector}")
                        break
                except:
                    continue
            
            if not edit_clicked:
                # Try to find any pending order row and click edit
                await page.click('table tr:first-child td:last-child a')
                
            await page.wait_for_timeout(3000)
            logger.info("✅ Successfully entered edit mode for pending order")
            
        except Exception as e:
            raise Exception(f"Could not find or click Edit button: {str(e)}")

    async def _add_item_to_existing_order(self, page, item: Dict[str, Any]) -> bool:
        """
        Add a single item to the existing order being edited
        """
        try:
            logger.info(f"➕ Adding: {item['item_code']} - {item['product_name']} (Qty: {item['quantity']})")
            
            # STEP 1: Click Add To Order dropdown
            try:
                dropdown_selector = 'button.btn.btn-primary.dropdown-toggle[id="dropdownMenuButton"]'
                await page.wait_for_selector(dropdown_selector, timeout=10000)
                await page.click(dropdown_selector)
                await page.wait_for_timeout(2000)
            except Exception:
                await page.click('button:has-text("Add To Order")')
            
            # STEP 2: Select All Items from dropdown
            await page.click('text=All Items')
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(2000)
            
            # STEP 3: Search for specific product (using just name, no size/code)
            # Extract just the product name without size specifications
            product_name = item['product_name']
            # Remove size info (ml, etc.) and common descriptors
            search_term = product_name.split(' ')[0:2]  # Take first 2 words typically brand + type
            if 'BUFFALO' in product_name:
                search_term = "BUFFALO TRACE"
            elif 'JACK DANIELS' in product_name:
                search_term = "JACK DANIELS"
            elif 'JAMESON' in product_name:
                search_term = "JAMESON"
            elif 'FIVE WIVES' in product_name:
                search_term = "FIVE WIVES"
            elif 'CROWN ROYAL' in product_name:
                search_term = "CROWN ROYAL"
            elif 'HOUSE WINE' in product_name:
                search_term = "HOUSE WINE"
            elif 'BLACK BOX' in product_name:
                search_term = "BLACK BOX"
            elif 'VENDANGE' in product_name:
                search_term = "VENDANGE"
            elif 'BOTA BOX' in product_name:
                search_term = "BOTA BOX"
            elif 'DAY OWL' in product_name:
                search_term = "DAY OWL"
            elif 'SIERRA NEVADA' in product_name:
                search_term = "SIERRA NEVADA"
            elif 'NEW BELGIUM' in product_name:
                search_term = "NEW BELGIUM"
            elif 'OSKAR BLUES' in product_name:
                search_term = "OSKAR BLUES"
            elif 'NATTY DADDY' in product_name:
                search_term = "NATTY DADDY"
            else:
                # For other products, just use the item code
                search_term = item['item_code']
            
            logger.info(f"🔍 Searching for: {search_term}")
            
            try:
                search_selector = 'input[type="search"].form-control.form-control-sm[placeholder="Item Code or Name"]'
                await page.wait_for_selector(search_selector, timeout=10000)
                await page.fill(search_selector, str(search_term))
                await page.wait_for_timeout(2000)
            except Exception:
                await page.fill('input[placeholder*="Item Code"]', str(search_term))
            
            await page.wait_for_timeout(2000)
            
            # STEP 4: Set quantity
            try:
                quantity_selector = 'input.form-control.Normal11[id="quantity"][name="i.QuantityOrdered"]'
                await page.wait_for_selector(quantity_selector, timeout=10000)
                
                # Clear field and set quantity
                await page.click(quantity_selector)
                await page.evaluate('(selector) => document.querySelector(selector).select()', quantity_selector)
                await page.type(quantity_selector, str(item['quantity']))
                
            except Exception as e:
                logger.error(f"❌ Quantity input error: {e}")
                return False
            
            # STEP 5: Click Add to Order button
            try:
                add_to_order_selector = 'a.btn.btn-primary.btn-sm[href*="EditOrder"]'
                await page.wait_for_selector(add_to_order_selector, timeout=10000)
                await page.click(add_to_order_selector)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(2000)
                
            except Exception:
                await page.click('text=Add to Order')
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add {item['item_code']}: {str(e)}")
            return False

async def main():
    """Main execution function"""
    print("🚀 DABS Order Editor - Adding 28 Restaurant Items")
    print("=" * 60)
    
    editor = DABSOrderEditor()
    results = await editor.edit_existing_order_with_items()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print(f"✅ Success: {results['success']}")
    print(f"📦 Items Added: {results['items_added']}/{results['total_items']}")
    print(f"❌ Items Failed: {results['items_failed']}")
    print(f"⏱️ Processing Time: {results['processing_time']} seconds")
    
    if results['errors']:
        print("\n❌ Errors encountered:")
        for error in results['errors']:
            print(f"   • {error}")
    
    return results

if __name__ == "__main__":
    # Run the order editing process
    results = asyncio.run(main())
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)
