#!/usr/bin/env python3
"""
Verifone UPC Formatter for SSCS Integration
Handles specific Verifone barcode format requirements
"""

import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class VerifoneFormatter:
    """Format UPC codes for Verifone register compatibility"""
    
    @staticmethod
    def validate_upc_checksum(upc: str) -> bool:
        """Validate UPC-A check digit"""
        if len(upc) != 12 or not upc.isdigit():
            return False
        
        # Calculate check digit
        odd_sum = sum(int(upc[i]) for i in range(0, 11, 2))
        even_sum = sum(int(upc[i]) for i in range(1, 11, 2))
        
        total = (odd_sum * 3) + even_sum
        check_digit = (10 - (total % 10)) % 10
        
        return int(upc[11]) == check_digit
    
    @staticmethod
    def format_for_verifone(upc: str) -> Optional[str]:
        """
        Format UPC for Verifone registers
        
        Based on user note: "Verifone registers are specific in the barcode format. 
        So if you send me a 12 digit barcode like for the Buffalo Trace one (080244000923) 
        the last digit (3) likely needs to be dropped for it to work"
        
        Args:
            upc: 12 or 13 digit UPC code
            
        Returns:
            11-digit UPC for Verifone (12-digit with last digit dropped)
        """
        if not upc:
            return None
        
        # Clean UPC
        clean_upc = re.sub(r'[^\d]', '', upc)
        
        if len(clean_upc) == 13:
            # EAN-13 to UPC-12 conversion (remove leading 0)
            if clean_upc.startswith('0'):
                clean_upc = clean_upc[1:]
            else:
                logger.warning(f"EAN-13 {upc} doesn't start with 0, may not convert properly")
        
        if len(clean_upc) == 12:
            # Validate the 12-digit UPC first
            if VerifoneFormatter.validate_upc_checksum(clean_upc):
                # Drop the last digit (check digit) for Verifone
                verifone_upc = clean_upc[:-1]  # Remove last digit
                logger.info(f"Formatted UPC for Verifone: {clean_upc} → {verifone_upc}")
                return verifone_upc
            else:
                logger.warning(f"Invalid UPC checksum: {clean_upc}")
                # Still return the 11-digit version, but log the warning
                return clean_upc[:-1]
        
        elif len(clean_upc) == 11:
            # Already in Verifone format
            logger.info(f"UPC already in Verifone format: {clean_upc}")
            return clean_upc
        
        else:
            logger.error(f"Invalid UPC length: {len(clean_upc)} digits: {clean_upc}")
            return None
    
    @staticmethod
    def format_with_validation(upc: str) -> Tuple[Optional[str], bool, str]:
        """
        Format UPC with validation details
        
        Returns:
            Tuple of (formatted_upc, is_valid, validation_message)
        """
        if not upc:
            return None, False, "Empty UPC"
        
        clean_upc = re.sub(r'[^\d]', '', upc)
        
        if len(clean_upc) not in [11, 12, 13]:
            return None, False, f"Invalid UPC length: {len(clean_upc)} digits"
        
        # Handle different input formats
        if len(clean_upc) == 13:
            if clean_upc.startswith('0'):
                clean_upc = clean_upc[1:]  # Convert EAN-13 to UPC-12
            else:
                return None, False, "EAN-13 doesn't start with 0"
        
        if len(clean_upc) == 12:
            # Validate checksum
            is_valid = VerifoneFormatter.validate_upc_checksum(clean_upc)
            verifone_upc = clean_upc[:-1]  # Drop check digit
            
            validation_msg = "Valid UPC with correct checksum" if is_valid else "Invalid checksum but formatted anyway"
            
            return verifone_upc, is_valid, validation_msg
        
        elif len(clean_upc) == 11:
            # Already in Verifone format, can't validate checksum
            return clean_upc, True, "Already in Verifone 11-digit format"
        
        return None, False, "Unexpected format error"
    
    @staticmethod
    def batch_format(upcs: list) -> dict:
        """
        Format multiple UPCs for Verifone
        
        Returns:
            Dictionary with results for each UPC
        """
        results = {}
        
        for original_upc in upcs:
            formatted, is_valid, message = VerifoneFormatter.format_with_validation(original_upc)
            
            results[original_upc] = {
                'verifone_format': formatted,
                'is_valid': is_valid,
                'validation_message': message,
                'original_length': len(re.sub(r'[^\d]', '', original_upc)) if original_upc else 0
            }
        
        return results

# Test function
def test_verifone_formatting():
    """Test Verifone UPC formatting with examples"""
    
    test_upcs = [
        "080244000923",  # Buffalo Trace example from user
        "0802440009230", # Same with extra 0
        "123456789012",  # Generic 12-digit
        "0123456789012", # EAN-13 format
        "12345678901",   # Already 11-digit
        "invalid",       # Invalid format
        "",              # Empty
        None             # None value
    ]
    
    print("\n🎯 Verifone UPC Formatting Test:")
    print("=" * 60)
    
    for upc in test_upcs:
        formatted, is_valid, message = VerifoneFormatter.format_with_validation(upc)
        
        status = "✅" if is_valid else "⚠️" if formatted else "❌"
        
        print(f"\n{status} Original: {upc}")
        print(f"   Verifone: {formatted}")
        print(f"   Valid: {is_valid}")
        print(f"   Message: {message}")
    
    # Batch test
    print(f"\n📊 Batch Formatting Test:")
    batch_results = VerifoneFormatter.batch_format(test_upcs[:5])
    
    for original, result in batch_results.items():
        print(f"{original} → {result['verifone_format']} ({'✅' if result['is_valid'] else '⚠️'})")

if __name__ == "__main__":
    test_verifone_formatting()
