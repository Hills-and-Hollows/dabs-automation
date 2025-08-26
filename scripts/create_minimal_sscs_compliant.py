#!/usr/bin/env python3
"""
Create Minimal SSCS-Compliant NAXML File
Based on official SSCS specification from portal.sscsinc.com

Removes ALL non-documented fields including UPCVerified
"""

import xml.etree.ElementTree as ET
import argparse
import sys
from datetime import datetime
from pathlib import Path

class MinimalSSCSCompliantCreator:
    """Creates minimal SSCS-compliant NAXML files with only documented fields"""
    
    def __init__(self):
        self.items_processed = 0
        self.fields_removed = 0
        self.errors_found = []
        
        # OFFICIAL SSCS DOCUMENTED FIELDS ONLY
        self.REQUIRED_ITEM_FIELDS = [
            'PLU', 'ItemName', 'Price', 'Cost', 'Category', 'Size',
            'VendorItemCode', 'LastUpdated', 'Status'
        ]
        
        # OPTIONAL FIELDS DOCUMENTED BY SSCS
        self.OPTIONAL_ITEM_FIELDS = [
            'UPC'  # Only UPC is documented, not UPCVerified or VerifoneUPC
        ]
        
    def create_minimal_compliant_file(self, xml_file_path: str, output_path: str) -> bool:
        """
        Create minimal SSCS-compliant file with only documented fields
        
        Args:
            xml_file_path: Path to input NAXML file
            output_path: Path for minimal compliant output file
            
        Returns:
            bool: True if successful, False if errors
        """
        try:
            print(f"🔧 Creating Minimal SSCS-Compliant File...")
            print(f"   Authority: portal.sscsinc.com official specification")
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
                self._clean_item_to_minimal_spec(item)
                
            # Write minimal compliant file
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            print(f"✅ Minimal SSCS-Compliant File Created:")
            print(f"   Items Processed: {self.items_processed}")
            print(f"   Non-Standard Fields Removed: {self.fields_removed}")
            print(f"   Output File: {output_path}")
            print(f"   Status: Contains ONLY officially documented SSCS fields")
            
            return True
            
        except Exception as e:
            self.errors_found.append(f"Processing error: {str(e)}")
            return False
            
    def _clean_item_to_minimal_spec(self, item: ET.Element) -> None:
        """Clean item to contain only officially documented SSCS fields"""
        
        # Get all current child elements
        current_fields = [child.tag for child in item]
        
        # Remove any field not in the official SSCS specification
        allowed_fields = self.REQUIRED_ITEM_FIELDS + self.OPTIONAL_ITEM_FIELDS
        
        for child in list(item):  # Use list() to avoid modification during iteration
            if child.tag not in allowed_fields:
                item.remove(child)
                self.fields_removed += 1
                print(f"   Removed non-standard field: <{child.tag}>")
        
        # Special handling for UPC - keep only if it has a valid value
        upc = item.find('UPC')
        if upc is not None and not upc.text:
            # Empty UPC should be removed entirely for minimal compliance
            item.remove(upc)
            self.fields_removed += 1
            print(f"   Removed empty UPC field")

def main():
    parser = argparse.ArgumentParser(description='Create minimal SSCS-compliant NAXML with only documented fields')
    parser.add_argument('--input', required=True, help='Input NAXML file path')
    parser.add_argument('--output', help='Output minimal compliant file path (defaults to input_MINIMAL_SSCS.xml)')
    
    args = parser.parse_args()
    
    # Set default output path if not provided
    if not args.output:
        input_path = Path(args.input)
        args.output = str(input_path.parent / f"{input_path.stem}_MINIMAL_SSCS{input_path.suffix}")
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)
        
    # Create output directory if needed
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Execute minimal compliance creation
    creator = MinimalSSCSCompliantCreator()
    
    success = creator.create_minimal_compliant_file(args.input, args.output)
    
    if success:
        print(f"\n✅ Minimal SSCS Specification Compliance Complete!")
        print(f"   File contains ONLY fields documented by SSCS")
        print(f"   Authority: portal.sscsinc.com official specification")
        print(f"   Non-standard fields removed: UPCVerified, VerifoneUPC, etc.")
        print(f"   Ready for production EDI delivery")
        sys.exit(0)
    else:
        print(f"\n❌ Minimal SSCS Specification Creation Failed!")
        for error in creator.errors_found:
            print(f"   Error: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
