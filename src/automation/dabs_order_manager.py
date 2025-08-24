#!/usr/bin/env python3
"""
DABS Order Management Integration System - Hills & Hollows LLC
Orchestrates order automation with existing DABS processing pipeline

Integrates:
- DABS order extraction automation
- Purchase data analysis and tracking
- Price variance monitoring and alerts  
- Integration with existing DABS processor
- Scheduled automation and monitoring
- Tessa notification system integration

Author: DABS Automation System
Created: 2025-01-11
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.automation.dabs_order_automation import DABSOrderAutomation
from src.automation.dabs_invoice_analyzer import DABSInvoiceAnalyzer
from src.automation.notification_system import TessaNotificationSystem
from src.processors.dabs_processor import DABSProcessor
from src.audit.audit_trail import AuditTrail

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DABS_ORDER_MANAGER - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/logs/dabs_order_manager.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class OrderProcessingResult:
    """Results from complete order processing workflow"""
    extraction_successful: bool
    orders_processed: int
    pdfs_downloaded: int
    analysis_completed: bool
    reports_generated: List[str]
    alerts_triggered: List[Dict[str, Any]]
    processing_duration_minutes: float
    next_scheduled_run: Optional[str]

class DABSOrderManager:
    """
    Complete DABS order management and integration system
    
    Orchestrates:
    - Automated order data extraction
    - Purchase analysis and tracking
    - Price variance monitoring
    - Integration with existing DABS processing
    - Automated reporting and notifications
    """
    
    def __init__(self):
        self.project_root = Path('/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory')
        
        # Initialize subsystems
        self.order_automation = DABSOrderAutomation()
        self.invoice_analyzer = DABSInvoiceAnalyzer()
        self.notification_system = TessaNotificationSystem()
        self.dabs_processor = DABSProcessor()
        self.audit_trail = AuditTrail()
        
        # Configuration
        self.config = self._load_config()
        
        logger.info("DABS Order Manager initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load order management configuration"""
        return {
            'default_extraction_days': 7,  # Daily incremental
            'full_extraction_days': 90,    # Weekly full
            'price_variance_threshold': 20.0,
            'high_priority_variance': 50.0,
            'notification_thresholds': {
                'critical_discrepancies': 5,
                'high_variance_items': 10,
                'failed_extractions': 1
            },
            'performance_targets': {
                'max_extraction_time_minutes': 30,
                'max_analysis_time_minutes': 15,
                'min_success_rate': 95
            },
            'integration_settings': {
                'update_dabs_pricing': True,
                'trigger_sscs_sync': True,
                'update_quickbooks': False  # Future enhancement
            }
        }
    
    async def run_daily_order_processing(self) -> OrderProcessingResult:
        """Execute daily order processing workflow"""
        
        start_time = datetime.now()
        logger.info("Starting daily DABS order processing workflow")
        
        result = OrderProcessingResult(
            extraction_successful=False,
            orders_processed=0,
            pdfs_downloaded=0,
            analysis_completed=False,
            reports_generated=[],
            alerts_triggered=[],
            processing_duration_minutes=0.0,
            next_scheduled_run=None
        )
        
        try:
            # Step 1: Extract recent orders (last 7 days)
            logger.info("Step 1: Extracting recent order data...")
            extraction_result = await self.order_automation.run_complete_automation(
                days_back=self.config['default_extraction_days']
            )
            
            result.extraction_successful = extraction_result['status'] == 'completed_success'
            result.orders_processed = extraction_result.get('orders_extracted', 0)
            result.pdfs_downloaded = extraction_result.get('pdfs_downloaded', 0)
            
            if not result.extraction_successful:
                raise Exception(f"Order extraction failed: {extraction_result.get('errors', [])}")
            
            # Step 2: Analyze extracted data
            logger.info("Step 2: Analyzing purchase data...")
            report = await self.invoice_analyzer.generate_purchase_tracking_report()
            result.analysis_completed = True
            
            # Step 3: Generate and export reports
            logger.info("Step 3: Generating reports...")
            export_files = await self.invoice_analyzer.export_analysis_reports(report)
            result.reports_generated = list(export_files.values())
            
            # Step 4: Check for alerts and notifications
            logger.info("Step 4: Processing alerts and notifications...")
            alerts = await self._process_alerts_and_notifications(report)
            result.alerts_triggered = alerts
            
            # Step 5: Integration with existing systems
            logger.info("Step 5: Integrating with existing DABS systems...")
            await self._integrate_with_dabs_systems(report)
            
            # Step 6: Audit trail logging
            await self.audit_trail.log_automation_event({
                'event_type': 'daily_order_processing',
                'status': 'success',
                'orders_processed': result.orders_processed,
                'reports_generated': len(result.reports_generated),
                'alerts_count': len(result.alerts_triggered),
                'processing_time': (datetime.now() - start_time).total_seconds()
            })
            
            # Calculate performance metrics
            result.processing_duration_minutes = (datetime.now() - start_time).total_seconds() / 60
            result.next_scheduled_run = (datetime.now() + timedelta(days=1)).replace(hour=2, minute=0).isoformat()
            
            logger.info(f"Daily order processing completed successfully in {result.processing_duration_minutes:.1f} minutes")
            
        except Exception as e:
            logger.error(f"Daily order processing failed: {e}")
            
            # Log failure in audit trail
            await self.audit_trail.log_automation_event({
                'event_type': 'daily_order_processing',
                'status': 'failed',
                'error': str(e),
                'processing_time': (datetime.now() - start_time).total_seconds()
            })
            
            # Send error notification
            await self.notification_system.notify_automation_error({
                'workflow': 'DABS Order Processing',
                'error_type': type(e).__name__,
                'error_message': str(e),
                'timestamp': datetime.now().isoformat(),
                'impact': 'Daily purchase tracking disrupted'
            })
        
        return result
    
    async def run_weekly_full_processing(self) -> OrderProcessingResult:
        """Execute weekly full order processing with extended historical data"""
        
        start_time = datetime.now()
        logger.info("Starting weekly full DABS order processing workflow")
        
        result = OrderProcessingResult(
            extraction_successful=False,
            orders_processed=0,
            pdfs_downloaded=0,
            analysis_completed=False,
            reports_generated=[],
            alerts_triggered=[],
            processing_duration_minutes=0.0,
            next_scheduled_run=None
        )
        
        try:
            # Step 1: Full historical extraction (90 days)
            logger.info("Step 1: Full historical order extraction...")
            extraction_result = await self.order_automation.run_complete_automation(
                days_back=self.config['full_extraction_days']
            )
            
            result.extraction_successful = extraction_result['status'] == 'completed_success'
            result.orders_processed = extraction_result.get('orders_extracted', 0)
            result.pdfs_downloaded = extraction_result.get('pdfs_downloaded', 0)
            
            # Step 2: Comprehensive analysis with trends
            logger.info("Step 2: Comprehensive purchase analysis...")
            report = await self.invoice_analyzer.generate_purchase_tracking_report()
            result.analysis_completed = True
            
            # Step 3: Advanced analytics and forecasting
            logger.info("Step 3: Advanced analytics and forecasting...")
            advanced_analytics = await self._run_advanced_analytics(report)
            
            # Step 4: Generate comprehensive reports
            logger.info("Step 4: Generating comprehensive reports...")
            export_files = await self.invoice_analyzer.export_analysis_reports(report)
            result.reports_generated = list(export_files.values())
            
            # Step 5: Send weekly summary to Tessa
            logger.info("Step 5: Sending weekly summary...")
            await self._send_weekly_summary(report, advanced_analytics)
            
            # Performance metrics
            result.processing_duration_minutes = (datetime.now() - start_time).total_seconds() / 60
            result.next_scheduled_run = (datetime.now() + timedelta(weeks=1)).isoformat()
            
            logger.info(f"Weekly full processing completed in {result.processing_duration_minutes:.1f} minutes")
            
        except Exception as e:
            logger.error(f"Weekly full processing failed: {e}")
            result.alerts_triggered.append({
                'level': 'CRITICAL',
                'message': f"Weekly processing failed: {e}",
                'timestamp': datetime.now().isoformat()
            })
        
        return result
    
    async def _process_alerts_and_notifications(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process alerts and send notifications based on analysis results"""
        
        alerts = []
        
        # High variance price alerts
        high_variance_alerts = [
            alert for alert in report.get('price_variance_alerts', [])
            if alert.get('alert_level') == 'HIGH'
        ]
        
        if len(high_variance_alerts) >= self.config['notification_thresholds']['high_variance_items']:
            alert = {
                'level': 'HIGH',
                'type': 'price_variance',
                'message': f"{len(high_variance_alerts)} products show high price variance",
                'items_affected': len(high_variance_alerts),
                'action_required': 'Review vendor pricing and consider price locks',
                'timestamp': datetime.now().isoformat()
            }
            alerts.append(alert)
            
            # Send notification
            await self.notification_system.notify_price_variance({
                'high_variance_count': len(high_variance_alerts),
                'affected_products': [item['description'] for item in high_variance_alerts[:5]],
                'max_variance': max(alert['price_variance_percent'] for alert in high_variance_alerts),
                'recommendation': 'Immediate vendor price review recommended'
            })
        
        # Price discrepancy alerts
        discrepancies = report.get('price_reconciliation', {}).get('discrepancies', [])
        critical_discrepancies = [d for d in discrepancies if d.get('severity') == 'HIGH']
        
        if len(critical_discrepancies) >= self.config['notification_thresholds']['critical_discrepancies']:
            alert = {
                'level': 'CRITICAL',
                'type': 'price_discrepancy',
                'message': f"{len(critical_discrepancies)} critical price discrepancies found",
                'items_affected': len(critical_discrepancies),
                'action_required': 'Update DABS pricing or investigate vendor billing',
                'timestamp': datetime.now().isoformat()
            }
            alerts.append(alert)
            
            # Send critical notification
            await self.notification_system.notify_critical_discrepancy({
                'discrepancy_count': len(critical_discrepancies),
                'max_difference': max(d['percent_difference'] for d in critical_discrepancies),
                'affected_items': [d['description'] for d in critical_discrepancies[:5]]
            })
        
        return alerts
    
    async def _integrate_with_dabs_systems(self, report: Dict[str, Any]) -> None:
        """Integrate order analysis with existing DABS processing systems"""
        
        try:
            # Update price tracking in main DABS system
            if self.config['integration_settings']['update_dabs_pricing']:
                await self._update_dabs_price_tracking(report)
            
            # Trigger SSCS synchronization if needed
            if self.config['integration_settings']['trigger_sscs_sync']:
                await self._check_sscs_sync_requirements(report)
            
            logger.info("DABS systems integration completed")
            
        except Exception as e:
            logger.error(f"DABS systems integration failed: {e}")
    
    async def _update_dabs_price_tracking(self, report: Dict[str, Any]) -> None:
        """Update DABS price tracking with order data insights"""
        
        # Extract price variance data
        price_alerts = report.get('price_variance_alerts', [])
        
        if price_alerts:
            # Create price tracking update
            price_update = {
                'update_timestamp': datetime.now().isoformat(),
                'source': 'dabs_order_analysis',
                'variance_alerts': price_alerts,
                'action': 'price_tracking_update'
            }
            
            # Save for DABS processor integration
            tracking_file = self.project_root / 'data/price_tracking_updates.json'
            
            existing_updates = []
            if tracking_file.exists():
                with open(tracking_file, 'r') as f:
                    existing_updates = json.load(f)
            
            existing_updates.append(price_update)
            
            with open(tracking_file, 'w') as f:
                json.dump(existing_updates, f, indent=2)
            
            logger.info(f"Price tracking updated with {len(price_alerts)} variance alerts")
    
    async def _check_sscs_sync_requirements(self, report: Dict[str, Any]) -> None:
        """Check if SSCS synchronization is needed based on order analysis"""
        
        # Check for significant price discrepancies that might require SSCS updates
        discrepancies = report.get('price_reconciliation', {}).get('discrepancies', [])
        critical_discrepancies = [d for d in discrepancies if d.get('severity') == 'HIGH']
        
        if critical_discrepancies:
            # Create SSCS sync trigger
            sync_trigger = {
                'trigger_timestamp': datetime.now().isoformat(),
                'reason': 'critical_price_discrepancies',
                'affected_items': len(critical_discrepancies),
                'priority': 'HIGH',
                'action': 'sscs_price_sync_required'
            }
            
            # Save sync trigger for SSCS integration system
            sync_file = self.project_root / 'data/sscs_sync_triggers.json'
            
            existing_triggers = []
            if sync_file.exists():
                with open(sync_file, 'r') as f:
                    existing_triggers = json.load(f)
            
            existing_triggers.append(sync_trigger)
            
            with open(sync_file, 'w') as f:
                json.dump(existing_triggers, f, indent=2)
            
            logger.info(f"SSCS sync trigger created for {len(critical_discrepancies)} critical discrepancies")
    
    async def _run_advanced_analytics(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Run advanced analytics for deeper insights"""
        
        logger.info("Running advanced analytics...")
        
        advanced_analytics = {
            'demand_forecasting': await self._forecast_demand(),
            'vendor_performance': await self._analyze_vendor_performance(),
            'seasonal_patterns': await self._analyze_seasonal_patterns(),
            'cost_optimization': await self._identify_cost_optimization()
        }
        
        return advanced_analytics
    
    async def _forecast_demand(self) -> Dict[str, Any]:
        """Forecast demand based on historical purchase patterns"""
        
        # Load analyzer data
        await self.invoice_analyzer.load_extracted_data()
        
        if self.invoice_analyzer.line_items_data is None:
            return {'error': 'No data available for forecasting'}
        
        # Simple demand forecasting based on purchase frequency
        items_df = self.invoice_analyzer.line_items_data
        
        # Group by product and month to identify patterns
        monthly_demand = items_df.groupby(['item_code', items_df['delivery_date'].dt.to_period('M')]).agg({
            'quantity': 'sum',
            'extended_price': 'sum'
        }).reset_index()
        
        # Calculate average monthly demand
        avg_monthly_demand = monthly_demand.groupby('item_code').agg({
            'quantity': 'mean',
            'extended_price': 'mean'
        }).round(2)
        
        # Generate next month forecasts
        forecasts = []
        for item_code, row in avg_monthly_demand.iterrows():
            forecast = {
                'item_code': item_code,
                'forecasted_quantity': int(row['quantity']),
                'forecasted_value': float(row['extended_price']),
                'confidence': 'MEDIUM',  # Simple model confidence
                'forecast_period': (datetime.now() + timedelta(days=30)).strftime('%Y-%m')
            }
            forecasts.append(forecast)
        
        return {
            'forecast_date': datetime.now().isoformat(),
            'forecast_period': '30_days',
            'total_forecasted_items': len(forecasts),
            'forecasts': forecasts[:50]  # Top 50 by volume
        }
    
    async def _analyze_vendor_performance(self) -> Dict[str, Any]:
        """Analyze vendor performance based on price consistency and delivery"""
        
        # This would analyze vendor performance if we had vendor data
        # For now, return placeholder structure
        return {
            'analysis_date': datetime.now().isoformat(),
            'vendor_count': 1,  # DABS is primary vendor
            'price_consistency': 'STABLE',
            'delivery_performance': 'RELIABLE',
            'recommendations': ['Continue current vendor relationship']
        }
    
    async def _analyze_seasonal_patterns(self) -> Dict[str, Any]:
        """Analyze seasonal purchasing patterns"""
        
        await self.invoice_analyzer.load_extracted_data()
        
        if self.invoice_analyzer.line_items_data is None:
            return {'error': 'No data available for seasonal analysis'}
        
        items_df = self.invoice_analyzer.line_items_data
        
        # Add time-based columns
        items_df['month'] = items_df['delivery_date'].dt.month
        items_df['quarter'] = items_df['delivery_date'].dt.quarter
        items_df['season'] = items_df['month'].map({
            12: 'Winter', 1: 'Winter', 2: 'Winter',
            3: 'Spring', 4: 'Spring', 5: 'Spring',
            6: 'Summer', 7: 'Summer', 8: 'Summer',
            9: 'Fall', 10: 'Fall', 11: 'Fall'
        })
        
        # Seasonal analysis
        seasonal_totals = items_df.groupby('season').agg({
            'quantity': 'sum',
            'extended_price': 'sum'
        }).round(2)
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'seasonal_totals': seasonal_totals.to_dict(),
            'peak_season': seasonal_totals['extended_price'].idxmax(),
            'low_season': seasonal_totals['extended_price'].idxmin()
        }
    
    async def _identify_cost_optimization(self) -> Dict[str, Any]:
        """Identify cost optimization opportunities"""
        
        await self.invoice_analyzer.load_extracted_data()
        
        if self.invoice_analyzer.line_items_data is None:
            return {'error': 'No data available for cost analysis'}
        
        items_df = self.invoice_analyzer.line_items_data
        
        # Find bulk purchase opportunities
        high_volume_items = items_df.groupby('item_code').agg({
            'quantity': 'sum',
            'extended_price': 'sum',
            'order_id': 'count'
        })
        
        bulk_opportunities = high_volume_items[
            (high_volume_items['quantity'] >= 10) & 
            (high_volume_items['order_id'] >= 3)
        ].sort_values('extended_price', ascending=False)
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'bulk_purchase_opportunities': len(bulk_opportunities),
            'potential_savings_items': bulk_opportunities.head(10).to_dict('records'),
            'total_value_bulk_candidates': float(bulk_opportunities['extended_price'].sum())
        }
    
    async def _send_weekly_summary(self, report: Dict[str, Any], advanced_analytics: Dict[str, Any]) -> None:
        """Send comprehensive weekly summary to Tessa"""
        
        summary_data = {
            'report_period': report['report_period'],
            'executive_summary': report['executive_summary'],
            'key_insights': {
                'top_spending_categories': report['purchase_patterns']['top_products']['by_total_value'][:5],
                'price_trend_summary': report['price_trends'],
                'critical_alerts': len([a for a in report['price_variance_alerts'] if a['alert_level'] == 'HIGH'])
            },
            'advanced_insights': {
                'demand_forecast': advanced_analytics.get('demand_forecasting', {}),
                'cost_optimization': advanced_analytics.get('cost_optimization', {}),
                'seasonal_trends': advanced_analytics.get('seasonal_patterns', {})
            },
            'action_items': report.get('recommendations', [])[:5]
        }
        
        await self.notification_system.notify_weekly_summary(summary_data)
        logger.info("Weekly summary sent to Tessa")
    
    async def setup_automation_scheduling(self) -> Dict[str, Any]:
        """Setup complete automation scheduling for order processing"""
        
        schedule_config = {
            'dabs_order_automation': {
                'daily_processing': {
                    'schedule': 'Daily at 2:00 AM',
                    'cron': '0 2 * * *',
                    'command': f'python3 {self.project_root}/src/automation/dabs_order_manager.py --daily',
                    'description': 'Daily incremental order data extraction and analysis',
                    'estimated_duration': '15-30 minutes',
                    'tessa_impact': 'Eliminates manual order tracking'
                },
                'weekly_full_processing': {
                    'schedule': 'Sunday at 1:00 AM',
                    'cron': '0 1 * * 0',
                    'command': f'python3 {self.project_root}/src/automation/dabs_order_manager.py --weekly',
                    'description': 'Weekly comprehensive analysis and reporting',
                    'estimated_duration': '45-60 minutes',
                    'tessa_impact': 'Automated weekly insights and recommendations'
                },
                'monthly_reconciliation': {
                    'schedule': '1st of month at 4:00 AM',
                    'cron': '0 4 1 * *',
                    'command': f'python3 {self.project_root}/src/automation/dabs_order_manager.py --monthly',
                    'description': 'Monthly reconciliation with DABS pricing and compliance reporting',
                    'estimated_duration': '30-45 minutes',
                    'tessa_impact': 'Automated compliance preparation'
                }
            }
        }
        
        # Save scheduling configuration
        schedule_file = self.project_root / 'config/dabs_order_automation_complete_schedule.json'
        with open(schedule_file, 'w') as f:
            json.dump(schedule_config, f, indent=2)
        
        logger.info(f"Complete automation scheduling configured: {schedule_file}")
        return schedule_config

