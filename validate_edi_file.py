#!/usr/bin/env python3
"""
Final EDI Validation for SSCS Compliance
Comprehensive validation of NAXML file before EDI delivery
"""

import xml.etree.ElementTree as ET
from pathlib import Path

def validate_sscs_edi_file(file_path):
    """Validate NAXML file against SSCS EDI specifications"""
    
    print('🔍 FINAL EDI REVIEW - SSCS COMPLIANCE VALIDATION')
    print('=' * 60)
    
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    validation_results = {
        'xml_structure': False,
        'vendor_info': False,
        'items_validation': False,
        'totals_validation': False,
        'dabs_codes': False,
        'upc_format': False,
        'overall_compliance': False
    }
    
    # 1. Validate XML structure
    print('\n✅ XML STRUCTURE VALIDATION:')
    xml_valid = (
        root.tag == 'ItemSynch' and
        root.get('version') == '2.0' and
        root.get('vendor') == 'DABS'
    )
    print(f'   Root Element: {root.tag} (Expected: ItemSynch)')
    print(f'   Version: {root.get("version")} (Expected: 2.0)')
    print(f'   Vendor: {root.get("vendor")} (Expected: DABS)')
    print(f'   Status: {"✅ PASS" if xml_valid else "❌ FAIL"}')
    validation_results['xml_structure'] = xml_valid
    
    # 2. Validate VendorInfo
    print('\n✅ VENDOR INFO VALIDATION:')
    vendor_info = root.find('VendorInfo')
    vendor_valid = (
        vendor_info.find('VendorID').text == 'DABS' and
        vendor_info.find('CustomerNumber').text == '6242' and

        'v6242s1@edidelivery.com' in vendor_info.find('EDIDeliveryEmail').text
    )
    print(f'   VendorID: {vendor_info.find("VendorID").text} (Expected: DABS)')
    print(f'   Customer #: {vendor_info.find("CustomerNumber").text} (Expected: 6242)')

    print(f'   EDI Email: {vendor_info.find("EDIDeliveryEmail").text}')
    print(f'   Status: {"✅ PASS" if vendor_valid else "❌ FAIL"}')
    validation_results['vendor_info'] = vendor_valid
    
    # 3. Validate Items
    items = root.find('Items').findall('Item')
    print(f'\n✅ ITEMS VALIDATION:')
    print(f'   Total Items: {len(items)}')
    
    # Check for required fields and calculate totals
    total_cost = 0.0
    total_retail = 0.0
    items_with_upc = 0
    dabs_codes = []
    required_fields_valid = True
    
    for item in items:
        plu = item.find('PLU').text
        price_elem = item.find('Price')
        cost_elem = item.find('Cost')
        upc_elem = item.find('UPC')
        
        # Check required fields exist
        if not all([plu, price_elem is not None, cost_elem is not None]):
            required_fields_valid = False
            continue
            
        price = float(price_elem.text)
        cost = float(cost_elem.text)
        upc = upc_elem.text if upc_elem is not None else ""
        
        dabs_codes.append(plu)
        total_cost += cost
        total_retail += price
        
        if upc and upc.strip():
            items_with_upc += 1
    
    # Check for duplicates
    duplicate_codes = set([code for code in dabs_codes if dabs_codes.count(code) > 1])
    
    items_valid = required_fields_valid and len(duplicate_codes) == 0
    print(f'   Required Fields Present: {"✅ YES" if required_fields_valid else "❌ NO"}')
    print(f'   Items with UPC: {items_with_upc}')
    print(f'   UPC Coverage: {(items_with_upc/len(items)*100):.1f}%')
    print(f'   Duplicate DABS Codes: {len(duplicate_codes)} (Expected: 0)')
    print(f'   Status: {"✅ PASS" if items_valid else "❌ FAIL"}')
    validation_results['items_validation'] = items_valid
    
    # 4. Validate Totals
    print('\n✅ TOTALS VALIDATION:')
    invoice_totals = root.find('InvoiceTotals')
    file_subtotal = float(invoice_totals.find('SubTotal').text)
    file_retail_total = float(invoice_totals.find('RetailTotal').text)
    file_item_count = int(invoice_totals.find('ItemCount').text)
    
    totals_valid = (
        abs(total_cost - file_subtotal) < 0.01 and
        abs(total_retail - file_retail_total) < 0.01 and
        len(items) == file_item_count
    )
    
    print(f'   Calculated Cost Total: ${total_cost:.2f}')
    print(f'   File SubTotal: ${file_subtotal:.2f}')
    print(f'   Cost Match: {"✅ YES" if abs(total_cost - file_subtotal) < 0.01 else "❌ NO"}')
    print(f'   Calculated Retail Total: ${total_retail:.2f}')
    print(f'   File Retail Total: ${file_retail_total:.2f}')
    print(f'   Retail Match: {"✅ YES" if abs(total_retail - file_retail_total) < 0.01 else "❌ NO"}')
    print(f'   Item Count Match: {"✅ YES" if len(items) == file_item_count else "❌ NO"}')
    print(f'   Status: {"✅ PASS" if totals_valid else "❌ FAIL"}')
    validation_results['totals_validation'] = totals_valid
    
    # 5. Validate specific DABS codes from original PDF
    expected_codes = ['039593', '087123', '523110', '580790', '733238', '908418', '918761', '918951', '919829', '926272']
    missing_codes = [code for code in expected_codes if code not in dabs_codes]
    extra_codes = [code for code in dabs_codes if code not in expected_codes]
    
    dabs_codes_valid = len(missing_codes) == 0 and len(extra_codes) == 0
    print('\n✅ DABS CODE VALIDATION:')
    print(f'   Expected Codes: {len(expected_codes)}')
    print(f'   Found Codes: {len(dabs_codes)}')
    print(f'   Missing Codes: {missing_codes if missing_codes else "None"}')
    print(f'   Extra Codes: {extra_codes if extra_codes else "None"}')
    print(f'   Status: {"✅ PASS" if dabs_codes_valid else "❌ FAIL"}')
    validation_results['dabs_codes'] = dabs_codes_valid
    
    # 6. Validate UPC format for verified items
    print('\n✅ UPC FORMAT VALIDATION:')
    upc_format_valid = True
    verified_upcs = 0
    
    for item in items:
        upc_elem = item.find('UPC')
        upc_verified_elem = item.find('UPCVerified')
        plu = item.find('PLU').text
        
        if upc_elem is not None and upc_verified_elem is not None:
            upc = upc_elem.text
            upc_verified = upc_verified_elem.text
            
            if upc and upc.strip() and upc_verified == 'true':
                verified_upcs += 1
                verifone_upc_elem = item.find('VerifoneUPC')
                verifone_upc = verifone_upc_elem.text if verifone_upc_elem is not None else 'None'
                print(f'   {plu}: UPC-12: {upc}, Verifone-11: {verifone_upc}')
                
                # Validate UPC length
                if len(upc) != 12:
                    print(f'   ❌ Invalid UPC length for {plu}: {len(upc)} (Expected: 12)')
                    upc_format_valid = False
    
    print(f'   Verified UPCs: {verified_upcs}')
    print(f'   Status: {"✅ PASS" if upc_format_valid else "❌ FAIL"}')
    validation_results['upc_format'] = upc_format_valid
    
    # 7. Overall Compliance Check
    all_checks_pass = all(validation_results.values())
    validation_results['overall_compliance'] = all_checks_pass
    
    print('\n🎯 FINAL COMPLIANCE STATUS:')
    if all_checks_pass:
        print('✅ ALL COMPLIANCE CHECKS PASSED - READY FOR EDI DELIVERY')
        print('\n📧 EDI DELIVERY READY:')
        print(f'   To: v6242s1@edidelivery.com')
        print(f'   Subject: DABS_ItemPrice_20250825.xml')
        print(f'   Attachment: {Path(file_path).name}')
        print(f'   Body: DABS Vendor Price Update - {len(items)} items')
    else:
        print('❌ COMPLIANCE ISSUES FOUND - REVIEW REQUIRED')
        failed_checks = [k for k, v in validation_results.items() if not v]
        print(f'   Failed Checks: {failed_checks}')
    
    return validation_results

if __name__ == "__main__":
    file_path = "src/edi/data/edi_output/DABS_20250825_151238_ItemPrice_SSCS_COMPLIANT.xml"
    results = validate_sscs_edi_file(file_path)
