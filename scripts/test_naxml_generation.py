#!/usr/bin/env python3
"""
NAXML Generation Production Test
Test NAXML file generation with real ProcessInventory.csv data

Created: January 23, 2025
Purpose: Validate SSCS CPB integration readiness
"""

import asyncio
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def test_naxml_generation_with_real_data():
    print('📤 NAXML GENERATION PRODUCTION TEST')
    print('=' * 50)
    print('🎯 Testing with real ProcessInventory.csv data')
    print()
    
    try:
        from processors.sscs_integration import create_sscs_cpb_integrator
        from processors.dabs_processor import DABSProduct
        
        # Load real ProcessInventory.csv data
        print('📊 Loading ProcessInventory.csv...')
        df = pd.read_csv('dabs/ProcessInventory.csv', sep='\t', header=None, on_bad_lines='skip')
        print(f'✅ Loaded {len(df):,} total items')
        
        # Filter alcohol items (department column analysis)
        print('🍺 Filtering alcohol items...')
        alcohol_items = df[df.iloc[:, 5].str.contains('LIQUOR|BEER', na=False, case=False)]
        print(f'✅ Found {len(alcohol_items):,} alcohol items')
        
        # Convert first 10 items to DABSProduct objects for testing
        print('🔄 Converting to DABS product format...')
        products = []
        
        for i, (_, row) in enumerate(alcohol_items.head(10).iterrows()):
            try:
                # Map ProcessInventory.csv columns to DABSProduct
                upc_code = str(row.iloc[0]).strip()
                description = str(row.iloc[1]).strip()
                retail_price = float(row.iloc[4]) if pd.notna(row.iloc[4]) and row.iloc[4] != 0 else 29.99
                department = str(row.iloc[5]).strip()
                
                # Skip items with invalid data
                if not upc_code or upc_code == '0' or not description:
                    continue
                
                product = DABSProduct(
                    sku=upc_code,  # Use UPC as SKU
                    product_name=description,
                    retail_price=retail_price,
                    category=department,
                    on_special_pricing=False,
                    effective_date=datetime.now(),
                    status='Active',
                    updated_on=datetime.now()
                )
                products.append(product)
                
                print(f'   📋 Item {i+1}: {description[:40]}... → ${retail_price}')
                
            except Exception as e:
                print(f'   ⚠️  Skipped item {i+1}: {e}')
                continue
        
        print(f'✅ Converted {len(products)} valid products')
        print()
        
        if not products:
            print('❌ No valid products for NAXML generation')
            return False
        
        # Generate NAXML file using SSCS CPB integrator
        print('📤 Generating NAXML for SSCS CPB vendor import...')
        integrator = create_sscs_cpb_integrator()
        
        result = await integrator.upload_pricing_data(products)
        
        if result.success:
            print('✅ NAXML GENERATION: SUCCESS!')
            print(f'📁 File Created: {result.file_path}')
            print(f'📊 SKUs Processed: {result.skus_uploaded}')
            print(f'⏱️  Processing Time: {result.upload_time:.2f}s')
            print(f'🔒 File Checksum: {result.checksum[:16]}...')
            
            # Verify file content
            if result.file_path and Path(result.file_path).exists():
                file_size = Path(result.file_path).stat().st_size
                print(f'📄 File Size: {file_size:,} bytes')
                
                # Read and display sample content
                print()
                print('📋 NAXML Content Sample:')
                with open(result.file_path, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')[:10]  # First 10 lines
                    for i, line in enumerate(lines, 1):
                        print(f'   {i:2d}: {line}')
                
                print()
                if file_size > 1000:  # Should be substantial for valid NAXML
                    print('✅ NAXML FILE: VALID CONTENT')
                    print('🎯 READY FOR SSCS CPB VENDOR IMPORT')
                    
                    # Check for proper NAXML structure
                    if '<ItemSynch' in content and '<Items>' in content:
                        print('✅ NAXML STRUCTURE: VALID')
                        return True
                    else:
                        print('⚠️  NAXML STRUCTURE: CHECK REQUIRED')
                        return False
                else:
                    print('❌ NAXML FILE: INSUFFICIENT CONTENT')
                    return False
            else:
                print('❌ NAXML FILE: NOT FOUND')
                return False
        else:
            print('❌ NAXML GENERATION: FAILED')
            print(f'🚨 Errors: {result.errors}')
            return False
            
    except Exception as e:
        print(f'💥 NAXML generation test error: {e}')
        import traceback
        traceback.print_exc()
        return False

async def main():
    print('🎯 HILLS & HOLLOWS LLC - UPC AUTOMATION')
    print('📤 NAXML PRODUCTION VALIDATION TEST')
    print('=' * 60)
    print()
    
    result = await test_naxml_generation_with_real_data()
    
    print()
    print('🎯 VALIDATION RESULT:')
    if result:
        print('✅ NAXML GENERATION: PRODUCTION READY')
        print('🎊 SSCS CPB integration validated')
        print('⚡ Ready for Phase 2 testing (SSCS CPB vendor setup)')
    else:
        print('❌ NAXML GENERATION: REQUIRES ATTENTION')
        print('🔧 Review errors and adjust before SSCS integration')
    
    return 0 if result else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
