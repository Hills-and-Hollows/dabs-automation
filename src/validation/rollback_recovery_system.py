#!/usr/bin/env python3
"""
Automated Rollback and Recovery System
Provides transaction-style rollback for DABS processing failures

This system ensures data integrity by implementing database-style transactions
for DABS order processing, with automatic rollback on validation failures.

Business Context:
- Prevents partial processing states that corrupt data
- Ensures atomic operations for Order 233808 prevention
- Maintains system integrity during failures
- Provides recovery mechanisms for Utah Package Agency compliance
"""

import logging
import json
import shutil
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from contextlib import asynccontextmanager
import sqlite3
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionState(Enum):
    """Transaction state enumeration"""
    STARTED = "started"
    CHECKPOINT = "checkpoint"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"

@dataclass
class Checkpoint:
    """Processing checkpoint for rollback"""
    checkpoint_id: str
    stage: str
    timestamp: str
    data_snapshot: Dict[str, Any]
    file_backups: List[str]
    database_state: Optional[Dict[str, Any]] = None

@dataclass
class Transaction:
    """Processing transaction with rollback capability"""
    transaction_id: str
    start_time: str
    state: TransactionState
    checkpoints: List[Checkpoint]
    operations: List[Dict[str, Any]]
    rollback_actions: List[Callable]
    metadata: Dict[str, Any]

