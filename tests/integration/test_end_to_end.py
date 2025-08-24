"""
Integration tests for the DABS Automation System

Tests cover:
- End-to-end processing workflows
- Integration between components
- Real-world scenarios
- Performance under load
- Error recovery and rollback
"""

import pytest
import asyncio
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch

from processors.dabs_processor import DABSProcessor
from audit.audit_trail import AuditTrailManager, AuditEventType


@pytest.mark.integration
@pytest.mark.asyncio
class TestEndToEndWorkflows:
    """Test complete end-to-end workflows"""
    
    async def test_complete_dabs_processing_workflow(self, temp_dir):
        """Test complete DABS processing workflow from file to audit"""
        # Setup
        data_dir = temp_dir / "data"
        export_dir = temp_dir / "exports"
        audit_dir = temp_dir / "audit"
        
        for directory in [data_dir, export_dir, audit_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Create test config
        config = {
            'data_directory': str(data_dir),
            'export_directory': str(export_dir),
            'backup_files': True,
            'validate_prices': True,
            'max_price_variance_percent': 20.0,
            'required_columns': ['SKU', 'ITEM NAME', 'PRICE', 'ITEM TYPE'],
            'column_mapping': {
                'SKU': 'SKU',
                'ITEM NAME': 'ProductName', 
                'PRICE': 'RetailPrice',
                'ITEM TYPE': 'Category',
                'ITEM STATUS': 'Status',
                'ON SPA?': 'OnSpecialPricing',
                'FROM DATE': 'EffectiveDate',
                'TO DATE': 'EndDate'
            },
            'naxml_version': '2.0',
            'export_formats': ['naxml', 'csv', 'json'],
            'processing_timeout_minutes': 30,
            'excel_header_row': 1,
            'audit_retention_years': 7
        }
        
        config_file = temp_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Create test DABS file
        test_data = pd.DataFrame([
            {
                'SKU': '123456',
                'ITEM NAME': 'Premium Whiskey 750ml',
                'PRICE': 89.99,
                'ITEM TYPE': 'Whiskey',
                'ITEM STATUS': 'Active',
                'ON SPA?': 'No',
                'FROM DATE': '2025-01-01',
                'TO DATE': '2025-12-31'
            },
            {
                'SKU': '789012',
                'ITEM NAME': 'Craft Beer 6-pack',
                'PRICE': 15.99,
                'ITEM TYPE': 'Beer',
                'ITEM STATUS': 'Active',
                'ON SPA?': 'Yes',
                'FROM DATE': '2025-01-01',
                'TO DATE': '2025-12-31'
            },
            {
                'SKU': '345678',
                'ITEM NAME': 'Premium Vodka 1L',
                'PRICE': 1299.99,  # High price - should trigger warning
                'ITEM TYPE': 'Vodka',
                'ITEM STATUS': 'Active',
                'ON SPA?': 'No',
                'FROM DATE': '2025-01-01',
                'TO DATE': '2025-12-31'
            }
        ])
        
        excel_file = temp_dir / "DABS_Price_Changes.xlsx"
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            header_df = pd.DataFrame([['DABS Price Changes Report']])
            header_df.to_excel(writer, index=False, header=False, startrow=0)
            test_data.to_excel(writer, index=False, startrow=1)
        
        # Initialize processor
        processor = DABSProcessor(str(config_file))
        
        # Process the file
        result = await processor.process_dabs_file(excel_file)
        
        # Verify processing success
        assert result.success is True
        assert result.total_skus == 3
        assert result.processed_skus == 3
        assert result.failed_skus == 0
        
        # Verify output files were created
        assert len(result.output_files) >= 3
        
        # Check NAXML file
        naxml_files = [f for f in result.output_files if f.endswith('.xml')]
        assert len(naxml_files) == 1
        assert Path(naxml_files[0]).exists()
        
        # Check CSV file
        csv_files = [f for f in result.output_files if f.endswith('.csv')]
        assert len(csv_files) == 1
        csv_df = pd.read_csv(csv_files[0])
        assert len(csv_df) == 3
        assert str(csv_df.iloc[0]['SKU']) == '123456'
        
        # Check JSON file
        json_files = [f for f in result.output_files if f.endswith('.json') and 'validation' not in f]
        assert len(json_files) == 1
        with open(json_files[0], 'r') as f:
            json_data = json.load(f)
        assert len(json_data['products']) == 3
        
        # Verify validation exceptions (should have high price warning)
        assert len(result.exceptions) > 0
        high_price_exceptions = [e for e in result.exceptions if e['type'] == 'high_price_warning']
        assert len(high_price_exceptions) == 1
        assert str(high_price_exceptions[0]['sku']) == '345678'
        
        # Verify audit trail
        if processor.audit_manager:
            audit_events = await processor.audit_manager.get_audit_trail(limit=20)
            
            # Should have file processing event
            file_events = [e for e in audit_events if e['event_type'] == 'file_processed']
            assert len(file_events) == 1
            
            # Should have validation exception events
            validation_events = [e for e in audit_events if e['event_type'] == 'validation_exception']
            assert len(validation_events) == 1
            
            # Verify audit integrity
            integrity = await processor.audit_manager.verify_audit_integrity()
            assert integrity['integrity_verified'] is True
        
        # Verify backup was created
        backup_files = list(processor.backup_dir.glob("*.xlsx"))
        assert len(backup_files) == 1
        
        print(f"✅ Complete workflow test passed:")
        print(f"   - Processed {result.processed_skus} SKUs in {result.processing_time:.2f}s")
        print(f"   - Generated {len(result.output_files)} output files")
        print(f"   - Detected {len(result.exceptions)} validation exceptions")
        print(f"   - Created backup and audit trail")
    
    async def test_price_variance_workflow(self, temp_dir):
        """Test price variance detection workflow"""
        # Setup processor
        data_dir = temp_dir / "data"
        export_dir = temp_dir / "exports"
        
        for directory in [data_dir, export_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        config = {
            'data_directory': str(data_dir),
            'export_directory': str(export_dir),
            'backup_files': True,
            'validate_prices': True,
            'max_price_variance_percent': 20.0,
            'required_columns': ['SKU', 'ITEM NAME', 'PRICE', 'ITEM TYPE'],
            'column_mapping': {
                'SKU': 'SKU',
                'ITEM NAME': 'ProductName', 
                'PRICE': 'RetailPrice',
                'ITEM TYPE': 'Category',
                'ITEM STATUS': 'Status',
                'ON SPA?': 'OnSpecialPricing',
                'FROM DATE': 'EffectiveDate',
                'TO DATE': 'EndDate'
            },
            'naxml_version': '2.0',
            'export_formats': ['csv'],
            'excel_header_row': 1
        }
        
        config_file = temp_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        processor = DABSProcessor(str(config_file))
        
        # Step 1: Process initial file to create historical data
        initial_data = pd.DataFrame([
            {
                'SKU': '111111',
                'ITEM NAME': 'Test Item 1',
                'PRICE': 50.00,
                'ITEM TYPE': 'Test',
                'ITEM STATUS': 'Active',
                'ON SPA?': 'No',
                'FROM DATE': '2025-01-01',
                'TO DATE': '2025-12-31'
            },
            {
                'SKU': '222222',
                'ITEM NAME': 'Test Item 2',
                'PRICE': 30.00,
                'ITEM TYPE': 'Test',
                'ITEM STATUS': 'Active',
                'ON SPA?': 'No',
                'FROM DATE': '2025-01-01',
                'TO DATE': '2025-12-31'
            }
        ])
        
        initial_file = temp_dir / "initial_prices.xlsx"
        with pd.ExcelWriter(initial_file, engine='openpyxl') as writer:
            header_df = pd.DataFrame([['DABS Price Changes Report']])
            header_df.to_excel(writer, index=False, header=False, startrow=0)
            initial_data.to_excel(writer, index=False, startrow=1)
        
        result1 = await processor.process_dabs_file(initial_file)
        assert result1.success is True

        # Make the historical CSV file appear older than 1 minute
        import os
        import time
        csv_files = [f for f in result1.output_files if f.endswith('.csv')]
        if csv_files:
            old_time = time.time() - 120  # 2 minutes ago
            os.utime(csv_files[0], (old_time, old_time))

        # Wait a moment to ensure file timestamps are different
        await asyncio.sleep(1)
        
        # Step 2: Process updated file with significant price changes
        updated_data = pd.DataFrame([
            {
                'SKU': '111111',
                'ITEM NAME': 'Test Item 1',
                'PRICE': 75.00,  # 50% increase - should trigger variance
                'ITEM TYPE': 'Test',
                'ITEM STATUS': 'Active',
                'ON SPA?': 'No',
                'FROM DATE': '2025-01-01',
                'TO DATE': '2025-12-31'
            },
            {
                'SKU': '222222',
                'ITEM NAME': 'Test Item 2',
                'PRICE': 32.00,  # 6.7% increase - should not trigger variance
                'ITEM TYPE': 'Test',
                'ITEM STATUS': 'Active',
                'ON SPA?': 'No',
                'FROM DATE': '2025-01-01',
                'TO DATE': '2025-12-31'
            }
        ])
        
        updated_file = temp_dir / "updated_prices.xlsx"
        with pd.ExcelWriter(updated_file, engine='openpyxl') as writer:
            header_df = pd.DataFrame([['DABS Price Changes Report']])
            header_df.to_excel(writer, index=False, header=False, startrow=0)
            updated_data.to_excel(writer, index=False, startrow=1)
        
        result2 = await processor.process_dabs_file(updated_file)
        assert result2.success is True
        
        # Verify variance detection
        variance_exceptions = [e for e in result2.exceptions if e.get('type') == 'price_variance']
        assert len(variance_exceptions) == 1
        
        variance_exc = variance_exceptions[0]
        assert variance_exc['sku'] == '111111'
        assert variance_exc['variance_percent'] == 50.0
        assert variance_exc['direction'] == 'increase'
        assert variance_exc['current_price'] == 75.00
        assert variance_exc['historical_price'] == 50.00
        
        print(f"✅ Price variance workflow test passed:")
        print(f"   - Detected {len(variance_exceptions)} price variances")
        print(f"   - SKU {variance_exc['sku']}: {variance_exc['variance_percent']}% {variance_exc['direction']}")
    
    async def test_error_recovery_workflow(self, temp_dir):
        """Test error recovery and rollback capabilities"""
        # Setup processor
        data_dir = temp_dir / "data"
        export_dir = temp_dir / "exports"
        
        for directory in [data_dir, export_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        config = {
            'data_directory': str(data_dir),
            'export_directory': str(export_dir),
            'backup_files': True,
            'validate_prices': True,
            'required_columns': ['SKU', 'ITEM NAME', 'PRICE', 'ITEM TYPE'],
            'column_mapping': {
                'SKU': 'SKU',
                'ITEM NAME': 'ProductName', 
                'PRICE': 'RetailPrice',
                'ITEM TYPE': 'Category',
                'ITEM STATUS': 'Status',
                'ON SPA?': 'OnSpecialPricing',
                'FROM DATE': 'EffectiveDate',
                'TO DATE': 'EndDate'
            },
            'naxml_version': '2.0',
            'export_formats': ['csv'],
            'excel_header_row': 1
        }
        
        config_file = temp_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        processor = DABSProcessor(str(config_file))
        
        # Test 1: Missing required columns
        invalid_data = pd.DataFrame([
            {
                'INVALID_COLUMN': 'test',
                'ANOTHER_INVALID': 'test'
            }
        ])
        
        invalid_file = temp_dir / "invalid_columns.xlsx"
        with pd.ExcelWriter(invalid_file, engine='openpyxl') as writer:
            header_df = pd.DataFrame([['DABS Price Changes Report']])
            header_df.to_excel(writer, index=False, header=False, startrow=0)
            invalid_data.to_excel(writer, index=False, startrow=1)
        
        result1 = await processor.process_dabs_file(invalid_file)
        assert result1.success is False
        assert len(result1.errors) > 0
        assert 'Missing required columns' in result1.errors[0]
        
        # Test 2: Empty file
        empty_data = pd.DataFrame()
        
        empty_file = temp_dir / "empty_file.xlsx"
        with pd.ExcelWriter(empty_file, engine='openpyxl') as writer:
            header_df = pd.DataFrame([['DABS Price Changes Report']])
            header_df.to_excel(writer, index=False, header=False, startrow=0)
            empty_data.to_excel(writer, index=False, startrow=1)
        
        result2 = await processor.process_dabs_file(empty_file)
        assert result2.success is False
        assert len(result2.errors) > 0
        assert 'Could not load Excel file' in result2.errors[0]
        
        # Test 3: Non-existent file
        nonexistent_file = temp_dir / "does_not_exist.xlsx"
        
        result3 = await processor.process_dabs_file(nonexistent_file)
        assert result3.success is False
        assert len(result3.errors) > 0
        assert 'not found' in result3.errors[0]
        
        # Verify no partial files were created for failed processing
        output_files = list(export_dir.glob("*"))
        # Should only have files from successful processing (none in this case)
        assert len(output_files) == 0
        
        print(f"✅ Error recovery workflow test passed:")
        print(f"   - Handled missing columns error")
        print(f"   - Handled empty file error")
        print(f"   - Handled non-existent file error")
        print(f"   - No partial files created during failures")
    
    @pytest.mark.slow
    async def test_performance_workflow(self, temp_dir):
        """Test performance under realistic load"""
        # Setup processor
        data_dir = temp_dir / "data"
        export_dir = temp_dir / "exports"
        
        for directory in [data_dir, export_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        config = {
            'data_directory': str(data_dir),
            'export_directory': str(export_dir),
            'backup_files': True,
            'validate_prices': True,
            'max_price_variance_percent': 20.0,
            'required_columns': ['SKU', 'ITEM NAME', 'PRICE', 'ITEM TYPE'],
            'column_mapping': {
                'SKU': 'SKU',
                'ITEM NAME': 'ProductName', 
                'PRICE': 'RetailPrice',
                'ITEM TYPE': 'Category',
                'ITEM STATUS': 'Status',
                'ON SPA?': 'OnSpecialPricing',
                'FROM DATE': 'EffectiveDate',
                'TO DATE': 'EndDate'
            },
            'naxml_version': '2.0',
            'export_formats': ['naxml', 'csv', 'json'],
            'excel_header_row': 1
        }
        
        config_file = temp_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        processor = DABSProcessor(str(config_file))
        
        # Create realistic dataset (1,239 SKUs like real DABS file)
        realistic_data = []
        categories = ['Whiskey', 'Vodka', 'Rum', 'Gin', 'Beer', 'Wine', 'Liqueur']
        
        for i in range(1239):
            realistic_data.append({
                'SKU': f'{i+1:06d}',
                'ITEM NAME': f'Product {i+1} {750 if i % 3 == 0 else 1000}ml',
                'PRICE': round(10.00 + (i % 200) + (i / 100), 2),
                'ITEM TYPE': categories[i % len(categories)],
                'ITEM STATUS': 'Active',
                'ON SPA?': 'Yes' if i % 5 == 0 else 'No',
                'FROM DATE': '2025-01-01',
                'TO DATE': '2025-12-31'
            })
        
        realistic_df = pd.DataFrame(realistic_data)
        realistic_file = temp_dir / "realistic_dabs.xlsx"
        
        with pd.ExcelWriter(realistic_file, engine='openpyxl') as writer:
            header_df = pd.DataFrame([['DABS Price Changes Report']])
            header_df.to_excel(writer, index=False, header=False, startrow=0)
            realistic_df.to_excel(writer, index=False, startrow=1)
        
        # Process and measure performance
        start_time = datetime.now()
        result = await processor.process_dabs_file(realistic_file)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Verify success
        assert result.success is True
        assert result.total_skus == 1239
        assert result.processed_skus == 1239
        assert result.failed_skus == 0
        
        # Verify performance requirements (should process within 15 minutes)
        assert processing_time < 900  # 15 minutes
        
        # Verify all output files were created
        assert len(result.output_files) >= 3
        
        # Verify file sizes are reasonable
        for output_file in result.output_files:
            file_path = Path(output_file)
            assert file_path.exists()
            assert file_path.stat().st_size > 0
        
        print(f"✅ Performance workflow test passed:")
        print(f"   - Processed {result.processed_skus} SKUs in {processing_time:.2f}s")
        print(f"   - Performance: {result.processed_skus / processing_time:.1f} SKUs/second")
        print(f"   - Generated {len(result.output_files)} output files")
        print(f"   - Met 15-minute processing requirement")
        
        return processing_time
