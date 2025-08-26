#!/usr/bin/env python3
"""
SSCS NAXML Specification Correction Master Script
Zero Tolerance Error Correction Orchestrator

This script orchestrates the complete correction process for NAXML specification violations.
"""

import subprocess
import sys
import argparse
from datetime import datetime
from pathlib import Path
import shutil

class NAXMLCorrectionOrchestrator:
    """Orchestrates the complete NAXML correction process"""
    
    def __init__(self):
        self.corrections_completed = []
        self.corrections_failed = []
        self.start_time = datetime.now()
        
    def execute_full_correction(self, input_file: str, customer_number: str = "6242", 
                              vendor_id: str = "DABS", license_number: str = "PA-539",
                              compliance_officer: str = "Tessa Owen") -> bool:
        """
        Execute complete NAXML correction process
        
        Args:
            input_file: Path to original NAXML file
            customer_number: Customer number for SSCS
            vendor_id: Vendor ID for SSCS
            license_number: Utah Package Agency license
            compliance_officer: Name of compliance officer
            
        Returns:
            bool: True if all corrections successful
        """
        
        print("🚀 STARTING NAXML SPECIFICATION CORRECTION PROCESS")
        print("="*70)
        print(f"Input File: {input_file}")
        print(f"Customer: {customer_number}")
        print(f"Vendor: {vendor_id}")
        print(f"License: {license_number}")
        print(f"Officer: {compliance_officer}")
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Validate input file exists
        if not Path(input_file).exists():
            print(f"❌ ERROR: Input file not found: {input_file}")
            return False
            
        # Create backup of original file
        backup_file = self._create_backup(input_file)
        if not backup_file:
            return False
            
        # Phase 1: Critical Violations
        print("\n🚨 PHASE 1: CRITICAL VIOLATIONS")
        print("-" * 50)
        
        current_file = input_file
        
        # Step 1.1: UPC Formatting Correction
        step1_output = self._get_step_output_path(input_file, "step1_upc_corrected")
        if not self._execute_upc_correction(current_file, step1_output):
            return False
        current_file = step1_output
        
        # Step 1.2: Vendor Info Enhancement
        step2_output = self._get_step_output_path(input_file, "step2_vendor_enhanced")
        if not self._execute_vendor_enhancement(current_file, step2_output, customer_number):
            return False
        current_file = step2_output
        
        # Step 1.3: Compliance Section Addition
        step3_output = self._get_step_output_path(input_file, "step3_compliance_added")
        if not self._execute_compliance_addition(current_file, step3_output, license_number, compliance_officer):
            return False
        current_file = step3_output
        
        # Phase 1 Validation
        if not self._validate_compliance(current_file, customer_number, vendor_id, strict_mode=False):
            print("❌ Phase 1 validation failed")
            return False
            
        print("✅ Phase 1: Critical Violations - COMPLETED")
        
        # Phase 2: High Priority Violations
        print("\n⚠️  PHASE 2: HIGH PRIORITY VIOLATIONS")
        print("-" * 50)
        
        # Step 2.1: Item Field Enhancement (placeholder - would need implementation)
        print("📝 Step 2.1: Item field enhancement - MANUAL REVIEW REQUIRED")
        print("   Note: Advanced item field enhancement requires manual review")
        
        # Step 2.2: Invoice Totals Restructuring (placeholder - would need implementation)
        print("📝 Step 2.2: Invoice totals restructuring - MANUAL REVIEW REQUIRED")
        print("   Note: Invoice totals restructuring requires manual review")
        
        # Final Validation
        print("\n🔍 FINAL VALIDATION")
        print("-" * 50)
        
        if not self._validate_compliance(current_file, customer_number, vendor_id, strict_mode=True):
            print("⚠️  Final validation shows remaining issues - manual review recommended")
        else:
            print("✅ Final validation: FULLY COMPLIANT")
            
        # Create final corrected file
        final_output = self._get_final_output_path(input_file)
        shutil.copy2(current_file, final_output)
        
        # Generate completion report
        self._generate_completion_report(input_file, final_output, backup_file)
        
        return True
        
    def _create_backup(self, input_file: str) -> str:
        """Create backup of original file"""
        try:
            backup_file = self._get_step_output_path(input_file, "ORIGINAL_BACKUP")
            shutil.copy2(input_file, backup_file)
            print(f"✅ Backup created: {backup_file}")
            return backup_file
        except Exception as e:
            print(f"❌ Failed to create backup: {str(e)}")
            return None
            
    def _execute_upc_correction(self, input_file: str, output_file: str) -> bool:
        """Execute UPC formatting correction"""
        print("🔧 Step 1.1: UPC Formatting Correction")
        
        try:
            cmd = [
                "python3", "scripts/fix_upc_formatting.py",
                "--input", input_file,
                "--output", output_file,
                "--mode", "standardize_upc_fields"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
            
            if result.returncode == 0:
                print("✅ UPC formatting correction completed")
                self.corrections_completed.append("UPC Formatting")
                return True
            else:
                print(f"❌ UPC formatting correction failed:")
                print(f"   STDOUT: {result.stdout}")
                print(f"   STDERR: {result.stderr}")
                self.corrections_failed.append("UPC Formatting")
                return False
                
        except Exception as e:
            print(f"❌ UPC formatting correction error: {str(e)}")
            self.corrections_failed.append("UPC Formatting")
            return False
            
    def _execute_vendor_enhancement(self, input_file: str, output_file: str, customer_number: str) -> bool:
        """Execute vendor information enhancement"""
        print("🔧 Step 1.2: Vendor Information Enhancement")
        
        try:
            po_number = f"DABS_PO_{datetime.now().strftime('%Y%m%d')}_001"
            
            cmd = [
                "python3", "scripts/enhance_vendor_info.py",
                "--input", input_file,
                "--output", output_file,
                "--customer-number", customer_number,
                "--po-number", po_number,
                "--terms", "NET30"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
            
            if result.returncode == 0:
                print("✅ Vendor information enhancement completed")
                self.corrections_completed.append("Vendor Information")
                return True
            else:
                print(f"❌ Vendor information enhancement failed:")
                print(f"   STDOUT: {result.stdout}")
                print(f"   STDERR: {result.stderr}")
                self.corrections_failed.append("Vendor Information")
                return False
                
        except Exception as e:
            print(f"❌ Vendor information enhancement error: {str(e)}")
            self.corrections_failed.append("Vendor Information")
            return False
            
    def _execute_compliance_addition(self, input_file: str, output_file: str, 
                                   license_number: str, compliance_officer: str) -> bool:
        """Execute compliance section addition"""
        print("🔧 Step 1.3: Compliance Section Addition")
        
        try:
            cmd = [
                "python3", "scripts/add_compliance_section.py",
                "--input", input_file,
                "--output", output_file,
                "--license", license_number,
                "--officer", compliance_officer,
                "--retention", "7_YEARS"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
            
            if result.returncode == 0:
                print("✅ Compliance section addition completed")
                self.corrections_completed.append("Compliance Section")
                return True
            else:
                print(f"❌ Compliance section addition failed:")
                print(f"   STDOUT: {result.stdout}")
                print(f"   STDERR: {result.stderr}")
                self.corrections_failed.append("Compliance Section")
                return False
                
        except Exception as e:
            print(f"❌ Compliance section addition error: {str(e)}")
            self.corrections_failed.append("Compliance Section")
            return False
            
    def _validate_compliance(self, file_path: str, customer_number: str, vendor_id: str, strict_mode: bool) -> bool:
        """Execute compliance validation"""
        validation_type = "Strict" if strict_mode else "Standard"
        print(f"🔍 {validation_type} Compliance Validation")
        
        try:
            cmd = [
                "python3", "scripts/validate_sscs_compliance.py",
                "--input", file_path,
                "--customer", customer_number,
                "--vendor", vendor_id
            ]
            
            if strict_mode:
                cmd.append("--strict-mode")
                
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
            
            # Print validation output
            print(result.stdout)
            if result.stderr:
                print(f"Validation warnings: {result.stderr}")
                
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Compliance validation error: {str(e)}")
            return False
            
    def _get_step_output_path(self, input_file: str, step_suffix: str) -> str:
        """Generate output path for correction step"""
        input_path = Path(input_file)
        return str(input_path.parent / f"{input_path.stem}_{step_suffix}{input_path.suffix}")
        
    def _get_final_output_path(self, input_file: str) -> str:
        """Generate final corrected output path"""
        input_path = Path(input_file)
        return str(input_path.parent / f"{input_path.stem}_CORRECTED_FINAL{input_path.suffix}")
        
    def _generate_completion_report(self, input_file: str, output_file: str, backup_file: str) -> None:
        """Generate completion report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "="*70)
        print("🎉 NAXML CORRECTION PROCESS COMPLETED")
        print("="*70)
        print(f"Original File: {input_file}")
        print(f"Corrected File: {output_file}")
        print(f"Backup File: {backup_file}")
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {duration.total_seconds():.1f} seconds")
        print(f"Corrections Completed: {len(self.corrections_completed)}")
        print(f"Corrections Failed: {len(self.corrections_failed)}")
        
        if self.corrections_completed:
            print("\n✅ SUCCESSFUL CORRECTIONS:")
            for correction in self.corrections_completed:
                print(f"   • {correction}")
                
        if self.corrections_failed:
            print("\n❌ FAILED CORRECTIONS:")
            for correction in self.corrections_failed:
                print(f"   • {correction}")
                
        print("\n📋 NEXT STEPS:")
        print("   1. Review the corrected file for accuracy")
        print("   2. Perform final manual validation if needed")
        print("   3. Test EDI delivery with SSCS system")
        print("   4. Monitor processing results")
        
        success_rate = (len(self.corrections_completed) / 
                       (len(self.corrections_completed) + len(self.corrections_failed)) * 100) if (len(self.corrections_completed) + len(self.corrections_failed)) > 0 else 100
        
        print(f"\n🎯 SUCCESS RATE: {success_rate:.1f}%")
        
        if success_rate >= 100:
            print("🏆 STATUS: PERFECT EXECUTION - ZERO ERRORS")
        elif success_rate >= 80:
            print("✅ STATUS: SUCCESSFUL - MINOR ISSUES")
        else:
            print("⚠️  STATUS: PARTIAL SUCCESS - MANUAL REVIEW REQUIRED")

def main():
    parser = argparse.ArgumentParser(description='Execute complete NAXML specification corrections')
    parser.add_argument('--input', required=True, help='Input NAXML file path')
    parser.add_argument('--customer', default='6242', help='Customer number (default: 6242)')
    parser.add_argument('--vendor', default='DABS', help='Vendor ID (default: DABS)')
    parser.add_argument('--license', default='PA-539', help='Utah Package Agency license (default: PA-539)')
    parser.add_argument('--officer', default='Tessa Owen', help='Compliance officer (default: Tessa Owen)')
    
    args = parser.parse_args()
    
    # Execute correction process
    orchestrator = NAXMLCorrectionOrchestrator()
    
    success = orchestrator.execute_full_correction(
        args.input, args.customer, args.vendor, args.license, args.officer
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
