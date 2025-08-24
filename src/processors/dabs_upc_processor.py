#!/usr/bin/env python3
"""
DABS UPC Processing Engine
Automated DABS file processing with integrated UPC management

Created: January 23, 2025
Purpose: Process DABS monthly files with automated UPC resolution and case configuration
"""

import asyncio
import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import xml.etree.ElementTree as ET

from processors.upc_master_database import UPCMasterDatabase, UPCMasterRecord
from integration_hub.sscs_ccb_client import SSCSCCBClient, SSCSCaseUPC

logger = logging.getLogger(__name__)

@dataclass
class DABSItem:
    """DABS item from monthly Excel file"""
    csc_code: str
    product_name: str
    size_ml: str
    case_pack: int
    status_code: str
    category: str
    current_retail: float
    new_retail: float
    effective_date: str
    
@dataclass
class DABSProcessingResult:
    """Result of DABS file processing"""
    total_items: int
    successfully_processed: int
    upc_resolved: int
    case_upcs_configured: int
    exceptions: List[str]
    processing_time_seconds: float
    naxml_output_path: str

class DABSUPCProcessor:
    """
    DABS UPC Processing Engine
    
    Processes DABS monthly Excel files with integrated UPC management:
    - Automatic UPC resolution using SSCS data
    - Case UPC configuration before delivery
    - NAXML output generation for SSCS integration
    - Exception handling and manual review interface
    """
    
    def __init__(self):
        """Initialize DABS UPC processor"""
        # UPC Master Database for UPC resolution
        self.upc_db = UPCMasterDatabase()
        
        # SSCS CCB client for direct system access
        self.ccb_client = SSCSCCBClient()
        
        # Processing configuration
        self.max_price_variance_percent = 20.0
        self.confidence_threshold = 0.8
        self.auto_configure_case_upcs = True
        
        # Processing results tracking
        self.processing_stats = {
            'files_processed': 0,
            'items_processed': 0,
            'upcs_resolved': 0,
            'case_upcs_configured': 0,
            'exceptions_handled': 0
        }
        
        logger.info("DABS UPC Processor initialized")

    async def process_dabs_file(self, dabs_file_path: str, 
                              output_directory: str = "exports") -> DABSProcessingResult:
        """
        Process DABS monthly Excel file with integrated UPC management
        
        Args:
            dabs_file_path: Path to DABS Excel file
            output_directory: Directory for output files
            
        Returns:
            DABSProcessingResult: Complete processing results
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Processing DABS file: {dabs_file_path}")
            
            # Load DABS Excel file
            dabs_items = self._load_dabs_excel(dabs_file_path)
            logger.info(f"Loaded {len(dabs_items)} items from DABS file")
            
            # Process each item with UPC resolution
            processed_items = []
            exceptions = []
            upc_resolved_count = 0
            case_configured_count = 0
            
            for dabs_item in dabs_items:
                try:
                    # Resolve UPC for DABS item
                    upc_record = await self._resolve_upc_for_dabs_item(dabs_item)
                    
                    if upc_record:
                        upc_resolved_count += 1
                        
                        # Configure case UPC if needed
                        case_config = await self._configure_case_upc_for_dabs_item(dabs_item, upc_record)
                        
                        if case_config:
                            case_configured_count += 1
                        
                        # Add to processed items
                        processed_items.append({
                            'dabs_item': dabs_item,
                            'upc_record': upc_record,
                            'case_config': case_config,
                            'processing_status': 'success'
                        })
                        
                        logger.info(f"DABS item processed: {dabs_item.product_name} → UPC: {upc_record.upc_code}")
                    else:
                        # Add to exceptions for manual review
                        exceptions.append(f"UPC not resolved: {dabs_item.csc_code} - {dabs_item.product_name}")
                        processed_items.append({
                            'dabs_item': dabs_item,
                            'upc_record': None,
                            'case_config': None,
                            'processing_status': 'upc_not_resolved'
                        })
                        logger.warning(f"UPC not resolved for: {dabs_item.product_name}")
                
                except Exception as e:
                    exceptions.append(f"Processing error: {dabs_item.csc_code} - {str(e)}")
                    logger.error(f"Error processing DABS item {dabs_item.csc_code}: {e}")
            
            # Generate NAXML output for SSCS integration
            naxml_path = await self._generate_naxml_output(processed_items, output_directory)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create processing result
            result = DABSProcessingResult(
                total_items=len(dabs_items),
                successfully_processed=len([item for item in processed_items if item['processing_status'] == 'success']),
                upc_resolved=upc_resolved_count,
                case_upcs_configured=case_configured_count,
                exceptions=exceptions,
                processing_time_seconds=processing_time,
                naxml_output_path=naxml_path
            )
            
            # Update processing stats
            self.processing_stats['files_processed'] += 1
            self.processing_stats['items_processed'] += len(dabs_items)
            self.processing_stats['upcs_resolved'] += upc_resolved_count
            self.processing_stats['case_upcs_configured'] += case_configured_count
            self.processing_stats['exceptions_handled'] += len(exceptions)
            
            logger.info(f"DABS processing complete: {result.successfully_processed}/{result.total_items} successful")
            return result
            
        except Exception as e:
            logger.error(f"DABS file processing error: {e}")
            return DABSProcessingResult(
                total_items=0,
                successfully_processed=0,
                upc_resolved=0,
                case_upcs_configured=0,
                exceptions=[f"File processing failed: {str(e)}"],
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                naxml_output_path=""
            )

    def _load_dabs_excel(self, file_path: str) -> List[DABSItem]:
        """
        Load DABS Excel file and extract item data
        
        Args:
            file_path: Path to DABS Excel file
            
        Returns:
            List[DABSItem]: DABS items from Excel file
        """
        try:
            # Load DABS Excel file (assuming standard structure)
            df = pd.read_excel(file_path)
            
            # Map columns to standard DABS structure
            column_mapping = {
                'CSC Code': 'csc_code',
                'Product Name': 'product_name', 
                'Size (ml)': 'size_ml',
                'Case Pack': 'case_pack',
                'Status': 'status_code',
                'Category': 'category',
                'Current Retail': 'current_retail',
                'New Retail': 'new_retail',
                'Effective Date': 'effective_date'
            }
            
            items = []
            for _, row in df.iterrows():
                item = DABSItem(
                    csc_code=str(row.get('CSC Code', '')).strip(),
                    product_name=str(row.get('Product Name', '')).strip(),
                    size_ml=str(row.get('Size (ml)', '')).strip(),
                    case_pack=int(row.get('Case Pack', 6)),
                    status_code=str(row.get('Status', '')).strip(),
                    category=str(row.get('Category', '')).strip(),
                    current_retail=float(row.get('Current Retail', 0.0)),
                    new_retail=float(row.get('New Retail', 0.0)),
                    effective_date=str(row.get('Effective Date', datetime.now().strftime('%Y-%m-%d')))
                )
                items.append(item)
            
            logger.info(f"Loaded {len(items)} DABS items from Excel file")
            return items
            
        except Exception as e:
            logger.error(f"DABS Excel loading error: {e}")
            return []

    async def _resolve_upc_for_dabs_item(self, dabs_item: DABSItem) -> Optional[UPCMasterRecord]:
        """
        Resolve UPC for DABS item using multiple strategies
        
        Args:
            dabs_item: DABS item needing UPC resolution
            
        Returns:
            UPCMasterRecord: Resolved UPC record or None
        """
        try:
            # Strategy 1: Direct DABS code lookup
            upc_record = self.upc_db.get_upc_by_dabs_code(dabs_item.csc_code)
            if upc_record:
                logger.info(f"Direct DABS lookup: {dabs_item.csc_code} → {upc_record.upc_code}")
                return upc_record
            
            # Strategy 2: Product description fuzzy matching
            search_description = f"{dabs_item.product_name} {dabs_item.size_ml}"
            upc_record = self.upc_db.find_upc_by_description_fuzzy(search_description, self.confidence_threshold)
            
            if upc_record:
                # Update DABS mapping for future direct lookups
                await self._update_dabs_mapping(dabs_item.csc_code, upc_record)
                logger.info(f"Fuzzy match: '{search_description}' → {upc_record.upc_code}")
                return upc_record
            
            # Strategy 3: Size and brand matching
            brand_name = dabs_item.product_name.split()[0]  # First word as brand
            size_search = f"{brand_name} {dabs_item.size_ml}"
            upc_record = self.upc_db.find_upc_by_description_fuzzy(size_search, 0.7)  # Lower threshold
            
            if upc_record:
                await self._update_dabs_mapping(dabs_item.csc_code, upc_record)
                logger.info(f"Brand+size match: '{size_search}' → {upc_record.upc_code}")
                return upc_record
            
            logger.warning(f"UPC resolution failed for: {dabs_item.csc_code} - {dabs_item.product_name}")
            return None
            
        except Exception as e:
            logger.error(f"UPC resolution error for {dabs_item.csc_code}: {e}")
            return None

    async def _update_dabs_mapping(self, dabs_code: str, upc_record: UPCMasterRecord):
        """Update DABS mapping database with new UPC resolution"""
        try:
            cursor = self.upc_db.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO dabs_sscs_mapping 
                (dabs_csc_code, sscs_item_id, upc_code, description, confidence_score, manual_verified)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                dabs_code,
                upc_record.sscs_item_id,
                upc_record.upc_code,
                upc_record.description,
                upc_record.confidence_score,
                False  # Auto-resolved, not manually verified
            ))
            
            # Update UPC master with DABS mapping
            cursor.execute("""
                UPDATE upc_master 
                SET dabs_csc_code = ?, dabs_mapped = TRUE 
                WHERE upc_code = ?
            """, (dabs_code, upc_record.upc_code))
            
            self.upc_db.conn.commit()
            logger.info(f"DABS mapping updated: {dabs_code} → {upc_record.upc_code}")
            
        except Exception as e:
            logger.error(f"DABS mapping update error: {e}")

    async def _configure_case_upc_for_dabs_item(self, dabs_item: DABSItem, 
                                              upc_record: UPCMasterRecord) -> Optional[SSCSCaseUPC]:
        """
        Configure case UPC for DABS item before delivery
        
        Args:
            dabs_item: DABS item with case pack information
            upc_record: Resolved UPC record for the item
            
        Returns:
            SSCSCaseUPC: Configured case UPC or None
        """
        try:
            if not self.auto_configure_case_upcs:
                return None
            
            # Check if case UPC already configured
            cursor = self.upc_db.conn.cursor()
            cursor.execute("""
                SELECT * FROM case_upc_config 
                WHERE bottle_upc = ? AND case_pack_size = ?
            """, (upc_record.upc_code, dabs_item.case_pack))
            
            existing_case = cursor.fetchone()
            
            if existing_case:
                # Return existing case configuration
                case_config = SSCSCaseUPC(
                    case_upc=existing_case[0],
                    bottle_upc=existing_case[1],
                    case_pack_size=existing_case[2],
                    description=existing_case[3],
                    configured_date=datetime.fromisoformat(existing_case[4]),
                    validation_status=existing_case[5]
                )
                logger.info(f"Existing case UPC: {dabs_item.product_name} → {case_config.case_upc}")
                return case_config
            else:
                # Generate new case UPC configuration
                case_config = await self.upc_db.ccb_client.generate_case_upc_for_item(
                    upc_record, dabs_item.case_pack
                )
                
                if case_config:
                    logger.info(f"New case UPC configured: {dabs_item.product_name} → {case_config.case_upc}")
                    return case_config
                else:
                    logger.warning(f"Case UPC configuration failed: {dabs_item.product_name}")
                    return None
                    
        except Exception as e:
            logger.error(f"Case UPC configuration error for {dabs_item.csc_code}: {e}")
            return None

    async def _generate_naxml_output(self, processed_items: List[Dict], 
                                   output_directory: str) -> str:
        """
        Generate NAXML output file for SSCS integration
        
        Args:
            processed_items: List of processed DABS items with UPC data
            output_directory: Directory for NAXML output
            
        Returns:
            str: Path to generated NAXML file
        """
        try:
            # Create output directory
            output_path = Path(output_directory)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate NAXML filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            naxml_filename = f"DABS_ItemPrice_{timestamp}.xml"
            naxml_path = output_path / naxml_filename
            
            # Create NAXML root element
            root = ET.Element("NAXML_PBIPriceChange")
            root.set("xmlns", "http://www.naxml.org/POSBO/Vocabulary/2003-10-16")
            
            # Transmission header
            header = ET.SubElement(root, "TransmissionHeader")
            store_id = ET.SubElement(header, "StoreLocationID")
            store_id.text = "HILLS_HOLLOWS_BOULDER"
            transmission_date = ET.SubElement(header, "TransmissionDate")
            transmission_date.text = datetime.now().strftime('%Y-%m-%d')
            
            # Process successfully resolved items
            for item_data in processed_items:
                if item_data['processing_status'] == 'success' and item_data['upc_record']:
                    dabs_item = item_data['dabs_item']
                    upc_record = item_data['upc_record']
                    
                    # Create ItemPriceChange element
                    price_change = ET.SubElement(root, "ItemPriceChange")
                    
                    # Item identification (using SSCS Item ID)
                    item_id = ET.SubElement(price_change, "ItemID")
                    item_id.text = upc_record.sscs_item_id
                    
                    # UPC code for scanning
                    upc_element = ET.SubElement(price_change, "UPCCode")
                    upc_element.text = upc_record.upc_code
                    
                    # Receipt description
                    receipt_desc = ET.SubElement(price_change, "ReceiptDescription")
                    receipt_desc.text = dabs_item.product_name
                    
                    # Price information
                    price = ET.SubElement(price_change, "Price")
                    price.text = str(dabs_item.new_retail)
                    
                    # Effective date
                    effective_date = ET.SubElement(price_change, "PriceEffectiveDate")
                    effective_date.text = dabs_item.effective_date
                    
                    # Case UPC information (if configured)
                    if item_data['case_config']:
                        case_info = ET.SubElement(price_change, "CaseUPCInfo")
                        case_upc_element = ET.SubElement(case_info, "CaseUPCCode")
                        case_upc_element.text = item_data['case_config'].case_upc
                        case_pack = ET.SubElement(case_info, "CasePackSize")
                        case_pack.text = str(item_data['case_config'].case_pack_size)
            
            # Write NAXML file
            tree = ET.ElementTree(root)
            tree.write(str(naxml_path), encoding='utf-8', xml_declaration=True)
            
            logger.info(f"NAXML output generated: {naxml_path}")
            return str(naxml_path)
            
        except Exception as e:
            logger.error(f"NAXML generation error: {e}")
            return ""

    async def process_restaurant_order_preparation(self, restaurant_orders: List[Dict]) -> Dict[str, List[SSCSCaseUPC]]:
        """
        Pre-process restaurant orders for delivery day UPC configuration
        
        Args:
            restaurant_orders: List of restaurant orders with item details
            
        Returns:
            Dict[str, List[SSCSCaseUPC]]: Case UPCs by restaurant
        """
        try:
            logger.info(f"Processing restaurant orders for UPC preparation: {len(restaurant_orders)} orders")
            
            restaurant_upcs = {}
            
            for order in restaurant_orders:
                restaurant_name = order.get('restaurant_name', 'Unknown')
                order_items = order.get('items', [])
                
                # Prepare case UPCs for this restaurant's order
                case_upcs = await self.upc_db.prepare_restaurant_delivery_upcs(order_items)
                
                if case_upcs:
                    restaurant_upcs[restaurant_name] = list(case_upcs.values())
                    logger.info(f"Restaurant UPCs prepared: {restaurant_name} - {len(case_upcs)} items")
                else:
                    logger.warning(f"No UPCs prepared for restaurant: {restaurant_name}")
            
            total_upcs = sum(len(upcs) for upcs in restaurant_upcs.values())
            logger.info(f"Restaurant order UPC preparation complete: {total_upcs} case UPCs ready")
            
            return restaurant_upcs
            
        except Exception as e:
            logger.error(f"Restaurant order preparation error: {e}")
            return {}

    def validate_price_variance(self, dabs_item: DABSItem, upc_record: UPCMasterRecord) -> bool:
        """
        Validate price variance between DABS and SSCS
        
        Args:
            dabs_item: DABS item with new price
            upc_record: Current SSCS UPC record
            
        Returns:
            bool: True if variance within acceptable range
        """
        try:
            if upc_record.current_price == 0:
                return True  # No current price to compare
            
            price_variance = abs(dabs_item.new_retail - upc_record.current_price) / upc_record.current_price * 100
            
            if price_variance > self.max_price_variance_percent:
                logger.warning(f"Price variance alert: {dabs_item.product_name} - "
                             f"Current: ${upc_record.current_price}, New: ${dabs_item.new_retail} "
                             f"({price_variance:.1f}% change)")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Price variance validation error: {e}")
            return True  # Default to accepting on error

    async def generate_processing_report(self, result: DABSProcessingResult, 
                                       output_path: str) -> bool:
        """
        Generate comprehensive processing report for management review
        
        Args:
            result: DABS processing result
            output_path: Path for processing report
            
        Returns:
            bool: True if report generated successfully
        """
        try:
            # Get database statistics
            db_stats = self.upc_db.get_database_stats()
            
            # Create comprehensive report
            report_data = {
                'processing_summary': {
                    'processing_date': datetime.now().isoformat(),
                    'total_items': result.total_items,
                    'successfully_processed': result.successfully_processed,
                    'upc_resolved': result.upc_resolved,
                    'case_upcs_configured': result.case_upcs_configured,
                    'processing_time_seconds': result.processing_time_seconds,
                    'success_rate': f"{(result.successfully_processed/result.total_items*100):.1f}%" if result.total_items > 0 else "0%"
                },
                'upc_database_stats': db_stats,
                'processing_stats': self.processing_stats,
                'exceptions': result.exceptions,
                'naxml_output': result.naxml_output_path,
                'recommendations': self._generate_recommendations(result)
            }
            
            # Write report
            with open(output_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"Processing report generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Processing report generation error: {e}")
            return False

    def _generate_recommendations(self, result: DABSProcessingResult) -> List[str]:
        """Generate recommendations based on processing results"""
        recommendations = []
        
        # UPC resolution rate recommendations
        upc_rate = (result.upc_resolved / result.total_items * 100) if result.total_items > 0 else 0
        if upc_rate < 95:
            recommendations.append(f"UPC resolution rate is {upc_rate:.1f}% - consider manual UPC mapping for unresolved items")
        
        # Case UPC configuration recommendations
        case_rate = (result.case_upcs_configured / result.upc_resolved * 100) if result.upc_resolved > 0 else 0
        if case_rate < 90:
            recommendations.append(f"Case UPC configuration rate is {case_rate:.1f}% - review SSCS backend access")
        
        # Exception handling recommendations
        if len(result.exceptions) > result.total_items * 0.05:  # >5% exceptions
            recommendations.append("High exception rate - consider improving fuzzy matching threshold")
        
        # Performance recommendations
        if result.processing_time_seconds > 300:  # >5 minutes
            recommendations.append("Processing time exceeded 5 minutes - consider performance optimization")
        
        return recommendations

    async def close(self):
        """Clean up database and client connections"""
        await self.ccb_client.close()
        self.upc_db.close()
        logger.info("DABS UPC Processor closed")

# Example usage and testing
async def main():
    """Test DABS UPC processor functionality"""
    processor = DABSUPCProcessor()
    
    try:
        print("=== DABS UPC Processor Test ===")
        
        # Test with sample DABS file (if available)
        dabs_file_path = "/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/dabs/Type-2-3-Package-Agency-Monthly-Sales-Detail-Report-Template.xlsx"
        
        if Path(dabs_file_path).exists():
            print(f"\n1. Processing DABS file: {dabs_file_path}")
            result = await processor.process_dabs_file(dabs_file_path, "data/exports")
            
            print(f"✅ Processing complete:")
            print(f"   Total items: {result.total_items}")
            print(f"   Successfully processed: {result.successfully_processed}")
            print(f"   UPCs resolved: {result.upc_resolved}")
            print(f"   Case UPCs configured: {result.case_upcs_configured}")
            print(f"   Exceptions: {len(result.exceptions)}")
            print(f"   Processing time: {result.processing_time_seconds:.2f} seconds")
            
            if result.exceptions:
                print(f"\nExceptions requiring review:")
                for exception in result.exceptions[:5]:  # Show first 5
                    print(f"   - {exception}")
            
            # Generate processing report
            report_path = "data/exports/dabs_processing_report.json"
            report_success = await processor.generate_processing_report(result, report_path)
            print(f"✅ Processing report: {report_path}" if report_success else "❌ Report generation failed")
        
        else:
            print(f"❌ DABS file not found: {dabs_file_path}")
        
        # Test restaurant order preparation
        print(f"\n2. Testing restaurant order preparation...")
        sample_restaurant_orders = [
            {
                'restaurant_name': 'Test Restaurant 1',
                'items': [
                    {'description': 'BACARDI MOJITO 1750ml', 'case_pack': 6},
                    {'description': 'WASATCH BEER 6PK', 'case_pack': 4}
                ]
            }
        ]
        
        restaurant_upcs = await processor.process_restaurant_order_preparation(sample_restaurant_orders)
        print(f"✅ Restaurant UPCs prepared for {len(restaurant_upcs)} restaurants")
        
        print("\n✅ DABS UPC Processor test complete!")
        
    except Exception as e:
        print(f"❌ DABS UPC Processor test failed: {e}")
    
    finally:
        await processor.close()

if __name__ == "__main__":
    asyncio.run(main())
