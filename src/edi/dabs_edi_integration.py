"""
DABS EDI Integration Pipeline
Integrates EDI invoice generation with existing DABS processing system

Business Context:
- Connects monthly DABS Excel processing to EDI delivery
- Automates 90% time reduction workflow (10+ hours → <1 hour)
- Maintains Utah Package Agency compliance
- Delivers $28,000 annual value through automation
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import json
import os

from dabs_edi_generator import DABSEDIGenerator, DABSItem
from dabs_edi_mailer import EDIDeliveryManager, EDIDeliveryResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DABSEDIIntegration:
    """Integration layer for DABS processing and EDI delivery"""
    
    def __init__(self, smtp_config: Optional[Dict[str, Any]] = None):
        """
        Initialize DABS EDI integration
        
        Args:
            smtp_config: SMTP configuration for email delivery
        """
        self.generator = DABSEDIGenerator()
        self.delivery_manager = EDIDeliveryManager(smtp_config)
        
        # Configuration paths
        self.config_dir = Path("config")
        self.data_dir = Path("data")
        self.output_dir = Path("data/edi_output")
        self.backup_dir = Path("data/dabs_backups")
        
        # Ensure directories exist
        for directory in [self.config_dir, self.data_dir, self.output_dir, self.backup_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def process_monthly_dabs_update(self, excel_file_path: str) -> Dict[str, Any]:
        """
        Complete monthly DABS processing workflow with EDI delivery
        
        Args:
            excel_file_path: Path to DABS Excel file
            
        Returns:
            Processing results and delivery status
        """
        start_time = datetime.now()
        logger.info(f"Starting monthly DABS EDI processing: {excel_file_path}")
        
        try:
            # Step 1: Backup original file
            backup_path = await self._backup_original_file(excel_file_path)
            
            # Step 2: Process DABS Excel data
            dabs_items = await self._process_dabs_excel(excel_file_path)
            
            # Step 3: Generate NAXML EDI invoice
            invoice_number = f"DABS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            naxml_content = self.generator.generate_naxml(dabs_items, invoice_number)
            
            # Step 4: Validate NAXML
            validation = self.generator.validate_naxml(naxml_content)
            if not validation['valid']:
                raise ValueError(f"NAXML validation failed: {validation['errors']}")
            
            # Step 5: Save NAXML file
            naxml_file_path = self.generator.save_naxml_file(naxml_content, str(self.output_dir))
            
            # Step 6: Deliver EDI invoice
            delivery_result = self.delivery_manager.deliver_dabs_invoice(naxml_content, invoice_number)
            
            # Step 7: Generate processing report
            processing_time = (datetime.now() - start_time).total_seconds()
            report = await self._generate_processing_report(
                excel_file_path, backup_path, naxml_file_path, 
                dabs_items, validation, delivery_result, processing_time
            )
            
            logger.info(f"Monthly DABS EDI processing completed successfully in {processing_time:.2f} seconds")
            return report
            
        except Exception as e:
            logger.error(f"Monthly DABS EDI processing failed: {str(e)}")
            error_report = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'processing_time': (datetime.now() - start_time).total_seconds()
            }
            await self._log_error_report(error_report)
            return error_report
    
    async def _backup_original_file(self, excel_file_path: str) -> str:
        """
        Backup original DABS Excel file for Utah compliance
        
        Args:
            excel_file_path: Path to original Excel file
            
        Returns:
            Path to backup file
        """
        original_path = Path(excel_file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"DABS_ORIGINAL_{timestamp}_{original_path.name}"
        backup_path = self.backup_dir / backup_filename
        
        # Copy file to backup location
        import shutil
        shutil.copy2(original_path, backup_path)
        
        logger.info(f"Original DABS file backed up to: {backup_path}")
        return str(backup_path)
    
    async def _process_dabs_excel(self, excel_file_path: str) -> List[DABSItem]:
        """
        Process DABS Excel file and convert to DABSItem objects
        
        Args:
            excel_file_path: Path to DABS Excel file
            
        Returns:
            List of DABSItem objects
        """
        logger.info(f"Processing DABS Excel file: {excel_file_path}")
        
        # Read Excel file
        df = pd.read_excel(excel_file_path)
        
        # Validate required columns
        required_columns = ['CSC Code', 'Description', 'Retail Price', 'Cost', 'Category', 'Size']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Convert to DABSItem objects
        dabs_items = []
        for index, row in df.iterrows():
            try:
                item = DABSItem(
                    csc_code=str(row['CSC Code']).strip(),
                    description=str(row['Description']).strip()[:50],  # Limit to 50 chars
                    retail_price=float(row['Retail Price']),
                    cost=float(row['Cost']),
                    category=str(row['Category']).strip().upper(),
                    size=str(row['Size']).strip(),
                    upc=str(row.get('UPC', '')).strip() if pd.notna(row.get('UPC')) else None,
                    vendor_item_code=str(row['CSC Code']).strip()
                )
                
                # Validate item data
                if not item.csc_code or not item.description:
                    logger.warning(f"Row {index + 1}: Missing CSC Code or Description - skipping")
                    continue
                
                if item.retail_price <= 0 or item.cost <= 0:
                    logger.warning(f"Row {index + 1}: Invalid price data - skipping")
                    continue
                
                dabs_items.append(item)
                
            except (ValueError, TypeError) as e:
                logger.error(f"Row {index + 1}: Error processing item - {str(e)}")
                continue
        
        logger.info(f"Processed {len(dabs_items)} valid DABS items from {len(df)} rows")
        
        # Validate minimum item count (should be close to 1,239)
        if len(dabs_items) < 1000:
            logger.warning(f"Low item count: {len(dabs_items)} (expected ~1,239)")
        
        return dabs_items
    
    async def _generate_processing_report(self, 
                                        excel_file_path: str,
                                        backup_path: str,
                                        naxml_file_path: str,
                                        dabs_items: List[DABSItem],
                                        validation: Dict[str, Any],
                                        delivery_result: EDIDeliveryResult,
                                        processing_time: float) -> Dict[str, Any]:
        """
        Generate comprehensive processing report
        
        Args:
            excel_file_path: Original Excel file path
            backup_path: Backup file path
            naxml_file_path: Generated NAXML file path
            dabs_items: Processed DABS items
            validation: NAXML validation results
            delivery_result: EDI delivery results
            processing_time: Total processing time in seconds
            
        Returns:
            Comprehensive processing report
        """
        # Calculate statistics
        total_retail_value = sum(item.retail_price for item in dabs_items)
        total_cost_value = sum(item.cost for item in dabs_items)
        average_margin = ((total_retail_value - total_cost_value) / total_retail_value * 100) if total_retail_value > 0 else 0
        
        # Category breakdown
        category_counts = {}
        for item in dabs_items:
            category_counts[item.category] = category_counts.get(item.category, 0) + 1
        
        report = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'processing_time_seconds': processing_time,
            'files': {
                'original_excel': excel_file_path,
                'backup_file': backup_path,
                'naxml_file': naxml_file_path,
                'naxml_filename': delivery_result.filename
            },
            'data_statistics': {
                'total_items': len(dabs_items),
                'total_retail_value': round(total_retail_value, 2),
                'total_cost_value': round(total_cost_value, 2),
                'average_margin_percent': round(average_margin, 2),
                'category_breakdown': category_counts
            },
            'validation_results': validation,
            'edi_delivery': {
                'success': delivery_result.success,
                'filename': delivery_result.filename,
                'edi_email': delivery_result.edi_email,
                'file_size_bytes': delivery_result.file_size,
                'error_message': delivery_result.error_message
            },
            'business_metrics': {
                'time_savings_hours': round((10.0 - (processing_time / 3600)), 2),  # Assuming 10 hours manual
                'time_reduction_percent': round((1 - (processing_time / 36000)) * 100, 2),  # 10 hours = 36000 seconds
                'estimated_cost_savings': round((10.0 - (processing_time / 3600)) * 25, 2),  # $25/hour
                'utah_compliance': 'MAINTAINED' if validation['valid'] else 'AT_RISK'
            }
        }
        
        # Save report
        report_filename = f"DABS_EDI_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.output_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Processing report saved to: {report_path}")
        return report
    
    async def _log_error_report(self, error_report: Dict[str, Any]):
        """
        Log error report for troubleshooting
        
        Args:
            error_report: Error details and context
        """
        error_log_dir = Path("logs/edi_errors")
        error_log_dir.mkdir(parents=True, exist_ok=True)
        
        error_filename = f"DABS_EDI_Error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        error_path = error_log_dir / error_filename
        
        with open(error_path, 'w', encoding='utf-8') as f:
            json.dump(error_report, f, indent=2, ensure_ascii=False)
        
        logger.error(f"Error report saved to: {error_path}")
    
    async def validate_system_health(self) -> Dict[str, Any]:
        """
        Validate system health and readiness for EDI processing
        
        Returns:
            System health status
        """
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'HEALTHY',
            'checks': {}
        }
        
        # Check directories
        directories = [self.config_dir, self.data_dir, self.output_dir, self.backup_dir]
        for directory in directories:
            health_report['checks'][f'directory_{directory.name}'] = {
                'status': 'OK' if directory.exists() else 'MISSING',
                'path': str(directory)
            }
            if not directory.exists():
                health_report['overall_status'] = 'DEGRADED'
        
        # Check SMTP configuration
        smtp_validation = self.delivery_manager.mailer.validate_smtp_config()
        health_report['checks']['smtp_config'] = {
            'status': 'OK' if smtp_validation['valid'] else 'FAILED',
            'errors': smtp_validation['errors'],
            'warnings': smtp_validation['warnings']
        }
        if not smtp_validation['valid']:
            health_report['overall_status'] = 'FAILED'
        
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.data_dir)
            free_gb = free / (1024**3)
            health_report['checks']['disk_space'] = {
                'status': 'OK' if free_gb > 1.0 else 'LOW',
                'free_gb': round(free_gb, 2)
            }
            if free_gb < 0.5:
                health_report['overall_status'] = 'DEGRADED'
        except Exception as e:
            health_report['checks']['disk_space'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        logger.info(f"System health check: {health_report['overall_status']}")
        return health_report

class DABSEDIScheduler:
    """Scheduler for automated DABS EDI processing"""
    
    def __init__(self, integration: DABSEDIIntegration):
        self.integration = integration
        self.schedule_config = {
            'monthly_day': 25,  # Process on 25th of each month
            'monthly_hour': 3,  # Process at 3:00 AM
            'monthly_minute': 0
        }
    
    async def schedule_monthly_processing(self, excel_file_path: str):
        """
        Schedule monthly DABS processing
        
        Args:
            excel_file_path: Path to DABS Excel file
        """
        logger.info("Scheduling monthly DABS EDI processing")
        
        # In production, this would integrate with a proper scheduler like Celery
        # For now, we'll process immediately
        result = await self.integration.process_monthly_dabs_update(excel_file_path)
        
        if result['success']:
            logger.info("Scheduled DABS processing completed successfully")
            await self._send_success_notification(result)
        else:
            logger.error("Scheduled DABS processing failed")
            await self._send_failure_notification(result)
        
        return result
    
    async def _send_success_notification(self, result: Dict[str, Any]):
        """Send success notification to stakeholders"""
        logger.info(f"DABS EDI Success: {result['data_statistics']['total_items']} items processed in {result['processing_time_seconds']:.2f}s")
    
    async def _send_failure_notification(self, result: Dict[str, Any]):
        """Send failure notification to stakeholders"""
        logger.error(f"DABS EDI Failure: {result.get('error', 'Unknown error')}")

# Example usage and integration points
async def main():
    """Example main function for DABS EDI integration"""
    
    # Initialize integration
    smtp_config = {
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'username': os.getenv('SMTP_USERNAME'),
        'password': os.getenv('SMTP_PASSWORD'),
        'use_tls': True
    }
    
    integration = DABSEDIIntegration(smtp_config)
    
    # Health check
    health = await integration.validate_system_health()
    print(f"System Health: {health['overall_status']}")
    
    if health['overall_status'] in ['HEALTHY', 'DEGRADED']:
        # Example processing (replace with actual file path)
        excel_file = "data/DABS_Monthly_Update_202508.xlsx"
        
        if Path(excel_file).exists():
            # Process monthly update
            result = await integration.process_monthly_dabs_update(excel_file)
            
            if result['success']:
                print(f"✅ DABS EDI processing successful!")
                print(f"   Items processed: {result['data_statistics']['total_items']}")
                print(f"   Processing time: {result['processing_time_seconds']:.2f} seconds")
                print(f"   Time savings: {result['business_metrics']['time_savings_hours']:.2f} hours")
                print(f"   EDI delivered: {result['edi_delivery']['success']}")
            else:
                print(f"❌ DABS EDI processing failed: {result.get('error')}")
        else:
            print(f"⚠️  Excel file not found: {excel_file}")
    else:
        print("❌ System health check failed - cannot process DABS EDI")

if __name__ == "__main__":
    asyncio.run(main())
