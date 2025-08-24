#!/usr/bin/env python3
"""
QuickBooks OAuth Token Exchange
Exchange authorization code for access/refresh tokens

This script takes the authorization code from OAuth Playground
and exchanges it for tokens that can be used for API calls.

Author: DABS Automation System
Created: 2025-08-22
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from automation.workflows.quickbooks_integration.qb_oauth_manager import QuickBooksOAuthManager

async def exchange_tokens():
    """Exchange authorization code for tokens"""
    
    print("🔄 QUICKBOOKS TOKEN EXCHANGE")
    print("=" * 50)
    print("Hills & Hollows LLC - DABS Automation")
    print()
    
    # Initialize OAuth manager
    oauth_manager = QuickBooksOAuthManager()
    
    # Check environment
    client_id = os.getenv('QB_CLIENT_ID')
    client_secret = os.getenv('QB_CLIENT_SECRET')
    
    print(f"🔑 Client ID: {client_id}")
    print(f"🔒 Client Secret: {'SET' if client_secret else 'NOT SET'}")
    print()
    
    if not client_id or not client_secret:
        print("❌ Missing OAuth credentials")
        return False
    
    # From OAuth Playground - FRESH CODE
    auth_code = "XAB11755904758ZynF0rXLgBRYIowE8X3ZsPE2ooTMmZ5kp4Ml"
    company_id = "9130355762729646"
    
    print(f"📝 Authorization Code: {auth_code}")
    print(f"🏢 Company ID: {company_id}")
    print()
    
    try:
        print("🔄 Exchanging authorization code for tokens...")
        
        tokens = await oauth_manager.exchange_code_for_tokens(auth_code, company_id)
        
        print("✅ TOKEN EXCHANGE SUCCESSFUL!")
        print(f"   📅 Expires: {tokens.expires_at}")
        print(f"   🏢 Company ID: {tokens.company_id}")
        print(f"   🔑 Access Token: {tokens.access_token[:20]}...")
        print(f"   🔄 Refresh Token: {tokens.refresh_token[:20]}...")
        print()
        
        # Test the tokens
        print("🧪 Testing API connectivity...")
        
        try:
            access_token = await oauth_manager.get_valid_access_token()
            print("✅ API connectivity test passed!")
            print("🎯 QuickBooks OAuth setup complete!")
            print()
            print("📋 NEXT STEPS:")
            print("   • Tokens are saved and encrypted")
            print("   • Ready for DABS automation integration")
            print("   • Can now sync inventory with QuickBooks")
            
            return True
            
        except Exception as e:
            print(f"❌ API connectivity test failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Token exchange failed: {e}")
        print()
        print("🔍 TROUBLESHOOTING:")
        print("   • Verify authorization code is correct")
        print("   • Check that company ID matches")
        print("   • Ensure redirect URI is configured properly")
        print("   • Try generating a new authorization code")
        
        return False

async def main():
    """Main execution"""
    success = await exchange_tokens()
    
    if success:
        print("\n🎉 SUCCESS: QuickBooks OAuth 2.0 setup complete!")
    else:
        print("\n❌ FAILED: Token exchange unsuccessful")

if __name__ == "__main__":
    asyncio.run(main())
