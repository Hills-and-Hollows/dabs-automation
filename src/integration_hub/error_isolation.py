#!/usr/bin/env python3
"""
Error Isolation System - Hills & Hollows LLC
Comprehensive error handling and rollback capabilities for DABS automation

Provides:
- System-level error isolation
- Automatic rollback mechanisms
- Transaction-like behavior across integrations
- Error recovery strategies
- Audit trail for all operations

Author: DABS Automation System
Created: 2025-08-22
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import shutil
import traceback

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SystemType(Enum):
    """Integrated system types"""
    DABS = "dabs"
    SSCS = "sscs"
    QUICKBOOKS = "quickbooks"
    VERIFONE = "verifone"
    COORDINATOR = "coordinator"


class RollbackAction(Enum):
    """Types of rollback actions"""
    FILE_RESTORE = "file_restore"
    DATA_REVERT = "data_revert"
    API_UNDO = "api_undo"
    CACHE_CLEAR = "cache_clear"
    NOTIFICATION = "notification"


@dataclass
class ErrorContext:
    """Context information for an error"""
    system: SystemType
    operation: str
    timestamp: datetime
    severity: ErrorSeverity
    error_message: str
    stack_trace: Optional[str] = None
    data_context: Optional[Dict[str, Any]] = None
    affected_skus: List[str] = field(default_factory=list)
    recovery_suggestions: List[str] = field(default_factory=list)


@dataclass
class RollbackStep:
    """Individual rollback step"""
    action: RollbackAction
    system: SystemType
    description: str
    rollback_function: Optional[Callable] = None
    rollback_data: Optional[Dict[str, Any]] = None
    executed: bool = False
    success: bool = False
    error_message: Optional[str] = None
    execution_time: Optional[datetime] = None


@dataclass
class TransactionState:
    """State tracking for a transaction across systems"""
    transaction_id: str
    start_time: datetime
    systems_involved: List[SystemType]
    rollback_steps: List[RollbackStep] = field(default_factory=list)
    completed_operations: List[str] = field(default_factory=list)
    backup_locations: Dict[str, str] = field(default_factory=dict)
    is_committed: bool = False
    is_rolled_back: bool = False


class ErrorIsolationManager:
    """
    Error Isolation and Rollback Manager
    
    Provides transaction-like behavior across multiple systems:
    - Tracks operations across DABS, SSCS, QuickBooks, Verifone
    - Creates rollback points before critical operations
    - Automatically rolls back on failures
    - Isolates errors to prevent cascade failures
    """
    
    def __init__(self, backup_directory: Optional[str] = None):
        self.backup_directory = Path(backup_directory or 
                                   '/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/data/rollback_backups')
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        
        # Active transactions
        self.active_transactions: Dict[str, TransactionState] = {}
        self.error_history: List[ErrorContext] = []
        
        # System health tracking
        self.system_health: Dict[SystemType, bool] = {
            SystemType.DABS: True,
            SystemType.SSCS: True,
            SystemType.QUICKBOOKS: True,
            SystemType.VERIFONE: True,
            SystemType.COORDINATOR: True
        }
        
        logger.info("Error Isolation Manager initialized")
    
    def start_transaction(self, transaction_id: str, systems: List[SystemType]) -> TransactionState:
        """Start a new transaction across multiple systems"""
        transaction = TransactionState(
            transaction_id=transaction_id,
            start_time=datetime.now(),
            systems_involved=systems
        )
        
        self.active_transactions[transaction_id] = transaction
        logger.info(f"Started transaction {transaction_id} involving systems: {[s.value for s in systems]}")
        
        return transaction
    
    def add_rollback_step(self, transaction_id: str, step: RollbackStep):
        """Add a rollback step to a transaction"""
        if transaction_id in self.active_transactions:
            self.active_transactions[transaction_id].rollback_steps.append(step)
            logger.debug(f"Added rollback step for {step.system.value}: {step.description}")
    
    def create_backup(self, transaction_id: str, file_path: Union[str, Path], 
                     backup_name: str) -> str:
        """Create a backup file for rollback purposes"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")
        
        # Create transaction-specific backup directory
        transaction_backup_dir = self.backup_directory / transaction_id
        transaction_backup_dir.mkdir(exist_ok=True)
        
        backup_path = transaction_backup_dir / f"{backup_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        
        # Track backup location
        if transaction_id in self.active_transactions:
            self.active_transactions[transaction_id].backup_locations[backup_name] = str(backup_path)
        
        logger.info(f"Created backup: {backup_path}")
        return str(backup_path)
    
    async def handle_error(self, error: Exception, system: SystemType, 
                          operation: str, transaction_id: Optional[str] = None,
                          severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                          affected_skus: List[str] = None) -> ErrorContext:
        """Handle an error with appropriate isolation and recovery"""
        
        error_context = ErrorContext(
            system=system,
            operation=operation,
            timestamp=datetime.now(),
            severity=severity,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            affected_skus=affected_skus or []
        )
        
        # Add to error history
        self.error_history.append(error_context)
        
        # Update system health
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.system_health[system] = False
            logger.error(f"System {system.value} marked as unhealthy due to {severity.value} error")
        
        # Determine recovery strategy
        recovery_suggestions = self._generate_recovery_suggestions(error_context)
        error_context.recovery_suggestions = recovery_suggestions
        
        # Auto-rollback for critical errors
        if severity == ErrorSeverity.CRITICAL and transaction_id:
            logger.critical(f"Critical error in {system.value}, initiating automatic rollback")
            await self.rollback_transaction(transaction_id)
        
        logger.error(f"Error in {system.value} during {operation}: {str(error)}")
        return error_context
    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction by executing all rollback steps in reverse order"""
        if transaction_id not in self.active_transactions:
            logger.error(f"Cannot rollback unknown transaction: {transaction_id}")
            return False
        
        transaction = self.active_transactions[transaction_id]
        if transaction.is_rolled_back:
            logger.warning(f"Transaction {transaction_id} already rolled back")
            return True
        
        logger.info(f"Starting rollback for transaction {transaction_id}")
        rollback_success = True
        
        # Execute rollback steps in reverse order
        for step in reversed(transaction.rollback_steps):
            try:
                step.execution_time = datetime.now()
                
                if step.rollback_function:
                    # Execute custom rollback function
                    await step.rollback_function(step.rollback_data)
                else:
                    # Execute standard rollback actions
                    await self._execute_standard_rollback(step, transaction)
                
                step.executed = True
                step.success = True
                logger.info(f"Rollback step completed: {step.description}")
                
            except Exception as e:
                step.executed = True
                step.success = False
                step.error_message = str(e)
                rollback_success = False
                logger.error(f"Rollback step failed: {step.description} - {str(e)}")
        
        transaction.is_rolled_back = True
        
        # Clean up transaction
        if transaction_id in self.active_transactions:
            del self.active_transactions[transaction_id]
        
        logger.info(f"Rollback {'completed' if rollback_success else 'completed with errors'} for transaction {transaction_id}")
        return rollback_success
    
    async def _execute_standard_rollback(self, step: RollbackStep, transaction: TransactionState):
        """Execute standard rollback actions"""
        if step.action == RollbackAction.FILE_RESTORE:
            # Restore file from backup
            backup_name = step.rollback_data.get('backup_name')
            target_path = step.rollback_data.get('target_path')
            
            if backup_name in transaction.backup_locations:
                backup_path = transaction.backup_locations[backup_name]
                shutil.copy2(backup_path, target_path)
                logger.info(f"Restored file from backup: {backup_path} -> {target_path}")
        
        elif step.action == RollbackAction.DATA_REVERT:
            # Revert data changes (placeholder)
            logger.info(f"Data revert for {step.system.value}: {step.description}")
        
        elif step.action == RollbackAction.API_UNDO:
            # Undo API operations (placeholder)
            logger.info(f"API undo for {step.system.value}: {step.description}")
        
        elif step.action == RollbackAction.CACHE_CLEAR:
            # Clear caches (placeholder)
            logger.info(f"Cache clear for {step.system.value}: {step.description}")
        
        elif step.action == RollbackAction.NOTIFICATION:
            # Send notifications (placeholder)
            logger.info(f"Notification sent for {step.system.value}: {step.description}")
    
    def _generate_recovery_suggestions(self, error_context: ErrorContext) -> List[str]:
        """Generate recovery suggestions based on error context"""
        suggestions = []
        
        if error_context.system == SystemType.DABS:
            suggestions.extend([
                "Verify DABS Excel file format and structure",
                "Check for missing required columns",
                "Validate price data for reasonable ranges"
            ])
        
        elif error_context.system == SystemType.SSCS:
            suggestions.extend([
                "Verify SSCS connection and credentials",
                "Check NAXML file format compliance",
                "Ensure CPB vendor import is configured"
            ])
        
        elif error_context.system == SystemType.QUICKBOOKS:
            suggestions.extend([
                "Refresh QuickBooks OAuth token",
                "Verify QuickBooks Online connectivity",
                "Check item mapping configuration"
            ])
        
        # Add severity-specific suggestions
        if error_context.severity == ErrorSeverity.CRITICAL:
            suggestions.append("Consider manual intervention and system restart")
        
        return suggestions
    
    def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a transaction (mark as successful)"""
        if transaction_id not in self.active_transactions:
            return False
        
        transaction = self.active_transactions[transaction_id]
        transaction.is_committed = True
        
        # Clean up old backups after successful commit
        self._cleanup_transaction_backups(transaction_id)
        
        # Remove from active transactions
        del self.active_transactions[transaction_id]
        
        logger.info(f"Transaction {transaction_id} committed successfully")
        return True
    
    def _cleanup_transaction_backups(self, transaction_id: str):
        """Clean up backup files for a committed transaction"""
        transaction_backup_dir = self.backup_directory / transaction_id
        if transaction_backup_dir.exists():
            shutil.rmtree(transaction_backup_dir)
            logger.debug(f"Cleaned up backups for transaction {transaction_id}")
    
    def get_system_health(self) -> Dict[SystemType, bool]:
        """Get current system health status"""
        return self.system_health.copy()
    
    def mark_system_healthy(self, system: SystemType):
        """Mark a system as healthy"""
        self.system_health[system] = True
        logger.info(f"System {system.value} marked as healthy")
    
    def get_error_history(self, limit: int = 50) -> List[ErrorContext]:
        """Get recent error history"""
        return self.error_history[-limit:]
    
    def get_active_transactions(self) -> List[TransactionState]:
        """Get all active transactions"""
        return list(self.active_transactions.values())


# Convenience functions for common rollback operations
def create_file_rollback_step(system: SystemType, file_path: str, 
                             backup_name: str) -> RollbackStep:
    """Create a file restore rollback step"""
    return RollbackStep(
        action=RollbackAction.FILE_RESTORE,
        system=system,
        description=f"Restore {file_path} from backup",
        rollback_data={
            'backup_name': backup_name,
            'target_path': file_path
        }
    )


def create_api_rollback_step(system: SystemType, operation: str,
                           rollback_function: Callable) -> RollbackStep:
    """Create an API undo rollback step"""
    return RollbackStep(
        action=RollbackAction.API_UNDO,
        system=system,
        description=f"Undo {operation}",
        rollback_function=rollback_function
    )
