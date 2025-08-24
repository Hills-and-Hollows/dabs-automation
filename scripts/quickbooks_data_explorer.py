#!/usr/bin/env python3
"""
QuickBooks Data Explorer - Interactive Data Retrieval
Hills & Hollows LLC - DABS Automation System

This script provides easy access to QuickBooks sandbox data
for testing and exploration purposes.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.automation.workflows.quickbooks_integration.qb_oauth_manager import QuickBooksOAuthManager

class QuickBooksDataExplorer:
    """Interactive QuickBooks data explorer for sandbox testing"""
    
    def __init__(self):
        self.oauth_manager = QuickBooksOAuthManager()
    
    async def get_all_items(self, limit: int = 20):
        """Get all items from QuickBooks"""
        try:
            access_token = await self.oauth_manager.get_valid_access_token()
            query = f"SELECT * FROM Item MAXRESULTS {limit}"
            return await self._execute_query(query, access_token)
        except Exception as e:
            print(f"Error getting items: {e}")
            return None
    
    async def get_inventory_items(self, limit: int = 20):
        """Get only inventory items"""
        try:
            access_token = await self.oauth_manager.get_valid_access_token()
            query = f"SELECT * FROM Item WHERE Type = 'Inventory' MAXRESULTS {limit}"
            return await self._execute_query(query, access_token)
        except Exception as e:
            print(f"Error getting inventory items: {e}")
            return None
    
    async def get_customers(self, limit: int = 20):
        """Get all customers"""
        try:
            access_token = await self.oauth_manager.get_valid_access_token()
            query = f"SELECT * FROM Customer MAXRESULTS {limit}"
            return await self._execute_query(query, access_token)
        except Exception as e:
            print(f"Error getting customers: {e}")
            return None
    
    async def get_vendors(self, limit: int = 20):
        """Get all vendors"""
        try:
            access_token = await self.oauth_manager.get_valid_access_token()
            query = f"SELECT * FROM Vendor MAXRESULTS {limit}"
            return await self._execute_query(query, access_token)
        except Exception as e:
            print(f"Error getting vendors: {e}")
            return None
    
    async def get_accounts(self, limit: int = 50):
        """Get all accounts"""
        try:
            access_token = await self.oauth_manager.get_valid_access_token()
            query = f"SELECT * FROM Account MAXRESULTS {limit}"
            return await self._execute_query(query, access_token)
        except Exception as e:
            print(f"Error getting accounts: {e}")
            return None
    
    async def get_invoices(self, limit: int = 20):
        """Get all invoices"""
        try:
            access_token = await self.oauth_manager.get_valid_access_token()
            query = f"SELECT * FROM Invoice MAXRESULTS {limit}"
            return await self._execute_query(query, access_token)
        except Exception as e:
            print(f"Error getting invoices: {e}")
            return None
    
    async def get_company_info(self):
        """Get company information"""
        try:
            return await self.oauth_manager.get_company_info()
        except Exception as e:
            print(f"Error getting company info: {e}")
            return None
    
    async def find_item_by_sku(self, sku: str):
        """Find specific item by SKU"""
        try:
            access_token = await self.oauth_manager.get_valid_access_token()
            query = f"SELECT * FROM Item WHERE Sku = '{sku}'"
            return await self._execute_query(query, access_token)
        except Exception as e:
            print(f"Error finding item by SKU: {e}")
            return None
    
    async def custom_query(self, query: str):
        """Execute custom QuickBooks query"""
        try:
            access_token = await self.oauth_manager.get_valid_access_token()
            return await self._execute_query(query, access_token)
        except Exception as e:
            print(f"Error executing custom query: {e}")
            return None
    
    async def _execute_query(self, query: str, access_token: str):
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
                    error_text = await response.text()
                    raise Exception(f"Query failed with status {response.status}: {error_text}")

async def main():
    """Interactive QuickBooks data explorer"""
    
    print("🔍 QUICKBOOKS SANDBOX DATA EXPLORER")
    print("=" * 50)
    print("🧪 Environment: SANDBOX ONLY - Safe for testing")
    print("🏢 Company: Advanced Sandbox Company_US_2")
    print()
    
    explorer = QuickBooksDataExplorer()
    
    while True:
        print("\n📋 Available Commands:")
        print("1. Get all items")
        print("2. Get inventory items only")
        print("3. Get customers")
        print("4. Get vendors")
        print("5. Get accounts")
        print("6. Get invoices")
        print("7. Get company info")
        print("8. Find item by SKU")
        print("9. Custom query")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-9): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            print("\n📦 Getting all items...")
            data = await explorer.get_all_items()
            if data:
                items = data.get('QueryResponse', {}).get('Item', [])
                print(f"Found {len(items)} items")
                for item in items[:5]:  # Show first 5
                    print(f"  - {item.get('Name', 'N/A')} (SKU: {item.get('Sku', 'N/A')})")
        elif choice == "2":
            print("\n📦 Getting inventory items...")
            data = await explorer.get_inventory_items()
            if data:
                items = data.get('QueryResponse', {}).get('Item', [])
                print(f"Found {len(items)} inventory items")
                for item in items:
                    print(f"  - {item.get('Name', 'N/A')} (SKU: {item.get('Sku', 'N/A')}) - ${item.get('UnitPrice', 'N/A')}")
        elif choice == "3":
            print("\n👥 Getting customers...")
            data = await explorer.get_customers()
            if data:
                customers = data.get('QueryResponse', {}).get('Customer', [])
                print(f"Found {len(customers)} customers")
                for customer in customers[:5]:
                    print(f"  - {customer.get('Name', 'N/A')}")
        elif choice == "4":
            print("\n🏪 Getting vendors...")
            data = await explorer.get_vendors()
            if data:
                vendors = data.get('QueryResponse', {}).get('Vendor', [])
                print(f"Found {len(vendors)} vendors")
                for vendor in vendors[:5]:
                    print(f"  - {vendor.get('Name', 'N/A')}")
        elif choice == "5":
            print("\n💰 Getting accounts...")
            data = await explorer.get_accounts()
            if data:
                accounts = data.get('QueryResponse', {}).get('Account', [])
                print(f"Found {len(accounts)} accounts")
                for account in accounts[:10]:
                    print(f"  - {account.get('Name', 'N/A')} ({account.get('AccountType', 'N/A')})")
        elif choice == "6":
            print("\n🧾 Getting invoices...")
            data = await explorer.get_invoices()
            if data:
                invoices = data.get('QueryResponse', {}).get('Invoice', [])
                print(f"Found {len(invoices)} invoices")
                for invoice in invoices[:5]:
                    print(f"  - Invoice #{invoice.get('DocNumber', 'N/A')} - ${invoice.get('TotalAmt', 'N/A')}")
        elif choice == "7":
            print("\n🏢 Getting company info...")
            data = await explorer.get_company_info()
            if data:
                print(json.dumps(data, indent=2))
        elif choice == "8":
            sku = input("Enter SKU to search for: ").strip()
            if sku:
                print(f"\n🔍 Searching for item with SKU: {sku}")
                data = await explorer.find_item_by_sku(sku)
                if data:
                    items = data.get('QueryResponse', {}).get('Item', [])
                    if items:
                        item = items[0]
                        print(f"Found: {item.get('Name', 'N/A')} - ${item.get('UnitPrice', 'N/A')}")
                        print(json.dumps(item, indent=2))
                    else:
                        print("No item found with that SKU")
        elif choice == "9":
            query = input("Enter custom QuickBooks query: ").strip()
            if query:
                print(f"\n🔍 Executing query: {query}")
                data = await explorer.custom_query(query)
                if data:
                    print(json.dumps(data, indent=2))
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())
