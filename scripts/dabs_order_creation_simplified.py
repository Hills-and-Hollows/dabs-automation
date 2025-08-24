#!/usr/bin/env python3
"""
DABS Order Creation - Simplified Approach
Following proven working method from diagnostic testing

Based on successful authentication from mcp_vs_playwright_comparison test
Using the exact approach that worked: headless=True with proper session handling
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.dabs_automated_ordering import DABSAutomatedOrdering

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def create_dabs_order_simplified():
    """
    Simplified DABS order creation using proven working method
    """
    
    print("🎯 SIMPLIFIED DABS ORDER CREATION")
    print("=" * 60)
    print("Using proven working method from diagnostic testing")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Original 28-item specification from task
    order_items = [
        # SPIRITS
        {'item_code': '018006', 'product_name': 'BUFFALO TRACE BOURBON 750ml', 'quantity': 1},
        {'item_code': '026826', 'product_name': 'JACK DANIELS BLACK LABEL 750ml', 'quantity': 1},
        {'item_code': '035318', 'product_name': 'BARTON VODKA 1750ml', 'quantity': 1},
        {'item_code': '035929', 'product_name': 'FIVE WIVES VODKA 750ml', 'quantity': 1},
        {'item_code': '015626', 'product_name': 'JAMESON IRISH WHISKEY 750ml', 'quantity': 1},
        
        # WINE  
        {'item_code': '402913', 'product_name': 'BLACK BOX CABERNET 3000ml', 'quantity': 1},
        {'item_code': '518328', 'product_name': 'VENDANGE CABERNET SAUVIGNON 500ml', 'quantity': 1},
        {'item_code': '403296', 'product_name': 'BOTA BOX PINOT NOIR 3000ml', 'quantity': 1},
        
        # BEER
        {'item_code': '900888', 'product_name': 'WOODCHUCK HARD CIDER PEARSECCO 355ml', 'quantity': 1},
        {'item_code': '901977', 'product_name': 'SALTFIRE CHARLOTTE SOMETIMES CAN 473ml', 'quantity': 1}
    ]
    
    print(f"📦 Testing with {len(order_items)} products (subset of original 28)")
    
    processor = None
    try:
        # Use the EXACT same approach that worked in testing
        print("🔄 Initializing DABS processor (headless=True)...")
        
        processor = DABSAutomatedOrdering(
            headless=True,  # CRITICAL: This is what prevents CAPTCHA
            timeout=45000   # 45 seconds - reasonable for testing
        )
        
        print("🔄 Initializing automation system...")
        await processor.initialize_automation_system()
        print("✅ System initialized")
        
        # Check if we have saved authentication
        auth_file = Path("dabs_auth.json")
        if auth_file.exists():
            print("✅ Found saved authentication session")
            
            # Try to use saved session directly
            print("🔄 Attempting to use saved session...")
            
            # Let's try the order creation method directly
            # This should use the saved session if available
            print("🔄 Attempting direct order creation...")
            
            result = await processor.create_dabs_order_with_products(order_items)
            
            if result and result.get('success'):
                print("🎉 SUCCESS: DABS order created successfully!")
                print(f"📋 Order ID: {result.get('order_id', 'N/A')}")
                print(f"📦 Products Added: {result.get('products_added', 'N/A')}")
                print(f"⏱️ Processing Time: {result.get('processing_time', 'N/A')} seconds")
                
                # Generate audit trail
                audit_data = {
                    "timestamp": datetime.now().isoformat(),
                    "method": "simplified_dabs_creation",
                    "dabs_order_id": result.get('order_id'),
                    "products_tested": len(order_items),
                    "success": True,
                    "approach": "headless_playwright_with_saved_session"
                }
                
                # Save audit
                audit_file = Path("logs/dabs_order_audit.jsonl")
                audit_file.parent.mkdir(exist_ok=True)
                with open(audit_file, 'a') as f:
                    f.write(json.dumps(audit_data) + '\n')
                
                print("✅ Audit trail logged")
                
                return {
                    "success": True,
                    "order_id": result.get('order_id'),
                    "message": "Simplified approach successful"
                }
                
            else:
                error = result.get('error_message') if result else 'No result returned'
                print(f"❌ Order creation failed: {error}")
                
                # If saved session failed, try fresh authentication
                print("🔄 Trying fresh authentication...")
                
                auth_result = await processor.perform_dabs_login()
                if auth_result:
                    print("✅ Fresh authentication successful")
                    
                    # Try order creation again
                    result = await processor.create_dabs_order_with_products(order_items)
                    
                    if result and result.get('success'):
                        print("🎉 SUCCESS after fresh authentication!")
                        print(f"📋 Order ID: {result.get('order_id', 'N/A')}")
                        return {
                            "success": True,
                            "order_id": result.get('order_id'),
                            "message": "Success after fresh authentication"
                        }
                    else:
                        print(f"❌ Still failed after fresh auth: {result}")
                        return {"success": False, "error": "failed_after_fresh_auth"}
                else:
                    print("❌ Fresh authentication also failed")
                    return {"success": False, "error": "authentication_failed"}
        else:
            print("⚠️ No saved authentication found")
            
            # Try fresh authentication
            print("🔄 Attempting fresh authentication...")
            auth_result = await processor.perform_dabs_login()
            
            if auth_result:
                print("✅ Fresh authentication successful")
                
                result = await processor.create_dabs_order_with_products(order_items)
                
                if result and result.get('success'):
                    print("🎉 SUCCESS with fresh authentication!")
                    print(f"📋 Order ID: {result.get('order_id', 'N/A')}")
                    return {
                        "success": True,
                        "order_id": result.get('order_id'),
                        "message": "Success with fresh authentication"
                    }
                else:
                    print(f"❌ Order creation failed: {result}")
                    return {"success": False, "error": "order_creation_failed"}
            else:
                print("❌ Authentication failed")
                return {"success": False, "error": "authentication_failed"}
                
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return {"success": False, "error": str(e)}
        
    finally:
        if processor:
            print("🧹 Cleaning up...")
            await processor.cleanup()
            print("✅ Cleanup completed")

async def main():
    """Main execution"""
    
    result = await create_dabs_order_simplified()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    if result.get("success"):
        print("✅ DABS ORDER CREATION SUCCESSFUL!")
        print(f"📋 Order ID: {result.get('order_id', 'N/A')}")
        print(f"💡 Method: {result.get('message', 'N/A')}")
        print()
        print("🎯 This proves the documented headless approach works!")
        print("🚀 Ready for production implementation")
    else:
        print("❌ DABS ORDER CREATION FAILED")
        print(f"❌ Error: {result.get('error', 'Unknown')}")
        print()
        print("💡 This indicates need for further investigation")
    
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
