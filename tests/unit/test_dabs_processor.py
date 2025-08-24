"""
Unit tests for the DABS Processor

Tests cover:
- File loading and validation
- Data processing and conversion
- Price validation logic
- Export functionality (NAXML, CSV, JSON)
- Error handling and edge cases
- Audit trail integration
"""

import pytest
import asyncio
import pandas as pd
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from processors.dabs_processor import DABSProcessor, DABSProduct, ProcessingResult


@pytest.mark.unit
@pytest.mark.asyncio
class TestDABSProcessor:
    """Test suite for DABSProcessor class"""
    
    async def test_initialization(self, dabs_processor):
        """Test DABS processor initialization"""
        assert dabs_processor.config is not None
        assert dabs_processor.data_dir.exists()
        assert dabs_processor.export_dir.exists()
        assert dabs_processor.backup_dir.exists()
        assert dabs_processor.audit_dir.exists()
        
        # Test audit manager initialization
        assert dabs_processor.audit_manager is not None
    
    async def test_load_excel_file(self, dabs_processor, sample_excel_file):
        """Test Excel file loading"""
        df = await dabs_processor._load_excel_file(sample_excel_file)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3  # Sample data has 3 rows
        assert 'SKU' in df.columns
        assert 'ITEM NAME' in df.columns
        assert 'PRICE' in df.columns
    
    async def test_validate_data_success(self, dabs_processor, sample_dabs_data):
        """Test successful data validation"""
        validation_result = await dabs_processor._validate_data(sample_dabs_data)
        
        assert validation_result['valid'] is True
        assert len(validation_result['errors']) == 0
        # May have warnings but should be valid
    
    async def test_validate_data_missing_columns(self, dabs_processor):
        """Test validation with missing required columns"""
        invalid_df = pd.DataFrame([{'INVALID_COLUMN': 'test'}])
        
        validation_result = await dabs_processor._validate_data(invalid_df)
        
        assert validation_result['valid'] is False
        assert len(validation_result['errors']) > 0
        assert any('Missing required columns' in error for error in validation_result['errors'])
    
    async def test_validate_data_empty(self, dabs_processor):
        """Test validation with empty data"""
        empty_df = pd.DataFrame()
        
        validation_result = await dabs_processor._validate_data(empty_df)
        
        assert validation_result['valid'] is False
        assert any('no data rows' in error for error in validation_result['errors'])
    
    async def test_price_validation(self, dabs_processor, sample_dabs_data):
        """Test price validation logic"""
        # Add invalid prices to test data
        invalid_data = sample_dabs_data.copy()
        invalid_data.loc[len(invalid_data)] = {
            'SKU': '999999',
            'ITEM NAME': 'Invalid Item',
            'PRICE': -10.00,  # Negative price
            'ITEM TYPE': 'Test',
            'ITEM STATUS': 'Active',
            'ON SPA?': 'No',
            'FROM DATE': '2025-01-01',
            'TO DATE': '2025-12-31'
        }
        
        price_validation = await dabs_processor._validate_prices(invalid_data)
        
        assert 'errors' in price_validation
        assert 'warnings' in price_validation
        assert 'exceptions' in price_validation
        
        # Should have exceptions for negative price
        exceptions = price_validation['exceptions']
        negative_price_exceptions = [e for e in exceptions if e['type'] == 'negative_price']
        assert len(negative_price_exceptions) > 0
    
    async def test_convert_to_products(self, dabs_processor, sample_dabs_data):
        """Test conversion of DataFrame to DABSProduct objects"""
        products = await dabs_processor._convert_to_products(sample_dabs_data)
        
        assert len(products) == 3
        assert all(isinstance(p, DABSProduct) for p in products)
        
        # Test first product
        product = products[0]
        assert product.sku == '123456'
        assert product.product_name == 'Test Whiskey 750ml'
        assert product.retail_price == 29.99
        assert product.category == 'Whiskey'
        assert product.on_special_pricing is False
        assert product.size_ml == '750'
    
    async def test_extract_size_ml(self, dabs_processor):
        """Test size extraction from product names"""
        test_cases = [
            ('Test Whiskey 750ml', '750'),
            ('Vodka 1L', '1000.0'),
            ('Beer 12oz', '12'),  # Note: the method doesn't convert oz to ml
            ('Wine 1.5L', '1500.0'),
            ('No Size Product', None),
            ('Multiple 750ml and 1L sizes', '750')  # Should get first match
        ]
        
        for product_name, expected_size in test_cases:
            size = dabs_processor._extract_size_ml(product_name)
            assert size == expected_size, f"Failed for '{product_name}': expected {expected_size}, got {size}"
    
    async def test_generate_naxml(self, dabs_processor, sample_products, temp_dir):
        """Test NAXML file generation"""
        # Override export directory for test
        dabs_processor.export_dir = temp_dir
        
        naxml_file = await dabs_processor._generate_naxml(sample_products)
        
        assert Path(naxml_file).exists()
        assert naxml_file.endswith('.xml')
        
        # Parse and validate XML structure
        tree = ET.parse(naxml_file)
        root = tree.getroot()
        
        assert root.tag == '{http://www.naxml.org/NAXML}ItemSynch'
        assert root.get('version') == '2.0'
        # Check namespace is properly set (namespace is part of the tag when parsed)
        assert 'naxml.org' in root.tag
        
        # Define namespace for XML parsing
        ns = {'naxml': 'http://www.naxml.org/NAXML'}

        # Check header
        header = root.find('naxml:Header', ns)
        assert header is not None
        assert header.find('naxml:Source', ns).text == 'DABS-Hills-Hollows'
        assert header.find('naxml:Destination', ns).text == 'SSCS-POS'
        assert header.find('naxml:RecordCount', ns).text == '2'

        # Check items
        items = root.find('naxml:Items', ns)
        assert items is not None
        item_elements = items.findall('naxml:Item', ns)
        assert len(item_elements) == 2
        
        # Check first item
        item = item_elements[0]
        assert item.get('action') == 'update'
        assert item.find('naxml:SKU', ns).text == '123456'
        assert item.find('naxml:Description', ns).text == 'Test Whiskey 750ml'

        # Check pricing
        pricing = item.find('naxml:Pricing', ns)
        assert pricing is not None
        assert pricing.find('naxml:RetailPrice', ns).text == '29.99'
        assert pricing.find('naxml:Currency', ns).text == 'USD'
        assert pricing.find('naxml:OnSpecial', ns).text == 'false'
    
    async def test_generate_csv(self, dabs_processor, sample_products, temp_dir):
        """Test CSV file generation"""
        dabs_processor.export_dir = temp_dir
        
        csv_file = await dabs_processor._generate_csv(sample_products)
        
        assert Path(csv_file).exists()
        assert csv_file.endswith('.csv')
        
        # Read and validate CSV
        df = pd.read_csv(csv_file)
        assert len(df) == 2
        assert 'SKU' in df.columns
        assert 'ProductName' in df.columns
        assert 'RetailPrice' in df.columns
        
        # Check data
        assert str(df.iloc[0]['SKU']) == '123456'
        assert df.iloc[0]['ProductName'] == 'Test Whiskey 750ml'
        assert df.iloc[0]['RetailPrice'] == 29.99
    
    async def test_generate_json(self, dabs_processor, sample_products, temp_dir):
        """Test JSON file generation"""
        dabs_processor.export_dir = temp_dir
        
        json_file = await dabs_processor._generate_json(sample_products)
        
        assert Path(json_file).exists()
        assert json_file.endswith('.json')
        
        # Read and validate JSON
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        assert 'metadata' in data
        assert 'products' in data
        assert len(data['products']) == 2
        
        # Check metadata
        metadata = data['metadata']
        assert metadata['total_items'] == 2
        assert metadata['source'] == 'DABS-Hills-Hollows'
        
        # Check product data
        product = data['products'][0]
        assert product['sku'] == '123456'
        assert product['product_name'] == 'Test Whiskey 750ml'
        assert product['retail_price'] == 29.99
    
    async def test_calculate_checksum(self, dabs_processor, sample_products):
        """Test checksum calculation"""
        checksum = await dabs_processor._calculate_checksum(sample_products)
        
        assert checksum is not None
        assert len(checksum) == 64  # SHA256 hex length
        
        # Same products should produce same checksum
        checksum2 = await dabs_processor._calculate_checksum(sample_products)
        assert checksum == checksum2
        
        # Different products should produce different checksum
        modified_products = sample_products.copy()
        modified_products[0].retail_price = 99.99
        checksum3 = await dabs_processor._calculate_checksum(modified_products)
        assert checksum != checksum3
    
    async def test_backup_file(self, dabs_processor, sample_excel_file):
        """Test file backup functionality"""
        await dabs_processor._backup_file(sample_excel_file)
        
        # Check backup was created
        backup_files = list(dabs_processor.backup_dir.glob("*.xlsx"))
        assert len(backup_files) > 0
        
        backup_file = backup_files[0]
        assert backup_file.exists()
        assert 'backup_' in backup_file.name
    
    async def test_process_dabs_file_success(self, dabs_processor, sample_excel_file):
        """Test successful DABS file processing"""
        result = await dabs_processor.process_dabs_file(sample_excel_file)
        
        assert isinstance(result, ProcessingResult)
        assert result.success is True
        assert result.total_skus == 3
        assert result.processed_skus == 3
        assert result.failed_skus == 0
        assert len(result.errors) == 0
        assert len(result.output_files) > 0
        assert result.checksum is not None
        assert result.processing_time > 0
    
    async def test_process_dabs_file_with_validation_exceptions(self, dabs_processor, temp_dir):
        """Test DABS file processing with validation exceptions"""
        # Create Excel file with problematic data
        problem_data = pd.DataFrame([
            {
                'SKU': '999999',
                'ITEM NAME': 'Expensive Item',
                'PRICE': 1500.00,  # High price warning
                'ITEM TYPE': 'Premium',
                'ITEM STATUS': 'Active',
                'ON SPA?': 'No',
                'FROM DATE': '2025-01-01',
                'TO DATE': '2025-12-31'
            },
            {
                'SKU': '888888',
                'ITEM NAME': 'Cheap Item',
                'PRICE': 2.99,  # Low price warning
                'ITEM TYPE': 'Budget',
                'ITEM STATUS': 'Active',
                'ON SPA?': 'No',
                'FROM DATE': '2025-01-01',
                'TO DATE': '2025-12-31'
            }
        ])
        
        excel_file = temp_dir / "problem_data.xlsx"
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            header_df = pd.DataFrame([['DABS Price Changes Report']])
            header_df.to_excel(writer, index=False, header=False, startrow=0)
            problem_data.to_excel(writer, index=False, startrow=1)
        
        result = await dabs_processor.process_dabs_file(excel_file)
        
        assert result.success is True
        assert result.processed_skus == 2
        assert len(result.exceptions) > 0  # Should have validation exceptions
        
        # Check for high and low price warnings
        exception_types = [exc['type'] for exc in result.exceptions]
        assert 'high_price_warning' in exception_types
        assert 'low_price_warning' in exception_types
    
    async def test_process_nonexistent_file(self, dabs_processor):
        """Test processing of non-existent file"""
        nonexistent_file = Path("nonexistent_file.xlsx")
        
        result = await dabs_processor.process_dabs_file(nonexistent_file)
        
        assert result.success is False
        assert len(result.errors) > 0
        assert 'not found' in result.errors[0].lower()
    
    async def test_audit_integration(self, dabs_processor, sample_excel_file):
        """Test audit trail integration during processing"""
        # Process file
        result = await dabs_processor.process_dabs_file(sample_excel_file)
        
        assert result.success is True
        
        # Check audit events were logged
        if dabs_processor.audit_manager:
            events = await dabs_processor.audit_manager.get_audit_trail(limit=10)
            
            # Should have file processing event
            file_events = [e for e in events if e['event_type'] == 'file_processed']
            assert len(file_events) > 0
            
            file_event = file_events[0]
            assert 'sample_excel_file' in file_event['description'] or 'test_dabs.xlsx' in file_event['description']
    
    async def test_price_variance_detection(self, dabs_processor, temp_dir):
        """Test price variance detection against historical data"""
        # First, create a historical CSV file
        historical_data = pd.DataFrame([
            {
                'SKU': '123456',
                'ProductName': 'Test Item',
                'RetailPrice': 10.00,
                'Category': 'Test',
                'OnSpecialPricing': 'No',
                'EffectiveDate': '2025-01-01',
                'Status': 'Active',
                'UpdatedOn': '2025-01-01 00:00:00',
                'Size': ''
            }
        ])
        
        historical_file = dabs_processor.export_dir / "dabs_pricing_20250101_000000.csv"
        historical_data.to_csv(historical_file, index=False)

        # Make the historical file appear older than 1 minute
        import os
        import time
        old_time = time.time() - 120  # 2 minutes ago
        os.utime(historical_file, (old_time, old_time))
        
        # Now create new data with significant price change
        new_data = pd.DataFrame([
            {
                'SKU': '123456',
                'ITEM NAME': 'Test Item',
                'PRICE': 25.00,  # 150% increase from $10
                'ITEM TYPE': 'Test',
                'ITEM STATUS': 'Active',
                'ON SPA?': 'No',
                'FROM DATE': '2025-01-01',
                'TO DATE': '2025-12-31'
            }
        ])
        
        excel_file = temp_dir / "variance_test.xlsx"
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            header_df = pd.DataFrame([['DABS Price Changes Report']])
            header_df.to_excel(writer, index=False, header=False, startrow=0)
            new_data.to_excel(writer, index=False, startrow=1)
        
        # Process and check for variance detection
        result = await dabs_processor.process_dabs_file(excel_file)
        
        assert result.success is True
        
        # Should detect price variance
        variance_exceptions = [exc for exc in result.exceptions if exc.get('type') == 'price_variance']
        assert len(variance_exceptions) > 0
        
        variance_exc = variance_exceptions[0]
        assert variance_exc['sku'] == '123456'
        assert variance_exc['variance_percent'] > 20  # Should be 150%
    
    @pytest.mark.slow
    async def test_large_dataset_processing(self, dabs_processor, temp_dir):
        """Test processing of large dataset (performance test)"""
        # Create large dataset (1000 items)
        large_data = []
        for i in range(1000):
            large_data.append({
                'SKU': f'{i:06d}',
                'ITEM NAME': f'Test Item {i}',
                'PRICE': 10.00 + (i % 100),
                'ITEM TYPE': 'Test',
                'ITEM STATUS': 'Active',
                'ON SPA?': 'No' if i % 2 == 0 else 'Yes',
                'FROM DATE': '2025-01-01',
                'TO DATE': '2025-12-31'
            })
        
        large_df = pd.DataFrame(large_data)
        excel_file = temp_dir / "large_dataset.xlsx"
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            header_df = pd.DataFrame([['DABS Price Changes Report']])
            header_df.to_excel(writer, index=False, header=False, startrow=0)
            large_df.to_excel(writer, index=False, startrow=1)
        
        # Process and measure time
        start_time = datetime.now()
        result = await dabs_processor.process_dabs_file(excel_file)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        assert result.success is True
        assert result.processed_skus == 1000
        assert processing_time < 60  # Should process 1000 items in under 1 minute
        
        # Verify all output files were created
        assert len(result.output_files) >= 3  # NAXML, CSV, JSON minimum
