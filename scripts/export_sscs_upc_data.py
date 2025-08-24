#!/usr/bin/env python3
"""
Export SSCS UPC Data for Mapping Validation
Retrieves current UPC structure from SSCS for safe import validation

Created: January 23, 2025
Purpose: Validate UPC mapping requirements before NAXML import
"""

import sys
from pathlib import Path
import csv
import json
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def analyze_current_inventory_structure():
    """Analyze ProcessInventory.csv to understand UPC field structure"""
    print('📊 ANALYZING CURRENT INVENTORY UPC STRUCTURE')
    print('=' * 60)
    
    try:
        # Load ProcessInventory.csv
        print('📁 Loading ProcessInventory.csv...')
        df = pd.read_csv('dabs/ProcessInventory.csv', sep='\t', header=None, on_bad_lines='skip')
        print(f'✅ Loaded {len(df):,} items')
        
        # Filter alcohol items
        alcohol_items = df[df.iloc[:, 5].str.contains('LIQUOR|BEER', na=False, case=False)]
        print(f'🍺 Alcohol items: {len(alcohol_items):,}')
        
        print()
        print('🔍 UPC DATA ANALYSIS:')
        print('-' * 40)
        
        # Analyze UPC structure (assumed to be in column 0)
        upc_analysis = {}
        upc_samples = []
        
        for i, (_, row) in enumerate(alcohol_items.head(20).iterrows()):
            upc = str(row.iloc[0]).strip()
            description = str(row.iloc[1]).strip()
            department = str(row.iloc[5]).strip()
            
            # Analyze UPC format
            if upc and upc != '0':
                upc_length = len(upc)
                if upc_length not in upc_analysis:
                    upc_analysis[upc_length] = 0
                upc_analysis[upc_length] += 1
                
                upc_samples.append({
                    'UPC': upc,
                    'Description': description[:40],
                    'Department': department,
                    'Length': upc_length,
                    'Valid_UPC': len(upc) in [12, 13, 14]  # Standard UPC lengths
                })
        
        print('📊 UPC LENGTH ANALYSIS:')
        for length, count in sorted(upc_analysis.items()):
            status = "✅ STANDARD" if length in [12, 13, 14] else "⚠️  NON-STANDARD"
            print(f'   {length:2d} digits: {count:3d} items {status}')
        
        print()
        print('📋 UPC SAMPLES (First 10 alcohol items):')
        print('-' * 80)
        for i, sample in enumerate(upc_samples[:10], 1):
            valid = "✅" if sample['Valid_UPC'] else "⚠️ "
            print(f'{i:2d}. {valid} {sample["UPC"]:<15} | {sample["Description"]:<35} | {sample["Department"]}')
        
        # Determine if UPCs are valid for SSCS matching
        total_items = len(upc_samples)
        valid_upcs = sum(1 for s in upc_samples if s['Valid_UPC'])
        
        print()
        print('🎯 UPC VALIDITY ASSESSMENT:')
        print(f'   Total analyzed: {total_items}')
        print(f'   Valid UPCs: {valid_upcs} ({valid_upcs/total_items*100:.1f}%)')
        print(f'   Invalid UPCs: {total_items - valid_upcs} ({(total_items-valid_upcs)/total_items*100:.1f}%)')
        
        if valid_upcs / total_items >= 0.95:
            print('   ✅ EXCELLENT: 95%+ valid UPCs - safe for UPC field population')
        elif valid_upcs / total_items >= 0.90:
            print('   ✅ GOOD: 90%+ valid UPCs - proceed with validation')
        else:
            print('   ⚠️  CONCERN: <90% valid UPCs - needs UPC cleanup')
        
        return upc_samples, upc_analysis
        
    except Exception as e:
        print(f'❌ Error analyzing inventory: {e}')
        return [], {}

