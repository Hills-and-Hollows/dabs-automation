#!/usr/bin/env python3
"""
QuickBooks Environment Checker
=============================

Check if we're using sandbox vs production and what access we should have.
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

async def check_environment():
    """Check QuickBooks environment and access"""
    
    print("🔍 QUICKBOOKS ENVIRONMENT ANALYSIS")
    print("=" * 50)
    
    # Get configuration
    client_id = os.getenv('QB_CLIENT_ID')
    base_url = os.getenv('QB_BASE_URL', 'https://quickbooks.api.intuit.com')
    company_id = "9341455220939846"  # From our tokens
    
    print("📋 Current Configuration:")
    print("-" * 30)
    print(f"   🔑 Client ID: {client_id}")
    print(f"   🌐 Base URL: {base_url}")
    print(f"   🏢 Company ID: {company_id}")
    print()
    
    # Determine environment
    if 'sandbox' in base_url.lower():
        environment = "SANDBOX"
        expected_company_format = "Sandbox company (usually starts with 123)"
        print("🧪 ENVIRONMENT: SANDBOX")
        print("   ✅ Should work with development apps")
        print("   📊 Uses test data only")
    else:
        environment = "PRODUCTION"
        expected_company_format = "Real QuickBooks Online company"
        print("🏭 ENVIRONMENT: PRODUCTION")
        print("   ⚠️  Requires published app OR developer's own company")
        print("   📊 Uses real business data")
    
    print(f"   🎯 Company Type: {expected_company_format}")
    print()
    
    # Analyze company ID
    print("🏢 Company ID Analysis:")
    print("-" * 30)
    
    if environment == "SANDBOX":
        if company_id.startswith('123'):
            print("   ✅ Company ID format matches sandbox pattern")
        else:
            print("   ⚠️  Company ID doesn't look like sandbox format")
            print("   💡 Sandbox companies usually start with '123'")
    else:
        print(f"   📊 Production Company ID: {company_id}")
        print("   🎯 This is a real QuickBooks Online company")
        
        # Check if this could be the developer's company
        if len(company_id) > 10:
            print("   ✅ Company ID format looks valid for production")
        else:
            print("   ⚠️  Company ID format seems unusual")
    
    print()
    
    # Check what access we should have
    print("🔐 Expected Access Rights:")
    print("-" * 30)
    
    if environment == "SANDBOX":
        print("   ✅ Development app should have full access to sandbox")
        print("   ✅ No publishing required for sandbox")
        print("   🎯 Perfect for testing and development")
    else:
        print("   🤔 Development app accessing production company...")
        print("   📋 This works ONLY if:")
        print("      1. ✅ Company belongs to the app developer")
        print("      2. ✅ Developer has admin access to the company")
        print("      3. ✅ App was authorized by the company admin")
        print("   ❌ Will NOT work for other companies without publishing")
    
    print()
    
    # Test sandbox endpoint if we think we should be using sandbox
    if environment == "PRODUCTION":
        print("🧪 Testing Sandbox Alternative:")
        print("-" * 30)
        
        sandbox_url = "https://sandbox-quickbooks.api.intuit.com"
        print(f"   🔄 Sandbox URL: {sandbox_url}")
        print("   💡 Consider switching to sandbox for development")
        print("   📋 Sandbox benefits:")
        print("      - No publishing required")
        print("      - Safe test environment")
        print("      - Full API access")
        print("      - No risk to real data")
    
    print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS:")
    print("-" * 30)
    
    if environment == "SANDBOX":
        print("   ✅ Current setup is ideal for development")
        print("   🔄 If still getting 403 errors:")
        print("      1. Re-run OAuth flow")
        print("      2. Check app permissions in developer dashboard")
        print("      3. Verify sandbox company is properly set up")
    else:
        print("   🎯 You have TWO options:")
        print()
        print("   📋 OPTION A: Continue with Production (Current)")
        print("      ✅ Pros: Real data, production environment")
        print("      ❌ Cons: Requires app publishing for other companies")
        print("      🔧 Next steps:")
        print("         1. Verify this is YOUR QuickBooks company")
        print("         2. Re-authorize the app")
        print("         3. If still fails, publish the app")
        print()
        print("   📋 OPTION B: Switch to Sandbox (Recommended for Dev)")
        print("      ✅ Pros: No publishing needed, safe testing")
        print("      ❌ Cons: Test data only")
        print("      🔧 Next steps:")
        print("         1. Update QB_BASE_URL to sandbox")
        print("         2. Create sandbox company")
        print("         3. Re-run OAuth with sandbox")
    
    print()
    
    # Show how to switch to sandbox
    print("🔧 HOW TO SWITCH TO SANDBOX:")
    print("-" * 30)
    print("   1. Update environment variable:")
    print("      QB_BASE_URL=https://sandbox-quickbooks.api.intuit.com")
    print()
    print("   2. Create sandbox company:")
    print("      - Go to https://developer.intuit.com/")
    print("      - Navigate to your app")
    print("      - Use 'Sandbox' environment")
    print("      - Create test company")
    print()
    print("   3. Re-run OAuth setup:")
    print("      python3 scripts/setup_quickbooks_oauth.py")
    
    print()
    
    # Final recommendation
    print("🎯 IMMEDIATE RECOMMENDATION:")
    print("-" * 30)
    
    if environment == "PRODUCTION":
        print("   🔄 Try re-authorizing first:")
        print("      python3 scripts/setup_quickbooks_oauth.py")
        print()
        print("   📊 If that fails, the issue is likely:")
        print("      - App needs to be published, OR")
        print("      - This isn't the developer's company, OR") 
        print("      - Company admin needs to authorize")
        print()
        print("   💡 For development, consider switching to sandbox")
    else:
        print("   ✅ Sandbox setup looks good")
        print("   🔄 Re-run OAuth to fix authorization")

if __name__ == "__main__":
    asyncio.run(check_environment())
