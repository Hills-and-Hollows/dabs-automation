"""
DABS EDI Invoice Generator
Creates NAXML format EDI invoices for SSCS CDB system integration

Business Context:
- Processes 1,239 DABS SKUs monthly
- Sends to v6242s1@edidelivery.com for automatic SSCS import
- Delivers 90% time reduction (10+ hours → <1 hour)
- Maintains Utah Package Agency compliance
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DABSItem:
    """DABS item data structure"""
    csc_code: str
    description: str
    retail_price: float
    cost: float
    category: str
    size: str
    upc: Optional[str] = None
    vendor_item_code: Optional[str] = None
    status: str = "Active"

class DABSEDIGenerator:
    """Generate NAXML EDI invoices for DABS items"""
    
    def __init__(self):
        self.vendor_id = "DABS"
        self.vendor_name = "Utah Division of Alcoholic Beverage Control"
        self.store_location_id = "HILLS_HOLLOWS_BOULDER"
        
    def generate_naxml(self, items: List[DABSItem], invoice_number: Optional[str] = None) -> str:
        """
        Generate NAXML format EDI invoice
        
        Args:
            items: List of DABS items to include
            invoice_number: Optional custom invoice number
            
        Returns:
            NAXML formatted XML string
        """
        timestamp = datetime.now().isoformat() + "Z"
        invoice_date = datetime.now().strftime("%Y-%m-%d")
        
        if not invoice_number:
            invoice_number = f"DABS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Generating NAXML for {len(items)} items, Invoice: {invoice_number}")
        
        # Create root element
        root = ET.Element("ItemSynch")
        root.set("version", "2.0")
        root.set("timestamp", timestamp)
        root.set("vendor", self.vendor_id)
        
        # Vendor Info Section
        vendor_info = ET.SubElement(root, "VendorInfo")
        ET.SubElement(vendor_info, "VendorID").text = self.vendor_id
        ET.SubElement(vendor_info, "VendorName").text = self.vendor_name
        ET.SubElement(vendor_info, "InvoiceNumber").text = invoice_number
        ET.SubElement(vendor_info, "InvoiceDate").text = invoice_date
        ET.SubElement(vendor_info, "TotalItems").text = str(len(items))
        ET.SubElement(vendor_info, "StoreLocationID").text = self.store_location_id
        ET.SubElement(vendor_info, "TransmissionDate").text = invoice_date
        
        # Items Section
        items_element = ET.SubElement(root, "Items")
        total_cost = 0.0
        total_retail = 0.0
        
        for item in items:
            item_element = ET.SubElement(items_element, "Item")
            
            # Required fields
            ET.SubElement(item_element, "PLU").text = str(item.csc_code)
            ET.SubElement(item_element, "ItemName").text = item.description[:50]  # Limit to 50 chars
            ET.SubElement(item_element, "Price").text = f"{item.retail_price:.2f}"
            ET.SubElement(item_element, "Cost").text = f"{item.cost:.2f}"
            ET.SubElement(item_element, "Category").text = item.category
            ET.SubElement(item_element, "Size").text = item.size
            ET.SubElement(item_element, "VendorItemCode").text = item.vendor_item_code or str(item.csc_code)
            ET.SubElement(item_element, "LastUpdated").text = timestamp
            ET.SubElement(item_element, "Status").text = item.status
            
            # UPC field - CRITICAL for SSCS barcode scanning
            # Always include UPC field for SSCS compatibility
            upc_value = item.upc if item.upc else ""
            ET.SubElement(item_element, "UPC").text = str(upc_value)
            
            total_cost += item.cost
            total_retail += item.retail_price
        
        # Invoice Totals Section
        totals = ET.SubElement(root, "InvoiceTotals")
        ET.SubElement(totals, "SubTotal").text = f"{total_cost:.2f}"
        ET.SubElement(totals, "Tax").text = "0.00"  # DABS items typically tax-exempt at wholesale
        ET.SubElement(totals, "Total").text = f"{total_cost:.2f}"
        ET.SubElement(totals, "ItemCount").text = str(len(items))
        ET.SubElement(totals, "RetailTotal").text = f"{total_retail:.2f}"
        
        # Format XML with proper indentation
        ET.indent(root, space="  ")
        xml_string = ET.tostring(root, encoding='unicode', xml_declaration=True)
        
        logger.info(f"NAXML generated: {len(items)} items, Total Cost: ${total_cost:.2f}")
        return xml_string
    
    def validate_naxml(self, xml_content: str) -> Dict[str, Any]:
        """
        Validate NAXML content for SSCS compatibility
        
        Args:
            xml_content: NAXML XML string to validate
            
        Returns:
            Validation results dictionary
        """
        try:
            root = ET.fromstring(xml_content)
            
            validation_results = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'item_count': 0,
                'total_cost': 0.0
            }
            
            # Check root element
            if root.tag != "ItemSynch":
                validation_results['errors'].append("Root element must be 'ItemSynch'")
                validation_results['valid'] = False
            
            # Check required attributes
            if not root.get('version'):
                validation_results['errors'].append("Missing 'version' attribute")
                validation_results['valid'] = False
            
            if not root.get('vendor'):
                validation_results['errors'].append("Missing 'vendor' attribute")
                validation_results['valid'] = False
            
            # Check VendorInfo section
            vendor_info = root.find('VendorInfo')
            if vendor_info is None:
                validation_results['errors'].append("Missing VendorInfo section")
                validation_results['valid'] = False
            else:
                required_vendor_fields = ['VendorID', 'VendorName', 'InvoiceNumber', 'InvoiceDate']
                for field in required_vendor_fields:
                    if vendor_info.find(field) is None:
                        validation_results['errors'].append(f"Missing required field: {field}")
                        validation_results['valid'] = False
            
            # Check Items section
            items = root.find('Items')
            if items is None:
                validation_results['errors'].append("Missing Items section")
                validation_results['valid'] = False
            else:
                item_elements = items.findall('Item')
                validation_results['item_count'] = len(item_elements)
                
                for i, item in enumerate(item_elements):
                    required_item_fields = ['PLU', 'ItemName', 'Price', 'Cost', 'Category']
                    for field in required_item_fields:
                        if item.find(field) is None:
                            validation_results['errors'].append(f"Item {i+1}: Missing required field: {field}")
                            validation_results['valid'] = False
                    
                    # Validate price format
                    try:
                        price_elem = item.find('Price')
                        cost_elem = item.find('Cost')
                        if price_elem is not None and cost_elem is not None:
                            price = float(price_elem.text)
                            cost = float(cost_elem.text)
                            validation_results['total_cost'] += cost
                            
                            if price < cost:
                                validation_results['warnings'].append(f"Item {i+1}: Retail price (${price:.2f}) less than cost (${cost:.2f})")
                    except ValueError:
                        validation_results['errors'].append(f"Item {i+1}: Invalid price or cost format")
                        validation_results['valid'] = False
            
            # Check InvoiceTotals section
            totals = root.find('InvoiceTotals')
            if totals is None:
                validation_results['warnings'].append("Missing InvoiceTotals section (recommended)")
            
            logger.info(f"NAXML validation complete: Valid={validation_results['valid']}, Items={validation_results['item_count']}")
            return validation_results
            
        except ET.ParseError as e:
            return {
                'valid': False,
                'errors': [f"XML Parse Error: {str(e)}"],
                'warnings': [],
                'item_count': 0,
                'total_cost': 0.0
            }
    
    def save_naxml_file(self, xml_content: str, output_dir: str = "data/edi_output") -> str:
        """
        Save NAXML content to file with proper naming convention
        
        Args:
            xml_content: NAXML XML string
            output_dir: Output directory path
            
        Returns:
            Full path to saved file
        """
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"DABS_{timestamp}_ItemPrice.xml"
        filepath = Path(output_dir) / filename
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        logger.info(f"NAXML saved to: {filepath}")
        return str(filepath)
    
    def process_dabs_excel_data(self, excel_data: List[Dict[str, Any]]) -> List[DABSItem]:
        """
        Convert DABS Excel data to DABSItem objects
        
        Args:
            excel_data: List of dictionaries from DABS Excel processing
            
        Returns:
            List of DABSItem objects
        """
        items = []
        
        for row in excel_data:
            try:
                # Map Excel columns to DABSItem fields
                item = DABSItem(
                    csc_code=str(row.get('CSC Code', row.get('csc_code', ''))),
                    description=str(row.get('Description', row.get('description', ''))),
                    retail_price=float(row.get('Retail Price', row.get('retail_price', 0.0))),
                    cost=float(row.get('Cost', row.get('cost', 0.0))),
                    category=str(row.get('Category', row.get('category', 'SPIRITS'))),
                    size=str(row.get('Size', row.get('size', ''))),
                    upc=row.get('UPC', row.get('upc')),
                    vendor_item_code=str(row.get('CSC Code', row.get('csc_code', '')))
                )
                items.append(item)
                
            except (ValueError, KeyError) as e:
                logger.error(f"Error processing row {len(items)+1}: {e}")
                continue
        
        logger.info(f"Processed {len(items)} DABS items from Excel data")
        return items

def create_test_dabs_data() -> List[DABSItem]:
    """Create test DABS data for validation"""
    return [
        DABSItem(
            csc_code="12345",
            description="Tito's Handmade Vodka 750ml",
            retail_price=24.99,
            cost=18.75,
            category="SPIRITS",
            size="750ml",
            upc="123456789012"
        ),
        DABSItem(
            csc_code="67890",
            description="Bacardi Mojito 1.75L",
            retail_price=19.99,
            cost=15.25,
            category="SPIRITS",
            size="1.75L",
            upc="678901234567"
        ),
        DABSItem(
            csc_code="11111",
            description="Kendall Jackson Chardonnay 750ml",
            retail_price=16.99,
            cost=12.50,
            category="WINE",
            size="750ml",
            upc="111111111111"
        )
    ]

# Example usage and testing
if __name__ == "__main__":
    # Initialize generator
    generator = DABSEDIGenerator()
    
    # Create test data
    test_items = create_test_dabs_data()
    
    # Generate NAXML
    naxml_content = generator.generate_naxml(test_items, "DABS_TEST_001")
    
    # Validate NAXML
    validation = generator.validate_naxml(naxml_content)
    print(f"Validation Results: {json.dumps(validation, indent=2)}")
    
    # Save to file
    if validation['valid']:
        filepath = generator.save_naxml_file(naxml_content)
        print(f"Test NAXML saved to: {filepath}")
    else:
        print("NAXML validation failed - not saving file")
        for error in validation['errors']:
            print(f"ERROR: {error}")
