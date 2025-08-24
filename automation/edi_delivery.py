def send_dabs_naxml_to_sscs(naxml_file_path, invoice_data):
    """Send DABS NAXML file via confirmed SSCS EDI channel"""
    
    # Confirmed EDI email from research
    edi_email = "v6242s1@edidelivery.com"
    
    # Subject format (based on SSCS vendor patterns)
    subject = f"DABS_ItemPrice_{invoice_data['date'].strftime('%Y%m%d')}.xml"
    
    # Minimal body (file attachment is primary)
    body = f"""DABS Vendor Price Update
Invoice: {invoice_data['invoice_number']}
Date: {invoice_data['date']}
Items: {len(invoice_data['items'])}
Format: NAXML ItemSynch v2.0"""
    
    # Attachment with specific naming
    filename = f"DABS_{invoice_data['date'].strftime('%Y%m%d_%H%M%S')}_ItemPrice.xml"
    
    send_email_with_attachment(edi_email, subject, body, naxml_file_path, filename)
    
    logger.info(f"DABS NAXML sent to SSCS EDI: {filename}")
