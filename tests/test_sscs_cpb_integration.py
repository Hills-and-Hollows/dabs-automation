#!/usr/bin/env python3
"""
Test SSCS CPB Integration - Hills & Hollows LLC
Tests the SSCS Central Price Book vendor import functionality

Author: DABS Automation System
Created: 2025-08-22
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# Import our modules
import sys
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from processors.sscs_integration import create_sscs_cpb_integrator, SSCSIntegrationConfig
from processors.dabs_processor import DABSProduct


@pytest.fixture
def sample_products():
    """Create sample DABS products for testing"""
    return [
        DABSProduct(
            sku="12345",
            product_name="Test Whiskey 750ml",
            retail_price=29.99,
            category="Spirits",
            status="Active",
            effective_date=datetime.now(),
            on_special_pricing=False,
            size_ml=750,
            updated_on=datetime.now()
        ),
        DABSProduct(
            sku="67890",
            product_name="Test Vodka 1L",
            retail_price=24.99,
            category="Spirits",
            status="Active",
            effective_date=datetime.now(),
            on_special_pricing=True,
            size_ml=1000,
            updated_on=datetime.now()
        )
    ]


@pytest.fixture
def temp_export_dir():
    """Create temporary directory for exports"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


class TestSSCSCPBIntegration:
    """Test suite for SSCS CPB integration"""
    
    def test_cpb_integrator_creation(self, temp_export_dir):
        """Test creating CPB integrator with correct configuration"""
        integrator = create_sscs_cpb_integrator(
            upload_directory=str(temp_export_dir)
        )
        
        assert integrator.config.integration_method == 'file'
        assert integrator.config.file_format == 'naxml'
        assert integrator.config.upload_method == 'local'
        assert "DABS_" in integrator.config.file_naming_pattern
        assert "ItemPrice.xml" in integrator.config.file_naming_pattern
        assert integrator.config.validate_before_upload is True
    
    @pytest.mark.asyncio
    async def test_naxml_generation_cpb_format(self, sample_products, temp_export_dir):
        """Test NAXML generation with CPB vendor import format"""
        integrator = create_sscs_cpb_integrator(
            upload_directory=str(temp_export_dir)
        )
        
        # Override export directory for testing
        integrator.export_dir = temp_export_dir
        
        # Generate NAXML file
        naxml_file = await integrator._generate_naxml_file(sample_products)
        
        # Verify file was created
        assert naxml_file.exists()
        assert naxml_file.name.startswith("DABS_")
        assert naxml_file.name.endswith("_ItemPrice.xml")
        
        # Parse and validate XML structure
        tree = ET.parse(naxml_file)
        root = tree.getroot()
        
        # Validate root element
        assert root.tag == "ItemSynch"
        assert root.get("version") == "2.0"
        assert root.get("vendor") == "DABS"
        
        # Validate header
        header = root.find("Header")
        assert header is not None
        assert header.find("Source").text == "DABS"
        assert header.find("Destination").text == "SSCS-CPB"
        assert header.find("VendorName").text == "DABS"
        assert header.find("VendorZone").text == "ZONE0_GLOBAL"
        assert header.find("RecordCount").text == "2"
        assert header.find("ApplyVendorListPrice").text == "true"
        
        # Validate items
        items = root.find("Items")
        assert items is not None
        
        item_elements = items.findall("Item")
        assert len(item_elements) == 2
        
        # Validate first item
        first_item = item_elements[0]
        assert first_item.find("VendorItemCode").text == "12345"
        assert first_item.find("Description").text == "Test Whiskey 750ml"
        assert first_item.find("Category").text == "Spirits"
        assert first_item.find("Status").text == "Active"
        
        # Validate pricing
        pricing = first_item.find("Pricing")
        assert pricing is not None
        assert pricing.find("VendorListPrice").text == "29.99"
        assert pricing.find("PriceType").text == "Regular"
        
        # Validate attributes
        attributes = first_item.find("Attributes")
        assert attributes is not None
        assert attributes.find("VendorZone").text == "ZONE0_GLOBAL"
        assert attributes.find("AutoAccept").text == "false"
    
    @pytest.mark.asyncio
    async def test_cpb_integration_workflow(self, sample_products, temp_export_dir):
        """Test complete CPB integration workflow"""
        integrator = create_sscs_cpb_integrator(
            upload_directory=str(temp_export_dir / "cpb_import")
        )
        
        # Override export directory for testing
        integrator.export_dir = temp_export_dir
        
        # Run integration
        result = await integrator.upload_pricing_data(sample_products)
        
        # Verify result
        assert result.success is True
        assert result.integration_method == 'file'
        assert result.skus_uploaded == 2
        assert len(result.errors) == 0
        
        # Verify file was created in upload directory
        upload_dir = Path(temp_export_dir / "cpb_import")
        assert upload_dir.exists()
        
        xml_files = list(upload_dir.glob("DABS_*_ItemPrice.xml"))
        assert len(xml_files) == 1
        
        # Verify file content
        xml_file = xml_files[0]
        tree = ET.parse(xml_file)
        root = tree.getroot()
        assert root.get("vendor") == "DABS"
    
    @pytest.mark.asyncio
    async def test_connection_test(self, temp_export_dir):
        """Test connection testing for CPB integration"""
        integrator = create_sscs_cpb_integrator(
            upload_directory=str(temp_export_dir)
        )
        
        # Test connection (should succeed for local file method)
        test_result = await integrator.test_connection()
        
        assert test_result["success"] is True
        assert test_result["integration_method"] == "file"
        assert len(test_result["errors"]) == 0
    
    def test_cpb_configuration_validation(self):
        """Test CPB configuration validation"""
        # Test with valid configuration
        config = SSCSIntegrationConfig(
            integration_method='file',
            file_format='naxml',
            upload_method='local',
            upload_directory='/tmp/test'
        )
        
        integrator = create_sscs_cpb_integrator()
        assert integrator.config.integration_method == 'file'
        assert integrator.config.file_format == 'naxml'


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
