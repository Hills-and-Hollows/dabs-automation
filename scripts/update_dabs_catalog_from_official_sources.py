#!/usr/bin/env python3
"""
Update DABS catalog from official Utah DABS sources
Based on documentation of official DABS data sources and tools

Official Sources:
1. Monthly Retail Price Books (PDF) - abs.utah.gov/vendors/monthly-price-books/
2. Interactive Product List Spreadsheet (Excel) - abs.utah.gov/shop-products/interactive-product-list/
3. DABS Online Product Locator - webapps2.abc.utah.gov/ProdApps/ProductLocatorCore
4. Special Order Products Portal - webapps2.abc.utah.gov/ProdApps/SpecialOrdersCore
5. Approved Canned Cocktails (RTDs) - Google Looker Studio
6. Off-Premise Approved Products - abs.utah.gov/licenses-permits/off-premise-products

Key Data Fields:
- CSC (Control State Code) - unique product ID
- Product Name/Description
- Size (mL)
- Case Pack (units per case)
- Status Code (1=general, S=special order, D=discontinued)
- Category/Subcategory
- Retail Price
- Inventory levels (from online locator)
"""

import asyncio
import aiohttp
import pandas as pd
import json
import requests
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DABSOfficialDataUpdater:
    """Update DABS catalog from official Utah DABS sources"""
    
    def __init__(self):
        self.base_urls = {
            'price_books': 'https://abs.utah.gov/vendors/monthly-price-books/',
            'product_list': 'https://abs.utah.gov/shop-products/interactive-product-list/',
            'product_locator': 'https://webapps2.abc.utah.gov/ProdApps/ProductLocatorCore',
            'special_orders': 'https://webapps2.abc.utah.gov/ProdApps/SpecialOrdersCore',
            'off_premise': 'https://abs.utah.gov/licenses-permits/off-premise-products'
        }
        
        self.output_dir = Path('data/official_dabs_sources')
        self.output_dir.mkdir(exist_ok=True)
        
        # Status code mappings from DABS documentation
        self.status_codes = {
            '1': 'General',
            'S': 'Special Order',
            'D': 'Discontinued',
            'L': 'Limited',
            'N': 'New'
        }
        
        # Category mappings (will be populated from data)
        self.categories = {}
    
    async def download_excel_product_list(self):
        """Download the latest Excel product list from DABS"""
        logger.info("Downloading official DABS Excel product list...")
        
        try:
            # This would need to be updated with the actual direct download URL
            # The documentation shows files like "August-2025-Product-List_FY26_P2.xlsx"
            excel_url = "https://abs.utah.gov/wp-content/uploads/current-product-list.xlsx"
            
            response = requests.get(excel_url)
            if response.status_code == 200:
                excel_path = self.output_dir / f"dabs_product_list_{datetime.now().strftime('%Y%m%d')}.xlsx"
                with open(excel_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Downloaded Excel product list to {excel_path}")
                return excel_path
            else:
                logger.error(f"Failed to download Excel file: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading Excel product list: {e}")
            return None
    
    def parse_excel_product_list(self, excel_path):
        """Parse the official DABS Excel product list"""
        logger.info(f"Parsing Excel product list: {excel_path}")
        
        try:
            # Read the Excel file
            df = pd.read_excel(excel_path)
            
            # Expected columns based on DABS documentation:
            # CSC, Product Name, Size, Case Pack, Status, Category, Retail Price
            
            products = []
            for _, row in df.iterrows():
                try:
                    # Map Excel columns to our format
                    product = {
                        'csc': str(row.get('CSC', row.get('Code', ''))).strip(),
                        'sku': str(row.get('CSC', row.get('Code', ''))).strip(),  # CSC is the SKU
                        'vendor_item_code': str(row.get('CSC', row.get('Code', ''))).strip(),
                        'product_name': str(row.get('Product Name', row.get('Description', ''))).strip(),
                        'description': str(row.get('Product Name', row.get('Description', ''))).strip(),
                        'size': str(row.get('Size', '')).strip(),
                        'case_pack': self.parse_case_pack(row.get('Case Pack', row.get('Pack', ''))),
                        'status': str(row.get('Status', '1')).strip(),
                        'status_description': self.status_codes.get(str(row.get('Status', '1')).strip(), 'General'),
                        'category': str(row.get('Category', row.get('Cat', ''))).strip(),
                        'subcategory': str(row.get('Subcategory', row.get('Subcat', ''))).strip(),
                        'price': self.parse_price(row.get('Retail Price', row.get('Price', 0))),
                        'effective_date': datetime.now().strftime('%Y-%m-%d'),
                        'last_updated': datetime.now().isoformat(),
                        'source': 'DABS Official Excel Product List'
                    }
                    
                    # Generate UPC from CSC (for SSCS integration)
                    product['upc'] = self.generate_upc_from_csc(product['csc'])
                    
                    # Create search terms
                    product['search_terms'] = self.create_search_terms(product)
                    
                    products.append(product)
                    
                except Exception as e:
                    logger.warning(f"Error parsing product row: {e}")
                    continue
            
            logger.info(f"Parsed {len(products)} products from Excel file")
            return products
            
        except Exception as e:
            logger.error(f"Error parsing Excel file: {e}")
            return []
    
    def parse_case_pack(self, case_pack_value):
        """Parse case pack value to integer"""
        try:
            if pd.isna(case_pack_value):
                return 12  # Default case size
            
            # Handle various formats like "12", "12/case", "12 bottles", etc.
            case_str = str(case_pack_value).lower().strip()
            
            # Extract number from string
            import re
            numbers = re.findall(r'\d+', case_str)
            if numbers:
                return int(numbers[0])
            
            return 12  # Default
            
        except:
            return 12  # Default case size
    
    def parse_price(self, price_value):
        """Parse price value to float"""
        try:
            if pd.isna(price_value):
                return 0.0
            
            # Handle various price formats
            price_str = str(price_value).replace('$', '').replace(',', '').strip()
            return float(price_str)
            
        except:
            return 0.0
    
    def generate_upc_from_csc(self, csc):
        """Generate UPC code from CSC for SSCS integration"""
        try:
            # Pad CSC to create a 12-digit UPC
            csc_clean = ''.join(filter(str.isdigit, str(csc)))
            if len(csc_clean) <= 11:
                return f"0{csc_clean.zfill(11)}"
            else:
                return csc_clean[:12]
        except:
            return "000000000000"
    
    def create_search_terms(self, product):
        """Create search terms for product"""
        terms = []
        
        # Add product name words
        if product['product_name']:
            terms.extend(product['product_name'].lower().split())
        
        # Add category
        if product['category']:
            terms.append(product['category'].lower())
        
        # Add size
        if product['size']:
            terms.append(product['size'].lower())
        
        # Add CSC/SKU
        if product['csc']:
            terms.append(product['csc'].lower())
        
        return ' '.join(set(terms))
    
    def generate_restaurant_catalog(self, products):
        """Generate catalog JSON for restaurant portal"""
        logger.info("Generating restaurant catalog JSON...")
        
        # Filter active products only
        active_products = [p for p in products if p['status'] in ['1', 'L', 'N']]
        
        # Get unique categories
        categories = sorted(list(set(p['category'] for p in active_products if p['category'])))
        
        catalog = {
            'success': True,
            'total_found': len(active_products),
            'total_available': len(products),
            'last_updated': datetime.now().isoformat(),
            'categories': categories,
            'source': 'Utah DABS Official Data Sources',
            'products': active_products
        }
        
        # Save to restaurant portal
        output_path = Path('archon-mcp/archon-ui-main/public/src/web_portal/official_dabs_catalog.json')
        with open(output_path, 'w') as f:
            json.dump(catalog, f, indent=2)
        
        logger.info(f"Generated restaurant catalog with {len(active_products)} active products")
        logger.info(f"Categories: {categories}")
        
        return catalog
    
    async def update_from_official_sources(self):
        """Main method to update catalog from official DABS sources"""
        logger.info("Starting update from official DABS sources...")
        
        # Step 1: Download Excel product list
        excel_path = await self.download_excel_product_list()
        if not excel_path:
            logger.error("Failed to download Excel product list")
            return False
        
        # Step 2: Parse Excel data
        products = self.parse_excel_product_list(excel_path)
        if not products:
            logger.error("Failed to parse products from Excel file")
            return False
        
        # Step 3: Generate restaurant catalog
        catalog = self.generate_restaurant_catalog(products)
        
        # Step 4: Save raw data for analysis
        raw_data_path = self.output_dir / f"raw_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(raw_data_path, 'w') as f:
            json.dump(products, f, indent=2)
        
        logger.info(f"Update complete! Generated catalog with {catalog['total_found']} active products")
        logger.info(f"Raw data saved to: {raw_data_path}")
        
        return True

async def main():
    """Main function to run the DABS data update"""
    updater = DABSOfficialDataUpdater()
    success = await updater.update_from_official_sources()
    
    if success:
        print("✅ Successfully updated DABS catalog from official sources!")
    else:
        print("❌ Failed to update DABS catalog")

if __name__ == "__main__":
    asyncio.run(main())
