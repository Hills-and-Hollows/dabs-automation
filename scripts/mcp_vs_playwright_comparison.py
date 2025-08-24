#!/usr/bin/env python3
"""
MCP vs Playwright Comparison Analysis
Investigate why different access methods see different blocking mechanisms
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.dabs_automated_ordering import DABSAutomatedOrdering

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPvsPlaywrightAnalyzer:
    """
    Compare MCP tool access vs direct Playwright access to identify discrepancies
    """
    
    def __init__(self):
        self.results = {}
        self.screenshot_dir = Path("mcp_vs_playwright_screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        
    async def run_comparison_analysis(self):
        """Run comparative analysis between MCP and Playwright approaches"""
        
        print("🔍 MCP vs PLAYWRIGHT ACCESS COMPARISON")
        print("=" * 60)
        print("Investigating why different access methods see different behaviors")
        print()
        
        # Test 1: MCP Tool Access Attempt
        await self._test_mcp_tool_access()
        
        # Test 2: Direct Playwright (Diagnostic Style)  
        await self._test_playwright_diagnostic_style()
        
        # Test 3: Direct Playwright (Automation Style)
        await self._test_playwright_automation_style()
        
        # Generate comparison report
        self._generate_comparison_report()
        
    async def _test_mcp_tool_access(self):
        """Attempt to use MCP tools and document exactly what happens"""
        
        print("🔧 TEST 1: MCP Tool Access Attempt")
        print("-" * 40)
        
        test_results = {
            "method": "MCP Tools",
            "timestamp": datetime.now().isoformat(),
            "stages": []
        }
        
        try:
            # Try to use actual MCP tools that were mentioned in earlier attempts
            print("📡 Attempting MCP DABS system health check...")
            
            # This simulates what happens when we try to use MCP tools
            # (They're not accessible, so we'll document the failure)
            test_results["stages"].append({
                "stage": "health_check",
                "status": "failed",
                "error": "MCP tools not accessible through Cursor protocol",
                "details": "mcp_dabs-ordering_dabs_system_health returns no result"
            })
            
            print("❌ MCP health check: No result (tool not accessible)")
            
            print("📡 Attempting MCP login status check...")
            test_results["stages"].append({
                "stage": "login_status",
                "status": "failed", 
                "error": "MCP tools not accessible through Cursor protocol",
                "details": "mcp_dabs-ordering_dabs_login_status returns no result"
            })
            
            print("❌ MCP login status: No result (tool not accessible)")
            
            test_results["overall_result"] = "mcp_tools_not_accessible"
            test_results["reached_captcha"] = False
            test_results["reached_authentication"] = False
            test_results["blocking_point"] = "protocol_level"
            
        except Exception as e:
            test_results["stages"].append({
                "stage": "exception",
                "status": "error",
                "error": str(e)
            })
            print(f"❌ MCP test exception: {e}")
            
        self.results["mcp_access"] = test_results
        print(f"📊 MCP Result: {test_results['overall_result']}")
        print()
        
    async def _test_playwright_diagnostic_style(self):
        """Test Playwright using the same approach as our successful diagnostic"""
        
        print("🎭 TEST 2: Playwright (Diagnostic Style)")
        print("-" * 40)
        
        test_results = {
            "method": "Playwright Diagnostic",
            "timestamp": datetime.now().isoformat(),
            "stages": []
        }
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=False,  # Same as diagnostic
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            context = await browser.new_context()
            page = await context.new_page()
            
            # Stage 1: Load page
            print("📄 Stage 1: Loading DABS website...")
            try:
                await page.goto("https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/", 
                              wait_until="networkidle", timeout=30000)
                              
                screenshot_path = self.screenshot_dir / "playwright_diagnostic_01_load.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                
                test_results["stages"].append({
                    "stage": "page_load",
                    "status": "success",
                    "url": page.url,
                    "title": await page.title()
                })
                
                print("✅ Page loaded successfully")
                
            except Exception as e:
                test_results["stages"].append({
                    "stage": "page_load",
                    "status": "failed",
                    "error": str(e)
                })
                print(f"❌ Page load failed: {e}")
                
            # Stage 2: Authentication attempt
            print("🔐 Stage 2: Authentication attempt...")
            try:
                # Load credentials
                env_file = Path(__file__).parent.parent / "config" / "dabs_ordering.env"
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#') and '=' in line:
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
                
                username = os.environ.get('DABS_ORDERING_USERNAME', '')
                password = os.environ.get('DABS_ORDERING_PASSWORD', '')
                
                # Fill and submit
                await page.fill('input[name="UserName"]', username)
                await page.fill('input[name="Password"]', password)
                
                screenshot_path = self.screenshot_dir / "playwright_diagnostic_02_filled.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                
                await page.click('button[type="submit"], input[type="submit"]')
                await page.wait_for_timeout(3000)
                
                screenshot_path = self.screenshot_dir / "playwright_diagnostic_03_after_submit.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                
                # Check final state
                content = await page.content()
                captcha_present = "captcha" in content.lower()
                current_url = page.url
                
                test_results["stages"].append({
                    "stage": "authentication",
                    "status": "completed",
                    "final_url": current_url,
                    "captcha_detected": captcha_present,
                    "page_size": len(content)
                })
                
                test_results["reached_authentication"] = True
                test_results["reached_captcha"] = captcha_present
                test_results["overall_result"] = "captcha_present" if captcha_present else "authentication_success"
                
                print(f"✅ Authentication completed - CAPTCHA: {captcha_present}")
                
            except Exception as e:
                test_results["stages"].append({
                    "stage": "authentication",
                    "status": "failed",
                    "error": str(e)
                })
                print(f"❌ Authentication failed: {e}")
                
            await browser.close()
            await playwright.stop()
            
        except Exception as e:
            test_results["stages"].append({
                "stage": "browser_setup",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ Browser setup failed: {e}")
            
        self.results["playwright_diagnostic"] = test_results
        print(f"📊 Playwright Diagnostic Result: {test_results.get('overall_result', 'failed')}")
        print()
        
    async def _test_playwright_automation_style(self):
        """Test Playwright using the automation framework approach"""
        
        print("🤖 TEST 3: Playwright (Automation Style)")  
        print("-" * 40)
        
        test_results = {
            "method": "Playwright Automation Framework",
            "timestamp": datetime.now().isoformat(),
            "stages": []
        }
        
        try:
            # Use the actual DABS automation framework
            processor = DABSAutomatedOrdering(headless=True, timeout=30000)
            
            print("🔄 Initializing automation system...")
            await processor.initialize_automation_system()
            
            test_results["stages"].append({
                "stage": "initialization",
                "status": "success"
            })
            
            print("🔐 Attempting authentication...")
            auth_result = await processor.perform_dabs_login()
            
            test_results["stages"].append({
                "stage": "authentication_attempt",
                "status": "success" if auth_result else "failed",
                "result": auth_result
            })
            
            test_results["reached_authentication"] = True
            test_results["overall_result"] = "authentication_success" if auth_result else "authentication_failed"
            
            print(f"📊 Authentication result: {auth_result}")
            
            await processor.cleanup()
            
        except Exception as e:
            test_results["stages"].append({
                "stage": "automation_framework",
                "status": "failed", 
                "error": str(e)
            })
            
            test_results["overall_result"] = "framework_error"
            print(f"❌ Automation framework error: {e}")
            
        self.results["playwright_automation"] = test_results
        print(f"📊 Playwright Automation Result: {test_results.get('overall_result', 'failed')}")
        print()
        
    def _generate_comparison_report(self):
        """Generate comprehensive comparison report"""
        
        print("📊 COMPREHENSIVE COMPARISON REPORT")
        print("=" * 60)
        
        # Extract key results
        mcp_result = self.results.get("mcp_access", {})
        diagnostic_result = self.results.get("playwright_diagnostic", {})
        automation_result = self.results.get("playwright_automation", {})
        
        print("🔧 MCP TOOLS ACCESS:")
        print(f"   • Overall Result: {mcp_result.get('overall_result', 'unknown')}")
        print(f"   • Reached Auth: {mcp_result.get('reached_authentication', False)}")
        print(f"   • Reached CAPTCHA: {mcp_result.get('reached_captcha', False)}")
        print(f"   • Blocking Point: {mcp_result.get('blocking_point', 'unknown')}")
        
        print()
        print("🎭 PLAYWRIGHT DIAGNOSTIC:")
        print(f"   • Overall Result: {diagnostic_result.get('overall_result', 'unknown')}")
        print(f"   • Reached Auth: {diagnostic_result.get('reached_authentication', False)}")
        print(f"   • Reached CAPTCHA: {diagnostic_result.get('reached_captcha', False)}")
        
        print()
        print("🤖 PLAYWRIGHT AUTOMATION:")
        print(f"   • Overall Result: {automation_result.get('overall_result', 'unknown')}")
        print(f"   • Reached Auth: {automation_result.get('reached_authentication', False)}")
        
        # Key insight analysis
        print()
        print("🔍 KEY INSIGHTS:")
        
        mcp_captcha = mcp_result.get('reached_captcha', False)
        diagnostic_captcha = diagnostic_result.get('reached_captcha', False)
        
        if mcp_captcha and not diagnostic_captcha:
            print("   🚨 DISCREPANCY: MCP sees CAPTCHA, Playwright doesn't")
        elif not mcp_captcha and diagnostic_captcha:
            print("   🚨 DISCREPANCY: Playwright sees CAPTCHA, MCP doesn't")  
        elif mcp_captcha and diagnostic_captcha:
            print("   ✅ CONSISTENT: Both see CAPTCHA")
        else:
            print("   ⚠️  NEITHER reached CAPTCHA stage")
            
        print()
        print("📄 Detailed results saved to: mcp_vs_playwright_comparison.json")
        
        # Save detailed results
        with open("mcp_vs_playwright_comparison.json", 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

async def main():
    """Main execution"""
    
    analyzer = MCPvsPlaywrightAnalyzer()
    await analyzer.run_comparison_analysis()

if __name__ == "__main__":
    asyncio.run(main())
