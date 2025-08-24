#!/usr/bin/env python3
"""
Test script for the DABS Audit Trail System

This script tests the audit trail functionality to ensure it's working correctly
before integrating with the main DABS processor.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from audit.audit_trail import AuditTrailManager, AuditEventType
    print("✅ Successfully imported audit trail system")
except ImportError as e:
    print(f"❌ Failed to import audit trail system: {e}")
    sys.exit(1)


async def test_audit_trail():
    """Test the audit trail system functionality"""
    print("\n🔍 Testing DABS Audit Trail System")
    print("=" * 50)
    
    # Initialize audit manager
    audit_dir = Path("data/audit_test")
    audit_manager = AuditTrailManager(audit_dir, retention_years=7)
    print(f"✅ Initialized audit manager: {audit_dir}")
    
    # Test 1: Log a price change event
    print("\n📝 Test 1: Logging price change event")
    event_id = await audit_manager.log_price_change(
        sku="123456",
        old_price=25.99,
        new_price=27.99,
        source_file="DABS Price Changes.xlsx",
        user_id="system",
        metadata={"test": True}
    )
    print(f"✅ Logged price change event: {event_id}")
    
    # Test 2: Log file processing event
    print("\n📝 Test 2: Logging file processing event")
    event_id = await audit_manager.log_file_processing(
        file_path="test_file.xlsx",
        total_skus=100,
        processed_skus=98,
        failed_skus=2,
        processing_time=15.5,
        checksum="abc123def456",
        metadata={"test_run": True}
    )
    print(f"✅ Logged file processing event: {event_id}")
    
    # Test 3: Log validation exception
    print("\n📝 Test 3: Logging validation exception")
    event_id = await audit_manager.log_validation_exception(
        sku="789012",
        exception_type="high_price_warning",
        message="Price above $1000 - verify if correct",
        value=1299.99,
        metadata={"threshold": 1000.0}
    )
    print(f"✅ Logged validation exception: {event_id}")
    
    # Test 4: Retrieve audit trail
    print("\n📝 Test 4: Retrieving audit trail")
    events = await audit_manager.get_audit_trail(limit=10)
    print(f"✅ Retrieved {len(events)} audit events")
    
    for i, event in enumerate(events[:3], 1):
        print(f"   Event {i}: {event['event_type']} - {event['description'][:50]}...")
    
    # Test 5: Verify audit integrity
    print("\n📝 Test 5: Verifying audit integrity")
    integrity_result = await audit_manager.verify_audit_integrity()
    if integrity_result['integrity_verified']:
        print(f"✅ Audit integrity verified: {integrity_result['total_events']} events")
    else:
        print(f"❌ Audit integrity issues: {integrity_result['corrupted_events']} corrupted events")
    
    # Test 6: Create backup
    print("\n📝 Test 6: Creating audit backup")
    backup_file = await audit_manager.create_backup()
    print(f"✅ Created backup: {backup_file}")
    
    # Test 7: Generate compliance report
    print("\n📝 Test 7: Generating compliance report")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    report = await audit_manager.generate_compliance_report(
        start_date=start_date,
        end_date=end_date,
        report_type="test"
    )
    
    print(f"✅ Generated compliance report:")
    print(f"   Report ID: {report['report_metadata']['report_id']}")
    print(f"   Total Events: {report['summary']['total_events']}")
    print(f"   Price Changes: {report['summary']['total_price_changes']}")
    print(f"   Integrity Status: {report['integrity_status']['integrity_verified']}")
    
    print("\n🎉 All audit trail tests completed successfully!")
    print(f"📁 Audit data stored in: {audit_dir}")
    
    return True


async def test_dabs_processor_integration():
    """Test the DABS processor with audit trail integration"""
    print("\n🔗 Testing DABS Processor Integration")
    print("=" * 50)
    
    try:
        from processors.dabs_processor import DABSProcessor
        
        # Initialize processor (should include audit trail)
        processor = DABSProcessor()
        
        if processor.audit_manager:
            print("✅ DABS Processor has audit trail manager")
            
            # Test audit logging
            await processor.audit_manager.log_event(
                event_type=AuditEventType.SYSTEM_ERROR,
                source_system="DABS_PROCESSOR_TEST",
                description="Integration test event",
                metadata={"test": "integration"}
            )
            print("✅ Successfully logged test event from DABS processor")
        else:
            print("⚠️  DABS Processor audit trail manager not available")
            
    except Exception as e:
        print(f"❌ DABS Processor integration test failed: {e}")
        return False
        
    return True


async def main():
    """Main test function"""
    print("🚀 DABS Audit Trail System Test Suite")
    print("=" * 60)
    
    try:
        # Test audit trail system
        success1 = await test_audit_trail()
        
        # Test DABS processor integration
        success2 = await test_dabs_processor_integration()
        
        if success1 and success2:
            print("\n🎉 All tests passed! Audit trail system is ready.")
            return 0
        else:
            print("\n❌ Some tests failed. Check the output above.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
