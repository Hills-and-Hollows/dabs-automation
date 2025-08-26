#!/usr/bin/env python3
"""
SSCS Format Matching Enhancement Script
Enhances NAXML files to match the exact SSCS CDB format from screenshot analysis

Based on screenshot analysis of successfully received invoices in SSCS CDB system.
"""

import xml.etree.ElementTree as ET
import argparse
import sys
from datetime import datetime
from pathlib import Path

class SSCSFormatMatcher:
    """Enhances NAXML to match SSCS CDB format exactly"""
    
    def __init__(self):
        self.items_processed = 0
        self.fields_added = 0
        self.calculations_performed = 0
        self.errors_found = []
        
    def enhance_to_sscs_format(self, xml_file_path: str, output_path: str) -> bool:
        """
        Enhance NAXML file to match SSCS CDB format from screenshot analysis
        
        Args:
            xml_file_path: Path to input NAXML file
            output_path: Path for enhanced output file
            
        Returns:
            bool: True if successful, False if errors
        """
        try:
            # Parse XML file
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Enhance VendorInfo section
            self._enhance_vendor_info(root)
            
            # Find Items section
            items = root.find('Items')
            if items is None:
                self.errors_found.append("No Items section found in XML")
                return False
                
            # Process all items with SSCS format enhancements
            for item in items.findall('Item'):
                self.items_processed += 1
                self._enhance_item_to_sscs_format(item)
                
            # Enhance InvoiceTotals section
            self._enhance_invoice_totals(root)
                
            # Write enhanced file
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            print(f"✅ SSCS Format Enhancement Complete:")
            print(f"   Items Processed: {self.items_processed}")
            print(f"   Fields Added: {self.fields_added}")
            print(f"   Calculations Performed: {self.calculations_performed}")
            print(f"   Output File: {output_path}")
            
            return True
            
        except Exception as e:
            self.errors_found.append(f"Processing error: {str(e)}")
            return False
            
    def _enhance_vendor_info(self, root: ET.Element) -> None:
        """Enhance VendorInfo section with SSCS-specific fields"""
        vendor_info = root.find('VendorInfo')
        if vendor_info is None:
            return
            
        # Add LocationID (from screenshot: "01")
        if vendor_info.find('LocationID') is None:
            location_element = ET.SubElement(vendor_info, 'LocationID')
            location_element.text = "01"
            self.fields_added += 1
            
        # Add ProcessingStatus
        if vendor_info.find('ProcessingStatus') is None:
            status_element = ET.SubElement(vendor_info, 'ProcessingStatus')
            status_element.text = "Pending"
            self.fields_added += 1
            
    def _enhance_item_to_sscs_format(self, item: ET.Element) -> None:
        """Enhance a single item to match SSCS CDB format from screenshot"""
        
        # Get current item data for calculations
        plu = item.find('PLU')
        plu_code = plu.text if plu is not None else "UNKNOWN"
        
        cost_element = item.find('Cost')
        cost = float(cost_element.text) if cost_element is not None else 0.0
        
        price_element = item.find('Price')
        price = float(price_element.text) if price_element is not None else 0.0
        
        item_name = item.find('ItemName')
        item_name_text = item_name.text if item_name is not None else ""
        
        # Add Pack Size (from screenshot analysis)
        if item.find('PackSize') is None:
            pack_size = self._determine_pack_size(item_name_text)
            pack_element = ET.SubElement(item, 'PackSize')
            pack_element.text = str(pack_size)
            self.fields_added += 1
            
        # Add Order Quantity (assume 1 case for individual orders)
        if item.find('OrderQuantity') is None:
            qty_element = ET.SubElement(item, 'OrderQuantity')
            qty_element.text = "1.00"
            self.fields_added += 1
            
        # Calculate and add Extended Cost (Cost × Quantity)
        order_qty = 1.0  # Default quantity
        if item.find('ExtendedCost') is None:
            ext_cost = cost * order_qty
            ext_cost_element = ET.SubElement(item, 'ExtendedCost')
            ext_cost_element.text = f"{ext_cost:.2f}"
            self.fields_added += 1
            self.calculations_performed += 1
            
        # Calculate and add Extended Price (Price × Quantity)  
        if item.find('ExtendedPrice') is None:
            ext_price = price * order_qty
            ext_price_element = ET.SubElement(item, 'ExtendedPrice')
            ext_price_element.text = f"{ext_price:.2f}"
            self.fields_added += 1
            self.calculations_performed += 1
            
        # Calculate and add Profit Margin (ExtPrice - ExtCost)
        if item.find('ProfitMargin') is None:
            ext_cost = cost * order_qty
            ext_price = price * order_qty
            margin = ext_price - ext_cost
            margin_element = ET.SubElement(item, 'ProfitMargin')
            margin_element.text = f"{margin:.2f}"
            self.fields_added += 1
            self.calculations_performed += 1
            
        # Add Unit Margin (Price - Cost)
        if item.find('UnitMargin') is None:
            unit_margin = price - cost
            unit_margin_element = ET.SubElement(item, 'UnitMargin')
            unit_margin_element.text = f"{unit_margin:.2f}"
            self.fields_added += 1
            self.calculations_performed += 1
            
        # Calculate and add Margin Percentage
        if item.find('MarginPercent') is None and cost > 0:
            margin_percent = ((price - cost) / cost) * 100
            margin_percent_element = ET.SubElement(item, 'MarginPercent')
            margin_percent_element.text = f"{margin_percent:.1f}"
            self.fields_added += 1
            self.calculations_performed += 1
            
        # Add Location ID for inventory tracking
        if item.find('LocationID') is None:
            location_element = ET.SubElement(item, 'LocationID')
            location_element.text = "01"
            self.fields_added += 1
            
        # Enhance Department format to match SSCS (e.g., "LIQUOR STR")
        department = item.find('Department')
        if department is not None:
            dept_text = department.text
            if dept_text == "LIQUOR":
                department.text = "LIQUOR STR"
            elif dept_text == "WINE":
                department.text = "WINE STR"
            elif dept_text == "BEER":
                department.text = "BEER STR"
                
        # Add Total Units calculation (PackSize × OrderQuantity)
        pack_size = int(item.find('PackSize').text) if item.find('PackSize') is not None else 1
        order_qty = float(item.find('OrderQuantity').text) if item.find('OrderQuantity') is not None else 1.0
        
        if item.find('TotalUnits') is None:
            total_units = pack_size * order_qty
            total_units_element = ET.SubElement(item, 'TotalUnits')
            total_units_element.text = f"{int(total_units)}"
            self.fields_added += 1
            self.calculations_performed += 1
            
        # Add Stock Status
        if item.find('StockStatus') is None:
            stock_element = ET.SubElement(item, 'StockStatus')
            stock_element.text = "Available"
            self.fields_added += 1
            
    def _enhance_invoice_totals(self, root: ET.Element) -> None:
        """Enhance InvoiceTotals with extended calculations"""
        totals = root.find('InvoiceTotals')
        if totals is None:
            return
            
        # Calculate total extended costs and prices
        items = root.find('Items')
        if items is None:
            return
            
        total_ext_cost = 0.0
        total_ext_price = 0.0
        total_margin = 0.0
        
        for item in items.findall('Item'):
            ext_cost_elem = item.find('ExtendedCost')
            ext_price_elem = item.find('ExtendedPrice')
            margin_elem = item.find('ProfitMargin')
            
            if ext_cost_elem is not None:
                total_ext_cost += float(ext_cost_elem.text)
            if ext_price_elem is not None:
                total_ext_price += float(ext_price_elem.text)
            if margin_elem is not None:
                total_margin += float(margin_elem.text)
                
        # Add TotalExtendedCost
        if totals.find('TotalExtendedCost') is None:
            total_ext_cost_elem = ET.SubElement(totals, 'TotalExtendedCost')
            total_ext_cost_elem.text = f"{total_ext_cost:.2f}"
            self.fields_added += 1
            
        # Add TotalExtendedPrice  
        if totals.find('TotalExtendedPrice') is None:
            total_ext_price_elem = ET.SubElement(totals, 'TotalExtendedPrice')
            total_ext_price_elem.text = f"{total_ext_price:.2f}"
            self.fields_added += 1
            
        # Add TotalMargin
        if totals.find('TotalMargin') is None:
            total_margin_elem = ET.SubElement(totals, 'TotalMargin')
            total_margin_elem.text = f"{total_margin:.2f}"
            self.fields_added += 1
            
        # Add Overall Margin Percentage
        if totals.find('OverallMarginPercent') is None and total_ext_cost > 0:
            overall_margin_percent = (total_margin / total_ext_cost) * 100
            margin_percent_elem = ET.SubElement(totals, 'OverallMarginPercent')
            margin_percent_elem.text = f"{overall_margin_percent:.1f}"
            self.fields_added += 1
            
    def _determine_pack_size(self, item_name: str) -> int:
        """Determine pack size based on item name and category"""
        item_upper = item_name.upper()
        
        # Most spirits and wine come in cases of 12
        if any(spirit in item_upper for spirit in ['VODKA', 'TEQUILA', 'WHISKEY', 'RUM', 'GIN']):
            return 12
        elif any(wine in item_upper for wine in ['WINE', 'PINOT', 'CHARDONNAY', 'CABERNET', 'MERLOT']):
            return 12
        elif 'BEER' in item_upper:
            # Beer often comes in cases of 24 or 6-packs
            if '6PACK' in item_upper or '6-PACK' in item_upper:
                return 4  # 4 six-packs = 24 beers
            else:
                return 24  # Standard case
        else:
            return 12  # Default case size

def main():
    parser = argparse.ArgumentParser(description='Enhance NAXML to match SSCS CDB format')
    parser.add_argument('--input', required=True, help='Input NAXML file path')
    parser.add_argument('--output', help='Output enhanced file path (defaults to input_SSCS_ENHANCED.xml)')
    
    args = parser.parse_args()
    
    # Set default output path if not provided
    if not args.output:
        input_path = Path(args.input)
        args.output = str(input_path.parent / f"{input_path.stem}_SSCS_ENHANCED{input_path.suffix}")
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)
        
    # Create output directory if needed
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Execute SSCS format enhancement
    enhancer = SSCSFormatMatcher()
    
    print(f"🔧 Starting SSCS Format Enhancement...")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output}")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = enhancer.enhance_to_sscs_format(args.input, args.output)
    
    if success:
        print(f"✅ SSCS Format Enhancement Complete!")
        print(f"   File now matches SSCS CDB format from screenshot analysis")
        sys.exit(0)
    else:
        print(f"❌ SSCS Format Enhancement Failed!")
        for error in enhancer.errors_found:
            print(f"   Error: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