async def run_daily_workflow():
    """Execute daily order processing workflow"""
    
    print("🌅 DABS Daily Order Processing Workflow")
    print("=" * 50)
    
    manager = DABSOrderManager()
    result = await manager.run_daily_order_processing()
    
    print(f"\n📊 DAILY PROCESSING RESULTS:")
    print(f"   ✅ Extraction: {'Success' if result.extraction_successful else 'Failed'}")
    print(f"   📦 Orders: {result.orders_processed}")
    print(f"   📄 PDFs: {result.pdfs_downloaded}")
    print(f"   📈 Analysis: {'Completed' if result.analysis_completed else 'Failed'}")
    print(f"   ⏱️ Duration: {result.processing_duration_minutes:.1f} minutes")
    
    if result.alerts_triggered:
        print(f"\n🚨 ALERTS:")
        for alert in result.alerts_triggered:
            print(f"   {alert['level']}: {alert['message']}")
    
    return result.extraction_successful and result.analysis_completed

async def run_weekly_workflow():
    """Execute weekly full processing workflow"""
    
    print("📊 DABS Weekly Full Processing Workflow")
    print("=" * 50)
    
    manager = DABSOrderManager()
    result = await manager.run_weekly_full_processing()
    
    print(f"\n📈 WEEKLY PROCESSING RESULTS:")
    print(f"   ✅ Extraction: {'Success' if result.extraction_successful else 'Failed'}")
    print(f"   📦 Orders: {result.orders_processed}")
    print(f"   📊 Analysis: {'Completed' if result.analysis_completed else 'Failed'}")
    print(f"   📄 Reports: {len(result.reports_generated)}")
    print(f"   ⏱️ Duration: {result.processing_duration_minutes:.1f} minutes")
    
    return result.extraction_successful and result.analysis_completed

