#!/usr/bin/env python3
"""
SSCS NAXML Compliance Validation Script
Zero Tolerance Validation for SSCS EDI Requirements

This script performs comprehensive validation of NAXML files against SSCS specifications.
"""

import xml.etree.ElementTree as ET
import argparse
import sys
from datetime import datetime
from pathlib import Path
import re
from typing import List, Dict, Tuple

class SSCSComplianceValidator:
    """Comprehensive SSCS compliance validation"""
    
    def __init__(self):
        self.validation_results = {
            'structure': {'passed': 0, 'failed': 0, 'errors': []},
            'vendor_info': {'passed': 0, 'failed': 0, 'errors': []},
            'items': {'passed': 0, 'failed': 0, 'errors': []},
            'totals': {'passed': 0, 'failed': 0, 'errors': []},
            'compliance': {'passed': 0, 'failed': 0, 'errors': []},
            'upc': {'passed': 0, 'failed': 0, 'errors': []}
        }
        self.total_items = 0
        self.items_with_upc = 0
        
    def validate_compliance(self, xml_file_path: str, customer: str, vendor: str, strict_mode: bool = True) -> bool:
        """
        Perform comprehensive SSCS compliance validation
        
        Args:
            xml_file_path: Path to NAXML file
            customer: Expected customer number
            vendor: Expected vendor ID
            strict_mode: Enable strict validation mode
            
        Returns:
            bool: True if fully compliant, False if violations found
        """
        try:
            # Parse XML file
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Run all validation checks
            self._validate_structure(root, strict_mode)
            self._validate_vendor_info(root, customer, vendor, strict_mode)
            self._validate_items(root, strict_mode)
            self._validate_totals(root, strict_mode)
            self._validate_compliance_section(root, strict_mode)
            self._validate_upc_coverage(root, strict_mode)
            
            # Generate validation report
            return self._generate_report()
            
        except Exception as e:
            print(f"❌ Validation Error: {str(e)}")
            return False
            
    def _validate_structure(self, root: ET.Element, strict_mode: bool) -> None:
        """Validate XML structure and required sections"""
        print("🔍 Validating XML Structure...")
        
        # Check root element
        if root.tag != 'ItemSynch':
            self.validation_results['structure']['errors'].append("Root element must be 'ItemSynch'")
            self.validation_results['structure']['failed'] += 1
        else:
            self.validation_results['structure']['passed'] += 1
            
        # Check version attribute
        version = root.get('version')
        if version != '2.0':
            self.validation_results['structure']['errors'].append(f"Version must be '2.0', found '{version}'")
            self.validation_results['structure']['failed'] += 1
        else:
            self.validation_results['structure']['passed'] += 1
            
        # Check required sections
        required_sections = ['VendorInfo', 'Items', 'InvoiceTotals', 'ProcessingInstructions']
        for section in required_sections:
            if root.find(section) is None:
                self.validation_results['structure']['errors'].append(f"Missing required section: {section}")
                self.validation_results['structure']['failed'] += 1
            else:
                self.validation_results['structure']['passed'] += 1
                
    def _validate_vendor_info(self, root: ET.Element, customer: str, vendor: str, strict_mode: bool) -> None:
        """Validate VendorInfo section"""
        print("🔍 Validating Vendor Information...")
        
        vendor_info = root.find('VendorInfo')
        if vendor_info is None:
            self.validation_results['vendor_info']['errors'].append("VendorInfo section missing")
            self.validation_results['vendor_info']['failed'] += 1
            return
            
        # Required vendor fields
        required_fields = {
            'VendorID': vendor,
            'VendorName': None,  # Any value acceptable
            'CustomerNumber': customer,
            'InvoiceNumber': None,
            'InvoiceDate': None,
            'TransmissionDate': None,
            'EDIDeliveryEmail': 'v6242s1@edidelivery.com'
        }
        
        # Enhanced fields for strict mode
        if strict_mode:
            required_fields.update({
                'DeliveryDate': None,
                'PurchaseOrderNumber': None,
                'Terms': None,
                'BackupContactEmail': None,
                'VendorContactPhone': None
            })
            
        for field_name, expected_value in required_fields.items():
            field_element = vendor_info.find(field_name)
            if field_element is None:
                self.validation_results['vendor_info']['errors'].append(f"Missing required field: {field_name}")
                self.validation_results['vendor_info']['failed'] += 1
            elif expected_value and field_element.text != expected_value:
                self.validation_results['vendor_info']['errors'].append(
                    f"Field {field_name} value '{field_element.text}' does not match expected '{expected_value}'"
                )
                self.validation_results['vendor_info']['failed'] += 1
            else:
                self.validation_results['vendor_info']['passed'] += 1
                
    def _validate_items(self, root: ET.Element, strict_mode: bool) -> None:
        """Validate Items section"""
        print("🔍 Validating Items...")
        
        items = root.find('Items')
        if items is None:
            self.validation_results['items']['errors'].append("Items section missing")
            self.validation_results['items']['failed'] += 1
            return
            
        item_list = items.findall('Item')
        self.total_items = len(item_list)
        
        if self.total_items == 0:
            self.validation_results['items']['errors'].append("No items found in Items section")
            self.validation_results['items']['failed'] += 1
            return
            
        # Required item fields
        required_fields = ['PLU', 'ItemName', 'Price', 'Cost', 'Category', 'Status']
        
        # Enhanced fields for strict mode
        if strict_mode:
            required_fields.extend(['Department', 'Taxable', 'MinimumOrderQuantity', 'CaseSize'])
            
        for i, item in enumerate(item_list):
            item_errors = []
            
            for field_name in required_fields:
                field_element = item.find(field_name)
                if field_element is None:
                    item_errors.append(f"Missing field: {field_name}")
                elif not field_element.text or field_element.text.strip() == "":
                    item_errors.append(f"Empty field: {field_name}")
                    
            # Validate numeric fields
            numeric_fields = ['Price', 'Cost']
            for field_name in numeric_fields:
                field_element = item.find(field_name)
                if field_element is not None and field_element.text:
                    try:
                        float(field_element.text)
                    except ValueError:
                        item_errors.append(f"Invalid numeric value in {field_name}: {field_element.text}")
                        
            if item_errors:
                plu = item.find('PLU')
                plu_text = plu.text if plu is not None else f"Item {i+1}"
                for error in item_errors:
                    self.validation_results['items']['errors'].append(f"{plu_text}: {error}")
                self.validation_results['items']['failed'] += len(item_errors)
            else:
                self.validation_results['items']['passed'] += 1
                
    def _validate_totals(self, root: ET.Element, strict_mode: bool) -> None:
        """Validate InvoiceTotals section"""
        print("🔍 Validating Invoice Totals...")
        
        totals = root.find('InvoiceTotals')
        if totals is None:
            self.validation_results['totals']['errors'].append("InvoiceTotals section missing")
            self.validation_results['totals']['failed'] += 1
            return
            
        # Required total fields
        required_fields = ['SubTotal', 'Tax', 'Total', 'ItemCount']
        
        for field_name in required_fields:
            field_element = totals.find(field_name)
            if field_element is None:
                self.validation_results['totals']['errors'].append(f"Missing field: {field_name}")
                self.validation_results['totals']['failed'] += 1
            elif not field_element.text or field_element.text.strip() == "":
                self.validation_results['totals']['errors'].append(f"Empty field: {field_name}")
                self.validation_results['totals']['failed'] += 1
            else:
                # Validate numeric fields
                if field_name in ['SubTotal', 'Tax', 'Total']:
                    try:
                        float(field_element.text)
                        self.validation_results['totals']['passed'] += 1
                    except ValueError:
                        self.validation_results['totals']['errors'].append(
                            f"Invalid numeric value in {field_name}: {field_element.text}"
                        )
                        self.validation_results['totals']['failed'] += 1
                elif field_name == 'ItemCount':
                    try:
                        item_count = int(field_element.text)
                        if item_count != self.total_items:
                            self.validation_results['totals']['errors'].append(
                                f"ItemCount ({item_count}) does not match actual items ({self.total_items})"
                            )
                            self.validation_results['totals']['failed'] += 1
                        else:
                            self.validation_results['totals']['passed'] += 1
                    except ValueError:
                        self.validation_results['totals']['errors'].append(
                            f"Invalid integer value in ItemCount: {field_element.text}"
                        )
                        self.validation_results['totals']['failed'] += 1
                        
    def _validate_compliance_section(self, root: ET.Element, strict_mode: bool) -> None:
        """Validate ComplianceInformation section"""
        print("🔍 Validating Compliance Information...")
        
        compliance = root.find('ComplianceInformation')
        if compliance is None:
            if strict_mode:
                self.validation_results['compliance']['errors'].append("ComplianceInformation section missing")
                self.validation_results['compliance']['failed'] += 1
            return
            
        # Required compliance fields
        required_fields = [
            'UtahPackageAgencyLicense', 'ComplianceOfficer', 'AuditTrailID', 
            'RetentionPeriod', 'ComplianceVersion'
        ]
        
        for field_name in required_fields:
            field_element = compliance.find(field_name)
            if field_element is None:
                self.validation_results['compliance']['errors'].append(f"Missing compliance field: {field_name}")
                self.validation_results['compliance']['failed'] += 1
            elif not field_element.text or field_element.text.strip() == "":
                self.validation_results['compliance']['errors'].append(f"Empty compliance field: {field_name}")
                self.validation_results['compliance']['failed'] += 1
            else:
                self.validation_results['compliance']['passed'] += 1
                
    def _validate_upc_coverage(self, root: ET.Element, strict_mode: bool) -> None:
        """Validate UPC coverage and formatting"""
        print("🔍 Validating UPC Coverage...")
        
        items = root.find('Items')
        if items is None:
            return
            
        item_list = items.findall('Item')
        upc_verified_count = 0
        upc_pending_count = 0
        upc_missing_count = 0
        
        for item in item_list:
            upc_element = item.find('UPC')
            upc_verified = item.find('UPCVerified')
            
            if upc_element is not None and upc_element.text:
                if upc_element.text == "PENDING_LOOKUP":
                    upc_pending_count += 1
                elif upc_verified is not None and upc_verified.text == "true":
                    upc_verified_count += 1
                    self.items_with_upc += 1
                else:
                    # UPC present but not verified
                    self.items_with_upc += 1
            else:
                upc_missing_count += 1
                
        # Calculate coverage percentage
        coverage_percentage = (self.items_with_upc / self.total_items * 100) if self.total_items > 0 else 0
        
        print(f"   UPC Coverage: {coverage_percentage:.1f}% ({self.items_with_upc}/{self.total_items})")
        print(f"   Verified: {upc_verified_count}, Pending: {upc_pending_count}, Missing: {upc_missing_count}")
        
        if coverage_percentage < 80 and strict_mode:
            self.validation_results['upc']['errors'].append(
                f"UPC coverage {coverage_percentage:.1f}% below recommended 80% threshold"
            )
            self.validation_results['upc']['failed'] += 1
        else:
            self.validation_results['upc']['passed'] += 1
            
    def _generate_report(self) -> bool:
        """Generate comprehensive validation report"""
        print("\n" + "="*60)
        print("📊 SSCS COMPLIANCE VALIDATION REPORT")
        print("="*60)
        
        total_passed = 0
        total_failed = 0
        overall_compliant = True
        
        for category, results in self.validation_results.items():
            passed = results['passed']
            failed = results['failed']
            errors = results['errors']
            
            total_passed += passed
            total_failed += failed
            
            if failed > 0:
                overall_compliant = False
                
            status = "✅ PASS" if failed == 0 else "❌ FAIL"
            print(f"\n{category.upper().replace('_', ' ')}: {status}")
            print(f"   Passed: {passed}, Failed: {failed}")
            
            if errors:
                print("   Errors:")
                for error in errors[:5]:  # Show first 5 errors
                    print(f"     • {error}")
                if len(errors) > 5:
                    print(f"     ... and {len(errors) - 5} more errors")
                    
        # Overall summary
        print("\n" + "-"*60)
        print("OVERALL COMPLIANCE SUMMARY")
        print("-"*60)
        print(f"Total Checks: {total_passed + total_failed}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_failed}")
        
        if overall_compliant:
            print("🎉 STATUS: ✅ FULLY COMPLIANT")
            compliance_percentage = 100.0
        else:
            compliance_percentage = (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0
            print(f"⚠️  STATUS: ❌ NON-COMPLIANT ({compliance_percentage:.1f}%)")
            
        print(f"Compliance Score: {compliance_percentage:.1f}%")
        print(f"Items Processed: {self.total_items}")
        print(f"UPC Coverage: {(self.items_with_upc / self.total_items * 100):.1f}%" if self.total_items > 0 else "UPC Coverage: N/A")
        
        return overall_compliant

def main():
    parser = argparse.ArgumentParser(description='Validate SSCS compliance for NAXML files')
    parser.add_argument('--input', required=True, help='Input NAXML file path')
    parser.add_argument('--customer', required=True, help='Expected customer number')
    parser.add_argument('--vendor', required=True, help='Expected vendor ID')
    parser.add_argument('--strict-mode', action='store_true', help='Enable strict validation mode')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)
        
    # Execute validation
    validator = SSCSComplianceValidator()
    
    print(f"🔧 Starting SSCS Compliance Validation...")
    print(f"   Input: {args.input}")
    print(f"   Customer: {args.customer}")
    print(f"   Vendor: {args.vendor}")
    print(f"   Strict Mode: {'Enabled' if args.strict_mode else 'Disabled'}")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    is_compliant = validator.validate_compliance(args.input, args.customer, args.vendor, args.strict_mode)
    
    if is_compliant:
        print(f"\n✅ SSCS Compliance Validation: PASSED")
        sys.exit(0)
    else:
        print(f"\n❌ SSCS Compliance Validation: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
