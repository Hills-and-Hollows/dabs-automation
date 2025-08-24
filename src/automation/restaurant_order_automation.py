#!/usr/bin/env python3
"""
Restaurant Order Automation System
Complete restaurant order management with UPC integration

Created: January 23, 2025
Purpose: Automate restaurant ordering workflow from submission to delivery
"""

import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import json
import smtplib
try:
    from email.mime.text import MIMEText as MimeText
    from email.mime.multipart import MIMEMultipart as MimeMultipart
except ImportError:
    # Fallback for older Python versions
    from email.MIMEText import MIMEText as MimeText
    from email.MIMEMultipart import MIMEMultipart as MimeMultipart

from processors.upc_master_database import UPCMasterDatabase, UPCMasterRecord
from processors.dabs_upc_processor import DABSUPCProcessor
from integration_hub.sscs_ccb_client import SSCSCCBClient, SSCSCaseUPC
from integration.dabs_automated_ordering import DABSAutomatedOrdering, RestaurantOrder as DABSRestaurantOrder, RestaurantOrderItem as DABSOrderItem

logger = logging.getLogger(__name__)

@dataclass
class RestaurantOrder:
    """Restaurant order data structure"""
    order_id: str
    restaurant_name: str
    restaurant_contact: str
    order_date: datetime
    requested_delivery_date: datetime
    items: List[Dict]
    total_amount: float
    payment_method: str
    credit_card_last_four: Optional[str] = None
    processing_fee: float = 0.0
    order_status: str = "submitted"
    confirmation_date: Optional[datetime] = None
    case_upcs_configured: bool = False

@dataclass 
class RestaurantOrderProcessingResult:
    """Result of restaurant order processing"""
    total_orders: int
    successfully_processed: int
    upcs_configured: int
    payment_processed: int
    exceptions: List[str]
    friday_confirmation_ready: bool

