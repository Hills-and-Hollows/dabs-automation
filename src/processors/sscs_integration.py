#!/usr/bin/env python3
"""
SSCS Integration Module - Hills & Hollows LLC
Utah Package Agency SSCS POS Integration System

Handles integration with SSCS POS system via multiple methods:
- File-based integration (NAXML, CSV)
- API integration (when available)
- Direct database integration (if supported)

Author: DABS Automation System
Created: 2025-08-21
"""

import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import logging
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
import hashlib
import ftplib
from io import StringIO
import csv
import pandas as pd

from .dabs_processor import DABSProduct, ProcessingResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/logs/sscs_integration.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class SSCSIntegrationConfig:
    """Configuration for SSCS integration"""
    integration_method: str  # 'file', 'api', 'database'
    file_format: str  # 'naxml', 'csv', 'xml', 'json'
    upload_method: str  # 'ftp', 'sftp', 'api', 'local'
    
    # File-based configuration
    upload_directory: Optional[str] = None
    file_naming_pattern: str = "dabs_pricing_{timestamp}.{extension}"
    processing_schedule: str = "immediate"  # 'immediate', 'hourly', 'daily'
    
    # API configuration
    api_base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_version: str = "v1"
    
    # Database configuration
    db_connection_string: Optional[str] = None
    db_table_name: str = "products"
    
    # FTP configuration
    ftp_host: Optional[str] = None
    ftp_username: Optional[str] = None
    ftp_password: Optional[str] = None
    ftp_directory: str = "/incoming"
    
    # Validation and error handling
    validate_before_upload: bool = True
    max_retry_attempts: int = 3
    timeout_seconds: int = 300
    backup_failed_uploads: bool = True

@dataclass
class IntegrationResult:
    """Result of SSCS integration attempt"""
    success: bool
    integration_method: str
    skus_uploaded: int
    upload_time: float
    file_path: Optional[str] = None
    api_response: Optional[Dict] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    retry_attempts: int = 0
    checksum: Optional[str] = None

    def __post_init__(self):
        """Initialize lists if None"""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

