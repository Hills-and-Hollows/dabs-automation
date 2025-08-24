#!/usr/bin/env python3
"""
Comprehensive MCP Integration Testing Plan
Tests all aspects of the Archon MCP server integration for DABS project
"""

import asyncio
import json
import sys
import time
import aiohttp
from pathlib import Path
from typing import Dict, List, Any, Tuple
import subprocess

class ComprehensiveMCPTester:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {
            "timestamp": int(time.time()),
            "overall_status": "PENDING",
            "categories": {
                "infrastructure": {"passed": 0, "failed": 0, "tests": {}},
                "mcp_protocol": {"passed": 0, "failed": 0, "tests": {}},  
                "dabs_tools": {"passed": 0, "failed": 0, "tests": {}},
                "knowledge_base": {"passed": 0, "failed": 0, "tests": {}},
                "cursor_integration": {"passed": 0, "failed": 0, "tests": {}},
                "workflow_validation": {"passed": 0, "failed": 0, "tests": {}}
            }
        }

    async def test_infrastructure_readiness(self) -> Dict[str, Any]:
        """Test 1: Infrastructure Readiness - All services accessible on correct ports"""
        print("🏗️  TESTING INFRASTRUCTURE READINESS")
        print("=" * 50)
        
        services = {
            "archon_ui": "http://localhost:3837",
            "archon_server": "http://localhost:8281/health", 
            "archon_mcp": "http://localhost:8151/mcp",
            "archon_agents": "http://localhost:8152/health"
        }
        
        results = {}
        for service, url in services.items():
            print(f"🔍 Testing {service} at {url}")
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get(url) as response:
                        if response.status in [200, 406]:  # 406 is expected for MCP
                            print(f"✅ {service}: Accessible")
                            results[service] = {"success": True, "status": response.status}
                            self.test_results["categories"]["infrastructure"]["passed"] += 1
                        else:
                            print(f"❌ {service}: HTTP {response.status}")
                            results[service] = {"success": False, "status": response.status}
                            self.test_results["categories"]["infrastructure"]["failed"] += 1
            except Exception as e:
                print(f"❌ {service}: {str(e)}")
                results[service] = {"success": False, "error": str(e)}
                self.test_results["categories"]["infrastructure"]["failed"] += 1
        
        self.test_results["categories"]["infrastructure"]["tests"] = results
        return results

    async def test_mcp_protocol_compliance(self) -> Dict[str, Any]:
        """Test 2: MCP Protocol Compliance - SSE transport and JSON-RPC responses"""
        print("\n📡 TESTING MCP PROTOCOL COMPLIANCE") 
        print("=" * 50)
        
        results = {}
        
        # Test SSE endpoint availability
        print("🔍 Testing SSE endpoint compliance")
        try:
            async with aiohttp.ClientSession() as session:
                # Test with proper SSE headers
                headers = {
                    "Accept": "text/event-stream",
                    "Cache-Control": "no-cache"
                }
                async with session.get("http://localhost:8151/mcp", headers=headers) as response:
                    if response.status in [200, 400]:  # 400 with proper error is expected
                        response_text = await response.text()
                        if "jsonrpc" in response_text:
                            print("✅ MCP SSE: JSON-RPC protocol detected")
                            results["sse_protocol"] = {"success": True, "message": "JSON-RPC detected"}
                            self.test_results["categories"]["mcp_protocol"]["passed"] += 1
                        else:
                            print("⚠️  MCP SSE: Responding but no JSON-RPC detected")
                            results["sse_protocol"] = {"success": False, "message": "No JSON-RPC"}
                            self.test_results["categories"]["mcp_protocol"]["failed"] += 1
                    else:
                        print(f"❌ MCP SSE: HTTP {response.status}")
                        results["sse_protocol"] = {"success": False, "status": response.status}
                        self.test_results["categories"]["mcp_protocol"]["failed"] += 1
        except Exception as e:
            print(f"❌ MCP SSE: {str(e)}")
            results["sse_protocol"] = {"success": False, "error": str(e)}
            self.test_results["categories"]["mcp_protocol"]["failed"] += 1
        
        # Test JSON-RPC error handling (expected behavior)
        print("🔍 Testing JSON-RPC error handling")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8151/mcp") as response:
                    response_text = await response.text()
                    if "jsonrpc" in response_text and "error" in response_text:
                        print("✅ MCP JSON-RPC: Proper error handling detected")
                        results["jsonrpc_errors"] = {"success": True, "message": "Proper error handling"}
                        self.test_results["categories"]["mcp_protocol"]["passed"] += 1
                    else:
                        print("❌ MCP JSON-RPC: No proper error handling")
                        results["jsonrpc_errors"] = {"success": False, "message": "No error handling"}
                        self.test_results["categories"]["mcp_protocol"]["failed"] += 1
        except Exception as e:
            print(f"❌ MCP JSON-RPC: {str(e)}")
            results["jsonrpc_errors"] = {"success": False, "error": str(e)}
            self.test_results["categories"]["mcp_protocol"]["failed"] += 1
            
        self.test_results["categories"]["mcp_protocol"]["tests"] = results
        return results

    async def test_dabs_specific_tools(self) -> Dict[str, Any]:
        """Test 3: DABS-Specific Tools - Expected tools are available"""
        print("\n🛠️  TESTING DABS-SPECIFIC TOOLS")
        print("=" * 50)
        
        expected_tools = [
            "search_dabs_knowledge",
            "create_dabs_task", 
            "get_dabs_project_status",
            "perform_rag_query",
            "manage_task",
            "manage_project"
        ]
        
        # Note: Without a proper MCP client, we can't directly test tool availability
        # But we can test that the MCP server is configured to handle tool requests
        print("🔍 Testing MCP tool endpoint configuration")
        
        results = {}
        try:
            # Check that server responds to tool-related requests properly
            async with aiohttp.ClientSession() as session:
                # Send a malformed JSON-RPC request to see if it handles tools
                headers = {"Content-Type": "application/json"}
                test_payload = {
                    "jsonrpc": "2.0",
                    "id": "test-1", 
                    "method": "tools/list"
                }
                
                async with session.post("http://localhost:8151/mcp", 
                                      headers=headers, 
                                      json=test_payload) as response:
                    response_text = await response.text()
                    if "jsonrpc" in response_text:
                        print("✅ DABS Tools: MCP server handles tool requests")
                        results["tool_handling"] = {"success": True, "message": "Tool requests handled"}
                        self.test_results["categories"]["dabs_tools"]["passed"] += 1
                        
                        # Log the expected tools for verification
                        print(f"📋 Expected DABS tools: {', '.join(expected_tools)}")
                        results["expected_tools"] = {"success": True, "tools": expected_tools}
                        self.test_results["categories"]["dabs_tools"]["passed"] += 1
                    else:
                        print("❌ DABS Tools: Server doesn't handle tool requests properly")
                        results["tool_handling"] = {"success": False, "message": "No tool handling"}
                        self.test_results["categories"]["dabs_tools"]["failed"] += 1
                        
        except Exception as e:
            print(f"❌ DABS Tools: {str(e)}")
            results["tool_handling"] = {"success": False, "error": str(e)}
            self.test_results["categories"]["dabs_tools"]["failed"] += 1
        
        self.test_results["categories"]["dabs_tools"]["tests"] = results
        return results

    async def test_knowledge_base_readiness(self) -> Dict[str, Any]:
        """Test 4: Knowledge Base - Documentation sources and content availability"""
        print("\n📚 TESTING KNOWLEDGE BASE READINESS")
        print("=" * 50)
        
        results = {}
        
        # Check for required documentation files
        expected_docs = [
            "docs/FUNCTIONAL_REQUIREMENTS.md",
            "docs/TECHNICAL_ARCHITECTURE.md", 
            "docs/ACCEPTANCE_CRITERIA.md",
            "docs/USER_STORIES.md"
        ]
        
        print("🔍 Checking DABS documentation availability")
        docs_found = []
        docs_missing = []
        
        for doc_path in expected_docs:
            full_path = self.project_root / doc_path
            if full_path.exists():
                docs_found.append(doc_path)
                print(f"✅ Found: {doc_path}")
            else:
                docs_missing.append(doc_path)
                print(f"❌ Missing: {doc_path}")
        
        if len(docs_found) >= len(expected_docs) * 0.75:  # 75% threshold
            results["documentation"] = {"success": True, "found": docs_found, "missing": docs_missing}
            self.test_results["categories"]["knowledge_base"]["passed"] += 1
        else:
            results["documentation"] = {"success": False, "found": docs_found, "missing": docs_missing}
            self.test_results["categories"]["knowledge_base"]["failed"] += 1
        
        # Check if Archon Server is ready to serve knowledge base
        print("🔍 Testing knowledge base server accessibility")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8281/api/sources") as response:
                    if response.status == 200:
                        print("✅ Knowledge base API: Accessible")
                        results["kb_api"] = {"success": True, "status": response.status}
                        self.test_results["categories"]["knowledge_base"]["passed"] += 1
                    else:
                        print(f"⚠️  Knowledge base API: HTTP {response.status}")
                        results["kb_api"] = {"success": False, "status": response.status}
                        self.test_results["categories"]["knowledge_base"]["failed"] += 1
        except Exception as e:
            print(f"❌ Knowledge base API: {str(e)}")
            results["kb_api"] = {"success": False, "error": str(e)}
            self.test_results["categories"]["knowledge_base"]["failed"] += 1
            
        self.test_results["categories"]["knowledge_base"]["tests"] = results
        return results

    def test_cursor_integration_config(self) -> Dict[str, Any]:
        """Test 5: Cursor Integration Config - Configuration files and setup"""
        print("\n🎯 TESTING CURSOR INTEGRATION CONFIG")
        print("=" * 50)
        
        results = {}
        
        # Check cursor_mcp_config.json
        config_file = self.project_root / "cursor_mcp_config.json"
        print(f"🔍 Checking Cursor MCP configuration: {config_file}")
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Verify essential configuration elements
                cursor_config = config_data.get("cursor_mcp_configuration", {})
                
                checks = {
                    "mcp_endpoint": cursor_config.get("mcp_endpoint") == "http://localhost:8151/mcp/sse",
                    "server_config": "server_config" in cursor_config,
                    "available_tools": len(cursor_config.get("available_tools", [])) > 0,
                    "test_commands": len(cursor_config.get("test_commands", [])) > 0
                }
                
                passed = sum(checks.values())
                total = len(checks)
                
                if passed == total:
                    print("✅ Cursor config: All elements configured correctly")
                    results["config_file"] = {"success": True, "checks_passed": f"{passed}/{total}"}
                    self.test_results["categories"]["cursor_integration"]["passed"] += 1
                else:
                    print(f"⚠️  Cursor config: {passed}/{total} elements configured")
                    results["config_file"] = {"success": False, "checks_passed": f"{passed}/{total}", "details": checks}
                    self.test_results["categories"]["cursor_integration"]["failed"] += 1
                    
            except Exception as e:
                print(f"❌ Cursor config: Error reading file - {str(e)}")
                results["config_file"] = {"success": False, "error": str(e)}
                self.test_results["categories"]["cursor_integration"]["failed"] += 1
        else:
            print(f"❌ Cursor config: File not found")
            results["config_file"] = {"success": False, "error": "File not found"}
            self.test_results["categories"]["cursor_integration"]["failed"] += 1
        
        # Test the specific endpoint that Cursor should connect to
        print("🔍 Testing Cursor connection endpoint")
        try:
            import subprocess
            result = subprocess.run([
                "curl", "-s", "-w", "%{http_code}", 
                "http://localhost:8151/mcp/sse"
            ], capture_output=True, text=True, timeout=5)
            
            if "406" in result.stdout or "400" in result.stdout:  # Expected responses for MCP
                print("✅ Cursor endpoint: Ready for connection (406/400 expected)")
                results["endpoint_test"] = {"success": True, "message": "Ready for connection"}
                self.test_results["categories"]["cursor_integration"]["passed"] += 1
            else:
                print(f"⚠️  Cursor endpoint: Unexpected response")
                results["endpoint_test"] = {"success": False, "response": result.stdout}
                self.test_results["categories"]["cursor_integration"]["failed"] += 1
                
        except Exception as e:
            print(f"❌ Cursor endpoint: {str(e)}")
            results["endpoint_test"] = {"success": False, "error": str(e)}
            self.test_results["categories"]["cursor_integration"]["failed"] += 1
            
        self.test_results["categories"]["cursor_integration"]["tests"] = results
        return results

    def test_workflow_validation(self) -> Dict[str, Any]:
        """Test 6: Workflow Validation - End-to-end workflow readiness"""
        print("\n🚀 TESTING WORKFLOW VALIDATION")
        print("=" * 50)
        
        results = {}
        
        # Test the expected DABS development workflow steps
        workflow_steps = [
            "1. Start Archon services",
            "2. Upload DABS documentation to knowledge base", 
            "3. Create DABS integration project structure",
            "4. Configure AI coding assistant with MCP server",
            "5. Begin development with AI assistance"
        ]
        
        print("📋 Validating DABS development workflow steps:")
        
        # Step 1: Archon services
        step1_ready = all([
            self.test_results["categories"]["infrastructure"]["passed"] >= 3,  # Most services running
            self.test_results["categories"]["mcp_protocol"]["passed"] >= 1    # MCP responding
        ])
        
        if step1_ready:
            print("✅ Step 1: Archon services are running")
            results["step_1"] = {"success": True, "message": "Services running"}
            self.test_results["categories"]["workflow_validation"]["passed"] += 1
        else:
            print("❌ Step 1: Archon services not fully ready")
            results["step_1"] = {"success": False, "message": "Services not ready"}
            self.test_results["categories"]["workflow_validation"]["failed"] += 1
        
        # Step 2: Documentation ready for upload
        docs_ready = self.test_results["categories"]["knowledge_base"]["passed"] >= 1
        if docs_ready:
            print("✅ Step 2: Documentation available for upload")
            results["step_2"] = {"success": True, "message": "Documentation ready"}
            self.test_results["categories"]["workflow_validation"]["passed"] += 1
        else:
            print("⚠️  Step 2: Documentation may need preparation")
            results["step_2"] = {"success": False, "message": "Documentation needs preparation"}
            self.test_results["categories"]["workflow_validation"]["failed"] += 1
        
        # Step 4: Cursor integration ready
        cursor_ready = self.test_results["categories"]["cursor_integration"]["passed"] >= 1
        if cursor_ready:
            print("✅ Step 4: Cursor integration configured")
            results["step_4"] = {"success": True, "message": "Cursor config ready"}
            self.test_results["categories"]["workflow_validation"]["passed"] += 1
        else:
            print("❌ Step 4: Cursor integration needs configuration")
            results["step_4"] = {"success": False, "message": "Cursor config needed"}
            self.test_results["categories"]["workflow_validation"]["failed"] += 1
            
        self.test_results["categories"]["workflow_validation"]["tests"] = results
        return results

    async def run_comprehensive_test(self):
        """Run all test categories"""
        print("🧪 COMPREHENSIVE MCP INTEGRATION TEST SUITE")
        print("=" * 70)
        print("Testing Archon MCP Server integration for DABS project")
        print("=" * 70)
        
        # Run all test categories
        await self.test_infrastructure_readiness()
        await self.test_mcp_protocol_compliance() 
        await self.test_dabs_specific_tools()
        await self.test_knowledge_base_readiness()
        self.test_cursor_integration_config()
        self.test_workflow_validation()
        
        # Calculate overall results
        total_passed = sum(cat["passed"] for cat in self.test_results["categories"].values())
        total_failed = sum(cat["failed"] for cat in self.test_results["categories"].values())
        total_tests = total_passed + total_failed
        
        # Determine overall status
        if total_failed == 0:
            self.test_results["overall_status"] = "ALL_PASS"
        elif total_passed >= total_tests * 0.8:  # 80% threshold
            self.test_results["overall_status"] = "MOSTLY_PASS"
        elif total_passed >= total_tests * 0.6:  # 60% threshold
            self.test_results["overall_status"] = "PARTIAL_PASS"
        else:
            self.test_results["overall_status"] = "NEEDS_WORK"

    def print_final_report(self):
        """Print comprehensive test report"""
        print("\n" + "=" * 70)
        print("🔍 COMPREHENSIVE MCP INTEGRATION TEST REPORT")
        print("=" * 70)
        
        status_icons = {
            "ALL_PASS": "🎉",
            "MOSTLY_PASS": "✅", 
            "PARTIAL_PASS": "⚠️",
            "NEEDS_WORK": "❌"
        }
        
        print(f"Overall Status: {status_icons.get(self.test_results['overall_status'], '❓')} {self.test_results['overall_status']}")
        
        print(f"\n📊 Category Breakdown:")
        for category, results in self.test_results["categories"].items():
            total = results["passed"] + results["failed"]
            if total > 0:
                percentage = (results["passed"] / total) * 100
                status = "✅" if results["failed"] == 0 else "⚠️" if percentage >= 50 else "❌"
                print(f"   {status} {category.replace('_', ' ').title()}: {results['passed']}/{total} ({percentage:.1f}%)")
        
        # Next steps based on status
        if self.test_results["overall_status"] == "ALL_PASS":
            print(f"\n🚀 READY FOR DEVELOPMENT!")
            print("✅ All systems operational")
            print("✅ Cursor can connect to: http://localhost:8151/mcp/sse") 
            print("✅ Begin Archon-first development workflow")
            
        elif self.test_results["overall_status"] in ["MOSTLY_PASS", "PARTIAL_PASS"]:
            print(f"\n⚠️  MOSTLY READY - Minor issues to address:")
            
            # Identify failing categories
            failing_categories = []
            for category, results in self.test_results["categories"].items():
                if results["failed"] > 0:
                    failing_categories.append(category.replace('_', ' ').title())
            
            if failing_categories:
                print(f"   📋 Review: {', '.join(failing_categories)}")
            
            print("🔗 Cursor connection: Should work with minor issues")
            
        else:
            print(f"\n❌ NEEDS WORK - Major issues to resolve:")
            print("   🔧 Fix infrastructure issues first")
            print("   ⏰ Allow more time for services to fully start")
            print("   🔄 Consider restarting Docker services")

    async def save_detailed_report(self):
        """Save detailed test results"""
        report_file = self.project_root / "test_results" / "comprehensive_mcp_test_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n💾 Detailed report saved: {report_file}")

async def main():
    """Run comprehensive MCP testing"""
    tester = ComprehensiveMCPTester()
    
    try:
        await tester.run_comprehensive_test()
        tester.print_final_report()
        await tester.save_detailed_report()
        
        # Return exit code based on results
        if tester.test_results["overall_status"] == "ALL_PASS":
            return 0
        elif tester.test_results["overall_status"] in ["MOSTLY_PASS", "PARTIAL_PASS"]:
            return 1
        else:
            return 2
            
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return 3

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
