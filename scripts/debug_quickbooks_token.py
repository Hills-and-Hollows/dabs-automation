#!/usr/bin/env python3
"""
QuickBooks Token Debug Script
============================

Simple script to debug QuickBooks token issues and test API access.
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.automation.workflows.quickbooks_integration.qb_oauth_manager import QuickBooksOAuthManager

async def debug_token():
    """Debug QuickBooks token and API access"""
    
    print("🔍 QUICKBOOKS TOKEN DEBUG")
    print("=" * 40)
    
    try:
        # Initialize OAuth manager
        oauth_manager = QuickBooksOAuthManager()
        
        # Load tokens
        await oauth_manager.load_tokens()
        
        if not oauth_manager.current_tokens:
            print("❌ No tokens found")
            return
        
        tokens = oauth_manager.current_tokens
        print(f"✅ Tokens loaded")
        print(f"   📅 Created: {tokens.created_at}")
        print(f"   📅 Expires: {tokens.expires_at}")
        print(f"   ⏰ Is Expired: {tokens.is_expired}")
        print(f"   🏢 Company ID: {tokens.company_id}")
        print(f"   🔑 Access Token (first 20 chars): {tokens.access_token[:20]}...")
        print()
        
        # Test direct API call
        print("🧪 Testing Direct API Call")
        print("-" * 30)
        
        headers = {
            'Authorization': f'Bearer {tokens.access_token}',
            'Accept': 'application/json'
        }
        
        # Try company info endpoint
        url = f"{oauth_manager.base_url}/v3/company/{tokens.company_id}/companyinfo/{tokens.company_id}"
        print(f"📡 URL: {url}")
        print(f"🔑 Authorization: Bearer {tokens.access_token[:20]}...")
        print()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                print(f"📊 Response Status: {response.status}")
                print(f"📋 Response Headers:")
                for key, value in response.headers.items():
                    print(f"   {key}: {value}")
                print()
                
                response_text = await response.text()
                print(f"📄 Response Body:")
                print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
                print()
                
                if response.status == 200:
                    print("✅ API call successful!")
                    try:
                        data = json.loads(response_text)
                        print("📊 Parsed JSON response:")
                        print(json.dumps(data, indent=2)[:1000] + "..." if len(str(data)) > 1000 else json.dumps(data, indent=2))
                    except:
                        print("⚠️  Could not parse JSON response")
                else:
                    print(f"❌ API call failed with status {response.status}")
                    
                    if response.status == 401:
                        print("🔒 401 Unauthorized - Token may be invalid or expired")
                    elif response.status == 403:
                        print("🚫 403 Forbidden - Insufficient permissions or scope issues")
                    elif response.status == 400:
                        print("📝 400 Bad Request - Request format issue")
        
        # Test token refresh if needed
        if tokens.is_expired:
            print("\n🔄 Token is expired, attempting refresh...")
            try:
                await oauth_manager.refresh_access_token()
                print("✅ Token refresh successful")
            except Exception as e:
                print(f"❌ Token refresh failed: {e}")
        
    except Exception as e:
        print(f"💥 Debug error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_token())
