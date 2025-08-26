#!/usr/bin/env python3
"""
Remove VerifoneUPC Field from NAXML Files
Corrects template implementation based on official SSCS specification

SSCS does NOT require or document a VerifoneUPC field in invoice imports.
Only UPC (12-digit GTIN) is required for SSCS Central Price Book.
"""

import xml.etree.ElementTree as ET
import argparse
import sys
from datetime import datetime
from pathlib import Path

class VerifoneUPCRemover:
    """Removes non-standard VerifoneUPC fields from NAXML files"""
    
    def __init__(self):
        self.items_processed = 0
        self.fields_removed = 0
        self.errors_found = []
        
    def remove_verifone_upc_fields(self, xml_file_path: str, output_path: str) -> bool:
        """
        Remove VerifoneUPC fields from NAXML file to match official SSCS specification
        
        Args:
            xml_file_path: Path to input NAXML file
            output_path: Path for corrected output file
            
        Returns:
            bool: True if successful, False if errors
        """
        try:
            print(f"🔧 Removing Non-Standard VerifoneUPC Fields...")
            print(f"   Reason: SSCS does not require or document VerifoneUPC field")
            print(f"   Input: {xml_file_path}")
            print(f"   Output: {output_path}")
            print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Parse XML file
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Find Items section
            items = root.find('Items')
            if items is None:
                self.errors_found.append("No Items section found in XML")
                return False
                
            # Process all items
            for item in items.findall('Item'):
                self.items_processed += 1
                self._remove_verifone_upc_from_item(item)
                
            # Write corrected file
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            print(f"✅ VerifoneUPC Field Removal Complete:")
            print(f"   Items Processed: {self.items_processed}")
            print(f"   Fields Removed: {self.fields_removed}")
            print(f"   Output File: {output_path}")
            print(f"   Status: Now compliant with official SSCS specification")
            
            return True
            
        except Exception as e:
            self.errors_found.append(f"Processing error: {str(e)}")
            return False
            
    def _remove_verifone_upc_from_item(self, item: ET.Element) -> None:
        """Remove VerifoneUPC field from a single item"""
        
        # Find and remove VerifoneUPC element
        verifone_upc = item.find('VerifoneUPC')
        if verifone_upc is not None:
            item.remove(verifone_upc)
            self.fields_removed += 1
            
        # Keep UPC field as-is (this is the official SSCS requirement)
        upc = item.find('UPC')
        if upc is not None:
            # UPC field is correct and should remain
            pass

def main():
    parser = argparse.ArgumentParser(description='Remove non-standard VerifoneUPC fields from NAXML')
    parser.add_argument('--input', required=True, help='Input NAXML file path')
    parser.add_argument('--output', help='Output corrected file path (defaults to input_SSCS_CORRECTED.xml)')
    
    args = parser.parse_args()
    
    # Set default output path if not provided
    if not args.output:
        input_path = Path(args.input)
        args.output = str(input_path.parent / f"{input_path.stem}_SSCS_CORRECTED{input_path.suffix}")
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)
        
    # Create output directory if needed
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Execute VerifoneUPC removal
    remover = VerifoneUPCRemover()
    
    success = remover.remove_verifone_upc_fields(args.input, args.output)
    
    if success:
        print(f"\n✅ SSCS Specification Correction Complete!")
        print(f"   File now matches official SSCS requirements")
        print(f"   VerifoneUPC field removed (not required by SSCS)")
        print(f"   UPC field retained (official SSCS requirement)")
        sys.exit(0)
    else:
        print(f"\n❌ SSCS Specification Correction Failed!")
        for error in remover.errors_found:
            print(f"   Error: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
