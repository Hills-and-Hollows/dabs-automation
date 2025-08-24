async def send_confirmed_order_to_sscs(self, confirmed_dabs_order):
    """Send confirmed DABS order to SSCS via EDI for inventory staging"""
    
    # Generate NAXML for confirmed order
    naxml_content = self._generate_order_naxml(confirmed_dabs_order)
    
    # Create EDI file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"DABS_ORDER_{confirmed_dabs_order['dabs_order_id']}_{timestamp}.xml"
    
    # Send via EDI email
    edi_result = await self._send_edi_email(
        to="v6242s1@edidelivery.com",
        subject=filename,
        attachment_content=naxml_content,
        attachment_name=filename
    )
    
    return {
        'success': True,
        'filename': filename,
        'edi_delivery_time': datetime.now().isoformat(),
        'sscs_import_expected': True
    }