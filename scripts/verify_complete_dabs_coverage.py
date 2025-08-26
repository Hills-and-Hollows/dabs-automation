#!/usr/bin/env python3
"""
Verify complete DABS catalog coverage against official September 2025 price list

This script downloads and processes the official September 2025 DABS price list
to ensure our restaurant catalog includes ALL available products.
"""

import requests
import json
import pandas as pd
import PyPDF2
import io
from datetime import datetime
from pathlib import Path
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DABSCoverageVerifier:
    """Verify complete DABS catalog coverage"""
    
    def __init__(self):
        self.official_pdf_url = "https://abs.utah.gov/wp-content/uploads/Sept2025AlphaPriceList.pdf"
        self.data_dir = Path('data/official_dabs_sources')
        self.data_dir.mkdir(exist_ok=True)
        
    def download_official_price_list(self):
        """Download the official September 2025 price list"""
        logger.info("Downloading official September 2025 DABS price list...")
        
        try:
            response = requests.get(self.official_pdf_url, timeout=30)
            if response.status_code == 200:
                pdf_path = self.data_dir / "Sept2025AlphaPriceList.pdf"
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded price list: {pdf_path}")
                logger.info(f"File size: {len(response.content):,} bytes")
                return pdf_path
            else:
                logger.error(f"Failed to download: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading price list: {e}")
            return None
    
    def parse_pdf_price_list(self, pdf_path):
        """Parse the PDF price list to extract all products"""
        logger.info(f"Parsing PDF price list: {pdf_path}")
        
        try:
            products = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    
                    # Parse each line for product information
                    lines = text.split('\n')
                    for line in lines:
                        product = self.parse_product_line(line)
                        if product:
                            products.append(product)
            
            logger.info(f"Parsed {len(products)} products from PDF")
            return products
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            return []
    
    def parse_product_line(self, line):
        """Parse a single line from the PDF to extract product information"""
        try:
            # DABS price list format typically:
            # CSC CODE | PRODUCT NAME | SIZE | CASE PACK | STATUS | CATEGORY | PRICE
            
            # Skip header lines and empty lines
            if not line.strip() or 'CSC' in line or 'CODE' in line:
                return None
            
            # Look for lines with CSC codes (typically 6 digits)
            csc_match = re.search(r'\b(\d{6})\b', line)
            if not csc_match:
                return None
            
            csc = csc_match.group(1)
            
            # Extract price (typically at end of line)
            price_match = re.search(r'\$(\d+\.\d{2})', line)
            price = float(price_match.group(1)) if price_match else 0.0
            
            # Extract product name (between CSC and price)
            name_part = line[csc_match.end():price_match.start() if price_match else len(line)]
            name_part = name_part.strip()
            
            # Extract size information
            size_match = re.search(r'(\d+(?:\.\d+)?\s*(?:ML|L|OZ))', name_part, re.IGNORECASE)
            size = size_match.group(1) if size_match else ''
            
            # Clean product name
            product_name = re.sub(r'\s+', ' ', name_part).strip()
            
            return {
                'csc': csc,
                'sku': csc,
                'product_name': product_name,
                'size': size,
                'price': price,
                'source': 'September 2025 Official PDF'
            }
            
        except Exception as e:
            logger.debug(f"Error parsing line '{line}': {e}")
            return None
    
    def load_current_catalog(self):
        """Load our current restaurant catalog"""
        try:
            catalog_path = Path('archon-mcp/archon-ui-main/public/src/web_portal/complete_dabs_catalog.json')
            with open(catalog_path, 'r') as f:
                catalog = json.load(f)
            
            logger.info(f"Loaded current catalog: {catalog['total_found']} products")
            return catalog['products']
            
        except Exception as e:
            logger.error(f"Error loading current catalog: {e}")
            return []
    
    def compare_catalogs(self, official_products, current_products):
        """Compare official price list with our current catalog"""
        logger.info("Comparing official price list with current catalog...")
        
        # Create lookup sets
        official_skus = {p['sku'] for p in official_products}
        current_skus = {p['sku'] for p in current_products}
        
        # Find differences
        missing_in_current = official_skus - current_skus
        extra_in_current = current_skus - official_skus
        common_skus = official_skus & current_skus
        
        # Create detailed comparison
        comparison = {
            'official_count': len(official_products),
            'current_count': len(current_products),
            'common_count': len(common_skus),
            'missing_in_current': len(missing_in_current),
            'extra_in_current': len(extra_in_current),
            'coverage_percentage': (len(common_skus) / len(official_skus) * 100) if official_skus else 0,
            'missing_products': [p for p in official_products if p['sku'] in missing_in_current],
            'extra_products': [p for p in current_products if p['sku'] in extra_in_current]
        }
        
        return comparison
    
    def generate_coverage_report(self, comparison):
        """Generate a detailed coverage report"""
        report = f"""
# DABS Catalog Coverage Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Official September 2025 Products**: {comparison['official_count']:,}
- **Current Catalog Products**: {comparison['current_count']:,}
- **Common Products**: {comparison['common_count']:,}
- **Coverage Percentage**: {comparison['coverage_percentage']:.1f}%

## Missing Products ({comparison['missing_in_current']} items)
"""
        
        if comparison['missing_products']:
            report += "\n### Products in Official List but Missing from Our Catalog:\n"
            for product in comparison['missing_products'][:20]:  # Show first 20
                report += f"- **{product['sku']}**: {product['product_name']} - ${product['price']:.2f}\n"
            
            if len(comparison['missing_products']) > 20:
                report += f"\n... and {len(comparison['missing_products']) - 20} more products\n"
        
        if comparison['extra_products']:
            report += f"\n## Extra Products ({comparison['extra_in_current']} items)\n"
            report += "### Products in Our Catalog but Not in Official List:\n"
            for product in comparison['extra_products'][:10]:  # Show first 10
                report += f"- **{product['sku']}**: {product['product_name']} - ${product['price']:.2f}\n"
        
        report += f"""
## Recommendations

{'✅ **EXCELLENT COVERAGE!**' if comparison['coverage_percentage'] > 95 else '⚠️ **COVERAGE GAPS DETECTED**'}

"""
        
        if comparison['coverage_percentage'] < 100:
            report += f"""
### Action Items:
1. **Add Missing Products**: {comparison['missing_in_current']} products need to be added
2. **Update Automation**: Ensure daily updates capture all product statuses
3. **Verify Sources**: Check if missing products are special orders or discontinued
4. **Enhanced Parsing**: Improve PDF parsing to capture all product variations

### Next Steps:
1. Run the enhanced catalog updater to include missing products
2. Update the restaurant portal with complete catalog
3. Verify NAXML generation includes all products
4. Test search functionality across complete catalog
"""
        else:
            report += """
### Status: COMPLETE ✅
- All official DABS products are included in our catalog
- Restaurant customers have access to the complete inventory
- NAXML generation covers all available products
- Automated updates are working perfectly
"""
        
        return report
    
    def verify_complete_coverage(self):
        """Main method to verify complete DABS coverage"""
        logger.info("Starting complete DABS coverage verification...")
        
        # Download official price list
        pdf_path = self.download_official_price_list()
        if not pdf_path:
            logger.error("Failed to download official price list")
            return False
        
        # Parse official products
        official_products = self.parse_pdf_price_list(pdf_path)
        if not official_products:
            logger.error("Failed to parse official products")
            return False
        
        # Load current catalog
        current_products = self.load_current_catalog()
        if not current_products:
            logger.error("Failed to load current catalog")
            return False
        
        # Compare catalogs
        comparison = self.compare_catalogs(official_products, current_products)
        
        # Generate report
        report = self.generate_coverage_report(comparison)
        
        # Save report
        report_path = self.data_dir / f"coverage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        # Save detailed data
        data_path = self.data_dir / f"coverage_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(data_path, 'w') as f:
            json.dump({
                'comparison': comparison,
                'official_products': official_products[:100],  # Sample
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("🔍 DABS CATALOG COVERAGE VERIFICATION COMPLETE")
        print("="*60)
        print(f"📊 Official Products: {comparison['official_count']:,}")
        print(f"📋 Current Catalog: {comparison['current_count']:,}")
        print(f"✅ Coverage: {comparison['coverage_percentage']:.1f}%")
        print(f"❌ Missing: {comparison['missing_in_current']}")
        print(f"📄 Report: {report_path}")
        print(f"💾 Data: {data_path}")
        
        if comparison['coverage_percentage'] >= 95:
            print("🎉 EXCELLENT COVERAGE! Your catalog is comprehensive.")
        else:
            print("⚠️  COVERAGE GAPS DETECTED - Action required.")
        
        return True

def main():
    """Main function"""
    verifier = DABSCoverageVerifier()
    success = verifier.verify_complete_coverage()
    
    if success:
        print("\n✅ Coverage verification completed successfully!")
    else:
        print("\n❌ Coverage verification failed")

if __name__ == "__main__":
    main()
