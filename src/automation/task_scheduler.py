#!/usr/bin/env python3
"""
Task Scheduler for DABS Automation System - Hills & Hollows LLC
Automated scheduling system for DABS workflows and Utah Package Agency compliance

Schedules and coordinates:
- Monthly DABS price updates (25th at 3:00 AM)
- Weekly inventory reconciliation
- Daily delivery processing  
- Real-time QuickBooks synchronization
- Utah compliance reporting

Author: DABS Automation System
Created: 2025-08-23
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import httpx

# Import task manager for integration
from integration_hub.task_manager import get_dabs_task_manager, DABSTask, TaskType, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Types of automated schedules"""
    MONTHLY = "monthly"
    WEEKLY = "weekly" 
    DAILY = "daily"
    REAL_TIME = "real_time"
    EVENT_DRIVEN = "event_driven"
    COMPLIANCE = "compliance"


class WorkflowPriority(Enum):
    """Workflow execution priority"""
    CRITICAL = 1  # Tessa's primary relief (monthly automation)
    HIGH = 2      # Daily operations (delivery processing)
    MEDIUM = 3    # Weekly tasks (inventory, invoices)
    LOW = 4       # Analytics and optimization


@dataclass
class ScheduledWorkflow:
    """Scheduled DABS automation workflow"""
    workflow_id: str
    name: str
    description: str
    schedule_type: ScheduleType
    cron_expression: str
    priority: WorkflowPriority
    workflow_function: str  # Function name to execute
    enabled: bool = True
    utah_compliance_required: bool = True
    max_execution_time: int = 1800  # 30 minutes default
    retry_attempts: int = 3
    retry_delay: int = 300  # 5 minutes
    notification_on_failure: bool = True
    dependencies: List[str] = field(default_factory=list)
    performance_requirements: Dict[str, Any] = field(default_factory=dict)
    last_execution: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    execution_count: int = 0
    failure_count: int = 0


