#!/usr/bin/env python3
"""
Test Workflow Engine - Hills & Hollows LLC
Tests the advanced workflow orchestration engine

Author: DABS Automation System
Created: 2025-08-22
"""

import pytest
import asyncio
from datetime import datetime

# Import our modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from integration_hub.workflow_engine import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowStepType,
    WorkflowPriority,
    StepStatus,
    RetryConfig,
    create_dabs_automation_workflow
)


class TestWorkflowEngine:
    """Test suite for Workflow Engine"""
    
    def test_engine_initialization(self):
        """Test workflow engine initialization"""
        engine = WorkflowEngine(max_concurrent_workflows=3)
        
        assert engine.max_concurrent_workflows == 3
        assert len(engine.active_executions) == 0
        assert len(engine.execution_history) == 0
        assert len(engine.workflow_templates) == 0
        assert len(engine.execution_queue) == 0
    
    def test_workflow_template_registration(self):
        """Test workflow template registration"""
        engine = WorkflowEngine()
        
        # Create simple workflow
        async def dummy_step(**kwargs):
            return {"result": "success"}
        
        workflow = WorkflowDefinition(
            workflow_id="test_workflow",
            name="Test Workflow",
            description="Simple test workflow",
            steps=[
                WorkflowStep(
                    step_id="step1",
                    name="Test Step",
                    step_type=WorkflowStepType.SEQUENTIAL,
                    function=dummy_step
                )
            ]
        )
        
        engine.register_workflow_template(workflow)
        
        assert "test_workflow" in engine.workflow_templates
        assert engine.workflow_templates["test_workflow"] == workflow
    
    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self):
        """Test execution of a simple workflow"""
        engine = WorkflowEngine()
        
        # Track execution
        execution_order = []
        
        async def step1(**kwargs):
            execution_order.append("step1")
            await asyncio.sleep(0.1)
            return {"step": "step1", "result": "success"}
        
        async def step2(**kwargs):
            execution_order.append("step2")
            await asyncio.sleep(0.1)
            return {"step": "step2", "result": "success"}
        
        workflow = WorkflowDefinition(
            workflow_id="simple_test",
            name="Simple Test Workflow",
            description="Test sequential execution",
            steps=[
                WorkflowStep(
                    step_id="step1",
                    name="First Step",
                    step_type=WorkflowStepType.SEQUENTIAL,
                    function=step1
                ),
                WorkflowStep(
                    step_id="step2",
                    name="Second Step",
                    step_type=WorkflowStepType.SEQUENTIAL,
                    function=step2,
                    dependencies=["step1"]
                )
            ]
        )
        
        # Execute workflow and wait for completion
        execution = await engine.execute_workflow(workflow, wait_for_completion=True)
        
        # Verify execution
        assert execution.status == StepStatus.COMPLETED
        assert len(execution.completed_steps) == 2
        assert "step1" in execution.completed_steps
        assert "step2" in execution.completed_steps
        assert execution_order == ["step1", "step2"]
    
    @pytest.mark.asyncio
    async def test_workflow_with_failure(self):
        """Test workflow execution with step failure"""
        engine = WorkflowEngine()
        
        async def failing_step(**kwargs):
            raise ValueError("Intentional test failure")
        
        async def success_step(**kwargs):
            return {"result": "success"}
        
        workflow = WorkflowDefinition(
            workflow_id="failure_test",
            name="Failure Test Workflow",
            description="Test failure handling",
            steps=[
                WorkflowStep(
                    step_id="fail_step",
                    name="Failing Step",
                    step_type=WorkflowStepType.SEQUENTIAL,
                    function=failing_step
                ),
                WorkflowStep(
                    step_id="success_step",
                    name="Success Step",
                    step_type=WorkflowStepType.SEQUENTIAL,
                    function=success_step,
                    dependencies=["fail_step"]
                )
            ]
        )
        
        # Execute workflow and wait for completion
        execution = await engine.execute_workflow(workflow, wait_for_completion=True)
        
        # Verify failure handling
        assert execution.status == StepStatus.FAILED
        assert len(execution.failed_steps) == 1
        assert "fail_step" in execution.failed_steps
        assert len(execution.completed_steps) == 0
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """Test step retry mechanism"""
        engine = WorkflowEngine()
        
        attempt_count = 0
        
        async def flaky_step(**kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError(f"Failure attempt {attempt_count}")
            return {"result": "success", "attempts": attempt_count}
        
        retry_config = RetryConfig(
            max_attempts=3,
            initial_delay=0.1,
            max_delay=1.0,
            exponential_base=2.0
        )
        
        workflow = WorkflowDefinition(
            workflow_id="retry_test",
            name="Retry Test Workflow",
            description="Test retry mechanism",
            steps=[
                WorkflowStep(
                    step_id="flaky_step",
                    name="Flaky Step",
                    step_type=WorkflowStepType.SEQUENTIAL,
                    function=flaky_step,
                    retry_config=retry_config
                )
            ]
        )
        
        # Execute workflow and wait for completion
        execution = await engine.execute_workflow(workflow, wait_for_completion=True)
        
        # Verify retry worked
        assert execution.status == StepStatus.COMPLETED
        assert len(execution.completed_steps) == 1
        assert attempt_count == 3
        
        # Check step retry count (retry_count is number of retries, not total attempts)
        flaky_step_obj = next(s for s in workflow.steps if s.step_id == "flaky_step")
        assert flaky_step_obj.retry_count == 2  # 2 retries + 1 initial attempt = 3 total
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test parallel step execution"""
        engine = WorkflowEngine()
        
        execution_times = {}
        
        async def timed_step(step_name, duration=0.2, **kwargs):
            start_time = datetime.now()
            await asyncio.sleep(duration)
            end_time = datetime.now()
            execution_times[step_name] = (start_time, end_time)
            return {"step": step_name, "duration": duration}
        
        workflow = WorkflowDefinition(
            workflow_id="parallel_test",
            name="Parallel Test Workflow",
            description="Test parallel execution",
            steps=[
                WorkflowStep(
                    step_id="init_step",
                    name="Initialization Step",
                    step_type=WorkflowStepType.SEQUENTIAL,
                    function=lambda **kwargs: timed_step("init", 0.1, **kwargs)
                ),
                WorkflowStep(
                    step_id="parallel_step1",
                    name="Parallel Step 1",
                    step_type=WorkflowStepType.PARALLEL,
                    function=lambda **kwargs: timed_step("parallel1", 0.2, **kwargs),
                    dependencies=["init_step"]
                ),
                WorkflowStep(
                    step_id="parallel_step2",
                    name="Parallel Step 2",
                    step_type=WorkflowStepType.PARALLEL,
                    function=lambda **kwargs: timed_step("parallel2", 0.2, **kwargs),
                    dependencies=["init_step"]
                )
            ]
        )
        
        # Execute workflow and wait for completion
        execution = await engine.execute_workflow(workflow, wait_for_completion=True)
        
        # Verify parallel execution
        assert execution.status == StepStatus.COMPLETED
        assert len(execution.completed_steps) == 3
        
        # Check that parallel steps ran concurrently
        if "parallel1" in execution_times and "parallel2" in execution_times:
            start1, end1 = execution_times["parallel1"]
            start2, end2 = execution_times["parallel2"]
            
            # Steps should have overlapping execution times
            overlap = min(end1, end2) - max(start1, start2)
            assert overlap.total_seconds() > 0.1  # Significant overlap
    
    @pytest.mark.asyncio
    async def test_workflow_timeout(self):
        """Test workflow step timeout"""
        engine = WorkflowEngine()
        
        async def slow_step(**kwargs):
            await asyncio.sleep(2.0)  # Longer than timeout
            return {"result": "should_not_complete"}
        
        workflow = WorkflowDefinition(
            workflow_id="timeout_test",
            name="Timeout Test Workflow",
            description="Test step timeout",
            steps=[
                WorkflowStep(
                    step_id="slow_step",
                    name="Slow Step",
                    step_type=WorkflowStepType.SEQUENTIAL,
                    function=slow_step,
                    timeout_seconds=0.5  # Short timeout
                )
            ]
        )
        
        # Execute workflow and wait for completion
        execution = await engine.execute_workflow(workflow, wait_for_completion=True)
        
        # Verify timeout handling
        assert execution.status == StepStatus.FAILED
        assert len(execution.failed_steps) == 1
        assert "slow_step" in execution.failed_steps
    
    def test_dabs_workflow_template_creation(self):
        """Test DABS automation workflow template creation"""
        workflow = create_dabs_automation_workflow()
        
        assert workflow.workflow_id == "dabs_automation_standard"
        assert workflow.priority == WorkflowPriority.HIGH
        assert len(workflow.steps) == 8
        
        # Verify step dependencies
        step_map = {step.step_id: step for step in workflow.steps}
        
        # Check specific dependencies
        assert "validate_dabs_file" in step_map
        assert step_map["backup_original_file"].dependencies == ["validate_dabs_file"]
        assert step_map["process_dabs_file"].dependencies == ["backup_original_file"]
        assert step_map["upload_to_sscs"].dependencies == ["process_dabs_file"]
        assert step_map["sync_quickbooks"].dependencies == ["process_dabs_file"]
        assert set(step_map["validate_integrations"].dependencies) == {"upload_to_sscs", "sync_quickbooks"}
    
    @pytest.mark.asyncio
    async def test_dabs_workflow_execution(self):
        """Test execution of DABS automation workflow"""
        engine = WorkflowEngine()
        workflow = create_dabs_automation_workflow()
        
        # Execute workflow with context and wait for completion
        context = {"file_path": "/test/dabs_file.xlsx"}
        execution = await engine.execute_workflow(workflow, context, wait_for_completion=True)
        
        # Verify execution completed
        assert execution.status == StepStatus.COMPLETED
        assert len(execution.completed_steps) == 8
        assert len(execution.failed_steps) == 0
    
    @pytest.mark.asyncio
    async def test_workflow_cancellation(self):
        """Test workflow execution cancellation"""
        engine = WorkflowEngine()
        
        async def long_running_step(**kwargs):
            await asyncio.sleep(10)  # Long running step
            return {"result": "completed"}
        
        workflow = WorkflowDefinition(
            workflow_id="cancellation_test",
            name="Cancellation Test",
            description="Test workflow cancellation",
            steps=[
                WorkflowStep(
                    step_id="long_step",
                    name="Long Running Step",
                    step_type=WorkflowStepType.SEQUENTIAL,
                    function=long_running_step
                )
            ]
        )
        
        # Start execution
        execution = await engine.execute_workflow(workflow)
        
        # Wait a bit then cancel
        await asyncio.sleep(0.2)
        success = await engine.cancel_execution(execution.execution_id)
        
        assert success is True
        assert execution.status == StepStatus.FAILED
        assert execution.execution_id not in engine.active_executions


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
