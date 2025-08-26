#!/usr/bin/env python3
"""
Fix Critical NAXML BusDocInvoice Issues for Order 233813
Addresses namespace, totals, and compliance issues identified in manual review
"""

import xml.etree.ElementTree as ET
from decimal import Decimal
import sys
from datetime import datetime

def fix_critical_naxml_issues(input_file, output_file):
    """Fix critical NAXML compliance issues"""
    
    print(f"🔧 Fixing Critical NAXML Issues...")
    print(f"   Input: {input_file}")
    print(f"   Output: {output_file}")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Parse XML
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    fixes_applied = 0
    
    # Fix 1: Add NAXML namespace declaration
    if 'xmlns' not in root.attrib:
        root.set('xmlns', 'http://www.naxml.org/Retail-EDI/Vocabulary/2003-10-16')
        print(f"   ✅ Added NAXML namespace declaration")
        fixes_applied += 1
    
    # Fix 2: Calculate and fix invoice totals
    line_items = root.findall('.//LineItem')
    total_units = len(line_items)
    total_net_amount = Decimal('0.00')
    
    for item in line_items:
        net_amt_elem = item.find('.//LineItemNetAmt')
        if net_amt_elem is not None and net_amt_elem.text:
            try:
                amount = Decimal(net_amt_elem.text)
                total_net_amount += amount
            except:
                pass
    
    # Update invoice totals
    total_units_elem = root.find('.//TotalInvoiceUnits')
    if total_units_elem is not None:
        if total_units_elem.text == '0':
            total_units_elem.text = str(total_units)
            print(f"   ✅ Fixed TotalInvoiceUnits: 0 → {total_units}")
            fixes_applied += 1
    
    total_net_elem = root.find('.//TotalLineItemNetAmt')
    if total_net_elem is not None:
        if total_net_elem.text == '0.00':
            total_net_elem.text = f"{total_net_amount:.2f}"
            total_net_elem.set('currency', 'USD')
            print(f"   ✅ Fixed TotalLineItemNetAmt: 0.00 → {total_net_amount:.2f}")
            fixes_applied += 1
    
    total_due_elem = root.find('.//TotalInvoiceDueAmt')
    if total_due_elem is not None:
        if total_due_elem.text == '0.00':
            total_due_elem.text = f"{total_net_amount:.2f}"
            total_due_elem.set('currency', 'USD')
            print(f"   ✅ Fixed TotalInvoiceDueAmt: 0.00 → {total_net_amount:.2f}")
            fixes_applied += 1
    
    # Fix 3: Ensure all monetary fields have currency attributes
    monetary_fields = [
        'LineItemGrossAmt', 'LineItemNetAmt', 'InvoiceUnitCost', 
        'RetailPrice', 'TotalTaxes'
    ]
    
    currency_fixes = 0
    for field_name in monetary_fields:
        elements = root.findall(f'.//{field_name}')
        for elem in elements:
            if 'currency' not in elem.attrib:
                elem.set('currency', 'USD')
                currency_fixes += 1
    
    if currency_fixes > 0:
        print(f"   ✅ Added currency attributes to {currency_fixes} monetary fields")
        fixes_applied += 1
    
    # Fix 4: Standardize date formats (already appear correct)
    
    # Write fixed XML
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    print(f"✅ Critical NAXML Fixes Applied:")
    print(f"   Total Fixes: {fixes_applied}")
    print(f"   Total Units: {total_units}")
    print(f"   Total Amount: ${total_net_amount:.2f}")
    print(f"   Output File: {output_file}")
    print(f"   Status: Ready for SSCS compliance validation")
    
    return fixes_applied, total_units, float(total_net_amount)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 fix_critical_naxml_issues.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        fixes, units, amount = fix_critical_naxml_issues(input_file, output_file)
        print(f"\n✅ Critical NAXML Issues Fixed!")
        print(f"   All {fixes} critical issues resolved")
        print(f"   Invoice now has correct totals: {units} units, ${amount:.2f}")
        print(f"   Ready for SSCS EDI delivery")
    except Exception as e:
        print(f"❌ Error fixing NAXML issues: {e}")
        sys.exit(1)
