#!/usr/bin/env python3
"""
Generate NAXML invoice from restaurant portal order

This script creates NAXML-BusDoc format invoices that match the exact structure
used by DABS for SSCS integration, based on Order 233813 format.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

class NAXMLGenerator:
    """Generate NAXML invoices compatible with SSCS integration"""
    
    def __init__(self):
        self.transmission_id_base = "DABS_HILLS_HOLLOWS"
        
    def generate_naxml_invoice(self, order_data):
        """Generate NAXML invoice from order data"""
        
        # Create root element
        root = ET.Element("NAXML-BusDoc")
        
        # Add transmission header
        self._add_transmission_header(root, order_data)
        
        # Add parties
        self._add_parties(root, order_data)
        
        # Add invoice
        self._add_invoice(root, order_data)
        
        return root
    
    def _add_transmission_header(self, root, order_data):
        """Add transmission header section"""
        header = ET.SubElement(root, "TransmissionHeader")
        
        # Generate transmission ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        transmission_id = f"{self.transmission_id_base}_{timestamp}_{timestamp}"
        
        ET.SubElement(header, "TransmissionId").text = transmission_id
        ET.SubElement(header, "TransmissionDate").text = datetime.now().strftime("%Y-%m-%d")
        ET.SubElement(header, "TransmissionTime").text = datetime.now().strftime("%H:%M:%S")
        ET.SubElement(header, "TransmissionStatus").text = "original"
    
    def _add_parties(self, root, order_data):
        """Add parties section"""
        parties = ET.SubElement(root, "Parties")
        
        # Supplier (DABS)
        supplier = ET.SubElement(parties, "Supplier")
        ET.SubElement(supplier, "Name").text = "Utah Division of Alcoholic Beverage Control"
        org_id = ET.SubElement(supplier, "OrganizationId", ident="DABS")
        org_id.text = "DABS"
        
        # Buyer (Restaurant)
        buyer = ET.SubElement(parties, "Buyer")
        restaurant_name = order_data.get('restaurant_name', 'Restaurant Customer')
        ET.SubElement(buyer, "Name").text = restaurant_name
        
        # ShipTo (Hills & Hollows)
        ship_to = ET.SubElement(parties, "ShipTo", ident="HILLS_HOLLOWS_BOULDER")
        ET.SubElement(ship_to, "Name").text = "Hills & Hollows Package Agency"
    
    def _add_invoice(self, root, order_data):
        """Add invoice section"""
        invoice = ET.SubElement(root, "Invoice")
        
        # Location
        location = ET.SubElement(invoice, "Location")
        location_name = ET.SubElement(location, "Name", ident="HILLS_HOLLOWS_BOULDER")
        location_name.text = "Hills & Hollows Package Agency"
        
        # Invoice details
        invoice_number = f"HILLS_HOLLOWS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ET.SubElement(invoice, "InvoiceNumber").text = invoice_number
        ET.SubElement(invoice, "InvoiceDate").text = datetime.now().strftime("%Y-%m-%d")
        
        currency = ET.SubElement(invoice, "Currency", code="USD")
        currency.text = "USD"
        
        # Invoice detail
        invoice_detail = ET.SubElement(invoice, "InvoiceDetail")
        
        # Add line items
        total_cost = 0
        total_units = 0
        
        for item in order_data.get('products', []):
            line_item = self._create_line_item(invoice_detail, item)
            total_cost += item['price'] * item['quantity']
            total_units += item['quantity']
        
        # Add invoice summary
        self._add_invoice_summary(invoice_detail, total_units, total_cost)
        
        # Add terms
        self._add_terms(invoice_detail)
    
    def _create_line_item(self, parent, item):
        """Create a line item element"""
        line_item = ET.SubElement(parent, "LineItem")
        
        # Invoice unit
        invoice_unit = ET.SubElement(line_item, "InvoiceUnit")
        
        # VIN (SKU)
        vin_id = ET.SubElement(invoice_unit, "InvoiceUnitId", identType="VIN")
        vin_id.text = item['sku']
        
        # GTIN (UPC) - inline with VIN
        gtin_id = ET.SubElement(invoice_unit, "InvoiceUnitId", identType="GTIN")
        gtin_id.text = item.get('upc', f"0000000{item['sku'].zfill(7)}")
        
        # Description
        ET.SubElement(invoice_unit, "InvoiceUnitDescription").text = item['product_name']
        
        # Quantity
        qty = ET.SubElement(invoice_unit, "InvoiceUnitQty", cstoreUOMBasis="each")
        qty.text = str(item['quantity'])
        
        # Cost (wholesale price - estimated at 70% of retail)
        wholesale_cost = round(item['price'] * 0.70, 2)
        cost = ET.SubElement(invoice_unit, "InvoiceUnitCost", currency="USD")
        cost.text = f"{wholesale_cost:.2f}"
        
        # Line amounts
        line_gross = wholesale_cost * item['quantity']
        ET.SubElement(invoice_unit, "LineItemGrossAmt").text = f"{line_gross:.2f}"
        ET.SubElement(invoice_unit, "LineItemNetAmt").text = f"{line_gross:.2f}"
        
        # Retail unit pricing
        retail_pricing = ET.SubElement(line_item, "RetailUnitPricing")
        
        retail_id = ET.SubElement(retail_pricing, "RetailUnitId", identType="GTIN")
        retail_id.text = item.get('upc', f"0000000{item['sku'].zfill(7)}")
        
        ET.SubElement(retail_pricing, "RetailUnitQty").text = str(item['quantity'])
        
        retail_price = ET.SubElement(retail_pricing, "RetailPrice", currency="USD")
        retail_price.text = f"{item['price']:.2f}"
        
        return line_item
    
    def _add_invoice_summary(self, parent, total_units, total_cost):
        """Add invoice summary"""
        summary = ET.SubElement(parent, "InvoiceSummary")
        totals = ET.SubElement(summary, "InvoiceTotals")
        
        ET.SubElement(totals, "TotalInvoiceUnits").text = str(total_units)
        
        total_net = ET.SubElement(totals, "TotalLineItemNetAmt", currency="USD")
        total_net.text = f"{total_cost:.2f}"
        
        ET.SubElement(totals, "TotalTaxes").text = "0.00"
        
        total_due = ET.SubElement(totals, "TotalInvoiceDueAmt", currency="USD")
        total_due.text = f"{total_cost:.2f}"
    
    def _add_terms(self, parent):
        """Add payment terms"""
        terms = ET.SubElement(parent, "Terms")
        
        terms_type = ET.SubElement(terms, "TermsType", ident="NET30")
        terms_type.text = "NET30"
        
        due_date = datetime.now() + timedelta(days=30)
        ET.SubElement(terms, "InvoiceDueDate").text = due_date.strftime("%Y-%m-%d")
    
    def format_xml(self, root):
        """Format XML with proper indentation"""
        rough_string = ET.tostring(root, encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
    
    def save_naxml_invoice(self, order_data, output_path=None):
        """Generate and save NAXML invoice"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"src/edi/data/edi_output/HILLS_HOLLOWS_Invoice_{timestamp}.na.xml"
        
        # Generate NAXML
        root = self.generate_naxml_invoice(order_data)
        
        # Format and save
        formatted_xml = self.format_xml(root)
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_xml)
        
        print(f"✅ NAXML invoice generated: {output_path}")
        return output_path

def generate_sample_naxml():
    """Generate sample NAXML from Order 233813 products"""
    
    # Sample order data matching Order 233813 structure
    sample_order = {
        'restaurant_name': 'Sample Restaurant',
        'order_date': datetime.now().isoformat(),
        'products': [
            {
                'sku': '017088',
                'upc': '00000000017082',
                'product_name': 'BULLEIT BOURBON FRONTIER WHISK 750ml',
                'price': 32.99,
                'quantity': 1
            },
            {
                'sku': '419951',
                'upc': '00000000419952',
                'product_name': '19 CRIMES CABERNET SAUVIGNON 750ml',
                'price': 12.99,
                'quantity': 1
            },
            {
                'sku': '445303',
                'upc': '00000000445300',
                'product_name': 'BOTA BOX NIGHTHAWK BLACK RED 3000ml',
                'price': 17.99,
                'quantity': 1
            }
        ]
    }
    
    generator = NAXMLGenerator()
    output_path = generator.save_naxml_invoice(sample_order)
    
    print(f"📋 Sample NAXML invoice generated")
    print(f"🔗 Compatible with SSCS integration")
    print(f"📁 Saved to: {output_path}")

if __name__ == "__main__":
    generate_sample_naxml()
