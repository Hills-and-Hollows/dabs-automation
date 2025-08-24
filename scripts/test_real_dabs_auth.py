#!/usr/bin/env python3
"""
Real DABS Authentication Test
Test the actual perform_dabs_login() method
"""

import sys
import asyncio
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.dabs_automated_ordering import DABSAutomatedOrdering

async def test_real_dabs_auth():
    """Test real DABS authentication using perform_dabs_login()"""
    
    print("🔐 REAL DABS AUTHENTICATION TEST")
    print("=" * 60)
    
    try:
        # Initialize DABS processor
        print("🔄 Initializing DABS Automated Ordering System...")
        processor = DABSAutomatedOrdering(headless=False)  # Visible for debugging
        
        # Initialize browser
        print("🌐 Starting browser session...")
        await processor.initialize_browser()
        
        # Attempt authentication
        print("🔑 Attempting DABS authentication...")
        result = await processor.perform_dabs_login()
        
        if result:
            print("✅ AUTHENTICATION SUCCESSFUL!")
            print("🎯 System authenticated and ready for order processing")
            return True
        else:
            print("❌ AUTHENTICATION FAILED")
            print("💡 May require manual intervention or CAPTCHA solving")
            return False
            
    except Exception as e:
        print(f"❌ Authentication Error: {e}")
        print(f"📝 Error Type: {type(e).__name__}")
        return False
    finally:
        # Clean shutdown
        if 'processor' in locals() and processor.browser:
            await processor.browser.close()
        if 'processor' in locals() and processor.playwright:
            await processor.playwright.stop()

if __name__ == "__main__":
    result = asyncio.run(test_real_dabs_auth())
    
    if result:
        print("\n🚀 CONFIRMED: System can authenticate automatically")
        print("✅ Ready to proceed with order creation")
    else:
        print("\n⚠️  Authentication requires attention")
        print("🔧 May need manual CAPTCHA solving or security verification")
