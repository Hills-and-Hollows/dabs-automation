#!/usr/bin/env python3
"""
Fresh QuickBooks OAuth Setup
Handles the complete OAuth flow with fresh authorization codes

This script:
1. Generates a new authorization URL
2. Guides you through getting a fresh code
3. Immediately exchanges it for tokens
4. Tests the connection

Author: DABS Automation System
Created: 2025-08-22
"""

import asyncio
import os
import sys
import webbrowser
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from automation.workflows.quickbooks_integration.qb_oauth_manager import QuickBooksOAuthManager

async def fresh_oauth_setup():
    """Complete fresh OAuth setup"""
    
    print("🔄 FRESH QUICKBOOKS OAUTH SETUP")
    print("=" * 50)
    print("Hills & Hollows LLC - DABS Automation")
    print()
    
    # Initialize OAuth manager
    oauth_manager = QuickBooksOAuthManager()
    
    # Check environment
    client_id = os.getenv('QB_CLIENT_ID')
    client_secret = os.getenv('QB_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Missing OAuth credentials")
        return False
    
    print(f"🔑 Client ID: {client_id}")
    print(f"🔒 Client Secret: SET")
    print()
    
    # Step 1: Generate fresh authorization URL
    print("🔗 STEP 1: Generate Fresh Authorization URL")
    print("-" * 50)
    
    try:
        auth_url = oauth_manager.generate_authorization_url()
        print("✅ Fresh authorization URL generated:")
        print(f"{auth_url}")
        print()
        
        # Open in browser
        print("🌐 Opening in browser...")
        webbrowser.open(auth_url)
        
    except Exception as e:
        print(f"❌ Error generating URL: {e}")
        return False
    
    # Step 2: Guide user through process
    print("📋 STEP 2: Complete Authorization (FRESH)")
    print("-" * 50)
    print("In your browser:")
    print("1. ✅ Sign in to QuickBooks Online (shawn@owenent.com)")
    print("2. ✅ Select: Hills & Hollows LLC")
    print("3. ✅ Click 'Authorize'")
    print("4. ✅ You'll be redirected to OAuth Playground")
    print("5. ✅ Copy the NEW authorization code")
    print()
    print("⚠️  IMPORTANT: Use the code immediately (expires in 10 minutes)")
    print()
    
    # Step 3: Get fresh code from user
    print("🔄 STEP 3: Enter Fresh Authorization Details")
    print("-" * 50)
    
    auth_code = input("📝 Enter NEW Authorization Code: ").strip()
    
    if not auth_code:
        print("❌ Authorization code required")
        return False
    
    # Use the same company ID
    company_id = "9130355762729646"
    print(f"🏢 Using Company ID: {company_id}")
    
    # Step 4: Immediate token exchange
    print("\n🚀 STEP 4: Immediate Token Exchange")
    print("-" * 50)
    
    try:
        print("🔄 Exchanging fresh code for tokens...")
        
        tokens = await oauth_manager.exchange_code_for_tokens(auth_code, company_id)
        
        print("✅ SUCCESS! Fresh tokens obtained!")
        print(f"   📅 Expires: {tokens.expires_at}")
        print(f"   🏢 Company ID: {tokens.company_id}")
        print(f"   🔑 Access Token: {tokens.access_token[:20]}...")
        
        # Step 5: Test immediately
        print("\n🧪 STEP 5: Testing Fresh Connection")
        print("-" * 50)
        
        access_token = await oauth_manager.get_valid_access_token()
        print("✅ Fresh tokens working perfectly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Token exchange failed: {e}")
        print()
        print("🔍 Common causes:")
        print("   • Authorization code expired (>10 minutes old)")
        print("   • Code already used")
        print("   • Typo in authorization code")
        print("   • Network connectivity issue")
        
        return False

async def main():
    """Main execution"""
    
    print("🎯 This script will get fresh OAuth tokens for QuickBooks")
    print("   Authorization codes expire quickly, so we'll do this fast!")
    print()
    
    success = await fresh_oauth_setup()
    
    if success:
        print("\n🎉 SUCCESS: Fresh QuickBooks OAuth setup complete!")
        print("🚀 Ready for DABS automation integration!")
    else:
        print("\n❌ Setup failed - please try again with a fresh code")

if __name__ == "__main__":
    asyncio.run(main())
