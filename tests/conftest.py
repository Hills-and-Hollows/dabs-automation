"""
Pytest configuration and shared fixtures for DABS test suite

This module provides common test fixtures and configuration for all tests
in the DABS automation system.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import json
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from audit.audit_trail import AuditTrailManager, AuditEventType
from processors.dabs_processor import DABSProcessor, DABSProduct


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def audit_manager(temp_dir):
    """Create an audit trail manager for testing"""
    audit_dir = temp_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    return AuditTrailManager(audit_dir, retention_years=1)


@pytest.fixture
def dabs_processor(temp_dir):
    """Create a DABS processor for testing"""
    # Create test directories
    data_dir = temp_dir / "data"
    export_dir = temp_dir / "exports"
    data_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)
    
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
        'audit_retention_years': 1
    }
    
    # Save config to temp file
    config_file = temp_dir / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f)
    
    return DABSProcessor(str(config_file))


@pytest.fixture
def sample_dabs_data():
    """Create sample DABS data for testing"""
    return pd.DataFrame([
        {
            'SKU': '123456',
            'ITEM NAME': 'Test Whiskey 750ml',
            'PRICE': 29.99,
            'ITEM TYPE': 'Whiskey',
            'ITEM STATUS': 'Active',
            'ON SPA?': 'No',
            'FROM DATE': '2025-01-01',
            'TO DATE': '2025-12-31'
        },
        {
            'SKU': '789012',
            'ITEM NAME': 'Test Vodka 1L',
            'PRICE': 24.99,
            'ITEM TYPE': 'Vodka',
            'ITEM STATUS': 'Active',
            'ON SPA?': 'Yes',
            'FROM DATE': '2025-01-01',
            'TO DATE': '2025-12-31'
        },
        {
            'SKU': '345678',
            'ITEM NAME': 'Test Beer 6-pack',
            'PRICE': 12.99,
            'ITEM TYPE': 'Beer',
            'ITEM STATUS': 'Active',
            'ON SPA?': 'No',
            'FROM DATE': '2025-01-01',
            'TO DATE': '2025-12-31'
        }
    ])


@pytest.fixture
def sample_excel_file(temp_dir, sample_dabs_data):
    """Create a sample Excel file for testing"""
    excel_file = temp_dir / "test_dabs.xlsx"
    
    # Create Excel file with header row
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Add a header row (DABS files have headers in row 2)
        header_df = pd.DataFrame([['DABS Price Changes Report']])
        header_df.to_excel(writer, index=False, header=False, startrow=0)
        
        # Add the actual data starting from row 2
        sample_dabs_data.to_excel(writer, index=False, startrow=1)
    
    return excel_file


@pytest.fixture
def sample_products():
    """Create sample DABSProduct objects for testing"""
    return [
        DABSProduct(
            sku='123456',
            product_name='Test Whiskey 750ml',
            retail_price=29.99,
            category='Whiskey',
            on_special_pricing=False,
            effective_date=datetime(2025, 1, 1),
            status='Active',
            updated_on=datetime.now(),
            size_ml=750,
            upc=None
        ),
        DABSProduct(
            sku='789012',
            product_name='Test Vodka 1L',
            retail_price=24.99,
            category='Vodka',
            on_special_pricing=True,
            effective_date=datetime(2025, 1, 1),
            status='Active',
            updated_on=datetime.now(),
            size_ml=1000,
            upc=None
        )
    ]


@pytest.fixture
def invalid_dabs_data():
    """Create invalid DABS data for testing error handling"""
    return pd.DataFrame([
        {
            'SKU': '999999',
            'ITEM NAME': 'Invalid Item',
            'PRICE': -10.00,  # Invalid negative price
            'ITEM TYPE': 'Unknown',
            'ITEM STATUS': 'Active',
            'ON SPA?': 'No',
            'FROM DATE': '2025-01-01',
            'TO DATE': '2025-12-31'
        },
        {
            'SKU': '888888',
            'ITEM NAME': 'Another Invalid Item',
            'PRICE': 'not_a_number',  # Invalid non-numeric price
            'ITEM TYPE': 'Unknown',
            'ITEM STATUS': 'Active',
            'ON SPA?': 'No',
            'FROM DATE': '2025-01-01',
            'TO DATE': '2025-12-31'
        }
    ])


@pytest.fixture
def high_variance_data():
    """Create data with high price variances for testing"""
    return pd.DataFrame([
        {
            'SKU': '111111',
            'ITEM NAME': 'High Variance Item',
            'PRICE': 100.00,  # Will be compared against historical price
            'ITEM TYPE': 'Test',
            'ITEM STATUS': 'Active',
            'ON SPA?': 'No',
            'FROM DATE': '2025-01-01',
            'TO DATE': '2025-12-31'
        }
    ])


@pytest.fixture
def historical_prices():
    """Create historical price data for variance testing"""
    return {
        '111111': 50.00  # 100% increase from this historical price
    }


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance
pytest.mark.slow = pytest.mark.slow
