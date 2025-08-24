#!/usr/bin/env python3
"""
Generate Test NAXML File for SSCS CPB Testing
Based on research report specifications and Conexxus standards

Author: DABS Automation System
Created: 2024-12-19
"""

import json
import os
import sys
from datetime import datetime, date
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def generate_test_naxml_for_cpb():
    """Generate test NAXML ItemPrice file for SSCS CPB testing"""
    
    print("🔧 Generating Test NAXML for SSCS CPB")
    print("=" * 40)
    
    # Test data based on research report example
    test_products = [
        {
            'csc_code': '056828',
            'product_name': 'BACARDI MOJITO 1750ml',
            'current_price': 22.19,
            'new_price': 19.99,
            'category': 'PREMIXED - MISC',
            'size_ml': '1750',
            'upc': '080480008628'
        },
        {
            'csc_code': '123456',
            'product_name': 'TEST BEER 12oz',
            'current_price': 15.99,
            'new_price': 14.99,
            'category': 'BEER',
            'size_ml': '355',
            'upc': '123456789012'
        }
    ]
    
    # Generate NAXML ItemPrice based on Conexxus standards
    naxml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<NAXML_PBIPriceChange xmlns="http://www.naxml.org/POSBO/Vocabulary/2003-10-16">
  <TransmissionHeader>
    <StoreLocationID>HILLS_HOLLOWS_BOULDER</StoreLocationID>
    <VendorZone>ZONE0_GLOBAL</VendorZone>
    <TransmissionDate>{datetime.now().isoformat()}</TransmissionDate>
    <SourceIdentifier>DABS_AUTOMATION_SYSTEM</SourceIdentifier>
  </TransmissionHeader>'''
    
    # Add ItemPriceChange elements for each product
    for product in test_products:
        naxml_content += f'''
  <ItemPriceChange>
    <ItemID>DABS-{product['csc_code']}</ItemID>
    <ReceiptDescription>{product['product_name']}</ReceiptDescription>
    <Price>{product['new_price']}</Price>
    <PriceEffectiveDate>{date.today().isoformat()}</PriceEffectiveDate>
    <Department>{product['category']}</Department>
    <UPC>{product['upc']}</UPC>
  </ItemPriceChange>'''
    
    naxml_content += '''
</NAXML_PBIPriceChange>'''
    
    # Save test NAXML file
    test_file_path = Path('data/sscs_discovery/DABS_TEST_ItemPrice.xml')
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(naxml_content)
    
    print(f"✅ Test NAXML file generated: {test_file_path}")
    print(f"📦 Products included: {len(test_products)}")
    print(f"🔧 Format: NAXML ItemPrice (Conexxus standard)")
    print(f"🎯 Purpose: SSCS CPB Vendor Import testing")
    
    # Also generate CSV mapping for reference
    csv_data = []
    for product in test_products:
        csv_data.append({
            'DABS_CSC_Code': product['csc_code'],
            'DABS_Product_Name': product['product_name'],
            'DABS_Current_Retail': product['current_price'],
            'DABS_New_Retail': product['new_price'],
            'DABS_Category': product['category'],
            'SSCS_Item_ID': f"DABS-{product['csc_code']}",
            'NAXML_ItemID': f"DABS-{product['csc_code']}",
            'NAXML_Price': product['new_price'],
            'NAXML_EffectiveDate': date.today().isoformat()
        })
    
    # Save CSV mapping
    import pandas as pd
    df = pd.DataFrame(csv_data)
    csv_file_path = Path('data/sscs_discovery/DABS_SSCS_Test_Mapping.csv')
    df.to_csv(csv_file_path, index=False)
    
    print(f"📊 Test mapping CSV generated: {csv_file_path}")
    
    return {
        'naxml_file': str(test_file_path),
        'csv_mapping': str(csv_file_path),
        'product_count': len(test_products),
        'file_size_bytes': test_file_path.stat().st_size
    }

def generate_manual_testing_guide():
    """Generate manual testing guide for SSCS CPB"""
    
    guide_content = """# SSCS CPB Manual Testing Guide
## Test NAXML Upload for Tessa's Automation

### Step 1: Login to SSCS
1. Open browser: https://sscsta.sscsinc.com/TransactionAnalysis.App/#!/merchandisesales/
2. Username: v6242shawn
3. Password: Notone2016!
4. Should redirect to CDB interface

### Step 2: Navigate to Central Price Book
1. Look for "Price Book", "CPB", "Central Price", or "Vendor" links
2. Navigate to CPB section
3. Look for "Vendor Import" or "Import" functionality

### Step 3: Configure DABS Vendor
1. Create new vendor profile named "DABS"
2. Set import type to "NAXML ItemSynch/ItemPrice" (McLane profile)
3. Set file mask to "DABS*.xml"
4. Enable "Apply Vendor List Price"
5. Set vendor zone to "ZONE0_GLOBAL"

### Step 4: Test NAXML Upload
1. Use test file: data/sscs_discovery/DABS_TEST_ItemPrice.xml
2. Upload via vendor import interface
3. Check "Outside Updates" for staged changes
4. Validate price changes match test data

### Step 5: Test DTS (Distribute to Sites)
1. Accept changes in Outside Updates
2. Run "Distribute to Sites" (DTS)
3. Check for Scheduled Task automation options
4. Validate price changes reach POS terminals

### Expected Results:
- CPB processes NAXML file without errors
- Test products appear in Outside Updates
- Price changes match test data (BACARDI MOJITO: $19.99)
- DTS successfully distributes to POS

### Documentation:
- Screenshot each step
- Note any configuration options
- Document error messages (if any)
- Record timing for processing steps
"""
    
    guide_path = Path('docs/SSCS_CPB_MANUAL_TESTING_GUIDE.md')
    guide_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(guide_path, 'w') as f:
        f.write(guide_content)
    
    print(f"📋 Manual testing guide created: {guide_path}")
    return str(guide_path)

if __name__ == "__main__":
    print("🔧 SSCS Test File Generation")
    print("=" * 30)
    
    # Generate test NAXML file
    naxml_result = generate_test_naxml_for_cpb()
    
    # Generate manual testing guide
    guide_path = generate_manual_testing_guide()
    
    print(f"\n✅ Test files ready for SSCS CPB validation:")
    print(f"📄 NAXML test file: {naxml_result['naxml_file']}")
    print(f"📊 CSV mapping: {naxml_result['csv_mapping']}")
    print(f"📋 Testing guide: {guide_path}")
    
    print(f"\n🎯 Next Steps for Tessa's Automation:")
    print(f"1. 🌐 Login to SSCS manually using confirmed credentials")
    print(f"2. 🔍 Navigate to CPB Vendor Import section")
    print(f"3. ⚙️ Configure DABS vendor profile")
    print(f"4. 📤 Test NAXML file upload")
    print(f"5. ✅ Validate CPB → DTS → POS workflow")
    print(f"6. 🚀 Deploy automated solution for Tessa")
    
    print(f"\n🎊 TOOLS READY - PROCEEDING WITH TESSA'S RELIEF IMPLEMENTATION ✅")
