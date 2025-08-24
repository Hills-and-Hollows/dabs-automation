async def process_dabs_monthly_update():
    """Complete DABS to SSCS integration workflow"""
    
    # 1. Load DABS Excel file
    dabs_products = await load_dabs_excel_file()
    
    # 2. Generate NAXML ItemSynch
    naxml_content = generate_dabs_naxml(dabs_products)
    
    # 3. Save NAXML file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"DABS_{timestamp}_ItemPrice.xml"
    naxml_path = save_naxml_file(naxml_content, filename)
    
    # 4. Send via EDI email
    invoice_data = {
        'invoice_number': f"DABS_{timestamp}",
        'date': datetime.now(),
        'items': dabs_products
    }
    
    await send_dabs_naxml_to_sscs(naxml_path, invoice_data)
    
    # 5. Log and monitor
    logger.info(f"DABS NAXML sent: {filename} ({len(dabs_products)} items)")
    
    return {
        'success': True,
        'filename': filename,
        'items_processed': len(dabs_products),
        'edi_email': 'v6242s1@edidelivery.com'
    }