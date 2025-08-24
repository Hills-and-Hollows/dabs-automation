#!/usr/bin/env python3
"""
QuickBooks App Configuration Debug
=================================

Debug QuickBooks app configuration and environment settings.
"""

import asyncio
import aiohttp
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv(project_root / '.env')
load_dotenv(project_root / 'config/quickbooks_config.env')

async def debug_app_config():
    """Debug QuickBooks app configuration"""
    
    print("🔍 QUICKBOOKS APP CONFIGURATION DEBUG")
    print("=" * 50)
    
    # Get configuration
    client_id = os.getenv('QB_CLIENT_ID')
    client_secret = os.getenv('QB_CLIENT_SECRET')
    base_url = os.getenv('QB_BASE_URL', 'https://quickbooks.api.intuit.com')
    scope = os.getenv('QB_SCOPE', 'com.intuit.quickbooks.accounting')
    redirect_uri = os.getenv('QB_REDIRECT_URI', 'https://localhost:8000/auth/quickbooks/callback')
    
    print("📋 Current Configuration:")
    print("-" * 30)
    print(f"   🔑 Client ID: {client_id}")
    print(f"   🔒 Client Secret: {client_secret[:10]}...")
    print(f"   🌐 Base URL: {base_url}")
    print(f"   🎯 Scope: {scope}")
    print(f"   🔄 Redirect URI: {redirect_uri}")
    print()
    
    # Determine environment
    if 'sandbox' in base_url.lower():
        environment = "SANDBOX"
        print("🧪 Environment: SANDBOX")
    else:
        environment = "PRODUCTION"
        print("🏭 Environment: PRODUCTION")
    print()
    
    # Test OAuth discovery endpoint
    print("🔍 Testing OAuth Discovery:")
    print("-" * 30)
    
    discovery_url = "https://appcenter.intuit.com/connect/oauth2"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test if we can reach the OAuth endpoint
            async with session.get(discovery_url) as response:
                print(f"   📡 Discovery URL: {discovery_url}")
                print(f"   📊 Status: {response.status}")
                
                if response.status == 200:
                    print("   ✅ OAuth discovery endpoint reachable")
                else:
                    print("   ❌ OAuth discovery endpoint issue")
    except Exception as e:
        print(f"   ❌ Discovery test failed: {e}")
    
    print()
    
    # Test authorization URL generation
    print("🔗 Testing Authorization URL Generation:")
    print("-" * 30)
    
    try:
        import secrets
        from urllib.parse import urlencode
        
        state = secrets.token_urlsafe(32)
        
        auth_params = {
            'client_id': client_id,
            'scope': scope,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'access_type': 'offline',
            'state': state
        }
        
        auth_url = f"https://appcenter.intuit.com/connect/oauth2?{urlencode(auth_params)}"
        
        print(f"   ✅ Authorization URL generated successfully")
        print(f"   🔗 URL: {auth_url[:100]}...")
        print()
        
        # Validate URL components
        print("🔍 URL Component Analysis:")
        print("-" * 30)
        print(f"   🔑 client_id: {auth_params['client_id']}")
        print(f"   🎯 scope: {auth_params['scope']}")
        print(f"   🔄 redirect_uri: {auth_params['redirect_uri']}")
        print(f"   📝 response_type: {auth_params['response_type']}")
        print(f"   🔐 access_type: {auth_params['access_type']}")
        print()
        
    except Exception as e:
        print(f"   ❌ Authorization URL generation failed: {e}")
    
    # Test token endpoint accessibility
    print("🔐 Testing Token Endpoint:")
    print("-" * 30)
    
    token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test POST to token endpoint (will fail but should be reachable)
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {'grant_type': 'test'}  # Invalid but tests reachability
            
            async with session.post(token_url, headers=headers, data=data) as response:
                print(f"   📡 Token URL: {token_url}")
                print(f"   📊 Status: {response.status}")
                
                if response.status in [400, 401]:  # Expected for invalid request
                    print("   ✅ Token endpoint reachable (400/401 expected)")
                    
                    response_text = await response.text()
                    print(f"   📄 Response: {response_text[:200]}...")
                else:
                    print(f"   ⚠️  Unexpected status: {response.status}")
                    
    except Exception as e:
        print(f"   ❌ Token endpoint test failed: {e}")
    
    print()
    
    # Analyze potential issues
    print("🎯 POTENTIAL ISSUES ANALYSIS:")
    print("-" * 30)
    
    issues = []
    
    # Check environment consistency
    if environment == "PRODUCTION":
        if 'sandbox' in base_url.lower():
            issues.append("❌ Environment mismatch: Using production app with sandbox URL")
        else:
            print("   ✅ Environment consistency: Production app with production URL")
    
    # Check scope
    if scope != 'com.intuit.quickbooks.accounting':
        issues.append(f"❌ Scope issue: Expected 'com.intuit.quickbooks.accounting', got '{scope}'")
    else:
        print("   ✅ Scope correct: com.intuit.quickbooks.accounting")
    
    # Check redirect URI
    if not redirect_uri.startswith('https://localhost:8000'):
        issues.append(f"❌ Redirect URI issue: Expected localhost:8000, got '{redirect_uri}'")
    else:
        print("   ✅ Redirect URI format correct")
    
    # Check client ID format
    if not client_id or len(client_id) < 30:
        issues.append("❌ Client ID format issue: Too short or missing")
    else:
        print("   ✅ Client ID format appears correct")
    
    if issues:
        print("\n🚨 IDENTIFIED ISSUES:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ No obvious configuration issues found")
    
    print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS:")
    print("-" * 30)
    
    if environment == "PRODUCTION":
        print("   1. ✅ Using PRODUCTION environment - correct for live data")
        print("   2. 🔍 Check Intuit Developer Dashboard:")
        print("      - Verify app is PUBLISHED (not in development)")
        print("      - Confirm redirect URI exactly matches")
        print("      - Check app permissions/scopes")
        print("      - Verify app is approved for production")
        print("   3. 🔄 Try re-authorizing the app:")
        print("      - Disconnect app in QuickBooks Online")
        print("      - Re-run OAuth flow with fresh authorization")
    else:
        print("   1. 🧪 Using SANDBOX environment")
        print("   2. Consider switching to production for live data")
    
    print("\n🎯 NEXT STEPS:")
    print("-" * 30)
    print("   1. Check Intuit Developer Dashboard app status")
    print("   2. Verify app is published and approved")
    print("   3. Confirm redirect URI matches exactly")
    print("   4. Try disconnecting and re-authorizing the app")

if __name__ == "__main__":
    asyncio.run(debug_app_config())
