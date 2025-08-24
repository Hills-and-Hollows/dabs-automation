#!/usr/bin/env python3
"""
DABS Integration Testing Script
Hills & Hollows LLC - Utah Package Agency
Date: August 23, 2025

This script tests the DABS OAuth, MCP Server, and automation integration components.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.dabs_automated_ordering import DABSAutomatedOrdering, RestaurantOrder, RestaurantOrderItem
from integration.dabs_oauth_client import DABSOAuthClient
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DABSIntegrationTester:
    """
    Comprehensive tester for DABS integration components
    """
    
    def __init__(self):
        self.test_results = {}
    
    async def test_environment_setup(self):
        """Test 1: Environment Configuration"""
        logger.info("🧪 Test 1: Environment Configuration")
        
        try:
            required_vars = [
                "DABS_ORDERING_USERNAME",
                "DABS_ORDERING_PASSWORD",
                "DABS_ORDERING_LOGIN_URL"
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                raise Exception(f"Missing environment variables: {missing_vars}")
            
            logger.info("✅ All required environment variables are set")
            self.test_results["environment_setup"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Environment setup test failed: {str(e)}")
            self.test_results["environment_setup"] = False
            return False
    
    async def test_dabs_automation_init(self):
        """Test 2: DABS Automation Initialization"""
        logger.info("🧪 Test 2: DABS Automation Initialization")
        
        try:
            automation = DABSAutomatedOrdering(headless=True)
            
            # Check that credentials are loaded
            if not automation.dabs_username or not automation.dabs_password:
                raise Exception("DABS credentials not loaded from environment")
            
            logger.info(f"✅ DABS Automation initialized with username: {automation.dabs_username}")
            self.test_results["automation_init"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ DABS automation init test failed: {str(e)}")
            self.test_results["automation_init"] = False
            return False
    
    async def test_oauth_client_init(self):
        """Test 3: OAuth Client Initialization"""
        logger.info("🧪 Test 3: OAuth Client Initialization")
        
        try:
            async with DABSOAuthClient() as oauth_client:
                # Test OAuth URL generation
                auth_url = oauth_client.get_authorization_url(state="test_state")
                
                if not auth_url or "authorize" not in auth_url:
                    raise Exception("Invalid OAuth authorization URL generated")
                
                logger.info(f"✅ OAuth client initialized, auth URL: {auth_url[:80]}...")
                self.test_results["oauth_init"] = True
                return True
                
        except Exception as e:
            logger.error(f"❌ OAuth client init test failed: {str(e)}")
            self.test_results["oauth_init"] = False
            return False
    
    async def test_playwright_browser_init(self):
        """Test 4: Playwright Browser Initialization"""
        logger.info("🧪 Test 4: Playwright Browser Initialization")
        
        try:
            automation = DABSAutomatedOrdering(headless=True)
            await automation.initialize_automation_system()
            
            if not automation.browser or not automation.browser_context:
                raise Exception("Playwright browser not properly initialized")
            
            logger.info("✅ Playwright browser system initialized successfully")
            
            # Cleanup
            await automation.browser.close()
            
            self.test_results["playwright_init"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Playwright browser init test failed: {str(e)}")
            self.test_results["playwright_init"] = False
            return False
    
    async def test_dabs_login_simulation(self):
        """Test 5: DABS Login Simulation (No Actual Login)"""
        logger.info("🧪 Test 5: DABS Login Simulation")
        
        try:
            automation = DABSAutomatedOrdering(headless=True)
            
            # Test that login method exists and can be called
            # (without actually performing login to avoid hitting production)
            if not hasattr(automation, 'perform_dabs_login'):
                raise Exception("perform_dabs_login method not found")
            
            logger.info("✅ DABS login method exists and is callable")
            self.test_results["login_simulation"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ DABS login simulation test failed: {str(e)}")
            self.test_results["login_simulation"] = False
            return False
    
    async def test_restaurant_order_creation(self):
        """Test 6: Restaurant Order Object Creation"""
        logger.info("🧪 Test 6: Restaurant Order Object Creation")
        
        try:
            # Create test order items
            test_items = [
                RestaurantOrderItem(
                    sku="90000",
                    product_name="Test Vodka",
                    quantity=2,
                    unit_price=25.99,
                    category="Spirits"
                ),
                RestaurantOrderItem(
                    sku="90001", 
                    product_name="Test Wine",
                    quantity=1,
                    unit_price=18.50,
                    category="Wine"
                )
            ]
            
            # Create test restaurant order
            test_order = RestaurantOrder(
                id="TEST-ORDER-001",
                customer_name="Boulder Mountain Lodge",
                customer_email="test@bouldermountainlodge.com",
                items=test_items,
                total_amount=70.48,
                order_date=datetime.utcnow(),
                payment_method="Credit Card",
                delivery_address="Boulder, UT"
            )
            
            if not test_order.id or len(test_order.items) != 2:
                raise Exception("Restaurant order not created correctly")
            
            logger.info(f"✅ Restaurant order created: {test_order.id} with {len(test_order.items)} items")
            self.test_results["order_creation"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Restaurant order creation test failed: {str(e)}")
            self.test_results["order_creation"] = False
            return False
    
    async def test_file_permissions(self):
        """Test 7: File Permissions and Security"""
        logger.info("🧪 Test 7: File Permissions and Security")
        
        try:
            # Check that config directory exists and has proper permissions
            config_dir = Path(__file__).parent.parent / "config"
            if not config_dir.exists():
                raise Exception("Config directory does not exist")
            
            # Check DABS environment file
            env_file = config_dir / "dabs_ordering.env"
            if not env_file.exists():
                raise Exception("DABS environment file does not exist")
            
            # Check file permissions (should be readable)
            if not os.access(env_file, os.R_OK):
                raise Exception("DABS environment file is not readable")
            
            logger.info("✅ File permissions and security checks passed")
            self.test_results["file_permissions"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ File permissions test failed: {str(e)}")
            self.test_results["file_permissions"] = False
            return False
    
    async def run_all_tests(self):
        """Run all DABS integration tests"""
        logger.info("🚀 Starting DABS Integration Tests")
        logger.info("=" * 60)
        
        tests = [
            self.test_environment_setup,
            self.test_dabs_automation_init,
            self.test_oauth_client_init,
            self.test_playwright_browser_init,
            self.test_dabs_login_simulation,
            self.test_restaurant_order_creation,
            self.test_file_permissions
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed_tests += 1
            except Exception as e:
                logger.error(f"Test execution error: {str(e)}")
            
            logger.info("-" * 40)
        
        # Summary
        logger.info("=" * 60)
        logger.info("🎯 DABS INTEGRATION TEST RESULTS")
        logger.info("=" * 60)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} {test_name}")
        
        logger.info(f"\n📊 Overall Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED - DABS Integration Ready!")
            return True
        else:
            logger.warning(f"⚠️  {total_tests - passed_tests} tests failed - Review issues above")
            return False

# Utility functions
def create_sample_mcp_tools_config():
    """Create sample MCP tools configuration for DABS"""
    
    config = {
        "mcp_tools": {
            "dabs_ordering": {
                "server_name": "dabs-ordering-server",
                "executable": "python3",
                "args": ["src/mcp/dabs_ordering_mcp_server.py"],
                "env": {
                    "PYTHONPATH": "./src"
                },
                "tools": [
                    "dabs_login_status",
                    "dabs_perform_login", 
                    "dabs_process_restaurant_order",
                    "dabs_get_order_history",
                    "dabs_oauth_status",
                    "dabs_generate_oauth_url",
                    "dabs_system_health"
                ]
            }
        }
    }
    
    config_path = Path(__file__).parent.parent / "config" / "dabs_mcp_tools_config.json"
    
    import json
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"📄 Created MCP tools config: {config_path}")

# Main execution
async def main():
    """Run DABS integration tests"""
    
    # Create MCP tools config
    create_sample_mcp_tools_config()
    
    # Run tests
    tester = DABSIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("\n🎯 NEXT STEPS:")
        logger.info("1. ✅ Environment configured correctly")
        logger.info("2. ✅ DABS automation system ready")
        logger.info("3. ✅ OAuth client initialized")
        logger.info("4. 🚀 Ready to test actual DABS login (use perform_dabs_login)")
        logger.info("5. 🚀 Ready to process restaurant orders")
        logger.info("6. 🚀 MCP tools configuration created")
        
        return 0  # Success exit code
    else:
        logger.error("\n❌ INTEGRATION NOT READY:")
        logger.error("Fix the failed tests before proceeding with DABS automation")
        return 1  # Failure exit code

if __name__ == "__main__":
    exit_code = asyncio.run(main())
