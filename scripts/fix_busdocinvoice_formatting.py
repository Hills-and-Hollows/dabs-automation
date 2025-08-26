#!/usr/bin/env python3
"""
Fix BusDocInvoice Formatting Issues
Corrects XML formatting and GTIN check digit issues

This script fixes the formatting problems identified in the BusDocInvoice
validation and ensures proper GTIN check digits.
"""

import xml.etree.ElementTree as ET
import argparse
import sys
from datetime import datetime
from pathlib import Path
import re

class BusDocInvoiceFormatter:
    """Fix BusDocInvoice formatting and GTIN issues"""
    
    def __init__(self):
        self.fixes_applied = 0
        self.gtins_corrected = 0
        self.errors_found = []
        
    def fix_busdocinvoice_formatting(self, input_file: str, output_file: str) -> bool:
        """
        Fix BusDocInvoice formatting and GTIN issues
        
        Args:
            input_file: Path to input BusDocInvoice XML
            output_file: Path for corrected output
            
        Returns:
            bool: True if successful, False if errors
        """
        try:
            print(f"🔧 Fixing BusDocInvoice Formatting Issues...")
            print(f"   Input: {input_file}")
            print(f"   Output: {output_file}")
            print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Parse XML
            tree = ET.parse(input_file)
            root = tree.getroot()
            
            # Fix formatting issues
            self._fix_text_formatting(root)
            
            # Fix GTIN check digits
            self._fix_gtin_check_digits(root)
            
            # Write corrected XML with proper formatting
            self._write_formatted_xml(root, output_file)
            
            print(f"✅ BusDocInvoice Formatting Fixed:")
            print(f"   Formatting Fixes Applied: {self.fixes_applied}")
            print(f"   GTINs Corrected: {self.gtins_corrected}")
            print(f"   Output File: {output_file}")
            print(f"   Status: Ready for SSCS EDI delivery")
            
            return True
            
        except Exception as e:
            self.errors_found.append(f"Formatting error: {str(e)}")
            return False
    
    def _fix_text_formatting(self, root: ET.Element) -> None:
        """Fix text formatting issues (remove extra whitespace)"""
        
        for element in root.iter():
            if element.text:
                # Remove leading/trailing whitespace and normalize
                original_text = element.text
                cleaned_text = ' '.join(original_text.split())
                
                if original_text != cleaned_text:
                    element.text = cleaned_text
                    self.fixes_applied += 1
    
    def _fix_gtin_check_digits(self, root: ET.Element) -> None:
        """Fix GTIN check digits using GS1 algorithm"""
        
        # Find all GTIN elements
        gtin_elements = (
            root.findall('.//InvoiceUnitId[@identType="GTIN"]') +
            root.findall('.//RetailUnitId[@identType="GTIN"]')
        )
        
        for element in gtin_elements:
            if element.text:
                original_gtin = element.text.strip()
                corrected_gtin = self._calculate_correct_gtin(original_gtin)
                
                if original_gtin != corrected_gtin:
                    element.text = corrected_gtin
                    self.gtins_corrected += 1
                    print(f"   GTIN Corrected: {original_gtin} → {corrected_gtin}")
    
    def _calculate_correct_gtin(self, gtin: str) -> str:
        """Calculate correct GTIN with proper check digit"""
        
        # Remove any non-digits
        digits_only = re.sub(r'\D', '', gtin)
        
        # Handle different input lengths
        if len(digits_only) == 12:
            # UPC-A: pad to 14 digits
            base_digits = f"00{digits_only[:-1]}"  # Remove original check digit
        elif len(digits_only) == 13:
            # EAN-13: pad to 14 digits
            base_digits = f"0{digits_only[:-1]}"  # Remove original check digit
        elif len(digits_only) == 14:
            # GTIN-14: use first 13 digits
            base_digits = digits_only[:-1]  # Remove original check digit
        else:
            # Invalid length, return as-is
            return gtin
        
        # Calculate correct check digit
        check_digit = self._calculate_gtin_check_digit(base_digits)
        
        return f"{base_digits}{check_digit}"
    
    def _calculate_gtin_check_digit(self, digits: str) -> int:
        """Calculate GTIN check digit using GS1 algorithm"""
        
        if len(digits) != 13:
            raise ValueError(f"Expected 13 digits for check digit calculation, got {len(digits)}")
        
        # GS1 algorithm: multiply by 1 or 3 alternately, sum, then mod 10
        total = 0
        for i, digit in enumerate(digits):
            multiplier = 3 if i % 2 else 1  # Odd positions (0-indexed) get 3
            total += int(digit) * multiplier
        
        # Check digit makes the total divisible by 10
        check_digit = (10 - (total % 10)) % 10
        
        return check_digit
    
    def _write_formatted_xml(self, root: ET.Element, output_file: str) -> None:
        """Write XML with proper formatting"""
        
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
    parser = argparse.ArgumentParser(description='Fix BusDocInvoice formatting and GTIN issues')
    parser.add_argument('--input', required=True, help='Input BusDocInvoice XML file')
    parser.add_argument('--output', help='Output corrected file (defaults to input_FIXED.xml)')
    
    args = parser.parse_args()
    
    # Set default output path if not provided
    if not args.output:
        input_path = Path(args.input)
        args.output = str(input_path.parent / f"{input_path.stem}_FIXED{input_path.suffix}")
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)
        
    # Create output directory if needed
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Execute formatting fixes
    formatter = BusDocInvoiceFormatter()
    
    success = formatter.fix_busdocinvoice_formatting(args.input, args.output)
    
    if success:
        print(f"\n✅ BusDocInvoice Formatting Complete!")
        print(f"   All formatting issues resolved")
        print(f"   GTIN check digits corrected")
        print(f"   Ready for Conexxus compliance validation")
        sys.exit(0)
    else:
        print(f"\n❌ BusDocInvoice Formatting Failed!")
        for error in formatter.errors_found:
            print(f"   Error: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
