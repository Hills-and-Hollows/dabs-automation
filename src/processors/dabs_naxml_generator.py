def generate_dabs_naxml(dabs_products: List[DABSProduct]) -> str:
    """Generate NAXML ItemSynch for DABS products"""
    
    # Create root element with SSCS-expected attributes
    root = ET.Element("ItemSynch")
    root.set("version", "2.0")
    root.set("timestamp", datetime.now().isoformat())
    root.set("vendor", "DABS")
    
    # Vendor info header
    vendor_info = ET.SubElement(root, "VendorInfo")
    ET.SubElement(vendor_info, "VendorID").text = "DABS"
    ET.SubElement(vendor_info, "VendorName").text = "Utah Division of Alcoholic Beverage Control"
    ET.SubElement(vendor_info, "TotalItems").text = str(len(dabs_products))
    
    # Items section
    items = ET.SubElement(root, "Items")
    
    for product in dabs_products:
        item = ET.SubElement(items, "Item")
        
        # Map DABS fields to NAXML
        ET.SubElement(item, "PLU").text = product.csc_code  # DABS CSC Code
        ET.SubElement(item, "ItemName").text = product.product_name
        ET.SubElement(item, "Price").text = f"{product.retail_price:.2f}"
        ET.SubElement(item, "Category").text = product.category
        ET.SubElement(item, "Size").text = product.size_ml
        ET.SubElement(item, "VendorItemCode").text = product.csc_code
        ET.SubElement(item, "Status").text = product.status
        ET.SubElement(item, "LastUpdated").text = datetime.now().isoformat()
        
        # Add UPC if available from mapping
        if hasattr(product, 'upc_code') and product.upc_code:
            ET.SubElement(item, "UPC").text = product.upc_code
    
    return ET.tostring(root, encoding='unicode', xml_declaration=True)