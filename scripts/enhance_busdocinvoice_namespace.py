#!/usr/bin/env python3
"""
Enhance BusDocInvoice with Namespace Declarations
Adds proper namespace and schema declarations per Conexxus specification

This script adds the official Conexxus namespace and schema location
to make the BusDocInvoice even more standards-compliant.
"""

import xml.etree.ElementTree as ET
import argparse
import sys
from datetime import datetime
from pathlib import Path

class BusDocInvoiceNamespaceEnhancer:
    """Add namespace declarations to BusDocInvoice"""
    
    def __init__(self):
        self.enhancements_applied = 0
        self.errors_found = []
        
    def enhance_namespace_declarations(self, input_file: str, output_file: str) -> bool:
        """
        Add namespace declarations to BusDocInvoice XML
        
        Args:
            input_file: Path to input BusDocInvoice XML
            output_file: Path for enhanced output
            
        Returns:
            bool: True if successful, False if errors
        """
        try:
            print(f"🔧 Enhancing BusDocInvoice with Namespace Declarations...")
            print(f"   Authority: Official Conexxus NAXML specification")
            print(f"   Input: {input_file}")
            print(f"   Output: {output_file}")
            print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Parse XML
            tree = ET.parse(input_file)
            root = tree.getroot()
            
            # Add namespace declarations
            self._add_namespace_declarations(root)
            
            # Write enhanced XML
            self._write_enhanced_xml(root, output_file)
            
            print(f"✅ Namespace Enhancement Complete:")
            print(f"   Enhancements Applied: {self.enhancements_applied}")
            print(f"   Output File: {output_file}")
            print(f"   Status: Enhanced standards compliance")
            
            return True
            
        except Exception as e:
            self.errors_found.append(f"Enhancement error: {str(e)}")
            return False
    
    def _add_namespace_declarations(self, root: ET.Element) -> None:
        """Add proper namespace declarations to root element"""
        
        # Add namespace declarations
        root.set('xmlns', 'http://www.naxml.org/Retail-EDI/Vocabulary/2003-10-16')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.set('xsi:schemaLocation', 'http://www.naxml.org/Retail-EDI/Vocabulary/2003-10-16 NAXML-BusDocInvoice15.xsd')
        
        self.enhancements_applied += 3
        print(f"   Added namespace declarations: xmlns, xmlns:xsi, xsi:schemaLocation")
    
    def _write_enhanced_xml(self, root: ET.Element, output_file: str) -> None:
        """Write enhanced XML with proper formatting"""
        
        # Use minidom for better formatting
        from xml.dom import minidom
        
        # Convert ElementTree to string
        rough_string = ET.tostring(root, encoding='utf-8')
        
        # Parse with minidom for pretty printing
        reparsed = minidom.parseString(rough_string)
        
        # Get pretty printed XML
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding='utf-8')
        
        # Write to file
        with open(output_file, 'wb') as f:
            f.write(pretty_xml)

def main():
    parser = argparse.ArgumentParser(description='Enhance BusDocInvoice with namespace declarations')
    parser.add_argument('--input', required=True, help='Input BusDocInvoice XML file')
    parser.add_argument('--output', help='Output enhanced file (defaults to input_ENHANCED.xml)')
    
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
    
    # Execute enhancement
    enhancer = BusDocInvoiceNamespaceEnhancer()
    
    success = enhancer.enhance_namespace_declarations(args.input, args.output)
    
    if success:
        print(f"\n✅ BusDocInvoice Namespace Enhancement Complete!")
        print(f"   Standards compliance improved")
        print(f"   Namespace declarations added")
        print(f"   Ready for formal XML validation")
        sys.exit(0)
    else:
        print(f"\n❌ BusDocInvoice Namespace Enhancement Failed!")
        for error in enhancer.errors_found:
            print(f"   Error: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
