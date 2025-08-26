#!/usr/bin/env python3
"""
Real-Time SSCS Validation System
Prevents EDI delivery failures by validating against SSCS requirements

This system validates NAXML files against SSCS schema and business rules
before transmission to prevent delivery failures and ensure 100% compatibility.

Business Context:
- SSCS CDB system has strict import requirements
- Invalid EDI files cause processing failures and manual intervention
- Real-time validation prevents delivery of bad data
- Utah Package Agency compliance requires successful data delivery
"""

import logging
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal
from pathlib import Path
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationIssue:
    """SSCS validation issue"""
    severity: str  # error, warning, info
    code: str
    message: str
    element: Optional[str] = None
    line_number: Optional[int] = None
    suggested_fix: Optional[str] = None

@dataclass
class SSCSValidationResult:
    """SSCS validation result"""
    valid: bool
    schema_valid: bool
    business_rules_valid: bool
    issues: List[ValidationIssue]
    total_items: int
    validated_items: int
    total_amount: Decimal
    validation_timestamp: str
    naxml_version: str
    sscs_compatibility: str

class SSCSValidator:
    """
    Real-time SSCS validation system
    
    Validates NAXML files against:
    1. XML schema requirements
    2. SSCS business rules and constraints
    3. Data format and content validation
    4. Mathematical integrity checks
    """
    
    def __init__(self, config_file: str = "config/sscs_validation_rules.json"):
        self.config_file = Path(config_file)
        self.validation_rules = self._load_validation_rules()
        self.validation_history = []
        
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load SSCS validation rules and constraints"""
        default_rules = {
            "required_elements": [
                "VendorInfo/VendorID",
                "VendorInfo/VendorName", 
                "VendorInfo/InvoiceNumber",
                "VendorInfo/InvoiceDate",
                "Items/Item/PLU",
                "Items/Item/ItemName",
                "Items/Item/Price",
                "Items/Item/Cost"
            ],
            "optional_elements": [
                "Items/Item/UPC",
                "Items/Item/VendorItemCode",
                "Items/Item/Category",
                "Items/Item/Size",
                "Items/Item/Status"
            ],
            "data_constraints": {
                "VendorID": {"max_length": 20, "pattern": r"^[A-Z0-9]+$"},
                "InvoiceNumber": {"max_length": 50, "pattern": r"^[A-Z0-9_-]+$"},
                "PLU": {"max_length": 20, "pattern": r"^[0-9]+$"},
                "ItemName": {"max_length": 50},
                "Price": {"min_value": 0.01, "max_value": 9999.99, "decimal_places": 2},
                "Cost": {"min_value": 0.01, "max_value": 9999.99, "decimal_places": 2},
                "UPC": {"pattern": r"^[0-9]{8,14}$"}
            },
            "business_rules": {
                "max_items_per_invoice": 1000,
                "max_invoice_total": 100000.00,
                "required_vendor_id": "DABS",
                "supported_naxml_versions": ["2.0"],
                "price_cost_ratio_max": 10.0,  # Price should not be more than 10x cost
                "price_cost_ratio_min": 1.1    # Price should be at least 10% above cost
            }
        }
        
        # Try to load from file, fall back to defaults
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_rules = json.load(f)
                    # Merge with defaults
                    for key, value in loaded_rules.items():
                        if key in default_rules:
                            if isinstance(value, dict):
                                default_rules[key].update(value)
                            else:
                                default_rules[key] = value
                        else:
                            default_rules[key] = value
                    return default_rules
            except Exception as e:
                logger.warning(f"Failed to load validation rules from {self.config_file}: {e}")
        
        # Save default rules
        self._save_validation_rules(default_rules)
        return default_rules
    
    def _save_validation_rules(self, rules: Dict[str, Any]):
        """Save validation rules to file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_file, 'w') as f:
            json.dump(rules, f, indent=2, default=str)
        
        logger.info(f"SSCS validation rules saved to {self.config_file}")
    
    def validate_naxml_file(self, naxml_path: str) -> SSCSValidationResult:
        """
        Validate NAXML file against SSCS requirements
        
        Args:
            naxml_path: Path to NAXML file to validate
            
        Returns:
            SSCSValidationResult with validation details
        """
        timestamp = datetime.now().isoformat()
        issues = []
        
        logger.info(f"🔍 Validating NAXML file: {naxml_path}")
        
        try:
            # Parse XML file
            tree = ET.parse(naxml_path)
            root = tree.getroot()
            
            # Validate XML structure and schema
            schema_valid, schema_issues = self._validate_xml_schema(root)
            issues.extend(schema_issues)
            
            # Validate business rules
            business_valid, business_issues = self._validate_business_rules(root)
            issues.extend(business_issues)
            
            # Extract metrics
            items = root.findall(".//Item")
            total_items = len(items)
            validated_items = len([item for item in items if self._is_item_valid(item)])
            
            # Calculate total amount
            total_amount = Decimal('0')
            for item in items:
                try:
                    price_elem = item.find("Price")
                    if price_elem is not None and price_elem.text:
                        total_amount += Decimal(price_elem.text)
                except:
                    pass
            
            # Determine overall validity
            valid = schema_valid and business_valid and len([i for i in issues if i.severity == 'error']) == 0
            
            # Determine NAXML version
            naxml_version = root.get('version', 'unknown')
            
            # Determine SSCS compatibility
            if valid:
                sscs_compatibility = "compatible"
            elif schema_valid:
                sscs_compatibility = "schema_valid_business_issues"
            else:
                sscs_compatibility = "incompatible"
            
            result = SSCSValidationResult(
                valid=valid,
                schema_valid=schema_valid,
                business_rules_valid=business_valid,
                issues=issues,
                total_items=total_items,
                validated_items=validated_items,
                total_amount=total_amount,
                validation_timestamp=timestamp,
                naxml_version=naxml_version,
                sscs_compatibility=sscs_compatibility
            )
            
            # Log results
            if valid:
                logger.info(f"✅ NAXML validation passed: {total_items} items, ${total_amount}")
            else:
                error_count = len([i for i in issues if i.severity == 'error'])
                warning_count = len([i for i in issues if i.severity == 'warning'])
                logger.error(f"❌ NAXML validation failed: {error_count} errors, {warning_count} warnings")
            
            self.validation_history.append(result)
            return result
            
        except Exception as e:
            logger.error(f"❌ NAXML validation error: {e}")
            issues.append(ValidationIssue(
                severity="error",
                code="PARSE_ERROR",
                message=f"Failed to parse NAXML file: {e}"
            ))
            
            return SSCSValidationResult(
                valid=False,
                schema_valid=False,
                business_rules_valid=False,
                issues=issues,
                total_items=0,
                validated_items=0,
                total_amount=Decimal('0'),
                validation_timestamp=timestamp,
                naxml_version="unknown",
                sscs_compatibility="incompatible"
            )
    
    def _validate_xml_schema(self, root: ET.Element) -> Tuple[bool, List[ValidationIssue]]:
        """Validate XML schema and structure"""
        issues = []
        
        # Check root element
        if root.tag != "ItemSynch":
            issues.append(ValidationIssue(
                severity="error",
                code="INVALID_ROOT",
                message="Root element must be 'ItemSynch'",
                element=root.tag,
                suggested_fix="Change root element to 'ItemSynch'"
            ))
        
        # Check required elements
        for required_path in self.validation_rules["required_elements"]:
            elements = root.findall(f".//{required_path.split('/')[-1]}")
            if not elements:
                issues.append(ValidationIssue(
                    severity="error",
                    code="MISSING_REQUIRED_ELEMENT",
                    message=f"Required element missing: {required_path}",
                    element=required_path,
                    suggested_fix=f"Add required element: {required_path}"
                ))
        
        # Validate data constraints
        for element_name, constraints in self.validation_rules["data_constraints"].items():
            elements = root.findall(f".//{element_name}")
            for elem in elements:
                if elem.text:
                    issues.extend(self._validate_element_constraints(elem, element_name, constraints))
        
        schema_valid = len([i for i in issues if i.severity == 'error']) == 0
        return schema_valid, issues
    
    def _validate_element_constraints(self, element: ET.Element, element_name: str, constraints: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate individual element against constraints"""
        issues = []
        value = element.text.strip() if element.text else ""
        
        # Check max length
        if "max_length" in constraints and len(value) > constraints["max_length"]:
            issues.append(ValidationIssue(
                severity="error",
                code="VALUE_TOO_LONG",
                message=f"{element_name} exceeds maximum length of {constraints['max_length']}: '{value}'",
                element=element_name,
                suggested_fix=f"Truncate to {constraints['max_length']} characters"
            ))
        
        # Check pattern
        if "pattern" in constraints:
            pattern = constraints["pattern"]
            if not re.match(pattern, value):
                issues.append(ValidationIssue(
                    severity="error",
                    code="INVALID_FORMAT",
                    message=f"{element_name} does not match required pattern {pattern}: '{value}'",
                    element=element_name,
                    suggested_fix=f"Format {element_name} according to pattern {pattern}"
                ))
        
        # Check numeric constraints
        if element_name in ["Price", "Cost"]:
            try:
                numeric_value = float(value)
                
                if "min_value" in constraints and numeric_value < constraints["min_value"]:
                    issues.append(ValidationIssue(
                        severity="error",
                        code="VALUE_TOO_LOW",
                        message=f"{element_name} below minimum value {constraints['min_value']}: {numeric_value}",
                        element=element_name,
                        suggested_fix=f"Set {element_name} to at least {constraints['min_value']}"
                    ))
                
                if "max_value" in constraints and numeric_value > constraints["max_value"]:
                    issues.append(ValidationIssue(
                        severity="error", 
                        code="VALUE_TOO_HIGH",
                        message=f"{element_name} exceeds maximum value {constraints['max_value']}: {numeric_value}",
                        element=element_name,
                        suggested_fix=f"Set {element_name} to at most {constraints['max_value']}"
                    ))
                
                # Check decimal places
                if "decimal_places" in constraints:
                    decimal_str = str(numeric_value)
                    if '.' in decimal_str:
                        decimal_places = len(decimal_str.split('.')[1])
                        if decimal_places > constraints["decimal_places"]:
                            issues.append(ValidationIssue(
                                severity="warning",
                                code="TOO_MANY_DECIMALS",
                                message=f"{element_name} has too many decimal places: {decimal_places}",
                                element=element_name,
                                suggested_fix=f"Round to {constraints['decimal_places']} decimal places"
                            ))
            except ValueError:
                issues.append(ValidationIssue(
                    severity="error",
                    code="INVALID_NUMBER",
                    message=f"{element_name} is not a valid number: '{value}'",
                    element=element_name,
                    suggested_fix=f"Provide valid numeric value for {element_name}"
                ))
        
        return issues
    
    def _validate_business_rules(self, root: ET.Element) -> Tuple[bool, List[ValidationIssue]]:
        """Validate SSCS business rules"""
        issues = []
        rules = self.validation_rules["business_rules"]
        
        # Check vendor ID
        vendor_id_elem = root.find(".//VendorID")
        if vendor_id_elem is not None and vendor_id_elem.text:
            if vendor_id_elem.text != rules["required_vendor_id"]:
                issues.append(ValidationIssue(
                    severity="error",
                    code="INVALID_VENDOR_ID",
                    message=f"Vendor ID must be '{rules['required_vendor_id']}', got '{vendor_id_elem.text}'",
                    element="VendorID",
                    suggested_fix=f"Set VendorID to '{rules['required_vendor_id']}'"
                ))
        
        # Check NAXML version
        version = root.get('version')
        if version not in rules["supported_naxml_versions"]:
            issues.append(ValidationIssue(
                severity="warning",
                code="UNSUPPORTED_VERSION",
                message=f"NAXML version '{version}' may not be supported. Supported: {rules['supported_naxml_versions']}",
                element="version",
                suggested_fix=f"Use supported version: {rules['supported_naxml_versions'][0]}"
            ))
        
        # Check item count
        items = root.findall(".//Item")
        if len(items) > rules["max_items_per_invoice"]:
            issues.append(ValidationIssue(
                severity="error",
                code="TOO_MANY_ITEMS",
                message=f"Invoice contains {len(items)} items, maximum allowed: {rules['max_items_per_invoice']}",
                element="Items",
                suggested_fix=f"Split invoice to have at most {rules['max_items_per_invoice']} items"
            ))
        
        # Check invoice total
        total_amount = Decimal('0')
        for item in items:
            try:
                price_elem = item.find("Price")
                if price_elem is not None and price_elem.text:
                    total_amount += Decimal(price_elem.text)
            except:
                pass
        
        if total_amount > Decimal(str(rules["max_invoice_total"])):
            issues.append(ValidationIssue(
                severity="error",
                code="INVOICE_TOTAL_TOO_HIGH",
                message=f"Invoice total ${total_amount} exceeds maximum ${rules['max_invoice_total']}",
                element="InvoiceTotal",
                suggested_fix=f"Split invoice to keep total under ${rules['max_invoice_total']}"
            ))
        
        # Check price/cost ratios
        for item in items:
            price_elem = item.find("Price")
            cost_elem = item.find("Cost")
            
            if price_elem is not None and cost_elem is not None:
                try:
                    price = Decimal(price_elem.text)
                    cost = Decimal(cost_elem.text)
                    
                    if cost > 0:
                        ratio = price / cost
                        
                        if ratio > Decimal(str(rules["price_cost_ratio_max"])):
                            issues.append(ValidationIssue(
                                severity="warning",
                                code="HIGH_PRICE_COST_RATIO",
                                message=f"Price/cost ratio {ratio:.2f} is unusually high (max recommended: {rules['price_cost_ratio_max']})",
                                element="Price/Cost",
                                suggested_fix="Review pricing accuracy"
                            ))
                        
                        if ratio < Decimal(str(rules["price_cost_ratio_min"])):
                            issues.append(ValidationIssue(
                                severity="warning",
                                code="LOW_PRICE_COST_RATIO", 
                                message=f"Price/cost ratio {ratio:.2f} is unusually low (min recommended: {rules['price_cost_ratio_min']})",
                                element="Price/Cost",
                                suggested_fix="Review pricing accuracy"
                            ))
                except:
                    pass
        
        business_valid = len([i for i in issues if i.severity == 'error']) == 0
        return business_valid, issues
    
    def _is_item_valid(self, item: ET.Element) -> bool:
        """Check if individual item is valid"""
        required_fields = ["PLU", "ItemName", "Price", "Cost"]
        
        for field in required_fields:
            elem = item.find(field)
            if elem is None or not elem.text or not elem.text.strip():
                return False
        
        return True
    
    def validate_before_transmission(self, naxml_path: str) -> bool:
        """
        Validate NAXML file before EDI transmission
        
        Returns True if file is ready for transmission, False otherwise
        """
        logger.info("🔍 Pre-transmission validation starting...")
        
        result = self.validate_naxml_file(naxml_path)
        
        if result.valid:
            logger.info("✅ Pre-transmission validation PASSED - Ready for EDI delivery")
            return True
        else:
            logger.error("❌ Pre-transmission validation FAILED - EDI delivery blocked")
            
            # Log all issues
            for issue in result.issues:
                if issue.severity == 'error':
                    logger.error(f"   ERROR: {issue.message}")
                elif issue.severity == 'warning':
                    logger.warning(f"   WARNING: {issue.message}")
            
            return False
    
    def get_validation_report(self, result: SSCSValidationResult) -> str:
        """Generate human-readable validation report"""
        report = []
        report.append(f"SSCS NAXML Validation Report")
        report.append(f"=" * 40)
        report.append(f"File Status: {'✅ VALID' if result.valid else '❌ INVALID'}")
        report.append(f"Schema Valid: {'✅' if result.schema_valid else '❌'}")
        report.append(f"Business Rules Valid: {'✅' if result.business_rules_valid else '❌'}")
        report.append(f"SSCS Compatibility: {result.sscs_compatibility}")
        report.append(f"")
        report.append(f"Items: {result.validated_items}/{result.total_items} valid")
        report.append(f"Total Amount: ${result.total_amount}")
        report.append(f"NAXML Version: {result.naxml_version}")
        report.append(f"Validation Time: {result.validation_timestamp}")
        
        if result.issues:
            report.append(f"")
            report.append(f"Issues Found:")
            report.append(f"-" * 20)
            
            errors = [i for i in result.issues if i.severity == 'error']
            warnings = [i for i in result.issues if i.severity == 'warning']
            
            if errors:
                report.append(f"ERRORS ({len(errors)}):")
                for issue in errors:
                    report.append(f"  ❌ {issue.code}: {issue.message}")
                    if issue.suggested_fix:
                        report.append(f"     Fix: {issue.suggested_fix}")
            
            if warnings:
                report.append(f"WARNINGS ({len(warnings)}):")
                for issue in warnings:
                    report.append(f"  ⚠️ {issue.code}: {issue.message}")
                    if issue.suggested_fix:
                        report.append(f"     Fix: {issue.suggested_fix}")
        
        return "\n".join(report)

# Example usage and testing
if __name__ == "__main__":
    # Initialize validator
    validator = SSCSValidator()
    
    # Create test NAXML content
    test_naxml = '''<?xml version="1.0" encoding="utf-8"?>
<ItemSynch version="2.0" timestamp="2025-08-26T01:00:00Z" vendor="DABS">
  <VendorInfo>
    <VendorID>DABS</VendorID>
    <VendorName>Utah Division of Alcoholic Beverage Control</VendorName>
    <InvoiceNumber>DABS_20250826_010000</InvoiceNumber>
    <InvoiceDate>2025-08-26</InvoiceDate>
    <TotalItems>2</TotalItems>
  </VendorInfo>
  <Items>
    <Item>
      <PLU>917817</PLU>
      <ItemName>RED ROCK ELEPHINO IPA 500ml</ItemName>
      <Price>48.48</Price>
      <Cost>35.00</Cost>
      <Category>Beer</Category>
      <UPC>123456789012</UPC>
    </Item>
    <Item>
      <PLU>039271</PLU>
      <ItemName>SUGAR HOUSE VODKA 1000ml</ItemName>
      <Price>131.94</Price>
      <Cost>95.00</Cost>
      <Category>Spirits</Category>
    </Item>
  </Items>
</ItemSynch>'''
    
    # Save test file
    test_file = Path("test_naxml.xml")
    with open(test_file, 'w') as f:
        f.write(test_naxml)
    
    print("🧪 Testing SSCS validation...")
    result = validator.validate_naxml_file(str(test_file))
    
    print("\n📊 Validation Report:")
    print(validator.get_validation_report(result))
    
    print(f"\n🚀 Ready for transmission: {'✅ YES' if result.valid else '❌ NO'}")
    
    # Clean up
    test_file.unlink()
