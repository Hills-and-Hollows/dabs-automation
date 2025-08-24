#!/usr/bin/env python3
"""
Test SSCS CCB Authentication with Corrected URLs
Quick validation script to test the URL fix

Created: January 23, 2025
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def test_corrected_authentication():
    print('🔧 Testing CORRECTED SSCS CCB Authentication')
    print('=' * 50)
    
    try:
        from integration_hub.sscs_ccb_client import SSCSCCBClient
        
        client = SSCSCCBClient()
        print(f'🌐 Corrected CCB URL: {client.ccb_url}')
        print(f'📊 Transaction URL: {client.transaction_url}')
        print(f'👤 Username: {client.username}')
        print(f'🔑 Password: {"*" * len(client.password) if client.password else "NOT SET"}')
        print()
        
        print('🔍 Attempting production authentication...')
        auth_result = await client.authenticate_ccb()
        
        if auth_result:
            print('✅ CORRECTED AUTHENTICATION: SUCCESS!')
            print(f'🔒 Session expires: {client.session_expires}')
            print('🎯 Production validation: UNBLOCKED')
            
            # Test inventory access
            print()
            print('📊 Testing inventory access...')
            inventory = await client.get_liquor_beer_wine_inventory()
            
            if inventory:
                print(f'✅ Inventory Access: SUCCESS ({len(inventory)} items)')
                if len(inventory) > 0:
                    sample = inventory[0]
                    print(f'📋 Sample: {sample.description}')
                    print(f'🏷️  UPC: {sample.upc_code}')
                    print(f'💰 Price: ${sample.current_price}')
                    
                print()
                print('🎊 PRODUCTION VALIDATION: READY TO PROCEED')
                return True
            else:
                print('⚠️  No inventory items returned')
                return False
                
        else:
            print('❌ Authentication still failing')
            print('💡 May need different authentication approach')
            return False
        
    except Exception as e:
        print(f'💥 Authentication test error: {e}')
        return False
    finally:
        await client.close()

if __name__ == "__main__":
    result = asyncio.run(test_corrected_authentication())
    print()
    if result:
        print("🎯 RESULT: Ready for full production validation suite")
    else:
        print("🚨 RESULT: Authentication requires further investigation")
