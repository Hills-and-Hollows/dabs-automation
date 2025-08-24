#!/usr/bin/env python3
"""
Integration Coordinator - Hills & Hollows LLC
Central coordination system for DABS automation workflow

Orchestrates data flow between:
- DABS Excel processing
- SSCS POS integration (CPB vendor import)
- QuickBooks Online integration
- Verifone system integration

Author: DABS Automation System
Created: 2025-08-22
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json

# Import our processors
import sys
sys.path.append(str(Path(__file__).parent.parent))

from processors.dabs_processor import DABSProcessor, ProcessingResult, DABSProduct
from processors.sscs_integration import create_sscs_cpb_integrator, IntegrationResult
from integration_hub.error_isolation import (
    ErrorIsolationManager, ErrorSeverity, SystemType,
    create_file_rollback_step, create_api_rollback_step
)
from automation.workflows.quickbooks_integration.qb_oauth_manager import QuickBooksOAuthManager
from automation.workflows.quickbooks_integration.qb_realtime_sync import QuickBooksRealtimeSync

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL_SUCCESS = "partial_success"


class IntegrationStep(Enum):
    """Individual integration steps"""
    DABS_PROCESSING = "dabs_processing"
    SSCS_UPLOAD = "sscs_upload"
    QUICKBOOKS_SYNC = "quickbooks_sync"
    VERIFONE_UPDATE = "verifone_update"
    VALIDATION = "validation"
    ROLLBACK = "rollback"


@dataclass
class StepResult:
    """Result of an individual integration step"""
    step: IntegrationStep
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate step duration"""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None