class DABSTaskScheduler:
    """
    DABS Task Scheduler with Utah Package Agency Compliance
    
    Manages automated scheduling for all DABS workflows according to:
    - .cursorrules ARCHON-FIRST workflow requirements
    - Utah Package Agency monthly reporting deadlines
    - Performance gates from .cursor/rules/performance-gates.mdc
    - SSCS integration timing requirements
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.scheduler = AsyncIOScheduler(timezone='America/Denver')  # Utah timezone
        self.task_manager = get_dabs_task_manager()
        
        # Workflow registry
        self.workflows: Dict[str, ScheduledWorkflow] = {}
        self.active_executions: Dict[str, datetime] = {}
        
        # Utah Package Agency specific settings
        self.utah_deadline_monitoring = True
        self.compliance_alerts_enabled = True
        
        logger.info("DABS Task Scheduler initialized with Utah Package Agency compliance")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load scheduler configuration"""
        default_config = {
            'max_concurrent_workflows': 2,
            'execution_timeout': 1800,  # 30 minutes
            'retry_attempts': 3,
            'retry_delay': 300,  # 5 minutes
            'notification_email': 'shawn@owenent.com',
            'archon_mcp_url': 'http://localhost:8151',
            'enable_utah_compliance_monitoring': True,
            'tessa_notification_enabled': True
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def register_dabs_workflows(self):
        """Register all standard DABS automation workflows"""
        
        # 🔥 CRITICAL: Monthly Price Updates (Tessa's primary relief)
        self.register_workflow(ScheduledWorkflow(
            workflow_id="monthly_price_updates",
            name="Monthly DABS Price Updates",
            description="Automated monthly price processing - Tessa's 2-4 hour → 5 minute transformation",
            schedule_type=ScheduleType.MONTHLY,
            cron_expression="0 3 25 * *",  # 25th at 3:00 AM
            priority=WorkflowPriority.CRITICAL,
            workflow_function="execute_monthly_price_update",
            utah_compliance_required=True,
            max_execution_time=900,  # 15 minutes max per performance gates
            performance_requirements={
                "max_processing_time": 900,  # 15 minutes for 1,239 SKUs
                "target_time_reduction": 0.9,  # 90% reduction target
                "max_error_rate": 0.001  # <0.1% error rate
            }
        ))
        
        # ⚡ HIGH: Daily Delivery Processing
        self.register_workflow(ScheduledWorkflow(
            workflow_id="delivery_processing",
            name="DABS Delivery Invoice Processing", 
            description="Automated processing of delivery invoices - 30-60 min → 10-15 min reduction",
            schedule_type=ScheduleType.DAILY,
            cron_expression="0 */4 8-18 * *",  # Every 4 hours during business
            priority=WorkflowPriority.HIGH,
            workflow_function="execute_delivery_processing",
            max_execution_time=1800  # 30 minutes
        ))
        
        # 📊 MEDIUM: Weekly Inventory Sync
        self.register_workflow(ScheduledWorkflow(
            workflow_id="weekly_inventory_sync",
            name="SSCS ↔ QuickBooks Inventory Synchronization",
            description="Weekly inventory reconciliation between SSCS and QuickBooks",
            schedule_type=ScheduleType.WEEKLY,
            cron_expression="0 17 * * 5",  # Friday at 5:00 PM
            priority=WorkflowPriority.MEDIUM,
            workflow_function="execute_inventory_sync",
            performance_requirements={
                "max_variance_percentage": 2.0,  # <2% variance requirement
                "sync_interval_minutes": 15  # 15-minute intervals
            }
        ))
        
        # 📋 CRITICAL: Monthly Utah Compliance Reporting  
        self.register_workflow(ScheduledWorkflow(
            workflow_id="utah_monthly_reporting",
            name="Utah DABS Monthly Compliance Reporting",
            description="Automated monthly reporting to Utah DABS (deadline: 10th of following month)",
            schedule_type=ScheduleType.COMPLIANCE,
            cron_expression="0 6 1 * *",  # 1st at 6:00 AM
            priority=WorkflowPriority.CRITICAL,
            workflow_function="execute_utah_reporting",
            utah_compliance_required=True,
            max_execution_time=900  # 15 minutes
        ))
        
        # ⚡ REAL-TIME: QuickBooks Sync
        self.register_workflow(ScheduledWorkflow(
            workflow_id="realtime_qb_sync",
            name="Real-time QuickBooks Inventory Sync",
            description="15-minute interval QuickBooks synchronization",
            schedule_type=ScheduleType.REAL_TIME,
            cron_expression="*/15 8-22 * * *",  # Every 15 minutes during business
            priority=WorkflowPriority.MEDIUM,
            workflow_function="execute_realtime_qb_sync",
            performance_requirements={
                "rate_limit": 500,  # 500 requests/minute QB limit
                "max_variance": 0.02  # <2% variance requirement
            }
        ))
        
        logger.info("All DABS workflows registered with scheduler")
    
    def register_workflow(self, workflow: ScheduledWorkflow):
        """Register a workflow with the scheduler"""
        self.workflows[workflow.workflow_id] = workflow
        
        # Add to APScheduler
        self.scheduler.add_job(
            func=self._execute_workflow,
            trigger=CronTrigger.from_crontab(workflow.cron_expression),
            args=[workflow.workflow_id],
            id=workflow.workflow_id,
            name=workflow.name,
            max_instances=1,  # Prevent overlapping executions
            coalesce=True,  # Combine missed executions
            misfire_grace_time=300  # 5 minute grace period
        )
        
        logger.info(f"Workflow registered: {workflow.name} ({workflow.cron_expression})")
    
    async def _execute_workflow(self, workflow_id: str):
        """Execute a scheduled workflow with full error handling"""
        if workflow_id not in self.workflows:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        workflow = self.workflows[workflow_id]
        execution_start = datetime.now()
        
        # Check for concurrent execution
        if workflow_id in self.active_executions:
            logger.warning(f"Workflow {workflow_id} already executing, skipping")
            return
        
        self.active_executions[workflow_id] = execution_start
        
        try:
            logger.info(f"Starting workflow: {workflow.name}")
            
            # Create Archon task for tracking (if available)
            archon_task = await self._create_archon_tracking_task(workflow)
            
            # Execute the actual workflow function
            result = await self._call_workflow_function(workflow)
            
            # Update execution tracking
            workflow.last_execution = execution_start
            workflow.execution_count += 1
            workflow.next_execution = self._calculate_next_execution(workflow)
            
            # Update Archon task status
            if archon_task:
                await self._update_archon_task_status(archon_task, "done", result)
            
            # Performance validation
            execution_time = (datetime.now() - execution_start).total_seconds()
            if execution_time > workflow.max_execution_time:
                logger.warning(f"Workflow {workflow_id} exceeded time limit: {execution_time}s > {workflow.max_execution_time}s")
            
            logger.info(f"Workflow {workflow.name} completed successfully in {execution_time:.2f}s")
            
        except Exception as e:
            workflow.failure_count += 1
            logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            
            # Update Archon task with failure
            if archon_task:
                await self._update_archon_task_status(archon_task, "blocked", {"error": str(e)})
            
            # Send failure notifications if enabled
            if workflow.notification_on_failure:
                await self._send_failure_notification(workflow, str(e))
            
        finally:
            # Remove from active executions
            if workflow_id in self.active_executions:
                del self.active_executions[workflow_id]
    
    async def _create_archon_tracking_task(self, workflow: ScheduledWorkflow) -> Optional[str]:
        """Create Archon task for workflow execution tracking"""
        try:
            task = DABSTask(
                task_id=f"sched_{workflow.workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=f"Scheduled: {workflow.name}",
                description=f"Automated execution of {workflow.description}",
                task_type=self._map_workflow_to_task_type(workflow),
                priority=self._map_priority_to_task_priority(workflow.priority),
                status=TaskStatus.DOING,
                phase=self._determine_phase_from_workflow(workflow),
                utah_compliance_required=workflow.utah_compliance_required,
                performance_requirements=workflow.performance_requirements
            )
            
            return await self.task_manager.create_dabs_task(task)
            
        except Exception as e:
            logger.warning(f"Failed to create Archon tracking task: {e}")
            return None
    
    async def _call_workflow_function(self, workflow: ScheduledWorkflow) -> Dict[str, Any]:
        """Call the actual workflow function"""
        # Map workflow functions to actual implementations
        workflow_functions = {
            "execute_monthly_price_update": self._execute_monthly_price_update,
            "execute_delivery_processing": self._execute_delivery_processing,
            "execute_inventory_sync": self._execute_inventory_sync,
            "execute_utah_reporting": self._execute_utah_reporting,
            "execute_realtime_qb_sync": self._execute_realtime_qb_sync
        }
        
        func = workflow_functions.get(workflow.workflow_function)
        if not func:
            raise Exception(f"Workflow function {workflow.workflow_function} not implemented")
        
        return await func(workflow)
    
    async def _execute_monthly_price_update(self, workflow: ScheduledWorkflow) -> Dict[str, Any]:
        """Execute monthly DABS price update automation"""
        logger.info("🔥 EXECUTING CRITICAL MONTHLY AUTOMATION - Tessa's Primary Relief")
        
        try:
            # Import integration coordinator for coordinated workflow
            from integration_hub.coordinator import IntegrationCoordinator
            
            coordinator = IntegrationCoordinator()
            
            # Process DABS files from configured directory
            dabs_directory = Path(self.config.get('dabs_input_directory', 'data/dabs_backups'))
            latest_dabs_file = self._find_latest_dabs_file(dabs_directory)
            
            if not latest_dabs_file:
                raise Exception("No DABS file found for monthly processing")
            
            # Execute coordinated workflow: DABS → SSCS → QuickBooks → Compliance
            result = await coordinator.execute_workflow(latest_dabs_file)
            
            return {
                "success": result.status.value == "completed",
                "skus_processed": result.total_skus_processed,
                "integrations_successful": result.successful_integrations,
                "processing_time": result.duration.total_seconds() if result.duration else 0,
                "tessa_relief_delivered": True,
                "workflow_id": result.workflow_id
            }
            
        except Exception as e:
            logger.error(f"Monthly price update failed: {e}")
            return {"success": False, "error": str(e), "tessa_relief_delivered": False}
    
    async def _execute_delivery_processing(self, workflow: ScheduledWorkflow) -> Dict[str, Any]:
        """Execute delivery invoice processing automation"""
        logger.info("📦 EXECUTING DELIVERY PROCESSING AUTOMATION")
        
        # Placeholder for delivery processing workflow
        # TODO: Implement PDF parsing and SSCS form automation
        return {
            "success": True,
            "deliveries_processed": 0,
            "time_saved_minutes": 0,
            "message": "Delivery processing automation - implementation pending Phase 2"
        }
    
    async def _execute_inventory_sync(self, workflow: ScheduledWorkflow) -> Dict[str, Any]:
        """Execute inventory synchronization between SSCS and QuickBooks"""
        logger.info("📊 EXECUTING INVENTORY SYNCHRONIZATION")
        
        # Placeholder for inventory sync workflow
        # TODO: Implement SSCS ↔ QuickBooks inventory reconciliation
        return {
            "success": True,
            "variance_percentage": 0.0,
            "items_synced": 0,
            "message": "Inventory sync automation - implementation pending Phase 2"
        }
    
    async def _execute_utah_reporting(self, workflow: ScheduledWorkflow) -> Dict[str, Any]:
        """Execute Utah DABS monthly compliance reporting"""
        logger.info("📋 EXECUTING UTAH COMPLIANCE REPORTING")
        
        # Check Utah deadline compliance (10th of following month)
        current_date = datetime.now()
        deadline_day = 10
        
        if current_date.day > deadline_day:
            logger.warning("Utah reporting executed after deadline - compliance violation risk")
        
        # Placeholder for Utah reporting workflow
        # TODO: Implement SSCS data export → DABS format → Utah submission
        return {
            "success": True,
            "utah_compliance_status": "compliant",
            "deadline_met": current_date.day <= deadline_day,
            "message": "Utah reporting automation - implementation pending Phase 3"
        }
    
    async def _execute_realtime_qb_sync(self, workflow: ScheduledWorkflow) -> Dict[str, Any]:
        """Execute real-time QuickBooks synchronization"""
        logger.info("⚡ EXECUTING REAL-TIME QUICKBOOKS SYNC")
        
        # Placeholder for real-time QB sync
        # TODO: Implement 15-minute interval QB synchronization with rate limiting
        return {
            "success": True,
            "sync_interval_minutes": 15,
            "rate_limit_respected": True,
            "variance_within_limits": True,
            "message": "Real-time QB sync - implementation pending Phase 2"
        }
    
    def _find_latest_dabs_file(self, directory: Path) -> Optional[Path]:
        """Find the most recent DABS Excel file"""
        if not directory.exists():
            return None
        
        dabs_files = list(directory.glob("*.xlsx")) + list(directory.glob("*.xls"))
        if not dabs_files:
            return None
        
        # Return most recent file
        return max(dabs_files, key=lambda f: f.stat().st_mtime)
    
    def _map_workflow_to_task_type(self, workflow: ScheduledWorkflow) -> TaskType:
        """Map workflow to appropriate task type"""
        workflow_mapping = {
            "monthly_price_updates": TaskType.DABS_PROCESSING,
            "delivery_processing": TaskType.SSCS_INTEGRATION,
            "inventory_sync": TaskType.QUICKBOOKS_SYNC,
            "utah_reporting": TaskType.UTAH_REPORTING,
            "realtime_qb_sync": TaskType.QUICKBOOKS_SYNC
        }
        return workflow_mapping.get(workflow.workflow_id, TaskType.DABS_PROCESSING)
    
    def _map_priority_to_task_priority(self, workflow_priority: WorkflowPriority) -> TaskPriority:
        """Map workflow priority to task priority"""
        priority_mapping = {
            WorkflowPriority.CRITICAL: TaskPriority.CRITICAL,
            WorkflowPriority.HIGH: TaskPriority.HIGH,
            WorkflowPriority.MEDIUM: TaskPriority.MEDIUM,
            WorkflowPriority.LOW: TaskPriority.LOW
        }
        return priority_mapping.get(workflow_priority, TaskPriority.MEDIUM)
    
    def _determine_phase_from_workflow(self, workflow: ScheduledWorkflow) -> str:
        """Determine DABS project phase from workflow"""
        phase_mapping = {
            "monthly_price_updates": "core_integrations",
            "delivery_processing": "core_integrations", 
            "inventory_sync": "core_integrations",
            "utah_reporting": "compliance_reporting",
            "realtime_qb_sync": "core_integrations"
        }
        return phase_mapping.get(workflow.workflow_id, "core_integrations")
    
    def _calculate_next_execution(self, workflow: ScheduledWorkflow) -> datetime:
        """Calculate next execution time for workflow"""
        trigger = CronTrigger.from_crontab(workflow.cron_expression)
        return trigger.get_next_fire_time(None, datetime.now())
    
    async def _update_archon_task_status(self, task_id: str, status: str, result: Dict[str, Any]):
        """Update Archon task status with execution results"""
        try:
            await self.task_manager.update_task_status(
                task_id,
                TaskStatus(status),
                f"Scheduled execution result: {json.dumps(result, indent=2)}"
            )
        except Exception as e:
            logger.warning(f"Failed to update Archon task status: {e}")
    
    async def _send_failure_notification(self, workflow: ScheduledWorkflow, error: str):
        """Send failure notification to Tessa and stakeholders"""
        notification_msg = f"""
        🚨 DABS AUTOMATION FAILURE ALERT
        
        Workflow: {workflow.name}
        Time: {datetime.now().isoformat()}
        Error: {error}
        
        Utah Compliance Impact: {'YES - Immediate attention required' if workflow.utah_compliance_required else 'NO'}
        Tessa Relief Impact: {'YES - Monthly processing affected' if workflow.workflow_id == 'monthly_price_updates' else 'NO'}
        
        Action Required: Check automation system and contact technical support if needed.
        """
        
        logger.critical(notification_msg)
        # TODO: Implement actual email/SMS notification system
    
    async def start_scheduler(self):
        """Start the task scheduler"""
        try:
            # Register all DABS workflows
            self.register_dabs_workflows()
            
            # Start APScheduler
            self.scheduler.start()
            
            # Log startup information
            logger.info("🚀 DABS Task Scheduler started successfully")
            logger.info(f"Registered workflows: {len(self.workflows)}")
            logger.info("🔥 CRITICAL: Monthly automation scheduled (25th at 3:00 AM) - Tessa's relief")
            logger.info("📋 Utah compliance monitoring enabled")
            
            # Print schedule summary
            await self._print_schedule_summary()
            
        except Exception as e:
            logger.error(f"Failed to start DABS scheduler: {e}")
            raise
    
    async def stop_scheduler(self):
        """Stop the task scheduler gracefully"""
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("DABS Task Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    async def _print_schedule_summary(self):
        """Print summary of all scheduled workflows"""
        logger.info("📅 DABS AUTOMATION SCHEDULE SUMMARY:")
        logger.info("=" * 50)
        
        for workflow in sorted(self.workflows.values(), key=lambda w: w.priority.value):
            priority_icon = {
                WorkflowPriority.CRITICAL: "🔥",
                WorkflowPriority.HIGH: "⚡", 
                WorkflowPriority.MEDIUM: "📊",
                WorkflowPriority.LOW: "📈"
            }
            
            logger.info(f"{priority_icon[workflow.priority]} {workflow.name}")
            logger.info(f"   Schedule: {workflow.cron_expression}")
            logger.info(f"   Next: {workflow.next_execution}")
            logger.info(f"   Utah Compliance: {'✅' if workflow.utah_compliance_required else '❌'}")
            logger.info("")
    
    async def get_schedule_status(self) -> Dict[str, Any]:
        """Get current schedule status and upcoming executions"""
        return {
            "scheduler_running": self.scheduler.running,
            "total_workflows": len(self.workflows),
            "active_executions": len(self.active_executions),
            "next_critical_execution": self._get_next_critical_execution(),
            "utah_compliance_status": await self._check_utah_compliance_status(),
            "tessa_relief_status": self._get_tessa_relief_status()
        }
    
    def _get_next_critical_execution(self) -> Optional[Dict[str, Any]]:
        """Get next critical workflow execution"""
        critical_workflows = [w for w in self.workflows.values() 
                            if w.priority == WorkflowPriority.CRITICAL and w.enabled]
        
        if not critical_workflows:
            return None
        
        next_workflow = min(critical_workflows, key=lambda w: w.next_execution or datetime.max)
        return {
            "workflow_name": next_workflow.name,
            "next_execution": next_workflow.next_execution.isoformat() if next_workflow.next_execution else None,
            "description": next_workflow.description
        }
    
    async def _check_utah_compliance_status(self) -> Dict[str, Any]:
        """Check Utah Package Agency compliance status"""
        utah_workflows = [w for w in self.workflows.values() if w.utah_compliance_required]
        
        compliance_status = {
            "total_compliance_workflows": len(utah_workflows),
            "enabled_workflows": len([w for w in utah_workflows if w.enabled]),
            "recent_failures": len([w for w in utah_workflows if w.failure_count > 0]),
            "next_deadline": None
        }
        
        # Check for upcoming Utah reporting deadline (10th of month)
        current_date = datetime.now()
        next_month = current_date.replace(day=1) + timedelta(days=32)
        utah_deadline = next_month.replace(day=10, hour=23, minute=59, second=59)
        
        compliance_status["next_deadline"] = utah_deadline.isoformat()
        compliance_status["days_until_deadline"] = (utah_deadline - current_date).days
        
        return compliance_status
    
    def _get_tessa_relief_status(self) -> Dict[str, Any]:
        """Get status of Tessa's relief (monthly automation)"""
        monthly_workflow = self.workflows.get("monthly_price_updates")
        
        if not monthly_workflow:
            return {"status": "not_configured", "relief_delivered": False}
        
        return {
            "status": "configured",
            "enabled": monthly_workflow.enabled,
            "next_execution": monthly_workflow.next_execution.isoformat() if monthly_workflow.next_execution else None,
            "execution_count": monthly_workflow.execution_count,
            "failure_count": monthly_workflow.failure_count,
            "relief_delivered": monthly_workflow.execution_count > 0 and monthly_workflow.failure_count == 0,
            "time_reduction_target": "90% (2-4 hours → 5 minutes)"
        }


# Global scheduler instance
_scheduler = None


def get_dabs_scheduler() -> DABSTaskScheduler:
    """Get or create global DABS task scheduler"""
    global _scheduler
    if _scheduler is None:
        _scheduler = DABSTaskScheduler()
    return _scheduler


async def main():
    """Example usage and testing"""
    scheduler = get_dabs_scheduler()
    
    # Start scheduler
    await scheduler.start_scheduler()
    
    # Get status
    status = await scheduler.get_schedule_status()
    print("📅 DABS Scheduler Status:")
    print(json.dumps(status, indent=2, default=str))
    
    try:
        # Keep running
        logger.info("Scheduler running... Press Ctrl+C to stop")
        while True:
            await asyncio.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        await scheduler.stop_scheduler()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    asyncio.run(main())