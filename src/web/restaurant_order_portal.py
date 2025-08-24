async def submit_restaurant_order(self, order_data: Dict):
    """Capture restaurant order and initiate complete flow"""
    
    # Create restaurant order object
    restaurant_order = RestaurantOrder(
        restaurant_name=order_data['restaurant_name'],
        contact_info=order_data['contact'],
        items=order_data['items'],
        delivery_date=order_data['requested_delivery'],
        payment_method=order_data['payment']
    )
    
    # Validate against live SSCS inventory
    inventory_check = await self.sscs_client.check_item_availability(restaurant_order.items)
    
    if inventory_check['all_available']:
        # Initiate complete automated flow
        flow_result = await self.order_controller.process_complete_order_flow(restaurant_order)
        
        if flow_result['success']:
            return {
                'status': 'order_submitted',
                'order_id': restaurant_order.order_id,
                'dabs_order_id': flow_result['dabs_order_id'],
                'estimated_delivery': restaurant_order.delivery_date,
                'confirmation_email_sent': True
            }
    
    return {'status': 'validation_failed', 'errors': inventory_check['unavailable_items']}