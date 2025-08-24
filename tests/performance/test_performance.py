"""
Performance tests for DABS automation system.

Tests validate that the system can process 1,239 SKUs within 15 minutes
and meets all performance requirements for Hills & Hollows LLC.
"""

import asyncio
import json
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import pytest
from faker import Faker

from processors.dabs_processor import DABSProcessor
from integration_hub.coordinator import IntegrationCoordinator
from audit.audit_trail import AuditTrailManager


class TestPerformanceRequirements:
    """Performance test suite for DABS automation system"""
    
    @pytest.fixture
    def performance_config(self, temp_dir):
        """Create optimized configuration for performance testing"""
        config = {
            'data_directory': str(temp_dir / "data"),
            'export_directory': str(temp_dir / "exports"),
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
            'audit_retention_years': 7,
            'batch_size': 100,  # Optimize for performance
            'enable_parallel_processing': True
        }
        
        config_file = temp_dir / "performance_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        return str(config_file)
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for performance tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create required subdirectories
            for subdir in ['data', 'exports', 'audit', 'dabs_backups']:
                (temp_path / subdir).mkdir(parents=True, exist_ok=True)
            
            yield temp_path
    
    def generate_large_dabs_dataset(self, num_skus: int = 1239) -> pd.DataFrame:
        """Generate large DABS dataset for performance testing"""
        import random
        fake = Faker()
        Faker.seed(42)  # For reproducible results
        random.seed(42)  # For reproducible random numbers
        
        # Liquor categories and types
        categories = ['Whiskey', 'Vodka', 'Rum', 'Gin', 'Tequila', 'Brandy', 'Liqueur', 'Wine', 'Beer']
        sizes = ['50ml', '200ml', '375ml', '750ml', '1L', '1.75L']
        statuses = ['Active', 'Discontinued', 'Seasonal']
        
        data = []
        for i in range(num_skus):
            sku = str(100000 + i).zfill(6)
            category = fake.random_element(categories)
            size = fake.random_element(sizes)
            
            # Generate realistic pricing based on category and size
            base_price = {
                'Whiskey': 45.0, 'Vodka': 25.0, 'Rum': 30.0, 'Gin': 35.0,
                'Tequila': 40.0, 'Brandy': 50.0, 'Liqueur': 28.0, 'Wine': 15.0, 'Beer': 8.0
            }.get(category, 30.0)
            
            size_multiplier = {
                '50ml': 0.3, '200ml': 0.6, '375ml': 0.8, '750ml': 1.0,
                '1L': 1.3, '1.75L': 1.8
            }.get(size, 1.0)
            
            price = round(base_price * size_multiplier * random.uniform(0.8, 1.5), 2)
            
            data.append({
                'SKU': sku,
                'ITEM NAME': f"{fake.company()} {category} {size}",
                'PRICE': price,
                'ITEM TYPE': category,
                'ITEM STATUS': fake.random_element(statuses),
                'ON SPA?': fake.random_element(['Yes', 'No']),
                'FROM DATE': '2025-01-01',
                'TO DATE': '2025-12-31'
            })
        
        return pd.DataFrame(data)
    
    def create_performance_excel_file(self, data: pd.DataFrame, file_path: Path) -> None:
        """Create Excel file in DABS format for performance testing"""
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Add DABS header
            header_df = pd.DataFrame([['DABS Price Changes Report']])
            header_df.to_excel(writer, index=False, header=False, startrow=0)
            
            # Add data starting from row 2
            data.to_excel(writer, index=False, startrow=1)
    
    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_dataset_processing_performance(self, performance_config, temp_dir):
        """Test processing 1,239 SKUs within 15-minute requirement"""
        # Generate test dataset
        test_data = self.generate_large_dabs_dataset(1239)
        excel_file = temp_dir / "performance_test_1239_skus.xlsx"
        self.create_performance_excel_file(test_data, excel_file)
        
        # Initialize processor
        processor = DABSProcessor(performance_config)
        
        # Measure processing time
        start_time = time.time()
        result = await processor.process_dabs_file(excel_file)
        end_time = time.time()
        
        processing_time = end_time - start_time
        processing_minutes = processing_time / 60
        
        # Verify performance requirements
        assert result.success is True, f"Processing failed: {result.errors}"
        assert result.total_skus == 1239, f"Expected 1239 SKUs, got {result.total_skus}"
        assert result.processed_skus == 1239, f"Expected 1239 processed SKUs, got {result.processed_skus}"
        
        # Critical performance requirement: Must complete within 15 minutes
        assert processing_minutes <= 15.0, f"Processing took {processing_minutes:.2f} minutes, exceeds 15-minute limit"
        
        # Performance metrics
        skus_per_second = 1239 / processing_time
        skus_per_minute = skus_per_second * 60
        
        print(f"\n=== PERFORMANCE METRICS ===")
        print(f"Total SKUs processed: {result.processed_skus}")
        print(f"Processing time: {processing_minutes:.2f} minutes ({processing_time:.2f} seconds)")
        print(f"Processing rate: {skus_per_minute:.1f} SKUs/minute ({skus_per_second:.1f} SKUs/second)")
        print(f"Performance requirement: ✅ PASSED (< 15 minutes)")
        
        # Verify output files were created
        assert len(result.output_files) >= 3, "Expected at least 3 output files (NAXML, CSV, JSON)"
        
        # Verify file sizes are reasonable
        for file_path in result.output_files:
            file_size = Path(file_path).stat().st_size
            assert file_size > 0, f"Output file {file_path} is empty"
            print(f"Output file: {Path(file_path).name} ({file_size:,} bytes)")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_large_dataset(self, performance_config, temp_dir):
        """Test memory usage remains reasonable with large datasets"""
        import psutil
        import os
        
        # Generate test dataset
        test_data = self.generate_large_dabs_dataset(1239)
        excel_file = temp_dir / "memory_test_1239_skus.xlsx"
        self.create_performance_excel_file(test_data, excel_file)
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process file
        processor = DABSProcessor(performance_config)
        result = await processor.process_dabs_file(excel_file)
        
        # Get peak memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Verify processing succeeded
        assert result.success is True
        
        # Memory usage should be reasonable (< 500MB increase for 1,239 SKUs)
        assert memory_increase < 500, f"Memory usage increased by {memory_increase:.1f}MB, exceeds 500MB limit"
        
        print(f"\n=== MEMORY USAGE METRICS ===")
        print(f"Initial memory: {initial_memory:.1f} MB")
        print(f"Peak memory: {peak_memory:.1f} MB")
        print(f"Memory increase: {memory_increase:.1f} MB")
        print(f"Memory per SKU: {memory_increase/1239:.3f} MB/SKU")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_processing_performance(self, performance_config, temp_dir):
        """Test system performance under concurrent load"""
        # Create multiple smaller datasets
        datasets = []
        files = []
        
        for i in range(3):
            data = self.generate_large_dabs_dataset(400)  # 3 x 400 = 1200 SKUs total
            file_path = temp_dir / f"concurrent_test_{i}.xlsx"
            self.create_performance_excel_file(data, file_path)
            datasets.append(data)
            files.append(file_path)
        
        # Process files concurrently
        start_time = time.time()
        
        async def process_file(file_path):
            processor = DABSProcessor(performance_config)
            return await processor.process_dabs_file(file_path)
        
        # Run concurrent processing
        results = await asyncio.gather(*[process_file(f) for f in files])
        
        end_time = time.time()
        processing_time = end_time - start_time
        processing_minutes = processing_time / 60
        
        # Verify all processing succeeded
        total_skus = sum(result.processed_skus for result in results)
        assert all(result.success for result in results), "Some concurrent processing failed"
        assert total_skus == 1200, f"Expected 1200 total SKUs, got {total_skus}"
        
        # Concurrent processing should be faster than sequential
        # and still meet reasonable time limits
        assert processing_minutes <= 10.0, f"Concurrent processing took {processing_minutes:.2f} minutes"
        
        print(f"\n=== CONCURRENT PROCESSING METRICS ===")
        print(f"Files processed: {len(files)}")
        print(f"Total SKUs: {total_skus}")
        print(f"Processing time: {processing_minutes:.2f} minutes")
        print(f"Concurrent processing rate: {total_skus/processing_time:.1f} SKUs/second")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_integration_coordinator_performance(self, temp_dir):
        """Test end-to-end workflow performance through Integration Coordinator"""
        # Generate test dataset
        test_data = self.generate_large_dabs_dataset(500)  # Smaller for integration test
        excel_file = temp_dir / "integration_performance_test.xlsx"
        self.create_performance_excel_file(test_data, excel_file)
        
        # Initialize coordinator
        coordinator = IntegrationCoordinator()
        
        # Override directories for testing
        coordinator.config['sscs_upload_directory'] = str(temp_dir / "sscs_uploads")
        coordinator.sscs_integrator.config.upload_directory = str(temp_dir / "sscs_uploads")
        coordinator.sscs_integrator.export_dir = temp_dir
        
        # Measure end-to-end workflow time
        start_time = time.time()
        result = await coordinator.execute_workflow(excel_file)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Verify workflow succeeded
        assert result is not None
        assert result.total_skus_processed == 500
        
        # Integration workflow should complete reasonably quickly
        assert processing_time <= 120, f"Integration workflow took {processing_time:.1f}s, exceeds 2-minute limit"
        
        print(f"\n=== INTEGRATION WORKFLOW METRICS ===")
        print(f"SKUs processed: {result.total_skus_processed}")
        print(f"Workflow time: {processing_time:.1f} seconds")
        print(f"Integration rate: {500/processing_time:.1f} SKUs/second")
        print(f"Successful integrations: {len(result.successful_integrations)}")
        print(f"Failed integrations: {len(result.failed_integrations)}")
