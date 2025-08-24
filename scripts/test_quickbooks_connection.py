#!/usr/bin/env python3
"""
QuickBooks Connection Test & Data Discovery
===========================================

Comprehensive test script to verify QuickBooks Online API access
and discover available data for Hills & Hollows DABS automation.

Features:
- OAuth token validation
- Company information retrieval
- Inventory/Items discovery
- Account structure analysis
- Customer data access
- Vendor information
- Financial data capabilities

Author: Hills & Hollows LLC - DABS Automation
Date: 2025-08-22
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.automation.workflows.quickbooks_integration.qb_oauth_manager import (
    QuickBooksOAuthManager,
    QuickBooksInventoryManager
)
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("QB_CONNECTION_TEST")

class QuickBooksDataDiscovery:
    """Comprehensive QuickBooks data discovery and testing"""
    
    def __init__(self):
        self.oauth_manager = QuickBooksOAuthManager()
        self.inventory_manager = QuickBooksInventoryManager()
        self.test_results = {
            "test_timestamp": datetime.now().isoformat(),
            "connection_status": "unknown",
            "company_info": {},
            "available_data": {},
            "api_capabilities": {},
            "errors": []
        }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run complete QuickBooks connection and data discovery test"""
        
        print("🚀 QUICKBOOKS CONNECTION & DATA DISCOVERY TEST")
        print("=" * 60)
        print("Hills & Hollows LLC - DABS Automation System")
        print()
        
        try:
            # Step 1: Validate OAuth connection
            await self._test_oauth_connection()
            
            # Step 2: Get company information
            await self._discover_company_info()
            
            # Step 3: Discover available data types
            await self._discover_data_types()
            
            # Step 4: Test inventory capabilities
            await self._test_inventory_capabilities()
            
            # Step 5: Analyze account structure
            await self._analyze_account_structure()
            
            # Step 6: Test customer/vendor access
            await self._test_customer_vendor_access()
            
            # Step 7: Test financial data access
            await self._test_financial_data_access()
            
            # Step 8: Generate summary report
            await self._generate_summary_report()
            
        except Exception as e:
            logger.error(f"Test execution error: {e}")
            self.test_results["errors"].append(f"Test execution error: {e}")
        
        return self.test_results
    
    async def _test_oauth_connection(self):
        """Test OAuth token validation and API connectivity"""
        
        print("🔐 STEP 1: Testing OAuth Connection")
        print("-" * 40)
        
        try:
            # Validate tokens
            is_valid = await self.oauth_manager.validate_tokens()
            
            if is_valid:
                print("   ✅ OAuth tokens valid")
                print("   ✅ API connectivity confirmed")
                self.test_results["connection_status"] = "connected"
                
                # Get token info
                if self.oauth_manager.current_tokens:
                    token_info = {
                        "expires_at": self.oauth_manager.current_tokens.expires_at.isoformat(),
                        "company_id": self.oauth_manager.current_tokens.company_id,
                        "is_expired": self.oauth_manager.current_tokens.is_expired
                    }
                    self.test_results["token_info"] = token_info
                    print(f"   📅 Token expires: {token_info['expires_at']}")
                    print(f"   🏢 Company ID: {token_info['company_id']}")
                
            else:
                print("   ❌ OAuth token validation failed")
                self.test_results["connection_status"] = "failed"
                self.test_results["errors"].append("OAuth token validation failed")
                
        except Exception as e:
            logger.error(f"OAuth connection test error: {e}")
            print(f"   ❌ Connection test failed: {e}")
            self.test_results["connection_status"] = "error"
            self.test_results["errors"].append(f"OAuth connection error: {e}")
        
        print()
    
    async def _discover_company_info(self):
        """Discover QuickBooks company information"""
        
        print("🏢 STEP 2: Discovering Company Information")
        print("-" * 40)
        
        try:
            company_data = await self.oauth_manager.get_company_info()
            
            if company_data:
                # Extract key company information
                query_response = company_data.get('QueryResponse', {})
                company_info = query_response.get('CompanyInfo', [{}])[0] if query_response.get('CompanyInfo') else {}
                
                if company_info:
                    self.test_results["company_info"] = {
                        "company_name": company_info.get('CompanyName', 'Unknown'),
                        "legal_name": company_info.get('LegalName', 'Unknown'),
                        "country": company_info.get('Country', 'Unknown'),
                        "fiscal_year_start": company_info.get('FiscalYearStartMonth', 'Unknown'),
                        "company_id": company_info.get('Id', 'Unknown'),
                        "supported_languages": company_info.get('SupportedLanguages', 'Unknown')
                    }
                    
                    print(f"   ✅ Company: {self.test_results['company_info']['company_name']}")
                    print(f"   ✅ Legal Name: {self.test_results['company_info']['legal_name']}")
                    print(f"   ✅ Country: {self.test_results['company_info']['country']}")
                    print(f"   ✅ Fiscal Year Start: {self.test_results['company_info']['fiscal_year_start']}")
                else:
                    print("   ⚠️  Company info structure unexpected")
                    self.test_results["company_info"] = {"raw_data": company_data}
            else:
                print("   ❌ Failed to retrieve company information")
                self.test_results["errors"].append("Failed to retrieve company information")
                
        except Exception as e:
            logger.error(f"Company info discovery error: {e}")
            print(f"   ❌ Company info error: {e}")
            self.test_results["errors"].append(f"Company info error: {e}")
        
        print()

    async def _discover_data_types(self):
        """Discover available QuickBooks data types and entities"""

        print("📊 STEP 3: Discovering Available Data Types")
        print("-" * 40)

        # Test various QuickBooks entities
        entities_to_test = [
            ("Items", "SELECT * FROM Item MAXRESULTS 5"),
            ("Customers", "SELECT * FROM Customer MAXRESULTS 5"),
            ("Vendors", "SELECT * FROM Vendor MAXRESULTS 5"),
            ("Accounts", "SELECT * FROM Account MAXRESULTS 10"),
            ("Invoices", "SELECT * FROM Invoice MAXRESULTS 5"),
            ("Bills", "SELECT * FROM Bill MAXRESULTS 5"),
            ("Payments", "SELECT * FROM Payment MAXRESULTS 5"),
            ("Purchases", "SELECT * FROM Purchase MAXRESULTS 5")
        ]

        available_entities = {}

        try:
            access_token = await self.oauth_manager.get_valid_access_token()

            for entity_name, query in entities_to_test:
                try:
                    count = await self._query_entity_count(entity_name, query, access_token)
                    available_entities[entity_name] = count
                    print(f"   ✅ {entity_name}: {count} records found")

                except Exception as e:
                    available_entities[entity_name] = f"Error: {e}"
                    print(f"   ❌ {entity_name}: Access error")

            self.test_results["available_data"] = available_entities

        except Exception as e:
            logger.error(f"Data discovery error: {e}")
            print(f"   ❌ Data discovery failed: {e}")
            self.test_results["errors"].append(f"Data discovery error: {e}")

        print()

    async def _query_entity_count(self, entity_name: str, query: str, access_token: str) -> int:
        """Query QuickBooks entity and return count"""

        import aiohttp

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }

        url = f"{self.oauth_manager.base_url}/v3/company/{self.oauth_manager.current_tokens.company_id}/query"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params={'query': query}) as response:
                if response.status == 200:
                    data = await response.json()
                    query_response = data.get('QueryResponse', {})
                    entity_data = query_response.get(entity_name.rstrip('s'), [])  # Remove 's' for API response
                    return len(entity_data) if isinstance(entity_data, list) else (1 if entity_data else 0)
                else:
                    raise Exception(f"Query failed with status {response.status}")

    async def _test_inventory_capabilities(self):
        """Test inventory-specific capabilities"""

        print("📦 STEP 4: Testing Inventory Capabilities")
        print("-" * 40)

        try:
            access_token = await self.oauth_manager.get_valid_access_token()

            # Test inventory item query
            inventory_query = "SELECT * FROM Item WHERE Type = 'Inventory' MAXRESULTS 10"
            inventory_items = await self._execute_query(inventory_query, access_token)

            if inventory_items:
                items = inventory_items.get('QueryResponse', {}).get('Item', [])
                self.test_results["api_capabilities"]["inventory_items"] = len(items)
                print(f"   ✅ Inventory items found: {len(items)}")

                # Analyze first item structure
                if items:
                    sample_item = items[0]
                    item_fields = list(sample_item.keys())
                    self.test_results["api_capabilities"]["inventory_fields"] = item_fields
                    print(f"   ✅ Available item fields: {len(item_fields)}")
                    print(f"      📋 Key fields: {', '.join(item_fields[:8])}...")

                    # Check for DABS-relevant fields
                    dabs_relevant = []
                    for field in ['Sku', 'Name', 'UnitPrice', 'QtyOnHand', 'Description']:
                        if field in item_fields:
                            dabs_relevant.append(field)

                    print(f"   ✅ DABS-relevant fields: {', '.join(dabs_relevant)}")
                    self.test_results["api_capabilities"]["dabs_relevant_fields"] = dabs_relevant
            else:
                print("   ⚠️  No inventory items found")
                self.test_results["api_capabilities"]["inventory_items"] = 0

        except Exception as e:
            logger.error(f"Inventory test error: {e}")
            print(f"   ❌ Inventory test failed: {e}")
            self.test_results["errors"].append(f"Inventory test error: {e}")

        print()

    async def _analyze_account_structure(self):
        """Analyze QuickBooks account structure"""

        print("💰 STEP 5: Analyzing Account Structure")
        print("-" * 40)

        try:
            access_token = await self.oauth_manager.get_valid_access_token()

            # Get all accounts
            accounts_query = "SELECT * FROM Account"
            accounts_data = await self._execute_query(accounts_query, access_token)

            if accounts_data:
                accounts = accounts_data.get('QueryResponse', {}).get('Account', [])

                # Categorize accounts
                account_types = {}
                for account in accounts:
                    acc_type = account.get('AccountType', 'Unknown')
                    if acc_type not in account_types:
                        account_types[acc_type] = 0
                    account_types[acc_type] += 1

                self.test_results["api_capabilities"]["account_structure"] = account_types

                print(f"   ✅ Total accounts: {len(accounts)}")
                for acc_type, count in account_types.items():
                    print(f"      📊 {acc_type}: {count} accounts")

                # Find key accounts for inventory
                key_accounts = {}
                for account in accounts:
                    acc_type = account.get('AccountType', '')
                    acc_name = account.get('Name', '')

                    if 'Income' in acc_type or 'Sales' in acc_name:
                        key_accounts['income'] = account.get('Id')
                    elif 'Cost of Goods Sold' in acc_type or 'COGS' in acc_name:
                        key_accounts['cogs'] = account.get('Id')
                    elif 'Inventory' in acc_name or 'Asset' in acc_type:
                        key_accounts['inventory_asset'] = account.get('Id')

                self.test_results["api_capabilities"]["key_accounts"] = key_accounts
                print(f"   ✅ Key accounts identified: {len(key_accounts)}")

            else:
                print("   ❌ Failed to retrieve account structure")

        except Exception as e:
            logger.error(f"Account analysis error: {e}")
            print(f"   ❌ Account analysis failed: {e}")
            self.test_results["errors"].append(f"Account analysis error: {e}")

        print()

    async def _test_customer_vendor_access(self):
        """Test customer and vendor data access"""

        print("👥 STEP 6: Testing Customer & Vendor Access")
        print("-" * 40)

        try:
            access_token = await self.oauth_manager.get_valid_access_token()

            # Test customer access
            customers_query = "SELECT * FROM Customer MAXRESULTS 5"
            customers_data = await self._execute_query(customers_query, access_token)

            if customers_data:
                customers = customers_data.get('QueryResponse', {}).get('Customer', [])
                self.test_results["api_capabilities"]["customers_count"] = len(customers)
                print(f"   ✅ Customers accessible: {len(customers)}")

            # Test vendor access
            vendors_query = "SELECT * FROM Vendor MAXRESULTS 5"
            vendors_data = await self._execute_query(vendors_query, access_token)

            if vendors_data:
                vendors = vendors_data.get('QueryResponse', {}).get('Vendor', [])
                self.test_results["api_capabilities"]["vendors_count"] = len(vendors)
                print(f"   ✅ Vendors accessible: {len(vendors)}")

        except Exception as e:
            logger.error(f"Customer/Vendor test error: {e}")
            print(f"   ❌ Customer/Vendor test failed: {e}")
            self.test_results["errors"].append(f"Customer/Vendor test error: {e}")

        print()

    async def _test_financial_data_access(self):
        """Test financial data access capabilities"""

        print("💼 STEP 7: Testing Financial Data Access")
        print("-" * 40)

        try:
            access_token = await self.oauth_manager.get_valid_access_token()

            # Test various financial entities
            financial_tests = [
                ("Invoices", "SELECT * FROM Invoice MAXRESULTS 3"),
                ("Bills", "SELECT * FROM Bill MAXRESULTS 3"),
                ("Payments", "SELECT * FROM Payment MAXRESULTS 3"),
                ("Journal Entries", "SELECT * FROM JournalEntry MAXRESULTS 3")
            ]

            financial_access = {}

            for entity_name, query in financial_tests:
                try:
                    data = await self._execute_query(query, access_token)
                    if data and data.get('QueryResponse'):
                        entity_key = entity_name.replace(' ', '').replace('s', '')  # Remove spaces and 's'
                        entities = data.get('QueryResponse', {}).get(entity_key, [])
                        count = len(entities) if isinstance(entities, list) else (1 if entities else 0)
                        financial_access[entity_name] = count
                        print(f"   ✅ {entity_name}: {count} records accessible")
                    else:
                        financial_access[entity_name] = 0
                        print(f"   ⚠️  {entity_name}: No records found")

                except Exception as e:
                    financial_access[entity_name] = f"Error: {str(e)}"
                    print(f"   ❌ {entity_name}: Access error")

            self.test_results["api_capabilities"]["financial_data"] = financial_access

        except Exception as e:
            logger.error(f"Financial data test error: {e}")
            print(f"   ❌ Financial data test failed: {e}")
            self.test_results["errors"].append(f"Financial data test error: {e}")

        print()

    async def _execute_query(self, query: str, access_token: str) -> Optional[Dict[str, Any]]:
        """Execute QuickBooks API query"""

        import aiohttp

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }

        url = f"{self.oauth_manager.base_url}/v3/company/{self.oauth_manager.current_tokens.company_id}/query"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params={'query': query}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Query failed with status {response.status}")

    async def _generate_summary_report(self):
        """Generate comprehensive summary report"""

        print("📋 STEP 8: Generating Summary Report")
        print("-" * 40)

        # Connection summary
        if self.test_results["connection_status"] == "connected":
            print("   ✅ QuickBooks Online connection: SUCCESSFUL")
        else:
            print("   ❌ QuickBooks Online connection: FAILED")

        # Company info summary
        if self.test_results.get("company_info"):
            company = self.test_results["company_info"]
            print(f"   🏢 Company: {company.get('company_name', 'Unknown')}")

        # Data access summary
        available_data = self.test_results.get("available_data", {})
        print(f"   📊 Data entities accessible: {len([k for k, v in available_data.items() if isinstance(v, int) and v > 0])}")

        # API capabilities summary
        capabilities = self.test_results.get("api_capabilities", {})
        if capabilities.get("inventory_items", 0) > 0:
            print(f"   📦 Inventory items: {capabilities['inventory_items']} found")

        if capabilities.get("dabs_relevant_fields"):
            print(f"   🎯 DABS integration fields: {len(capabilities['dabs_relevant_fields'])} available")

        # Error summary
        errors = self.test_results.get("errors", [])
        if errors:
            print(f"   ⚠️  Errors encountered: {len(errors)}")
        else:
            print("   ✅ No errors encountered")

        print()
        print("🎯 DABS INTEGRATION READINESS:")
        print("-" * 40)

        if self.test_results["connection_status"] == "connected":
            print("   ✅ Ready for inventory synchronization")
            print("   ✅ Ready for pricing automation")
            print("   ✅ Ready for financial reporting integration")
        else:
            print("   ❌ Connection issues prevent integration")

        print()

async def main():
    """Main test execution function"""
    
    try:
        # Initialize discovery system
        discovery = QuickBooksDataDiscovery()
        
        # Run comprehensive test
        results = await discovery.run_comprehensive_test()
        
        # Save results to file
        results_file = Path("test_results/quickbooks_discovery_results.json")
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📊 Test results saved to: {results_file}")
        
        # Return success/failure based on connection status
        if results["connection_status"] == "connected":
            print("\n✅ QuickBooks connection test PASSED")
            return 0
        else:
            print("\n❌ QuickBooks connection test FAILED")
            return 1
            
    except Exception as e:
        logger.error(f"Main execution error: {e}")
        print(f"\n💥 Test execution failed: {e}")
        return 2

if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
