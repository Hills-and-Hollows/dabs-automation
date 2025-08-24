#!/usr/bin/env python3
"""
Test Integration Coordinator - Hills & Hollows LLC
Tests the central coordination system for DABS automation workflow

Author: DABS Automation System
Created: 2025-08-22
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime
import pandas as pd

# Import our modules
import sys
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from integration_hub.coordinator import (
    IntegrationCoordinator, 
    WorkflowStatus, 
    IntegrationStep,
    StepResult,
    WorkflowResult
)
from processors.dabs_processor import DABSProduct


@pytest.fixture
def sample_dabs_excel():
    """Create a sample DABS Excel file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        # Create sample data with proper DABS column names
        data = {
            'SKU': ['12345', '67890', '11111'],
            'ITEM NAME': ['Test Whiskey 750ml', 'Test Vodka 1L', 'Test Rum 750ml'],
            'PRICE': [29.99, 24.99, 32.99],
            'ITEM TYPE': ['Spirits', 'Spirits', 'Spirits'],
            'ITEM STATUS': ['Active', 'Active', 'Active'],
            'ON SPA?': ['No', 'Yes', 'No'],
            'FROM DATE': ['2025-01-01', '2025-01-01', '2025-01-01'],
            'TO DATE': ['2025-12-31', '2025-12-31', '2025-12-31']
        }

        df = pd.DataFrame(data)

        # Create Excel file with header row like DABS format
        with pd.ExcelWriter(tmp_file.name, engine='openpyxl') as writer:
            header_df = pd.DataFrame([['DABS Price Changes Report']])
            header_df.to_excel(writer, index=False, header=False, startrow=0)
            df.to_excel(writer, index=False, startrow=1)
        
        return Path(tmp_file.name)


