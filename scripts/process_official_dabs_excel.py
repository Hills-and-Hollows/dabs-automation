#!/usr/bin/env python3
"""
Process official DABS Excel files to create comprehensive restaurant catalog

This script processes Excel files downloaded from:
https://abs.utah.gov/shop-products/interactive-product-list/

Usage:
1. Download the latest Excel file from DABS (e.g., "August-2025-Product-List_FY26_P2.xlsx")
2. Place it in the data/official_dabs_sources/ directory
3. Run this script to generate the restaurant catalog

The script will:
- Parse all products from the official Excel file
- Apply proper case sizing based on DABS packaging standards
- Generate UPC codes for SSCS integration
- Create comprehensive search terms
- Output a complete catalog for the restaurant portal
"""

import pandas as pd
import json
import re
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DABSExcelProcessor:
    """Process official DABS Excel files"""
    
    def __init__(self):
        self.data_dir = Path('data/official_dabs_sources')
        self.data_dir.mkdir(exist_ok=True)
        
        # Status code mappings from DABS documentation
        self.status_codes = {
            '1': 'General',
            'S': 'Special Order', 
            'D': 'Discontinued',
            'L': 'Limited',
            'N': 'New',
            'SPA': 'Special Pricing'
        }
        
        # DABS packaging standards (from Order 233813 analysis)
        self.packaging_rules = {
            '750ml': 12,    # 750ml bottles: 12 per case
            '1000ml': 6,    # 1L bottles: 6 per case  
            '1l': 6,        # 1L bottles: 6 per case
            '3000ml': 4,    # 3L boxes: 4 per case
            '3l': 4,        # 3L boxes: 4 per case
            '500ml': 12,    # 500ml bottles: 12 per case
            '355ml': 24,    # 355ml cans: 24 per case
            'can': 24,      # Cans: 24 per case
            'bottle': 12,   # Default bottles: 12 per case
            'box': 4        # Default boxes: 4 per case
        }
    
    def find_latest_excel_file(self):
        """Find the latest DABS Excel file in the data directory"""
        excel_files = list(self.data_dir.glob("*.xlsx"))
        
        if not excel_files:
            logger.error("No Excel files found in data/official_dabs_sources/")
            logger.info("Please download the latest Excel file from:")
            logger.info("https://abs.utah.gov/shop-products/interactive-product-list/")
            return None
        
        # Sort by modification time, get the latest
        latest_file = max(excel_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"Processing latest Excel file: {latest_file}")
        return latest_file
    
    def determine_case_size(self, product_name, size, category):
        """Determine case size based on DABS packaging standards"""
        try:
            # Convert to lowercase for matching
            name_lower = str(product_name).lower()
            size_lower = str(size).lower()
            category_lower = str(category).lower()
            
            # Check size-based rules first
            for size_key, case_size in self.packaging_rules.items():
                if size_key in size_lower or size_key in name_lower:
                    return case_size
            
            # Category-based defaults
            if any(word in category_lower for word in ['beer', 'cider']):
                if 'can' in name_lower or '355' in size_lower:
                    return 24  # Cans
                else:
                    return 12  # Bottles
            
            if any(word in category_lower for word in ['wine', 'spirit', 'liquor']):
                return 12  # Standard wine/spirits case
            
            # Default case size
            return 12
            
        except Exception as e:
            logger.warning(f"Error determining case size: {e}")
            return 12
    
    def generate_upc_from_csc(self, csc):
        """Generate UPC code from CSC for SSCS integration"""
        try:
            # Clean CSC and create UPC
            csc_clean = ''.join(filter(str.isdigit, str(csc)))
            if len(csc_clean) <= 11:
                return f"0{csc_clean.zfill(11)}"
            else:
                return csc_clean[:12]
        except:
            return "000000000000"
    
    def create_search_terms(self, product):
        """Create comprehensive search terms"""
        terms = []
        
        # Product name words
        if product.get('product_name'):
            # Remove common words and split
            name_words = re.findall(r'\b\w+\b', product['product_name'].lower())
            terms.extend([w for w in name_words if len(w) > 2])
        
        # Category and subcategory
        for field in ['category', 'subcategory']:
            if product.get(field):
                terms.extend(product[field].lower().split())
        
        # Size information
        if product.get('size'):
            terms.append(product['size'].lower())
        
        # CSC/SKU
        if product.get('csc'):
            terms.append(str(product['csc']).lower())
        
        return ' '.join(set(terms))
    
    def parse_excel_file(self, excel_path):
        """Parse the official DABS Excel file"""
        logger.info(f"Parsing Excel file: {excel_path}")
        
        try:
            # Try different sheet names that might contain the data
            sheet_names = ['Sheet1', 'Products', 'Product List', 'Data']
            df = None
            
            for sheet_name in sheet_names:
                try:
                    df = pd.read_excel(excel_path, sheet_name=sheet_name)
                    logger.info(f"Successfully read sheet: {sheet_name}")
                    break
                except:
                    continue
            
            if df is None:
                # Try reading the first sheet
                df = pd.read_excel(excel_path)
                logger.info("Reading first sheet of Excel file")
            
            logger.info(f"Excel file has {len(df)} rows and columns: {list(df.columns)}")
            
            products = []
            for idx, row in df.iterrows():
                try:
                    # Map common column names (DABS uses various formats)
                    csc = self.get_column_value(row, ['CSC', 'Code', 'SKU', 'Product Code'])
                    name = self.get_column_value(row, ['Product Name', 'Description', 'Name', 'Product'])
                    size = self.get_column_value(row, ['Size', 'Volume', 'ML', 'Container Size'])
                    category = self.get_column_value(row, ['Category', 'Cat', 'Type'])
                    subcategory = self.get_column_value(row, ['Subcategory', 'Subcat', 'Sub Category'])
                    status = self.get_column_value(row, ['Status', 'Stat', 'Active'])
                    price = self.get_column_value(row, ['Price', 'Retail Price', 'Cost', 'Amount'])
                    
                    # Skip if missing essential data
                    if not csc or not name:
                        continue
                    
                    # Clean and format data
                    csc = str(csc).strip()
                    name = str(name).strip()
                    size = str(size).strip() if size else ''
                    category = str(category).strip() if category else 'General'
                    subcategory = str(subcategory).strip() if subcategory else ''
                    status = str(status).strip() if status else '1'
                    
                    # Parse price
                    try:
                        price = float(str(price).replace('$', '').replace(',', '')) if price else 0.0
                    except:
                        price = 0.0
                    
                    # Determine case size
                    case_size = self.determine_case_size(name, size, category)
                    
                    # Create product record
                    product = {
                        'sku': csc,
                        'vendor_item_code': csc,
                        'csc': csc,
                        'upc': self.generate_upc_from_csc(csc),
                        'product_name': name,
                        'description': name,
                        'size': size,
                        'category': category.upper(),
                        'subcategory': subcategory,
                        'case_size': case_size,
                        'status': status,
                        'status_description': self.status_codes.get(status, 'General'),
                        'price': price,
                        'case_price': price * case_size,
                        'effective_date': datetime.now().strftime('%Y-%m-%d'),
                        'last_updated': datetime.now().isoformat(),
                        'source': f'DABS Official Excel: {excel_path.name}'
                    }
                    
                    # Add search terms
                    product['search_terms'] = self.create_search_terms(product)
                    
                    products.append(product)
                    
                except Exception as e:
                    logger.warning(f"Error parsing row {idx}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(products)} products")
            return products
            
        except Exception as e:
            logger.error(f"Error parsing Excel file: {e}")
            return []
    
    def get_column_value(self, row, possible_names):
        """Get value from row using possible column names"""
        for name in possible_names:
            if name in row.index and pd.notna(row[name]):
                return row[name]
        return None
    
    def generate_restaurant_catalog(self, products):
        """Generate catalog JSON for restaurant portal"""
        logger.info("Generating restaurant catalog...")
        
        # Filter active products (status 1, L, N)
        active_products = [p for p in products if p['status'] in ['1', 'L', 'N']]
        
        # Get unique categories
        categories = sorted(list(set(p['category'] for p in active_products if p['category'])))
        
        catalog = {
            'success': True,
            'total_found': len(active_products),
            'total_available': len(products),
            'last_updated': datetime.now().isoformat(),
            'categories': categories,
            'source': 'Utah DABS Official Excel Product List',
            'data_notes': {
                'case_sizing': 'Based on DABS packaging standards from Order 233813',
                'upc_generation': 'Generated from CSC codes for SSCS integration',
                'status_codes': self.status_codes,
                'active_statuses': ['1', 'L', 'N']
            },
            'products': active_products
        }
        
        # Save to restaurant portal
        output_path = Path('archon-mcp/archon-ui-main/public/src/web_portal/official_dabs_catalog.json')
        with open(output_path, 'w') as f:
            json.dump(catalog, f, indent=2)
        
        logger.info(f"Generated restaurant catalog with {len(active_products)} active products")
        logger.info(f"Categories: {categories}")
        logger.info(f"Saved to: {output_path}")
        
        return catalog
    
    def process_official_excel(self):
        """Main method to process official DABS Excel file"""
        logger.info("Starting DABS Excel processing...")
        
        # Find latest Excel file
        excel_path = self.find_latest_excel_file()
        if not excel_path:
            return False
        
        # Parse Excel data
        products = self.parse_excel_file(excel_path)
        if not products:
            logger.error("No products parsed from Excel file")
            return False
        
        # Generate restaurant catalog
        catalog = self.generate_restaurant_catalog(products)
        
        # Save raw data for analysis
        raw_data_path = self.data_dir / f"processed_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(raw_data_path, 'w') as f:
            json.dump(products, f, indent=2)
        
        logger.info(f"Processing complete!")
        logger.info(f"Active products: {catalog['total_found']}")
        logger.info(f"Total products: {catalog['total_available']}")
        logger.info(f"Raw data saved: {raw_data_path}")
        
        return True

def main():
    """Main function"""
    processor = DABSExcelProcessor()
    success = processor.process_official_excel()
    
    if success:
        print("✅ Successfully processed official DABS Excel file!")
        print("📋 Restaurant catalog updated with official DABS data")
        print("🔄 Update the restaurant portal to use 'official_dabs_catalog.json'")
    else:
        print("❌ Failed to process DABS Excel file")
        print("📥 Please download the latest Excel file from:")
        print("   https://abs.utah.gov/shop-products/interactive-product-list/")
        print("📁 Place it in: data/official_dabs_sources/")

if __name__ == "__main__":
    main()
