#!/usr/bin/env python3
"""
Create enhanced catalog using Category Price List for better restaurant experience

This script processes the Category price list to create a restaurant catalog
with improved category organization and browsing experience.
"""

import json
import PyPDF2
import re
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CategoryEnhancedCatalog:
    """Create enhanced catalog from Category price list"""
    
    def __init__(self):
        self.data_dir = Path('data/official_dabs_sources')
        
        # Enhanced category mappings for better restaurant experience
        self.category_mappings = {
            'spirits': 'SPIRITS',
            'wine': 'WINE', 
            'beer': 'BEER',
            'liqueur': 'LIQUEURS',
            'special': 'SPECIAL ORDERS',
            'general': 'GENERAL'
        }
        
        # Status codes
        self.status_codes = {
            '1': 'General',
            'D': 'Discontinued',
            'U': 'Special Order', 
            'X': 'Inactive',
            'S': 'Special',
            'L': 'Limited',
            'N': 'New'
        }
    
    def parse_category_pdf(self):
        """Parse the Category price list PDF"""
        logger.info("Parsing Category price list PDF...")
        
        pdf_path = self.data_dir / "Sept2025CategoryPriceList.pdf"
        if not pdf_path.exists():
            logger.error("Category price list not found. Run analyze_category_price_list.py first.")
            return []
        
        products = []
        current_category = "GENERAL"
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    lines = text.split('\n')
                    
                    for line in lines:
                        # Check for category headers
                        category = self.detect_category_header(line)
                        if category:
                            current_category = category
                            logger.info(f"Found category: {current_category}")
                            continue
                        
                        # Parse product lines
                        product = self.parse_product_line(line, current_category)
                        if product:
                            products.append(product)
            
            logger.info(f"Parsed {len(products)} products from Category PDF")
            return products
            
        except Exception as e:
            logger.error(f"Error parsing Category PDF: {e}")
            return []
    
    def detect_category_header(self, line):
        """Detect category headers in the PDF"""
        line_clean = line.strip().upper()
        
        # Common DABS category headers
        category_indicators = {
            'SPIRITS': 'SPIRITS',
            'WINE': 'WINE',
            'BEER': 'BEER', 
            'ALE': 'BEER',
            'LIQUEUR': 'LIQUEURS',
            'CORDIAL': 'LIQUEURS',
            'SPECIAL ORDER': 'SPECIAL ORDERS',
            'SPARKLING': 'SPARKLING WINE',
            'CHAMPAGNE': 'SPARKLING WINE',
            'RED WINE': 'RED WINE',
            'WHITE WINE': 'WHITE WINE',
            'VODKA': 'SPIRITS - VODKA',
            'WHISKEY': 'SPIRITS - WHISKEY',
            'GIN': 'SPIRITS - GIN',
            'RUM': 'SPIRITS - RUM',
            'TEQUILA': 'SPIRITS - TEQUILA'
        }
        
        # Check if line is a category header
        for indicator, category in category_indicators.items():
            if indicator in line_clean and len(line_clean.split()) <= 4:
                return category
        
        return None
    
    def parse_product_line(self, line, current_category):
        """Parse individual product line from Category PDF"""
        try:
            # Skip header lines and empty lines
            if not line.strip() or 'CS Code' in line or 'Page' in line:
                return None
            
            # Look for CSC codes (6 digits)
            csc_match = re.search(r'\b(\d{6})\b', line)
            if not csc_match:
                return None
            
            csc = csc_match.group(1)
            
            # Extract size (usually follows CSC)
            size_match = re.search(r'(\d+(?:\.\d+)?\s*(?:ML|L|OZ))', line, re.IGNORECASE)
            size = size_match.group(1) if size_match else ''
            
            # Extract price
            price_match = re.search(r'\$?(\d+\.\d{2})', line)
            price = float(price_match.group(1)) if price_match else 0.0
            
            # Extract status
            status = '1'  # Default
            for code in self.status_codes.keys():
                if f' {code} ' in line:
                    status = code
                    break
            
            # Extract product name (complex parsing needed)
            product_name = self.extract_product_name(line, csc, size)
            
            # Determine case size
            case_size = self.determine_case_size(size, product_name, current_category)
            
            # Generate UPC
            upc = self.generate_upc_from_csc(csc)
            
            product = {
                'sku': csc,
                'vendor_item_code': csc,
                'csc': csc,
                'upc': upc,
                'product_name': product_name,
                'description': product_name,
                'size': size,
                'category': current_category,
                'case_size': case_size,
                'status': status,
                'status_description': self.status_codes.get(status, 'Unknown'),
                'price': price,
                'case_price': price * case_size,
                'effective_date': '2025-09-01',
                'last_updated': datetime.now().isoformat(),
                'source': 'September 2025 Category Price List'
            }
            
            # Create search terms
            product['search_terms'] = self.create_search_terms(product)
            
            return product
            
        except Exception as e:
            logger.debug(f"Error parsing line '{line}': {e}")
            return None
    
    def extract_product_name(self, line, csc, size):
        """Extract clean product name from line"""
        try:
            # Remove CSC code
            line_clean = line.replace(csc, '', 1)
            
            # Remove size if found
            if size:
                line_clean = line_clean.replace(size, '', 1)
            
            # Remove common patterns
            patterns_to_remove = [
                r'\$\d+\.\d{2}',  # Prices
                r'\b[UDXSLN]\b',  # Status codes
                r'\d+\s*$',      # Trailing numbers
                r'YS[ETCB]',     # DABS category codes
                r'[A-Z]{3}\s*$'  # 3-letter codes at end
            ]
            
            for pattern in patterns_to_remove:
                line_clean = re.sub(pattern, '', line_clean)
            
            # Clean up whitespace and extract meaningful name
            words = line_clean.split()
            
            # Filter out non-name words
            name_words = []
            for word in words:
                if (len(word) > 1 and 
                    not word.isdigit() and 
                    not re.match(r'^\d+\.\d+$', word)):
                    name_words.append(word)
            
            product_name = ' '.join(name_words).strip()
            
            # Ensure minimum name length
            if len(product_name) < 5:
                product_name = f"Product {csc}"
            
            return product_name
            
        except:
            return f"Product {csc}"
    
    def determine_case_size(self, size, product_name, category):
        """Determine case size based on size, name, and category"""
        try:
            size_lower = size.lower()
            name_lower = product_name.lower()
            category_lower = category.lower()
            
            # Size-based rules (most reliable)
            if '750' in size_lower:
                return 12  # 750ml bottles
            elif '1000' in size_lower or '1l' in size_lower:
                return 6   # 1L bottles
            elif '3000' in size_lower or '3l' in size_lower:
                return 4   # 3L boxes
            elif '500' in size_lower:
                return 12  # 500ml bottles
            elif '355' in size_lower or '330' in size_lower:
                return 24  # Cans
            elif '19000' in size_lower:
                return 1   # Kegs
            
            # Category-based rules
            if 'beer' in category_lower:
                return 24 if 'can' in name_lower else 12
            elif 'wine' in category_lower or 'spirits' in category_lower:
                return 12
            
            return 12  # Default
            
        except:
            return 12
    
    def generate_upc_from_csc(self, csc):
        """Generate UPC from CSC"""
        try:
            csc_clean = ''.join(filter(str.isdigit, str(csc)))
            if len(csc_clean) <= 11:
                return f"0{csc_clean.zfill(11)}"
            else:
                return csc_clean[:12]
        except:
            return "000000000000"
    
    def create_search_terms(self, product):
        """Create search terms"""
        terms = []
        
        if product.get('product_name'):
            name_words = re.findall(r'\b\w+\b', product['product_name'].lower())
            terms.extend([w for w in name_words if len(w) > 2])
        
        if product.get('category'):
            terms.extend(product['category'].lower().split())
        
        if product.get('size'):
            terms.append(product['size'].lower())
        
        if product.get('csc'):
            terms.append(str(product['csc']).lower())
        
        return ' '.join(set(terms))
    
    def create_enhanced_restaurant_catalog(self, products):
        """Create enhanced restaurant catalog with category organization"""
        logger.info("Creating enhanced restaurant catalog...")
        
        # Filter for restaurant-appropriate products
        restaurant_statuses = ['1', 'L', 'N', 'U']
        restaurant_products = [p for p in products if p['status'] in restaurant_statuses]
        
        # Get unique categories and sort them logically
        categories = sorted(list(set(p['category'] for p in restaurant_products if p['category'])))
        
        # Organize categories for better restaurant experience
        category_order = [
            'SPIRITS', 'SPIRITS - VODKA', 'SPIRITS - WHISKEY', 'SPIRITS - GIN', 
            'SPIRITS - RUM', 'SPIRITS - TEQUILA',
            'WINE', 'RED WINE', 'WHITE WINE', 'SPARKLING WINE',
            'BEER', 'LIQUEURS', 'SPECIAL ORDERS', 'GENERAL'
        ]
        
        # Sort categories by preferred order
        ordered_categories = []
        for cat in category_order:
            if cat in categories:
                ordered_categories.append(cat)
        
        # Add any remaining categories
        for cat in categories:
            if cat not in ordered_categories:
                ordered_categories.append(cat)
        
        catalog = {
            'success': True,
            'total_found': len(restaurant_products),
            'total_available': len(products),
            'last_updated': datetime.now().isoformat(),
            'categories': ordered_categories,
            'source': 'September 2025 Category Price List - Enhanced',
            'automation_status': 'Active - Daily Updates at 6 AM UTC',
            'organization': 'Category-based for optimal restaurant browsing',
            'coverage': {
                'active_products': len([p for p in products if p['status'] == '1']),
                'special_orders': len([p for p in products if p['status'] == 'U']),
                'discontinued': len([p for p in products if p['status'] == 'D']),
                'limited': len([p for p in products if p['status'] == 'L']),
                'new': len([p for p in products if p['status'] == 'N'])
            },
            'products': restaurant_products
        }
        
        return catalog
    
    def create_category_enhanced_catalog(self):
        """Main method to create category-enhanced catalog"""
        logger.info("Creating category-enhanced DABS catalog...")
        
        # Parse Category PDF
        products = self.parse_category_pdf()
        if not products:
            logger.error("Failed to parse Category PDF")
            return False
        
        # Create enhanced restaurant catalog
        catalog = self.create_enhanced_restaurant_catalog(products)
        
        # Save enhanced catalog
        output_path = Path('archon-mcp/archon-ui-main/public/src/web_portal/category_enhanced_dabs_catalog.json')
        with open(output_path, 'w') as f:
            json.dump(catalog, f, indent=2)
        
        logger.info(f"Created category-enhanced catalog with {catalog['total_found']} restaurant products")
        logger.info(f"Categories: {len(catalog['categories'])}")
        logger.info(f"Saved to: {output_path}")
        
        return True

def main():
    """Main function"""
    creator = CategoryEnhancedCatalog()
    success = creator.create_category_enhanced_catalog()
    
    if success:
        print("✅ Category-enhanced DABS catalog created successfully!")
        print("🏪 Restaurant portal now optimized for category-based browsing")
    else:
        print("❌ Failed to create category-enhanced catalog")

if __name__ == "__main__":
    main()