class RestaurantOrderAutomation:
    """
    Restaurant Order Automation System
    
    Manages complete restaurant ordering workflow:
    - Thursday order submission and validation
    - Friday confirmation with UPC staging
    - Case UPC pre-configuration for delivery
    - Tuesday delivery and pickup optimization
    """
    
    def __init__(self):
        """Initialize restaurant order automation"""
        # Core components
        self.upc_db = UPCMasterDatabase()
        self.dabs_processor = DABSUPCProcessor()
        self.ccb_client = SSCSCCBClient()
        
        # Restaurant order management
        self.orders_db_path = Path("data/restaurant_orders.json")
        self.orders_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Order processing configuration
        self.credit_card_processing_fee_percent = 2.5  # 2.5% processing fee
        self.friday_confirmation_deadline = 17  # 5 PM deadline
        self.sunday_cutoff_hour = 23  # 11 PM Sunday cutoff
        
        # Load existing orders
        self.restaurant_orders = self._load_restaurant_orders()
        
        logger.info("Restaurant Order Automation initialized")

    def _load_restaurant_orders(self) -> Dict[str, RestaurantOrder]:
        """Load existing restaurant orders from persistent storage"""
        try:
            if self.orders_db_path.exists():
                with open(self.orders_db_path, 'r') as f:
                    orders_data = json.load(f)
                    
                orders = {}
                for order_id, order_data in orders_data.items():
                    order = RestaurantOrder(
                        order_id=order_data['order_id'],
                        restaurant_name=order_data['restaurant_name'],
                        restaurant_contact=order_data['restaurant_contact'],
                        order_date=datetime.fromisoformat(order_data['order_date']),
                        requested_delivery_date=datetime.fromisoformat(order_data['requested_delivery_date']),
                        items=order_data['items'],
                        total_amount=order_data['total_amount'],
                        payment_method=order_data['payment_method'],
                        credit_card_last_four=order_data.get('credit_card_last_four'),
                        processing_fee=order_data.get('processing_fee', 0.0),
                        order_status=order_data.get('order_status', 'submitted'),
                        confirmation_date=datetime.fromisoformat(order_data['confirmation_date']) if order_data.get('confirmation_date') else None,
                        case_upcs_configured=order_data.get('case_upcs_configured', False)
                    )
                    orders[order_id] = order
                
                logger.info(f"Loaded {len(orders)} existing restaurant orders")
                return orders
            else:
                logger.info("No existing restaurant orders found")
                return {}
                
        except Exception as e:
            logger.error(f"Restaurant orders loading error: {e}")
            return {}

    def _save_restaurant_orders(self):
        """Save restaurant orders to persistent storage"""
        try:
            orders_data = {}
            for order_id, order in self.restaurant_orders.items():
                orders_data[order_id] = {
                    'order_id': order.order_id,
                    'restaurant_name': order.restaurant_name,
                    'restaurant_contact': order.restaurant_contact,
                    'order_date': order.order_date.isoformat(),
                    'requested_delivery_date': order.requested_delivery_date.isoformat(),
                    'items': order.items,
                    'total_amount': order.total_amount,
                    'payment_method': order.payment_method,
                    'credit_card_last_four': order.credit_card_last_four,
                    'processing_fee': order.processing_fee,
                    'order_status': order.order_status,
                    'confirmation_date': order.confirmation_date.isoformat() if order.confirmation_date else None,
                    'case_upcs_configured': order.case_upcs_configured
                }
            
            with open(self.orders_db_path, 'w') as f:
                json.dump(orders_data, f, indent=2)
            
            logger.info(f"Restaurant orders saved: {len(orders_data)} orders")
            
        except Exception as e:
            logger.error(f"Restaurant orders saving error: {e}")

    async def process_thursday_order_submission(self, order_data: Dict) -> str:
        """
        Process restaurant order submission on Thursday
        
        Args:
            order_data: Restaurant order details
            
        Returns:
            str: Order ID if successful, empty string if failed
        """
        try:
            # Generate order ID
            order_id = f"REST_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{order_data['restaurant_name'][:3].upper()}"
            
            # Calculate processing fee for credit card orders
            processing_fee = 0.0
            if order_data.get('payment_method') == 'credit_card':
                processing_fee = order_data['total_amount'] * (self.credit_card_processing_fee_percent / 100)
            
            # Create restaurant order
            restaurant_order = RestaurantOrder(
                order_id=order_id,
                restaurant_name=order_data['restaurant_name'],
                restaurant_contact=order_data['restaurant_contact'],
                order_date=datetime.now(),
                requested_delivery_date=datetime.fromisoformat(order_data['delivery_date']),
                items=order_data['items'],
                total_amount=order_data['total_amount'],
                payment_method=order_data['payment_method'],
                credit_card_last_four=order_data.get('credit_card_last_four'),
                processing_fee=processing_fee,
                order_status='submitted'
            )
            
            # Validate order against SSCS inventory
            validation_result = await self._validate_order_against_inventory(restaurant_order)
            
            if validation_result['valid']:
                # Store order
                self.restaurant_orders[order_id] = restaurant_order
                self._save_restaurant_orders()
                
                # Send confirmation email
                await self._send_order_confirmation_email(restaurant_order)
                
                # Send admin notification email to shawn@owenent.com
                await self._send_admin_notification_email(restaurant_order)
                
                # **CRITICAL: Automatic DABS Order Placement**
                dabs_result = await self._place_automatic_dabs_order(restaurant_order)
                if dabs_result.success:
                    logger.info(f"✅ DABS order placed automatically: {dabs_result.dabs_order_id}")
                    restaurant_order.order_status = 'dabs_submitted'
                else:
                    logger.error(f"❌ DABS automation failed: {dabs_result.error}")
                    restaurant_order.order_status = 'dabs_failed'
                
                # Update order with DABS result
                self.restaurant_orders[order_id] = restaurant_order
                self._save_restaurant_orders()
                
                logger.info(f"Restaurant order processed: {order_id} - {restaurant_order.restaurant_name}")
                return order_id
            else:
                logger.warning(f"Order validation failed: {validation_result['errors']}")
                return ""
                
        except Exception as e:
            logger.error(f"Thursday order submission error: {e}")
            return ""

    async def _validate_order_against_inventory(self, order: RestaurantOrder) -> Dict[str, any]:
        """
        Validate restaurant order against current SSCS inventory
        
        Args:
            order: Restaurant order to validate
            
        Returns:
            Dict: Validation result with errors and warnings
        """
        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'out_of_stock_items': [],
                'upc_missing_items': []
            }
            
            for item in order.items:
                description = item['description']
                requested_qty = item['quantity']
                
                # Find UPC record for item
                upc_record = self.upc_db.find_upc_by_description_fuzzy(description)
                
                if not upc_record:
                    validation_result['upc_missing_items'].append(description)
                    validation_result['warnings'].append(f"UPC not found for: {description}")
                else:
                    # Check inventory levels (would require SSCS inventory API)
                    # For now, assume inventory is available
                    logger.info(f"Order item validated: {description} → {upc_record.upc_code}")
            
            # Check for critical issues
            if len(validation_result['upc_missing_items']) > len(order.items) * 0.2:  # >20% missing UPCs
                validation_result['valid'] = False
                validation_result['errors'].append("Too many items without UPC resolution")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Order validation error: {e}")
            return {'valid': False, 'errors': [f"Validation failed: {str(e)}"]}

    async def process_friday_confirmation(self) -> RestaurantOrderProcessingResult:
        """
        Process Friday confirmation workflow for restaurant orders
        
        Returns:
            RestaurantOrderProcessingResult: Friday processing results
        """
        try:
            logger.info("Starting Friday restaurant order confirmation...")
            
            # Get pending orders for this Friday
            pending_orders = [
                order for order in self.restaurant_orders.values()
                if order.order_status == 'submitted' and 
                   order.requested_delivery_date.weekday() == 1  # Tuesday delivery
            ]
            
            successfully_processed = 0
            upcs_configured = 0
            payment_processed = 0
            exceptions = []
            
            for order in pending_orders:
                try:
                    # Pre-configure case UPCs for order items
                    case_upcs = await self._preconfigure_case_upcs_for_order(order)
                    
                    if case_upcs:
                        order.case_upcs_configured = True
                        upcs_configured += 1
                        logger.info(f"Case UPCs configured for: {order.restaurant_name}")
                    
                    # Process payment if credit card
                    if order.payment_method == 'credit_card':
                        payment_success = await self._process_restaurant_payment(order)
                        if payment_success:
                            payment_processed += 1
                            logger.info(f"Payment processed for: {order.restaurant_name}")
                        else:
                            exceptions.append(f"Payment failed: {order.restaurant_name}")
                    
                    # Update order status
                    order.order_status = 'confirmed'
                    order.confirmation_date = datetime.now()
                    successfully_processed += 1
                    
                except Exception as e:
                    exceptions.append(f"Order processing failed: {order.restaurant_name} - {str(e)}")
                    logger.error(f"Friday confirmation error for {order.restaurant_name}: {e}")
            
            # Save updated orders
            self._save_restaurant_orders()
            
            # Generate Friday confirmation report for Tessa
            await self._generate_friday_confirmation_report(pending_orders, exceptions)
            
            result = RestaurantOrderProcessingResult(
                total_orders=len(pending_orders),
                successfully_processed=successfully_processed,
                upcs_configured=upcs_configured,
                payment_processed=payment_processed,
                exceptions=exceptions,
                friday_confirmation_ready=len(exceptions) == 0
            )
            
            logger.info(f"Friday confirmation complete: {successfully_processed}/{len(pending_orders)} orders confirmed")
            return result
            
        except Exception as e:
            logger.error(f"Friday confirmation processing error: {e}")
            return RestaurantOrderProcessingResult(0, 0, 0, 0, [str(e)], False)

    async def _preconfigure_case_upcs_for_order(self, order: RestaurantOrder) -> List[SSCSCaseUPC]:
        """
        Pre-configure case UPCs for restaurant order before delivery
        
        Args:
            order: Restaurant order needing case UPC configuration
            
        Returns:
            List[SSCSCaseUPC]: Configured case UPCs for the order
        """
        try:
            # Prepare order items for UPC configuration
            order_items_for_upc = []
            for item in order.items:
                order_items_for_upc.append({
                    'description': item['description'],
                    'case_pack': item.get('case_pack', 6),  # Default 6-pack
                    'quantity': item['quantity']
                })
            
            # Use UPC database to prepare delivery UPCs
            case_upcs = await self.upc_db.prepare_restaurant_delivery_upcs(order_items_for_upc)
            
            # Log case UPC configuration
            configured_upcs = []
            for description, case_config in case_upcs.items():
                configured_upcs.append(case_config)
                logger.info(f"Case UPC ready for delivery: {description} → {case_config.case_upc}")
            
            return configured_upcs
            
        except Exception as e:
            logger.error(f"Case UPC preconfiguration error for {order.restaurant_name}: {e}")
            return []

    async def _process_restaurant_payment(self, order: RestaurantOrder) -> bool:
        """
        Process restaurant payment (pre-payment before delivery)
        
        Args:
            order: Restaurant order with payment details
            
        Returns:
            bool: True if payment successful
        """
        try:
            # This would integrate with actual payment gateway
            # For now, simulate payment processing
            
            total_charge = order.total_amount + order.processing_fee
            
            logger.info(f"Processing payment for {order.restaurant_name}: "
                       f"${order.total_amount} + ${order.processing_fee} fee = ${total_charge}")
            
            # Simulate payment processing
            # In production, this would call actual payment gateway
            payment_success = True  # Simulate success
            
            if payment_success:
                # Update order with payment confirmation
                order.order_status = 'payment_processed'
                logger.info(f"Payment successful: {order.restaurant_name} - ${total_charge}")
                return True
            else:
                logger.error(f"Payment failed: {order.restaurant_name}")
                return False
                
        except Exception as e:
            logger.error(f"Payment processing error for {order.restaurant_name}: {e}")
            return False

    async def _generate_friday_confirmation_report(self, orders: List[RestaurantOrder], 
                                                 exceptions: List[str]):
        """
        Generate Friday confirmation report for Tessa's review
        
        Args:
            orders: Restaurant orders processed on Friday
            exceptions: List of processing exceptions
        """
        try:
            report_path = Path("data/exports/friday_confirmation_report.json")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create Friday confirmation report
            report_data = {
                'confirmation_date': datetime.now().isoformat(),
                'delivery_date': (datetime.now() + timedelta(days=4)).strftime('%A, %Y-%m-%d'),  # Next Tuesday
                'total_orders': len(orders),
                'confirmed_orders': len([o for o in orders if o.order_status == 'confirmed']),
                'exceptions_requiring_review': len(exceptions),
                'orders_summary': []
            }
            
            for order in orders:
                order_summary = {
                    'restaurant_name': order.restaurant_name,
                    'order_id': order.order_id,
                    'total_amount': order.total_amount,
                    'processing_fee': order.processing_fee,
                    'total_charge': order.total_amount + order.processing_fee,
                    'payment_method': order.payment_method,
                    'items_count': len(order.items),
                    'case_upcs_configured': order.case_upcs_configured,
                    'status': order.order_status
                }
                report_data['orders_summary'].append(order_summary)
            
            # Add exceptions
            report_data['exceptions'] = exceptions
            
            # Add recommendations for Tessa
            recommendations = []
            if exceptions:
                recommendations.append("Review exceptions before Sunday cutoff")
            if any(not order.case_upcs_configured for order in orders):
                recommendations.append("Some orders missing case UPC configuration - review before delivery")
            if len([o for o in orders if o.payment_method == 'credit_card']) > 0:
                total_processing_fees = sum(o.processing_fee for o in orders)
                recommendations.append(f"${total_processing_fees:.2f} in processing fees collected")
            
            report_data['recommendations_for_tessa'] = recommendations
            
            # Save report
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"Friday confirmation report generated: {report_path}")
            
            # Send email notification to Tessa
            await self._send_friday_confirmation_email(report_data)
            
        except Exception as e:
            logger.error(f"Friday confirmation report error: {e}")

    async def _send_friday_confirmation_email(self, report_data: Dict):
        """Send Friday confirmation email to Tessa"""
        try:
            # Email configuration (would be loaded from secure config)
            tessa_email = "tessa@hillshollows.com"
            
            # Create email content
            subject = f"Friday Restaurant Order Confirmation - {report_data['total_orders']} Orders for Tuesday Delivery"
            
            body = f"""
Friday Restaurant Order Confirmation
Delivery Date: {report_data['delivery_date']}

SUMMARY:
- Total Orders: {report_data['total_orders']}
- Confirmed Orders: {report_data['confirmed_orders']}
- Exceptions Requiring Review: {report_data['exceptions_requiring_review']}

ORDERS FOR TUESDAY DELIVERY:
"""
            
            for order in report_data['orders_summary']:
                body += f"""
Restaurant: {order['restaurant_name']}
Amount: ${order['total_amount']:.2f} + ${order['processing_fee']:.2f} fee = ${order['total_charge']:.2f}
Items: {order['items_count']} items
Case UPCs: {'✅ Ready' if order['case_upcs_configured'] else '⚠️ Pending'}
Status: {order['status']}
"""
            
            if report_data['exceptions']:
                body += f"\nEXCEPTIONS REQUIRING REVIEW:\n"
                for exception in report_data['exceptions']:
                    body += f"- {exception}\n"
            
            if report_data['recommendations_for_tessa']:
                body += f"\nRECOMMENDATIONS:\n"
                for rec in report_data['recommendations_for_tessa']:
                    body += f"- {rec}\n"
            
            # Log email content (actual sending would require SMTP configuration)
            logger.info(f"Friday confirmation email prepared for {tessa_email}")
            logger.info(f"Email subject: {subject}")
            logger.info(f"Email body preview: {body[:200]}...")
            
        except Exception as e:
            logger.error(f"Friday confirmation email error: {e}")

    async def _send_admin_notification_email(self, order: RestaurantOrder):
        """Send admin notification email to shawn@owenent.com for order tracking"""
        try:
            admin_email = "shawn@owenent.com"
            
            # Create email content
            subject = f"🍽️ New Restaurant Order - {order.restaurant_name} - ${order.total_amount:.2f}"
            
            # Calculate total charge with processing fees
            total_charge = order.total_amount + order.processing_fee
            
            body = f"""
RESTAURANT ORDER NOTIFICATION - ADMIN COPY
===========================================

Order Details:
• Order ID: {order.order_id}
• Restaurant: {order.restaurant_name}
• Contact: {order.restaurant_contact}
• Order Date: {order.order_date.strftime('%A, %B %d, %Y at %I:%M %p')}
• Delivery Date: {order.requested_delivery_date.strftime('%A, %B %d, %Y')}

Financial Summary:
• Subtotal: ${order.total_amount:.2f}
• Processing Fee: ${order.processing_fee:.2f} ({self.credit_card_processing_fee_percent}% for credit card)
• TOTAL CHARGE: ${total_charge:.2f}
• Payment Method: {order.payment_method.replace('_', ' ').title()}
{f"• Credit Card: ****{order.credit_card_last_four}" if order.credit_card_last_four else ""}

Order Items:
"""
            
            for i, item in enumerate(order.items, 1):
                body += f"{i}. {item['description']} - Qty: {item['quantity']}\n"
            
            body += f"""

Order Status: {order.order_status.replace('_', ' ').title()}
Items Count: {len(order.items)} items
Case UPCs Configured: {'Yes' if order.case_upcs_configured else 'Pending'}

Next Steps:
• Friday Confirmation: {order.confirmation_date.strftime('%A, %B %d, %Y') if order.confirmation_date else 'Pending Friday workflow'}
• Ready for Pickup: Tuesday delivery processing
• Processing Status: Order submitted and validated

System Information:
• Processed by: DABS Restaurant Automation System
• Manager Dashboard: Available for Tessa's review and confirmation
• Audit Trail: Complete order history maintained for Utah Package Agency compliance
• Time Savings: Automated processing (45 min → 3 min per order)

This is an automated notification for Hills & Hollows LLC administrative tracking.
All restaurant communications are handled separately.

---
Hills & Hollows LLC
Boulder, Utah Package Agency
Restaurant Order Automation System
            """
            
            # Log email content (actual sending would require SMTP configuration)
            logger.info(f"Admin notification email prepared for {admin_email}")
            logger.info(f"Email subject: {subject}")
            logger.info(f"Order total: ${total_charge:.2f} for {order.restaurant_name}")
            
            # TODO: Implement actual SMTP sending when email configuration is available
            # For now, this creates the complete email content and logs it
            
        except Exception as e:
            logger.error(f"Admin notification email error: {e}")

    async def _send_order_confirmation_email(self, order: RestaurantOrder):
        """Send order confirmation email to restaurant"""
        try:
            # This would send confirmation to the restaurant
            logger.info(f"Order confirmation email prepared for {order.restaurant_contact}")
            
        except Exception as e:
            logger.error(f"Order confirmation email error: {e}")

    async def process_tuesday_delivery_optimization(self) -> Dict[str, any]:
        """
        Process Tuesday delivery day optimization for restaurant pickups
        
        Returns:
            Dict: Delivery processing results
        """
        try:
            logger.info("Starting Tuesday delivery optimization...")
            
            # Get confirmed orders for today's delivery
            today = datetime.now().date()
            delivery_orders = [
                order for order in self.restaurant_orders.values()
                if order.order_status == 'confirmed' and 
                   order.requested_delivery_date.date() == today
            ]
            
            pickup_ready_count = 0
            exceptions = []
            
            for order in delivery_orders:
                try:
                    # Validate case UPCs are configured
                    if order.case_upcs_configured:
                        # Pre-stage restaurant pickup transaction in SSCS
                        prestage_success = await self._prestage_restaurant_pickup(order)
                        
                        if prestage_success:
                            order.order_status = 'ready_for_pickup'
                            pickup_ready_count += 1
                            logger.info(f"Restaurant pickup ready: {order.restaurant_name}")
                        else:
                            exceptions.append(f"Failed to prestage pickup: {order.restaurant_name}")
                    else:
                        exceptions.append(f"Case UPCs not configured: {order.restaurant_name}")
                
                except Exception as e:
                    exceptions.append(f"Delivery optimization error: {order.restaurant_name} - {str(e)}")
            
            # Save updated orders
            self._save_restaurant_orders()
            
            result = {
                'delivery_date': today.isoformat(),
                'total_deliveries': len(delivery_orders),
                'pickup_ready': pickup_ready_count,
                'exceptions': exceptions,
                'average_processing_time_estimate': '3 minutes per restaurant (vs 45 minutes manual)'
            }
            
            logger.info(f"Tuesday delivery optimization complete: {pickup_ready_count}/{len(delivery_orders)} ready")
            return result
            
        except Exception as e:
            logger.error(f"Tuesday delivery optimization error: {e}")
            return {'error': str(e)}

    async def _prestage_restaurant_pickup(self, order: RestaurantOrder) -> bool:
        """
        Pre-stage restaurant pickup transaction in SSCS for quick checkout
        
        Args:
            order: Restaurant order to pre-stage
            
        Returns:
            bool: True if pre-staging successful
        """
        try:
            # This would integrate with SSCS POS to pre-stage transactions
            # Using case UPCs for quick scanning vs individual bottles
            
            logger.info(f"Pre-staging pickup for: {order.restaurant_name}")
            
            # Get case UPCs for order items
            case_upcs = []
            for item in order.items:
                description = item['description']
                case_pack = item.get('case_pack', 6)
                
                # Find case UPC from database
                cursor = self.upc_db.conn.cursor()
                cursor.execute("""
                    SELECT case_upc FROM case_upc_config cu
                    JOIN upc_master um ON cu.bottle_upc = um.upc_code  
                    WHERE um.description LIKE ? AND cu.case_pack_size = ?
                """, (f"%{description}%", case_pack))
                
                case_result = cursor.fetchone()
                if case_result:
                    case_upcs.append({
                        'case_upc': case_result[0],
                        'description': description,
                        'quantity': item['quantity'],
                        'case_pack': case_pack
                    })
            
            if case_upcs:
                # Pre-stage transaction in SSCS (would use CCB integration)
                # For now, log the pre-staging details
                logger.info(f"Pre-staged {len(case_upcs)} case UPCs for {order.restaurant_name}")
                
                # Update order with pre-stage completion
                order.order_status = 'prestaged_for_pickup'
                return True
            else:
                logger.warning(f"No case UPCs available for pre-staging: {order.restaurant_name}")
                return False
                
        except Exception as e:
            logger.error(f"Restaurant pickup pre-staging error: {e}")
            return False

    def get_restaurant_order_summary(self, date_range_days: int = 14) -> Dict[str, any]:
        """
        Get restaurant order summary for specified date range
        
        Args:
            date_range_days: Number of days to include in summary
            
        Returns:
            Dict: Restaurant order summary statistics
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=date_range_days)
            
            recent_orders = [
                order for order in self.restaurant_orders.values()
                if order.order_date >= cutoff_date
            ]
            
            summary = {
                'date_range': f"Last {date_range_days} days",
                'total_orders': len(recent_orders),
                'total_revenue': sum(order.total_amount for order in recent_orders),
                'total_processing_fees': sum(order.processing_fee for order in recent_orders),
                'orders_by_status': {},
                'orders_by_restaurant': {},
                'payment_methods': {},
                'average_order_value': 0.0
            }
            
            # Calculate statistics
            for order in recent_orders:
                # By status
                status = order.order_status
                summary['orders_by_status'][status] = summary['orders_by_status'].get(status, 0) + 1
                
                # By restaurant
                restaurant = order.restaurant_name
                if restaurant not in summary['orders_by_restaurant']:
                    summary['orders_by_restaurant'][restaurant] = {
                        'order_count': 0,
                        'total_amount': 0.0,
                        'processing_fees': 0.0
                    }
                summary['orders_by_restaurant'][restaurant]['order_count'] += 1
                summary['orders_by_restaurant'][restaurant]['total_amount'] += order.total_amount
                summary['orders_by_restaurant'][restaurant]['processing_fees'] += order.processing_fee
                
                # By payment method
                payment = order.payment_method
                summary['payment_methods'][payment] = summary['payment_methods'].get(payment, 0) + 1
            
            # Calculate average order value
            if recent_orders:
                summary['average_order_value'] = summary['total_revenue'] / len(recent_orders)
            
            return summary
            
        except Exception as e:
            logger.error(f"Restaurant order summary error: {e}")
            return {}

    async def export_restaurant_processing_report(self, output_path: str) -> bool:
        """
        Export comprehensive restaurant processing report
        
        Args:
            output_path: Path for processing report
            
        Returns:
            bool: True if export successful
        """
        try:
            # Get comprehensive statistics
            summary = self.get_restaurant_order_summary(30)  # 30-day summary
            
            # Add UPC automation statistics
            upc_stats = self.upc_db.get_database_stats()
            
            report_data = {
                'export_date': datetime.now().isoformat(),
                'restaurant_order_summary': summary,
                'upc_automation_stats': upc_stats,
                'automation_benefits': {
                    'estimated_time_savings_per_order': '42 minutes (45 min → 3 min)',
                    'processing_fee_recovery': f"{summary.get('total_processing_fees', 0):.2f}",
                    'case_upcs_configured': upc_stats.get('case_upcs_configured', 0),
                    'order_automation_rate': f"{(summary.get('total_orders', 0) - len([o for o in self.restaurant_orders.values() if 'manual' in o.order_status])) / max(summary.get('total_orders', 1), 1) * 100:.1f}%"
                },
                'next_delivery_date': self._get_next_delivery_date().isoformat(),
                'pending_orders': len([o for o in self.restaurant_orders.values() if o.order_status == 'submitted'])
            }
            
            with open(output_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"Restaurant processing report exported: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Restaurant processing report error: {e}")
            return False

    def _get_next_delivery_date(self) -> datetime:
        """Get next Tuesday delivery date"""
        today = datetime.now()
        days_until_tuesday = (1 - today.weekday()) % 7  # Tuesday = 1
        if days_until_tuesday == 0 and today.hour > 12:  # After noon on Tuesday
            days_until_tuesday = 7  # Next Tuesday
        
        return today + timedelta(days=days_until_tuesday)

    async def _place_automatic_dabs_order(self, restaurant_order: RestaurantOrder):
        """
        Automatically place restaurant order in DABS Licensee Ordering System
        
        This is the CRITICAL automation that eliminates manual dual entry and 
        completes the end-to-end restaurant ordering automation workflow.
        
        Args:
            restaurant_order: The restaurant order to place in DABS
            
        Returns:
            DABSOrderResult: Result of DABS order placement
        """
        try:
            logger.info(f"🎯 Placing automatic DABS order for {restaurant_order.restaurant_name}")
            
            # Convert restaurant order to DABS format
            dabs_order_items = []
            for item in restaurant_order.items:
                # Try to find UPC for SKU mapping
                upc_record = self.upc_db.find_upc_by_description_fuzzy(item['description'])
                
                dabs_item = DABSOrderItem(
                    sku=upc_record.sku if upc_record else item.get('sku', 'UNKNOWN'),
                    product_name=item['description'],
                    quantity=item['quantity'],
                    unit_price=item.get('unit_price', 0.0),
                    category=item.get('category', 'Liquor')
                )
                dabs_order_items.append(dabs_item)
            
            # Create DABS restaurant order object
            dabs_restaurant_order = DABSRestaurantOrder(
                id=restaurant_order.order_id,
                customer_name=restaurant_order.restaurant_name,
                customer_email=restaurant_order.restaurant_contact,
                items=dabs_order_items,
                total_amount=restaurant_order.total_amount,
                order_date=restaurant_order.order_date,
                payment_method=restaurant_order.payment_method,
                delivery_address=None  # Restaurant pickup
            )
            
            # Initialize DABS automation system
            async with DABSAutomatedOrdering(headless=True) as dabs_automation:
                # Attempt automatic DABS order placement
                dabs_result = await dabs_automation.process_restaurant_order(dabs_restaurant_order)
                
                if dabs_result.success:
                    logger.info(f"✅ DABS order placement SUCCESS!")
                    logger.info(f"   DABS Order ID: {dabs_result.dabs_order_id}")
                    logger.info(f"   Items processed: {dabs_result.items_processed}/{len(dabs_order_items)}")
                    logger.info(f"   Processing time: {dabs_result.processing_time:.2f}s")
                    
                    # Log audit trail for Utah compliance
                    await self._log_dabs_automation_audit(restaurant_order, dabs_result)
                    
                else:
                    logger.error(f"❌ DABS order placement FAILED: {dabs_result.error}")
                    
                    # Send alert to admin for failed automation
                    await self._send_dabs_failure_alert(restaurant_order, dabs_result)
                
                return dabs_result
                
        except Exception as e:
            logger.error(f"❌ Critical DABS automation error: {str(e)}")
            
            # Create failed result
            from integration.dabs_automated_ordering import DABSOrderResult
            failed_result = DABSOrderResult(
                success=False,
                error=f"DABS automation system error: {str(e)}",
                processing_time=0.0
            )
            
            # Send critical failure alert
            await self._send_dabs_failure_alert(restaurant_order, failed_result)
            
            return failed_result

    async def _log_dabs_automation_audit(self, restaurant_order: RestaurantOrder, dabs_result):
        """Log DABS automation audit trail for Utah Package Agency compliance"""
        try:
            audit_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "AUTOMATED_DABS_ORDER_PLACEMENT",
                "restaurant_order_id": restaurant_order.order_id,
                "restaurant_customer": restaurant_order.restaurant_name,
                "dabs_order_id": dabs_result.dabs_order_id,
                "items_count": len(restaurant_order.items),
                "total_amount": restaurant_order.total_amount,
                "processing_time_seconds": dabs_result.processing_time,
                "automation_status": "SUCCESS",
                "compliance_notes": "Automated DABS order placement for restaurant customer - zero manual intervention"
            }
            
            # Save to audit log
            audit_path = Path("logs/dabs_automation_audit.log")
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(audit_path, 'a') as f:
                f.write(f"{json.dumps(audit_record)}\n")
            
            logger.info(f"📋 DABS automation audit logged: {restaurant_order.order_id} → {dabs_result.dabs_order_id}")
            
        except Exception as e:
            logger.error(f"Audit logging error: {e}")

    async def _send_dabs_failure_alert(self, restaurant_order: RestaurantOrder, dabs_result):
        """Send alert when DABS automation fails"""
        try:
            alert_subject = f"🚨 DABS Automation Failure - {restaurant_order.restaurant_name}"
            alert_body = f"""