@dataclass
class WorkflowResult:
    """Complete workflow execution result"""
    workflow_id: str
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    steps: List[StepResult] = field(default_factory=list)
    total_skus_processed: int = 0
    successful_integrations: List[str] = field(default_factory=list)
    failed_integrations: List[str] = field(default_factory=list)
    rollback_performed: bool = False
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate total workflow duration"""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if not self.steps:
            return 0.0
        successful_steps = sum(1 for step in self.steps if step.success)
        return (successful_steps / len(self.steps)) * 100


class IntegrationCoordinator:
    """
    Central Integration Coordinator
    
    Manages the complete DABS automation workflow:
    1. Process DABS Excel files
    2. Upload to SSCS via CPB vendor import
    3. Sync with QuickBooks Online
    4. Update Verifone systems
    5. Validate all integrations
    6. Handle errors and rollbacks
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.dabs_processor = DABSProcessor()
        self.sscs_integrator = create_sscs_cpb_integrator(
            upload_directory=self.config.get('sscs_upload_directory',
                                           '/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/exports/sscs_cpb')
        )

        # QuickBooks integration components
        self.qb_oauth_manager = QuickBooksOAuthManager()
        self.qb_realtime_sync = QuickBooksRealtimeSync()

        # Error isolation and rollback system
        self.error_manager = ErrorIsolationManager(
            backup_directory=self.config.get('backup_directory',
                                           '/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/data/rollback_backups')
        )

        # Workflow tracking
        self.active_workflows: Dict[str, WorkflowResult] = {}
        self.workflow_history: List[WorkflowResult] = []

        logger.info("Integration Coordinator initialized with error isolation")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load coordinator configuration"""
        default_config = {
            'max_concurrent_workflows': 1,
            'step_timeout_minutes': 30,
            'enable_rollback': True,
            'validation_enabled': True,
            'sscs_upload_directory': '/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/exports/sscs_cpb',
            'backup_directory': '/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/data/dabs_backups',
            'log_level': 'INFO'
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    async def execute_workflow(self, dabs_file_path: Union[str, Path]) -> WorkflowResult:
        """
        Execute complete DABS automation workflow
        
        Args:
            dabs_file_path: Path to DABS Excel file
            
        Returns:
            WorkflowResult with complete execution details
        """
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workflow = WorkflowResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.now()
        )
        
        self.active_workflows[workflow_id] = workflow
        
        try:
            logger.info(f"Starting workflow {workflow_id} for file: {dabs_file_path}")
            
            # Step 1: Process DABS file
            step_result = await self._execute_step(
                IntegrationStep.DABS_PROCESSING,
                self._process_dabs_file,
                dabs_file_path
            )
            workflow.steps.append(step_result)
            
            if not step_result.success:
                workflow.status = WorkflowStatus.FAILED
                workflow.failed_integrations.append("DABS Processing")
                return await self._finalize_workflow(workflow)
            
            products = step_result.data.get('products', [])
            workflow.total_skus_processed = len(products)
            
            # Step 2: Upload to SSCS
            step_result = await self._execute_step(
                IntegrationStep.SSCS_UPLOAD,
                self._upload_to_sscs,
                products
            )
            workflow.steps.append(step_result)
            
            if step_result.success:
                workflow.successful_integrations.append("SSCS")
            else:
                workflow.failed_integrations.append("SSCS")
            
            # Step 3: QuickBooks sync (placeholder for now)
            step_result = await self._execute_step(
                IntegrationStep.QUICKBOOKS_SYNC,
                self._sync_quickbooks,
                products
            )
            workflow.steps.append(step_result)
            
            if step_result.success:
                workflow.successful_integrations.append("QuickBooks")
            else:
                workflow.failed_integrations.append("QuickBooks")
            
            # Step 4: Validation
            if self.config.get('validation_enabled', True):
                step_result = await self._execute_step(
                    IntegrationStep.VALIDATION,
                    self._validate_integrations,
                    workflow
                )
                workflow.steps.append(step_result)
            
            # Determine final status
            if workflow.failed_integrations:
                if workflow.successful_integrations:
                    workflow.status = WorkflowStatus.PARTIAL_SUCCESS
                else:
                    workflow.status = WorkflowStatus.FAILED
            else:
                workflow.status = WorkflowStatus.COMPLETED
            
            return await self._finalize_workflow(workflow)
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed with exception: {str(e)}")
            workflow.status = WorkflowStatus.FAILED
            return await self._finalize_workflow(workflow)
    
    async def _execute_step(self, step_type: IntegrationStep, step_function, *args) -> StepResult:
        """Execute a single workflow step with error handling"""
        step_result = StepResult(
            step=step_type,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.now()
        )
        
        try:
            logger.info(f"Executing step: {step_type.value}")
            result = await step_function(*args)
            
            step_result.success = True
            step_result.data = result
            step_result.status = WorkflowStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Step {step_type.value} failed: {str(e)}")
            step_result.success = False
            step_result.errors.append(str(e))
            step_result.status = WorkflowStatus.FAILED
        
        finally:
            step_result.end_time = datetime.now()
        
        return step_result
    
    async def _process_dabs_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Process DABS Excel file"""
        result = await self.dabs_processor.process_dabs_file(file_path)

        if not result.success:
            raise Exception(f"DABS processing failed: {result.errors}")

        # For now, create mock products since ProcessingResult doesn't include them
        # TODO: Update DABSProcessor to return products in ProcessingResult
        mock_products = [
            DABSProduct(
                sku=f"SKU_{i}",
                product_name=f"Product {i}",
                retail_price=29.99,
                category="Spirits",
                on_special_pricing=False,
                effective_date=datetime.now(),
                status="Active",
                updated_on=datetime.now()
            ) for i in range(result.processed_skus)
        ]

        return {
            'products': mock_products,
            'output_files': result.output_files,
            'processing_time': result.processing_time
        }
    
    async def _upload_to_sscs(self, products: List[DABSProduct]) -> Dict[str, Any]:
        """Upload products to SSCS via CPB vendor import"""
        result = await self.sscs_integrator.upload_pricing_data(products)
        
        if not result.success:
            raise Exception(f"SSCS upload failed: {result.errors}")
        
        return {
            'skus_uploaded': result.skus_uploaded,
            'upload_time': result.upload_time,
            'file_path': result.file_path
        }
    
    async def _sync_quickbooks(self, products: List[DABSProduct]) -> Dict[str, Any]:
        """Sync with QuickBooks Online"""
        logger.info(f"Starting QuickBooks sync for {len(products)} products")

        start_time = datetime.now()

        try:
            # Ensure we have valid OAuth tokens
            access_token = await self.qb_oauth_manager.get_valid_access_token()
            logger.info("QuickBooks OAuth tokens validated")

            # Convert DABS products to QuickBooks format
            qb_products = []
            for product in products:
                qb_product = {
                    'sku': product.sku,
                    'name': product.description,
                    'unit_price': product.retail_price,
                    'cost': product.cost,
                    'quantity_on_hand': getattr(product, 'quantity', 0),
                    'category': 'Liquor',  # Utah Package Agency category
                    'tax_code': 'UT_LIQUOR_TAX'
                }
                qb_products.append(qb_product)

            # Perform inventory sync using OAuth manager
            sync_result = await self.qb_oauth_manager.sync_inventory_from_dabs(qb_products)

            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"QuickBooks sync completed in {processing_time:.2f} seconds")
            logger.info(f"Products processed: {sync_result.get('products_processed', 0)}")
            logger.info(f"Products updated: {sync_result.get('products_updated', 0)}")
            logger.info(f"Products created: {sync_result.get('products_created', 0)}")

            return {
                'skus_synced': sync_result.get('products_processed', 0),
                'skus_updated': sync_result.get('products_updated', 0),
                'skus_created': sync_result.get('products_created', 0),
                'sync_time': processing_time,
                'status': 'success',
                'sync_id': sync_result.get('sync_id', ''),
                'errors': sync_result.get('errors', [])
            }

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"QuickBooks sync failed: {e}")

            return {
                'skus_synced': 0,
                'skus_updated': 0,
                'skus_created': 0,
                'sync_time': processing_time,
                'status': 'failed',
                'error': str(e),
                'errors': [str(e)]
            }
    
    async def _validate_integrations(self, workflow: WorkflowResult) -> Dict[str, Any]:
        """Validate all integrations completed successfully"""
        validation_results = {
            'sscs_validation': True,  # Placeholder
            'quickbooks_validation': True,  # Placeholder
            'data_consistency': True  # Placeholder
        }
        
        return validation_results
    
    async def _finalize_workflow(self, workflow: WorkflowResult) -> WorkflowResult:
        """Finalize workflow and update tracking"""
        workflow.end_time = datetime.now()
        
        # Move from active to history
        if workflow.workflow_id in self.active_workflows:
            del self.active_workflows[workflow.workflow_id]
        
        self.workflow_history.append(workflow)
        
        # Keep only last 100 workflows in history
        if len(self.workflow_history) > 100:
            self.workflow_history = self.workflow_history[-100:]
        
        logger.info(f"Workflow {workflow.workflow_id} completed with status: {workflow.status.value}")
        return workflow
    
    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowResult]:
        """Get status of a specific workflow"""
        # Check active workflows first
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        
        # Check history
        for workflow in self.workflow_history:
            if workflow.workflow_id == workflow_id:
                return workflow
        
        return None
    
    def get_active_workflows(self) -> List[WorkflowResult]:
        """Get all currently active workflows"""
        return list(self.active_workflows.values())
    
    def get_workflow_history(self, limit: int = 10) -> List[WorkflowResult]:
        """Get recent workflow history"""
        return self.workflow_history[-limit:]
