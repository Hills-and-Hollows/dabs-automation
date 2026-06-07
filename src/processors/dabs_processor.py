#!/usr/bin/env python3
"""
DABS Processing Engine - Hills & Hollows LLC
Utah Package Agency Liquor Inventory Management

Processes DABS monthly Excel files (1,239+ SKUs) and converts to standardized formats
for SSCS POS integration via NAXML, CSV, or API endpoints.

Author: DABS Automation System
Created: 2025-08-21
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import sys
import re

# Import audit trail system
try:
    from ..audit.audit_trail import AuditTrailManager, AuditEventType
except ImportError:
    try:
        # Try absolute import for standalone execution
        from audit.audit_trail import AuditTrailManager, AuditEventType
    except ImportError:
        # Handle case where audit module is not available
        AuditTrailManager = None
        AuditEventType = None

# Configure logging
_log_handlers = [logging.StreamHandler()]
_log_path = Path('/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/logs/dabs_processor.log')
try:
    _log_path.parent.mkdir(parents=True, exist_ok=True)
    _log_handlers.insert(0, logging.FileHandler(_log_path))
except OSError:
    # Log directory unavailable (e.g. CI or non-dev machines); stream logging only
    pass
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=_log_handlers,
)

logger = logging.getLogger(__name__)

@dataclass
class DABSProduct:
    """Data class for DABS product information"""
    sku: str
    product_name: str
    retail_price: float
    category: str
    on_special_pricing: bool
    effective_date: datetime
    status: str
    updated_on: datetime
    size_ml: Optional[str] = None
    upc: Optional[str] = None
    vendor_code: Optional[str] = None
    cost_price: Optional[float] = None
    markup_percent: Optional[float] = None

@dataclass
class ProcessingResult:
    """Results from DABS file processing"""
    success: bool
    total_skus: int
    processed_skus: int
    failed_skus: int
    errors: List[str]
    warnings: List[str]
    processing_time: float
    output_files: List[str]
    checksum: str
    exceptions: List[Dict] = None  # Price validation exceptions

class DABSProcessor:
    """
    Core DABS Processing Engine for Hills & Hollows LLC
    
    Capabilities:
    - Excel file processing (1,239+ SKUs)
    - NAXML ItemSynch/ItemPrice generation
    - CSV export for SSCS integration
    - Data validation and error handling
    - Audit trail generation
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.data_dir = Path(self.config.get('data_directory', '/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/data'))
        self.export_dir = Path(self.config.get('export_directory', '/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/exports'))
        self.backup_dir = self.data_dir / 'dabs_backups'
        self.audit_dir = self.data_dir / 'audit'

        # Ensure directories exist
        for directory in [self.data_dir, self.export_dir, self.backup_dir, self.audit_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Initialize audit trail manager
        self.audit_manager = None
        if AuditTrailManager:
            try:
                self.audit_manager = AuditTrailManager(
                    audit_dir=self.audit_dir,
                    retention_years=self.config.get('audit_retention_years', 7)
                )
                logger.info("Audit trail manager initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize audit trail manager: {e}")
        else:
            logger.warning("Audit trail system not available")

        logger.info(f"DABS Processor initialized with data_dir: {self.data_dir}")
        logger.info(f"Export directory: {self.export_dir}")

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load processor configuration"""
        default_config = {
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
            'validate_prices': True,
            'backup_files': True,
            'processing_timeout_minutes': 30,
            'excel_header_row': 1  # DABS files have headers in row 2 (index 1)
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                
        return default_config

    async def process_dabs_file(self, file_path: Union[str, Path]) -> ProcessingResult:
        """
        Main processing method for DABS Excel files
        
        Args:
            file_path: Path to DABS Excel file
            
        Returns:
            ProcessingResult with processing details and output files
        """
        start_time = datetime.now()
        file_path = Path(file_path)
        
        logger.info(f"Starting DABS file processing: {file_path}")
        
        try:
            # Validate file exists and is accessible
            if not file_path.exists():
                raise FileNotFoundError(f"DABS file not found: {file_path}")
                
            # Create backup copy
            if self.config['backup_files']:
                await self._backup_file(file_path)
                
            # Load and validate Excel data
            df = await self._load_excel_file(file_path)
            validation_result = await self._validate_data(df)

            if not validation_result['valid']:
                raise ValueError(f"Data validation failed: {validation_result['errors']}")

            # Extract validation exceptions for reporting
            validation_exceptions = []
            if 'exceptions' in validation_result:
                validation_exceptions = validation_result['exceptions']

            # Convert to product objects
            products = await self._convert_to_products(df)
            
            # Generate output files
            output_files = []
            
            # Generate NAXML file
            if 'naxml' in self.config['export_formats']:
                naxml_file = await self._generate_naxml(products)
                output_files.append(naxml_file)
                
            # Generate CSV file  
            if 'csv' in self.config['export_formats']:
                csv_file = await self._generate_csv(products)
                output_files.append(csv_file)
                
            # Generate JSON file
            if 'json' in self.config['export_formats']:
                json_file = await self._generate_json(products)
                output_files.append(json_file)

            # Generate price validation report if exceptions exist
            if validation_exceptions:
                report_file = await self._generate_validation_report(validation_exceptions)
                output_files.append(report_file)

            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate checksum for integrity
            checksum = await self._calculate_checksum(products)

            # Log file processing to audit trail
            if self.audit_manager:
                try:
                    await self.audit_manager.log_file_processing(
                        file_path=str(file_path),
                        total_skus=len(df),
                        processed_skus=len(products),
                        failed_skus=len(df) - len(products),
                        processing_time=processing_time,
                        checksum=checksum,
                        metadata={
                            'output_files': output_files,
                            'validation_warnings': len(validation_result.get('warnings', [])),
                            'validation_exceptions': len(validation_exceptions)
                        }
                    )

                    # Log validation exceptions to audit trail
                    for exc in validation_exceptions:
                        await self.audit_manager.log_validation_exception(
                            sku=str(exc.get('sku', 'UNKNOWN')),
                            exception_type=exc.get('type', 'unknown'),
                            message=exc.get('message', 'No message'),
                            value=exc.get('value'),
                            metadata=exc
                        )
                except Exception as e:
                    logger.warning(f"Failed to log to audit trail: {e}")

            result = ProcessingResult(
                success=True,
                total_skus=len(df),
                processed_skus=len(products),
                failed_skus=len(df) - len(products),
                errors=[],
                warnings=validation_result.get('warnings', []),
                processing_time=processing_time,
                output_files=output_files,
                checksum=checksum,
                exceptions=validation_exceptions
            )
            
            logger.info(f"DABS processing completed successfully: {len(products)} SKUs in {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"DABS processing failed: {str(e)}")
            
            return ProcessingResult(
                success=False,
                total_skus=0,
                processed_skus=0,
                failed_skus=0,
                errors=[str(e)],
                warnings=[],
                processing_time=processing_time,
                output_files=[],
                checksum=""
            )

    async def _load_excel_file(self, file_path: Path) -> pd.DataFrame:
        """Load Excel file with error handling"""
        try:
            header_row = self.config.get('excel_header_row', 0)

            # Try different Excel engines
            for engine in ['openpyxl', 'xlrd']:
                try:
                    df = pd.read_excel(file_path, engine=engine, header=header_row)
                    logger.info(f"Successfully loaded Excel file with {engine}: {len(df)} rows, {len(df.columns)} columns")
                    logger.info(f"Columns found: {list(df.columns)}")
                    return df
                except Exception as e:
                    logger.warning(f"Failed to load with {engine}: {str(e)}")
                    continue

            raise Exception("Could not load Excel file with any available engine")

        except Exception as e:
            logger.error(f"Failed to load Excel file {file_path}: {str(e)}")
            raise

    async def _validate_data(self, df: pd.DataFrame) -> Dict:
        """Validate DABS data structure and content"""
        errors = []
        warnings = []

        # Check required columns
        required_cols = self.config['required_columns']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")

        # Check for empty data
        if len(df) == 0:
            errors.append("Excel file contains no data rows")

        # Comprehensive price validation
        price_exceptions = []
        if self.config.get('validate_prices', True):
            price_validation = await self._validate_prices(df)
            errors.extend(price_validation['errors'])
            warnings.extend(price_validation['warnings'])
            price_exceptions = price_validation.get('exceptions', [])

        # Check SKU uniqueness
        if 'SKU' in df.columns:
            duplicate_skus = df[df['SKU'].duplicated(keep=False)]
            if len(duplicate_skus) > 0:
                warnings.append(f"Found {len(duplicate_skus)} duplicate SKUs")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'exceptions': price_exceptions
        }

    async def _validate_prices(self, df: pd.DataFrame) -> Dict:
        """
        Comprehensive price validation with 20% variance detection and exception reporting

        Returns:
            Dict with 'errors', 'warnings', and 'exceptions' lists
        """
        errors = []
        warnings = []
        exceptions = []

        price_col = 'PRICE'
        if price_col not in df.columns:
            errors.append(f"Price column '{price_col}' not found")
            return {'errors': errors, 'warnings': warnings, 'exceptions': exceptions}

        # Convert prices to numeric, track conversion issues
        numeric_prices = pd.to_numeric(df[price_col], errors='coerce')

        # Check for non-numeric prices
        non_numeric_mask = numeric_prices.isna() & df[price_col].notna()
        if non_numeric_mask.any():
            non_numeric_skus = df.loc[non_numeric_mask, 'SKU'].tolist()
            warnings.append(f"Found {len(non_numeric_skus)} rows with non-numeric prices")
            exceptions.extend([{
                'type': 'non_numeric_price',
                'sku': sku,
                'value': df.loc[df['SKU'] == sku, price_col].iloc[0],
                'message': 'Price value is not numeric'
            } for sku in non_numeric_skus])

        # Check for negative prices
        negative_mask = numeric_prices < 0
        if negative_mask.any():
            negative_skus = df.loc[negative_mask, 'SKU'].tolist()
            warnings.append(f"Found {len(negative_skus)} rows with negative prices")
            exceptions.extend([{
                'type': 'negative_price',
                'sku': sku,
                'value': float(numeric_prices.loc[df['SKU'] == sku].iloc[0]),
                'message': 'Price cannot be negative'
            } for sku in negative_skus])

        # Check for zero prices
        zero_mask = numeric_prices == 0
        if zero_mask.any():
            zero_skus = df.loc[zero_mask, 'SKU'].tolist()
            warnings.append(f"Found {len(zero_skus)} rows with zero prices")
            exceptions.extend([{
                'type': 'zero_price',
                'sku': sku,
                'value': 0.0,
                'message': 'Price is zero - verify if intentional'
            } for sku in zero_skus])

        # 20% variance detection (compare against historical data if available)
        variance_exceptions = await self._detect_price_variance(df, numeric_prices)
        exceptions.extend(variance_exceptions)
        if variance_exceptions:
            warnings.append(f"Found {len(variance_exceptions)} prices with >20% variance from previous values")

        # Check for unusually high prices (potential data entry errors)
        high_price_threshold = 1000.0  # Configurable threshold
        high_price_mask = numeric_prices > high_price_threshold
        if high_price_mask.any():
            high_price_skus = df.loc[high_price_mask, 'SKU'].tolist()
            warnings.append(f"Found {len(high_price_skus)} items with prices above ${high_price_threshold}")
            exceptions.extend([{
                'type': 'high_price_warning',
                'sku': sku,
                'value': float(numeric_prices.loc[df['SKU'] == sku].iloc[0]),
                'message': f'Price above ${high_price_threshold} - verify if correct'
            } for sku in high_price_skus])

        # Check for unusually low prices for alcohol (potential data entry errors)
        low_price_threshold = 5.0  # Most alcohol should be above $5
        low_price_mask = (numeric_prices > 0) & (numeric_prices < low_price_threshold)
        if low_price_mask.any():
            low_price_skus = df.loc[low_price_mask, 'SKU'].tolist()
            warnings.append(f"Found {len(low_price_skus)} items with prices below ${low_price_threshold}")
            exceptions.extend([{
                'type': 'low_price_warning',
                'sku': sku,
                'value': float(numeric_prices.loc[df['SKU'] == sku].iloc[0]),
                'message': f'Price below ${low_price_threshold} - verify if correct'
            } for sku in low_price_skus])

        logger.info(f"Price validation completed: {len(exceptions)} exceptions found")

        return {
            'errors': errors,
            'warnings': warnings,
            'exceptions': exceptions
        }

    async def _detect_price_variance(self, df: pd.DataFrame, numeric_prices: pd.Series) -> List[Dict]:
        """
        Detect price variances greater than 20% from historical data

        Args:
            df: DataFrame with current DABS data
            numeric_prices: Series of numeric price values

        Returns:
            List of variance exception dictionaries
        """
        exceptions = []
        variance_threshold = self.config.get('max_price_variance_percent', 20.0) / 100.0

        # Try to load historical price data for comparison
        historical_prices = await self._load_historical_prices()

        if not historical_prices:
            logger.info("No historical price data available for variance detection")
            return exceptions

        for idx, row in df.iterrows():
            sku = str(row['SKU']).zfill(6)
            current_price = numeric_prices.iloc[idx]

            if pd.isna(current_price) or current_price <= 0:
                continue

            if sku in historical_prices:
                historical_price = historical_prices[sku]

                # Calculate percentage change
                if historical_price > 0:
                    price_change = abs(current_price - historical_price) / historical_price

                    if price_change > variance_threshold:
                        percentage_change = price_change * 100
                        direction = "increase" if current_price > historical_price else "decrease"

                        exceptions.append({
                            'type': 'price_variance',
                            'sku': sku,
                            'current_price': float(current_price),
                            'historical_price': float(historical_price),
                            'variance_percent': round(percentage_change, 2),
                            'direction': direction,
                            'message': f'Price {direction} of {percentage_change:.1f}% exceeds {variance_threshold*100}% threshold'
                        })

        logger.info(f"Price variance detection completed: {len(exceptions)} variances > {variance_threshold*100}% found")
        return exceptions

    async def _load_historical_prices(self) -> Dict[str, float]:
        """
        Load historical price data for variance comparison

        Returns:
            Dictionary mapping SKU to historical price
        """
        historical_prices = {}

        # Check for previous export files to use as historical data
        export_files = list(self.export_dir.glob("dabs_pricing_*.csv"))

        if not export_files:
            return historical_prices

        # Use the most recent file (excluding current processing)
        export_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Skip the most recent file if it was created in the last minute (likely current processing)
        for export_file in export_files:
            file_age_minutes = (datetime.now().timestamp() - export_file.stat().st_mtime) / 60
            if file_age_minutes > 1:  # Use files older than 1 minute
                try:
                    historical_df = pd.read_csv(export_file)
                    for _, row in historical_df.iterrows():
                        sku = str(row['SKU']).zfill(6)
                        price = float(row['RetailPrice'])
                        historical_prices[sku] = price

                    logger.info(f"Loaded {len(historical_prices)} historical prices from {export_file.name}")
                    break

                except Exception as e:
                    logger.warning(f"Failed to load historical prices from {export_file}: {str(e)}")
                    continue

        return historical_prices

    async def _generate_validation_report(self, exceptions: List[Dict]) -> str:
        """
        Generate a detailed price validation report

        Args:
            exceptions: List of validation exception dictionaries

        Returns:
            Path to generated report file
        """
        output_file = self.export_dir / f"dabs_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Create comprehensive report
        report = {
            "metadata": {
                "generated_date": datetime.now().isoformat(),
                "source": "DABS-Hills-Hollows",
                "total_exceptions": len(exceptions),
                "report_version": "1.0"
            },
            "summary": {},
            "exceptions": exceptions
        }

        # Generate summary by exception type
        exception_types = {}
        for exc in exceptions:
            exc_type = exc.get('type', 'unknown')
            if exc_type not in exception_types:
                exception_types[exc_type] = 0
            exception_types[exc_type] += 1

        report["summary"] = exception_types

        # Write report file
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Generated validation report: {output_file} with {len(exceptions)} exceptions")
        return str(output_file)

    async def _convert_to_products(self, df: pd.DataFrame) -> List[DABSProduct]:
        """Convert DataFrame to DABSProduct objects"""
        products = []
        column_mapping = self.config['column_mapping']

        for _, row in df.iterrows():
            try:
                # Map columns using the configuration
                product_name = str(row.get('ITEM NAME', '')).strip()

                # Extract size information from product name
                size_ml = self._extract_size_ml(product_name)

                # Parse effective date
                effective_date = pd.to_datetime(row.get('FROM DATE', datetime.now()))
                if pd.isna(effective_date):
                    effective_date = datetime.now()

                # Parse updated date (use current time since not in source)
                updated_on = datetime.now()

                # Parse special pricing
                on_spa = str(row.get('ON SPA?', 'No')).lower()
                on_special_pricing = on_spa in ['yes', 'true', '1', 'y', 'spa']

                product = DABSProduct(
                    sku=str(row['SKU']).zfill(6),  # Pad SKU to 6 digits
                    product_name=product_name,
                    retail_price=float(pd.to_numeric(row['PRICE'], errors='coerce') or 0.0),
                    category=str(row.get('ITEM TYPE', 'General')),
                    on_special_pricing=on_special_pricing,
                    effective_date=effective_date,
                    status=str(row.get('ITEM STATUS', 'Active')),
                    updated_on=updated_on,
                    size_ml=size_ml
                )

                # Skip invalid products
                if product.retail_price <= 0:
                    logger.warning(f"Skipping SKU {product.sku} with invalid price: {product.retail_price}")
                    continue

                products.append(product)

            except Exception as e:
                logger.warning(f"Failed to convert row to product: {str(e)}")
                continue

        logger.info(f"Successfully converted {len(products)} products from {len(df)} rows")
        return products

    def _extract_size_ml(self, product_name: str) -> Optional[str]:
        """Extract size in ML from product name"""
        import re
        
        # Common patterns for bottle sizes
        patterns = [
            r'(\d+)\s*ml',
            r'(\d+)\s*ML', 
            r'(\d+\.?\d*)\s*L',
            r'(\d+)\s*oz'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, product_name, re.IGNORECASE)
            if match:
                size = match.group(1)
                # Convert liters to ML
                if 'L' in match.group(0).upper() and 'ML' not in match.group(0).upper():
                    size = str(float(size) * 1000)
                return size
                
        return None

    async def _generate_naxml(self, products: List[DABSProduct]) -> str:
        """Generate NAXML ItemSynch file for SSCS integration"""
        output_file = self.export_dir / f"dabs_itemsynch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"

        # Create NAXML structure based on ItemSynch standard
        root = ET.Element("ItemSynch")
        root.set("version", self.config['naxml_version'])
        root.set("timestamp", datetime.now().isoformat())
        root.set("xmlns", "http://www.naxml.org/NAXML")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

        # Header information with enhanced metadata
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "Source").text = "DABS-Hills-Hollows"
        ET.SubElement(header, "Destination").text = "SSCS-POS"
        ET.SubElement(header, "MessageID").text = f"DABS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ET.SubElement(header, "RecordCount").text = str(len(products))
        ET.SubElement(header, "GeneratedDate").text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ET.SubElement(header, "ProcessingMode").text = "UPDATE"  # UPDATE, INSERT, DELETE
        ET.SubElement(header, "DataSource").text = "DABS_PRICE_CHANGES"

        # Processing statistics
        stats = ET.SubElement(header, "Statistics")
        ET.SubElement(stats, "TotalItems").text = str(len(products))
        ET.SubElement(stats, "ActiveItems").text = str(len([p for p in products if p.status == 'Active']))
        ET.SubElement(stats, "SpecialPricingItems").text = str(len([p for p in products if p.on_special_pricing]))

        # Products section
        items = ET.SubElement(root, "Items")

        for product in products:
            item = ET.SubElement(items, "Item")
            item.set("action", "update")  # update, insert, delete

            # Core item information
            ET.SubElement(item, "SKU").text = product.sku
            ET.SubElement(item, "UPC").text = product.upc or ""
            ET.SubElement(item, "Description").text = product.product_name
            ET.SubElement(item, "Category").text = product.category
            ET.SubElement(item, "Status").text = product.status
            ET.SubElement(item, "LastModified").text = product.updated_on.strftime("%Y-%m-%d %H:%M:%S")

            # Pricing information with enhanced details
            pricing = ET.SubElement(item, "Pricing")
            ET.SubElement(pricing, "RetailPrice").text = f"{product.retail_price:.2f}"
            ET.SubElement(pricing, "Currency").text = "USD"
            ET.SubElement(pricing, "EffectiveDate").text = product.effective_date.strftime("%Y-%m-%d")
            ET.SubElement(pricing, "OnSpecial").text = "true" if product.on_special_pricing else "false"

            # Tax information (standard for alcohol)
            tax = ET.SubElement(pricing, "Tax")
            ET.SubElement(tax, "Taxable").text = "true"
            ET.SubElement(tax, "TaxCategory").text = "ALCOHOL"

            # Additional attributes
            attributes = ET.SubElement(item, "Attributes")
            if product.size_ml:
                ET.SubElement(attributes, "Size").text = f"{product.size_ml}ml"
            ET.SubElement(attributes, "Department").text = "LIQUOR"
            ET.SubElement(attributes, "Vendor").text = "DABS"

            # Inventory flags
            inventory = ET.SubElement(item, "Inventory")
            ET.SubElement(inventory, "Trackable").text = "true"
            ET.SubElement(inventory, "Serialized").text = "false"
            ET.SubElement(inventory, "AgeRestricted").text = "true"  # Alcohol requires age verification

        # Write XML file with pretty formatting
        self._indent_xml(root)
        tree = ET.ElementTree(root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)

        logger.info(f"Generated NAXML file: {output_file} with {len(products)} items")
        return str(output_file)

    def _indent_xml(self, elem, level=0):
        """Add pretty-printing indentation to XML elements"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indent_xml(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    async def _generate_csv(self, products: List[DABSProduct]) -> str:
        """Generate CSV file for SSCS integration"""
        output_file = self.export_dir / f"dabs_pricing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Convert products to DataFrame
        data = []
        for product in products:
            data.append({
                'SKU': product.sku,
                'ProductName': product.product_name,
                'RetailPrice': product.retail_price,
                'Category': product.category,
                'OnSpecialPricing': 'Yes' if product.on_special_pricing else 'No',
                'EffectiveDate': product.effective_date.strftime('%Y-%m-%d'),
                'Status': product.status,
                'UpdatedOn': product.updated_on.strftime('%Y-%m-%d %H:%M:%S'),
                'Size': product.size_ml or ''
            })
            
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)
        
        logger.info(f"Generated CSV file: {output_file} with {len(products)} items")
        return str(output_file)

    async def _generate_json(self, products: List[DABSProduct]) -> str:
        """Generate JSON file for API integration"""
        output_file = self.export_dir / f"dabs_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert products to serializable format
        data = {
            "metadata": {
                "generated_date": datetime.now().isoformat(),
                "source": "DABS-Hills-Hollows",
                "total_items": len(products),
                "format_version": "1.0"
            },
            "products": [asdict(product) for product in products]
        }
        
        # Handle datetime serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=json_serializer)
            
        logger.info(f"Generated JSON file: {output_file} with {len(products)} items")
        return str(output_file)

    async def _backup_file(self, file_path: Path) -> None:
        """Create backup copy of original file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")

    async def _calculate_checksum(self, products: List[DABSProduct]) -> str:
        """Calculate checksum for data integrity verification"""
        # Create deterministic string representation
        product_data = []
        for product in sorted(products, key=lambda p: p.sku):
            product_data.append(f"{product.sku}:{product.retail_price}:{product.updated_on.isoformat()}")
            
        combined_data = "|".join(product_data)
        return hashlib.sha256(combined_data.encode()).hexdigest()

    def get_processing_status(self) -> Dict:
        """Get current processing status and statistics"""
        return {
            "processor_version": "1.0.0",
            "data_directory": str(self.data_dir),
            "export_directory": str(self.export_dir),
            "supported_formats": self.config['export_formats'],
            "last_processing": "Not available"
        }

# Async context manager for processor
class DABSProcessorContext:
    """Async context manager for DABS processor operations"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.processor = None
        
    async def __aenter__(self):
        self.processor = DABSProcessor(self.config_path)
        return self.processor
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"Processing failed: {exc_type.__name__}: {exc_val}")
        return False