class RollbackRecoverySystem:
    """
    Automated rollback and recovery system
    
    Provides:
    1. Transaction-style processing with rollback capability
    2. Checkpoint system for granular recovery
    3. Automatic file and database state management
    4. Recovery procedures for common failure scenarios
    """
    
    def __init__(self, backup_dir: str = "data/backups", db_path: str = "data/transactions.db"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.active_transactions = {}
        self._init_database()
        
    def _init_database(self):
        """Initialize transaction database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    start_time TEXT NOT NULL,
                    state TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    transaction_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data_snapshot TEXT,
                    file_backups TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS operations (
                    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    operation_data TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id)
                )
            ''')
            
            conn.commit()
    
    def generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"TXN_{timestamp}_{hash(str(datetime.now())) % 10000:04d}"
    
    def generate_checkpoint_id(self, transaction_id: str, stage: str) -> str:
        """Generate unique checkpoint ID"""
        timestamp = datetime.now().strftime("%H%M%S")
        return f"{transaction_id}_CP_{stage}_{timestamp}"
    
    @asynccontextmanager
    async def transaction(self, metadata: Optional[Dict[str, Any]] = None):
        """
        Async context manager for transactional processing
        
        Usage:
            async with rollback_system.transaction({'order_id': '233813'}) as txn:
                # Processing operations
                await txn.checkpoint('validation')
                # More operations
                await txn.checkpoint('conversion')
                # Transaction commits automatically on success
        """
        transaction_id = self.generate_transaction_id()
        start_time = datetime.now().isoformat()
        
        transaction = Transaction(
            transaction_id=transaction_id,
            start_time=start_time,
            state=TransactionState.STARTED,
            checkpoints=[],
            operations=[],
            rollback_actions=[],
            metadata=metadata or {}
        )
        
        self.active_transactions[transaction_id] = transaction
        
        # Save transaction to database
        await self._save_transaction(transaction)
        
        logger.info(f"🔄 Transaction started: {transaction_id}")
        
        try:
            # Yield transaction manager
            txn_manager = TransactionManager(self, transaction)
            yield txn_manager
            
            # Commit transaction on successful completion
            await self._commit_transaction(transaction)
            logger.info(f"✅ Transaction committed: {transaction_id}")
            
        except Exception as e:
            logger.error(f"❌ Transaction failed: {transaction_id} - {e}")
            await self._rollback_transaction(transaction)
            raise
        
        finally:
            # Clean up active transaction
            if transaction_id in self.active_transactions:
                del self.active_transactions[transaction_id]
    
    async def _save_transaction(self, transaction: Transaction):
        """Save transaction to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO transactions 
                (transaction_id, start_time, state, metadata)
                VALUES (?, ?, ?, ?)
            ''', (
                transaction.transaction_id,
                transaction.start_time,
                transaction.state.value,
                json.dumps(transaction.metadata, default=str)
            ))
            conn.commit()
    
    async def _commit_transaction(self, transaction: Transaction):
        """Commit transaction and clean up backups"""
        transaction.state = TransactionState.COMMITTED
        await self._save_transaction(transaction)
        
        # Clean up backup files (keep for audit trail)
        # In production, you might want to move to archive instead of delete
        logger.info(f"📋 Transaction {transaction.transaction_id} committed - {len(transaction.checkpoints)} checkpoints preserved")
    
    async def _rollback_transaction(self, transaction: Transaction):
        """Rollback transaction to last checkpoint or initial state"""
        logger.warning(f"🔄 Rolling back transaction: {transaction.transaction_id}")
        
        transaction.state = TransactionState.ROLLED_BACK
        
        try:
            # Execute rollback actions in reverse order
            for rollback_action in reversed(transaction.rollback_actions):
                try:
                    if asyncio.iscoroutinefunction(rollback_action):
                        await rollback_action()
                    else:
                        rollback_action()
                except Exception as e:
                    logger.error(f"❌ Rollback action failed: {e}")
            
            # Restore files from last checkpoint
            if transaction.checkpoints:
                last_checkpoint = transaction.checkpoints[-1]
                await self._restore_checkpoint(last_checkpoint)
            
            logger.info(f"✅ Transaction rolled back: {transaction.transaction_id}")
            
        except Exception as e:
            transaction.state = TransactionState.FAILED
            logger.error(f"❌ Rollback failed: {transaction.transaction_id} - {e}")
        
        await self._save_transaction(transaction)
    
    async def _restore_checkpoint(self, checkpoint: Checkpoint):
        """Restore system state from checkpoint"""
        logger.info(f"🔄 Restoring checkpoint: {checkpoint.checkpoint_id}")
        
        # Restore file backups
        for backup_path in checkpoint.file_backups:
            try:
                backup_file = Path(backup_path)
                if backup_file.exists():
                    # Extract original path from backup filename
                    original_path = self._get_original_path_from_backup(backup_path)
                    if original_path:
                        shutil.copy2(backup_file, original_path)
                        logger.info(f"📁 Restored file: {original_path}")
            except Exception as e:
                logger.error(f"❌ Failed to restore file {backup_path}: {e}")
        
        logger.info(f"✅ Checkpoint restored: {checkpoint.checkpoint_id}")
    
    def _get_original_path_from_backup(self, backup_path: str) -> Optional[str]:
        """Extract original file path from backup filename"""
        backup_file = Path(backup_path)
        
        # Backup filename format: original_filename_YYYYMMDD_HHMMSS_checkpoint.ext
        parts = backup_file.stem.split('_')
        if len(parts) >= 4:
            # Remove timestamp and checkpoint suffix to get original name
            original_name = '_'.join(parts[:-3]) + backup_file.suffix
            return str(backup_file.parent.parent / original_name)
        
        return None
    
    async def create_checkpoint(self, 
                              transaction: Transaction,
                              stage: str,
                              data_snapshot: Dict[str, Any],
                              files_to_backup: List[str] = None) -> Checkpoint:
        """Create processing checkpoint for rollback"""
        checkpoint_id = self.generate_checkpoint_id(transaction.transaction_id, stage)
        timestamp = datetime.now().isoformat()
        
        # Backup files
        file_backups = []
        if files_to_backup:
            for file_path in files_to_backup:
                backup_path = await self._backup_file(file_path, checkpoint_id)
                if backup_path:
                    file_backups.append(backup_path)
        
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            stage=stage,
            timestamp=timestamp,
            data_snapshot=data_snapshot,
            file_backups=file_backups
        )
        
        transaction.checkpoints.append(checkpoint)
        transaction.state = TransactionState.CHECKPOINT
        
        # Save checkpoint to database
        await self._save_checkpoint(checkpoint, transaction.transaction_id)
        
        logger.info(f"📍 Checkpoint created: {checkpoint_id} ({stage})")
        return checkpoint
    
    async def _backup_file(self, file_path: str, checkpoint_id: str) -> Optional[str]:
        """Create backup of file for rollback"""
        try:
            source_file = Path(file_path)
            if not source_file.exists():
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{source_file.stem}_{timestamp}_{checkpoint_id}{source_file.suffix}"
            backup_path = self.backup_dir / backup_filename
            
            shutil.copy2(source_file, backup_path)
            logger.info(f"📁 File backed up: {file_path} → {backup_path}")
            
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to backup file {file_path}: {e}")
            return None
    
    async def _save_checkpoint(self, checkpoint: Checkpoint, transaction_id: str):
        """Save checkpoint to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO checkpoints 
                (checkpoint_id, transaction_id, stage, timestamp, data_snapshot, file_backups)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                checkpoint.checkpoint_id,
                transaction_id,
                checkpoint.stage,
                checkpoint.timestamp,
                json.dumps(checkpoint.data_snapshot, default=str),
                json.dumps(checkpoint.file_backups)
            ))
            conn.commit()
    
    def add_rollback_action(self, transaction: Transaction, action: Callable):
        """Add rollback action to transaction"""
        transaction.rollback_actions.append(action)
        logger.info(f"📋 Rollback action added to transaction: {transaction.transaction_id}")
    
    async def recover_failed_transaction(self, transaction_id: str) -> bool:
        """Attempt to recover a failed transaction"""
        logger.info(f"🔄 Attempting recovery for transaction: {transaction_id}")
        
        try:
            # Load transaction from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT * FROM transactions WHERE transaction_id = ?
                ''', (transaction_id,))
                
                row = cursor.fetchone()
                if not row:
                    logger.error(f"❌ Transaction not found: {transaction_id}")
                    return False
                
                # Load checkpoints
                cursor = conn.execute('''
                    SELECT * FROM checkpoints WHERE transaction_id = ?
                    ORDER BY created_at DESC
                ''', (transaction_id,))
                
                checkpoint_rows = cursor.fetchall()
                
                if checkpoint_rows:
                    # Restore from most recent checkpoint
                    checkpoint_data = checkpoint_rows[0]
                    checkpoint = Checkpoint(
                        checkpoint_id=checkpoint_data[0],
                        stage=checkpoint_data[2],
                        timestamp=checkpoint_data[3],
                        data_snapshot=json.loads(checkpoint_data[4]),
                        file_backups=json.loads(checkpoint_data[5])
                    )
                    
                    await self._restore_checkpoint(checkpoint)
                    logger.info(f"✅ Transaction recovered: {transaction_id}")
                    return True
                else:
                    logger.warning(f"⚠️ No checkpoints found for transaction: {transaction_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Recovery failed for transaction {transaction_id}: {e}")
            return False
    
    def get_transaction_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get transaction history for monitoring"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT t.*, COUNT(c.checkpoint_id) as checkpoint_count
                FROM transactions t
                LEFT JOIN checkpoints c ON t.transaction_id = c.transaction_id
                GROUP BY t.transaction_id
                ORDER BY t.created_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            return [
                {
                    'transaction_id': row[0],
                    'start_time': row[1],
                    'state': row[2],
                    'metadata': json.loads(row[3]) if row[3] else {},
                    'checkpoint_count': row[5],
                    'created_at': row[4]
                }
                for row in rows
            ]

