#!/usr/bin/env python3
"""
DABS UPC Integration Tool
Complete integration of UPC verification with NAXML generation for EDI delivery
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

from .enhanced_upc_verifier import EnhancedUPCVerifier, EnhancedUPCResult
from .verifone_formatter import VerifoneFormatter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DABSItem:
    """DABS order item with UPC verification"""
    item_name: str
    dabs_code: str
    price: float
    quantity: int = 1
    upc_result: Optional[EnhancedUPCResult] = None
    category: str = "LIQUOR"
    size: str = "750ml"
    
    @property
    def has_upc(self) -> bool:
        return self.upc_result and self.upc_result.upc_code is not None
    
    @property
    def verifone_upc(self) -> Optional[str]:
        return self.upc_result.verifone_upc if self.upc_result else None
    
    @property
    def total_price(self) -> float:
        return self.price * self.quantity

class DABSUPCIntegrator:
    """Complete DABS UPC verification and NAXML generation system"""
    
    def __init__(self, output_dir: str = "src/edi/data/edi_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.verifier = None
        
        # NAXML template configuration
        self.naxml_config = {
            'vendor_id': 'HILLS_HOLLOWS_LLC',
            'location_id': 'BOULDER_UT',
            'document_type': 'ItemPrice',
            'version': '1.0'
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.verifier = EnhancedUPCVerifier()
        await self.verifier.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.verifier:
            await self.verifier.__aexit__(exc_type, exc_val, exc_tb)
    
    def parse_dabs_order_text(self, order_text: str) -> List[DABSItem]:
        """Parse DABS order text into structured items"""
        items = []
        
        # Split by lines and process each item
        lines = order_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or 'Summary Line' in line:
                continue
            
            # Parse format: "ITEM NAME (DABS_CODE) - $PRICE"
            if ' - $' in line and '(' in line and ')' in line:
                try:
                    # Extract item name and code
                    name_code_part, price_part = line.rsplit(' - $', 1)
                    
                    # Extract DABS code from parentheses
                    if '(' in name_code_part and ')' in name_code_part:
                        item_name = name_code_part[:name_code_part.rfind('(')].strip()
                        dabs_code = name_code_part[name_code_part.rfind('(')+1:name_code_part.rfind(')')].strip()
                        
                        # Extract price
                        price = float(price_part.replace(',', ''))
                        
                        # Determine category and size from item name
                        category = self.determine_category(item_name)
                        size = self.extract_size(item_name)
                        
                        item = DABSItem(
                            item_name=item_name,
                            dabs_code=dabs_code,
                            price=price,
                            category=category,
                            size=size
                        )
                        
                        items.append(item)
                        logger.info(f"Parsed DABS item: {item_name} ({dabs_code}) - ${price}")
                
                except Exception as e:
                    logger.error(f"Error parsing line '{line}': {e}")
        
        return items
    
    def determine_category(self, item_name: str) -> str:
        """Determine product category from item name"""
        name_lower = item_name.lower()
        
        if any(wine_term in name_lower for wine_term in ['pinot', 'chardonnay', 'cabernet', 'merlot', 'rosé', 'rose', 'brut', 'wine']):
            return "WINE"
        elif any(beer_term in name_lower for beer_term in ['beer', 'ale', 'lager', 'ipa', 'stout']):
            return "BEER"
        elif any(spirit_term in name_lower for spirit_term in ['tequila', 'vodka', 'whiskey', 'bourbon', 'rum', 'gin', 'brandy']):
            return "SPIRITS"
        else:
            return "LIQUOR"  # Default category
    
    def extract_size(self, item_name: str) -> str:
        """Extract size from item name"""
        import re
        
        # Look for size patterns
        size_patterns = [
            r'(\d+(?:\.\d+)?\s*ml)',
            r'(\d+(?:\.\d+)?\s*l)',
            r'(\d+(?:\.\d+)?\s*oz)',
            r'(750ml)',  # Common default
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, item_name, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "750ml"  # Default size
    
    async def verify_upcs_for_items(self, items: List[DABSItem]) -> List[DABSItem]:
        """Verify UPCs for all DABS items"""
        logger.info(f"Starting UPC verification for {len(items)} DABS items")
        
        # Prepare items for batch lookup
        lookup_items = [(item.item_name, item.dabs_code) for item in items]
        
        # Perform batch UPC lookup
        upc_results = await self.verifier.lookup_batch_upcs_enhanced(lookup_items)
        
        # Map results back to items
        result_map = {result.dabs_code: result for result in upc_results}
        
        for item in items:
            if item.dabs_code in result_map:
                item.upc_result = result_map[item.dabs_code]
        
        # Log summary
        found_count = sum(1 for item in items if item.has_upc)
        logger.info(f"UPC verification complete: {found_count}/{len(items)} items have UPCs")
        
        return items
    
    def generate_naxml(self, items: List[DABSItem], order_id: str = None) -> str:
        """Generate NAXML with UPC codes for EDI delivery"""
        
        # Create root element
        root = ET.Element("NAXMLDocument")
        root.set("version", self.naxml_config['version'])
        
        # Document header
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "VendorID").text = self.naxml_config['vendor_id']
        ET.SubElement(header, "LocationID").text = self.naxml_config['location_id']
        ET.SubElement(header, "DocumentType").text = self.naxml_config['document_type']
        ET.SubElement(header, "Timestamp").text = datetime.now().isoformat()
        
        if order_id:
            ET.SubElement(header, "OrderID").text = order_id
        
        # Items section
        items_element = ET.SubElement(root, "Items")
        ET.SubElement(items_element, "ItemCount").text = str(len(items))
        
        for item in items:
            item_element = ET.SubElement(items_element, "Item")
            
            # Basic item information
            ET.SubElement(item_element, "PLU").text = item.dabs_code
            ET.SubElement(item_element, "ItemName").text = item.item_name
            ET.SubElement(item_element, "Price").text = f"{item.price:.2f}"
            ET.SubElement(item_element, "Quantity").text = str(item.quantity)
            ET.SubElement(item_element, "Category").text = item.category
            ET.SubElement(item_element, "Size").text = item.size
            
            # UPC information (key addition)
            if item.has_upc:
                upc_element = ET.SubElement(item_element, "UPC")
                upc_element.text = item.upc_result.upc_code
                upc_element.set("format", "UPC-A")
                
                # Verifone-specific UPC for SSCS integration
                verifone_element = ET.SubElement(item_element, "VerifoneUPC")
                verifone_element.text = item.verifone_upc
                verifone_element.set("format", "11-digit")
                
                # UPC verification metadata
                verification = ET.SubElement(item_element, "UPCVerification")
                ET.SubElement(verification, "Confidence").text = f"{item.upc_result.confidence:.2f}"
                ET.SubElement(verification, "Sources").text = ",".join(item.upc_result.sources)
                ET.SubElement(verification, "Verified").text = str(item.upc_result.verified).lower()
            else:
                # Mark items without UPC for manual review
                upc_element = ET.SubElement(item_element, "UPC")
                upc_element.text = "MANUAL_REVIEW_REQUIRED"
                upc_element.set("status", "not_found")
                
                # Add error information
                if item.upc_result and item.upc_result.error:
                    ET.SubElement(item_element, "UPCError").text = item.upc_result.error
        
        # Summary section
        summary = ET.SubElement(root, "Summary")
        total_items = len(items)
        items_with_upc = sum(1 for item in items if item.has_upc)
        items_verified = sum(1 for item in items if item.has_upc and item.upc_result.verified)
        total_value = sum(item.total_price for item in items)
        
        ET.SubElement(summary, "TotalItems").text = str(total_items)
        ET.SubElement(summary, "ItemsWithUPC").text = str(items_with_upc)
        ET.SubElement(summary, "ItemsVerified").text = str(items_verified)
        ET.SubElement(summary, "TotalValue").text = f"{total_value:.2f}"
        ET.SubElement(summary, "UPCCoverageRate").text = f"{(items_with_upc/total_items*100):.1f}%"
        ET.SubElement(summary, "VerificationRate").text = f"{(items_verified/total_items*100):.1f}%"
        
        # Convert to pretty XML string
        rough_string = ET.tostring(root, 'unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        # Remove empty lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def save_naxml(self, xml_content: str, filename: str = None) -> Path:
        """Save NAXML to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"DABS_{timestamp}_ItemPrice_WithUPC.xml"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        logger.info(f"NAXML saved to: {output_path}")
        return output_path
    
    def generate_upc_report(self, items: List[DABSItem]) -> str:
        """Generate UPC verification report"""
        report_lines = []
        report_lines.append("🎯 DABS UPC Verification Report")
        report_lines.append("=" * 60)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Summary statistics
        total_items = len(items)
        items_with_upc = sum(1 for item in items if item.has_upc)
        items_verified = sum(1 for item in items if item.has_upc and item.upc_result.verified)
        total_value = sum(item.total_price for item in items)
        
        report_lines.append("📊 Summary Statistics:")
        report_lines.append(f"Total Items: {total_items}")
        report_lines.append(f"Items with UPC: {items_with_upc}")
        report_lines.append(f"Items Verified: {items_verified}")
        report_lines.append(f"Total Order Value: ${total_value:,.2f}")
        report_lines.append(f"UPC Coverage: {(items_with_upc/total_items*100):.1f}%")
        report_lines.append(f"Verification Rate: {(items_verified/total_items*100):.1f}%")
        report_lines.append("")
        
        # Detailed item results
        report_lines.append("📋 Detailed Results:")
        report_lines.append("")
        
        for item in items:
            status = "✅ VERIFIED" if item.has_upc and item.upc_result.verified else "⚠️  FOUND" if item.has_upc else "❌ NOT FOUND"
            
            report_lines.append(f"{status} {item.item_name}")
            report_lines.append(f"   DABS Code: {item.dabs_code}")
            report_lines.append(f"   Price: ${item.price:.2f}")
            
            if item.has_upc:
                report_lines.append(f"   UPC-12: {item.upc_result.upc_code}")
                report_lines.append(f"   Verifone UPC-11: {item.verifone_upc}")
                report_lines.append(f"   Confidence: {item.upc_result.confidence:.2f}")
                report_lines.append(f"   Sources: {', '.join(item.upc_result.sources)}")
            else:
                report_lines.append(f"   UPC: Not found")
                if item.upc_result and item.upc_result.error:
                    report_lines.append(f"   Error: {item.upc_result.error}")
            
            report_lines.append("")
        
        # Items requiring manual review
        manual_review_items = [item for item in items if not item.has_upc]
        if manual_review_items:
            report_lines.append("⚠️  Items Requiring Manual UPC Review:")
            for item in manual_review_items:
                report_lines.append(f"   • {item.item_name} ({item.dabs_code})")
            report_lines.append("")
        
        # Next steps
        report_lines.append("🎯 Next Steps:")
        if items_with_upc == total_items:
            report_lines.append("   ✅ All items have UPCs - Ready for EDI delivery")
        else:
            report_lines.append(f"   ⚠️  {total_items - items_with_upc} items need manual UPC lookup")
            report_lines.append("   📋 Review items marked for manual review")
            report_lines.append("   🔍 Use DABS Product Locator for missing UPCs")
        
        return "\n".join(report_lines)
    
    async def process_dabs_order(self, order_text: str, order_id: str = None) -> Tuple[str, str, Path]:
        """Complete DABS order processing with UPC verification"""
        logger.info("Starting complete DABS order processing")
        
        # Parse order text
        items = self.parse_dabs_order_text(order_text)
        logger.info(f"Parsed {len(items)} items from DABS order")
        
        # Verify UPCs
        items = await self.verify_upcs_for_items(items)
        
        # Generate NAXML with UPCs
        naxml_content = self.generate_naxml(items, order_id)
        
        # Save NAXML
        naxml_path = self.save_naxml(naxml_content)
        
        # Generate report
        report = self.generate_upc_report(items)
        
        logger.info("Complete DABS order processing finished")
        return naxml_content, report, naxml_path

# Test function
async def test_dabs_integration():
    """Test complete DABS UPC integration"""
    
    # Sample DABS order from user
    sample_order = """🍷 Order Contents (10 Items)
ARETTE CLASICA BLANCO TEQUILA (039593) - $395.88
WILLAMETTE VLY PINOT NOIR WL (087123) - $299.88
KING ESTATE PINOT GRIS SIGNATURE (523110) - $252.96
SEGURA VIUDAS BRUT 750ml (580790) - $167.88
POE ROSÉ'23 750ml (908418) - $251.88"""
    
    async with DABSUPCIntegrator() as integrator:
        naxml_content, report, naxml_path = await integrator.process_dabs_order(
            sample_order, 
            order_id="TEST_ORDER_001"
        )
        
        print("\n" + report)
        print(f"\n📄 NAXML saved to: {naxml_path}")
        print(f"\n📋 NAXML Preview (first 1000 chars):")
        print(naxml_content[:1000] + "..." if len(naxml_content) > 1000 else naxml_content)

if __name__ == "__main__":
    asyncio.run(test_dabs_integration())
