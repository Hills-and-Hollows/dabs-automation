#!/usr/bin/env python3
"""
Workflow Orchestration Engine - Hills & Hollows LLC
Advanced workflow engine for coordinating DABS automation operations

Provides:
- Sequential and parallel workflow execution
- Conditional workflow branching
- Retry mechanisms with exponential backoff
- Workflow templates and reusable patterns
- Real-time progress monitoring
- Dependency management between steps

Author: DABS Automation System
Created: 2025-08-22
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import json
import time

logger = logging.getLogger(__name__)


class WorkflowStepType(Enum):
    """Types of workflow steps"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    RETRY = "retry"
    VALIDATION = "validation"
    NOTIFICATION = "notification"


class StepStatus(Enum):
    """Status of individual workflow steps"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class WorkflowPriority(Enum):
    """Workflow execution priority"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class WorkflowCondition:
    """Condition for conditional workflow steps"""
    condition_type: str  # 'success', 'failure', 'custom'
    target_step: Optional[str] = None
    custom_function: Optional[Callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    retry_on_exceptions: List[type] = field(default_factory=lambda: [Exception])


@dataclass
class WorkflowStep:
    """Individual workflow step definition"""
    step_id: str
    name: str
    step_type: WorkflowStepType
    function: Callable[..., Awaitable[Any]]
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    conditions: List[WorkflowCondition] = field(default_factory=list)
    retry_config: Optional[RetryConfig] = None
    timeout_seconds: Optional[float] = None
    
    # Runtime state
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Any = None
    error: Optional[Exception] = None
    retry_count: int = 0


@dataclass
class WorkflowDefinition:
    """Complete workflow definition"""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    priority: WorkflowPriority = WorkflowPriority.NORMAL
    timeout_minutes: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """Runtime workflow execution state"""
    execution_id: str
    workflow_definition: WorkflowDefinition
    status: StepStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    step_results: Dict[str, Any] = field(default_factory=dict)
    execution_context: Dict[str, Any] = field(default_factory=dict)


class WorkflowEngine:
    """
    Advanced Workflow Orchestration Engine
    
    Manages complex workflows with:
    - Sequential and parallel execution
    - Conditional branching
    - Retry mechanisms
    - Dependency resolution
    - Progress monitoring
    """
    
    def __init__(self, max_concurrent_workflows: int = 5):
        self.max_concurrent_workflows = max_concurrent_workflows
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.execution_history: List[WorkflowExecution] = []
        self.workflow_templates: Dict[str, WorkflowDefinition] = {}
        
        # Execution queue for priority-based scheduling
        self.execution_queue: List[WorkflowExecution] = []
        self.queue_lock = asyncio.Lock()
        
        logger.info(f"Workflow Engine initialized with max {max_concurrent_workflows} concurrent workflows")
    
    def register_workflow_template(self, workflow: WorkflowDefinition):
        """Register a reusable workflow template"""
        self.workflow_templates[workflow.workflow_id] = workflow
        logger.info(f"Registered workflow template: {workflow.workflow_id}")
    
    async def execute_workflow(self, workflow: WorkflowDefinition,
                             context: Optional[Dict[str, Any]] = None,
                             wait_for_completion: bool = False) -> WorkflowExecution:
        """Execute a workflow with the given context"""
        execution_id = f"{workflow.workflow_id}_{int(time.time())}"

        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_definition=workflow,
            status=StepStatus.PENDING,
            start_time=datetime.now(),
            execution_context=context or {}
        )

        # For immediate execution (testing), execute directly
        if len(self.active_executions) < self.max_concurrent_workflows:
            self.active_executions[execution.execution_id] = execution

            if wait_for_completion:
                # Execute synchronously for testing
                await self._execute_workflow_steps(execution)
            else:
                # Start execution in background
                asyncio.create_task(self._execute_workflow_steps(execution))
        else:
            # Add to queue if at capacity
            async with self.queue_lock:
                self.execution_queue.append(execution)
                self.execution_queue.sort(key=lambda x: x.workflow_definition.priority.value, reverse=True)

        return execution
    
    async def _process_execution_queue(self):
        """Process the execution queue based on priority and capacity"""
        async with self.queue_lock:
            while (len(self.active_executions) < self.max_concurrent_workflows and 
                   self.execution_queue):
                
                execution = self.execution_queue.pop(0)
                self.active_executions[execution.execution_id] = execution
                
                # Start execution in background
                asyncio.create_task(self._execute_workflow_steps(execution))
    
    async def _execute_workflow_steps(self, execution: WorkflowExecution):
        """Execute all steps in a workflow"""
        try:
            execution.status = StepStatus.RUNNING
            logger.info(f"Starting workflow execution: {execution.execution_id}")
            
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(execution.workflow_definition.steps)
            
            # Execute steps based on dependencies
            await self._execute_dependency_graph(execution, dependency_graph)
            
            # Determine final status
            if execution.failed_steps:
                execution.status = StepStatus.FAILED
            else:
                execution.status = StepStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {execution.execution_id} - {str(e)}")
            execution.status = StepStatus.FAILED
        
        finally:
            execution.end_time = datetime.now()
            await self._finalize_execution(execution)
    
    def _build_dependency_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """Build a dependency graph for workflow steps"""
        graph = {}
        step_map = {step.step_id: step for step in steps}
        
        for step in steps:
            graph[step.step_id] = []
            for dep in step.dependencies:
                if dep in step_map:
                    graph[step.step_id].append(dep)
        
        return graph
    
    async def _execute_dependency_graph(self, execution: WorkflowExecution, 
                                      dependency_graph: Dict[str, List[str]]):
        """Execute steps respecting dependency order"""
        step_map = {step.step_id: step for step in execution.workflow_definition.steps}
        completed_steps = set()
        
        while len(completed_steps) < len(step_map):
            # Find steps ready to execute (all dependencies completed)
            ready_steps = []
            for step_id, dependencies in dependency_graph.items():
                if (step_id not in completed_steps and 
                    all(dep in completed_steps for dep in dependencies)):
                    ready_steps.append(step_map[step_id])
            
            if not ready_steps:
                # Check for circular dependencies or failed dependencies
                remaining_steps = set(step_map.keys()) - completed_steps
                logger.error(f"No ready steps found. Remaining: {remaining_steps}")
                break
            
            # Execute ready steps (can be parallel if no interdependencies)
            await self._execute_step_batch(execution, ready_steps)
            
            # Update completed steps
            for step in ready_steps:
                if step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]:
                    completed_steps.add(step.step_id)
                elif step.status == StepStatus.FAILED:
                    # Handle step failure
                    if not await self._handle_step_failure(execution, step):
                        return  # Workflow failed
    
    async def _execute_step_batch(self, execution: WorkflowExecution, steps: List[WorkflowStep]):
        """Execute a batch of steps (potentially in parallel)"""
        tasks = []
        for step in steps:
            task = asyncio.create_task(self._execute_single_step(execution, step))
            tasks.append(task)
        
        # Wait for all steps to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_single_step(self, execution: WorkflowExecution, step: WorkflowStep):
        """Execute a single workflow step with retry logic"""
        step.start_time = datetime.now()
        step.status = StepStatus.RUNNING
        execution.current_step = step.step_id
        
        logger.info(f"Executing step: {step.step_id} in workflow {execution.execution_id}")
        
        # Check conditions before execution
        if not await self._evaluate_step_conditions(execution, step):
            step.status = StepStatus.SKIPPED
            step.end_time = datetime.now()
            logger.info(f"Step {step.step_id} skipped due to conditions")
            return
        
        # Execute with retry logic
        for attempt in range((step.retry_config.max_attempts if step.retry_config else 1)):
            try:
                # Set timeout if specified
                if step.timeout_seconds:
                    step.result = await asyncio.wait_for(
                        step.function(**step.parameters, **execution.execution_context),
                        timeout=step.timeout_seconds
                    )
                else:
                    step.result = await step.function(**step.parameters, **execution.execution_context)
                
                step.status = StepStatus.COMPLETED
                execution.completed_steps.append(step.step_id)
                execution.step_results[step.step_id] = step.result
                
                logger.info(f"Step {step.step_id} completed successfully")
                break
                
            except Exception as e:
                step.error = e
                step.retry_count = attempt + 1
                
                if step.retry_config and attempt < step.retry_config.max_attempts - 1:
                    # Calculate retry delay
                    delay = min(
                        step.retry_config.initial_delay * (step.retry_config.exponential_base ** attempt),
                        step.retry_config.max_delay
                    )
                    
                    step.status = StepStatus.RETRYING
                    logger.warning(f"Step {step.step_id} failed (attempt {attempt + 1}), retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    step.status = StepStatus.FAILED
                    execution.failed_steps.append(step.step_id)
                    logger.error(f"Step {step.step_id} failed after {attempt + 1} attempts: {str(e)}")
                    break
        
        step.end_time = datetime.now()
    
    async def _evaluate_step_conditions(self, execution: WorkflowExecution, 
                                      step: WorkflowStep) -> bool:
        """Evaluate whether a step should be executed based on conditions"""
        if not step.conditions:
            return True
        
        for condition in step.conditions:
            if condition.condition_type == 'success':
                if condition.target_step in execution.failed_steps:
                    return False
            elif condition.condition_type == 'failure':
                if condition.target_step not in execution.failed_steps:
                    return False
            elif condition.condition_type == 'custom' and condition.custom_function:
                if not await condition.custom_function(execution, condition.parameters):
                    return False
        
        return True
    
    async def _handle_step_failure(self, execution: WorkflowExecution, 
                                 failed_step: WorkflowStep) -> bool:
        """Handle step failure and determine if workflow should continue"""
        # For now, any step failure stops the workflow
        # This can be enhanced with more sophisticated failure handling
        logger.error(f"Workflow {execution.execution_id} failed due to step {failed_step.step_id}")
        return False
    
    async def _finalize_execution(self, execution: WorkflowExecution):
        """Finalize workflow execution and cleanup"""
        # Remove from active executions
        if execution.execution_id in self.active_executions:
            del self.active_executions[execution.execution_id]
        
        # Add to history
        self.execution_history.append(execution)
        
        # Keep only last 100 executions in history
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
        
        # Process next workflow in queue
        await self._process_execution_queue()
        
        logger.info(f"Workflow execution finalized: {execution.execution_id} - Status: {execution.status.value}")
    
    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get status of a specific workflow execution"""
        # Check active executions
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]
        
        # Check history
        for execution in self.execution_history:
            if execution.execution_id == execution_id:
                return execution
        
        return None
    
    def get_active_executions(self) -> List[WorkflowExecution]:
        """Get all active workflow executions"""
        return list(self.active_executions.values())
    
    def get_execution_history(self, limit: int = 10) -> List[WorkflowExecution]:
        """Get recent execution history"""
        return self.execution_history[-limit:]
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an active workflow execution"""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = StepStatus.FAILED
            execution.end_time = datetime.now()
            
            # Find current step and mark as failed
            for step in execution.workflow_definition.steps:
                if step.step_id == execution.current_step:
                    step.status = StepStatus.FAILED
                    step.end_time = datetime.now()
                    break
            
            await self._finalize_execution(execution)
            logger.info(f"Cancelled workflow execution: {execution_id}")
            return True
        
        return False


# DABS-specific workflow templates
def create_dabs_automation_workflow() -> WorkflowDefinition:
    """Create the standard DABS automation workflow"""

    # Define retry configuration for critical steps
    critical_retry = RetryConfig(
        max_attempts=3,
        initial_delay=2.0,
        max_delay=30.0,
        exponential_base=2.0
    )

    steps = [
        WorkflowStep(
            step_id="validate_dabs_file",
            name="Validate DABS Excel File",
            step_type=WorkflowStepType.VALIDATION,
            function=validate_dabs_file_async,
            timeout_seconds=60.0
        ),

        WorkflowStep(
            step_id="backup_original_file",
            name="Create Backup of Original File",
            step_type=WorkflowStepType.SEQUENTIAL,
            function=create_file_backup_async,
            dependencies=["validate_dabs_file"]
        ),

        WorkflowStep(
            step_id="process_dabs_file",
            name="Process DABS Excel File",
            step_type=WorkflowStepType.SEQUENTIAL,
            function=process_dabs_file_async,
            dependencies=["backup_original_file"],
            retry_config=critical_retry,
            timeout_seconds=300.0
        ),

        WorkflowStep(
            step_id="upload_to_sscs",
            name="Upload to SSCS via CPB",
            step_type=WorkflowStepType.SEQUENTIAL,
            function=upload_to_sscs_async,
            dependencies=["process_dabs_file"],
            retry_config=critical_retry,
            timeout_seconds=180.0
        ),

        WorkflowStep(
            step_id="sync_quickbooks",
            name="Sync with QuickBooks Online",
            step_type=WorkflowStepType.PARALLEL,
            function=sync_quickbooks_async,
            dependencies=["process_dabs_file"],
            retry_config=critical_retry,
            timeout_seconds=240.0
        ),

        WorkflowStep(
            step_id="validate_integrations",
            name="Validate All Integrations",
            step_type=WorkflowStepType.VALIDATION,
            function=validate_all_integrations_async,
            dependencies=["upload_to_sscs", "sync_quickbooks"],
            timeout_seconds=120.0
        ),

        WorkflowStep(
            step_id="generate_reports",
            name="Generate Completion Reports",
            step_type=WorkflowStepType.SEQUENTIAL,
            function=generate_completion_reports_async,
            dependencies=["validate_integrations"],
            timeout_seconds=60.0
        ),

        WorkflowStep(
            step_id="send_notifications",
            name="Send Success Notifications",
            step_type=WorkflowStepType.NOTIFICATION,
            function=send_success_notifications_async,
            dependencies=["generate_reports"],
            timeout_seconds=30.0
        )
    ]

    return WorkflowDefinition(
        workflow_id="dabs_automation_standard",
        name="DABS Automation Standard Workflow",
        description="Complete DABS processing workflow with SSCS and QuickBooks integration",
        steps=steps,
        priority=WorkflowPriority.HIGH,
        timeout_minutes=30.0,
        metadata={
            "version": "1.0",
            "systems": ["DABS", "SSCS", "QuickBooks"],
            "estimated_duration_minutes": 15
        }
    )


# Placeholder async functions for workflow steps
async def validate_dabs_file_async(file_path: str = None, **kwargs) -> Dict[str, Any]:
    """Validate DABS file format and content"""
    await asyncio.sleep(1)
    return {"valid": True, "sku_count": 1239}


async def create_file_backup_async(file_path: str = None, **kwargs) -> Dict[str, Any]:
    """Create backup of original file"""
    await asyncio.sleep(0.5)
    return {"backup_path": f"{file_path}.backup" if file_path else "backup.xlsx"}


async def process_dabs_file_async(file_path: str = None, **kwargs) -> Dict[str, Any]:
    """Process DABS Excel file"""
    await asyncio.sleep(3)
    return {"products": [], "processed_count": 1239}


async def upload_to_sscs_async(products: List = None, **kwargs) -> Dict[str, Any]:
    """Upload products to SSCS"""
    await asyncio.sleep(2)
    return {"uploaded_count": len(products) if products else 1239}


async def sync_quickbooks_async(products: List = None, **kwargs) -> Dict[str, Any]:
    """Sync with QuickBooks Online"""
    await asyncio.sleep(2.5)
    return {"synced_count": len(products) if products else 1239}


async def validate_all_integrations_async(**kwargs) -> Dict[str, Any]:
    """Validate all integrations completed successfully"""
    await asyncio.sleep(1)
    return {"all_valid": True, "validation_details": {}}


async def generate_completion_reports_async(**kwargs) -> Dict[str, Any]:
    """Generate completion reports"""
    await asyncio.sleep(1)
    return {"reports_generated": ["summary.pdf", "audit_trail.csv"]}


async def send_success_notifications_async(**kwargs) -> Dict[str, Any]:
    """Send success notifications"""
    await asyncio.sleep(0.5)
    return {"notifications_sent": ["email", "dashboard"]}