class TransactionManager:
    """Transaction manager for use within transaction context"""
    
    def __init__(self, rollback_system: RollbackRecoverySystem, transaction: Transaction):
        self.rollback_system = rollback_system
        self.transaction = transaction
    
    async def checkpoint(self, 
                        stage: str, 
                        data_snapshot: Dict[str, Any] = None,
                        files_to_backup: List[str] = None):
        """Create checkpoint in current transaction"""
        return await self.rollback_system.create_checkpoint(
            self.transaction,
            stage,
            data_snapshot or {},
            files_to_backup or []
        )
    
    def add_rollback_action(self, action: Callable):
        """Add rollback action to current transaction"""
        self.rollback_system.add_rollback_action(self.transaction, action)
    
    def log_operation(self, operation_type: str, operation_data: Dict[str, Any] = None):
        """Log operation in current transaction"""
        operation = {
            'type': operation_type,
            'data': operation_data or {},
            'timestamp': datetime.now().isoformat()
        }
        self.transaction.operations.append(operation)
        
        logger.info(f"📋 Operation logged: {operation_type} in {self.transaction.transaction_id}")

# Example usage and testing
async def example_order_processing():
    """Example of using rollback system for order processing"""
    rollback_system = RollbackRecoverySystem()
    
    try:
        async with rollback_system.transaction({'order_id': '233813'}) as txn:
            # Stage 1: Data validation
            await txn.checkpoint('validation', {'items_count': 13})
            txn.log_operation('data_validation', {'status': 'passed'})
            
            # Simulate file creation that needs rollback
            test_file = Path("test_processing_file.txt")
            test_file.write_text("Processing data...")
            txn.add_rollback_action(lambda: test_file.unlink() if test_file.exists() else None)
            
            # Stage 2: Conversion
            await txn.checkpoint('conversion', 
                                {'conversions': 13}, 
                                files_to_backup=[str(test_file)])
            txn.log_operation('case_unit_conversion', {'conversions': 13})
            
            # Stage 3: NAXML generation
            await txn.checkpoint('naxml_generation', {'naxml_file': 'output.xml'})
            txn.log_operation('naxml_generation', {'output': 'output.xml'})
            
            # Simulate processing success
            logger.info("✅ Order processing completed successfully")
            
    except Exception as e:
        logger.error(f"❌ Order processing failed: {e}")
        # Rollback happens automatically

if __name__ == "__main__":
    # Test the rollback system
    asyncio.run(example_order_processing())
    
    # Show transaction history
    rollback_system = RollbackRecoverySystem()
    history = rollback_system.get_transaction_history(10)
    
    print("\n📊 Transaction History:")
    for txn in history:
        print(f"  {txn['transaction_id']}: {txn['state']} ({txn['checkpoint_count']} checkpoints)")
