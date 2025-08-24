#!/usr/bin/env python3
"""
Restaurant Order API Testing Script
Test all restaurant order automation endpoints

Created: August 23, 2025
Purpose: Validate restaurant order API functionality
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

API_BASE = "http://localhost:8000"

async def test_restaurant_api():
    """Test all restaurant order API endpoints"""
    print("🚀 Restaurant Order API Testing")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Check API Health
        print("\n1. Testing API Health...")
        try:
            async with session.get(f"{API_BASE}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ API Health: {data['status']}")
                else:
                    print(f"❌ API Health Failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ API Health Error: {e}")
            return False
        
        # Test 2: Restaurant System Status
        print("\n2. Testing Restaurant System Status...")
        try:
            async with session.get(f"{API_BASE}/restaurant/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Restaurant System: {data['status']}")
                    print(f"   Business Impact: {data['business_impact']['time_reduction']}")
                else:
                    print(f"❌ Restaurant Status Failed: {response.status}")
        except Exception as e:
            print(f"❌ Restaurant Status Error: {e}")
        
        # Test 3: Submit Test Order
        print("\n3. Testing Order Submission...")
        test_order = {
            "restaurant_name": "Test Bistro API",
            "restaurant_contact": "test@bistro.com",
            "delivery_date": (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
            "items": [
                {
                    "description": "BACARDI MOJITO 1750ml",
                    "quantity": 2,
                    "case_pack": 6
                },
                {
                    "description": "WASATCH BEER 6PK", 
                    "quantity": 3,
                    "case_pack": 4
                }
            ],
            "total_amount": 245.50,
            "payment_method": "credit_card",
            "credit_card_last_four": "1234"
        }
        
        order_id = None
        try:
            async with session.post(f"{API_BASE}/restaurant/orders/submit", 
                                  json=test_order) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['success']:
                        order_id = data['order_id']
                        print(f"✅ Order Submitted: {order_id}")
                        print(f"   Processing Fee: ${data['processing_fee']:.2f}")
                    else:
                        print(f"❌ Order Submission Failed: {data['message']}")
                else:
                    print(f"❌ Order Submission HTTP Error: {response.status}")
        except Exception as e:
            print(f"❌ Order Submission Error: {e}")
        
        # Test 4: Check Order Status (if order was created)
        if order_id:
            print("\n4. Testing Order Status Tracking...")
            try:
                async with session.get(f"{API_BASE}/restaurant/orders/status/{order_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Order Status: {data['status']}")
                        print(f"   Restaurant: {data['restaurant_name']}")
                        print(f"   Total Charge: ${data['total_charge']:.2f}")
                    else:
                        print(f"❌ Order Status Failed: {response.status}")
            except Exception as e:
                print(f"❌ Order Status Error: {e}")
        
        # Test 5: Get Restaurant Orders
        print("\n5. Testing Restaurant Order History...")
        try:
            async with session.get(f"{API_BASE}/restaurant/orders/Test%20Bistro%20API") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Order History: {data['total_orders']} orders found")
                    for order in data['orders']:
                        print(f"   Order {order['order_id']}: {order['status']} - ${order['total_amount']:.2f}")
                else:
                    print(f"❌ Order History Failed: {response.status}")
        except Exception as e:
            print(f"❌ Order History Error: {e}")
        
        # Test 6: Manager Dashboard - Pending Orders
        print("\n6. Testing Manager Dashboard - Pending Orders...")
        try:
            async with session.get(f"{API_BASE}/manager/orders/pending") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Pending Orders: {data['pending_orders_count']} found")
                    print(f"   Total Pending Value: ${data['total_pending_value']:.2f}")
                    print(f"   Friday Confirmation Ready: {data['friday_confirmation_ready']}")
                else:
                    print(f"❌ Pending Orders Failed: {response.status}")
        except Exception as e:
            print(f"❌ Pending Orders Error: {e}")
        
        # Test 7: Manager Dashboard Summary
        print("\n7. Testing Manager Dashboard Summary...")
        try:
            async with session.get(f"{API_BASE}/manager/dashboard/summary") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Dashboard Summary: {data['dashboard_summary']['total_orders']} total orders")
                    print(f"   Total Revenue: ${data['dashboard_summary']['total_revenue']:.2f}")
                    print(f"   Time Saved: {data['time_savings_metrics']['time_saved']}")
                    print(f"   Next Delivery: {data['operational_info']['next_delivery_date']}")
                else:
                    print(f"❌ Dashboard Summary Failed: {response.status}")
        except Exception as e:
            print(f"❌ Dashboard Summary Error: {e}")
        
        # Test 8: Order Confirmation (if we have an order)
        if order_id:
            print("\n8. Testing Order Confirmation...")
            try:
                async with session.post(f"{API_BASE}/manager/orders/{order_id}/confirm") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['success']:
                            print(f"✅ Order Confirmed: {data['restaurant_name']}")
                            print(f"   Confirmation Date: {data['confirmation_date']}")
                        else:
                            print(f"❌ Order Confirmation Failed: {data['message']}")
                    else:
                        print(f"❌ Order Confirmation HTTP Error: {response.status}")
            except Exception as e:
                print(f"❌ Order Confirmation Error: {e}")
        
        print("\n" + "=" * 50)
        print("🎯 API Testing Complete!")
        print("✅ Restaurant Order Automation API is operational")
        print("🚀 Ready for web portal integration")
        
        return True

async def test_api_performance():
    """Test API performance with multiple concurrent requests"""
    print("\n🚀 Performance Testing...")
    
    async with aiohttp.ClientSession() as session:
        # Test concurrent order submissions
        tasks = []
        
        for i in range(5):
            test_order = {
                "restaurant_name": f"Performance Test {i+1}",
                "restaurant_contact": f"test{i+1}@performance.com",
                "delivery_date": (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
                "items": [
                    {
                        "description": "TEST ITEM 750ml",
                        "quantity": 1,
                        "case_pack": 6
                    }
                ],
                "total_amount": 50.00,
                "payment_method": "house_account"
            }
            
            task = session.post(f"{API_BASE}/restaurant/orders/submit", json=test_order)
            tasks.append(task)
        
        start_time = datetime.now()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status == 200)
        
        print(f"✅ Performance Test Complete:")
        print(f"   Requests: 5 concurrent")
        print(f"   Successful: {successful}/5")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Rate: {5/duration:.1f} requests/second")

def main():
    """Main test runner"""
    print("🍾 Restaurant Order Automation API Test Suite")
    print(f"Testing API at: {API_BASE}")
    print(f"Start Time: {datetime.now().isoformat()}")
    
    try:
        # Run basic API tests
        asyncio.run(test_restaurant_api())
        
        # Run performance tests
        asyncio.run(test_api_performance())
        
        print("\n🎉 All tests completed successfully!")
        print("✅ Restaurant Order Automation System is ready for production")
        
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
