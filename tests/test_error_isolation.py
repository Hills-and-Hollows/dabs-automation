#!/usr/bin/env python3
"""
Test Error Isolation System - Hills & Hollows LLC
Tests the comprehensive error handling and rollback capabilities

Author: DABS Automation System
Created: 2025-08-22
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime
import shutil

# Import our modules
import sys
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from integration_hub.error_isolation import (
    ErrorIsolationManager,
    ErrorContext,
    ErrorSeverity,
    SystemType,
    RollbackAction,
    RollbackStep,
    TransactionState,
    create_file_rollback_step,
    create_api_rollback_step
)


@pytest.fixture
def temp_backup_dir():
    """Create temporary directory for backups"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_file():
    """Create a sample file for backup testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
        tmp_file.write("Sample content for testing")
        return Path(tmp_file.name)


class TestErrorIsolationManager:
    """Test suite for Error Isolation Manager"""
    
    def test_manager_initialization(self, temp_backup_dir):
        """Test error isolation manager initialization"""
        manager = ErrorIsolationManager(str(temp_backup_dir))
        
        assert manager.backup_directory == temp_backup_dir
        assert len(manager.active_transactions) == 0
        assert len(manager.error_history) == 0
        assert all(manager.system_health.values())  # All systems should start healthy
    
    def test_transaction_lifecycle(self, temp_backup_dir):
        """Test complete transaction lifecycle"""
        manager = ErrorIsolationManager(str(temp_backup_dir))
        
        # Start transaction
        systems = [SystemType.DABS, SystemType.SSCS]
        transaction = manager.start_transaction("test_tx_001", systems)
        
        assert transaction.transaction_id == "test_tx_001"
        assert transaction.systems_involved == systems
        assert not transaction.is_committed
        assert not transaction.is_rolled_back
        assert "test_tx_001" in manager.active_transactions
        
        # Commit transaction
        success = manager.commit_transaction("test_tx_001")
        assert success is True
        assert "test_tx_001" not in manager.active_transactions
    
    def test_backup_creation(self, temp_backup_dir, sample_file):
        """Test backup file creation"""
        manager = ErrorIsolationManager(str(temp_backup_dir))
        
        # Start transaction
        transaction = manager.start_transaction("backup_test", [SystemType.DABS])
        
        # Create backup
        backup_path = manager.create_backup("backup_test", sample_file, "test_backup")
        
        # Verify backup was created
        assert Path(backup_path).exists()
        assert "test_backup" in transaction.backup_locations
        
        # Verify backup content
        with open(backup_path, 'r') as f:
            content = f.read()
        assert "Sample content for testing" in content
    
    @pytest.mark.asyncio
    async def test_error_handling(self, temp_backup_dir):
        """Test error handling and context creation"""
        manager = ErrorIsolationManager(str(temp_backup_dir))
        
        # Create test error
        test_error = ValueError("Test error message")
        
        error_context = await manager.handle_error(
            error=test_error,
            system=SystemType.SSCS,
            operation="test_operation",
            severity=ErrorSeverity.MEDIUM,
            affected_skus=["SKU001", "SKU002"]
        )
        
        # Verify error context
        assert error_context.system == SystemType.SSCS
        assert error_context.operation == "test_operation"
        assert error_context.severity == ErrorSeverity.MEDIUM
        assert error_context.error_message == "Test error message"
        assert error_context.affected_skus == ["SKU001", "SKU002"]
        assert len(error_context.recovery_suggestions) > 0
        
        # Verify error was added to history
        assert len(manager.error_history) == 1
        assert manager.error_history[0] == error_context
    
    @pytest.mark.asyncio
    async def test_critical_error_auto_rollback(self, temp_backup_dir):
        """Test automatic rollback on critical errors"""
        manager = ErrorIsolationManager(str(temp_backup_dir))
        
        # Start transaction with rollback step
        transaction = manager.start_transaction("critical_test", [SystemType.DABS])
        
        rollback_step = RollbackStep(
            action=RollbackAction.NOTIFICATION,
            system=SystemType.DABS,
            description="Test rollback step"
        )
        manager.add_rollback_step("critical_test", rollback_step)
        
        # Create critical error (should trigger auto-rollback)
        critical_error = Exception("Critical system failure")
        
        await manager.handle_error(
            error=critical_error,
            system=SystemType.DABS,
            operation="critical_operation",
            transaction_id="critical_test",
            severity=ErrorSeverity.CRITICAL
        )
        
        # Verify transaction was rolled back
        assert "critical_test" not in manager.active_transactions
        assert manager.system_health[SystemType.DABS] is False
    
    @pytest.mark.asyncio
    async def test_file_rollback_execution(self, temp_backup_dir, sample_file):
        """Test file rollback execution"""
        manager = ErrorIsolationManager(str(temp_backup_dir))
        
        # Start transaction and create backup
        transaction = manager.start_transaction("file_rollback_test", [SystemType.DABS])
        backup_path = manager.create_backup("file_rollback_test", sample_file, "original_file")
        
        # Modify the original file
        with open(sample_file, 'w') as f:
            f.write("Modified content")
        
        # Add file rollback step
        rollback_step = create_file_rollback_step(
            SystemType.DABS,
            str(sample_file),
            "original_file"
        )
        manager.add_rollback_step("file_rollback_test", rollback_step)
        
        # Execute rollback
        success = await manager.rollback_transaction("file_rollback_test")
        assert success is True
        
        # Verify file was restored
        with open(sample_file, 'r') as f:
            content = f.read()
        assert "Sample content for testing" in content
        assert "Modified content" not in content
    
    @pytest.mark.asyncio
    async def test_custom_rollback_function(self, temp_backup_dir):
        """Test custom rollback function execution"""
        manager = ErrorIsolationManager(str(temp_backup_dir))
        
        # Track if custom function was called
        rollback_called = False
        rollback_data = None
        
        async def custom_rollback(data):
            nonlocal rollback_called, rollback_data
            rollback_called = True
            rollback_data = data
        
        # Start transaction
        transaction = manager.start_transaction("custom_rollback_test", [SystemType.QUICKBOOKS])
        
        # Add custom rollback step
        rollback_step = create_api_rollback_step(
            SystemType.QUICKBOOKS,
            "test_api_operation",
            custom_rollback
        )
        rollback_step.rollback_data = {"test_key": "test_value"}
        manager.add_rollback_step("custom_rollback_test", rollback_step)
        
        # Execute rollback
        success = await manager.rollback_transaction("custom_rollback_test")
        assert success is True
        assert rollback_called is True
        assert rollback_data == {"test_key": "test_value"}
    
    def test_system_health_management(self, temp_backup_dir):
        """Test system health tracking"""
        manager = ErrorIsolationManager(str(temp_backup_dir))
        
        # All systems should start healthy
        health = manager.get_system_health()
        assert all(health.values())
        
        # Mark system as unhealthy
        manager.system_health[SystemType.SSCS] = False
        health = manager.get_system_health()
        assert health[SystemType.SSCS] is False
        assert health[SystemType.DABS] is True
        
        # Mark system as healthy again
        manager.mark_system_healthy(SystemType.SSCS)
        health = manager.get_system_health()
        assert health[SystemType.SSCS] is True
    
    def test_error_history_tracking(self, temp_backup_dir):
        """Test error history tracking and retrieval"""
        manager = ErrorIsolationManager(str(temp_backup_dir))
        
        # Add multiple errors to history
        for i in range(5):
            error_context = ErrorContext(
                system=SystemType.DABS,
                operation=f"operation_{i}",
                timestamp=datetime.now(),
                severity=ErrorSeverity.LOW,
                error_message=f"Error {i}"
            )
            manager.error_history.append(error_context)
        
        # Test history retrieval
        history = manager.get_error_history(limit=3)
        assert len(history) == 3
        assert history[-1].error_message == "Error 4"  # Most recent
        
        # Test full history
        full_history = manager.get_error_history(limit=10)
        assert len(full_history) == 5
    
    def test_rollback_step_creation_helpers(self):
        """Test rollback step creation helper functions"""
        # Test file rollback step creation
        file_step = create_file_rollback_step(
            SystemType.DABS,
            "/path/to/file.txt",
            "backup_name"
        )
        
        assert file_step.action == RollbackAction.FILE_RESTORE
        assert file_step.system == SystemType.DABS
        assert file_step.rollback_data['target_path'] == "/path/to/file.txt"
        assert file_step.rollback_data['backup_name'] == "backup_name"
        
        # Test API rollback step creation
        async def dummy_rollback(data):
            pass
        
        api_step = create_api_rollback_step(
            SystemType.QUICKBOOKS,
            "create_item",
            dummy_rollback
        )
        
        assert api_step.action == RollbackAction.API_UNDO
        assert api_step.system == SystemType.QUICKBOOKS
        assert api_step.rollback_function == dummy_rollback
        assert "Undo create_item" in api_step.description
    
    def test_transaction_cleanup(self, temp_backup_dir):
        """Test transaction cleanup after commit/rollback"""
        manager = ErrorIsolationManager(str(temp_backup_dir))
        
        # Start multiple transactions
        tx1 = manager.start_transaction("tx1", [SystemType.DABS])
        tx2 = manager.start_transaction("tx2", [SystemType.SSCS])
        
        assert len(manager.active_transactions) == 2
        
        # Commit one transaction
        manager.commit_transaction("tx1")
        assert len(manager.active_transactions) == 1
        assert "tx1" not in manager.active_transactions
        assert "tx2" in manager.active_transactions
        
        # Get active transactions
        active = manager.get_active_transactions()
        assert len(active) == 1
        assert active[0].transaction_id == "tx2"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
