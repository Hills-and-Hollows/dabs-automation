"""
Unit tests for the DABS Audit Trail System

Tests cover:
- Event logging functionality
- Data integrity verification
- Backup and archival operations
- Compliance reporting
- Error handling and edge cases
"""

import pytest
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from audit.audit_trail import AuditTrailManager, AuditEventType, AuditEvent


@pytest.mark.unit
@pytest.mark.asyncio
class TestAuditTrailManager:
    """Test suite for AuditTrailManager class"""
    
    async def test_initialization(self, temp_dir):
        """Test audit trail manager initialization"""
        audit_dir = temp_dir / "audit"
        manager = AuditTrailManager(audit_dir, retention_years=5)
        
        assert manager.audit_dir == audit_dir
        assert manager.retention_years == 5
        assert manager.db_path.exists()
        assert manager.backup_dir.exists()
        assert manager.archive_dir.exists()
        
        # Verify database schema
        with sqlite3.connect(manager.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert 'audit_events' in tables
    
    async def test_log_event(self, audit_manager):
        """Test basic event logging"""
        event_id = await audit_manager.log_event(
            event_type=AuditEventType.PRICE_CHANGE,
            source_system="TEST_SYSTEM",
            description="Test price change",
            sku="123456",
            old_value=10.00,
            new_value=12.00,
            metadata={"test": True}
        )
        
        assert event_id.startswith("AUDIT_")
        
        # Verify event was stored
        events = await audit_manager.get_audit_trail(limit=1)
        assert len(events) == 1
        
        event = events[0]
        assert event['event_type'] == 'price_change'
        assert event['source_system'] == 'TEST_SYSTEM'
        assert event['sku'] == '123456'
        assert event['description'] == 'Test price change'
    
    async def test_log_price_change(self, audit_manager):
        """Test price change logging with metadata"""
        event_id = await audit_manager.log_price_change(
            sku="789012",
            old_price=25.99,
            new_price=27.99,
            source_file="test.xlsx",
            user_id="test_user",
            metadata={"category": "whiskey"}
        )
        
        assert event_id is not None
        
        events = await audit_manager.get_audit_trail(sku="789012")
        assert len(events) == 1
        
        event = events[0]
        assert event['event_type'] == 'price_change'
        assert json.loads(event['old_value']) == 25.99
        assert json.loads(event['new_value']) == 27.99
        
        metadata = json.loads(event['metadata'])
        assert metadata['source_file'] == 'test.xlsx'
        assert metadata['price_difference'] == 2.00
        assert metadata['category'] == 'whiskey'
    
    async def test_log_file_processing(self, audit_manager):
        """Test file processing event logging"""
        event_id = await audit_manager.log_file_processing(
            file_path="test_file.xlsx",
            total_skus=100,
            processed_skus=98,
            failed_skus=2,
            processing_time=15.5,
            checksum="abc123",
            metadata={"version": "1.0"}
        )
        
        assert event_id is not None
        
        events = await audit_manager.get_audit_trail(event_type=AuditEventType.FILE_PROCESSED)
        assert len(events) == 1
        
        event = events[0]
        metadata = json.loads(event['metadata'])
        assert metadata['total_skus'] == 100
        assert metadata['processed_skus'] == 98
        assert metadata['failed_skus'] == 2
        assert metadata['processing_time_seconds'] == 15.5
        assert metadata['file_checksum'] == 'abc123'
        assert metadata['success_rate'] == 98.0
    
    async def test_log_validation_exception(self, audit_manager):
        """Test validation exception logging"""
        event_id = await audit_manager.log_validation_exception(
            sku="999999",
            exception_type="high_price_warning",
            message="Price above threshold",
            value=1500.00,
            metadata={"threshold": 1000.0}
        )
        
        assert event_id is not None
        
        events = await audit_manager.get_audit_trail(event_type=AuditEventType.VALIDATION_EXCEPTION)
        assert len(events) == 1
        
        event = events[0]
        assert event['sku'] == '999999'
        assert json.loads(event['new_value']) == 1500.00
        
        metadata = json.loads(event['metadata'])
        assert metadata['exception_type'] == 'high_price_warning'
        assert metadata['threshold'] == 1000.0
    
    async def test_get_audit_trail_filtering(self, audit_manager):
        """Test audit trail retrieval with various filters"""
        # Create test events
        await audit_manager.log_price_change("111111", 10.00, 12.00, "file1.xlsx")
        await audit_manager.log_price_change("222222", 20.00, 22.00, "file2.xlsx")
        await audit_manager.log_validation_exception("333333", "test", "message", 100.00)
        
        # Test SKU filtering
        events = await audit_manager.get_audit_trail(sku="111111")
        assert len(events) == 1
        assert events[0]['sku'] == '111111'
        
        # Test event type filtering
        events = await audit_manager.get_audit_trail(event_type=AuditEventType.PRICE_CHANGE)
        assert len(events) == 2
        assert all(e['event_type'] == 'price_change' for e in events)
        
        # Test date filtering
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        events = await audit_manager.get_audit_trail(start_date=yesterday, end_date=tomorrow)
        assert len(events) == 3  # All events should be within this range
        
        # Test limit
        events = await audit_manager.get_audit_trail(limit=2)
        assert len(events) == 2
    
    async def test_verify_audit_integrity(self, audit_manager):
        """Test audit integrity verification"""
        # Add some events
        await audit_manager.log_price_change("111111", 10.00, 12.00, "test.xlsx")
        await audit_manager.log_validation_exception("222222", "test", "message", 100.00)
        
        # Verify integrity
        result = await audit_manager.verify_audit_integrity()
        
        assert result['integrity_verified'] is True
        assert result['total_events'] == 2
        assert result['corrupted_events'] == 0
        assert len(result['corruption_details']) == 0
        assert 'verification_timestamp' in result
    
    async def test_create_backup(self, audit_manager):
        """Test backup creation"""
        # Add some events
        await audit_manager.log_price_change("111111", 10.00, 12.00, "test.xlsx")
        
        # Create backup
        backup_file = await audit_manager.create_backup()
        
        assert Path(backup_file).exists()
        assert backup_file.endswith('.db.gz')
        assert 'audit_backup_' in backup_file
        
        # Verify backup event was logged
        events = await audit_manager.get_audit_trail(event_type=AuditEventType.BACKUP_CREATED)
        assert len(events) == 1
    
    async def test_cleanup_old_records(self, audit_manager):
        """Test old record cleanup and archival"""
        # Override retention for testing (use very short retention)
        audit_manager.retention_years = 0  # Everything is "old"
        
        # Add some events
        await audit_manager.log_price_change("111111", 10.00, 12.00, "test.xlsx")
        await audit_manager.log_validation_exception("222222", "test", "message", 100.00)
        
        # Run cleanup
        result = await audit_manager.cleanup_old_records()
        
        # Should have archived and deleted records
        assert result['archived_records'] >= 2
        assert result['deleted_records'] >= 2
        assert 'archive_file' in result
        
        # Verify archive file exists
        assert Path(result['archive_file']).exists()
        
        # Verify records were deleted from database
        events = await audit_manager.get_audit_trail()
        # Should only have the cleanup event itself
        assert len(events) == 1
        assert 'Archived' in events[0]['description']
    
    async def test_generate_compliance_report(self, audit_manager):
        """Test compliance report generation"""
        # Add test events
        await audit_manager.log_price_change("111111", 10.00, 12.00, "test.xlsx")
        await audit_manager.log_price_change("222222", 20.00, 18.00, "test.xlsx")  # Price decrease
        await audit_manager.log_validation_exception("333333", "high_price", "Too high", 1500.00)
        await audit_manager.log_file_processing("test.xlsx", 100, 98, 2, 15.5, "abc123")
        
        # Generate report
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        report = await audit_manager.generate_compliance_report(
            start_date=start_date,
            end_date=end_date,
            report_type="test"
        )
        
        # Verify report structure
        assert 'report_metadata' in report
        assert 'summary' in report
        assert 'integrity_status' in report
        assert 'compliance_indicators' in report
        assert 'detailed_analysis' in report
        
        # Verify metadata
        metadata = report['report_metadata']
        assert metadata['report_type'] == 'test'
        assert 'report_id' in metadata
        assert metadata['report_id'].startswith('COMPLIANCE_')
        
        # Verify summary
        summary = report['summary']
        assert summary['total_price_changes'] == 2
        assert summary['price_increases'] == 1
        assert summary['price_decreases'] == 1
        assert summary['validation_exceptions'] == 1
        
        # Verify compliance indicators
        indicators = report['compliance_indicators']
        assert indicators['audit_trail_complete'] is True
        assert indicators['all_changes_logged'] is True
        
        # Verify report generation was logged
        events = await audit_manager.get_audit_trail(event_type=AuditEventType.COMPLIANCE_REPORT)
        assert len(events) == 1
    
    async def test_checksum_calculation(self, audit_manager):
        """Test checksum calculation for tamper detection"""
        # Log an event
        event_id = await audit_manager.log_event(
            event_type=AuditEventType.PRICE_CHANGE,
            source_system="TEST",
            description="Test event",
            sku="123456",
            old_value=10.00,
            new_value=12.00
        )
        
        # Get the event
        events = await audit_manager.get_audit_trail(limit=1)
        event = events[0]
        
        # Verify checksum exists and is not empty
        assert event['checksum']
        assert len(event['checksum']) == 64  # SHA256 hex length
        
        # Verify integrity check passes
        integrity = await audit_manager.verify_audit_integrity()
        assert integrity['integrity_verified'] is True
    
    async def test_error_handling(self, audit_manager):
        """Test error handling in various scenarios"""
        # Test with invalid event type (should still work with string conversion)
        event_id = await audit_manager.log_event(
            event_type=AuditEventType.SYSTEM_ERROR,
            source_system="TEST",
            description="Error test",
            metadata={"error": "test error"}
        )
        
        assert event_id is not None
        
        # Test with None values
        event_id = await audit_manager.log_event(
            event_type=AuditEventType.USER_ACTION,
            source_system="TEST",
            description="None test",
            user_id=None,
            sku=None,
            old_value=None,
            new_value=None,
            metadata=None
        )
        
        assert event_id is not None
        
        # Verify events were stored
        events = await audit_manager.get_audit_trail(limit=2)
        assert len(events) == 2
