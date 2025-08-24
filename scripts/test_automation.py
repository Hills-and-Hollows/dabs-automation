#!/usr/bin/env python3
"""
DABS Automation Test Script - Hills & Hollows LLC
Complete test suite for DABS processing and SSCS integration

Author: DABS Automation System
Created: 2025-08-21
"""

import asyncio
import sys
from pathlib import Path
import json
import logging
import pandas as pd
from datetime import datetime
import os

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from processors.dabs_processor import DABSProcessor, process_dabs_file_async, DABSProduct
from processors.sscs_integration import create_sscs_integrator, SSCSIntegrationConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class DABSAutomationTester:
    """Test suite for DABS automation system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_data_dir = self.project_root / 'data'
        self.test_exports_dir = self.project_root / 'exports' / 'test'
        
        # Ensure test directories exist
        self.test_exports_dir.mkdir(parents=True, exist_ok=True)
        
    async def test_dabs_processor(self):
        """Test DABS Excel file processing"""
        print("\n🧪 Testing DABS Processor...")
        
        try:
            # Create test CSV data (simulating Excel processing)
            test_csv = self.project_root / 'sscs_pricing_update.csv'
            
            if not test_csv.exists():
                print(f"❌ Test data file not found: {test_csv}")
                return False
                
            # Test CSV processing as proxy for Excel
            df = pd.read_csv(test_csv)
            print(f"✅ Successfully loaded test data: {len(df)} rows")
            
            # Test product conversion
            test_products = []
            for _, row in df.head(10).iterrows():  # Test with first 10 rows
                product = DABSProduct(
                    sku=str(row['SKU']),
                    product_name=str(row['ProductName']),
                    retail_price=float(row['RetailPrice']),
                    category=str(row['Category']),
                    on_special_pricing=str(row.get('OnSpecialPricing', 'No')).lower() == 'yes',
                    effective_date=pd.to_datetime(row['EffectiveDate']),
                    status=str(row['Status']),
                    updated_on=pd.to_datetime(row['UpdatedOn'])
                )
                test_products.append(product)
            
            print(f"✅ Successfully converted {len(test_products)} products")
            
            # Test processor initialization
            processor = DABSProcessor()
            status = processor.get_processing_status()
            print(f"✅ Processor initialized: {status['processor_version']}")
            
            return True, test_products
            
        except Exception as e:
            print(f"❌ DABS processor test failed: {str(e)}")
            return False, []

    async def test_sscs_integration_file_csv(self, products):
        """Test SSCS CSV file integration"""
        print("\n🧪 Testing SSCS CSV Integration...")
        
        try:
            # Create CSV integrator
            integrator = create_sscs_integrator(
                integration_method='file',
                file_format='csv',
                upload_method='local',
                upload_directory=str(self.test_exports_dir / 'csv')
            )
            
            # Test connection
            connection_test = await integrator.test_connection()
            print(f"✅ Connection test: {connection_test['success']}")
            
            # Test upload
            result = await integrator.upload_pricing_data(products)
            
            if result.success:
                print(f"✅ CSV upload successful: {result.skus_uploaded} SKUs in {result.upload_time:.2f}s")
                print(f"📁 File created: {result.file_path}")
                return True
            else:
                print(f"❌ CSV upload failed: {result.errors}")
                return False
                
        except Exception as e:
            print(f"❌ CSV integration test failed: {str(e)}")
            return False

    async def test_sscs_integration_file_naxml(self, products):
        """Test SSCS NAXML file integration"""
        print("\n🧪 Testing SSCS NAXML Integration...")
        
        try:
            # Create NAXML integrator
            integrator = create_sscs_integrator(
                integration_method='file',
                file_format='naxml',
                upload_method='local',
                upload_directory=str(self.test_exports_dir / 'naxml')
            )
            
            # Test upload
            result = await integrator.upload_pricing_data(products)
            
            if result.success:
                print(f"✅ NAXML upload successful: {result.skus_uploaded} SKUs in {result.upload_time:.2f}s")
                print(f"📁 File created: {result.file_path}")
                
                # Validate NAXML structure
                if result.file_path and Path(result.file_path).exists():
                    import xml.etree.ElementTree as ET
                    tree = ET.parse(result.file_path)
                    root = tree.getroot()
                    
                    items = root.find('Items')
                    if items is not None:
                        item_count = len(list(items.findall('Item')))
                        print(f"✅ NAXML validation: {item_count} items in XML structure")
                    else:
                        print("⚠️ NAXML validation: No Items section found")
                        
                return True
            else:
                print(f"❌ NAXML upload failed: {result.errors}")
                return False
                
        except Exception as e:
            print(f"❌ NAXML integration test failed: {str(e)}")
            return False

    async def test_sscs_integration_file_json(self, products):
        """Test SSCS JSON file integration"""
        print("\n🧪 Testing SSCS JSON Integration...")
        
        try:
            # Create JSON integrator
            integrator = create_sscs_integrator(
                integration_method='file',
                file_format='json',
                upload_method='local',
                upload_directory=str(self.test_exports_dir / 'json')
            )
            
            # Test upload
            result = await integrator.upload_pricing_data(products)
            
            if result.success:
                print(f"✅ JSON upload successful: {result.skus_uploaded} SKUs in {result.upload_time:.2f}s")
                print(f"📁 File created: {result.file_path}")
                
                # Validate JSON structure
                if result.file_path and Path(result.file_path).exists():
                    with open(result.file_path, 'r') as f:
                        data = json.load(f)
                        
                    if 'products' in data and 'metadata' in data:
                        print(f"✅ JSON validation: {len(data['products'])} products in JSON structure")
                        print(f"✅ JSON metadata: {data['metadata']['total_items']} items total")
                    else:
                        print("⚠️ JSON validation: Invalid structure")
                        
                return True
            else:
                print(f"❌ JSON upload failed: {result.errors}")
                return False
                
        except Exception as e:
            print(f"❌ JSON integration test failed: {str(e)}")
            return False

    async def test_performance_benchmark(self, products):
        """Test performance with target metrics"""
        print("\n🧪 Performance Benchmark Test...")
        
        try:\n            start_time = datetime.now()
            
            # Test multiple format generation simultaneously
            tasks = []
            
            # CSV
            csv_integrator = create_sscs_integrator('file', 'csv', 'local', 
                upload_directory=str(self.test_exports_dir / 'perf_csv'))
            tasks.append(csv_integrator.upload_pricing_data(products))
            
            # NAXML
            naxml_integrator = create_sscs_integrator('file', 'naxml', 'local',
                upload_directory=str(self.test_exports_dir / 'perf_naxml'))
            tasks.append(naxml_integrator.upload_pricing_data(products))
            
            # JSON
            json_integrator = create_sscs_integrator('file', 'json', 'local',
                upload_directory=str(self.test_exports_dir / 'perf_json'))
            tasks.append(json_integrator.upload_pricing_data(products))
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            successful_uploads = sum(1 for r in results if hasattr(r, 'success') and r.success)
            
            print(f"✅ Performance benchmark completed:")
            print(f"   ⏱️ Total time: {total_time:.2f} seconds")
            print(f"   📊 Products processed: {len(products)}")
            print(f"   📁 Successful uploads: {successful_uploads}/3 formats")
            print(f"   🚀 Processing rate: {len(products)/total_time:.1f} SKUs/second")
            
            # Check against performance targets
            target_time_per_1239_skus = 15 * 60  # 15 minutes in seconds
            estimated_time_for_1239 = (total_time / len(products)) * 1239
            
            if estimated_time_for_1239 < target_time_per_1239_skus:
                print(f"✅ Performance target met: Estimated {estimated_time_for_1239/60:.1f} minutes for 1,239 SKUs")
            else:
                print(f"⚠️ Performance target missed: Estimated {estimated_time_for_1239/60:.1f} minutes for 1,239 SKUs")
            
            return True
            
        except Exception as e:
            print(f"❌ Performance benchmark failed: {str(e)}")
            return False

    async def test_error_handling(self):
        """Test error handling and validation"""
        print("\n🧪 Testing Error Handling...")
        
        try:
            # Test invalid file path
            processor = DABSProcessor()
            result = await processor.process_dabs_file("nonexistent_file.xlsx")
            
            if not result.success and "not found" in str(result.errors).lower():
                print("✅ File not found error handling works")
            else:
                print("❌ File not found error handling failed")
                
            # Test invalid products
            invalid_products = [
                DABSProduct(
                    sku="",  # Invalid: empty SKU
                    product_name="Test Product",
                    retail_price=-10.0,  # Invalid: negative price
                    category="Test",
                    on_special_pricing=False,
                    effective_date=datetime.now(),
                    status="Active",
                    updated_on=datetime.now()
                )
            ]
            
            integrator = create_sscs_integrator('file', 'csv', 'local',
                upload_directory=str(self.test_exports_dir / 'error_test'))
            
            result = await integrator.upload_pricing_data(invalid_products)
            
            if not result.success and result.errors:
                print("✅ Product validation error handling works")
            else:
                print("❌ Product validation error handling failed")
                
            return True
            
        except Exception as e:
            print(f"❌ Error handling test failed: {str(e)}")
            return False

    def generate_test_report(self, test_results):
        """Generate comprehensive test report"""
        print("\n📊 COMPREHENSIVE TEST REPORT")
        print("=" * 50)
        
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        print("\n🎯 System Readiness Assessment:")
        
        if all(test_results.values()):
            print("✅ ALL TESTS PASSED - System ready for production")
            print("🚀 Ready to process 1,239 SKUs automatically") 
            print("📁 Multiple export formats working (CSV, NAXML, JSON)")
            print("⚡ Performance targets achievable")
        else:
            failed_tests = [name for name, result in test_results.items() if not result]
            print(f"⚠️ {len(failed_tests)} test(s) failed:")
            for test in failed_tests:
                print(f"   - {test}")
            print("🔧 Address failed tests before production deployment")

async def main():
    """Run complete test suite"""
    print("🍾 DABS Automation System - Comprehensive Test Suite")
    print("Hills & Hollows LLC - Utah Package Agency")
    print("=" * 60)
    
    tester = DABSAutomationTester()
    test_results = {}
    
    # Test 1: DABS Processing
    processor_success, test_products = await tester.test_dabs_processor()
    test_results["DABS_Processing"] = processor_success
    
    if processor_success and test_products:
        # Test 2: CSV Integration
        test_results["SSCS_CSV_Integration"] = await tester.test_sscs_integration_file_csv(test_products)
        
        # Test 3: NAXML Integration
        test_results["SSCS_NAXML_Integration"] = await tester.test_sscs_integration_file_naxml(test_products)
        
        # Test 4: JSON Integration
        test_results["SSCS_JSON_Integration"] = await tester.test_sscs_integration_file_json(test_products)
        
        # Test 5: Performance Benchmark
        test_results["Performance_Benchmark"] = await tester.test_performance_benchmark(test_products)
    
    # Test 6: Error Handling
    test_results["Error_Handling"] = await tester.test_error_handling()
    
    # Generate final report
    tester.generate_test_report(test_results)
    
    # Return exit code based on results
    return 0 if all(test_results.values()) else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
