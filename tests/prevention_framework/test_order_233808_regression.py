#!/usr/bin/env python3
"""
Order 233808 Regression Test Suite
Comprehensive tests to prevent similar failures

This test suite implements regression tests based on the specific failure
patterns identified in Order 233808 analysis to ensure they never happen again.

Business Context:
- Prevents $320+ data loss incidents like Crown Royal + Squatters
- Ensures Utah Package Agency compliance through comprehensive testing
- Validates all prevention framework components work together
- Provides confidence in $28,000 annual automation value delivery
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any

# Import prevention framework components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.validation.source_data_validator import SourceDataValidator, DataItem, ValidationResult
from src.validation.case_unit_converter import CaseUnitConverter, ConversionResult
from src.validation.sscs_validator import SSCSValidator, SSCSValidationResult
from src.validation.rollback_recovery_system import RollbackRecoverySystem
from src.validation.vendor_mapping_system import VendorMappingSystem, VendorMapping
from src.validation.prevention_framework_orchestrator import PreventionFrameworkOrchestrator

class TestOrder233808Regression:
    """
    Regression tests for Order 233808 prevention
    
    Tests all identified failure scenarios:
    1. Data extraction completeness failures
    2. Case-to-unit conversion errors
    3. SSCS validation failures
    4. Vendor mapping issues
    5. End-to-end processing integrity
    """
    
    @pytest.fixture
    def order_233808_data(self):
        """Order 233808 test data that caused original failure"""
        return [
            {
                'id': '001',
                'name': 'Crown Royal Regal Apple',
                'category': 'Spirits',
                'quantity': 1,
                'unit_price': 359.88,
                'total_price': 359.88
            },
            {
                'id': '002', 
                'name': 'Squatters Hazy Hop',
                'category': 'Beer',
                'quantity': 1,
                'unit_price': 50.16,
                'total_price': 50.16
            },
            {
                'id': '003',
                'name': 'Other Test Item',
                'category': 'Wine',
                'quantity': 2,
                'unit_price': 19.99,
                'total_price': 39.98
            }
        ]
    
    @pytest.fixture
    def source_validator(self):
        """Source data validator instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield SourceDataValidator(temp_dir)
    
    @pytest.fixture
    def case_converter(self):
        """Case-to-unit converter instance"""
        yield CaseUnitConverter()
    
    @pytest.fixture
    def sscs_validator(self):
        """SSCS validator instance"""
        yield SSCSValidator()
    
    @pytest.fixture
    def vendor_mapper(self):
        """Vendor mapping system instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_mappings.db"
            yield VendorMappingSystem(str(db_path))
    
    @pytest.fixture
    def rollback_system(self):
        """Rollback recovery system instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            db_path = Path(temp_dir) / "transactions.db"
            yield RollbackRecoverySystem(str(backup_dir), str(db_path))
    
    def test_data_extraction_completeness_failure_prevention(self, source_validator, order_233808_data):
        """
        Test: Prevent data extraction completeness failures
        
        Scenario: Order 233808 lost Crown Royal Regal Apple ($359.88) and 
        Squatters Hazy Hop ($50.16) during extraction
        
        Expected: Validation must detect and prevent any data loss
        """
        # Convert to DataItem format
        source_items = [
            DataItem(
                id=item['id'],
                name=item['name'],
                quantity=item['quantity'],
                unit_price=Decimal(str(item['unit_price'])),
                total_price=Decimal(str(item['total_price'])),
                category=item['category']
            )
            for item in order_233808_data
        ]
        
        # Simulate extraction that loses items (Order 233808 failure scenario)
        extracted_items_with_loss = [source_items[2]]  # Only keep "Other Test Item"
        
        # Test validation detects data loss
        result = source_validator.validate_extraction_completeness(
            source_items, extracted_items_with_loss, "test_extraction"
        )
        
        # Assertions
        assert not result.success, "Validation should fail when items are lost"
        assert len(result.missing_items) == 2, "Should detect 2 missing items"
        assert "Crown Royal Regal Apple" in str(result.missing_items)
        assert "Squatters Hazy Hop" in str(result.missing_items)
        assert abs(result.total_expected - result.total_found) > Decimal('400'), "Should detect significant total difference"
        
        # Test validation passes with complete extraction
        extracted_items_complete = source_items.copy()
        result_complete = source_validator.validate_extraction_completeness(
            source_items, extracted_items_complete, "test_extraction_complete"
        )
        
        assert result_complete.success, "Validation should pass with complete data"
        assert len(result_complete.missing_items) == 0, "Should have no missing items"
        assert result_complete.total_expected == result_complete.total_found, "Totals should match"
    
    def test_case_unit_conversion_accuracy(self, case_converter):
        """
        Test: Ensure case-to-unit conversion accuracy
        
        Scenario: Prevent pricing errors from case/unit confusion
        Expected: All conversions must maintain mathematical integrity
        """
        test_items = [
            {
                'id': '917817',
                'name': 'RED ROCK ELEPHINO IPA 500ml',
                'category': 'Beer',
                'quantity': 4,
                'unit_price': 48.48
            },
            {
                'id': '039271',
                'name': 'SUGAR HOUSE VODKA 1000ml',
                'category': 'Spirits', 
                'quantity': 1,
                'unit_price': 131.94
            }
        ]
        
        # Test batch conversion
        results = case_converter.batch_convert(test_items)
        
        # Assertions
        assert len(results) == len(test_items), "All items should be converted"
        
        for i, result in enumerate(results):
            original_item = test_items[i]
            
            # Mathematical integrity check
            assert result.original_total == result.converted_total, f"Total price must be preserved for item {result.original_item_id}"
            
            # Conversion logic validation
            if "500ml" in original_item['name'] and "beer" in original_item['category'].lower():
                # 500ml beer should be 12 bottles per case
                expected_units = original_item['quantity'] * 12
                assert result.converted_quantity == expected_units, f"Beer 500ml should convert to {expected_units} units"
            
            # Confidence check
            assert result.confidence >= 0.7, f"Conversion confidence should be reasonable for {result.original_item_id}"
            
            # Validation check
            validation_success = case_converter.validate_conversion(result)
            assert validation_success, f"Conversion validation should pass for {result.original_item_id}"
    
    def test_sscs_validation_prevents_delivery_failures(self, sscs_validator):
        """
        Test: Prevent SSCS EDI delivery failures through validation
        
        Scenario: Invalid NAXML files cause delivery failures
        Expected: Validation must catch all SSCS compatibility issues
        """
        # Create test NAXML files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Valid NAXML file
            valid_naxml = Path(temp_dir) / "valid.xml"
            valid_content = '''<?xml version="1.0" encoding="utf-8"?>
<ItemSynch version="2.0" timestamp="2025-08-26T01:00:00Z" vendor="DABS">
  <VendorInfo>
    <VendorID>DABS</VendorID>
    <VendorName>Utah Division of Alcoholic Beverage Control</VendorName>
    <InvoiceNumber>TEST_233808_VALID</InvoiceNumber>
    <InvoiceDate>2025-08-26</InvoiceDate>
    <TotalItems>2</TotalItems>
  </VendorInfo>
  <Items>
    <Item>
      <PLU>001</PLU>
      <ItemName>Crown Royal Regal Apple</ItemName>
      <Price>359.88</Price>
      <Cost>250.00</Cost>
      <Category>Spirits</Category>
    </Item>
    <Item>
      <PLU>002</PLU>
      <ItemName>Squatters Hazy Hop</ItemName>
      <Price>50.16</Price>
      <Cost>35.00</Cost>
      <Category>Beer</Category>
    </Item>
  </Items>
</ItemSynch>'''
            
            valid_naxml.write_text(valid_content)
            
            # Invalid NAXML file (missing required elements)
            invalid_naxml = Path(temp_dir) / "invalid.xml"
            invalid_content = '''<?xml version="1.0" encoding="utf-8"?>
<ItemSynch version="2.0">
  <VendorInfo>
    <VendorID>WRONG_VENDOR</VendorID>
    <!-- Missing VendorName, InvoiceNumber, etc. -->
  </VendorInfo>
  <Items>
    <Item>
      <!-- Missing PLU, ItemName, Price, Cost -->
    </Item>
  </Items>
</ItemSynch>'''
            
            invalid_naxml.write_text(invalid_content)
            
            # Test valid file
            valid_result = sscs_validator.validate_naxml_file(str(valid_naxml))
            assert valid_result.valid, "Valid NAXML should pass validation"
            assert valid_result.schema_valid, "Schema should be valid"
            assert valid_result.business_rules_valid, "Business rules should be valid"
            assert valid_result.total_items == 2, "Should detect correct item count"
            
            # Test invalid file
            invalid_result = sscs_validator.validate_naxml_file(str(invalid_naxml))
            assert not invalid_result.valid, "Invalid NAXML should fail validation"
            assert len(invalid_result.issues) > 0, "Should report validation issues"
            
            # Test pre-transmission validation
            ready_for_transmission = sscs_validator.validate_before_transmission(str(valid_naxml))
            assert ready_for_transmission, "Valid file should be ready for transmission"
            
            not_ready_for_transmission = sscs_validator.validate_before_transmission(str(invalid_naxml))
            assert not not_ready_for_transmission, "Invalid file should be blocked from transmission"
    
    def test_vendor_mapping_accuracy(self, vendor_mapper):
        """
        Test: Ensure vendor mapping accuracy for DABS-SSCS integration
        
        Scenario: Incorrect vendor mappings cause EDI processing failures
        Expected: All mappings must be accurate and validated
        """
        # Add test mappings
        test_mapping = VendorMapping(
            dabs_plu="233808_TEST",
            dabs_name="Test Crown Royal Regal Apple",
            vendor_item_code="CR-REGAL-APPLE-750",
            vendor_name="Crown Royal",
            category="Spirits",
            size="750ml",
            confidence=1.0,
            verification_source="test_data"
        )
        
        success = vendor_mapper.add_mapping(test_mapping)
        assert success, "Should successfully add test mapping"
        
        # Test lookup
        result = vendor_mapper.lookup_vendor_code("233808_TEST", "Test Crown Royal Regal Apple")
        assert result.success, "Should find mapped vendor code"
        assert result.vendor_item_code == "CR-REGAL-APPLE-750", "Should return correct vendor code"
        assert result.confidence == 1.0, "Should have high confidence"
        
        # Test unmapped item
        unmapped_result = vendor_mapper.lookup_vendor_code("UNKNOWN_PLU", "Unknown Product")
        assert not unmapped_result.success, "Should fail for unmapped item"
        assert unmapped_result.error_message is not None, "Should provide error message"
        
        # Test fuzzy matching
        fuzzy_result = vendor_mapper.lookup_vendor_code("UNKNOWN_PLU", "Crown Royal Apple Test")
        if fuzzy_result.suggestions:
            assert len(fuzzy_result.suggestions) > 0, "Should provide fuzzy match suggestions"
            assert any("Crown Royal" in suggestion.dabs_name for suggestion in fuzzy_result.suggestions), "Should suggest similar items"
        
        # Test vendor code format validation
        valid_format, message = vendor_mapper.validate_vendor_code_format("VALID-CODE_123")
        assert valid_format, f"Valid vendor code should pass validation: {message}"
        
        invalid_format, message = vendor_mapper.validate_vendor_code_format("INVALID CODE WITH SPACES!")
        assert not invalid_format, f"Invalid vendor code should fail validation: {message}"
    
    @pytest.mark.asyncio
    async def test_rollback_recovery_system(self, rollback_system):
        """
        Test: Ensure rollback system prevents data corruption
        
        Scenario: Processing failures should rollback to safe state
        Expected: No partial processing states or data corruption
        """
        # Test successful transaction
        async with rollback_system.transaction({'test': 'order_233808_success'}) as txn:
            await txn.checkpoint('validation', {'items': 3, 'status': 'passed'})
            await txn.checkpoint('conversion', {'conversions': 3, 'status': 'completed'})
            txn.log_operation('test_operation', {'result': 'success'})
        
        # Verify transaction was committed
        history = rollback_system.get_transaction_history(10)
        assert len(history) > 0, "Should have transaction history"
        
        latest_txn = history[0]
        assert latest_txn['state'] == 'committed', "Transaction should be committed"
        
        # Test failed transaction with rollback
        rollback_triggered = False
        
        def test_rollback_action():
            nonlocal rollback_triggered
            rollback_triggered = True
        
        try:
            async with rollback_system.transaction({'test': 'order_233808_failure'}) as txn:
                await txn.checkpoint('validation', {'items': 3, 'status': 'passed'})
                txn.add_rollback_action(test_rollback_action)
                
                # Simulate failure
                raise Exception("Simulated processing failure")
        except Exception:
            pass  # Expected failure
        
        # Verify rollback was triggered
        assert rollback_triggered, "Rollback action should have been executed"
        
        # Verify transaction was rolled back
        history = rollback_system.get_transaction_history(10)
        failed_txn = next((txn for txn in history if txn['metadata'].get('test') == 'order_233808_failure'), None)
        assert failed_txn is not None, "Should find failed transaction"
        assert failed_txn['state'] == 'rolled_back', "Transaction should be rolled back"
    
    @pytest.mark.asyncio
    async def test_end_to_end_prevention_framework(self, order_233808_data):
        """
        Test: Complete end-to-end prevention framework
        
        Scenario: Full Order 233808 processing with all prevention measures
        Expected: Zero data loss, complete validation, successful processing
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize prevention framework
            orchestrator = PreventionFrameworkOrchestrator(str(Path(temp_dir) / "audit"))
            
            # Test complete order processing
            output_naxml = str(Path(temp_dir) / "test_output.xml")
            
            result = await orchestrator.process_order_with_prevention(
                order_233808_data,
                output_naxml
            )
            
            # Assertions
            assert result.success, f"End-to-end processing should succeed: {result.errors}"
            assert result.stage == "complete", "Should reach completion stage"
            assert result.source_validation is not None, "Should have source validation"
            assert result.source_validation.success, "Source validation should pass"
            assert result.conversion_results is not None, "Should have conversion results"
            assert len(result.conversion_results) == len(order_233808_data), "Should convert all items"
            assert result.sscs_validation is not None, "Should have SSCS validation"
            assert result.sscs_validation.valid, "SSCS validation should pass"
            
            # Verify output file exists
            assert Path(output_naxml).exists(), "Output NAXML file should be created"
            
            # Verify no data loss
            total_input_value = sum(Decimal(str(item['total_price'])) for item in order_233808_data)
            assert result.source_validation.total_expected == total_input_value, "Should preserve total value"
            
            # Verify processing time is reasonable
            assert result.processing_time < 30.0, "Processing should complete within 30 seconds"
            
            # Verify audit trail
            assert result.audit_trail is not None, "Should have audit trail"
            assert len(result.audit_trail) > 0, "Audit trail should contain entries"
    
    def test_order_233808_specific_items_regression(self, source_validator):
        """
        Test: Specific regression for Crown Royal and Squatters items
        
        Scenario: These exact items were lost in Order 233808
        Expected: Must never lose these items again
        """
        # Exact Order 233808 problematic items
        crown_royal = DataItem(
            id="CR001",
            name="Crown Royal Regal Apple",
            quantity=1,
            unit_price=Decimal("359.88"),
            total_price=Decimal("359.88"),
            category="Spirits"
        )
        
        squatters = DataItem(
            id="SQ001", 
            name="Squatters Hazy Hop",
            quantity=1,
            unit_price=Decimal("50.16"),
            total_price=Decimal("50.16"),
            category="Beer"
        )
        
        source_items = [crown_royal, squatters]
        
        # Test various extraction scenarios
        scenarios = [
            # Complete extraction (should pass)
            ([crown_royal, squatters], True, "Complete extraction"),
            
            # Missing Crown Royal (should fail)
            ([squatters], False, "Missing Crown Royal"),
            
            # Missing Squatters (should fail)
            ([crown_royal], False, "Missing Squatters"),
            
            # Empty extraction (should fail)
            ([], False, "Empty extraction"),
            
            # Wrong items (should fail)
            ([DataItem("OTHER", "Other Item", 1, Decimal("10.00"), Decimal("10.00"), "Other")], False, "Wrong items")
        ]
        
        for extracted_items, should_pass, scenario_name in scenarios:
            result = source_validator.validate_extraction_completeness(
                source_items, extracted_items, f"test_{scenario_name.lower().replace(' ', '_')}"
            )
            
            if should_pass:
                assert result.success, f"Scenario '{scenario_name}' should pass validation"
                assert len(result.missing_items) == 0, f"Scenario '{scenario_name}' should have no missing items"
            else:
                assert not result.success, f"Scenario '{scenario_name}' should fail validation"
                assert len(result.missing_items) > 0, f"Scenario '{scenario_name}' should detect missing items"
    
    def test_performance_requirements(self):
        """
        Test: Ensure prevention framework meets performance requirements
        
        Scenario: Framework must not significantly impact processing time
        Expected: Processing overhead should be minimal
        """
        import time
        
        # Test data processing performance
        large_dataset = [
            {
                'id': f'PERF_{i:04d}',
                'name': f'Performance Test Item {i}',
                'category': 'Test',
                'quantity': 1,
                'unit_price': 10.00 + (i * 0.01),
                'total_price': 10.00 + (i * 0.01)
            }
            for i in range(100)  # 100 items for performance test
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SourceDataValidator(temp_dir)
            
            # Convert to DataItem format
            source_items = [
                DataItem(
                    id=item['id'],
                    name=item['name'],
                    quantity=item['quantity'],
                    unit_price=Decimal(str(item['unit_price'])),
                    total_price=Decimal(str(item['total_price'])),
                    category=item['category']
                )
                for item in large_dataset
            ]
            
            # Measure validation performance
            start_time = time.time()
            result = validator.validate_extraction_completeness(
                source_items, source_items, "performance_test"
            )
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Assertions
            assert result.success, "Performance test should pass validation"
            assert processing_time < 5.0, f"Validation should complete within 5 seconds, took {processing_time:.2f}s"
            assert len(result.missing_items) == 0, "Performance test should have no missing items"

# Integration test for complete prevention framework
@pytest.mark.integration
class TestPreventionFrameworkIntegration:
    """Integration tests for complete prevention framework"""
    
    @pytest.mark.asyncio
    async def test_complete_order_233813_processing(self):
        """
        Test: Complete Order 233813 processing with prevention framework
        
        This test simulates the complete Order 233813 workflow with all
        prevention measures in place to ensure no Order 233808 type failures.
        """
        order_233813_data = [
            {'id': '917817', 'name': 'RED ROCK ELEPHINO IPA 500ml', 'category': 'Beer', 'quantity': 4, 'unit_price': 48.48, 'total_price': 193.92},
            {'id': '581015', 'name': 'BOTA BOX PINOT GRIGIO 3000ml', 'category': 'Wine', 'quantity': 3, 'unit_price': 71.97, 'total_price': 215.91},
            {'id': '989418', 'name': 'RED ROCK FROHLICH PILS 500ml', 'category': 'Beer', 'quantity': 3, 'unit_price': 48.48, 'total_price': 145.44},
            {'id': '927483', 'name': 'HIGHPOINT TRANSPLANT CIDER 355ml', 'category': 'Cider', 'quantity': 2, 'unit_price': 61.20, 'total_price': 122.40},
            {'id': '039271', 'name': 'SUGAR HOUSE VODKA 1000ml', 'category': 'Spirits', 'quantity': 1, 'unit_price': 131.94, 'total_price': 131.94}
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = PreventionFrameworkOrchestrator(str(Path(temp_dir) / "audit"))
            output_naxml = str(Path(temp_dir) / "order_233813_output.xml")
            
            result = await orchestrator.process_order_with_prevention(
                order_233813_data,
                output_naxml
            )
            
            # Comprehensive assertions
            assert result.success, "Order 233813 processing should succeed with prevention framework"
            assert result.source_validation.success, "Source validation should pass"
            assert len(result.conversion_results) == len(order_233813_data), "All items should be converted"
            assert result.sscs_validation.valid, "SSCS validation should pass"
            assert Path(output_naxml).exists(), "Output NAXML should be generated"
            
            # Verify zero data loss
            expected_total = sum(Decimal(str(item['total_price'])) for item in order_233813_data)
            assert result.source_validation.total_expected == expected_total, "Total value should be preserved"
            
            # Verify performance
            assert result.processing_time < 60.0, "Processing should complete within 60 seconds"

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
