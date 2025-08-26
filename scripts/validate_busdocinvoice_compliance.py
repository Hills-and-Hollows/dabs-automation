#!/usr/bin/env python3
"""
Validate Conexxus NAXML BusDocInvoice Compliance
Validates against official Conexxus specification for SSCS compatibility

This validator checks the BusDocInvoice format against the official
Conexxus NAXML specification that SSCS uses for invoice processing.
"""

import xml.etree.ElementTree as ET
import argparse
import sys
from datetime import datetime
import re

class BusDocInvoiceValidator:
    """Validate Conexxus NAXML BusDocInvoice format"""
    
    def __init__(self):
        self.validation_results = {
            'structure': {'passed': 0, 'failed': 0, 'errors': []},
            'transmission': {'passed': 0, 'failed': 0, 'errors': []},
            'parties': {'passed': 0, 'failed': 0, 'errors': []},
            'invoice_header': {'passed': 0, 'failed': 0, 'errors': []},
            'line_items': {'passed': 0, 'failed': 0, 'errors': []},
            'invoice_summary': {'passed': 0, 'failed': 0, 'errors': []},
            'gtin_format': {'passed': 0, 'failed': 0, 'errors': []}
        }
        
    def validate_busdocinvoice(self, xml_file: str) -> bool:
        """
        Validate BusDocInvoice XML against Conexxus specification
        
        Args:
            xml_file: Path to BusDocInvoice XML file
            
        Returns:
            bool: True if fully compliant, False if errors found
        """
        try:
            print(f"🔍 CONEXXUS BUSDOCINVOICE COMPLIANCE VALIDATION")
            print(f"============================================================")
            print(f"Authority: Official Conexxus NAXML BusDocInvoice specification")
            print(f"Input File: {xml_file}")
            print(f"Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"============================================================")
            
            # Parse XML
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Run validation checks
            print(f"\n🔍 Validating Document Structure...")
            self._validate_document_structure(root)
            
            print(f"🔍 Validating TransmissionHeader...")
            self._validate_transmission_header(root)
            
            print(f"🔍 Validating Parties Section...")
            self._validate_parties_section(root)
            
            print(f"🔍 Validating Invoice Header...")
            self._validate_invoice_header(root)
            
            print(f"🔍 Validating Line Items...")
            self._validate_line_items(root)
            
            print(f"🔍 Validating Invoice Summary...")
            self._validate_invoice_summary(root)
            
            print(f"🔍 Validating GTIN Format...")
            self._validate_gtin_format(root)
            
            # Generate report
            return self._generate_compliance_report()
            
        except ET.ParseError as e:
            print(f"❌ XML Parse Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Validation Error: {e}")
            return False
    
    def _validate_document_structure(self, root: ET.Element) -> None:
        """Validate basic document structure"""
        
        # Check root element
        if root.tag != "NAXML-BusDoc":
            self._add_error('structure', "Root element must be <NAXML-BusDoc>")
        else:
            self._add_pass('structure')
        
        # Check required top-level sections
        required_sections = ['TransmissionHeader', 'Parties', 'Invoice']
        for section in required_sections:
            if root.find(section) is not None:
                self._add_pass('structure')
            else:
                self._add_error('structure', f"Missing required section: <{section}>")
    
    def _validate_transmission_header(self, root: ET.Element) -> None:
        """Validate TransmissionHeader section"""
        
        header = root.find('TransmissionHeader')
        if header is None:
            self._add_error('transmission', "Missing <TransmissionHeader> section")
            return
        
        # Required fields
        required_fields = ['TransmissionId', 'TransmissionDate', 'TransmissionTime', 'TransmissionStatus']
        for field in required_fields:
            element = header.find(field)
            if element is not None and element.text:
                self._add_pass('transmission')
                
                # Validate date format
                if field == 'TransmissionDate':
                    if not re.match(r'^\d{4}-\d{2}-\d{2}$', element.text):
                        self._add_error('transmission', f"TransmissionDate format invalid: {element.text}")
                
                # Validate time format
                if field == 'TransmissionTime':
                    if not re.match(r'^\d{2}:\d{2}:\d{2}$', element.text):
                        self._add_error('transmission', f"TransmissionTime format invalid: {element.text}")
                        
            else:
                self._add_error('transmission', f"Missing or empty required field: <{field}>")
    
    def _validate_parties_section(self, root: ET.Element) -> None:
        """Validate Parties section"""
        
        parties = root.find('Parties')
        if parties is None:
            self._add_error('parties', "Missing <Parties> section")
            return
        
        # Check Supplier
        supplier = parties.find('Supplier')
        if supplier is not None:
            if supplier.find('Name') is not None and supplier.find('Name').text:
                self._add_pass('parties')
            else:
                self._add_error('parties', "Missing Supplier Name")
                
            org_id = supplier.find('OrganizationId')
            if org_id is not None and org_id.get('ident') and org_id.text:
                self._add_pass('parties')
            else:
                self._add_error('parties', "Missing Supplier OrganizationId with ident attribute")
        else:
            self._add_error('parties', "Missing <Supplier> section")
        
        # Check Buyer
        buyer = parties.find('Buyer')
        if buyer is not None and buyer.find('Name') is not None:
            self._add_pass('parties')
        else:
            self._add_error('parties', "Missing <Buyer> with Name")
        
        # Check ShipTo
        ship_to = parties.find('ShipTo')
        if ship_to is not None:
            if ship_to.get('ident'):
                self._add_pass('parties')
            else:
                self._add_error('parties', "ShipTo missing ident attribute")
                
            if ship_to.find('Name') is not None:
                self._add_pass('parties')
            else:
                self._add_error('parties', "ShipTo missing Name")
        else:
            self._add_error('parties', "Missing <ShipTo> section")
    
    def _validate_invoice_header(self, root: ET.Element) -> None:
        """Validate Invoice header section"""
        
        invoice = root.find('Invoice')
        if invoice is None:
            self._add_error('invoice_header', "Missing <Invoice> section")
            return
        
        # Required fields
        required_fields = ['InvoiceNumber', 'InvoiceDate', 'Currency']
        for field in required_fields:
            element = invoice.find(field)
            if element is not None and element.text:
                self._add_pass('invoice_header')
                
                # Validate date format
                if field == 'InvoiceDate':
                    if not re.match(r'^\d{4}-\d{2}-\d{2}$', element.text):
                        self._add_error('invoice_header', f"InvoiceDate format invalid: {element.text}")
                
                # Validate currency
                if field == 'Currency':
                    if element.get('code') != 'USD':
                        self._add_error('invoice_header', f"Currency code should be USD, found: {element.get('code')}")
                        
            else:
                self._add_error('invoice_header', f"Missing or empty required field: <{field}>")
        
        # Check Location
        location = invoice.find('Location')
        if location is not None:
            location_name = location.find('Name')
            if location_name is not None and location_name.get('ident'):
                self._add_pass('invoice_header')
            else:
                self._add_error('invoice_header', "Location Name missing ident attribute")
        else:
            self._add_error('invoice_header', "Missing <Location> section")
    
    def _validate_line_items(self, root: ET.Element) -> None:
        """Validate LineItem sections"""
        
        invoice = root.find('Invoice')
        if invoice is None:
            return
            
        invoice_detail = invoice.find('InvoiceDetail')
        if invoice_detail is None:
            self._add_error('line_items', "Missing <InvoiceDetail> section")
            return
        
        line_items = invoice_detail.findall('LineItem')
        if not line_items:
            self._add_error('line_items', "No <LineItem> elements found")
            return
        
        for i, line_item in enumerate(line_items):
            item_id = f"LineItem {i+1}"
            
            # Validate InvoiceUnit
            invoice_unit = line_item.find('InvoiceUnit')
            if invoice_unit is not None:
                self._validate_invoice_unit(invoice_unit, item_id)
            else:
                self._add_error('line_items', f"{item_id}: Missing <InvoiceUnit>")
            
            # Validate RetailUnitPricing (optional but recommended)
            retail_pricing = line_item.find('RetailUnitPricing')
            if retail_pricing is not None:
                self._validate_retail_pricing(retail_pricing, item_id)
    
    def _validate_invoice_unit(self, invoice_unit: ET.Element, item_id: str) -> None:
        """Validate InvoiceUnit section"""
        
        # Required fields
        required_fields = ['InvoiceUnitDescription', 'InvoiceUnitQty', 'InvoiceUnitCost']
        for field in required_fields:
            element = invoice_unit.find(field)
            if element is not None and element.text:
                self._add_pass('line_items')
                
                # Validate quantity attributes
                if field == 'InvoiceUnitQty':
                    if not element.get('cstoreUOMBasis'):
                        self._add_error('line_items', f"{item_id}: InvoiceUnitQty missing cstoreUOMBasis attribute")
                
                # Validate cost currency
                if field == 'InvoiceUnitCost':
                    if element.get('currency') != 'USD':
                        self._add_error('line_items', f"{item_id}: InvoiceUnitCost should have currency='USD'")
                        
            else:
                self._add_error('line_items', f"{item_id}: Missing or empty <{field}>")
        
        # Check optional but recommended fields
        optional_fields = ['LineItemGrossAmt', 'LineItemNetAmt']
        for field in optional_fields:
            element = invoice_unit.find(field)
            if element is not None and element.text:
                self._add_pass('line_items')
    
    def _validate_retail_pricing(self, retail_pricing: ET.Element, item_id: str) -> None:
        """Validate RetailUnitPricing section"""
        
        # Check RetailPrice
        retail_price = retail_pricing.find('RetailPrice')
        if retail_price is not None:
            if retail_price.text:
                self._add_pass('line_items')
            if retail_price.get('currency') != 'USD':
                self._add_error('line_items', f"{item_id}: RetailPrice should have currency='USD'")
        
        # Check RetailUnitQty
        retail_qty = retail_pricing.find('RetailUnitQty')
        if retail_qty is not None and retail_qty.text:
            self._add_pass('line_items')
    
    def _validate_invoice_summary(self, root: ET.Element) -> None:
        """Validate InvoiceSummary section"""
        
        invoice = root.find('Invoice')
        if invoice is None:
            return
            
        invoice_detail = invoice.find('InvoiceDetail')
        if invoice_detail is None:
            return
            
        invoice_summary = invoice_detail.find('InvoiceSummary')
        if invoice_summary is None:
            self._add_error('invoice_summary', "Missing <InvoiceSummary> section")
            return
        
        invoice_totals = invoice_summary.find('InvoiceTotals')
        if invoice_totals is None:
            self._add_error('invoice_summary', "Missing <InvoiceTotals> section")
            return
        
        # Check recommended total fields
        recommended_fields = ['TotalInvoiceUnits', 'TotalLineItemNetAmt', 'TotalInvoiceDueAmt']
        for field in recommended_fields:
            element = invoice_totals.find(field)
            if element is not None and element.text:
                self._add_pass('invoice_summary')
                
                # Check currency attributes
                if field in ['TotalLineItemNetAmt', 'TotalInvoiceDueAmt']:
                    if element.get('currency') != 'USD':
                        self._add_error('invoice_summary', f"{field} should have currency='USD'")
            else:
                self._add_error('invoice_summary', f"Missing recommended field: <{field}>")
    
    def _validate_gtin_format(self, root: ET.Element) -> None:
        """Validate GTIN format in InvoiceUnitId fields"""
        
        # Find all InvoiceUnitId elements
        invoice_unit_ids = root.findall('.//InvoiceUnitId[@identType="GTIN"]')
        retail_unit_ids = root.findall('.//RetailUnitId[@identType="GTIN"]')
        
        all_gtin_elements = invoice_unit_ids + retail_unit_ids
        
        for element in all_gtin_elements:
            if element.text:
                gtin = element.text.strip()
                
                # Validate GTIN format (should be 14 digits)
                if re.match(r'^\d{14}$', gtin):
                    self._add_pass('gtin_format')
                else:
                    self._add_error('gtin_format', f"Invalid GTIN format: '{gtin}' (should be 14 digits)")
                
                # Validate GTIN check digit (basic validation)
                if len(gtin) == 14:
                    if self._validate_gtin_check_digit(gtin):
                        self._add_pass('gtin_format')
                    else:
                        self._add_error('gtin_format', f"Invalid GTIN check digit: {gtin}")
            else:
                self._add_error('gtin_format', "Empty GTIN value found")
    
    def _validate_gtin_check_digit(self, gtin: str) -> bool:
        """Validate GTIN-14 check digit using GS1 algorithm"""
        if len(gtin) != 14:
            return False
            
        try:
            # Calculate check digit
            digits = [int(d) for d in gtin[:-1]]  # All but last digit
            weighted_sum = sum(d * (3 if i % 2 else 1) for i, d in enumerate(digits))
            calculated_check = (10 - (weighted_sum % 10)) % 10
            
            return calculated_check == int(gtin[-1])
        except (ValueError, IndexError):
            return False
    
    def _add_pass(self, category: str) -> None:
        """Add a passed validation"""
        self.validation_results[category]['passed'] += 1
    
    def _add_error(self, category: str, error: str) -> None:
        """Add a failed validation"""
        self.validation_results[category]['failed'] += 1
        self.validation_results[category]['errors'].append(error)
    
    def _generate_compliance_report(self) -> bool:
        """Generate final compliance report"""
        
        print(f"\n============================================================")
        print(f"📊 CONEXXUS BUSDOCINVOICE COMPLIANCE REPORT")
        print(f"============================================================")
        
        total_passed = 0
        total_failed = 0
        all_compliant = True
        
        for category, results in self.validation_results.items():
            passed = results['passed']
            failed = results['failed']
            errors = results['errors']
            
            total_passed += passed
            total_failed += failed
            
            status_icon = "✅ PASS" if failed == 0 else "❌ FAIL"
            category_name = category.replace('_', ' ').upper()
            
            print(f"\n{category_name}: {status_icon}")
            print(f"   Passed: {passed}, Failed: {failed}")
            
            if errors:
                all_compliant = False
                print(f"   Errors:")
                for error in errors:
                    print(f"     • {error}")
        
        print(f"\n------------------------------------------------------------")
        print(f"OVERALL COMPLIANCE SUMMARY")
        print(f"------------------------------------------------------------")
        print(f"Total Checks: {total_passed + total_failed}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_failed}")
        
        if all_compliant:
            print(f"🎉 STATUS: ✅ FULLY COMPLIANT WITH CONEXXUS BUSDOCINVOICE")
            print(f"Compliance Score: 100.0%")
            print(f"\n✅ CONEXXUS BUSDOCINVOICE VALIDATION: PASSED")
            print(f"   File is 100% compliant with official Conexxus specification")
            print(f"   SSCS Compatibility: ✅ CONFIRMED")
        else:
            compliance_score = (total_passed / (total_passed + total_failed)) * 100 if (total_passed + total_failed) > 0 else 0
            print(f"⚠️  STATUS: ❌ NON-COMPLIANT ({compliance_score:.1f}%)")
            print(f"Compliance Score: {compliance_score:.1f}%")
            print(f"\n❌ CONEXXUS BUSDOCINVOICE VALIDATION: FAILED")
            print(f"   Compliance score: {compliance_score:.1f}%")
        
        return all_compliant

def main():
    parser = argparse.ArgumentParser(description='Validate Conexxus NAXML BusDocInvoice compliance')
    parser.add_argument('--input', required=True, help='Input BusDocInvoice XML file')
    
    args = parser.parse_args()
    
    # Validate input file exists
    from pathlib import Path
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)
    
    # Execute validation
    validator = BusDocInvoiceValidator()
    
    is_compliant = validator.validate_busdocinvoice(args.input)
    
    sys.exit(0 if is_compliant else 1)

if __name__ == "__main__":
    main()
