#!/usr/bin/env python3
"""
NAXML Structure Validation Script
Validates SSCS CPB NAXML files for compliance and structure
"""

import xml.etree.ElementTree as ET
import sys
from pathlib import Path
from datetime import datetime

def validate_naxml_file(file_path):
    """Validate NAXML file structure and content"""
    print(f"🔍 Validating NAXML file: {file_path}")
    print("=" * 60)
    
    try:
        # Parse XML
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Validation results
        validation_results = {
            "file_exists": True,
            "valid_xml": True,
            "root_element": False,
            "header_present": False,
            "items_present": False,
            "vendor_info": False,
            "pricing_data": False,
            "required_fields": False,
            "errors": []
        }
        
        print("✅ XML parsing: SUCCESS")
        
        # Validate root element
        if root.tag == "ItemSynch":
            validation_results["root_element"] = True
            print("✅ Root element: ItemSynch (correct)")
            
            # Check version
            version = root.get("version")
            vendor = root.get("vendor")
            timestamp = root.get("timestamp")
            
            print(f"📋 Version: {version}")
            print(f"📋 Vendor: {vendor}")
            print(f"📋 Timestamp: {timestamp}")
            
            if vendor == "DABS":
                validation_results["vendor_info"] = True
                print("✅ Vendor: DABS (correct)")
            else:
                validation_results["errors"].append(f"Incorrect vendor: {vendor}")
                
        else:
            validation_results["errors"].append(f"Incorrect root element: {root.tag}")
            
        # Validate Header
        header = root.find("Header")
        if header is not None:
            validation_results["header_present"] = True
            print("✅ Header section: PRESENT")
            
            # Check header fields
            header_fields = {}
            for child in header:
                header_fields[child.tag] = child.text
                
            print("📋 Header fields:")
            for field, value in header_fields.items():
                print(f"   {field}: {value}")
                
            # Validate required header fields
            required_header_fields = ["Source", "Destination", "VendorName", "VendorZone", "RecordCount"]
            missing_fields = [field for field in required_header_fields if field not in header_fields]
            
            if not missing_fields:
                validation_results["required_fields"] = True
                print("✅ Required header fields: ALL PRESENT")
            else:
                validation_results["errors"].append(f"Missing header fields: {missing_fields}")
                
        else:
            validation_results["errors"].append("Header section missing")
            
        # Validate Items
        items = root.find("Items")
        if items is not None:
            validation_results["items_present"] = True
            item_count = len(items.findall("Item"))
            print(f"✅ Items section: PRESENT ({item_count} items)")
            
            # Validate first item structure
            if item_count > 0:
                first_item = items.find("Item")
                item_fields = {}
                
                # Direct fields
                for child in first_item:
                    if child.tag == "Pricing":
                        pricing_fields = {pc.tag: pc.text for pc in child}
                        item_fields["Pricing"] = pricing_fields
                        if "VendorListPrice" in pricing_fields:
                            validation_results["pricing_data"] = True
                    elif child.tag == "Attributes":
                        attr_fields = {ac.tag: ac.text for ac in child}
                        item_fields["Attributes"] = attr_fields
                    else:
                        item_fields[child.tag] = child.text
                        
                print("📋 Sample item structure:")
                for field, value in item_fields.items():
                    if isinstance(value, dict):
                        print(f"   {field}:")
                        for subfield, subvalue in value.items():
                            print(f"     {subfield}: {subvalue}")
                    else:
                        print(f"   {field}: {value}")
                        
                # Check required item fields
                required_item_fields = ["VendorItemCode", "Description", "Status"]
                missing_item_fields = [field for field in required_item_fields if field not in item_fields]
                
                if not missing_item_fields:
                    print("✅ Required item fields: ALL PRESENT")
                else:
                    validation_results["errors"].append(f"Missing item fields: {missing_item_fields}")
                    
        else:
            validation_results["errors"].append("Items section missing")
            
        # Summary
        print("\n" + "=" * 60)
        print("🎯 VALIDATION SUMMARY")
        print("=" * 60)
        
        passed_checks = sum(1 for key, value in validation_results.items() 
                          if key != "errors" and value is True)
        total_checks = len([key for key in validation_results.keys() if key != "errors"])
        
        print(f"✅ Passed checks: {passed_checks}/{total_checks}")
        
        if validation_results["errors"]:
            print("❌ Errors found:")
            for error in validation_results["errors"]:
                print(f"   • {error}")
        else:
            print("🎉 NO ERRORS FOUND")
            
        # Overall status
        if len(validation_results["errors"]) == 0 and passed_checks >= 6:
            print("\n🎊 OVERALL STATUS: VALID FOR SSCS CPB IMPORT")
            return True
        else:
            print("\n⚠️  OVERALL STATUS: NEEDS ATTENTION")
            return False
            
    except ET.ParseError as e:
        print(f"❌ XML parsing failed: {e}")
        return False
    except Exception as e:
        print(f"💥 Validation error: {e}")
        return False

def main():
    """Main validation function"""
    # Find the most recent NAXML file
    cpb_dir = Path("exports/sscs_cpb")
    if not cpb_dir.exists():
        print("❌ CPB export directory not found")
        return False
        
    naxml_files = list(cpb_dir.glob("DABS_*_ItemPrice.xml"))
    if not naxml_files:
        print("❌ No NAXML files found in CPB directory")
        return False
        
    # Get the most recent file
    latest_file = max(naxml_files, key=lambda f: f.stat().st_mtime)
    
    print(f"🎯 SSCS CPB NAXML VALIDATION")
    print(f"📁 File: {latest_file.name}")
    print(f"📊 Size: {latest_file.stat().st_size:,} bytes")
    print(f"⏰ Modified: {datetime.fromtimestamp(latest_file.stat().st_mtime)}")
    print()
    
    return validate_naxml_file(latest_file)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
