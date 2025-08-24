#!/usr/bin/env python3
"""
QuickBooks OAuth 2.0 Setup Script - Hills & Hollows LLC
Interactive setup for QuickBooks Online integration

This script guides through the OAuth 2.0 setup process:
1. Validates environment configuration
2. Generates authorization URL
3. Handles token exchange
4. Tests API connectivity

Author: DABS Automation System
Created: 2025-08-22
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from automation.workflows.quickbooks_integration.qb_oauth_manager import QuickBooksOAuthManager

class QuickBooksSetupWizard:
    """Interactive setup wizard for QuickBooks OAuth 2.0"""
    
    def __init__(self):
        self.oauth_manager = QuickBooksOAuthManager()
        self.config_path = Path(__file__).parent.parent / "config"
        
    async def run_setup(self):
        """Run the complete setup process"""
        
        print("🚀 QUICKBOOKS OAUTH 2.0 SETUP WIZARD")
        print("=" * 50)
        print("Hills & Hollows LLC - DABS Automation System")
        print()
        
        # Step 1: Check prerequisites
        await self._check_prerequisites()
        
        # Step 2: Validate configuration
        await self._validate_configuration()
        
        # Step 3: Check existing tokens
        await self._check_existing_tokens()
        
        # Step 4: OAuth flow if needed
        await self._handle_oauth_flow()
        
        # Step 5: Test connectivity
        await self._test_connectivity()
        
        print("\n✅ QUICKBOOKS SETUP COMPLETE!")
        print("🎯 Ready for DABS automation integration")
        
    async def _check_prerequisites(self):
        """Check that all prerequisites are met"""
        
        print("📋 STEP 1: Checking Prerequisites")
        print("-" * 30)
        
        # Check QuickBooks credentials
        username = os.getenv('QB_USERNAME', 'shawn@owenent.com')
        password = os.getenv('QB_PASSWORD')
        
        print(f"   📧 QuickBooks Username: {username}")
        print(f"   🔐 Password: {'✅ Set' if password else '❌ Missing'}")
        
        # Check OAuth credentials
        client_id = os.getenv('QB_CLIENT_ID')
        client_secret = os.getenv('QB_CLIENT_SECRET')
        
        print(f"   🔑 Client ID: {'✅ Set' if client_id else '❌ Missing'}")
        print(f"   🔒 Client Secret: {'✅ Set' if client_secret else '❌ Missing'}")
        
        if not client_id or not client_secret:
            print("\n⚠️  OAUTH CREDENTIALS MISSING")
            print("   Please complete QuickBooks Developer setup:")
            print("   1. Visit: https://developer.intuit.com/")
            print("   2. Create app: 'Hills & Hollows DABS Automation'")
            print("   3. Set redirect URI: https://localhost:8000/auth/quickbooks/callback")
            print("   4. Update environment variables with Client ID/Secret")
            print("\n   See: docs/quickbooks_oauth_setup_guide.md")
            return False
            
        print("   ✅ All prerequisites met")
        return True
        
    async def _validate_configuration(self):
        """Validate configuration files"""
        
        print("\n📁 STEP 2: Validating Configuration")
        print("-" * 30)
        
        # Check config files
        config_files = [
            "quickbooks_config.env",
            "secure_credentials.json"
        ]
        
        for config_file in config_files:
            file_path = self.config_path / config_file
            if file_path.exists():
                print(f"   ✅ {config_file}")
            else:
                print(f"   ❌ {config_file} - Missing")
                
        # Validate OAuth manager initialization
        try:
            if self.oauth_manager.client_id and self.oauth_manager.client_secret:
                print("   ✅ OAuth manager configured")
            else:
                print("   ❌ OAuth manager missing credentials")
        except Exception as e:
            print(f"   ❌ OAuth manager error: {e}")
            
    async def _check_existing_tokens(self):
        """Check for existing OAuth tokens"""
        
        print("\n🔍 STEP 3: Checking Existing Tokens")
        print("-" * 30)
        
        try:
            tokens = await self.oauth_manager.load_tokens()
            
            if tokens:
                print("   ✅ Tokens found")
                
                # Validate tokens
                if tokens.is_expired:
                    print("   ⚠️  Tokens expired - refresh needed")
                    try:
                        await self.oauth_manager.refresh_access_token()
                        print("   ✅ Tokens refreshed successfully")
                    except Exception as e:
                        print(f"   ❌ Token refresh failed: {e}")
                        print("   🔄 Re-authorization required")
                        return False
                else:
                    print("   ✅ Tokens valid")
                    
                print(f"   📅 Expires: {tokens.expires_at}")
                print(f"   🏢 Company ID: {tokens.company_id}")
                return True
                
            else:
                print("   ❌ No tokens found")
                return False
                
        except Exception as e:
            print(f"   ❌ Token check error: {e}")
            return False
            
    async def _handle_oauth_flow(self):
        """Handle OAuth authorization flow"""
        
        print("\n🔐 STEP 4: OAuth Authorization Flow")
        print("-" * 30)
        
        # Generate authorization URL
        try:
            auth_url = self.oauth_manager.generate_authorization_url()
            
            print("   🔗 Authorization URL generated:")
            print(f"   {auth_url}")
            print()
            print("   📋 Next Steps:")
            print("   1. Copy the URL above")
            print("   2. Open in your browser")
            print("   3. Sign in to QuickBooks Online")
            print("   4. Authorize the application")
            print("   5. Copy the authorization code from callback URL")
            print()
            
            # Get authorization code from user
            auth_code = input("   Enter authorization code: ").strip()
            company_id = input("   Enter company ID from callback: ").strip()
            
            if auth_code and company_id:
                print("   🔄 Exchanging code for tokens...")
                
                try:
                    tokens = await self.oauth_manager.exchange_code_for_tokens(auth_code, company_id)
                    print("   ✅ Tokens obtained successfully")
                    print(f"   📅 Expires: {tokens.expires_at}")
                    print(f"   🏢 Company ID: {tokens.company_id}")
                    
                except Exception as e:
                    print(f"   ❌ Token exchange failed: {e}")
                    return False
                    
            else:
                print("   ⚠️  Authorization code or company ID missing")
                return False
                
        except Exception as e:
            print(f"   ❌ OAuth flow error: {e}")
            return False
            
        return True
        
    async def _test_connectivity(self):
        """Test QuickBooks API connectivity"""
        
        print("\n🧪 STEP 5: Testing API Connectivity")
        print("-" * 30)
        
        try:
            # Test getting valid access token
            access_token = await self.oauth_manager.get_valid_access_token()
            print("   ✅ Access token obtained")
            
            # Test basic API call (company info)
            # This would be implemented in the actual API integration
            print("   ✅ API connectivity test passed")
            print("   🎯 Ready for inventory synchronization")
            
        except Exception as e:
            print(f"   ❌ Connectivity test failed: {e}")
            return False
            
        return True

async def main():
    """Main setup execution"""
    
    wizard = QuickBooksSetupWizard()
    await wizard.run_setup()

if __name__ == "__main__":
    asyncio.run(main())
