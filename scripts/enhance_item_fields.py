#!/usr/bin/env python3
"""
SSCS NAXML Item Field Enhancement Script
Zero Tolerance Error Correction for Item-Level Fields

This script adds missing required item-level fields for strict SSCS compliance.
"""

import xml.etree.ElementTree as ET
import argparse
import sys
from datetime import datetime
from pathlib import Path

class ItemFieldEnhancer:
    """Handles item-level field enhancement"""
    
    def __init__(self):
        self.items_processed = 0
        self.fields_added = 0
        self.errors_found = []
        
    def enhance_item_fields(self, xml_file_path: str, output_path: str, 
                           add_department: bool = True, add_tax_info: bool = True,
                           add_case_info: bool = True, add_alcohol_content: bool = True) -> bool:
        """
        Add missing item-level fields
        
        Args:
            xml_file_path: Path to input NAXML file
            output_path: Path for enhanced output file
            add_department: Add Department field
            add_tax_info: Add Taxable field
            add_case_info: Add case-related fields
            add_alcohol_content: Add alcohol content for spirits/wine/beer
            
        Returns:
            bool: True if successful, False if errors
        """
        try:
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
                self._enhance_single_item(item, add_department, add_tax_info, 
                                        add_case_info, add_alcohol_content)
                
            # Write enhanced file
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            print(f"✅ Item Field Enhancement Complete:")
            print(f"   Items Processed: {self.items_processed}")
            print(f"   Fields Added: {self.fields_added}")
            print(f"   Output File: {output_path}")
            
            return True
            
        except Exception as e:
            self.errors_found.append(f"Processing error: {str(e)}")
            return False
            
    def _enhance_single_item(self, item: ET.Element, add_department: bool, 
                           add_tax_info: bool, add_case_info: bool, 
                           add_alcohol_content: bool) -> None:
        """Enhance a single item with missing fields"""
        
        # Get item information for context
        plu = item.find('PLU')
        plu_code = plu.text if plu is not None else "UNKNOWN"
        
        category = item.find('Category')
        category_text = category.text if category is not None else "UNKNOWN"
        
        item_name = item.find('ItemName')
        item_name_text = item_name.text if item_name is not None else "UNKNOWN"
        
        # Add Department field
        if add_department and item.find('Department') is None:
            department = self._determine_department(category_text, item_name_text)
            dept_element = ET.SubElement(item, 'Department')
            dept_element.text = department
            self.fields_added += 1
            
        # Add Taxable field
        if add_tax_info and item.find('Taxable') is None:
            taxable_element = ET.SubElement(item, 'Taxable')
            taxable_element.text = "true"  # All alcohol is taxable
            self.fields_added += 1
            
        # Add case-related fields
        if add_case_info:
            if item.find('MinimumOrderQuantity') is None:
                min_qty_element = ET.SubElement(item, 'MinimumOrderQuantity')
                min_qty_element.text = "1"
                self.fields_added += 1
                
            if item.find('CaseSize') is None:
                case_size_element = ET.SubElement(item, 'CaseSize')
                case_size_element.text = "1"  # Individual bottles
                self.fields_added += 1
                
            if item.find('WeightPerUnit') is None:
                weight_element = ET.SubElement(item, 'WeightPerUnit')
                weight = self._estimate_weight(item_name_text)
                weight_element.text = str(weight)
                self.fields_added += 1
                
        # Add alcohol content
        if add_alcohol_content and item.find('AlcoholContent') is None:
            alcohol_content = self._determine_alcohol_content(category_text, item_name_text)
            if alcohol_content:
                alcohol_element = ET.SubElement(item, 'AlcoholContent')
                alcohol_element.text = str(alcohol_content)
                self.fields_added += 1
                
        # Add age restriction
        if item.find('AgeRestricted') is None:
            age_element = ET.SubElement(item, 'AgeRestricted')
            age_element.text = "true"  # All alcohol is age restricted
            self.fields_added += 1
            
        # Add product classification
        if item.find('ProductClassification') is None:
            class_element = ET.SubElement(item, 'ProductClassification')
            class_element.text = "ALCOHOLIC_BEVERAGE"
            self.fields_added += 1
            
        # Add regulatory category
        if item.find('RegulatoryCategory') is None:
            reg_element = ET.SubElement(item, 'RegulatoryCategory')
            reg_element.text = self._determine_regulatory_category(category_text)
            self.fields_added += 1
            
    def _determine_department(self, category: str, item_name: str) -> str:
        """Determine department based on category and item name"""
        category_upper = category.upper()
        item_upper = item_name.upper()
        
        if 'SPIRITS' in category_upper or 'VODKA' in item_upper or 'WHISKEY' in item_upper or 'TEQUILA' in item_upper:
            return "LIQUOR"
        elif 'WINE' in category_upper or 'PINOT' in item_upper or 'CHARDONNAY' in item_upper:
            return "WINE"
        elif 'BEER' in category_upper or 'IPA' in item_upper or 'LAGER' in item_upper:
            return "BEER"
        else:
            return "LIQUOR"  # Default for unknown
            
    def _determine_alcohol_content(self, category: str, item_name: str) -> float:
        """Determine alcohol content based on category and item name"""
        category_upper = category.upper()
        item_upper = item_name.upper()
        
        if 'SPIRITS' in category_upper:
            return 40.0  # Standard spirits ABV
        elif 'WINE' in category_upper:
            return 12.5  # Standard wine ABV
        elif 'BEER' in category_upper:
            return 5.0   # Standard beer ABV
        else:
            return 40.0  # Default to spirits
            
    def _estimate_weight(self, item_name: str) -> float:
        """Estimate weight based on bottle size in item name"""
        item_upper = item_name.upper()
        
        if '1750ML' in item_upper or '1.75L' in item_upper:
            return 1.75  # kg
        elif '1000ML' in item_upper or '1L' in item_upper:
            return 1.0   # kg
        elif '750ML' in item_upper:
            return 0.75  # kg
        elif '500ML' in item_upper:
            return 0.5   # kg
        elif '473ML' in item_upper:
            return 0.473 # kg
        else:
            return 0.75  # Default to 750ml equivalent
            
    def _determine_regulatory_category(self, category: str) -> str:
        """Determine regulatory category for Utah compliance"""
        category_upper = category.upper()
        
        if 'SPIRITS' in category_upper:
            return "DISTILLED_SPIRITS"
        elif 'WINE' in category_upper:
            return "WINE"
        elif 'BEER' in category_upper:
            return "BEER"
        else:
            return "DISTILLED_SPIRITS"  # Default

