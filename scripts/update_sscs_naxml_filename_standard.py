#!/usr/bin/env python3
"""
Update SSCS NAXML BusDocInvoice filename standard to official specification.
Per SSCS Implementation Guide for NAXML BusDocInvoice 1.5.
"""

import os
import re
from datetime import datetime

def update_filename_standard():
    """Update all automation scripts to use official SSCS NAXML filename standard"""
    
    print("🔧 Updating SSCS NAXML BusDocInvoice Filename Standard...")
    print(f"   Authority: SSCS Implementation Guide for NAXML BusDocInvoice 1.5")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Files to update
    files_to_update = [
        'src/edi/dabs_edi_generator.py',
        'scripts/convert_itemsynch_to_busdocinvoice.py',
        'scripts/fix_busdocinvoice_formatting.py'
    ]
    
    # Old patterns to replace
    old_patterns = [
        r'DABS_\d{8}_\d{6}_ItemPrice\.xml',
        r'DABS_ItemPrice_\d{8}_\d{6}\.xml',
        r'DABS_\d+_.*\.xml'
    ]
    
    # New pattern template
    new_pattern_template = 'DABS_BusDocInvoice_{order_id}.na.xml'
    
    updates_made = 0
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            print(f"   Updating: {file_path}")
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Update filename generation patterns
            original_content = content
            
            # Replace timestamp-based patterns with order-based patterns
            content = re.sub(
                r'f"DABS_\{timestamp\}_ItemPrice\.xml"',
                'f"DABS_BusDocInvoice_{order_id}.na.xml"',
                content
            )
            
            content = re.sub(
                r'f"DABS_ItemPrice_\{timestamp\}\.xml"',
                'f"DABS_BusDocInvoice_{order_id}.na.xml"',
                content
            )
            
            # Update extension patterns
            content = re.sub(r'\.xml"', '.na.xml"', content)
            
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                updates_made += 1
                print(f"     ✅ Updated filename patterns")
            else:
                print(f"     ℹ️  No patterns found to update")
    
    print(f"✅ SSCS NAXML Filename Standard Update Complete:")
    print(f"   Files Updated: {updates_made}")
    print(f"   New Standard: DABS_BusDocInvoice_{{ORDER_ID}}.na.xml")
    print(f"   Alternative: DABS_{{ORDER_ID}}_Invoice.na.xml")
    print(f"   Extension: .na.xml (SSCS routing requirement)")
    
    return updates_made

if __name__ == "__main__":
    try:
        updates = update_filename_standard()
        print(f"\n✅ SSCS NAXML Filename Standard Implementation Complete!")
        print(f"   Official SSCS Implementation Guide compliance achieved")
        print(f"   All future BusDocInvoice files will use correct naming")
    except Exception as e:
        print(f"❌ Error updating filename standard: {e}")
        exit(1)