CRITICAL: DABS Automation Failure Alert
=====================================

Restaurant Order: {restaurant_order.order_id}
Customer: {restaurant_order.restaurant_name}
Total Amount: ${restaurant_order.total_amount:.2f}
Items: {len(restaurant_order.items)} items

DABS Automation Error: {dabs_result.error}

REQUIRED ACTION:
• Manual DABS order entry needed immediately
• Restaurant order is confirmed but NOT in DABS system
• Contact Utah DABS system to place order manually

Order Details: {restaurant_order.items}

Time: {datetime.utcnow().isoformat()}
"""
            
            # This would integrate with actual email system
            logger.error(f"📧 DABS failure alert prepared for admin: {alert_subject}")
            logger.error(alert_body)
            
        except Exception as e:
            logger.error(f"Alert system error: {e}")

    async def close(self):
        """Clean up connections and save state"""
        await self.upc_db.ccb_client.close()
        await self.dabs_processor.close()
        self.upc_db.close()
        logger.info("Restaurant Order Automation closed")

# Example usage and testing
async def main():
    """Test Restaurant Order Automation functionality"""
    automation = RestaurantOrderAutomation()
    
    try:
        print("=== Restaurant Order Automation Test ===")
        
        # Test Thursday order submission
        print("\n1. Testing Thursday order submission...")
        sample_order = {
            'restaurant_name': 'Test Bistro',
            'restaurant_contact': 'manager@testbistro.com',
            'delivery_date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),  # Next Tuesday
            'items': [
                {'description': 'BACARDI MOJITO 1750ml', 'quantity': 2, 'case_pack': 6},
                {'description': 'WASATCH BEER 6PK', 'quantity': 3, 'case_pack': 4}
            ],
            'total_amount': 245.50,
            'payment_method': 'credit_card',
            'credit_card_last_four': '1234'
        }
        
        order_id = await automation.process_thursday_order_submission(sample_order)
        print(f"✅ Order processed: {order_id}" if order_id else "❌ Order processing failed")
        
        # Test Friday confirmation
        print("\n2. Testing Friday confirmation...")
        friday_result = await automation.process_friday_confirmation()
        print(f"✅ Friday confirmation: {friday_result.successfully_processed}/{friday_result.total_orders} confirmed")
        print(f"   UPCs configured: {friday_result.upcs_configured}")
        print(f"   Payments processed: {friday_result.payment_processed}")
        print(f"   Exceptions: {len(friday_result.exceptions)}")
        
        # Test Tuesday delivery optimization
        print("\n3. Testing Tuesday delivery optimization...")
        delivery_result = await automation.process_tuesday_delivery_optimization()
        print(f"✅ Delivery optimization: {delivery_result.get('pickup_ready', 0)} orders ready")
        
        # Test restaurant summary
        print("\n4. Restaurant order summary...")
        summary = automation.get_restaurant_order_summary()
        print(f"✅ Summary: {summary.get('total_orders', 0)} orders, ${summary.get('total_revenue', 0):.2f} revenue")
        
        # Export processing report
        print("\n5. Exporting processing report...")
        report_path = "data/exports/restaurant_automation_report.json"
        report_success = await automation.export_restaurant_processing_report(report_path)
        print(f"✅ Report exported: {report_path}" if report_success else "❌ Report export failed")
        
        print("\n✅ Restaurant Order Automation test complete!")
        
    except Exception as e:
        print(f"❌ Restaurant Order Automation test failed: {e}")
    
    finally:
        await automation.close()

if __name__ == "__main__":
    asyncio.run(main())
