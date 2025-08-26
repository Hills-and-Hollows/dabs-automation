#!/usr/bin/env python3
"""
SSCS NAXML Vendor Information Enhancement Script
Zero Tolerance Error Correction for Vendor Fields

This script adds missing required vendor fields to ensure SSCS compliance.
"""

import xml.etree.ElementTree as ET
import argparse
import sys
from datetime import datetime
from pathlib import Path

class VendorInfoEnhancer:
    """Handles vendor information field enhancement"""
    
    def __init__(self):
        self.fields_added = 0
        self.errors_found = []
        
    def enhance_vendor_info(self, xml_file_path: str, output_path: str, 
                           customer_number: str, po_number: str, terms: str) -> bool:
        """
        Add missing vendor information fields
        
        Args:
            xml_file_path: Path to input NAXML file
            output_path: Path for enhanced output file
            customer_number: Customer number (e.g., "6242")
            po_number: Purchase order number
            terms: Payment terms (e.g., "NET30")
            
        Returns:
            bool: True if successful, False if errors
        """
        try:
            # Parse XML file
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Find VendorInfo section
            vendor_info = root.find('VendorInfo')
            if vendor_info is None:
                self.errors_found.append("No VendorInfo section found in XML")
                return False
                
            # Add missing fields
            self._add_required_fields(vendor_info, customer_number, po_number, terms)
            
            # Write enhanced file
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            print(f"✅ Vendor Info Enhancement Complete:")
            print(f"   Fields Added: {self.fields_added}")
            print(f"   Output File: {output_path}")
            
            return True
            
        except Exception as e:
            self.errors_found.append(f"Processing error: {str(e)}")
            return False
            
    def _add_required_fields(self, vendor_info: ET.Element, customer_number: str, 
                           po_number: str, terms: str) -> None:
        """Add missing required vendor fields"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Required fields to add
        required_fields = {
            'DeliveryDate': current_date,
            'PurchaseOrderNumber': po_number,
            'Terms': terms,
            'BackupContactEmail': 'shawn@owenent.com',
            'VendorContactPhone': '(801) 977-6800'
        }
        
        # Add fields if they don't exist
        for field_name, field_value in required_fields.items():
            if vendor_info.find(field_name) is None:
                field_element = ET.SubElement(vendor_info, field_name)
                field_element.text = field_value
                self.fields_added += 1
                print(f"   Added: {field_name} = {field_value}")
                
        # Ensure CustomerNumber is present and correct
        customer_element = vendor_info.find('CustomerNumber')
        if customer_element is None:
            customer_element = ET.SubElement(vendor_info, 'CustomerNumber')
            customer_element.text = customer_number
            self.fields_added += 1
            print(f"   Added: CustomerNumber = {customer_number}")
        elif customer_element.text != customer_number:
            customer_element.text = customer_number
            print(f"   Updated: CustomerNumber = {customer_number}")

def main():
    parser = argparse.ArgumentParser(description='Enhance vendor info in NAXML files')
    parser.add_argument('--input', required=True, help='Input NAXML file path')
    parser.add_argument('--output', help='Output enhanced file path (defaults to input_ENHANCED.xml)')
    parser.add_argument('--customer-number', required=True, help='Customer number (e.g., 6242)')
    parser.add_argument('--po-number', required=True, help='Purchase order number')
    parser.add_argument('--terms', default='NET30', help='Payment terms (default: NET30)')
    
    args = parser.parse_args()
    
    # Set default output path if not provided
    if not args.output:
        input_path = Path(args.input)
        args.output = str(input_path.parent / f"{input_path.stem}_ENHANCED{input_path.suffix}")
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)
        
    # Create output directory if needed
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Execute vendor info enhancement
    enhancer = VendorInfoEnhancer()
    
    print(f"🔧 Starting Vendor Info Enhancement...")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output}")
    print(f"   Customer Number: {args.customer_number}")
    print(f"   PO Number: {args.po_number}")
    print(f"   Terms: {args.terms}")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = enhancer.enhance_vendor_info(args.input, args.output, 
                                         args.customer_number, args.po_number, args.terms)
    
    if success:
        print(f"✅ Vendor Info Enhancement Complete!")
        sys.exit(0)
    else:
        print(f"❌ Vendor Info Enhancement Failed!")
        for error in enhancer.errors_found:
            print(f"   Error: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
