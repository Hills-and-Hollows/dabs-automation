#!/usr/bin/env python3
"""
SSCS NAXML UPC Formatting Correction Script
Zero Tolerance Error Correction for UPC Fields

This script systematically corrects UPC formatting violations in NAXML files
to ensure 100% SSCS compliance.
"""

import xml.etree.ElementTree as ET
import argparse
import sys
from datetime import datetime
from pathlib import Path

class UPCFormatter:
    """Handles UPC field standardization and correction"""
    
    def __init__(self):
        self.corrections_made = 0
        self.items_processed = 0
        self.errors_found = []
        
    def standardize_upc_fields(self, xml_file_path: str, output_path: str) -> bool:
        """
        Standardize all UPC fields in NAXML file
        
        Args:
            xml_file_path: Path to input NAXML file
            output_path: Path for corrected output file
            
        Returns:
            bool: True if successful, False if errors
        """
        try:
            # Parse XML file
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Process all items
            items = root.find('Items')
            if items is None:
                self.errors_found.append("No Items section found in XML")
                return False
                
            for item in items.findall('Item'):
                self.items_processed += 1
                self._process_item_upc(item)
                
            # Write corrected file
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            print(f"✅ UPC Formatting Complete:")
            print(f"   Items Processed: {self.items_processed}")
            print(f"   Corrections Made: {self.corrections_made}")
            print(f"   Output File: {output_path}")
            
            return True
            
        except Exception as e:
            self.errors_found.append(f"Processing error: {str(e)}")
            return False
            
    def _process_item_upc(self, item: ET.Element) -> None:
        """Process UPC fields for a single item"""
        plu = item.find('PLU')
        plu_code = plu.text if plu is not None else "UNKNOWN"
        
        upc_element = item.find('UPC')
        upc_verified = item.find('UPCVerified')
        
        # Handle empty UPC fields
        if upc_element is not None:
            if not upc_element.text or upc_element.text.strip() == "":
                upc_element.text = "PENDING_LOOKUP"
                self._add_upc_status_fields(item, "REQUIRES_MANUAL_LOOKUP", 
                                          f"Manual UPC lookup required for DABS code {plu_code}")
                self.corrections_made += 1
                
        # Standardize UPCVerified field
        if upc_verified is not None:
            if upc_verified.text not in ["true", "false"]:
                # Handle non-standard values like "medium"
                original_value = upc_verified.text
                upc_verified.text = "false"  # Conservative approach
                
                # Add confidence field for non-boolean values
                confidence_element = ET.SubElement(item, 'UPCConfidence')
                confidence_element.text = original_value.upper()
                
                self.corrections_made += 1
                
        # Ensure all items have UPCStatus field
        if item.find('UPCStatus') is None:
            upc_text = upc_element.text if upc_element is not None else ""
            if upc_text == "PENDING_LOOKUP":
                status = "REQUIRES_MANUAL_LOOKUP"
            elif upc_verified is not None and upc_verified.text == "true":
                status = "VERIFIED"
            else:
                status = "UNVERIFIED"
                
            status_element = ET.SubElement(item, 'UPCStatus')
            status_element.text = status
            self.corrections_made += 1
            
    def _add_upc_status_fields(self, item: ET.Element, status: str, note: str) -> None:
        """Add UPC status and note fields to item"""
        # Add UPCStatus if not exists
        if item.find('UPCStatus') is None:
            status_element = ET.SubElement(item, 'UPCStatus')
            status_element.text = status
            
        # Update or add UPCNote
        note_element = item.find('UPCNote')
        if note_element is None:
            note_element = ET.SubElement(item, 'UPCNote')
        note_element.text = note

def main():
    parser = argparse.ArgumentParser(description='Fix UPC formatting in NAXML files')
    parser.add_argument('--input', required=True, help='Input NAXML file path')
    parser.add_argument('--output', required=True, help='Output corrected file path')
    parser.add_argument('--mode', default='standardize_upc_fields', 
                       help='Correction mode (default: standardize_upc_fields)')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)
        
    # Create output directory if needed
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Execute UPC formatting
    formatter = UPCFormatter()
    
    print(f"🔧 Starting UPC Formatting Correction...")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output}")
    print(f"   Mode: {args.mode}")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = formatter.standardize_upc_fields(args.input, args.output)
    
    if success:
        print(f"✅ UPC Formatting Correction Complete!")
        sys.exit(0)
    else:
        print(f"❌ UPC Formatting Correction Failed!")
        for error in formatter.errors_found:
            print(f"   Error: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
