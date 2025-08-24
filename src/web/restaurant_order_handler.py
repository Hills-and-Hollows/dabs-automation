async def process_restaurant_order_submission(self, order_data: Dict) -> Dict[str, Any]:
    """Process restaurant order and automatically place in DABS"""
    
    # Convert restaurant order to DABS format
    dabs_order = RestaurantDABSOrder(
        restaurant_name=order_data['restaurant_name'],
        delivery_date=order_data['requested_delivery'],
        items=[
            DABSOrderItem(
                product_code=item['dabs_code'],
                product_name=item['product_name'],
                quantity=item['quantity'],
                unit_price=item['unit_price']
            )
            for item in order_data['items']
        ],
        reference_number=f"REST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    # Automatically place order in DABS
    dabs_automation = DABSAutomatedOrdering()
    placement_result = await dabs_automation.place_restaurant_order_automatically(dabs_order)
    
    if placement_result['success']:
        # Send confirmation to restaurant
        await self.send_order_confirmation(order_data['restaurant_email'], placement_result)
        
        # Notify Tessa
        await self.notify_tessa_new_order(order_data, placement_result)
        
        # Generate SSCS EDI for inventory staging
        await self.generate_sscs_edi_staging(placement_result)
    
    return placement_result