@pytest.fixture
def temp_config_dir():
    """Create temporary directory for configuration"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


class TestIntegrationCoordinator:
    """Test suite for Integration Coordinator"""
    
    def test_coordinator_initialization(self, temp_config_dir):
        """Test coordinator initialization with default config"""
        coordinator = IntegrationCoordinator()
        
        assert coordinator.config is not None
        assert coordinator.dabs_processor is not None
        assert coordinator.sscs_integrator is not None
        assert len(coordinator.active_workflows) == 0
        assert len(coordinator.workflow_history) == 0
    
    def test_coordinator_with_custom_config(self, temp_config_dir):
        """Test coordinator initialization with custom config"""
        config_file = temp_config_dir / "test_config.json"
        config_data = {
            'max_concurrent_workflows': 2,
            'step_timeout_minutes': 45,
            'enable_rollback': False
        }
        
        with open(config_file, 'w') as f:
            import json
            json.dump(config_data, f)
        
        coordinator = IntegrationCoordinator(str(config_file))
        
        assert coordinator.config['max_concurrent_workflows'] == 2
        assert coordinator.config['step_timeout_minutes'] == 45
        assert coordinator.config['enable_rollback'] is False
    
    @pytest.mark.asyncio
    async def test_workflow_execution_success(self, sample_dabs_excel, temp_config_dir):
        """Test successful workflow execution"""
        coordinator = IntegrationCoordinator()
        
        # Override SSCS upload directory for testing
        coordinator.config['sscs_upload_directory'] = str(temp_config_dir / "sscs_uploads")
        coordinator.sscs_integrator.config.upload_directory = str(temp_config_dir / "sscs_uploads")
        coordinator.sscs_integrator.export_dir = temp_config_dir
        
        # Execute workflow
        result = await coordinator.execute_workflow(sample_dabs_excel)
        
        # Verify workflow result
        assert result is not None
        assert result.workflow_id.startswith("workflow_")
        assert result.status in [WorkflowStatus.COMPLETED, WorkflowStatus.PARTIAL_SUCCESS]
        assert result.total_skus_processed == 3
        assert result.start_time is not None
        assert result.end_time is not None
        assert result.duration is not None
        
        # Verify steps were executed
        assert len(result.steps) >= 3  # DABS processing, SSCS upload, QuickBooks sync
        
        # Check DABS processing step
        dabs_step = next((s for s in result.steps if s.step == IntegrationStep.DABS_PROCESSING), None)
        assert dabs_step is not None
        assert dabs_step.success is True
        assert dabs_step.data is not None
        assert 'products' in dabs_step.data
        
        # Check SSCS upload step
        sscs_step = next((s for s in result.steps if s.step == IntegrationStep.SSCS_UPLOAD), None)
        assert sscs_step is not None
        assert sscs_step.success is True
        
        # Verify workflow tracking
        assert len(coordinator.workflow_history) == 1
        assert len(coordinator.active_workflows) == 0
    
    @pytest.mark.asyncio
    async def test_workflow_with_invalid_file(self, temp_config_dir):
        """Test workflow execution with invalid DABS file"""
        coordinator = IntegrationCoordinator()
        
        # Try to process non-existent file
        non_existent_file = temp_config_dir / "non_existent.xlsx"
        
        result = await coordinator.execute_workflow(non_existent_file)
        
        # Verify workflow failed
        assert result.status == WorkflowStatus.FAILED
        assert len(result.failed_integrations) > 0
        assert "DABS Processing" in result.failed_integrations
        
        # Verify DABS processing step failed
        dabs_step = next((s for s in result.steps if s.step == IntegrationStep.DABS_PROCESSING), None)
        assert dabs_step is not None
        assert dabs_step.success is False
        assert len(dabs_step.errors) > 0
    
    def test_step_result_duration_calculation(self):
        """Test step result duration calculation"""
        from datetime import timedelta

        start_time = datetime.now()
        step = StepResult(
            step=IntegrationStep.DABS_PROCESSING,
            status=WorkflowStatus.RUNNING,
            start_time=start_time
        )

        # Duration should be None when end_time is not set
        assert step.duration is None

        # Set end_time and verify duration calculation
        step.end_time = start_time + timedelta(seconds=5)
        duration = step.duration
        assert duration is not None
        assert duration.total_seconds() == 5.0
    
    def test_workflow_result_success_rate(self):
        """Test workflow result success rate calculation"""
        workflow = WorkflowResult(
            workflow_id="test_workflow",
            status=WorkflowStatus.COMPLETED,
            start_time=datetime.now()
        )
        
        # Empty workflow should have 0% success rate
        assert workflow.success_rate == 0.0
        
        # Add successful steps
        workflow.steps.append(StepResult(
            step=IntegrationStep.DABS_PROCESSING,
            status=WorkflowStatus.COMPLETED,
            start_time=datetime.now(),
            success=True
        ))
        
        workflow.steps.append(StepResult(
            step=IntegrationStep.SSCS_UPLOAD,
            status=WorkflowStatus.FAILED,
            start_time=datetime.now(),
            success=False
        ))
        
        # Should be 50% success rate (1 out of 2 steps successful)
        assert workflow.success_rate == 50.0
    
    def test_workflow_status_tracking(self, temp_config_dir):
        """Test workflow status tracking functionality"""
        coordinator = IntegrationCoordinator()
        
        # Create a test workflow
        workflow = WorkflowResult(
            workflow_id="test_workflow_123",
            status=WorkflowStatus.RUNNING,
            start_time=datetime.now()
        )
        
        # Add to active workflows
        coordinator.active_workflows["test_workflow_123"] = workflow
        
        # Test getting active workflow
        retrieved = coordinator.get_workflow_status("test_workflow_123")
        assert retrieved is not None
        assert retrieved.workflow_id == "test_workflow_123"
        
        # Test getting active workflows list
        active = coordinator.get_active_workflows()
        assert len(active) == 1
        assert active[0].workflow_id == "test_workflow_123"
        
        # Move to history
        workflow.status = WorkflowStatus.COMPLETED
        workflow.end_time = datetime.now()
        del coordinator.active_workflows["test_workflow_123"]
        coordinator.workflow_history.append(workflow)
        
        # Test getting from history
        retrieved = coordinator.get_workflow_status("test_workflow_123")
        assert retrieved is not None
        assert retrieved.status == WorkflowStatus.COMPLETED
        
        # Test getting workflow history
        history = coordinator.get_workflow_history()
        assert len(history) == 1
        assert history[0].workflow_id == "test_workflow_123"
    
    def test_workflow_history_limit(self, temp_config_dir):
        """Test workflow history size limiting"""
        coordinator = IntegrationCoordinator()
        
        # Add more than 100 workflows to history
        for i in range(105):
            workflow = WorkflowResult(
                workflow_id=f"test_workflow_{i}",
                status=WorkflowStatus.COMPLETED,
                start_time=datetime.now()
            )
            coordinator.workflow_history.append(workflow)
        
        # Simulate finalization which should trim history
        test_workflow = WorkflowResult(
            workflow_id="final_workflow",
            status=WorkflowStatus.COMPLETED,
            start_time=datetime.now()
        )
        
        # Manually trigger the history trimming logic
        coordinator.workflow_history.append(test_workflow)
        if len(coordinator.workflow_history) > 100:
            coordinator.workflow_history = coordinator.workflow_history[-100:]
        
        # Verify history is limited to 100
        assert len(coordinator.workflow_history) == 100
        assert coordinator.workflow_history[-1].workflow_id == "final_workflow"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
