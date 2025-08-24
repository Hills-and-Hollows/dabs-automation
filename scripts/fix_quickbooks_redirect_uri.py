#!/usr/bin/env python3
"""
QuickBooks Redirect URI Configuration Helper
Helps fix the redirect URI configuration issue

This script provides step-by-step instructions to fix the redirect URI
configuration in your QuickBooks app settings.

Author: DABS Automation System
Created: 2025-08-22
"""

import os
import sys
from pathlib import Path

def main():
    """Main function to guide redirect URI configuration"""
    
    print("🔧 QUICKBOOKS REDIRECT URI CONFIGURATION FIX")
    print("=" * 60)
    print("Hills & Hollows LLC - DABS Automation")
    print()
    
    print("❌ PROBLEM IDENTIFIED:")
    print("   The redirect_uri query parameter value is invalid")
    print("   Current redirect URI: https://localhost:8000/auth/quickbooks/callback")
    print()
    
    print("🛠️  SOLUTION STEPS:")
    print()
    
    print("STEP 1: Access QuickBooks Developer Dashboard")
    print("   1. Go to: https://developer.intuit.com/")
    print("   2. Sign in with: shawn@owenent.com")
    print("   3. Navigate to 'My Apps'")
    print("   4. Select: 'Hills & Hollows DABS Automation'")
    print()
    
    print("STEP 2: Update Redirect URIs")
    print("   1. Click on the 'Keys & OAuth' tab")
    print("   2. Scroll down to 'Redirect URIs' section")
    print("   3. Add these redirect URIs (one per line):")
    print("      • http://localhost:8000/auth/quickbooks/callback")
    print("      • https://localhost:8000/auth/quickbooks/callback")
    print("      • http://127.0.0.1:8000/auth/quickbooks/callback")
    print("      • https://127.0.0.1:8000/auth/quickbooks/callback")
    print("   4. Click 'Save' to update the configuration")
    print()
    
    print("STEP 3: Verify App Configuration")
    print("   1. Ensure 'QuickBooks Online Accounting API' scope is enabled")
    print("   2. Verify the app is in 'Production' mode (not Sandbox)")
    print("   3. Check that Client ID matches: AB8BKzC2sT9vXeg5wKuwF2Irk990qM7G5UMSltwXd3UNFfUde3")
    print()
    
    print("STEP 4: Test the Configuration")
    print("   After updating the redirect URIs, run:")
    print("   python scripts/quickbooks_oauth_server.py")
    print()
    
    print("📋 ALTERNATIVE REDIRECT URIS TO TRY:")
    print("   If the above doesn't work, try these alternatives:")
    print("   • http://localhost:8000/callback")
    print("   • https://localhost:8000/callback")
    print("   • http://localhost:8000/")
    print("   • https://localhost:8000/")
    print()
    
    print("🔍 TROUBLESHOOTING TIPS:")
    print("   • Redirect URIs are case-sensitive")
    print("   • Must match exactly (including http/https)")
    print("   • No trailing slashes unless specified")
    print("   • Wait 5-10 minutes after saving changes")
    print()
    
    print("📞 SUPPORT RESOURCES:")
    print("   • QuickBooks Developer Support: https://help.developer.intuit.com/")
    print("   • OAuth 2.0 Documentation: https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth-2.0")
    print()
    
    # Check current environment
    client_id = os.getenv('QB_CLIENT_ID')
    if client_id:
        print(f"✅ Current Client ID: {client_id}")
    else:
        print("⚠️  QB_CLIENT_ID environment variable not set")
    
    print()
    print("🎯 Once you've updated the redirect URIs in the QuickBooks Developer Dashboard,")
    print("   run the OAuth server script to complete the setup:")
    print("   python scripts/quickbooks_oauth_server.py")

if __name__ == "__main__":
    main()