def main():
    parser = argparse.ArgumentParser(description='Enhance item fields in NAXML files')
    parser.add_argument('--input', required=True, help='Input NAXML file path')
    parser.add_argument('--output', help='Output enhanced file path (defaults to input_ITEM_ENHANCED.xml)')
    parser.add_argument('--add-department', action='store_true', default=True, help='Add Department field')
    parser.add_argument('--add-tax-info', action='store_true', default=True, help='Add Taxable field')
    parser.add_argument('--add-case-info', action='store_true', default=True, help='Add case-related fields')
    parser.add_argument('--add-alcohol-content', action='store_true', default=True, help='Add alcohol content')
    
    args = parser.parse_args()
    
    # Set default output path if not provided
    if not args.output:
        input_path = Path(args.input)
        args.output = str(input_path.parent / f"{input_path.stem}_ITEM_ENHANCED{input_path.suffix}")
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)
        
    # Create output directory if needed
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Execute item field enhancement
    enhancer = ItemFieldEnhancer()
    
    print(f"🔧 Starting Item Field Enhancement...")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output}")
    print(f"   Add Department: {args.add_department}")
    print(f"   Add Tax Info: {args.add_tax_info}")
    print(f"   Add Case Info: {args.add_case_info}")
    print(f"   Add Alcohol Content: {args.add_alcohol_content}")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = enhancer.enhance_item_fields(args.input, args.output, 
                                         args.add_department, args.add_tax_info,
                                         args.add_case_info, args.add_alcohol_content)
    
    if success:
        print(f"✅ Item Field Enhancement Complete!")
        sys.exit(0)
    else:
        print(f"❌ Item Field Enhancement Failed!")
        for error in enhancer.errors_found:
            print(f"   Error: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
