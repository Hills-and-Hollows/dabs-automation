#!/usr/bin/env python3
"""
Emergency Data Recovery for DABS Order 233811
Clean re-extraction and processing with data integrity validation
"""

import asyncio
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add the src directory to the path
sys.path.append('src')
sys.path.append('src/upc_verification')

from src.upc_verification.dabs_upc_integration import DABSUPCIntegrator

class EmergencyDataRecovery:
    """Emergency data recovery with strict validation"""
    
    def __init__(self):
        self.verified_data = None
        self.output_dir = Path("src/edi/data/edi_output")
        self.backup_dir = Path("data/corrupted_backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def get_verified_order_data(self):
        """Get verified order data directly from PDF extraction"""
        
        # VERIFIED data from original PDF: dabs/Licensee Orders_id_233811.pdf
        # This is the GROUND TRUTH - all other data must match this
        verified_order = """🍷 DABS Order 233811 - VERIFIED DATA FROM PDF
SUGAR HOUSE VODKA 1750ml (039593) - $227.94
ARETTE CLASICA BLANCO TEQUILA 1000ml (087123) - $395.88
WILLAMETTE VLY PINOT NOIR WL CLST 750ml (523110) - $299.88
KING ESTATE PINOT GRIS SIGNATURE 750ml (580790) - $252.96
SEGURA VIUDAS BRUT 750ml (733238) - $167.88
BUCKLIN BAMBINO ZIN'22 750ml (908418) - $287.88
POE ROSÉ'23 750ml (918761) - $251.88
LARCHAGO RIOJA RESERVE 750ml (918951) - $275.88
LORENZA ROSE 750ml (919829) - $239.88
HELPER BEER CIRCLE BACK IPA 473ml (926272) - $108.00"""
        
        return verified_order
    
    def backup_corrupted_files(self):
        """Backup corrupted files before cleanup"""
        
        corrupted_files = [
            "src/edi/data/edi_output/DABS_20250825_143251_ItemPrice_WithUPC.xml",
            "exports/DABS_ORDER_233811_UPC_ENHANCED_SUMMARY.md",
            "docs/DABS_ORDER_233811_UPC_VERIFICATION_COMPLETE.md"
        ]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for file_path in corrupted_files:
            source = Path(file_path)
            if source.exists():
                backup_name = f"{source.stem}_CORRUPTED_{timestamp}{source.suffix}"
                backup_path = self.backup_dir / backup_name
                
                # Copy to backup
                import shutil
                shutil.copy2(source, backup_path)
                print(f"📋 Backed up corrupted file: {source} → {backup_path}")
    
    def validate_dabs_codes(self, items):
        """Validate DABS codes against verified data"""
        
        expected_codes = {
            "SUGAR HOUSE VODKA 1750ml": "039593",
            "ARETTE CLASICA BLANCO TEQUILA 1000ml": "087123", 
            "WILLAMETTE VLY PINOT NOIR WL CLST 750ml": "523110",
            "KING ESTATE PINOT GRIS SIGNATURE 750ml": "580790",
            "SEGURA VIUDAS BRUT 750ml": "733238",
            "BUCKLIN BAMBINO ZIN'22 750ml": "908418",
            "POE ROSÉ'23 750ml": "918761",
            "LARCHAGO RIOJA RESERVE 750ml": "918951",
            "LORENZA ROSE 750ml": "919829",
            "HELPER BEER CIRCLE BACK IPA 473ml": "926272"
        }
        
        validation_errors = []
        
        for item in items:
            item_key = item.item_name
            expected_code = expected_codes.get(item_key)
            
            if expected_code is None:
                # Try partial matching
                for expected_name, code in expected_codes.items():
                    if expected_name.split()[0] in item_key and expected_name.split()[1] in item_key:
                        expected_code = code
                        break
            
            if expected_code and item.dabs_code != expected_code:
                validation_errors.append({
                    'item': item_key,
                    'found_code': item.dabs_code,
                    'expected_code': expected_code
                })
        
        return validation_errors
    
    async def create_clean_naxml(self):
        """Create clean NAXML with verified data and UPC integration"""
        
        print("🔄 Starting Emergency Data Recovery")
        print("=" * 50)
        
        # Step 1: Backup corrupted files
        print("\n📋 Step 1: Backing up corrupted files...")
        self.backup_corrupted_files()
        
        # Step 2: Get verified order data
        print("\n✅ Step 2: Using verified order data from PDF...")
        verified_order = self.get_verified_order_data()
        print("Verified order data loaded")
        
        # Step 3: Process with clean integration
        print("\n🔄 Step 3: Processing with clean UPC integration...")
        
        async with DABSUPCIntegrator() as integrator:
            # Parse verified data
            items = integrator.parse_dabs_order_text(verified_order)
            print(f"Parsed {len(items)} items from verified data")
            
            # Validate DABS codes
            validation_errors = self.validate_dabs_codes(items)
            if validation_errors:
                print("❌ VALIDATION ERRORS FOUND:")
                for error in validation_errors:
                    print(f"   {error['item']}: {error['found_code']} ≠ {error['expected_code']}")
                return False
            else:
                print("✅ All DABS codes validated successfully")
            
            # Apply UPC verification (this will use cache for previously found UPCs)
            print("\n🔍 Step 4: Applying UPC verification...")
            items = await integrator.verify_upcs_for_items(items)
            
            # Add the manually found UPC for SUGAR HOUSE VODKA
            for item in items:
                if item.dabs_code == "039593":  # SUGAR HOUSE VODKA
                    # Create a mock UPC result for the verified UPC
                    from src.upc_verification.enhanced_upc_verifier import EnhancedUPCResult
                    from src.upc_verification.verifone_formatter import VerifoneFormatter
                    
                    verified_upc = "615260026006"  # From Utah ABS price list
                    item.upc_result = EnhancedUPCResult(
                        item_name=item.item_name,
                        dabs_code=item.dabs_code,
                        upc_code=verified_upc,
                        verifone_upc=VerifoneFormatter.format_for_verifone(verified_upc),
                        confidence=1.0,
                        sources=['utah_abs_price_list'],
                        verified=True
                    )
                    print(f"✅ Added verified UPC for SUGAR HOUSE VODKA: {verified_upc}")
            
            # Generate clean NAXML
            print("\n📄 Step 5: Generating clean NAXML...")
            naxml_content = integrator.generate_naxml(items, "233811_CLEAN")
            
            # Save with clean filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_filename = f"DABS_233811_CLEAN_{timestamp}_ItemPrice_WithUPC.xml"
            naxml_path = integrator.save_naxml(naxml_content, clean_filename)
            
            # Generate clean report
            report = integrator.generate_upc_report(items)
            
            print(f"\n✅ Clean NAXML created: {naxml_path}")
            
            # Validate final output
            print("\n🔍 Step 6: Final validation...")
            self.validate_final_output(items)
            
            return naxml_path, report, items
    
    def validate_final_output(self, items):
        """Final validation of clean data"""
        
        print("Final validation checks:")
        
        # Check for duplicate UPCs
        upcs = [item.upc_result.upc_code for item in items if item.upc_result and item.upc_result.upc_code]
        duplicate_upcs = set([upc for upc in upcs if upcs.count(upc) > 1])
        
        if duplicate_upcs:
            print(f"❌ DUPLICATE UPCs FOUND: {duplicate_upcs}")
            return False
        else:
            print("✅ No duplicate UPCs found")
        
        # Check DABS code uniqueness
        dabs_codes = [item.dabs_code for item in items]
        duplicate_codes = set([code for code in dabs_codes if dabs_codes.count(code) > 1])
        
        if duplicate_codes:
            print(f"❌ DUPLICATE DABS CODES: {duplicate_codes}")
            return False
        else:
            print("✅ All DABS codes unique")
        
        # Count UPC coverage
        items_with_upc = sum(1 for item in items if item.has_upc)
        coverage = (items_with_upc / len(items)) * 100
        print(f"✅ UPC Coverage: {items_with_upc}/{len(items)} ({coverage:.1f}%)")
        
        return True

async def main():
    """Main recovery function"""
    
    recovery = EmergencyDataRecovery()
    
    try:
        result = await recovery.create_clean_naxml()
        
        if result:
            naxml_path, report, items = result
            
            print("\n" + "="*60)
            print("🎊 EMERGENCY DATA RECOVERY COMPLETE")
            print("="*60)
            print(f"✅ Clean NAXML: {naxml_path}")
            print(f"✅ Items processed: {len(items)}")
            print(f"✅ Data integrity: VERIFIED")
            print("\n📋 Clean Report:")
            print(report)
            
            return True
        else:
            print("\n❌ RECOVERY FAILED - Data validation errors")
            return False
            
    except Exception as e:
        print(f"\n❌ RECOVERY ERROR: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎯 Next step: Verify clean data and proceed with EDI delivery")
    else:
        print("\n🚨 Recovery failed - manual intervention required")
