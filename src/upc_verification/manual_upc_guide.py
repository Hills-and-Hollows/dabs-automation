#!/usr/bin/env python3
"""
Manual UPC Lookup Guide and NAXML Update Tool
Guide for finding UPCs manually and updating the NAXML file
"""

import asyncio
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
import sys
import os

sys.path.append(os.path.dirname(__file__))
from verifone_formatter import VerifoneFormatter

class ManualUPCGuide:
    """Guide and tools for manual UPC lookup and NAXML updates"""
    
    def __init__(self, naxml_path: str = "src/edi/data/edi_output/DABS_20250825_143251_ItemPrice_WithUPC.xml"):
        self.naxml_path = Path(naxml_path)
    
    def print_manual_lookup_guide(self):
        """Print comprehensive guide for manual UPC lookup"""
        
        print("🔍 Manual UPC Lookup Guide - DABS Product Locator")
        print("=" * 60)
        print()
        
        print("🌐 DABS Product Locator URL:")
        print("   https://webapps2.abc.utah.gov/ProdApps/ProductLocatorCore")
        print()
        
        print("📋 Items Requiring Manual Lookup:")
        print()
        
        # Item 1: Sugar House Vodka
        print("1️⃣  SUGAR HOUSE VODKA 1750ml")
        print("   DABS Code: 039593")
        print("   Price: $227.94")
        print("   Category: SPIRITS")
        print()
        print("   🔍 Search Strategies:")
        print("   • Search by DABS Code: '039593'")
        print("   • Search by Brand: 'SUGAR HOUSE'")
        print("   • Search by Product: 'SUGAR HOUSE VODKA'")
        print("   • Search by Size: '1750ml VODKA'")
        print("   • Alternative spellings: 'SUGARHOUSE', 'SUGAR-HOUSE'")
        print()
        
        # Item 2: Helper Beer
        print("2️⃣  HELPER BEER CIRCLE BACK IPA 473ml")
        print("   DABS Code: 926272")
        print("   Price: $108.00")
        print("   Category: BEER")
        print()
        print("   🔍 Search Strategies:")
        print("   • Search by DABS Code: '926272'")
        print("   • Search by Brewery: 'HELPER'")
        print("   • Search by Beer Name: 'CIRCLE BACK IPA'")
        print("   • Search by Style: 'IPA'")
        print("   • Search by Size: '473ml' or '16oz'")
        print("   • Alternative: 'HELPER BREWING'")
        print()
        
        print("📝 Manual Lookup Steps:")
        print("1. Go to DABS Product Locator website")
        print("2. Try each search strategy listed above")
        print("3. Look for UPC/Barcode information in product details")
        print("4. Verify UPC is 12 digits and passes checksum validation")
        print("5. Record the UPC and run the update tool below")
        print()
        
        print("⚡ Quick Update Command:")
        print("   python3 src/upc_verification/manual_upc_guide.py --update")
        print("   (Will prompt for UPC codes)")
        print()
        
        print("🎯 Expected UPC Format:")
        print("   • 12 digits (e.g., 123456789012)")
        print("   • Will be auto-converted to Verifone 11-digit format")
        print("   • Must pass checksum validation")
        print()
    
    def validate_upc(self, upc: str) -> tuple[bool, str]:
        """Validate UPC format and checksum"""
        if not upc or not upc.isdigit():
            return False, "UPC must contain only digits"
        
        if len(upc) != 12:
            return False, f"UPC must be 12 digits, got {len(upc)}"
        
        if not VerifoneFormatter.validate_upc_checksum(upc):
            return False, "UPC checksum validation failed"
        
        return True, "Valid UPC"
    
    def update_naxml_with_upcs(self, upc_updates: dict):
        """Update NAXML file with manually found UPCs"""
        
        if not self.naxml_path.exists():
            print(f"❌ NAXML file not found: {self.naxml_path}")
            return False
        
        try:
            # Parse existing NAXML
            tree = ET.parse(self.naxml_path)
            root = tree.getroot()
            
            # Track updates
            updates_made = 0
            
            # Find items section
            items_section = root.find('Items')
            if items_section is None:
                print("❌ Items section not found in NAXML")
                return False
            
            # Update each item
            for item in items_section.findall('Item'):
                plu_element = item.find('PLU')
                if plu_element is not None:
                    dabs_code = plu_element.text
                    
                    if dabs_code in upc_updates:
                        upc_12 = upc_updates[dabs_code]
                        verifone_upc = VerifoneFormatter.format_for_verifone(upc_12)
                        
                        # Remove existing UPC elements
                        for old_upc in item.findall('UPC'):
                            item.remove(old_upc)
                        for old_verifone in item.findall('VerifoneUPC'):
                            item.remove(old_verifone)
                        for old_verification in item.findall('UPCVerification'):
                            item.remove(old_verification)
                        
                        # Add new UPC elements
                        upc_element = ET.SubElement(item, 'UPC')
                        upc_element.text = upc_12
                        upc_element.set('format', 'UPC-A')
                        
                        verifone_element = ET.SubElement(item, 'VerifoneUPC')
                        verifone_element.text = verifone_upc
                        verifone_element.set('format', '11-digit')
                        
                        # Add verification metadata
                        verification = ET.SubElement(item, 'UPCVerification')
                        ET.SubElement(verification, 'Confidence').text = '1.00'
                        ET.SubElement(verification, 'Sources').text = 'manual_dabs_lookup'
                        ET.SubElement(verification, 'Verified').text = 'true'
                        
                        updates_made += 1
                        print(f"✅ Updated {dabs_code}: {upc_12} → {verifone_upc}")
            
            # Update summary statistics
            summary = root.find('Summary')
            if summary is not None:
                items_with_upc = summary.find('ItemsWithUPC')
                items_verified = summary.find('ItemsVerified')
                coverage_rate = summary.find('UPCCoverageRate')
                verification_rate = summary.find('VerificationRate')
                
                if items_with_upc is not None:
                    current_count = int(items_with_upc.text)
                    new_count = current_count + updates_made
                    items_with_upc.text = str(new_count)
                    
                    # Update rates
                    total_items = int(summary.find('TotalItems').text)
                    if coverage_rate is not None:
                        coverage_rate.text = f"{(new_count/total_items*100):.1f}%"
                    if verification_rate is not None:
                        verification_rate.text = f"{(new_count/total_items*100):.1f}%"
                    if items_verified is not None:
                        items_verified.text = str(new_count)  # Manual lookups are verified
            
            # Save updated NAXML
            rough_string = ET.tostring(root, 'unicode')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")
            
            # Remove empty lines
            lines = [line for line in pretty_xml.split('\n') if line.strip()]
            final_xml = '\n'.join(lines)
            
            # Create backup
            backup_path = self.naxml_path.with_suffix('.xml.backup')
            self.naxml_path.rename(backup_path)
            print(f"📋 Backup created: {backup_path}")
            
            # Write updated file
            with open(self.naxml_path, 'w', encoding='utf-8') as f:
                f.write(final_xml)
            
            print(f"✅ NAXML updated successfully!")
            print(f"📄 File: {self.naxml_path}")
            print(f"🔄 Updates made: {updates_made}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating NAXML: {e}")
            return False
    
    def interactive_update(self):
        """Interactive UPC update process"""
        
        print("🔄 Interactive UPC Update Tool")
        print("=" * 40)
        print()
        
        remaining_items = {
            "039593": "SUGAR HOUSE VODKA 1750ml",
            "926272": "HELPER BEER CIRCLE BACK IPA 473ml"
        }
        
        upc_updates = {}
        
        for dabs_code, item_name in remaining_items.items():
            print(f"📋 {item_name}")
            print(f"   DABS Code: {dabs_code}")
            
            while True:
                upc_input = input(f"   Enter UPC (12 digits) or 'skip': ").strip()
                
                if upc_input.lower() == 'skip':
                    print(f"   ⏭️  Skipped {dabs_code}")
                    break
                
                # Validate UPC
                is_valid, message = self.validate_upc(upc_input)
                
                if is_valid:
                    verifone_upc = VerifoneFormatter.format_for_verifone(upc_input)
                    print(f"   ✅ Valid UPC: {upc_input}")
                    print(f"   🔄 Verifone format: {verifone_upc}")
                    
                    confirm = input(f"   Confirm this UPC? (y/n): ").strip().lower()
                    if confirm == 'y':
                        upc_updates[dabs_code] = upc_input
                        print(f"   ✅ Added to updates")
                        break
                else:
                    print(f"   ❌ {message}")
                    print(f"   Please try again or type 'skip'")
            
            print()
        
        if upc_updates:
            print(f"📊 Ready to update {len(upc_updates)} items:")
            for code, upc in upc_updates.items():
                verifone = VerifoneFormatter.format_for_verifone(upc)
                print(f"   {code}: {upc} → {verifone}")
            
            print()
            confirm = input("Proceed with NAXML update? (y/n): ").strip().lower()
            
            if confirm == 'y':
                success = self.update_naxml_with_upcs(upc_updates)
                if success:
                    print("\n🎊 Update completed successfully!")
                    print("📄 Your NAXML file now has the manually found UPCs")
                    print("✅ Ready for EDI delivery to SSCS")
                else:
                    print("\n❌ Update failed - check error messages above")
            else:
                print("❌ Update cancelled")
        else:
            print("ℹ️  No UPCs to update")

def main():
    """Main function"""
    guide = ManualUPCGuide()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--update':
        guide.interactive_update()
    else:
        guide.print_manual_lookup_guide()

if __name__ == "__main__":
    main()
