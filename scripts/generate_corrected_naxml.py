#!/usr/bin/env python3
"""
Generate Corrected NAXML with Proper UPC Field Population
Fixes UPC matching issue for SSCS import validation

Created: January 23, 2025
Purpose: Create NAXML with both UPC and VendorItemCode populated for safe SSCS import
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def generate_corrected_naxml():
    """Generate NAXML with proper UPC field population"""
    print('🔧 GENERATING CORRECTED NAXML FOR SSCS IMPORT')
    print('=' * 60)
    print('🎯 Fixing UPC field population for safe item matching')
    print()
    
    try:
        from processors.dabs_processor import DABSProduct
        
        # Load real ProcessInventory.csv data
        print('📊 Loading ProcessInventory.csv...')
        df = pd.read_csv('dabs/ProcessInventory.csv', sep='\t', header=None, on_bad_lines='skip')
        
        # Filter alcohol items - first 5 for safe testing
        alcohol_items = df[df.iloc[:, 5].str.contains('LIQUOR|BEER', na=False, case=False)]
        print(f'✅ Found {len(alcohol_items):,} alcohol items')
        print('🧪 Using first 5 items for safe testing')
        print()
        
        # Convert to DABSProduct objects
        products = []
        for i, (_, row) in enumerate(alcohol_items.head(5).iterrows()):
            try:
                upc_code = str(row.iloc[0]).strip()
                description = str(row.iloc[1]).strip()
                retail_price = float(row.iloc[4]) if pd.notna(row.iloc[4]) and row.iloc[4] != 0 else 29.99
                department = str(row.iloc[5]).strip()
                
                # Skip items with invalid data
                if not upc_code or upc_code == '0' or not description:
                    continue
                
                product = DABSProduct(
                    sku=upc_code,
                    product_name=description,
                    retail_price=retail_price,
                    category=department,
                    on_special_pricing=False,
                    effective_date=datetime.now(),
                    status='Active',
                    updated_on=datetime.now()
                )
                products.append(product)
                
                print(f'   📋 {i+1}. {description[:40]:<40} | UPC: {upc_code} | ${retail_price}')
                
            except Exception as e:
                print(f'   ⚠️  Skipped item {i+1}: {e}')
                continue
        
        print(f'\n✅ Prepared {len(products)} valid products for NAXML')
        
        # Generate CORRECTED NAXML structure
        print('\n🔧 Generating corrected NAXML structure...')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"DABS_CORRECTED_{timestamp}_ItemPrice.xml"
        file_path = Path('exports') / filename
        
        # Create NAXML with CORRECTED UPC field population
        root = ET.Element("ItemSynch")
        root.set("version", "2.0")
        root.set("timestamp", datetime.now().isoformat())
        root.set("vendor", "DABS")
        
        # Header
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "Source").text = "DABS"
        ET.SubElement(header, "Destination").text = "SSCS-CPB"
        ET.SubElement(header, "VendorName").text = "DABS"
        ET.SubElement(header, "VendorZone").text = "ZONE0_GLOBAL"
        ET.SubElement(header, "RecordCount").text = str(len(products))
        ET.SubElement(header, "GeneratedDate").text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ET.SubElement(header, "ApplyVendorListPrice").text = "true"
        
        # Items with CORRECTED UPC field population
        items = ET.SubElement(root, "Items")
        
        for product in products:
            item = ET.SubElement(items, "Item")
            
            # ✅ CORRECTED: Populate BOTH UPC fields with same UPC
            ET.SubElement(item, "VendorItemCode").text = product.sku
            ET.SubElement(item, "UPC").text = product.sku  # ✅ NOW POPULATED!
            
            ET.SubElement(item, "Description").text = product.product_name
            ET.SubElement(item, "Category").text = product.category
            ET.SubElement(item, "Status").text = product.status
            
            # Pricing
            pricing = ET.SubElement(item, "Pricing")
            ET.SubElement(pricing, "VendorListPrice").text = str(product.retail_price)
            ET.SubElement(pricing, "EffectiveDate").text = product.effective_date.strftime("%Y-%m-%d")
            ET.SubElement(pricing, "PriceType").text = "Regular"
            
            # Attributes (SAFE: AutoAccept=false)
            attributes = ET.SubElement(item, "Attributes")
            ET.SubElement(attributes, "VendorZone").text = "ZONE0_GLOBAL"
            ET.SubElement(attributes, "AutoAccept").text = "false"  # ✅ SAFE: Manual approval
        
        # Write corrected NAXML file
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        
        file_size = file_path.stat().st_size
        print(f'✅ Generated corrected NAXML: {filename}')
        print(f'📄 File size: {file_size:,} bytes')
        print(f'📊 Items: {len(products)}')
        
        # Display corrected structure sample
        print()
        print('📋 CORRECTED NAXML STRUCTURE SAMPLE:')
        print('-' * 50)
        
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Show first item structure
        lines = content.split('\n')
        for i, line in enumerate(lines[:20], 1):
            if line.strip():
                print(f'{i:2d}: {line}')
        
        print()
        print('🎯 KEY CORRECTION MADE:')
        print('❌ OLD: <UPC /> (empty)')
        print('✅ NEW: <UPC>012354001350</UPC> (populated with actual UPC)')
        print()
        print('🛡️  SAFETY FEATURES MAINTAINED:')
        print('✅ AutoAccept="false" - Manual approval required')
        print('✅ Small batch (5 items) - Safe for testing')
        print('✅ Real product data - Accurate for validation')
        
        return str(file_path)
        
    except Exception as e:
        print(f'💥 Error generating corrected NAXML: {e}')
        import traceback
        traceback.print_exc()
        return None

def create_import_validation_plan():
    """Create step-by-step plan for safe SSCS import validation"""
    print()
    print('🎯 SAFE SSCS IMPORT VALIDATION PLAN')
    print('=' * 50)
    
    plan = [
        {
            'step': 1,
            'title': 'Upload Corrected NAXML (5 items)',
            'action': 'Use SSCS File Import Utility',
            'file': 'DABS_CORRECTED_*_ItemPrice.xml',
            'expected': 'SSCS shows preview of 5 price changes',
            'validation': 'Verify SSCS matches EXISTING items (not creating new)'
        },
        {
            'step': 2,
            'title': 'Review SSCS Import Preview',
            'action': 'Check SSCS preview screen',
            'file': 'N/A',
            'expected': 'Shows "Update existing item" not "Create new item"',
            'validation': 'Confirm item names and prices match expectations'
        },
        {
            'step': 3,
            'title': 'Manual Approval (1-2 items only)',
            'action': 'Approve 1-2 items manually in SSCS',
            'file': 'N/A',
            'expected': 'Prices update successfully in SSCS system',
            'validation': 'Verify no duplicate items created'
        },
        {
            'step': 4,
            'title': 'Validate Results',
            'action': 'Check SSCS inventory after import',
            'file': 'N/A',
            'expected': 'Updated prices visible, no duplicates',
            'validation': 'Item counts unchanged, prices updated correctly'
        },
        {
            'step': 5,
            'title': 'Full Batch Testing',
            'action': 'Generate NAXML with all 491 alcohol items',
            'file': 'DABS_FULL_*_ItemPrice.xml',
            'expected': 'All items matched correctly for update',
            'validation': 'Production-ready import confirmed'
        }
    ]
    
    for step in plan:
        print(f"STEP {step['step']}: {step['title']}")
        print(f"   ACTION: {step['action']}")
        if step['file'] != 'N/A':
            print(f"   FILE: {step['file']}")
        print(f"   EXPECTED: {step['expected']}")
        print(f"   VALIDATION: {step['validation']}")
        print()

def main():
    print('🎯 HILLS & HOLLOWS LLC - UPC AUTOMATION')
    print('🔧 CORRECTED NAXML GENERATION FOR SSCS IMPORT')
    print('=' * 70)
    print()
    
    # Generate corrected NAXML
    corrected_file = generate_corrected_naxml()
    
    if corrected_file:
        # Create validation plan
        create_import_validation_plan()
        
        print()
        print('🚀 READY FOR SAFE SSCS TESTING!')
        print(f'📁 Upload file: {corrected_file}')
        print('🛡️  Safe testing: Only 5 items, manual approval required')
        print('🎯 Validates UPC matching before full deployment')
        
        return 0
    else:
        print('❌ Failed to generate corrected NAXML')
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
