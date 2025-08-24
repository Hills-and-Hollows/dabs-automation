#!/usr/bin/env python3
"""
End-to-End Archon MCP Connection Test
Validates that all Archon services are running on correct ports and accessible
"""

import asyncio
import sys
import json
from pathlib import Path
from playwright.async_api import async_playwright
import aiohttp
import time

class ArchonConnectionTest:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {
            "timestamp": int(time.time()),
            "tests_passed": 0,
            "tests_failed": 0,
            "services": {},
            "overall_status": "UNKNOWN"
        }
        
        # Expected services with correct DABS ports
        self.services = {
            "archon_ui": {
                "name": "Archon UI",
                "url": "http://localhost:3837",
                "type": "web_ui",
                "expected_content": ["Archon", "Task", "Knowledge"]
            },
            "archon_server": {
                "name": "Archon Server", 
                "url": "http://localhost:8281/health",
                "type": "api",
                "expected_response": {"status": "healthy"}
            },
            "archon_mcp": {
                "name": "Archon MCP",
                "url": "http://localhost:8151/health", 
                "type": "mcp",
                "expected_response": {"status": "healthy"}
            },
            "archon_agents": {
                "name": "Archon Agents",
                "url": "http://localhost:8152/health",
                "type": "api", 
                "expected_response": {"status": "healthy"}
            }
        }

    async def test_http_service(self, service_id, service_config):
        """Test HTTP/API service connectivity"""
        print(f"🧪 Testing {service_config['name']} at {service_config['url']}")
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(service_config['url']) as response:
                    if response.status == 200:
                        if service_config['type'] == 'api':
                            # Test JSON API response
                            data = await response.json()
                            if 'status' in data and data['status'] == 'healthy':
                                print(f"✅ {service_config['name']} - Healthy API response")
                                return True, f"API healthy with status: {data.get('status')}"
                            else:
                                print(f"⚠️  {service_config['name']} - API responded but not healthy")
                                return False, f"API responded but status: {data}"
                        else:
                            print(f"✅ {service_config['name']} - HTTP 200 OK")
                            return True, f"HTTP 200 OK"
                    else:
                        print(f"❌ {service_config['name']} - HTTP {response.status}")
                        return False, f"HTTP {response.status}"
                        
        except asyncio.TimeoutError:
            print(f"❌ {service_config['name']} - Connection timeout")
            return False, "Connection timeout"
        except Exception as e:
            print(f"❌ {service_config['name']} - Error: {str(e)}")
            return False, str(e)

    async def test_web_ui(self, service_id, service_config):
        """Test web UI using Playwright"""
        print(f"🧪 Testing {service_config['name']} UI at {service_config['url']}")
        
        try:
            async with async_playwright() as p:
                # Use Chromium in headless mode
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Navigate to the service
                response = await page.goto(service_config['url'], timeout=15000)
                
                if response.status == 200:
                    # Wait for content to load
                    await page.wait_for_timeout(3000)
                    
                    # Get page content
                    page_content = await page.content()
                    title = await page.title()
                    
                    # Check for expected content
                    content_found = []
                    for expected in service_config.get('expected_content', []):
                        if expected.lower() in page_content.lower():
                            content_found.append(expected)
                    
                    await browser.close()
                    
                    if content_found:
                        print(f"✅ {service_config['name']} - UI loaded successfully")
                        print(f"   📄 Title: {title}")
                        print(f"   📋 Found content: {', '.join(content_found)}")
                        return True, f"UI loaded with title: {title}"
                    else:
                        print(f"⚠️  {service_config['name']} - UI loaded but missing expected content")
                        return False, "UI loaded but missing expected content"
                else:
                    await browser.close()
                    print(f"❌ {service_config['name']} - HTTP {response.status}")
                    return False, f"HTTP {response.status}"
                    
        except Exception as e:
            print(f"❌ {service_config['name']} - Playwright error: {str(e)}")
            return False, f"Playwright error: {str(e)}"

    async def test_mcp_endpoint(self, service_id, service_config):
        """Test MCP-specific endpoint"""
        print(f"🧪 Testing MCP Server at {service_config['url']}")
        
        # First test basic health endpoint
        health_passed, health_message = await self.test_http_service(service_id, service_config)
        
        if health_passed:
            # Test MCP-specific endpoint if health passed
            try:
                mcp_info_url = service_config['url'].replace('/health', '/info')
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(mcp_info_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"✅ MCP Server - Additional info endpoint accessible")
                            print(f"   📊 MCP Info: {json.dumps(data, indent=2)[:200]}...")
                            return True, f"MCP healthy + info accessible: {health_message}"
                        else:
                            print(f"✅ MCP Server - Health OK, info endpoint not required")
                            return True, health_message
            except:
                # Info endpoint not required for MCP to be functional
                print(f"✅ MCP Server - Health OK, info endpoint optional")
                return True, health_message
        else:
            return health_passed, health_message

    async def run_all_tests(self):
        """Run all service tests"""
        print("🚀 STARTING ARCHON MCP CONNECTION TESTS")
        print("=" * 50)
        
        for service_id, service_config in self.services.items():
            print(f"\n📋 Testing {service_config['name']}")
            print("-" * 30)
            
            try:
                if service_config['type'] == 'web_ui':
                    success, message = await self.test_web_ui(service_id, service_config)
                elif service_config['type'] == 'mcp':
                    success, message = await self.test_mcp_endpoint(service_id, service_config)
                else:
                    success, message = await self.test_http_service(service_id, service_config)
                
                self.results['services'][service_id] = {
                    "name": service_config['name'],
                    "url": service_config['url'],
                    "success": success,
                    "message": message,
                    "timestamp": int(time.time())
                }
                
                if success:
                    self.results['tests_passed'] += 1
                else:
                    self.results['tests_failed'] += 1
                    
            except Exception as e:
                print(f"❌ {service_config['name']} - Unexpected error: {str(e)}")
                self.results['services'][service_id] = {
                    "name": service_config['name'],
                    "url": service_config['url'], 
                    "success": False,
                    "message": f"Unexpected error: {str(e)}",
                    "timestamp": int(time.time())
                }
                self.results['tests_failed'] += 1
        
        # Determine overall status
        total_services = len(self.services)
        if self.results['tests_passed'] == total_services:
            self.results['overall_status'] = "ALL_PASS"
        elif self.results['tests_passed'] >= total_services * 0.75:  # 75% threshold
            self.results['overall_status'] = "MOSTLY_PASS"
        elif self.results['tests_passed'] > 0:
            self.results['overall_status'] = "PARTIAL_PASS"  
        else:
            self.results['overall_status'] = "ALL_FAIL"

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 50)
        print("🔍 ARCHON MCP CONNECTION TEST RESULTS")
        print("=" * 50)
        
        status_icon = {
            "ALL_PASS": "✅",
            "MOSTLY_PASS": "⚠️",
            "PARTIAL_PASS": "⚠️", 
            "ALL_FAIL": "❌"
        }
        
        print(f"Overall Status: {status_icon.get(self.results['overall_status'], '❓')} {self.results['overall_status']}")
        print(f"Tests Passed: {self.results['tests_passed']}/{len(self.services)}")
        print(f"Tests Failed: {self.results['tests_failed']}/{len(self.services)}")
        
        print(f"\n📊 Service Details:")
        for service_id, result in self.results['services'].items():
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['name']}: {result['message']}")
        
        if self.results['overall_status'] == "ALL_PASS":
            print(f"\n🎉 SUCCESS! All Archon services are running correctly!")
            print(f"🔗 Cursor can now connect to: http://localhost:8151/health")
            print(f"🚀 Ready for Archon-first development workflow!")
        elif self.results['overall_status'] in ["MOSTLY_PASS", "PARTIAL_PASS"]:
            print(f"\n⚠️  PARTIAL SUCCESS! Some services may still be starting up.")
            print(f"   Wait a few more minutes and test again.")
        else:
            print(f"\n❌ FAILED! Services are not accessible.")
            print(f"   Check Docker containers and try restarting.")

    async def save_results(self):
        """Save results to file"""
        results_file = self.project_root / "test_results" / "archon_connection_test.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")

async def main():
    """Main test function"""
    tester = ArchonConnectionTest()
    
    try:
        await tester.run_all_tests()
        tester.print_summary()
        await tester.save_results()
        
        # Return appropriate exit code
        if tester.results['overall_status'] == "ALL_PASS":
            return 0
        elif tester.results['overall_status'] in ["MOSTLY_PASS", "PARTIAL_PASS"]:
            return 1  # Partial success
        else:
            return 2  # Failure
            
    except Exception as e:
        print(f"❌ Test execution error: {str(e)}")
        return 3

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
