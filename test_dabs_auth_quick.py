#!/usr/bin/env python3
"""
Quick DABS Authentication Test
Check if we can authenticate with the production credentials
"""

import sys
import asyncio
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.dabs_automated_ordering import DABSAutomatedOrdering

async def test_dabs_auth():
    """Test DABS authentication with production credentials"""
    
    print("🔍 Testing DABS Authentication with Production Credentials")
    print("=" * 60)
    
    try:
        # Load environment variables from config
        env_file = Path(__file__).parent.parent / "config" / "dabs_ordering.env"
        
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        
        print(f"🌐 URL: {os.environ.get('DABS_ORDERING_LOGIN_URL', 'Not found')}")
        print(f"👤 Username: {os.environ.get('DABS_ORDERING_USERNAME', 'Not found')}")
        print(f"🔐 Password: {'[LOADED]' if os.environ.get('DABS_ORDERING_PASSWORD') else '[MISSING]'}")
        print()
        
        # Initialize DABS processor
        processor = DABSAutomatedOrdering()
        
        # Test authentication
        print("🔄 Attempting authentication...")
        result = await processor._authenticate_dabs()
        
        if result:
            print("✅ Authentication SUCCESSFUL!")
            print("🎯 Ready to proceed with order creation")
            
            # Quick check for existing open orders
            print("\n🔍 Checking for existing open orders...")
            # This would typically be done within authenticated session
            
        else:
            print("❌ Authentication FAILED")
            print("💡 Manual intervention may be required")
            
        return result
        
    except Exception as e:
        print(f"❌ Authentication Error: {e}")
        print(f"📝 Error Type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_dabs_auth())
    
    if result:
        print("\n🚀 System ready for automated order creation")
    else:
        print("\n⚠️  System requires manual authentication assistance")
