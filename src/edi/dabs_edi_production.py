"""
DABS EDI Production Deployment and Monitoring System
Production-ready deployment with monitoring, alerting, and maintenance

Business Context:
- Ensures 99.9% uptime for monthly DABS processing
- Maintains Utah Package Agency compliance requirements
- Delivers consistent 90% time reduction (10+ hours → <1 hour)
- Provides $28,000 annual value through reliable automation
"""

import asyncio
import logging
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import schedule
import time
from dataclasses import dataclass, asdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dabs_edi_integration import DABSEDIIntegration, DABSEDIScheduler

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dabs_edi_production.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProductionMetrics:
    """Production metrics for monitoring"""
    timestamp: str
    processing_time_seconds: float
    items_processed: int
    success_rate: float
    error_count: int
    uptime_hours: float
    memory_usage_mb: float
    disk_usage_gb: float
    last_successful_run: Optional[str] = None
    last_error: Optional[str] = None

class DABSEDIProductionMonitor:
    """Production monitoring and alerting system"""
    
    def __init__(self, alert_config: Optional[Dict[str, Any]] = None):
        """
        Initialize production monitor
        
        Args:
            alert_config: Alert configuration for notifications
        """
        self.alert_config = alert_config or {
            'smtp_server': os.getenv('ALERT_SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('ALERT_SMTP_PORT', '587')),
            'username': os.getenv('ALERT_SMTP_USERNAME'),
            'password': os.getenv('ALERT_SMTP_PASSWORD'),
            'alert_recipients': os.getenv('ALERT_RECIPIENTS', '').split(','),
            'use_tls': True
        }
        
        self.metrics_history: List[ProductionMetrics] = []
        self.start_time = datetime.now()
        
        # Alert thresholds
        self.thresholds = {
            'max_processing_time': 1800,  # 30 minutes
            'min_success_rate': 95.0,     # 95%
            'max_error_count': 5,         # 5 errors per day
            'min_disk_space_gb': 1.0,     # 1GB free space
            'max_memory_usage_mb': 512    # 512MB memory usage
        }
        
        # Create monitoring directories
        self.logs_dir = Path("logs")
        self.metrics_dir = Path("logs/metrics")
        self.alerts_dir = Path("logs/alerts")
        
        for directory in [self.logs_dir, self.metrics_dir, self.alerts_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def collect_system_metrics(self) -> ProductionMetrics:
        """
        Collect current system metrics
        
        Returns:
            Current system metrics
        """
        try:
            import psutil
            
            # System metrics
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            
            # Disk usage
            disk_usage = psutil.disk_usage('.')
            disk_free_gb = disk_usage.free / (1024**3)
            
            # Calculate uptime
            uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
            
            # Calculate success rate from recent history
            recent_metrics = self.metrics_history[-24:] if len(self.metrics_history) > 24 else self.metrics_history
            if recent_metrics:
                successful_runs = sum(1 for m in recent_metrics if m.error_count == 0)
                success_rate = (successful_runs / len(recent_metrics)) * 100
                total_errors = sum(m.error_count for m in recent_metrics)
            else:
                success_rate = 100.0
                total_errors = 0
            
            # Get last successful run
            last_successful = None
            for metric in reversed(self.metrics_history):
                if metric.error_count == 0:
                    last_successful = metric.timestamp
                    break
            
            metrics = ProductionMetrics(
                timestamp=datetime.now().isoformat(),
                processing_time_seconds=0.0,  # Will be updated during processing
                items_processed=0,             # Will be updated during processing
                success_rate=success_rate,
                error_count=total_errors,
                uptime_hours=uptime_hours,
                memory_usage_mb=memory_usage,
                disk_usage_gb=disk_free_gb,
                last_successful_run=last_successful
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            return ProductionMetrics(
                timestamp=datetime.now().isoformat(),
                processing_time_seconds=0.0,
                items_processed=0,
                success_rate=0.0,
                error_count=1,
                uptime_hours=0.0,
                memory_usage_mb=0.0,
                disk_usage_gb=0.0,
                last_error=str(e)
            )
    
    async def check_alert_conditions(self, metrics: ProductionMetrics) -> List[str]:
        """
        Check if any alert conditions are met
        
        Args:
            metrics: Current system metrics
            
        Returns:
            List of alert messages
        """
        alerts = []
        
        # Processing time alert
        if metrics.processing_time_seconds > self.thresholds['max_processing_time']:
            alerts.append(f"CRITICAL: Processing time exceeded threshold ({metrics.processing_time_seconds:.2f}s > {self.thresholds['max_processing_time']}s)")
        
        # Success rate alert
        if metrics.success_rate < self.thresholds['min_success_rate']:
            alerts.append(f"WARNING: Success rate below threshold ({metrics.success_rate:.1f}% < {self.thresholds['min_success_rate']}%)")
        
        # Error count alert
        if metrics.error_count > self.thresholds['max_error_count']:
            alerts.append(f"WARNING: High error count ({metrics.error_count} > {self.thresholds['max_error_count']})")
        
        # Disk space alert
        if metrics.disk_usage_gb < self.thresholds['min_disk_space_gb']:
            alerts.append(f"CRITICAL: Low disk space ({metrics.disk_usage_gb:.2f}GB < {self.thresholds['min_disk_space_gb']}GB)")
        
        # Memory usage alert
        if metrics.memory_usage_mb > self.thresholds['max_memory_usage_mb']:
            alerts.append(f"WARNING: High memory usage ({metrics.memory_usage_mb:.2f}MB > {self.thresholds['max_memory_usage_mb']}MB)")
        
        # Last successful run alert (no success in 48 hours)
        if metrics.last_successful_run:
            last_success = datetime.fromisoformat(metrics.last_successful_run)
            hours_since_success = (datetime.now() - last_success).total_seconds() / 3600
            if hours_since_success > 48:
                alerts.append(f"CRITICAL: No successful run in {hours_since_success:.1f} hours")
        
        return alerts
    
    async def send_alerts(self, alerts: List[str], metrics: ProductionMetrics):
        """
        Send alert notifications
        
        Args:
            alerts: List of alert messages
            metrics: Current system metrics
        """
        if not alerts or not self.alert_config.get('alert_recipients'):
            return
        
        try:
            # Create alert email
            msg = MIMEMultipart()
            msg['From'] = self.alert_config['username']
            msg['To'] = ', '.join(self.alert_config['alert_recipients'])
            msg['Subject'] = f"DABS EDI Production Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Email body
            body = f"""DABS EDI Production Alert
            
Timestamp: {metrics.timestamp}
System Status: {'CRITICAL' if any('CRITICAL' in alert for alert in alerts) else 'WARNING'}

ALERTS:
{chr(10).join(f'• {alert}' for alert in alerts)}

SYSTEM METRICS:
• Uptime: {metrics.uptime_hours:.2f} hours
• Success Rate: {metrics.success_rate:.1f}%
• Memory Usage: {metrics.memory_usage_mb:.2f} MB
• Disk Space: {metrics.disk_usage_gb:.2f} GB
• Last Successful Run: {metrics.last_successful_run or 'Never'}
• Error Count: {metrics.error_count}

BUSINESS IMPACT:
• Monthly DABS processing may be at risk
• Utah Package Agency compliance may be affected
• Time savings target (90% reduction) may not be achieved

ACTION REQUIRED:
Please investigate and resolve the issues immediately to maintain system reliability.

Hills & Hollows LLC - DABS Automation System
Utah Package Agency - Boulder, UT"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.alert_config['smtp_server'], self.alert_config['smtp_port'])
            if self.alert_config['use_tls']:
                server.starttls()
            server.login(self.alert_config['username'], self.alert_config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Alert sent to {len(self.alert_config['alert_recipients'])} recipients")
            
            # Log alert
            alert_log = {
                'timestamp': metrics.timestamp,
                'alerts': alerts,
                'metrics': asdict(metrics),
                'recipients': self.alert_config['alert_recipients']
            }
            
            alert_file = self.alerts_dir / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(alert_file, 'w', encoding='utf-8') as f:
                json.dump(alert_log, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to send alerts: {str(e)}")
    
    async def log_metrics(self, metrics: ProductionMetrics):
        """
        Log metrics to file for historical analysis
        
        Args:
            metrics: System metrics to log
        """
        # Add to history
        self.metrics_history.append(metrics)
        
        # Keep only last 168 hours (1 week) of metrics
        if len(self.metrics_history) > 168:
            self.metrics_history = self.metrics_history[-168:]
        
        # Log to daily file
        metrics_file = self.metrics_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(metrics_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(metrics)) + '\n')
        
        logger.info(f"Metrics logged: Success Rate={metrics.success_rate:.1f}%, Uptime={metrics.uptime_hours:.2f}h")

class DABSEDIProductionManager:
    """Production manager for DABS EDI system"""
    
    def __init__(self):
        """Initialize production manager"""
        # Load configuration
        self.config = self._load_production_config()
        
        # Initialize components
        self.integration = DABSEDIIntegration(self.config.get('smtp_config'))
        self.scheduler = DABSEDIScheduler(self.integration)
        self.monitor = DABSEDIProductionMonitor(self.config.get('alert_config'))
        
        # Production state
        self.is_running = False
        self.last_health_check = None
        
        logger.info("DABS EDI Production Manager initialized")
    
    def _load_production_config(self) -> Dict[str, Any]:
        """
        Load production configuration
        
        Returns:
            Production configuration
        """
        config_file = Path("config/dabs_edi_production.json")
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            # Default configuration
            config = {
                'smtp_config': {
                    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                    'username': os.getenv('SMTP_USERNAME'),
                    'password': os.getenv('SMTP_PASSWORD'),
                    'use_tls': True
                },
                'alert_config': {
                    'smtp_server': os.getenv('ALERT_SMTP_SERVER', 'smtp.gmail.com'),
                    'smtp_port': int(os.getenv('ALERT_SMTP_PORT', '587')),
                    'username': os.getenv('ALERT_SMTP_USERNAME'),
                    'password': os.getenv('ALERT_SMTP_PASSWORD'),
                    'alert_recipients': os.getenv('ALERT_RECIPIENTS', '').split(','),
                    'use_tls': True
                },
                'schedule': {
                    'monthly_day': 25,
                    'monthly_hour': 3,
                    'monthly_minute': 0,
                    'health_check_interval_minutes': 60
                }
            }
            
            # Save default configuration
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        
        return config
    
    async def start_production_system(self):
        """Start production system with monitoring"""
        logger.info("Starting DABS EDI Production System")
        self.is_running = True
        
        # Initial health check
        health = await self.integration.validate_system_health()
        if health['overall_status'] == 'FAILED':
            logger.error("System health check failed - cannot start production system")
            await self.monitor.send_alerts(
                ["CRITICAL: System health check failed - production system cannot start"],
                await self.monitor.collect_system_metrics()
            )
            return False
        
        # Schedule monitoring
        schedule.every(self.config['schedule']['health_check_interval_minutes']).minutes.do(
            lambda: asyncio.create_task(self._periodic_health_check())
        )
        
        # Schedule monthly processing (in production, this would be more sophisticated)
        schedule.every().day.at(f"{self.config['schedule']['monthly_hour']:02d}:{self.config['schedule']['monthly_minute']:02d}").do(
            lambda: asyncio.create_task(self._check_monthly_processing())
        )
        
        logger.info("DABS EDI Production System started successfully")
        return True
    
    async def _periodic_health_check(self):
        """Periodic health check and monitoring"""
        try:
            # Collect metrics
            metrics = await self.monitor.collect_system_metrics()
            
            # Check for alerts
            alerts = await self.monitor.check_alert_conditions(metrics)
            
            # Send alerts if necessary
            if alerts:
                await self.monitor.send_alerts(alerts, metrics)
            
            # Log metrics
            await self.monitor.log_metrics(metrics)
            
            self.last_health_check = datetime.now()
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
    
    async def _check_monthly_processing(self):
        """Check if monthly processing should run"""
        today = datetime.now()
        
        # Only run on the configured day of the month
        if today.day == self.config['schedule']['monthly_day']:
            # Look for DABS Excel file
            dabs_files = list(Path("data").glob("DABS_*.xlsx"))
            
            if dabs_files:
                # Process the most recent file
                latest_file = max(dabs_files, key=lambda f: f.stat().st_mtime)
                logger.info(f"Starting scheduled monthly processing: {latest_file}")
                
                start_time = datetime.now()
                result = await self.integration.process_monthly_dabs_update(str(latest_file))
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Update metrics
                metrics = await self.monitor.collect_system_metrics()
                metrics.processing_time_seconds = processing_time
                metrics.items_processed = result.get('data_statistics', {}).get('total_items', 0)
                
                if not result['success']:
                    metrics.error_count += 1
                    metrics.last_error = result.get('error', 'Unknown error')
                    
                    # Send failure alert
                    await self.monitor.send_alerts(
                        [f"CRITICAL: Monthly DABS processing failed - {result.get('error')}"],
                        metrics
                    )
                else:
                    # Log success
                    logger.info(f"Monthly DABS processing completed successfully in {processing_time:.2f} seconds")
                
                await self.monitor.log_metrics(metrics)
            else:
                logger.warning("No DABS Excel files found for monthly processing")
    
    async def run_production_loop(self):
        """Main production loop"""
        logger.info("Starting production monitoring loop")
        
        while self.is_running:
            try:
                # Run scheduled tasks
                schedule.run_pending()
                
                # Sleep for 1 minute
                await asyncio.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"Production loop error: {str(e)}")
                await asyncio.sleep(60)  # Continue after error
        
        logger.info("Production system stopped")
    
    async def shutdown_production_system(self):
        """Graceful shutdown of production system"""
        logger.info("Shutting down DABS EDI Production System")
        self.is_running = False
        
        # Final metrics collection
        final_metrics = await self.monitor.collect_system_metrics()
        await self.monitor.log_metrics(final_metrics)
        
        logger.info("DABS EDI Production System shutdown complete")

# Production deployment script
async def deploy_production():
    """Deploy DABS EDI system to production"""
    print("=" * 60)
    print("DABS EDI Production Deployment")
    print("=" * 60)
    print(f"Deployment Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Initialize production manager
        manager = DABSEDIProductionManager()
        
        # Start production system
        success = await manager.start_production_system()
        
        if success:
            print("✅ Production system started successfully")
            print("🔄 Starting monitoring loop...")
            
            # Run production loop
            await manager.run_production_loop()
        else:
            print("❌ Failed to start production system")
            return False
            
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
        if 'manager' in locals():
            await manager.shutdown_production_system()
    except Exception as e:
        print(f"❌ Production deployment failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    # Run production deployment
    asyncio.run(deploy_production())
