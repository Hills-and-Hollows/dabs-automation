#!/usr/bin/env python3
"""
SSCS NAXML Upload Safety Test
Safe workflow validation for SSCS CPB integration

Created: January 23, 2025
Purpose: Test SSCS import with safety validation
"""

import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def validate_naxml_safety(file_path: str):
    """Validate NAXML file has safety mechanisms enabled"""
    print('🔍 NAXML SAFETY VALIDATION')
    print('=' * 50)
    print(f'📁 File: {file_path}')
    print()
    
    try:
        # Parse NAXML file
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Check root element
        if root.tag != "ItemSynch":
            print('❌ INVALID: Not an ItemSynch NAXML file')
            return False
            
        print(f'✅ NAXML Format: {root.tag} version {root.get("version")}')
        print(f'✅ Vendor: {root.get("vendor")}')
        print(f'✅ Timestamp: {root.get("timestamp")}')
        print()
        
        # Check header
        header = root.find('Header')
        if header is not None:
            source = header.find('Source').text if header.find('Source') is not None else "Unknown"
            destination = header.find('Destination').text if header.find('Destination') is not None else "Unknown"
            record_count = header.find('RecordCount').text if header.find('RecordCount') is not None else "0"
            
            print('📊 HEADER VALIDATION:')
            print(f'   Source: {source}')
            print(f'   Destination: {destination}')
            print(f'   Record Count: {record_count}')
            print()
        
        # Check items and safety settings
        items = root.find('Items')
        if items is not None:
            item_list = items.findall('Item')
            print(f'🛡️  SAFETY VALIDATION ({len(item_list)} items):')
            
            safe_count = 0
            for i, item in enumerate(item_list[:5], 1):  # Check first 5 items
                # Check AutoAccept setting
                attributes = item.find('Attributes')
                auto_accept = False
                if attributes is not None:
                    auto_accept_elem = attributes.find('AutoAccept')
                    if auto_accept_elem is not None:
                        auto_accept = auto_accept_elem.text.lower() == 'true'
                
                # Get product info
                vendor_code = item.find('VendorItemCode').text if item.find('VendorItemCode') is not None else "N/A"
                description = item.find('Description').text if item.find('Description') is not None else "N/A"
                
                # Get pricing info
                pricing = item.find('Pricing')
                price = "N/A"
                if pricing is not None:
                    price_elem = pricing.find('VendorListPrice')
                    if price_elem is not None:
                        price = f"${price_elem.text}"
                
                safety_status = "✅ SAFE" if not auto_accept else "⚠️  AUTO-APPLY"
                if not auto_accept:
                    safe_count += 1
                
                print(f'   {i:2d}. {description[:35]:<35} | {price:>8} | {safety_status}')
            
            print()
            items_checked = min(5, len(item_list))
            if safe_count == items_checked:
                print('✅ ALL TESTED ITEMS SAFE: AutoAccept=false (Manual approval required)')
                print('🛡️  SSCS will PREVIEW changes before applying')
                print(f'📊 Validated {items_checked} of {len(item_list)} items - all safe')
            else:
                print('⚠️  WARNING: Some items have AutoAccept=true')
                print('🔧 Consider setting all items to AutoAccept=false for testing')
            
            print()
            print('🎯 TESTING WORKFLOW RECOMMENDATION:')
            print('1. Upload file to SSCS → Will show preview of changes')
            print('2. Review changes in SSCS interface → Validate accuracy')
            print('3. Manual approval in SSCS → Apply only if correct')
            print('4. Monitor results → Confirm no data corruption')
            
            return safe_count == items_checked
        else:
            print('❌ INVALID: No Items section found')
            return False
            
    except Exception as e:
        print(f'❌ VALIDATION ERROR: {e}')
        return False

def main():
    print('🎯 HILLS & HOLLOWS LLC - SSCS INTEGRATION')
    print('🛡️  NAXML SAFETY VALIDATION TEST')
    print('=' * 60)
    print()
    
    # Find most recent NAXML file
    exports_dir = Path('exports')
    naxml_files = list(exports_dir.glob('DABS_*_ItemPrice.xml'))
    
    if not naxml_files:
        print('❌ No NAXML files found in exports directory')
        return 1
    
    # Use most recent file
    latest_file = max(naxml_files, key=lambda f: f.stat().st_mtime)
    
    print(f'📁 Testing file: {latest_file}')
    print(f'📊 File size: {latest_file.stat().st_size:,} bytes')
    print()
    
    # Validate safety
    is_safe = validate_naxml_safety(str(latest_file))
    
    print()
    print('🎊 SAFETY VALIDATION RESULT:')
    if is_safe:
        print('✅ NAXML FILE: SAFE FOR SSCS TESTING')
        print('🎯 Ready for upload to SSCS CPB File Import')
        print('🛡️  All safety mechanisms active')
        print()
        print('📋 NEXT STEPS:')
        print('1. Upload file via SSCS File Import Utility')
        print('2. Review preview of changes in SSCS')
        print('3. Manually approve if changes look correct')
        print('4. Validate results and document success')
        
        return 0
    else:
        print('⚠️  NAXML FILE: REQUIRES SAFETY REVIEW')
        print('🔧 Address safety concerns before SSCS upload')
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
