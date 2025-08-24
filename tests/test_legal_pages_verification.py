#!/usr/bin/env python3
"""
Legal Pages Verification Test
Hills & Hollows LLC - DABS Automation System

Verifies that the legal pages are accessible and contain required content
for QuickBooks production app compliance.
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class LegalPagesVerifier:
    """Verify legal pages for QuickBooks compliance"""
    
    def __init__(self):
        self.base_url = "https://hillsandhollowsmarket.com"
        self.eula_url = f"{self.base_url}/dabs-eula/"
        self.privacy_url = f"{self.base_url}/dabs-privacy-policy/"
        self.results = {
            "eula": {"accessible": False, "content_valid": False, "errors": []},
            "privacy": {"accessible": False, "content_valid": False, "errors": []}
        }
    
    async def verify_pages(self):
        """Verify both legal pages"""
        
        print("🔍 LEGAL PAGES VERIFICATION")
        print("=" * 50)
        print(f"🌐 Domain: {self.base_url}")
        print(f"📄 EULA: {self.eula_url}")
        print(f"🔒 Privacy: {self.privacy_url}")
        print()
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Test EULA page
                await self._verify_eula_page(page)
                
                # Test Privacy page
                await self._verify_privacy_page(page)
                
            finally:
                await browser.close()
        
        # Generate report
        self._generate_report()
    
    async def _verify_eula_page(self, page):
        """Verify EULA page accessibility and content"""
        
        print("📋 TESTING EULA PAGE")
        print("-" * 30)
        
        try:
            # Navigate to EULA page
            print(f"🔗 Loading: {self.eula_url}")
            response = await page.goto(self.eula_url, wait_until="networkidle")
            
            if response.status == 200:
                self.results["eula"]["accessible"] = True
                print("✅ Page accessible (200 OK)")
            else:
                self.results["eula"]["errors"].append(f"HTTP {response.status}")
                print(f"❌ Page returned HTTP {response.status}")
                return
            
            # Check page title
            title = await page.title()
            print(f"📄 Page title: {title}")
            
            # Check for required EULA content
            required_content = [
                "Hills & Hollows LLC",
                "DABS Automation System",
                "Utah Package Agency",
                "License Grant",
                "QuickBooks",
                "admin@hillshollows.com"
            ]
            
            page_content = await page.content()
            missing_content = []
            
            for content in required_content:
                if content.lower() in page_content.lower():
                    print(f"✅ Found: {content}")
                else:
                    missing_content.append(content)
                    print(f"❌ Missing: {content}")
            
            if not missing_content:
                self.results["eula"]["content_valid"] = True
                print("✅ All required content found")
            else:
                self.results["eula"]["errors"].extend(missing_content)
                print(f"❌ Missing content: {missing_content}")
            
            # Check for proper HTML structure
            headings = await page.query_selector_all("h1, h2, h3")
            print(f"📋 Found {len(headings)} headings")
            
            # Take screenshot for verification
            await page.screenshot(path="test_results/eula_page_screenshot.png")
            print("📸 Screenshot saved: test_results/eula_page_screenshot.png")
            
        except Exception as e:
            self.results["eula"]["errors"].append(str(e))
            print(f"❌ Error testing EULA page: {e}")
        
        print()
    
    async def _verify_privacy_page(self, page):
        """Verify Privacy Policy page accessibility and content"""
        
        print("🔒 TESTING PRIVACY POLICY PAGE")
        print("-" * 30)
        
        try:
            # Navigate to Privacy page
            print(f"🔗 Loading: {self.privacy_url}")
            response = await page.goto(self.privacy_url, wait_until="networkidle")
            
            if response.status == 200:
                self.results["privacy"]["accessible"] = True
                print("✅ Page accessible (200 OK)")
            else:
                self.results["privacy"]["errors"].append(f"HTTP {response.status}")
                print(f"❌ Page returned HTTP {response.status}")
                return
            
            # Check page title
            title = await page.title()
            print(f"📄 Page title: {title}")
            
            # Check for required Privacy Policy content
            required_content = [
                "Privacy Policy",
                "Hills & Hollows LLC",
                "DABS Automation System",
                "Information We Collect",
                "Data Security",
                "QuickBooks Online",
                "Utah Package Agency",
                "admin@hillshollows.com"
            ]
            
            page_content = await page.content()
            missing_content = []
            
            for content in required_content:
                if content.lower() in page_content.lower():
                    print(f"✅ Found: {content}")
                else:
                    missing_content.append(content)
                    print(f"❌ Missing: {content}")
            
            if not missing_content:
                self.results["privacy"]["content_valid"] = True
                print("✅ All required content found")
            else:
                self.results["privacy"]["errors"].extend(missing_content)
                print(f"❌ Missing content: {missing_content}")
            
            # Check for proper HTML structure
            headings = await page.query_selector_all("h1, h2, h3")
            print(f"📋 Found {len(headings)} headings")
            
            # Take screenshot for verification
            await page.screenshot(path="test_results/privacy_page_screenshot.png")
            print("📸 Screenshot saved: test_results/privacy_page_screenshot.png")
            
        except Exception as e:
            self.results["privacy"]["errors"].append(str(e))
            print(f"❌ Error testing Privacy page: {e}")
        
        print()
    
    def _generate_report(self):
        """Generate verification report"""
        
        print("📊 VERIFICATION REPORT")
        print("=" * 50)
        
        # EULA Results
        print("📋 EULA Page:")
        if self.results["eula"]["accessible"] and self.results["eula"]["content_valid"]:
            print("   ✅ PASSED - Ready for QuickBooks compliance")
        else:
            print("   ❌ FAILED - Issues found:")
            for error in self.results["eula"]["errors"]:
                print(f"      - {error}")
        
        # Privacy Results
        print("\n🔒 Privacy Policy Page:")
        if self.results["privacy"]["accessible"] and self.results["privacy"]["content_valid"]:
            print("   ✅ PASSED - Ready for QuickBooks compliance")
        else:
            print("   ❌ FAILED - Issues found:")
            for error in self.results["privacy"]["errors"]:
                print(f"      - {error}")
        
        # Overall Status
        print(f"\n🎯 OVERALL STATUS:")
        if (self.results["eula"]["accessible"] and self.results["eula"]["content_valid"] and
            self.results["privacy"]["accessible"] and self.results["privacy"]["content_valid"]):
            print("   ✅ ALL TESTS PASSED")
            print("   🚀 Ready for QuickBooks production app configuration")
            print(f"\n📋 URLs for QuickBooks Developer Dashboard:")
            print(f"   EULA: {self.eula_url}")
            print(f"   Privacy: {self.privacy_url}")
        else:
            print("   ❌ TESTS FAILED")
            print("   🔧 Please fix issues before proceeding")
        
        print()

async def main():
    """Main verification function"""
    
    # Create test results directory
    Path("test_results").mkdir(exist_ok=True)
    
    # Run verification
    verifier = LegalPagesVerifier()
    await verifier.verify_pages()

if __name__ == "__main__":
    asyncio.run(main())