# Convenience functions
async def process_dabs_file_async(file_path: Union[str, Path], config_path: Optional[str] = None) -> ProcessingResult:
    """
    Convenience function to process a DABS file asynchronously
    
    Args:
        file_path: Path to DABS Excel file
        config_path: Optional path to configuration file
        
    Returns:
        ProcessingResult with processing details
    """
    async with DABSProcessorContext(config_path) as processor:
        return await processor.process_dabs_file(file_path)

def process_dabs_file_sync(file_path: Union[str, Path], config_path: Optional[str] = None) -> ProcessingResult:
    """
    Synchronous wrapper for DABS file processing
    
    Args:
        file_path: Path to DABS Excel file
        config_path: Optional path to configuration file
        
    Returns:
        ProcessingResult with processing details
    """
    return asyncio.run(process_dabs_file_async(file_path, config_path))

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        result = process_dabs_file_sync(file_path)
        
        if result.success:
            print(f"✅ Processing successful: {result.processed_skus} SKUs processed in {result.processing_time:.2f}s")
            print(f"📁 Output files: {', '.join(result.output_files)}")

            # Display warnings if any
            if result.warnings:
                print(f"⚠️  Warnings: {len(result.warnings)}")
                for warning in result.warnings:
                    print(f"   - {warning}")

            # Display price validation exceptions if any
            if result.exceptions:
                print(f"🔍 Price Validation Exceptions: {len(result.exceptions)}")

                # Group exceptions by type for better reporting
                exception_types = {}
                for exc in result.exceptions:
                    exc_type = exc.get('type', 'unknown')
                    if exc_type not in exception_types:
                        exception_types[exc_type] = []
                    exception_types[exc_type].append(exc)

                for exc_type, exceptions in exception_types.items():
                    print(f"   {exc_type.replace('_', ' ').title()}: {len(exceptions)} items")
                    for exc in exceptions[:5]:  # Show first 5 examples
                        sku = exc.get('sku', 'Unknown')
                        message = exc.get('message', 'No details')
                        print(f"     - SKU {sku}: {message}")
                    if len(exceptions) > 5:
                        print(f"     ... and {len(exceptions) - 5} more")
        else:
            print(f"❌ Processing failed: {', '.join(result.errors)}")
            sys.exit(1)
    else:
        print("Usage: python dabs_processor.py <path_to_dabs_file>")
        sys.exit(1)
