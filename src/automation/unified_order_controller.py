class UnifiedOrderController:
    """
    Complete order flow orchestration from Hills & Hollows website to SSCS
    
    Flow: Website → DABS → SSCS (Full Automation)
    """
    
    def __init__(self):
        self.restaurant_portal = RestaurantOrderPortal()
        self.dabs_api = DABSOrderAPI()
        self.sscs_edi = SSCSEDIClient()
        self.notification_system = TessaNotificationSystem()
    
    async def process_complete_order_flow(self, restaurant_order: RestaurantOrder):
        """Execute complete order flow with full control"""
        
        order_id = restaurant_order.order_id
        logger.info(f"Starting unified order flow: {order_id}")
        
        try:
            # STEP 1: Validate restaurant order against live inventory
            validation = await self._validate_order_against_sscs_inventory(restaurant_order)
            if not validation['valid']:
                return await self._handle_validation_failure(restaurant_order, validation)
            
            # STEP 2: Submit order to DABS system
            dabs_result = await self._submit_order_to_dabs(restaurant_order)
            if not dabs_result['success']:
                return await self._handle_dabs_failure(restaurant_order, dabs_result)
            
            # STEP 3: Confirm DABS order and get final details
            confirmed_order = await self._confirm_dabs_order(dabs_result['dabs_order_id'])
            
            # STEP 4: Generate NAXML for SSCS EDI import
            naxml_result = await self._generate_sscs_naxml(confirmed_order)
            
            # STEP 5: Send to SSCS via EDI
            edi_result = await self._send_to_sscs_edi(naxml_result)
            
            # STEP 6: Notify all parties of completion
            await self._notify_order_completion(restaurant_order, confirmed_order, edi_result)
            
            return {
                'success': True,
                'order_id': order_id,
                'dabs_order_id': dabs_result['dabs_order_id'],
                'sscs_edi_file': edi_result['filename'],
                'flow_duration': self._calculate_duration()
            }
            
        except Exception as e:
            logger.error(f"Unified order flow failed: {e}")
            await self._handle_flow_failure(restaurant_order, str(e))
            return {'success': False, 'error': str(e)}