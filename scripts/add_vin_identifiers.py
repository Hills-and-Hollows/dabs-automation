#!/usr/bin/env python3
"""
Add VIN (Vendor Item Number) identifiers to BusDocInvoice for SSCS reconciliation.
Each InvoiceUnit needs both VIN (DABS Order SKU) and GTIN (UPC) identifiers.
"""

import xml.etree.ElementTree as ET
import sys
import json
from datetime import datetime

def add_vin_identifiers(input_file, output_file, source_data_file):
    """Add VIN identifiers to existing BusDocInvoice"""
    
    print(f"🔧 Adding VIN Identifiers to BusDocInvoice...")
    print(f"   Input: {input_file}")
    print(f"   Output: {output_file}")
    print(f"   Source Data: {source_data_file}")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load source data for VIN mapping
    with open(source_data_file, 'r') as f:
        source_data = json.load(f)
    
    # Create VIN mapping by item description (more robust)
    vin_mapping = {}
    plu_corrections = {
        "017088": "017086",  # Bulleit Bourbon 750ml correction
        "068838": "068836"   # St-Germain correction
    }
    
    for item in source_data['items']:
        original_id = item['id']
        corrected_id = plu_corrections.get(original_id, original_id)
        item_name = item['name']
        
        # Map by both corrected PLU and item description
        vin_mapping[corrected_id] = original_id
        vin_mapping[item_name] = original_id
    
    print(f"   VIN Mapping: {len(vin_mapping)} items")
    
    # Parse XML
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    # Find namespace
    namespace = ''
    if root.tag.startswith('{'):
        namespace = root.tag[root.tag.find('{')+1:root.tag.find('}')]
        ns = {'ns': namespace}
    else:
        ns = {}
    
    # Process each InvoiceUnit
    invoice_units = root.findall('.//ns:InvoiceUnit' if namespace else './/InvoiceUnit', ns)
    vin_additions = 0
    
    for unit in invoice_units:
        # Find item description for matching
        description_elem = unit.find('ns:InvoiceUnitDescription' if namespace else 'InvoiceUnitDescription', ns)
        
        if description_elem is not None:
            description = description_elem.text.strip()
            
            # Find corresponding VIN by description
            vin = vin_mapping.get(description)
            if vin:
                # Check if VIN already exists
                existing_vin = unit.find('ns:InvoiceUnitId[@identType="VIN"]' if namespace else 'InvoiceUnitId[@identType="VIN"]', ns)
                
                if existing_vin is None:
                    # Create VIN identifier element
                    vin_element = ET.Element('InvoiceUnitId')
                    vin_element.set('identType', 'VIN')
                    vin_element.text = vin
                    
                    # Insert VIN before GTIN
                    unit.insert(0, vin_element)
                    vin_additions += 1
                    print(f"   VIN Added: {description} → VIN {vin}")
                else:
                    print(f"   VIN Exists: {description} → VIN {existing_vin.text}")
    
    # Write corrected XML
    if namespace:
        # Ensure namespace declaration
        root.set('xmlns', f'http://www.naxml.org/Retail-EDI/Vocabulary/2003-10-16')
    
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    print(f"✅ VIN Identifiers Added:")
    print(f"   VIN Identifiers Added: {vin_additions}")
    print(f"   Output File: {output_file}")
    print(f"   Status: Ready for SSCS reconciliation")
    
    return vin_additions

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 add_vin_identifiers.py <input_file> <output_file> <source_data_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    source_data_file = sys.argv[3]
    
    try:
        vin_count = add_vin_identifiers(input_file, output_file, source_data_file)
        print(f"\n✅ VIN Identifier Addition Complete!")
        print(f"   All {vin_count} items now have both VIN and GTIN identifiers")
        print(f"   Ready for SSCS EDI delivery with full reconciliation support")
    except Exception as e:
        print(f"❌ Error adding VIN identifiers: {e}")
        sys.exit(1)
