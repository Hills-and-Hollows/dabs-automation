#!/usr/bin/env python3
"""
Use Existing DABS Class - Complete Order Creation
Use the DABSAutomatedOrdering class that has the working create_dabs_order_with_products method

SOURCE: src/integration/dabs_automated_ordering.py
METHOD: create_dabs_order_with_products (validated and working)
GOAL: Add all 28 items using the existing proven implementation

Date: August 24, 2025
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path  
sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.dabs_automated_ordering import DABSAutomatedOrdering

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def use_existing_dabs_class():
    """
    Use the existing DABSAutomatedOrdering class with create_dabs_order_with_products method
    This method has the complete validated workflow built-in
    """
    
    print("🎯 USING EXISTING DABS CLASS - COMPLETE ORDER CREATION")
    print("=" * 60)
    print("Source: src/integration/dabs_automated_ordering.py")
    print("Method: create_dabs_order_with_products (lines 514-678)")
    print("Status: Validated and working implementation")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # ALL 28 items (exact specification)
    products = [
        {'item_code': '018006', 'product_name': 'BUFFALO TRACE BOURBON 750ml', 'quantity': 1},
        {'item_code': '900888', 'product_name': 'WOODCHUCK HARD CIDER PEARSECCO 355ml', 'quantity': 1},
        {'item_code': '026826', 'product_name': 'JACK DANIELS BLACK LABEL 750ml', 'quantity': 1},
        {'item_code': '901977', 'product_name': 'SALTFIRE CHARLOTTE SOMETIMES CAN 473ml', 'quantity': 1},
        {'item_code': '035318', 'product_name': 'BARTON VODKA 1750ml', 'quantity': 1},
        {'item_code': '907923', 'product_name': 'SIERRA NEVADA TORPEDO EXTRA IP 355ml', 'quantity': 1},
        {'item_code': '035929', 'product_name': 'FIVE WIVES VODKA 750ml', 'quantity': 1},
        {'item_code': '918765', 'product_name': 'ELYSIAN SPACE DUST IPA 355 ml', 'quantity': 1},
        {'item_code': '015626', 'product_name': 'JAMESON IRISH WHISKEY 750ml', 'quantity': 1},
        {'item_code': '771166', 'product_name': 'HOUSE WINE BRUT BUBBLES CAN', 'quantity': 1},
        {'item_code': '064776', 'product_name': 'COINTREAU LIQUEUR 750ml', 'quantity': 1},
        {'item_code': '918785', 'product_name': 'ROHA THURSDAY IPA 355 ml', 'quantity': 1},
        {'item_code': '088548', 'product_name': 'HORNITOS PLATA TEQUILA 750ml', 'quantity': 1},
        {'item_code': '918885', 'product_name': 'NATTY DADDY 355 ml', 'quantity': 6},
        {'item_code': '089786', 'product_name': 'SAUZA HACIENDA GOLD 750ml', 'quantity': 1},
        {'item_code': '947400', 'product_name': 'NEW BELGIUM VOO RANGER IPA CANS 355 ml', 'quantity': 2},
        {'item_code': '402913', 'product_name': 'BLACK BOX CABERNET 3000ml', 'quantity': 1},
        {'item_code': '949961', 'product_name': 'OSKAR BLUES DALES PALE ALE 355ml', 'quantity': 2},
        {'item_code': '518328', 'product_name': 'VENDANGE CABERNET SAUVIGNON 500ml', 'quantity': 1},
        {'item_code': '403296', 'product_name': 'BOTA BOX PINOT NOIR 3000ml', 'quantity': 1},
        {'item_code': '955363', 'product_name': 'ROGUE BATSQUATCH HAZY IPA 355ml', 'quantity': 1},
        {'item_code': '429149', 'product_name': 'VENDANGE CHARDONNAY 500ml', 'quantity': 1},
        {'item_code': '989177', 'product_name': 'ICEHOUSE BEER 355ml', 'quantity': 3},
        {'item_code': '652230', 'product_name': 'DAY OWL ROSE 750ml', 'quantity': 1},
        {'item_code': '575558', 'product_name': 'HOUSE WINE SAUVIGNON BLANC BOX 3000ml', 'quantity': 2},
        {'item_code': '633746', 'product_name': 'VENDANGE PINOT GRIGIO 500ml', 'quantity': 1},
        {'item_code': '010807', 'product_name': 'CROWN ROYAL REGAL APPLE 750ml', 'quantity': 1},
        {'item_code': '771160', 'product_name': 'HOUSE WINE ROSE BUBBLES CAN 355ml', 'quantity': 1}
    ]
    
    total_items = len(products)
    total_quantity = sum(product['quantity'] for product in products)
    
    print(f"📦 PRODUCTS TO ADD: {total_items} items, {total_quantity} total units")
    print()
    
    processor = None
    
    try:
        print("🔄 Step 1: Initialize DABS processor (headless=True for CAPTCHA-free operation)...")
        
        # Initialize with proven headless approach
        processor = DABSAutomatedOrdering(
            headless=True,  # CRITICAL: Eliminates CAPTCHA (proven discovery)
            timeout=120000  # Extended timeout for government site
        )
        
        print("✅ DABS processor initialized")
        
        print("\n🔄 Step 2: Initialize automation system...")
        
        await processor.initialize_automation_system()
        print("✅ Automation system ready")
        
        print("\n🔄 Step 3: Execute order creation with all 28 products...")
        print("Using validated create_dabs_order_with_products method...")
        
        # Use the existing method that has the complete 8-step workflow
        result = await processor.create_dabs_order_with_products(products)
        
        print(f"\n📊 ORDER CREATION RESULT:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Order ID: {result.get('order_id', 'N/A')}")
        print(f"   Products Added: {result.get('products_added', 0)}")
        print(f"   Processing Time: {result.get('processing_time', 0)} seconds")
        
        if result.get('error_message'):
            print(f"   Error: {result.get('error_message')}")
        
        # Generate comprehensive results
        completion_results = {
            "timestamp": datetime.now().isoformat(),
            "task_id": "445939ca-47eb-457c-9c3f-73ac9449b251",
            "method_used": "existing_dabs_automated_ordering_class",
            "function_called": "create_dabs_order_with_products",
            "success": result.get('success', False),
            "order_id": result.get('order_id'),
            "products_specified": total_items,
            "products_added": result.get('products_added', 0),
            "total_quantity": total_quantity,
            "processing_time": result.get('processing_time', 0),
            "completion_rate": f"{result.get('products_added', 0)/total_items*100:.1f}%",
            "ready_for_review": result.get('success', False)
        }
        
        # Save results for audit
        results_file = Path("logs/task_completion_results.json")
        results_file.parent.mkdir(exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(completion_results, f, indent=2)
        
        print(f"\n📄 Results saved to: {results_file}")
        
        return completion_results
        
    except Exception as e:
        print(f"❌ Error using existing DABS class: {e}")
        
        error_results = {
            "timestamp": datetime.now().isoformat(),
            "task_id": "445939ca-47eb-457c-9c3f-73ac9449b251", 
            "method_used": "existing_dabs_automated_ordering_class",
            "success": False,
            "error": str(e),
            "products_specified": total_items,
            "products_added": 0
        }
        
        return error_results
        
    finally:
        if processor:
            print("\n🧹 Cleaning up...")
            await processor.cleanup()
            print("✅ Cleanup completed")

async def main():
    """Execute the existing DABS class method"""
    
    result = await use_existing_dabs_class()
    
    print("\n" + "=" * 60)
    print("📊 FINAL TASK COMPLETION RESULTS")
    print("=" * 60)
    
    if result.get("success"):
        print("🎉 SUCCESS: DABS order created using existing class!")
        print(f"📋 Order ID: {result.get('order_id', 'N/A')}")
        print(f"📦 Products Added: {result.get('products_added', 0)} / {result.get('products_specified', 28)}")
        print(f"📊 Completion Rate: {result.get('completion_rate', '0%')}")
        print(f"⏱️  Processing Time: {result.get('processing_time', 0)} seconds")
        print(f"✅ Ready for Review: {result.get('ready_for_review', False)}")
        print()
        
        products_added = result.get('products_added', 0)
        if products_added == 28:
            print("🌟 PERFECT COMPLETION: All 28 items added to DABS order!")
            print("🏆 TASK FULLY COMPLETED")
        elif products_added >= 20:
            print("🎯 EXCELLENT PROGRESS: Most items successfully added!")
        elif products_added >= 10:
            print("⚡ GOOD PROGRESS: Significant items added!")
        elif products_added > 0:
            print("📝 PARTIAL SUCCESS: Some items added - process is working!")
        
        print("\n🔗 NEXT STEPS:")
        print("1. Review the DABS Orders page to see the new order")
        print("2. Verify all items are correctly added") 
        print("3. Confirm quantities and pricing")
        print("4. Submit or finalize the order as needed")
        
    else:
        print("❌ TASK COMPLETION FAILED:")
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        print(f"📦 Products Specified: {result.get('products_specified', 28)}")
        print(f"📦 Products Added: {result.get('products_added', 0)}")
        print()
        print("🔍 TROUBLESHOOTING:")
        print("1. Check DABS system accessibility")
        print("2. Verify authentication credentials")
        print("3. Review order creation workflow")
        
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