class SSCSIntegrator:
    """
    SSCS POS Integration Manager
    
    Supports multiple integration methods:
    1. File-based: NAXML, CSV exports with FTP/SFTP upload
    2. API-based: REST API integration (when available)
    3. Database: Direct database connection (if supported)
    """
    
    def __init__(self, config: SSCSIntegrationConfig):
        self.config = config
        self.export_dir = Path('/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/exports')
        self.failed_uploads_dir = self.export_dir / 'failed_uploads'
        
        # Ensure directories exist
        for directory in [self.export_dir, self.failed_uploads_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        logger.info(f"SSCS Integrator initialized with method: {config.integration_method}")

    async def upload_pricing_data(self, products: List[DABSProduct]) -> IntegrationResult:
        """
        Main method to upload pricing data to SSCS system
        
        Args:
            products: List of DABS products to upload
            
        Returns:
            IntegrationResult with upload status and details
        """
        start_time = datetime.now()
        
        logger.info(f"Starting SSCS upload: {len(products)} products via {self.config.integration_method}")
        
        try:
            # Validate products before upload
            if self.config.validate_before_upload:
                validation_errors = await self._validate_products(products)
                if validation_errors:
                    return IntegrationResult(
                        success=False,
                        integration_method=self.config.integration_method,
                        skus_uploaded=0,
                        upload_time=0,
                        errors=validation_errors
                    )
            
            # Route to appropriate integration method
            if self.config.integration_method == 'file':
                result = await self._upload_via_file(products)
            elif self.config.integration_method == 'api':
                result = await self._upload_via_api(products)
            elif self.config.integration_method == 'database':
                result = await self._upload_via_database(products)
            else:
                raise ValueError(f"Unsupported integration method: {self.config.integration_method}")
            
            upload_time = (datetime.now() - start_time).total_seconds()
            result.upload_time = upload_time
            
            if result.success:
                logger.info(f"SSCS upload completed successfully: {result.skus_uploaded} SKUs in {upload_time:.2f}s")
            else:
                logger.error(f"SSCS upload failed: {result.errors}")
                
            return result
            
        except Exception as e:
            upload_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"SSCS upload exception: {str(e)}")
            
            return IntegrationResult(
                success=False,
                integration_method=self.config.integration_method,
                skus_uploaded=0,
                upload_time=upload_time,
                errors=[str(e)]
            )

    async def _upload_via_file(self, products: List[DABSProduct]) -> IntegrationResult:
        """Upload pricing data via file-based integration"""
        try:
            # Generate file in requested format
            if self.config.file_format == 'naxml':
                file_path = await self._generate_naxml_file(products)
            elif self.config.file_format == 'csv':
                file_path = await self._generate_csv_file(products)
            elif self.config.file_format == 'xml':
                file_path = await self._generate_xml_file(products)
            elif self.config.file_format == 'json':
                file_path = await self._generate_json_file(products)
            else:
                raise ValueError(f"Unsupported file format: {self.config.file_format}")
            
            # Upload file using configured method
            if self.config.upload_method == 'ftp':
                upload_success = await self._upload_via_ftp(file_path)
            elif self.config.upload_method == 'sftp':
                upload_success = await self._upload_via_sftp(file_path)
            elif self.config.upload_method == 'api':
                upload_success = await self._upload_file_via_api(file_path)
            elif self.config.upload_method == 'local':
                upload_success = await self._copy_to_local_directory(file_path)
            else:
                raise ValueError(f"Unsupported upload method: {self.config.upload_method}")
            
            if upload_success:
                checksum = await self._calculate_file_checksum(file_path)
                return IntegrationResult(
                    success=True,
                    integration_method='file',
                    skus_uploaded=len(products),
                    upload_time=0,  # Will be set by caller
                    file_path=str(file_path),
                    checksum=checksum
                )
            else:
                return IntegrationResult(
                    success=False,
                    integration_method='file',
                    skus_uploaded=0,
                    upload_time=0,
                    errors=[f"Failed to upload file via {self.config.upload_method}"]
                )
                
        except Exception as e:
            return IntegrationResult(
                success=False,
                integration_method='file',
                skus_uploaded=0,
                upload_time=0,
                errors=[str(e)]
            )

    async def _upload_via_api(self, products: List[DABSProduct]) -> IntegrationResult:
        """Upload pricing data via REST API (when available)"""
        if not self.config.api_base_url:
            return IntegrationResult(
                success=False,
                integration_method='api',
                skus_uploaded=0,
                upload_time=0,
                errors=["API base URL not configured"]
            )
        
        try:
            async with aiohttp.ClientSession() as session:
                # Prepare API payload
                payload = {
                    "source": "DABS-Hills-Hollows",
                    "timestamp": datetime.now().isoformat(),
                    "products": []
                }
                
                for product in products:
                    payload["products"].append({
                        "sku": product.sku,
                        "name": product.product_name,
                        "price": product.retail_price,
                        "category": product.category,
                        "status": product.status,
                        "effective_date": product.effective_date.isoformat(),
                        "on_special": product.on_special_pricing
                    })
                
                # Prepare headers
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "DABS-Automation/1.0"
                }
                
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"
                
                # Make API request
                url = f"{self.config.api_base_url}/products/bulk_update"
                
                async with session.post(
                    url, 
                    json=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                ) as response:
                    
                    if response.status in [200, 201, 202]:
                        response_data = await response.json()
                        return IntegrationResult(
                            success=True,
                            integration_method='api',
                            skus_uploaded=len(products),
                            upload_time=0,
                            api_response=response_data
                        )
                    else:
                        error_text = await response.text()
                        return IntegrationResult(
                            success=False,
                            integration_method='api',
                            skus_uploaded=0,
                            upload_time=0,
                            errors=[f"API error {response.status}: {error_text}"]
                        )
                        
        except Exception as e:
            return IntegrationResult(
                success=False,
                integration_method='api',
                skus_uploaded=0,
                upload_time=0,
                errors=[str(e)]
            )

    async def _upload_via_database(self, products: List[DABSProduct]) -> IntegrationResult:
        """Upload pricing data via direct database connection"""
        # Note: This is a placeholder for database integration
        # Actual implementation would depend on SSCS database schema
        
        return IntegrationResult(
            success=False,
            integration_method='database',
            skus_uploaded=0,
            upload_time=0,
            errors=["Database integration not yet implemented - awaiting SSCS vendor documentation"]
        )

    async def _generate_naxml_file(self, products: List[DABSProduct]) -> Path:
        """Generate NAXML ItemSynch file for SSCS CPB Vendor Import"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Use DABS prefix for CPB vendor import recognition
        filename = f"DABS_{timestamp}_ItemPrice.xml"
        file_path = self.export_dir / filename
        
        # Create NAXML structure for SSCS CPB Vendor Import
        root = ET.Element("ItemSynch")
        root.set("version", "2.0")
        root.set("timestamp", datetime.now().isoformat())
        root.set("vendor", "DABS")  # CPB vendor identifier

        # Header for CPB import
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "Source").text = "DABS"
        ET.SubElement(header, "Destination").text = "SSCS-CPB"
        ET.SubElement(header, "VendorName").text = "DABS"
        ET.SubElement(header, "VendorZone").text = "ZONE0_GLOBAL"
        ET.SubElement(header, "RecordCount").text = str(len(products))
        ET.SubElement(header, "GeneratedDate").text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ET.SubElement(header, "ApplyVendorListPrice").text = "true"
        
        # Items for CPB vendor import
        items = ET.SubElement(root, "Items")

        for product in products:
            item = ET.SubElement(items, "Item")

            # Core item identification
            ET.SubElement(item, "VendorItemCode").text = product.sku
            ET.SubElement(item, "UPC").text = getattr(product, 'upc', '')
            ET.SubElement(item, "Description").text = product.product_name
            ET.SubElement(item, "Category").text = product.category
            ET.SubElement(item, "Status").text = "Active"  # CPB expects Active/Inactive

            # Pricing for CPB import
            pricing = ET.SubElement(item, "Pricing")
            ET.SubElement(pricing, "VendorListPrice").text = f"{product.retail_price:.2f}"
            ET.SubElement(pricing, "EffectiveDate").text = product.effective_date.strftime("%Y-%m-%d")
            ET.SubElement(pricing, "PriceType").text = "Regular"

            # CPB-specific attributes
            attributes = ET.SubElement(item, "Attributes")
            ET.SubElement(attributes, "VendorZone").text = "ZONE0_GLOBAL"
            ET.SubElement(attributes, "AutoAccept").text = "false"  # Manual review initially
        
        # Write file
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        
        logger.info(f"Generated NAXML file: {file_path}")
        return file_path

    async def _generate_csv_file(self, products: List[DABSProduct]) -> Path:
        """Generate CSV file for SSCS integration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.config.file_naming_pattern.format(
            timestamp=timestamp, 
            extension="csv"
        )
        file_path = self.export_dir / filename
        
        # Create CSV data
        fieldnames = [
            'SKU', 'ProductName', 'RetailPrice', 'Category', 
            'OnSpecialPricing', 'EffectiveDate', 'Status', 'UpdatedOn'
        ]
        
        async with aiofiles.open(file_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            await writer.writeheader()
            
            for product in products:
                await writer.writerow({
                    'SKU': product.sku,
                    'ProductName': product.product_name,
                    'RetailPrice': f"{product.retail_price:.2f}",
                    'Category': product.category,
                    'OnSpecialPricing': 'Yes' if product.on_special_pricing else 'No',
                    'EffectiveDate': product.effective_date.strftime('%Y-%m-%d'),
                    'Status': product.status,
                    'UpdatedOn': product.updated_on.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        logger.info(f"Generated CSV file: {file_path}")
        return file_path

    async def _generate_xml_file(self, products: List[DABSProduct]) -> Path:
        """Generate generic XML file for SSCS integration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.config.file_naming_pattern.format(
            timestamp=timestamp, 
            extension="xml"
        )
        file_path = self.export_dir / filename
        
        # Create XML structure
        root = ET.Element("PriceUpdate")
        root.set("source", "DABS-Hills-Hollows")
        root.set("timestamp", datetime.now().isoformat())
        root.set("count", str(len(products)))
        
        for product in products:
            item = ET.SubElement(root, "Product")
            item.set("sku", product.sku)
            
            ET.SubElement(item, "Name").text = product.product_name
            ET.SubElement(item, "Price").text = f"{product.retail_price:.2f}"
            ET.SubElement(item, "Category").text = product.category
            ET.SubElement(item, "Status").text = product.status
            ET.SubElement(item, "EffectiveDate").text = product.effective_date.strftime("%Y-%m-%d")
            ET.SubElement(item, "OnSpecial").text = "true" if product.on_special_pricing else "false"
        
        # Write file
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        
        logger.info(f"Generated XML file: {file_path}")
        return file_path

    async def _generate_json_file(self, products: List[DABSProduct]) -> Path:
        """Generate JSON file for SSCS integration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.config.file_naming_pattern.format(
            timestamp=timestamp, 
            extension="json"
        )
        file_path = self.export_dir / filename
        
        # Create JSON structure
        data = {
            "metadata": {
                "source": "DABS-Hills-Hollows-LLC",
                "generated_date": datetime.now().isoformat(),
                "total_items": len(products),
                "format_version": "1.0"
            },
            "products": []
        }
        
        for product in products:
            data["products"].append({
                "sku": product.sku,
                "name": product.product_name,
                "price": product.retail_price,
                "category": product.category,
                "status": product.status,
                "effective_date": product.effective_date.isoformat(),
                "on_special": product.on_special_pricing,
                "updated_on": product.updated_on.isoformat()
            })
        
        # Write file
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(data, indent=2))
        
        logger.info(f"Generated JSON file: {file_path}")
        return file_path

    async def _upload_via_ftp(self, file_path: Path) -> bool:
        """Upload file via FTP"""
        if not all([self.config.ftp_host, self.config.ftp_username, self.config.ftp_password]):
            logger.error("FTP configuration incomplete")
            return False
        
        try:
            # Note: This is a synchronous FTP implementation
            # For production, consider using aioftp for async FTP
            def ftp_upload():
                with ftplib.FTP(self.config.ftp_host) as ftp:
                    ftp.login(self.config.ftp_username, self.config.ftp_password)
                    ftp.cwd(self.config.ftp_directory)
                    
                    with open(file_path, 'rb') as f:
                        ftp.storbinary(f'STOR {file_path.name}', f)
                        
                return True
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, ftp_upload)
            
            logger.info(f"FTP upload successful: {file_path.name}")
            return success
            
        except Exception as e:
            logger.error(f"FTP upload failed: {str(e)}")
            return False

    async def _upload_via_sftp(self, file_path: Path) -> bool:
        """Upload file via SFTP (placeholder)"""
        logger.warning("SFTP upload not yet implemented")
        return False

    async def _upload_file_via_api(self, file_path: Path) -> bool:
        """Upload file via API endpoint"""
        if not self.config.api_base_url:
            logger.error("API base URL not configured")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.config.api_base_url}/files/upload"
                
                with open(file_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename=file_path.name)
                    
                    headers = {}
                    if self.config.api_key:
                        headers["Authorization"] = f"Bearer {self.config.api_key}"
                    
                    async with session.post(url, data=data, headers=headers) as response:
                        if response.status in [200, 201]:
                            logger.info(f"API file upload successful: {file_path.name}")
                            return True
                        else:
                            logger.error(f"API file upload failed: {response.status}")
                            return False
                            
        except Exception as e:
            logger.error(f"API file upload failed: {str(e)}")
            return False

    async def _copy_to_local_directory(self, file_path: Path) -> bool:
        """Copy file to local directory for SSCS to pick up"""
        if not self.config.upload_directory:
            logger.error("Upload directory not configured")
            return False
        
        try:
            import shutil
            destination_dir = Path(self.config.upload_directory)
            destination_dir.mkdir(parents=True, exist_ok=True)
            
            destination_path = destination_dir / file_path.name
            shutil.copy2(file_path, destination_path)
            
            logger.info(f"File copied to local directory: {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Local file copy failed: {str(e)}")
            return False

    async def _validate_products(self, products: List[DABSProduct]) -> List[str]:
        """Validate products before upload"""
        errors = []
        
        if not products:
            errors.append("No products to upload")
            return errors
        
        # Check for required fields
        for i, product in enumerate(products):
            if not product.sku:
                errors.append(f"Product {i}: Missing SKU")
            if not product.product_name:
                errors.append(f"Product {i}: Missing product name")
            if product.retail_price <= 0:
                errors.append(f"Product {i}: Invalid price: {product.retail_price}")
        
        # Check for duplicate SKUs
        skus = [p.sku for p in products]
        duplicates = set([sku for sku in skus if skus.count(sku) > 1])
        if duplicates:
            errors.append(f"Duplicate SKUs found: {', '.join(duplicates)}")
        
        return errors

    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate checksum for uploaded file"""
        hash_sha256 = hashlib.sha256()
        
        async with aiofiles.open(file_path, 'rb') as f:
            chunk = await f.read(8192)
            while chunk:
                hash_sha256.update(chunk)
                chunk = await f.read(8192)
        
        return hash_sha256.hexdigest()

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to SSCS system"""
        test_result = {
            "method": self.config.integration_method,
            "integration_method": self.config.integration_method,
            "success": False,
            "details": {},
            "errors": []
        }
        
        try:
            if self.config.integration_method == 'file':
                if self.config.upload_method == 'ftp':
                    # Test FTP connection
                    if not all([self.config.ftp_host, self.config.ftp_username, self.config.ftp_password]):
                        test_result["errors"].append("FTP configuration incomplete")
                        return test_result
                    
                    # Attempt connection
                    def test_ftp():
                        with ftplib.FTP(self.config.ftp_host, timeout=10) as ftp:
                            ftp.login(self.config.ftp_username, self.config.ftp_password)
                            return ftp.pwd()
                    
                    loop = asyncio.get_event_loop()
                    current_dir = await loop.run_in_executor(None, test_ftp)
                    
                    test_result["success"] = True
                    test_result["details"] = {
                        "ftp_host": self.config.ftp_host,
                        "current_directory": current_dir
                    }
                    
                elif self.config.upload_method == 'local':
                    # Test local directory access
                    if self.config.upload_directory:
                        upload_dir = Path(self.config.upload_directory)
                        upload_dir.mkdir(parents=True, exist_ok=True)
                        
                        test_result["success"] = upload_dir.exists() and upload_dir.is_dir()
                        test_result["details"] = {
                            "upload_directory": str(upload_dir),
                            "writable": upload_dir.stat().st_mode & 0o200 != 0
                        }
                    else:
                        test_result["errors"].append("Upload directory not configured")
                        
            elif self.config.integration_method == 'api':
                if self.config.api_base_url:
                    async with aiohttp.ClientSession() as session:
                        url = f"{self.config.api_base_url}/health"
                        
                        headers = {}
                        if self.config.api_key:
                            headers["Authorization"] = f"Bearer {self.config.api_key}"
                        
                        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            test_result["success"] = response.status == 200
                            test_result["details"] = {
                                "status_code": response.status,
                                "response": await response.text()
                            }
                else:
                    test_result["errors"].append("API base URL not configured")
                    
            return test_result
            
        except Exception as e:
            test_result["errors"].append(str(e))
            return test_result