def create_upc_mapping_recommendations():
    """Create recommendations for NAXML UPC field population"""
    print()
    print('🎯 NAXML UPC FIELD RECOMMENDATIONS:')
    print('=' * 50)
    
    recommendations = [
        {
            'scenario': 'UPCs are valid (12-14 digits)',
            'action': 'Populate both <UPC> and <VendorItemCode> with same UPC',
            'reason': 'Ensures SSCS can match by either field',
            'risk': 'LOW - Standard practice'
        },
        {
            'scenario': 'UPCs are invalid/non-standard',
            'action': 'Use VendorItemCode only, leave <UPC/> empty',
            'reason': 'Avoids UPC validation errors in SSCS',
            'risk': 'MEDIUM - May create new items instead of updating'
        },
        {
            'scenario': 'Mixed valid/invalid UPCs',
            'action': 'Populate <UPC> only for valid UPCs, empty for invalid',
            'reason': 'Maximizes matching while avoiding errors',
            'risk': 'MEDIUM - Complex logic required'
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f'{i}. SCENARIO: {rec["scenario"]}')
        print(f'   ACTION: {rec["action"]}')
        print(f'   REASON: {rec["reason"]}')
        print(f'   RISK: {rec["risk"]}')
        print()

def generate_test_naxml_with_upcs():
    """Generate improved NAXML with proper UPC field population"""
    print('🔧 GENERATING IMPROVED NAXML FORMAT:')
    print('=' * 50)
    
    # Load sample data
    try:
        df = pd.read_csv('dabs/ProcessInventory.csv', sep='\t', header=None, on_bad_lines='skip')
        alcohol_items = df[df.iloc[:, 5].str.contains('LIQUOR|BEER', na=False, case=False)]
        
        # Take first 3 items for example
        sample_items = []
        for _, row in alcohol_items.head(3).iterrows():
            upc = str(row.iloc[0]).strip()
            description = str(row.iloc[1]).strip()
            price = float(row.iloc[4]) if pd.notna(row.iloc[4]) and row.iloc[4] != 0 else 29.99
            
            # Validate UPC
            is_valid_upc = len(upc) in [12, 13, 14] and upc.isdigit()
            
            sample_items.append({
                'upc': upc,
                'description': description,
                'price': price,
                'valid_upc': is_valid_upc
            })
        
        print('📄 IMPROVED NAXML STRUCTURE:')
        print()
        
        for i, item in enumerate(sample_items, 1):
            print(f'ITEM {i}: {item["description"][:30]}...')
            if item['valid_upc']:
                print(f'  ✅ VALID UPC - Populate both fields:')
                print(f'    <VendorItemCode>{item["upc"]}</VendorItemCode>')
                print(f'    <UPC>{item["upc"]}</UPC>')
            else:
                print(f'  ⚠️  INVALID UPC - Use VendorItemCode only:')
                print(f'    <VendorItemCode>{item["upc"]}</VendorItemCode>')
                print(f'    <UPC />')
            print(f'    <VendorListPrice>{item["price"]}</VendorListPrice>')
            print()
        
    except Exception as e:
        print(f'❌ Error generating sample: {e}')

def main():
    print('🎯 HILLS & HOLLOWS LLC - SSCS UPC MAPPING ANALYSIS')
    print('🔍 UPC DATA VALIDATION FOR SAFE NAXML IMPORT')
    print('=' * 70)
    print()
    
    # Analyze current inventory UPC structure
    upc_samples, upc_analysis = analyze_current_inventory_structure()
    
    # Create recommendations
    create_upc_mapping_recommendations()
    
    # Generate improved NAXML format
    generate_test_naxml_with_upcs()
    
    print()
    print('🎯 NEXT STEPS FOR SAFE SSCS IMPORT:')
    print('1. Review UPC validity analysis above')
    print('2. Modify NAXML generator to populate UPC field properly')
    print('3. Test with small batch (3-5 items) in SSCS')
    print('4. Verify SSCS matches existing items vs creating new ones')
    print('5. Proceed with full import only after validation')
    
    print()
    print('⚠️  CRITICAL: Test import behavior with SSCS before full deployment!')
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
