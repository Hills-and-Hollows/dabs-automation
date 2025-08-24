#!/usr/bin/env python3
"""
Definitive DABS Authentication Test
Test if we can authenticate automatically without user intervention
"""

import sys
import asyncio
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.dabs_automated_ordering import DABSAutomatedOrdering

async def definitive_dabs_auth_test():
    """Definitive test of DABS automatic authentication capability"""
    
    print("🔐 DEFINITIVE DABS AUTHENTICATION TEST")
    print("=" * 60)
    print("Testing whether AI can authenticate to DABS without user intervention...")
    print()
    
    processor = None
    try:
        # Initialize DABS processor
        print("🔄 Initializing DABS Automated Ordering System...")
        processor = DABSAutomatedOrdering(headless=True, timeout=30000)
        
        # Initialize automation system
        print("🌐 Starting automation system...")
        await processor.initialize_automation_system()
        
        # Test authentication
        print("🔑 Attempting automated login...")
        auth_result = await processor.perform_dabs_login()
        
        if auth_result:
            print("✅ SUCCESS: Automatic authentication WORKS!")
            print("🎯 AI can authenticate to DABS without user intervention")
            print("🚀 System ready for automated order processing")
            return True
        else:
            print("❌ FAILED: Automatic authentication blocked")
            print("💡 Likely causes:")
            print("   • CAPTCHA verification required")
            print("   • Rate limiting/IP blocking")
            print("   • Browser fingerprint detection")
            print("   • Security policy changes")
            return False
            
    except Exception as e:
        print(f"❌ AUTHENTICATION ERROR: {e}")
        
        if "timeout" in str(e).lower():
            print("💡 TIMEOUT: Site may be slow or blocking automated access")
        elif "captcha" in str(e).lower():
            print("💡 CAPTCHA: Manual verification required")  
        elif "rate" in str(e).lower():
            print("💡 RATE LIMITING: Too many attempts, IP may be blocked")
        else:
            print("💡 UNKNOWN ERROR: Manual investigation needed")
            
        return False
        
    finally:
        # Cleanup
        if processor:
            try:
                await processor.cleanup()
            except:
                pass

if __name__ == "__main__":
    print("🎯 QUESTION: Can AI authenticate to DABS automatically?")
    print("🔍 TESTING: Automated login capabilities...")
    print()
    
    result = asyncio.run(definitive_dabs_auth_test())
    
    print("\n" + "=" * 60)
    if result:
        print("✅ ANSWER: YES - AI can authenticate automatically")
        print("🚀 Ready to proceed with order creation")
    else:
        print("❌ ANSWER: NO - Manual assistance required")
        print("👤 User intervention needed for authentication")
    print("=" * 60)