# Factory function for creating integrators
def create_sscs_integrator(
    integration_method: str = 'file',
    file_format: str = 'csv',
    upload_method: str = 'local',
    **kwargs
) -> SSCSIntegrator:
    """
    Factory function to create SSCS integrator with common configurations

    Args:
        integration_method: 'file', 'api', or 'database'
        file_format: 'naxml', 'csv', 'xml', 'json'
        upload_method: 'ftp', 'sftp', 'api', 'local'
        **kwargs: Additional configuration parameters

    Returns:
        Configured SSCSIntegrator instance
    """
    config = SSCSIntegrationConfig(
        integration_method=integration_method,
        file_format=file_format,
        upload_method=upload_method,
        **kwargs
    )

    return SSCSIntegrator(config)

def create_sscs_cpb_integrator(
    upload_directory: str = '/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/exports/sscs_cpb',
    **kwargs
) -> SSCSIntegrator:
    """
    Factory function to create SSCS CPB (Central Price Book) integrator
    Configured specifically for SSCS CPB Vendor Import functionality

    Args:
        upload_directory: Directory where CPB import files will be placed
        **kwargs: Additional configuration parameters

    Returns:
        SSCSIntegrator configured for CPB vendor import
    """
    config = SSCSIntegrationConfig(
        integration_method='file',
        file_format='naxml',
        upload_method='local',
        upload_directory=upload_directory,
        file_naming_pattern="DABS_{timestamp}_ItemPrice.xml",
        validate_before_upload=True,
        **kwargs
    )

    return SSCSIntegrator(config)

if __name__ == "__main__":
    # Test the integrator
    async def test_integration():
        integrator = create_sscs_integrator(
            integration_method='file',
            file_format='csv',
            upload_method='local',
            upload_directory='/tmp/sscs_test'
        )
        
        test_result = await integrator.test_connection()
        print(f"Connection test: {test_result}")

    asyncio.run(test_integration())
