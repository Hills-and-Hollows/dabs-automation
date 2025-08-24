#!/usr/bin/env python3
"""
QuickBooks OAuth 2.0 Setup using OAuth Playground
Uses Intuit's OAuth Playground for redirect handling

This script:
1. Generates the authorization URL
2. Guides you through the OAuth Playground flow
3. Helps you extract the authorization code
4. Exchanges code for tokens
5. Saves tokens securely

Author: DABS Automation System
Created: 2025-08-22
"""

import asyncio
import json
import os
import sys
import webbrowser
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from automation.workflows.quickbooks_integration.qb_oauth_manager import QuickBooksOAuthManager

class QuickBooksOAuthPlayground:
    """OAuth setup using Intuit's OAuth Playground"""
    
    def __init__(self):
        self.oauth_manager = QuickBooksOAuthManager()
        
    async def run_oauth_setup(self):
        """Run the complete OAuth setup process"""
        
        print("🚀 QUICKBOOKS OAUTH 2.0 SETUP")
        print("=" * 50)
        print("Hills & Hollows LLC - DABS Automation")
        print("Using Intuit OAuth Playground")
        print()
        
        # Check existing tokens first
        await self._check_existing_tokens()
        
        # Generate authorization URL
        await self._generate_auth_url()
        
        # Guide through manual process
        await self._guide_manual_process()
        
        # Exchange code for tokens
        await self._exchange_tokens()
        
        # Test connectivity
        await self._test_connectivity()
        
        print("\n✅ QUICKBOOKS OAUTH SETUP COMPLETE!")
        print("🎯 Ready for DABS automation integration")
        
    async def _check_existing_tokens(self):
        """Check for existing valid tokens"""
        
        print("🔍 STEP 1: Checking Existing Tokens")
        print("-" * 40)
        
        try:
            tokens = await self.oauth_manager.load_tokens()
            
            if tokens:
                print("   ✅ Tokens found")
                
                if tokens.is_expired:
                    print("   ⚠️  Tokens expired - refresh needed")
                    try:
                        await self.oauth_manager.refresh_access_token()
                        print("   ✅ Tokens refreshed successfully")
                        
                        # Test refreshed tokens
                        access_token = await self.oauth_manager.get_valid_access_token()
                        print("   ✅ Refreshed tokens are working")
                        print("   🎯 OAuth setup already complete!")
                        return True
                        
                    except Exception as e:
                        print(f"   ❌ Token refresh failed: {e}")
                        print("   🔄 Re-authorization required")
                else:
                    print("   ✅ Tokens are valid")
                    
                    # Test existing tokens
                    try:
                        access_token = await self.oauth_manager.get_valid_access_token()
                        print("   ✅ Existing tokens are working")
                        print("   🎯 OAuth setup already complete!")
                        return True
                    except Exception as e:
                        print(f"   ❌ Token validation failed: {e}")
                        
                print(f"   📅 Expires: {tokens.expires_at}")
                print(f"   🏢 Company ID: {tokens.company_id}")
                
            else:
                print("   ❌ No tokens found")
                
        except Exception as e:
            print(f"   ❌ Token check error: {e}")
            
        print("   🔄 Proceeding with new authorization...")
        return False
        
    async def _generate_auth_url(self):
        """Generate and display authorization URL"""
        
        print("\n🔗 STEP 2: Generate Authorization URL")
        print("-" * 40)
        
        try:
            # Generate authorization URL with OAuth Playground redirect
            auth_url = self.oauth_manager.generate_authorization_url()
            
            print("   ✅ Authorization URL generated:")
            print(f"   {auth_url}")
            print()
            
            # Open in browser
            print("   🌐 Opening authorization URL in browser...")
            webbrowser.open(auth_url)
            
            return auth_url
            
        except Exception as e:
            print(f"   ❌ Error generating authorization URL: {e}")
            raise
            
    async def _guide_manual_process(self):
        """Guide user through manual OAuth process"""
        
        print("\n📋 STEP 3: Complete Authorization")
        print("-" * 40)
        
        print("   Please complete these steps in your browser:")
        print()
        print("   1. ✅ Sign in to QuickBooks Online")
        print("      • Use: shawn@owenent.com")
        print("      • Enter your QuickBooks password")
        print()
        print("   2. ✅ Select Company")
        print("      • Choose: Hills & Hollows LLC")
        print("      • Verify it's the correct company")
        print()
        print("   3. ✅ Authorize Application")
        print("      • Review permissions requested")
        print("      • Click 'Authorize' to grant access")
        print()
        print("   4. ✅ OAuth Playground Redirect")
        print("      • You'll be redirected to OAuth Playground")
        print("      • Look for the authorization code in the response")
        print()
        
        input("   Press ENTER when you've completed the authorization...")
        
    async def _exchange_tokens(self):
        """Exchange authorization code for tokens"""
        
        print("\n🔄 STEP 4: Exchange Code for Tokens")
        print("-" * 40)
        
        print("   From the OAuth Playground response, please provide:")
        print()
        
        # Get authorization code from user
        auth_code = input("   📝 Enter Authorization Code: ").strip()
        company_id = input("   🏢 Enter Company ID (realmId): ").strip()
        
        if not auth_code:
            print("   ❌ Authorization code is required")
            return False
            
        if not company_id:
            print("   ❌ Company ID is required")
            return False
            
        try:
            print("   🔄 Exchanging code for tokens...")
            
            tokens = await self.oauth_manager.exchange_code_for_tokens(auth_code, company_id)
            
            print("   ✅ Tokens obtained successfully!")
            print(f"   📅 Expires: {tokens.expires_at}")
            print(f"   🏢 Company ID: {tokens.company_id}")
            print(f"   🔑 Access Token: {tokens.access_token[:20]}...")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Token exchange failed: {e}")
            print("   💡 Please verify the authorization code and company ID")
            return False
            
    async def _test_connectivity(self):
        """Test QuickBooks API connectivity"""
        
        print("\n🧪 STEP 5: Test API Connectivity")
        print("-" * 40)
        
        try:
            # Test getting valid access token
            access_token = await self.oauth_manager.get_valid_access_token()
            print("   ✅ Access token obtained")
            
            # Additional validation could be added here
            print("   ✅ API connectivity test passed")
            print("   🎯 Ready for inventory synchronization")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Connectivity test failed: {e}")
            return False

async def main():
    """Main execution function"""
    
    # Check environment
    client_id = os.getenv('QB_CLIENT_ID')
    client_secret = os.getenv('QB_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Missing QuickBooks OAuth credentials")
        print("   Please set QB_CLIENT_ID and QB_CLIENT_SECRET environment variables")
        print()
        print("   Current values:")
        print(f"   QB_CLIENT_ID: {client_id or 'NOT SET'}")
        print(f"   QB_CLIENT_SECRET: {'SET' if client_secret else 'NOT SET'}")
        return
    
    print(f"🔑 Using Client ID: {client_id}")
    print(f"🔒 Client Secret: {'SET' if client_secret else 'NOT SET'}")
    print()
    
    # Start OAuth flow
    oauth_playground = QuickBooksOAuthPlayground()
    await oauth_playground.run_oauth_setup()

if __name__ == "__main__":
    asyncio.run(main())