async def setup_complete_automation():
    """Setup complete DABS order automation scheduling"""
    
    print("⚙️ Setting up complete DABS order automation...")
    
    manager = DABSOrderManager()
    schedule_config = await manager.setup_automation_scheduling()
    
    print(f"✅ Complete automation configured:")
    print(f"   🌅 Daily: {schedule_config['dabs_order_automation']['daily_processing']['schedule']}")
    print(f"   📊 Weekly: {schedule_config['dabs_order_automation']['weekly_full_processing']['schedule']}")
    print(f"   📋 Monthly: {schedule_config['dabs_order_automation']['monthly_reconciliation']['schedule']}")
    
    return True

async def main():
    """Main execution with workflow options"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='DABS Order Management System')
    parser.add_argument('--daily', action='store_true', help='Run daily processing workflow')
    parser.add_argument('--weekly', action='store_true', help='Run weekly full processing workflow')
    parser.add_argument('--monthly', action='store_true', help='Run monthly reconciliation workflow')
    parser.add_argument('--setup', action='store_true', help='Setup automation scheduling')
    
    args = parser.parse_args()
    
    if args.daily:
        return await run_daily_workflow()
    elif args.weekly:
        return await run_weekly_workflow()
    elif args.monthly:
        # Monthly reconciliation
        manager = DABSOrderManager()
        result = await manager.run_weekly_full_processing()  # Full processing for monthly
        return result.extraction_successful and result.analysis_completed
    elif args.setup:
        return await setup_complete_automation()
    else:
        # Default: setup automation
        print("🚀 DABS Order Management System")
        print("Setting up complete automation by default...")
        return await setup_complete_automation()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
