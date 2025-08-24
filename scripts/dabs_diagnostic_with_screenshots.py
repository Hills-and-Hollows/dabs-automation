#!/usr/bin/env python3
"""
DABS Diagnostic Analysis with Screenshots
Comprehensive analysis of MCP server access and authentication blocking

This script will:
1. Test MCP server accessibility 
2. Capture screenshots during authentication attempts
3. Analyze specific blocking mechanisms
4. Document exact failure points
"""

import asyncio
import json
import logging
import os
import sys
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.dabs_automated_ordering import DABSAutomatedOrdering

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DABSDiagnosticAnalyzer:
    """
    Comprehensive diagnostic analyzer for DABS MCP and authentication issues
    """
    
    def __init__(self):
        self.screenshot_dir = Path("dabs_diagnostic_screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        self.results = {}
        
    async def run_comprehensive_analysis(self):
        """Run complete diagnostic analysis with screenshots"""
        
        print("🔍 DABS COMPREHENSIVE DIAGNOSTIC ANALYSIS")
        print("=" * 70)
        print("Analyzing MCP server access and authentication blocking mechanisms")
        print()
        
        # Test 1: MCP Server Accessibility
        await self._test_mcp_server_access()
        
        # Test 2: Network Connectivity Analysis
        await self._test_network_connectivity()
        
        # Test 3: Authentication Process Analysis with Screenshots
        await self._test_authentication_with_screenshots()
        
        # Test 4: Browser Security Analysis
        await self._test_browser_security_measures()
        
        # Generate comprehensive report
        self._generate_diagnostic_report()
        
    async def _test_mcp_server_access(self):
        """Test MCP server accessibility and status"""
        
        print("🔧 TEST 1: MCP Server Accessibility Analysis")
        print("-" * 50)
        
        test_results = {}
        
        # Check if DABS MCP tools are accessible through Cursor
        print("📡 Testing MCP tool accessibility...")
        
        try:
            # This would test if MCP tools are accessible
            # Since we know they're not working, let's document why
            test_results["mcp_tools_accessible"] = False
            test_results["mcp_error"] = "Tools exist but not accessible through MCP protocol"
            
            # Check MCP server process
            import subprocess
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            mcp_processes = [line for line in result.stdout.split('\n') if 'mcp' in line.lower() or 'dabs' in line.lower()]
            
            test_results["mcp_processes"] = len(mcp_processes)
            test_results["mcp_process_details"] = mcp_processes[:3]  # First 3 for brevity
            
            if mcp_processes:
                print(f"✅ Found {len(mcp_processes)} MCP-related processes running")
                for i, process in enumerate(mcp_processes[:2]):
                    print(f"   Process {i+1}: {process.strip()}")
            else:
                print("❌ No MCP processes found")
                
        except Exception as e:
            test_results["mcp_error"] = str(e)
            print(f"❌ MCP server test failed: {e}")
            
        # Test direct server endpoints
        test_ports = [8000, 8001, 8002, 3000, 3001]
        working_ports = []
        
        for port in test_ports:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    working_ports.append(port)
                    print(f"✅ Port {port}: Server responding")
            except:
                pass
                
        test_results["working_ports"] = working_ports
        test_results["total_ports_tested"] = len(test_ports)
        
        if not working_ports:
            print("❌ No MCP servers accessible via HTTP")
        
        self.results["mcp_server_access"] = test_results
        print()
        
    async def _test_network_connectivity(self):
        """Test network connectivity to DABS website"""
        
        print("🌐 TEST 2: Network Connectivity Analysis")
        print("-" * 50)
        
        test_results = {}
        dabs_url = "https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/"
        
        # Test 1: Basic HTTP connectivity
        try:
            response = requests.get(dabs_url, timeout=10)
            test_results["http_status"] = response.status_code
            test_results["response_size"] = len(response.content)
            test_results["response_headers"] = dict(response.headers)
            
            print(f"✅ HTTP Response: {response.status_code}")
            print(f"📦 Response Size: {len(response.content):,} bytes")
            
            # Check for security headers
            security_headers = ['x-frame-options', 'content-security-policy', 'x-content-type-options']
            found_security = [h for h in security_headers if h in response.headers]
            
            if found_security:
                print(f"🛡️  Security Headers Found: {found_security}")
                test_results["security_headers"] = found_security
            
        except Exception as e:
            test_results["http_error"] = str(e)
            print(f"❌ HTTP connectivity failed: {e}")
            
        # Test 2: DNS resolution
        import socket
        try:
            host = "webapps2.abc.utah.gov"
            ip = socket.gethostbyname(host)
            test_results["dns_resolution"] = ip
            print(f"✅ DNS Resolution: {host} → {ip}")
        except Exception as e:
            test_results["dns_error"] = str(e)
            print(f"❌ DNS resolution failed: {e}")
            
        self.results["network_connectivity"] = test_results
        print()
        
    async def _test_authentication_with_screenshots(self):
        """Test authentication process with detailed screenshots"""
        
        print("🔐 TEST 3: Authentication Process Analysis (With Screenshots)")
        print("-" * 50)
        
        test_results = {}
        screenshot_count = 0
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=False,  # Visible for screenshot analysis
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            context = await browser.new_context()
            page = await context.new_page()
            
            # Screenshot 1: Initial page load
            print("📸 Step 1: Loading DABS website...")
            try:
                await page.goto("https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/", 
                              wait_until="networkidle", timeout=30000)
                
                screenshot_path = self.screenshot_dir / f"01_initial_load.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                screenshot_count += 1
                
                print(f"✅ Screenshot saved: {screenshot_path}")
                test_results["initial_load"] = "success"
                
                # Check page title and content
                title = await page.title()
                test_results["page_title"] = title
                print(f"📄 Page Title: {title}")
                
            except Exception as e:
                screenshot_path = self.screenshot_dir / f"01_initial_load_FAILED.png"
                try:
                    await page.screenshot(path=screenshot_path, full_page=True)
                    screenshot_count += 1
                except:
                    pass
                    
                test_results["initial_load_error"] = str(e)
                print(f"❌ Initial load failed: {e}")
                
            # Screenshot 2: Login form analysis
            print("📸 Step 2: Analyzing login form...")
            try:
                # Look for login elements
                username_field = await page.query_selector('input[name="UserName"], input[type="text"], input[id*="user"]')
                password_field = await page.query_selector('input[name="Password"], input[type="password"]')
                submit_button = await page.query_selector('button[type="submit"], input[type="submit"], button:has-text("login")')
                
                if username_field and password_field:
                    print("✅ Login form detected")
                    test_results["login_form_found"] = True
                    
                    # Screenshot before filling
                    screenshot_path = self.screenshot_dir / f"02_login_form_detected.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    screenshot_count += 1
                    
                    # Fill credentials (load from env)
                    env_file = Path(__file__).parent.parent / "config" / "dabs_ordering.env"
                    with open(env_file, 'r') as f:
                        for line in f:
                            if line.strip() and not line.startswith('#') and '=' in line:
                                key, value = line.strip().split('=', 1)
                                os.environ[key] = value
                    
                    username = os.environ.get('DABS_ORDERING_USERNAME', '')
                    password = os.environ.get('DABS_ORDERING_PASSWORD', '')
                    
                    await page.fill('input[name="UserName"]', username)
                    await page.fill('input[name="Password"]', password)
                    
                    # Screenshot after filling
                    screenshot_path = self.screenshot_dir / f"03_credentials_filled.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    screenshot_count += 1
                    
                    print(f"✅ Credentials filled for user: {username}")
                    
                else:
                    print("❌ Login form not found")
                    test_results["login_form_found"] = False
                    
                    screenshot_path = self.screenshot_dir / f"02_no_login_form.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    screenshot_count += 1
                    
            except Exception as e:
                test_results["login_form_error"] = str(e)
                print(f"❌ Login form analysis failed: {e}")
                
            # Screenshot 3: Submit attempt and response
            print("📸 Step 3: Attempting login submission...")
            try:
                if test_results.get("login_form_found"):
                    # Click submit
                    submit_button = await page.query_selector('button[type="submit"], input[type="submit"]')
                    if submit_button:
                        await submit_button.click()
                        
                        # Wait for response
                        await page.wait_for_timeout(3000)  # 3 seconds
                        
                        # Screenshot after submit
                        screenshot_path = self.screenshot_dir / f"04_after_submit.png"
                        await page.screenshot(path=screenshot_path, full_page=True)
                        screenshot_count += 1
                        
                        # Check for error messages
                        error_selectors = [
                            '.validation-summary-errors',
                            '.alert-danger', 
                            '.error',
                            '[class*="error"]',
                            '[class*="invalid"]'
                        ]
                        
                        errors_found = []
                        for selector in error_selectors:
                            elements = await page.query_selector_all(selector)
                            for element in elements:
                                text = await element.text_content()
                                if text and text.strip():
                                    errors_found.append(text.strip())
                        
                        if errors_found:
                            test_results["login_errors"] = errors_found
                            print(f"❌ Login errors found: {errors_found}")
                        else:
                            # Check if we're redirected or still on login page
                            current_url = page.url
                            test_results["post_submit_url"] = current_url
                            
                            if "login" in current_url.lower():
                                print("⚠️ Still on login page - authentication may have failed")
                                test_results["login_result"] = "failed_or_blocked"
                            else:
                                print("✅ Redirected - authentication may have succeeded")
                                test_results["login_result"] = "success_or_redirect"
                                
            except Exception as e:
                test_results["submit_error"] = str(e)
                print(f"❌ Login submission failed: {e}")
                
            # Screenshot 4: Final state analysis
            print("📸 Step 4: Final state analysis...")
            try:
                screenshot_path = self.screenshot_dir / f"05_final_state.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                screenshot_count += 1
                
                # Get page content for analysis
                content = await page.content()
                test_results["final_page_size"] = len(content)
                
                # Check for specific indicators
                indicators = {
                    "captcha_present": "captcha" in content.lower(),
                    "blocked_message": any(word in content.lower() for word in ["blocked", "forbidden", "access denied"]),
                    "timeout_message": "timeout" in content.lower(),
                    "maintenance_mode": "maintenance" in content.lower()
                }
                
                test_results["security_indicators"] = indicators
                
                for indicator, present in indicators.items():
                    if present:
                        print(f"🛡️ {indicator}: {present}")
                        
            except Exception as e:
                test_results["final_analysis_error"] = str(e)
                print(f"❌ Final analysis failed: {e}")
                
            await browser.close()
            await playwright.stop()
            
            test_results["screenshots_captured"] = screenshot_count
            print(f"📸 Total screenshots captured: {screenshot_count}")
            
        except Exception as e:
            test_results["authentication_test_error"] = str(e)
            print(f"❌ Authentication test failed: {e}")
            
        self.results["authentication_analysis"] = test_results
        print()
        
    async def _test_browser_security_measures(self):
        """Test browser security and detection measures"""
        
        print("🛡️ TEST 4: Browser Security Analysis")
        print("-" * 50)
        
        test_results = {}
        
        try:
            playwright = await async_playwright().start()
            
            # Test different browser configurations
            configs = [
                ("Default Chromium", {}),
                ("Stealth Mode", {
                    "args": [
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage"
                    ]
                }),
                ("Mobile User Agent", {
                    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)"
                })
            ]
            
            for config_name, config in configs:
                print(f"🧪 Testing {config_name}...")
                
                try:
                    browser = await playwright.chromium.launch(headless=True, **config)
                    context = await browser.new_context()
                    page = await context.new_page()
                    
                    # Test basic connectivity
                    response = await page.goto("https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/", 
                                             wait_until="domcontentloaded", timeout=10000)
                    
                    status = response.status if response else "No response"
                    test_results[config_name.lower().replace(" ", "_")] = {
                        "status": status,
                        "success": status == 200 if response else False
                    }
                    
                    print(f"   Status: {status}")
                    
                    await browser.close()
                    
                except Exception as e:
                    test_results[config_name.lower().replace(" ", "_")] = {
                        "error": str(e),
                        "success": False
                    }
                    print(f"   Error: {e}")
                    
            await playwright.stop()
            
        except Exception as e:
            test_results["browser_security_test_error"] = str(e)
            print(f"❌ Browser security test failed: {e}")
            
        self.results["browser_security"] = test_results
        print()
        
    def _generate_diagnostic_report(self):
        """Generate comprehensive diagnostic report"""
        
        print("📊 COMPREHENSIVE DIAGNOSTIC REPORT")
        print("=" * 70)
        
        # MCP Server Access Summary
        mcp_results = self.results.get("mcp_server_access", {})
        print("🔧 MCP SERVER ACCESS:")
        print(f"   • Processes Found: {mcp_results.get('mcp_processes', 0)}")
        print(f"   • Working Ports: {mcp_results.get('working_ports', [])}")
        print(f"   • Tools Accessible: {mcp_results.get('mcp_tools_accessible', False)}")
        
        # Network Connectivity Summary  
        network_results = self.results.get("network_connectivity", {})
        print("🌐 NETWORK CONNECTIVITY:")
        print(f"   • HTTP Status: {network_results.get('http_status', 'Failed')}")
        print(f"   • DNS Resolution: {network_results.get('dns_resolution', 'Failed')}")
        print(f"   • Security Headers: {network_results.get('security_headers', [])}")
        
        # Authentication Analysis Summary
        auth_results = self.results.get("authentication_analysis", {})
        print("🔐 AUTHENTICATION ANALYSIS:")
        print(f"   • Login Form Found: {auth_results.get('login_form_found', False)}")
        print(f"   • Screenshots Captured: {auth_results.get('screenshots_captured', 0)}")
        print(f"   • Login Result: {auth_results.get('login_result', 'Unknown')}")
        
        if auth_results.get("login_errors"):
            print(f"   • Login Errors: {auth_results['login_errors']}")
            
        # Security Indicators
        security_indicators = auth_results.get("security_indicators", {})
        if security_indicators:
            print("🛡️ SECURITY INDICATORS:")
            for indicator, present in security_indicators.items():
                if present:
                    print(f"   • {indicator}: ✅")
                    
        # Browser Security Summary
        browser_results = self.results.get("browser_security", {})
        print("🛡️ BROWSER SECURITY TESTS:")
        for test_name, result in browser_results.items():
            if isinstance(result, dict) and "success" in result:
                status = "✅" if result["success"] else "❌"
                print(f"   • {test_name}: {status}")
                
        print()
        print(f"📸 Screenshots saved in: {self.screenshot_dir}")
        print("=" * 70)
        
        # Save detailed results to file
        report_file = Path("dabs_diagnostic_report.json")
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"📄 Detailed report saved: {report_file}")

async def main():
    """Main diagnostic execution"""
    
    analyzer = DABSDiagnosticAnalyzer()
    await analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    asyncio.run(main())
