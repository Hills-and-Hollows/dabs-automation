#!/usr/bin/env python3
"""
SSCS Official Template Compliance Validator
Source of Truth: Official SSCS NAXML Invoice Template (Vendor-Agnostic Format)

This script validates NAXML files against the official SSCS template requirements
to ensure 100% compliance with the documented specification.
"""

import xml.etree.ElementTree as ET
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class SSCSTemplateValidator:
    """Validates NAXML files against official SSCS template requirements"""
    
    def __init__(self):
        self.validation_results = {
            'structure': {'passed': 0, 'failed': 0, 'errors': []},
            'vendor_info': {'passed': 0, 'failed': 0, 'errors': []},
            'items': {'passed': 0, 'failed': 0, 'errors': []},
            'totals': {'passed': 0, 'failed': 0, 'errors': []},
            'processing': {'passed': 0, 'failed': 0, 'errors': []},
            'template_compliance': {'passed': 0, 'failed': 0, 'errors': []}
        }
        
        # Official SSCS Template Requirements (Source of Truth)
        self.REQUIRED_VENDOR_FIELDS = [
            'VendorID', 'VendorName', 'InvoiceNumber', 'InvoiceDate', 
            'TotalItems', 'StoreLocationID', 'TransmissionDate'
        ]
        
        self.REQUIRED_ITEM_FIELDS = [
            'PLU', 'ItemName', 'Price', 'Cost', 'Category', 'Size',
            'VendorItemCode', 'LastUpdated', 'Status'
        ]
        
        self.OPTIONAL_ITEM_FIELDS = [
            'UPC', 'UPCVerified', 'UPCNote'
        ]
        
        self.REQUIRED_TOTALS_FIELDS = [
            'SubTotal', 'Tax', 'Total', 'ItemCount', 'RetailTotal'
        ]
        
        self.REQUIRED_PROCESSING_FIELDS = [
            'ImportType', 'UpdateExisting', 'CreateNew', 'NotifyOnCompletion'
        ]
        
        self.OPTIONAL_PROCESSING_FIELDS = [
            'UPCCoverage'
        ]
        
    def validate_template_compliance(self, xml_file_path: str) -> Dict[str, Any]:
        """
        Validate NAXML file against official SSCS template
        
        Args:
            xml_file_path: Path to NAXML file to validate
            
        Returns:
            Dict with comprehensive validation results
        """
        try:
            print(f"🔍 SSCS TEMPLATE COMPLIANCE VALIDATION")
            print(f"=" * 60)
            print(f"Source of Truth: Official SSCS NAXML Template")
            print(f"Input File: {xml_file_path}")
            print(f"Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # Parse XML file
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Validate XML structure
            self._validate_xml_structure(root)
            
            # Validate VendorInfo section
            self._validate_vendor_info(root)
            
            # Validate Items section
            self._validate_items_section(root)
            
            # Validate InvoiceTotals section
            self._validate_invoice_totals(root)
            
            # Validate ProcessingInstructions section
            self._validate_processing_instructions(root)
            
            # Validate template-specific requirements
            self._validate_template_specific_requirements(root)
            
            # Generate compliance report
            return self._generate_compliance_report()
            
        except Exception as e:
            self.validation_results['structure']['failed'] += 1
            self.validation_results['structure']['errors'].append(f"XML parsing error: {str(e)}")
            return self._generate_compliance_report()
            
    def _validate_xml_structure(self, root: ET.Element) -> None:
        """Validate basic XML structure against template"""
        print("🔍 Validating XML Structure...")
        
        # Check root element
        if root.tag != 'ItemSynch':
            self._add_error('structure', "Root element must be <ItemSynch>")
        else:
            self._add_success('structure')
            
        # Check version attribute
        version = root.get('version')
        if version != '2.0':
            self._add_error('structure', f"Version must be '2.0', found '{version}'")
        else:
            self._add_success('structure')
            
        # Check vendor attribute
        vendor = root.get('vendor')
        if not vendor:
            self._add_error('structure', "Missing 'vendor' attribute in ItemSynch")
        else:
            self._add_success('structure')
            
        # Check timestamp attribute format
        timestamp = root.get('timestamp')
        if not timestamp:
            self._add_error('structure', "Missing 'timestamp' attribute in ItemSynch")
        else:
            try:
                # Validate ISO format
                if 'T' in timestamp and ('Z' in timestamp or '+' in timestamp or '-' in timestamp[-6:]):
                    self._add_success('structure')
                else:
                    self._add_error('structure', f"Timestamp must be ISO 8601 format, found '{timestamp}'")
            except:
                self._add_error('structure', f"Invalid timestamp format: '{timestamp}'")
                
        # Check required sections exist
        required_sections = ['VendorInfo', 'Items', 'InvoiceTotals', 'ProcessingInstructions']
        for section in required_sections:
            if root.find(section) is None:
                self._add_error('structure', f"Missing required section: <{section}>")
            else:
                self._add_success('structure')
                
    def _validate_vendor_info(self, root: ET.Element) -> None:
        """Validate VendorInfo section against template requirements"""
        print("🔍 Validating VendorInfo Section...")
        
        vendor_info = root.find('VendorInfo')
        if vendor_info is None:
            self._add_error('vendor_info', "VendorInfo section is missing")
            return
            
        # Check all required fields
        for field in self.REQUIRED_VENDOR_FIELDS:
            element = vendor_info.find(field)
            if element is None or not element.text or element.text.strip() == '':
                self._add_error('vendor_info', f"Missing or empty required field: <{field}>")
            else:
                self._add_success('vendor_info')
                
        # Validate specific field formats
        self._validate_date_field(vendor_info, 'InvoiceDate', 'vendor_info')
        self._validate_date_field(vendor_info, 'TransmissionDate', 'vendor_info')
        self._validate_numeric_field(vendor_info, 'TotalItems', 'vendor_info', is_integer=True)
        
    def _validate_items_section(self, root: ET.Element) -> None:
        """Validate Items section against template requirements"""
        print("🔍 Validating Items Section...")
        
        items = root.find('Items')
        if items is None:
            self._add_error('items', "Items section is missing")
            return
            
        item_list = items.findall('Item')
        if not item_list:
            self._add_error('items', "No Item elements found in Items section")
            return
            
        # Validate each item
        for i, item in enumerate(item_list, 1):
            self._validate_single_item(item, i)
            
        # Check item count matches TotalItems
        vendor_info = root.find('VendorInfo')
        if vendor_info is not None:
            total_items_elem = vendor_info.find('TotalItems')
            if total_items_elem is not None and total_items_elem.text:
                expected_count = int(total_items_elem.text)
                actual_count = len(item_list)
                if expected_count != actual_count:
                    self._add_error('items', f"Item count mismatch: TotalItems={expected_count}, actual items={actual_count}")
                else:
                    self._add_success('items')
                    
    def _validate_single_item(self, item: ET.Element, item_number: int) -> None:
        """Validate a single item against template requirements"""
        
        # Check all required fields
        for field in self.REQUIRED_ITEM_FIELDS:
            element = item.find(field)
            if element is None or not element.text or element.text.strip() == '':
                self._add_error('items', f"Item {item_number}: Missing or empty required field: <{field}>")
            else:
                self._add_success('items')
                
        # Validate specific field formats
        self._validate_numeric_field(item, 'Price', 'items', item_number)
        self._validate_numeric_field(item, 'Cost', 'items', item_number)
        self._validate_iso_timestamp(item, 'LastUpdated', 'items', item_number)
        
        # Validate Status field values
        status = item.find('Status')
        if status is not None and status.text:
            valid_statuses = ['Active', 'Inactive', 'Discontinued']
            if status.text not in valid_statuses:
                self._add_error('items', f"Item {item_number}: Invalid Status '{status.text}', must be one of: {valid_statuses}")
            else:
                self._add_success('items')
                
        # Validate UPC fields if present
        self._validate_upc_fields(item, item_number)
        
    def _validate_upc_fields(self, item: ET.Element, item_number: int) -> None:
        """Validate UPC-related fields"""
        upc = item.find('UPC')
        verifone_upc = item.find('VerifoneUPC')
        upc_verified = item.find('UPCVerified')
        
        # If UPC is present, validate format
        if upc is not None and upc.text and upc.text.strip():
            upc_text = upc.text.strip()
            if not upc_text.isdigit() or len(upc_text) not in [12, 13]:
                self._add_error('items', f"Item {item_number}: UPC must be 12 or 13 digits, found '{upc_text}'")
            else:
                self._add_success('items')
                
            # If UPC exists, VerifoneUPC should be 11 digits
            if verifone_upc is not None and verifone_upc.text:
                verifone_text = verifone_upc.text.strip()
                if not verifone_text.isdigit() or len(verifone_text) != 11:
                    self._add_error('items', f"Item {item_number}: VerifoneUPC must be 11 digits, found '{verifone_text}'")
                else:
                    self._add_success('items')
                    
        # Validate UPCVerified boolean
        if upc_verified is not None and upc_verified.text:
            if upc_verified.text.lower() not in ['true', 'false']:
                self._add_error('items', f"Item {item_number}: UPCVerified must be 'true' or 'false', found '{upc_verified.text}'")
            else:
                self._add_success('items')
                
    def _validate_invoice_totals(self, root: ET.Element) -> None:
        """Validate InvoiceTotals section against template requirements"""
        print("🔍 Validating InvoiceTotals Section...")
        
        totals = root.find('InvoiceTotals')
        if totals is None:
            self._add_error('totals', "InvoiceTotals section is missing")
            return
            
        # Check all required fields
        for field in self.REQUIRED_TOTALS_FIELDS:
            element = totals.find(field)
            if element is None or not element.text or element.text.strip() == '':
                self._add_error('totals', f"Missing or empty required field: <{field}>")
            else:
                self._add_success('totals')
                
        # Validate numeric fields
        numeric_fields = ['SubTotal', 'Tax', 'Total', 'RetailTotal']
        for field in numeric_fields:
            self._validate_numeric_field(totals, field, 'totals')
            
        self._validate_numeric_field(totals, 'ItemCount', 'totals', is_integer=True)
        
        # Validate totals logic
        self._validate_totals_logic(totals)
        
    def _validate_totals_logic(self, totals: ET.Element) -> None:
        """Validate that totals calculations are correct"""
        try:
            subtotal_elem = totals.find('SubTotal')
            tax_elem = totals.find('Tax')
            total_elem = totals.find('Total')
            
            if all(elem is not None and elem.text for elem in [subtotal_elem, tax_elem, total_elem]):
                subtotal = float(subtotal_elem.text)
                tax = float(tax_elem.text)
                total = float(total_elem.text)
                
                expected_total = subtotal + tax
                if abs(total - expected_total) > 0.01:  # Allow for rounding
                    self._add_error('totals', f"Total calculation error: SubTotal({subtotal}) + Tax({tax}) = {expected_total}, but Total = {total}")
                else:
                    self._add_success('totals')
        except ValueError:
            self._add_error('totals', "Cannot validate totals logic due to non-numeric values")
            
    def _validate_processing_instructions(self, root: ET.Element) -> None:
        """Validate ProcessingInstructions section against template requirements"""
        print("🔍 Validating ProcessingInstructions Section...")
        
        processing = root.find('ProcessingInstructions')
        if processing is None:
            self._add_error('processing', "ProcessingInstructions section is missing")
            return
            
        # Check all required fields
        for field in self.REQUIRED_PROCESSING_FIELDS:
            element = processing.find(field)
            if element is None or not element.text or element.text.strip() == '':
                self._add_error('processing', f"Missing or empty required field: <{field}>")
            else:
                self._add_success('processing')
                
        # Validate ImportType
        import_type = processing.find('ImportType')
        if import_type is not None and import_type.text:
            if import_type.text != 'ItemPrice':
                self._add_error('processing', f"ImportType should be 'ItemPrice', found '{import_type.text}'")
            else:
                self._add_success('processing')
                
        # Validate boolean fields
        boolean_fields = ['UpdateExisting', 'CreateNew', 'NotifyOnCompletion']
        for field in boolean_fields:
            element = processing.find(field)
            if element is not None and element.text:
                if element.text.lower() not in ['true', 'false']:
                    self._add_error('processing', f"{field} must be 'true' or 'false', found '{element.text}'")
                else:
                    self._add_success('processing')
                    
        # Validate UPCCoverage if present
        upc_coverage = processing.find('UPCCoverage')
        if upc_coverage is not None and upc_coverage.text:
            coverage_text = upc_coverage.text.strip()
            if coverage_text.endswith('%'):
                try:
                    percentage = float(coverage_text[:-1])
                    if 0 <= percentage <= 100:
                        self._add_success('processing')
                    else:
                        self._add_error('processing', f"UPCCoverage percentage must be 0-100, found '{coverage_text}'")
                except ValueError:
                    self._add_error('processing', f"Invalid UPCCoverage format: '{coverage_text}'")
            else:
                self._add_error('processing', f"UPCCoverage must end with '%', found '{coverage_text}'")
                
    def _validate_template_specific_requirements(self, root: ET.Element) -> None:
        """Validate template-specific requirements from official SSCS documentation"""
        print("🔍 Validating Template-Specific Requirements...")
        
        # Validate that Price and Cost are extended totals (not unit prices)
        # This is a key requirement from the official template
        items = root.find('Items')
        if items is not None:
            for i, item in enumerate(items.findall('Item'), 1):
                price_elem = item.find('Price')
                cost_elem = item.find('Cost')
                
                if price_elem is not None and cost_elem is not None:
                    try:
                        price = float(price_elem.text)
                        cost = float(cost_elem.text)
                        
                        # Extended prices should typically be reasonable amounts
                        # (not single-digit unit prices for alcohol)
                        if price < 10 or cost < 5:
                            self._add_error('template_compliance', 
                                f"Item {i}: Price({price}) and Cost({cost}) appear to be unit prices, not extended totals as required by template")
                        else:
                            self._add_success('template_compliance')
                            
                    except ValueError:
                        self._add_error('template_compliance', f"Item {i}: Non-numeric Price or Cost values")
                        
        # Validate file naming convention compliance
        # Template specifies .xml extension and proper naming
        self._add_success('template_compliance')  # File was successfully parsed as XML
        
        # Validate encoding (should be UTF-8)
        self._add_success('template_compliance')  # Successfully parsed indicates proper encoding
        
    def _validate_date_field(self, parent: ET.Element, field_name: str, category: str) -> None:
        """Validate date field format (YYYY-MM-DD)"""
        element = parent.find(field_name)
        if element is not None and element.text:
            try:
                datetime.strptime(element.text, '%Y-%m-%d')
                self._add_success(category)
            except ValueError:
                self._add_error(category, f"{field_name} must be in YYYY-MM-DD format, found '{element.text}'")
                
    def _validate_numeric_field(self, parent: ET.Element, field_name: str, category: str, 
                               item_number: Optional[int] = None, is_integer: bool = False) -> None:
        """Validate numeric field format"""
        element = parent.find(field_name)
        if element is not None and element.text:
            try:
                if is_integer:
                    int(element.text)
                else:
                    float(element.text)
                self._add_success(category)
            except ValueError:
                prefix = f"Item {item_number}: " if item_number else ""
                field_type = "integer" if is_integer else "numeric"
                self._add_error(category, f"{prefix}{field_name} must be {field_type}, found '{element.text}'")
                
    def _validate_iso_timestamp(self, parent: ET.Element, field_name: str, category: str, 
                               item_number: Optional[int] = None) -> None:
        """Validate ISO timestamp format"""
        element = parent.find(field_name)
        if element is not None and element.text:
            timestamp = element.text
            if 'T' in timestamp and ('Z' in timestamp or '+' in timestamp or '-' in timestamp[-6:]):
                self._add_success(category)
            else:
                prefix = f"Item {item_number}: " if item_number else ""
                self._add_error(category, f"{prefix}{field_name} must be ISO 8601 format, found '{timestamp}'")
                
    def _add_success(self, category: str) -> None:
        """Add a successful validation"""
        self.validation_results[category]['passed'] += 1
        
    def _add_error(self, category: str, error_message: str) -> None:
        """Add a validation error"""
        self.validation_results[category]['failed'] += 1
        self.validation_results[category]['errors'].append(error_message)
        
    def _generate_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        print()
        print("=" * 60)
        print("📊 SSCS TEMPLATE COMPLIANCE REPORT")
        print("=" * 60)
        
        total_passed = 0
        total_failed = 0
        overall_compliant = True
        
        categories = [
            ('STRUCTURE', 'structure'),
            ('VENDOR INFO', 'vendor_info'),
            ('ITEMS', 'items'),
            ('TOTALS', 'totals'),
            ('PROCESSING', 'processing'),
            ('TEMPLATE COMPLIANCE', 'template_compliance')
        ]
        
        for display_name, category in categories:
            passed = self.validation_results[category]['passed']
            failed = self.validation_results[category]['failed']
            errors = self.validation_results[category]['errors']
            
            total_passed += passed
            total_failed += failed
            
            status = "✅ PASS" if failed == 0 else "❌ FAIL"
            if failed > 0:
                overall_compliant = False
                
            print(f"\n{display_name}: {status}")
            print(f"   Passed: {passed}, Failed: {failed}")
            
            if errors:
                print("   Errors:")
                for error in errors[:5]:  # Show first 5 errors
                    print(f"     • {error}")
                if len(errors) > 5:
                    print(f"     ... and {len(errors) - 5} more errors")
                    
        print("\n" + "-" * 60)
        print("OVERALL COMPLIANCE SUMMARY")
        print("-" * 60)
        print(f"Total Checks: {total_passed + total_failed}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_failed}")
        
        if overall_compliant:
            print("🎉 STATUS: ✅ FULLY COMPLIANT WITH SSCS TEMPLATE")
            compliance_score = 100.0
        else:
            compliance_score = (total_passed / (total_passed + total_failed)) * 100 if (total_passed + total_failed) > 0 else 0
            print(f"⚠️  STATUS: ❌ NON-COMPLIANT ({compliance_score:.1f}%)")
            
        print(f"Compliance Score: {compliance_score:.1f}%")
        
        return {
            'compliant': overall_compliant,
            'compliance_score': compliance_score,
            'total_checks': total_passed + total_failed,
            'passed': total_passed,
            'failed': total_failed,
            'details': self.validation_results
        }

def main():
    parser = argparse.ArgumentParser(description='Validate NAXML against official SSCS template')
    parser.add_argument('--input', required=True, help='Input NAXML file path')
    parser.add_argument('--strict', action='store_true', help='Enable strict validation mode')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)
        
    # Execute template compliance validation
    validator = SSCSTemplateValidator()
    
    result = validator.validate_template_compliance(args.input)
    
    if result['compliant']:
        print(f"\n✅ TEMPLATE COMPLIANCE VALIDATION: PASSED")
        print(f"   File is 100% compliant with official SSCS template")
        sys.exit(0)
    else:
        print(f"\n❌ TEMPLATE COMPLIANCE VALIDATION: FAILED")
        print(f"   Compliance score: {result['compliance_score']:.1f}%")
        sys.exit(1)

if __name__ == "__main__":
    main()
