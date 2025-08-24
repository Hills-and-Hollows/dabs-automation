#!/usr/bin/env python3
"""
UPC Automation Testing Framework
Comprehensive testing for UPC management and DABS processing

Created: January 23, 2025
Purpose: Validate UPC automation functionality with real SSCS data
"""

import asyncio
import pytest
import logging
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from pathlib import Path
import json
import tempfile
import os

from processors.upc_master_database import UPCMasterDatabase, UPCMasterRecord
from processors.dabs_upc_processor import DABSUPCProcessor, DABSItem
from automation.restaurant_order_automation import RestaurantOrderAutomation, RestaurantOrder
from integration_hub.sscs_ccb_client import SSCSCCBClient, SSCSInventoryItem, SSCSCaseUPC

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestUPCAutomation:
    """Test suite for UPC automation functionality"""
    
    @pytest.fixture
    async def upc_database(self):
        """Test fixture for UPC master database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = UPCMasterDatabase(temp_db.name)
            yield db
            db.close()
            os.unlink(temp_db.name)

    @pytest.fixture
    async def ccb_client(self):
        """Test fixture for SSCS CCB client"""
        client = SSCSCCBClient()
        yield client
        await client.close()

    @pytest.fixture
    def sample_dabs_items(self):
        """Sample DABS items for testing"""
        return [
            DABSItem(
                csc_code="056828",
                product_name="BACARDI MOJITO 1750ml",
                size_ml="1750",
                case_pack=6,
                status_code="U",
                category="PREMIXED - MISC",
                current_retail=22.19,
                new_retail=19.99,
                effective_date="2025-01-23"
            ),
            DABSItem(
                csc_code="012345",
                product_name="WASATCH SUMMER ALE 6PK",
                size_ml="355",
                case_pack=4,
                status_code="U", 
                category="BEER",
                current_retail=13.09,
                new_retail=12.99,
                effective_date="2025-01-23"
            )
        ]

    @pytest.fixture
    def sample_sscs_inventory(self):
        """Sample SSCS inventory items for testing"""
        return [
            SSCSInventoryItem(
                upc_code="012354001350",
                sscs_item_id="SSCS-056828",
                description="BACARDI MOJITO 1.75L",
                department="LIQUOR STORE",
                pack_size="1.75L",
                current_price=22.19
            ),
            SSCSInventoryItem(
                upc_code="015203000153",
                sscs_item_id="SSCS-015203",
                description="WASATCH SUMMER ALE 6PK",
                department="BEER-GS",
                pack_size="6PK",
                current_price=13.09
            )
        ]

class TestUPCMasterDatabase:
    """Test UPC Master Database functionality"""

    async def test_database_initialization(self, upc_database):
        """Test UPC database initialization"""
        assert upc_database.conn is not None
        
        # Test table creation
        cursor = upc_database.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'upc_master' in tables
        assert 'dabs_sscs_mapping' in tables
        assert 'case_upc_config' in tables

    async def test_ccb_inventory_sync(self, upc_database, sample_sscs_inventory):
        """Test CCB inventory synchronization"""
        # Mock CCB client to return sample inventory
        with patch.object(upc_database.ccb_client, 'get_complete_inventory_with_upcs', 
                         return_value=sample_sscs_inventory):
            
            updated_count = await upc_database.sync_with_ccb_inventory()
            assert updated_count == len(sample_sscs_inventory)
            
            # Verify data in database
            stats = upc_database.get_database_stats()
            assert stats['total_items'] >= len(sample_sscs_inventory)

    async def test_fuzzy_upc_matching(self, upc_database, sample_sscs_inventory):
        """Test fuzzy description matching for UPC lookup"""
        # Add sample data to database
        await upc_database.sync_with_ccb_inventory()
        
        # Test exact match
        exact_match = upc_database.find_upc_by_description_fuzzy("BACARDI MOJITO 1.75L")
        assert exact_match is not None
        assert exact_match.upc_code == "012354001350"
        
        # Test fuzzy match
        fuzzy_match = upc_database.find_upc_by_description_fuzzy("BACARDI MOJITO 1750ml")
        assert fuzzy_match is not None
        assert fuzzy_match.confidence_score >= 0.8

    async def test_case_upc_configuration(self, upc_database, sample_sscs_inventory):
        """Test case UPC configuration functionality"""
        # Add sample data
        await upc_database.sync_with_ccb_inventory()
        
        # Test case UPC generation for sample items
        upc_records = [
            UPCMasterRecord(
                upc_code="012354001350",
                sscs_item_id="SSCS-056828",
                description="BACARDI MOJITO 1.75L",
                department="LIQUOR STORE",
                pack_size="1.75L",
                current_price=22.19,
                confidence_score=1.0
            )
        ]
        
        with patch.object(upc_database.ccb_client, 'generate_case_upc_for_item',
                         return_value=SSCSCaseUPC(
                             case_upc="012354001350C6",
                             bottle_upc="012354001350",
                             case_pack_size=6,
                             description="BACARDI MOJITO 1.75L (6-pack case)",
                             configured_date=datetime.now(),
                             validation_status="configured"
                         )):
            
            configured_cases = await upc_database.configure_case_upcs_bulk(upc_records)
            assert len(configured_cases) == 1
            assert configured_cases[0].case_upc == "012354001350C6"

class TestDABSUPCProcessor:
    """Test DABS UPC processing functionality"""

    async def test_dabs_file_processing(self, sample_dabs_items):
        """Test DABS file processing with UPC resolution"""
        processor = DABSUPCProcessor()
        
        try:
            # Mock UPC resolution
            with patch.object(processor, '_resolve_upc_for_dabs_item',
                             return_value=UPCMasterRecord(
                                 upc_code="012354001350",
                                 sscs_item_id="SSCS-056828",
                                 description="BACARDI MOJITO 1.75L",
                                 department="LIQUOR STORE",
                                 pack_size="1.75L",
                                 current_price=22.19,
                                 confidence_score=0.95
                             )):
                
                # Mock DABS Excel loading
                with patch.object(processor, '_load_dabs_excel', return_value=sample_dabs_items):
                    
                    # Create temporary DABS file
                    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
                        result = await processor.process_dabs_file(temp_file.name, "data/test_exports")
                        
                        assert result.total_items == len(sample_dabs_items)
                        assert result.upc_resolved > 0
                        assert result.processing_time_seconds > 0
                        
                        os.unlink(temp_file.name)
        finally:
            await processor.close()

    async def test_upc_resolution_strategies(self):
        """Test different UPC resolution strategies"""
        processor = DABSUPCProcessor()
        
        try:
            sample_dabs_item = DABSItem(
                csc_code="056828",
                product_name="BACARDI MOJITO 1750ml",
                size_ml="1750",
                case_pack=6,
                status_code="U",
                category="PREMIXED - MISC",
                current_retail=22.19,
                new_retail=19.99,
                effective_date="2025-01-23"
            )
            
            # Mock UPC database responses
            with patch.object(processor.upc_db, 'get_upc_by_dabs_code', return_value=None):
                with patch.object(processor.upc_db, 'find_upc_by_description_fuzzy',
                                 return_value=UPCMasterRecord(
                                     upc_code="012354001350",
                                     sscs_item_id="SSCS-056828",
                                     description="BACARDI MOJITO 1.75L",
                                     department="LIQUOR STORE",
                                     pack_size="1.75L",
                                     current_price=22.19,
                                     confidence_score=0.85
                                 )):
                    
                    upc_record = await processor._resolve_upc_for_dabs_item(sample_dabs_item)
                    assert upc_record is not None
                    assert upc_record.upc_code == "012354001350"
                    assert upc_record.confidence_score >= 0.8
                    
        finally:
            await processor.close()

class TestRestaurantOrderAutomation:
    """Test restaurant order automation functionality"""

    async def test_restaurant_order_submission(self):
        """Test Thursday restaurant order submission"""
        automation = RestaurantOrderAutomation()
        
        try:
            sample_order_data = {
                'restaurant_name': 'Test Restaurant',
                'restaurant_contact': 'test@restaurant.com',
                'delivery_date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
                'items': [
                    {'description': 'Test Item 1', 'quantity': 2, 'case_pack': 6},
                    {'description': 'Test Item 2', 'quantity': 1, 'case_pack': 4}
                ],
                'total_amount': 150.00,
                'payment_method': 'credit_card',
                'credit_card_last_four': '1234'
            }
            
            # Mock inventory validation
            with patch.object(automation, '_validate_order_against_inventory',
                             return_value={'valid': True, 'errors': [], 'warnings': []}):
                
                order_id = await automation.process_thursday_order_submission(sample_order_data)
                assert order_id != ""
                assert order_id.startswith("REST_")
                
                # Verify order stored
                assert order_id in automation.restaurant_orders
                stored_order = automation.restaurant_orders[order_id]
                assert stored_order.restaurant_name == 'Test Restaurant'
                assert stored_order.processing_fee > 0  # Credit card fee calculated
                
        finally:
            await automation.close()

    async def test_friday_confirmation_workflow(self):
        """Test Friday confirmation processing"""
        automation = RestaurantOrderAutomation()
        
        try:
            # Create sample order for Friday confirmation
            order_id = "TEST_ORDER_123"
            test_order = RestaurantOrder(
                order_id=order_id,
                restaurant_name="Test Restaurant",
                restaurant_contact="test@restaurant.com",
                order_date=datetime.now() - timedelta(days=1),
                requested_delivery_date=datetime.now() + timedelta(days=4),  # Next Tuesday
                items=[{'description': 'Test Item', 'quantity': 1, 'case_pack': 6}],
                total_amount=100.00,
                payment_method='credit_card',
                processing_fee=2.50,
                order_status='submitted'
            )
            
            automation.restaurant_orders[order_id] = test_order
            
            # Mock UPC configuration and payment processing
            with patch.object(automation, '_preconfigure_case_upcs_for_order',
                             return_value=[SSCSCaseUPC(
                                 case_upc="TEST123C6",
                                 bottle_upc="TEST123",
                                 case_pack_size=6,
                                 description="Test Item (6-pack case)",
                                 configured_date=datetime.now(),
                                 validation_status="configured"
                             )]):
                with patch.object(automation, '_process_restaurant_payment', return_value=True):
                    
                    result = await automation.process_friday_confirmation()
                    assert result.total_orders >= 1
                    assert result.successfully_processed >= 1
                    assert result.upcs_configured >= 1
                    assert result.payment_processed >= 1
                    
        finally:
            await automation.close()

class TestIntegrationWorkflow:
    """Test complete integration workflow"""

    async def test_complete_upc_workflow(self):
        """Test complete UPC workflow from DABS to restaurant delivery"""
        # Initialize components
        upc_db = UPCMasterDatabase()
        dabs_processor = DABSUPCProcessor()
        restaurant_automation = RestaurantOrderAutomation()
        
        try:
            print("=== Testing Complete UPC Workflow ===")
            
            # Step 1: Initialize UPC database with sample data
            print("\n1. Initializing UPC database...")
            sample_inventory = [
                SSCSInventoryItem(
                    upc_code="012354001350",
                    sscs_item_id="SSCS-056828",
                    description="BACARDI MOJITO 1.75L",
                    department="LIQUOR STORE",
                    pack_size="1.75L",
                    current_price=22.19
                )
            ]
            
            with patch.object(upc_db.ccb_client, 'get_complete_inventory_with_upcs',
                             return_value=sample_inventory):
                sync_count = await upc_db.sync_with_ccb_inventory()
                print(f"✅ UPC database synced: {sync_count} items")
            
            # Step 2: Process DABS file with UPC resolution
            print("\n2. Processing DABS file...")
            sample_dabs = [
                DABSItem(
                    csc_code="056828",
                    product_name="BACARDI MOJITO 1750ml", 
                    size_ml="1750",
                    case_pack=6,
                    status_code="U",
                    category="PREMIXED - MISC",
                    current_retail=22.19,
                    new_retail=19.99,
                    effective_date="2025-01-23"
                )
            ]
            
            with patch.object(dabs_processor, '_load_dabs_excel', return_value=sample_dabs):
                with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
                    result = await dabs_processor.process_dabs_file(temp_file.name, "data/test_exports")
                    print(f"✅ DABS processing: {result.successfully_processed}/{result.total_items} items")
                    print(f"   UPCs resolved: {result.upc_resolved}")
                    print(f"   Case UPCs configured: {result.case_upcs_configured}")
                    
                    os.unlink(temp_file.name)
            
            # Step 3: Restaurant order processing
            print("\n3. Testing restaurant order processing...")
            sample_order = {
                'restaurant_name': 'Test Bistro',
                'restaurant_contact': 'manager@testbistro.com',
                'delivery_date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
                'items': [
                    {'description': 'BACARDI MOJITO 1750ml', 'quantity': 1, 'case_pack': 6}
                ],
                'total_amount': 19.99,
                'payment_method': 'credit_card'
            }
            
            with patch.object(restaurant_automation, '_validate_order_against_inventory',
                             return_value={'valid': True, 'errors': []}):
                order_id = await restaurant_automation.process_thursday_order_submission(sample_order)
                print(f"✅ Restaurant order processed: {order_id}")
            
            # Step 4: Friday confirmation with UPC integration
            print("\n4. Testing Friday confirmation...")
            with patch.object(restaurant_automation, '_preconfigure_case_upcs_for_order',
                             return_value=[SSCSCaseUPC(
                                 case_upc="012354001350C6",
                                 bottle_upc="012354001350",
                                 case_pack_size=6,
                                 description="BACARDI MOJITO 1.75L (6-pack case)",
                                 configured_date=datetime.now(),
                                 validation_status="configured"
                             )]):
                with patch.object(restaurant_automation, '_process_restaurant_payment', return_value=True):
                    friday_result = await restaurant_automation.process_friday_confirmation()
                    print(f"✅ Friday confirmation: {friday_result.successfully_processed} orders confirmed")
                    print(f"   UPCs configured: {friday_result.upcs_configured}")
                    print(f"   Payments processed: {friday_result.payment_processed}")
            
            # Step 5: Tuesday delivery optimization
            print("\n5. Testing Tuesday delivery...")
            delivery_result = await restaurant_automation.process_tuesday_delivery_optimization()
            print(f"✅ Tuesday delivery: {delivery_result.get('pickup_ready', 0)} orders ready")
            
            print("\n✅ Complete UPC workflow test successful!")
            return True
            
        except Exception as e:
            print(f"❌ Complete workflow test failed: {e}")
            return False
            
        finally:
            await upc_db.ccb_client.close()
            await dabs_processor.close()
            await restaurant_automation.close()
            upc_db.close()

class TestRealSSCSDataIntegration:
    """Test integration with real SSCS data from /dabs folder"""

    async def test_process_inventory_csv_parsing(self):
        """Test parsing of actual ProcessInventory.csv file"""
        upc_db = UPCMasterDatabase()
        
        try:
            # Test with real ProcessInventory.csv if available
            process_inventory_path = "/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/dabs/ProcessInventory.csv"
            
            if Path(process_inventory_path).exists():
                print(f"\nTesting real ProcessInventory.csv: {process_inventory_path}")
                
                # Load and validate real data
                validated_count, variances = upc_db.validate_with_export_data(process_inventory_path)
                print(f"✅ Real data validation: {validated_count} items, {variances} variances")
                
                # Get liquor items from real data
                liquor_items = upc_db.get_all_liquor_upcs()
                print(f"✅ Liquor items found: {len(liquor_items)}")
                
                # Test UPC lookup with real descriptions
                if liquor_items:
                    sample_item = liquor_items[0]
                    fuzzy_match = upc_db.find_upc_by_description_fuzzy(sample_item.description)
                    print(f"✅ Fuzzy match test: {fuzzy_match.confidence_score:.2f} confidence" if fuzzy_match else "❌ Fuzzy match failed")
                
                # Export summary for review
                summary_path = "data/test_results/real_sscs_upc_summary.json"
                Path(summary_path).parent.mkdir(parents=True, exist_ok=True)
                success = upc_db.export_upc_summary_report(summary_path)
                print(f"✅ Summary exported: {summary_path}" if success else "❌ Summary export failed")
                
                return True
            else:
                print(f"❌ ProcessInventory.csv not found: {process_inventory_path}")
                return False
                
        except Exception as e:
            print(f"❌ Real SSCS data test failed: {e}")
            return False
            
        finally:
            await upc_db.ccb_client.close()
            upc_db.close()

    async def test_dabs_mapping_integration(self):
        """Test integration with real DABS mapping file"""
        upc_db = UPCMasterDatabase()
        
        try:
            # Test with real DABS mapping if available
            mapping_path = "/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/dabs/DABS_to_SSCS_Mapping_Workbook.csv"
            
            if Path(mapping_path).exists():
                print(f"\nTesting real DABS mapping: {mapping_path}")
                
                # Load real mapping data
                mapped_count = upc_db.load_dabs_mapping(mapping_path)
                print(f"✅ DABS mapping loaded: {mapped_count} mappings")
                
                # Test DABS code lookup
                if mapped_count > 0:
                    # Test lookup with known DABS code
                    test_upc = upc_db.get_upc_by_dabs_code("056828")
                    print(f"✅ DABS lookup test: {'Success' if test_upc else 'No match found'}")
                
                return True
            else:
                print(f"❌ DABS mapping file not found: {mapping_path}")
                return False
                
        except Exception as e:
            print(f"❌ Real DABS mapping test failed: {e}")
            return False
            
        finally:
            await upc_db.ccb_client.close()
            upc_db.close()

# Performance testing
class TestUPCPerformance:
    """Performance testing for UPC automation"""

    async def test_bulk_upc_processing_performance(self):
        """Test performance of bulk UPC processing"""
        upc_db = UPCMasterDatabase()
        
        try:
            start_time = datetime.now()
            
            # Test with simulated large dataset
            sample_size = 1000
            sample_items = []
            for i in range(sample_size):
                item = SSCSInventoryItem(
                    upc_code=f"01234567890{i:02d}",
                    sscs_item_id=f"SSCS-{i:05d}",
                    description=f"Test Product {i}",
                    department="LIQUOR STORE",
                    pack_size="750ml",
                    current_price=25.99
                )
                sample_items.append(item)
            
            # Mock CCB client for performance test
            with patch.object(upc_db.ccb_client, 'get_complete_inventory_with_upcs',
                             return_value=sample_items):
                
                sync_count = await upc_db.sync_with_ccb_inventory()
                processing_time = (datetime.now() - start_time).total_seconds()
                
                print(f"\n=== Performance Test Results ===")
                print(f"Items processed: {sync_count}")
                print(f"Processing time: {processing_time:.2f} seconds")
                print(f"Items per second: {sync_count/processing_time:.1f}")
                
                # Performance assertions
                assert processing_time < 30  # Should complete within 30 seconds
                assert sync_count == sample_size
                
                return True
                
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            return False
            
        finally:
            await upc_db.ccb_client.close()
            upc_db.close()

# Run all tests
async def run_all_tests():
    """Run comprehensive UPC automation test suite"""
    print("🧪 Starting UPC Automation Test Suite")
    print("="*50)
    
    test_results = []
    
    # Test 1: Real SSCS data integration
    print("\n📊 Testing Real SSCS Data Integration...")
    real_data_test = TestRealSSCSDataIntegration()
    result1 = await real_data_test.test_process_inventory_csv_parsing()
    test_results.append(("Real ProcessInventory.csv Test", result1))
    
    result2 = await real_data_test.test_dabs_mapping_integration()
    test_results.append(("Real DABS Mapping Test", result2))
    
    # Test 2: Complete workflow integration
    print("\n🔄 Testing Complete Workflow Integration...")
    workflow_test = TestIntegrationWorkflow()
    result3 = await workflow_test.test_complete_upc_workflow()
    test_results.append(("Complete UPC Workflow Test", result3))
    
    # Test 3: Performance testing
    print("\n⚡ Testing Performance...")
    performance_test = TestUPCPerformance()
    result4 = await performance_test.test_bulk_upc_processing_performance()
    test_results.append(("Bulk Processing Performance Test", result4))
    
    # Summary
    print("\n" + "="*50)
    print("🧪 Test Suite Results Summary")
    print("="*50)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nOverall: {passed}/{len(test_results)} tests passed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - UPC Automation ready for production!")
    else:
        print(f"⚠️  {failed} tests failed - review before production deployment")
    
    return failed == 0

if __name__ == "__main__":
    asyncio.run(run_all_tests())
