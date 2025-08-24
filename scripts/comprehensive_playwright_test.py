#!/usr/bin/env python3
"""
Comprehensive Playwright E2E Test Suite for Archon
Tests all possible endpoints and deployment scenarios
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError

class ComprehensiveArchonTester:
    """Complete E2E testing for Archon system"""
    
    def __init__(self):
        self.test_results = {
            "test_start": datetime.now().isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": []
        }
        
        # Test multiple possible endpoints
        self.test_endpoints = [
            {"url": "http://localhost:8151", "name": "Local Server", "expected": True},
            {"url": "http://localhost:3837", "name": "UI (Custom Port)", "expected": False},
            {"url": "http://localhost:3737", "name": "UI (Default Port)", "expected": False},
            {"url": "http://localhost:8281", "name": "Server (Custom Port)", "expected": False},
            {"url": "http://localhost:8181", "name": "Server (Default Port)", "expected": False}
        ]
        
        self.screenshots_dir = Path("data/playwright_screenshots")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async def run_comprehensive_tests(self):
        """Run complete E2E test suite"""
        
        print("🎭 COMPREHENSIVE ARCHON E2E TEST SUITE")
        print("=" * 60)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Testing {len(self.test_endpoints)} endpoints")
        print()
        
        async with async_playwright() as p:
            # Test with multiple browsers for comprehensive coverage
            browsers = [
                {"browser": p.chromium, "name": "Chromium"},
                {"browser": p.firefox, "name": "Firefox"} if hasattr(p, 'firefox') else None
            ]
            
            browsers = [b for b in browsers if b is not None]
            
            for browser_info in browsers:
                await self._test_with_browser(browser_info)
        
        # Generate comprehensive report
        await self._generate_final_report()
    
    async def _test_with_browser(self, browser_info):
        """Test with specific browser"""
        
        print(f"🌐 Testing with {browser_info['name']}")
        print("-" * 40)
        
        try:
            browser = await browser_info["browser"].launch(headless=False, slow_mo=500)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Set up logging
            page.on("console", lambda msg: print(f"   🖥️  Console: {msg.text}"))
            page.on("pageerror", lambda err: print(f"   ❌ Page Error: {err}"))
            
            # Test each endpoint
            for endpoint in self.test_endpoints:
                await self._test_endpoint(page, endpoint, browser_info['name'])
            
            # Test API endpoints if server is running
            await self._test_api_endpoints(page)
            
            # Keep browser open briefly for inspection
            await asyncio.sleep(5)
            
            await browser.close()
            print(f"✅ {browser_info['name']} testing complete\n")
            
        except Exception as e:
            print(f"❌ {browser_info['name']} testing failed: {e}\n")
    
    async def _test_endpoint(self, page, endpoint, browser_name):
        """Test individual endpoint"""
        
        test_name = f"{endpoint['name']} ({browser_name})"
        print(f"   🧪 Testing: {test_name}")
        
        try:
            # Attempt navigation
            response = await page.goto(endpoint["url"], timeout=10000, wait_until="domcontentloaded")
            
            # Check response status
            if response and response.status < 400:
                # Take success screenshot
                screenshot_path = self.screenshots_dir / f"success_{endpoint['name'].lower().replace(' ', '_')}_{browser_name.lower()}_{datetime.now().strftime('%H%M%S')}.png"
                await page.screenshot(path=str(screenshot_path))
                
                # Test passed
                self.test_results["tests_passed"] += 1
                self.test_results["test_details"].append({
                    "test": test_name,
                    "status": "PASS",
                    "endpoint": endpoint["url"],
                    "browser": browser_name,
                    "screenshot": str(screenshot_path),
                    "response_status": response.status if response else "unknown"
                })
                print(f"      ✅ PASS - Status: {response.status if response else 'N/A'}")
                
                # Test page content
                title = await page.title()
                if title:
                    print(f"      📑 Title: {title}")
                
            else:
                # Server error
                self.test_results["tests_failed"] += 1
                self.test_results["test_details"].append({
                    "test": test_name,
                    "status": "FAIL",
                    "endpoint": endpoint["url"],
                    "browser": browser_name,
                    "error": f"HTTP {response.status if response else 'No response'}"
                })
                print(f"      ❌ FAIL - HTTP {response.status if response else 'No response'}")
                
        except TimeoutError:
            # Connection timeout
            screenshot_path = self.screenshots_dir / f"timeout_{endpoint['name'].lower().replace(' ', '_')}_{browser_name.lower()}_{datetime.now().strftime('%H%M%S')}.png"
            await page.screenshot(path=str(screenshot_path))
            
            self.test_results["tests_failed"] += 1
            self.test_results["test_details"].append({
                "test": test_name,
                "status": "FAIL",
                "endpoint": endpoint["url"],
                "browser": browser_name,
                "error": "Connection timeout",
                "screenshot": str(screenshot_path)
            })
            print(f"      ❌ FAIL - Connection timeout")
            
        except Exception as e:
            # Other error
            self.test_results["tests_failed"] += 1
            self.test_results["test_details"].append({
                "test": test_name,
                "status": "FAIL",
                "endpoint": endpoint["url"], 
                "browser": browser_name,
                "error": str(e)
            })
            print(f"      ❌ FAIL - {e}")
    
    async def _test_api_endpoints(self, page):
        """Test API endpoints if server is responding"""
        
        print("   🔌 Testing API endpoints...")
        
        api_tests = [
            {"url": "http://localhost:8151/health", "name": "Health API"},
            {"url": "http://localhost:8151/mcp/sse", "name": "MCP SSE"},
            {"url": "http://localhost:8151/projects", "name": "Projects API"}
        ]
        
        for api_test in api_tests:
            try:
                response = await page.request.get(api_test["url"])
                if response.status < 400:
                    print(f"      ✅ {api_test['name']}: Status {response.status}")
                else:
                    print(f"      ❌ {api_test['name']}: Status {response.status}")
            except Exception as e:
                print(f"      ❌ {api_test['name']}: {e}")
    
    async def _generate_final_report(self):
        """Generate comprehensive test report"""
        
        self.test_results["test_end"] = datetime.now().isoformat()
        self.test_results["total_tests"] = self.test_results["tests_passed"] + self.test_results["tests_failed"]
        self.test_results["success_rate"] = (self.test_results["tests_passed"] / max(self.test_results["total_tests"], 1)) * 100
        
        # Save test report
        report_file = Path("data/test_results/archon_comprehensive_e2e_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📊 COMPREHENSIVE TEST RESULTS:")
        print(f"   Total Tests: {self.test_results['total_tests']}")
        print(f"   Passed: {self.test_results['tests_passed']}")
        print(f"   Failed: {self.test_results['tests_failed']}")
        print(f"   Success Rate: {self.test_results['success_rate']:.1f}%")
        print(f"   Report: {report_file}")
        print(f"   Screenshots: {self.screenshots_dir}")
        
        # Generate summary
        if self.test_results["success_rate"] > 80:
            print("🎊 OVERALL RESULT: EXCELLENT")
        elif self.test_results["success_rate"] > 60:
            print("✅ OVERALL RESULT: GOOD")
        elif self.test_results["success_rate"] > 40:
            print("⚠️ OVERALL RESULT: NEEDS ATTENTION")
        else:
            print("❌ OVERALL RESULT: REQUIRES FIXES")

async def main():
    """Main execution"""
    
    tester = ComprehensiveArchonTester()
    await tester.run_comprehensive_tests()
    
    print(f"\n📋 TEST COMPLETION SUMMARY:")
    print(f"   🎯 Endpoints tested: {len(tester.test_endpoints)}")
    print(f"   📸 Screenshots saved: {tester.screenshots_dir}")
    print(f"   📄 Test report: data/test_results/archon_comprehensive_e2e_report.json")
    print(f"   💡 Use this data to validate Archon functionality")

if __name__ == "__main__":
    asyncio.run(main())
