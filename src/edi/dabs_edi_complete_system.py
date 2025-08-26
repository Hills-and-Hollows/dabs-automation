"""
DABS EDI Complete System
Unified system for converting DABS data (Excel, PDF, CSV) to NAXML EDI format

Business Context:
- Handles all DABS data formats consistently
- Converts to SSCS-compatible NAXML for v6242s1@edidelivery.com
- Maintains Utah Package Agency compliance
- Delivers 90% time reduction through automation
"""

import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import pandas as pd
import json

from dabs_edi_generator import DABSEDIGenerator, DABSItem
from dabs_edi_mailer import EDIDeliveryManager
from dabs_pdf_to_naxml import DABSPDFToNAXMLConverter
from upc_lookup_integration import UPCLookupManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DABSEDICompleteSystem:
    """Complete DABS EDI processing system for all data formats"""
    
    def __init__(self, smtp_config: Optional[Dict[str, Any]] = None):
        """Initialize complete EDI system"""
        self.edi_generator = DABSEDIGenerator()
        self.pdf_converter = DABSPDFToNAXMLConverter()
        self.delivery_manager = EDIDeliveryManager(smtp_config)
        self.upc_manager = UPCLookupManager()
        
        # Supported file formats
        self.supported_formats = {
            '.xlsx': self._process_excel_file,
            '.xls': self._process_excel_file,
            '.csv': self._process_csv_file,
            '.pdf': self._process_pdf_file,
            '.json': self._process_json_file
        }
        
        logger.info("DABS EDI Complete System initialized")
    
    async def enhance_items_with_upcs(self, items: List[DABSItem]) -> List[DABSItem]:
        """
        Enhance DABS items with UPC lookup for SSCS barcode scanning
        
        Args:
            items: List of DABS items to enhance
            
        Returns:
            Enhanced items with UPC data
        """
        logger.info(f"Enhancing {len(items)} items with UPC lookup")
        
        # Prepare lookup data
        lookup_items = [(item.csc_code, item.description) for item in items]
        
        # Bulk lookup UPCs
        upc_results = await self.upc_manager.bulk_lookup_upcs(lookup_items)
        
        # Enhance items with UPC data
        enhanced_items = []
        upc_found_count = 0
        
        for item in items:
            upc_result = upc_results.get(item.csc_code)
            
            if upc_result and upc_result.upc_12_digit:
                # Use 11-digit UPC for Verifone compatibility
                item.upc = upc_result.upc_11_digit or upc_result.upc_12_digit
                upc_found_count += 1
                logger.debug(f"Enhanced {item.csc_code} with UPC: {item.upc}")
            else:
                # Keep empty UPC for manual lookup later
                item.upc = ""
                logger.debug(f"No UPC found for {item.csc_code}: {item.description}")
            
            enhanced_items.append(item)
        
        logger.info(f"UPC enhancement complete: {upc_found_count}/{len(items)} items have UPCs")
        return enhanced_items
    
    async def process_dabs_file(self, file_path: Union[str, Path], 
                               send_edi: bool = True,
                               invoice_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Process any DABS file format and convert to EDI
        
        Args:
            file_path: Path to DABS file (Excel, PDF, CSV, JSON)
            send_edi: Whether to send EDI email automatically
            invoice_number: Optional custom invoice number
            
        Returns:
            Complete processing results
        """
        file_path = Path(file_path)
        logger.info(f"Processing DABS file: {file_path.name}")
        
        try:
            # Check file exists
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'File not found: {file_path}',
                    'file_type': 'unknown'
                }
            
            # Determine file type and processor
            file_extension = file_path.suffix.lower()
            if file_extension not in self.supported_formats:
                return {
                    'success': False,
                    'error': f'Unsupported file format: {file_extension}',
                    'file_type': file_extension,
                    'supported_formats': list(self.supported_formats.keys())
                }
            
            # Process file based on type
            processor = self.supported_formats[file_extension]
            processing_result = await processor(file_path)
            
            if not processing_result['success']:
                return processing_result
            
            # Enhance items with UPC lookup for SSCS barcode scanning
            dabs_items = processing_result['dabs_items']
            enhanced_items = await self.enhance_items_with_upcs(dabs_items)
            
            # Generate NAXML with UPC-enhanced items
            naxml_invoice_number = invoice_number or f"DABS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            naxml_content = self.edi_generator.generate_naxml(enhanced_items, naxml_invoice_number)
            
            # Validate NAXML
            validation = self.edi_generator.validate_naxml(naxml_content)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': f'NAXML validation failed: {validation["errors"]}',
                    'processing_result': processing_result,
                    'validation_result': validation
                }
            
            # Save NAXML file
            naxml_file_path = self.edi_generator.save_naxml_file(naxml_content)
            
            # Send EDI if requested
            delivery_result = None
            if send_edi:
                delivery_result = self.delivery_manager.deliver_dabs_invoice(naxml_content, naxml_invoice_number)
            
            # Create comprehensive result
            result = {
                'success': True,
                'file_type': file_extension,
                'source_file': str(file_path),
                'items_processed': len(enhanced_items),
                'naxml_content': naxml_content,
                'naxml_file_path': naxml_file_path,
                'invoice_number': naxml_invoice_number,
                'processing_result': processing_result,
                'validation_result': validation,
                'delivery_result': delivery_result,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"DABS file processing complete: {len(dabs_items)} items, EDI sent: {send_edi}")
            return result
            
        except Exception as e:
            logger.error(f"DABS file processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_type': file_extension if 'file_extension' in locals() else 'unknown',
                'source_file': str(file_path)
            }
    
    async def _process_excel_file(self, file_path: Path) -> Dict[str, Any]:
        """Process Excel file to DABS items"""
        try:
            logger.info(f"Processing Excel file: {file_path.name}")
            
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Validate required columns
            required_columns = ['CSC Code', 'Description', 'Retail Price']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                # Try alternative column names
                column_mapping = {
                    'CSC Code': ['CSC', 'Code', 'Item Code', 'SKU'],
                    'Description': ['Product', 'Item', 'Name', 'Product Name'],
                    'Retail Price': ['Price', 'Unit Price', 'Retail', 'Cost']
                }
                
                for required_col in missing_columns:
                    found = False
                    for alt_col in column_mapping.get(required_col, []):
                        if alt_col in df.columns:
                            df[required_col] = df[alt_col]
                            found = True
                            break
                    if not found:
                        return {
                            'success': False,
                            'error': f'Missing required column: {required_col}',
                            'available_columns': list(df.columns),
                            'required_columns': required_columns
                        }
            
            # Convert to DABS items
            dabs_items = []
            for index, row in df.iterrows():
                try:
                    # Extract basic fields
                    csc_code = str(row['CSC Code']).strip()
                    description = str(row['Description']).strip()[:50]
                    retail_price = float(row['Retail Price'])
                    
                    # Extract optional fields
                    cost = float(row.get('Cost', retail_price * 0.75))  # Default to 75% of retail
                    category = str(row.get('Category', 'SPIRITS')).upper()
                    size = str(row.get('Size', '750ml'))
                    upc = str(row.get('UPC', '')).strip() if pd.notna(row.get('UPC')) else None
                    
                    # Validate data
                    if not csc_code or not description or retail_price <= 0:
                        logger.warning(f"Row {index + 1}: Invalid data - skipping")
                        continue
                    
                    item = DABSItem(
                        csc_code=csc_code,
                        description=description,
                        retail_price=retail_price,
                        cost=cost,
                        category=category,
                        size=size,
                        upc=upc,
                        vendor_item_code=csc_code
                    )
                    
                    dabs_items.append(item)
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Row {index + 1}: Error processing - {str(e)}")
                    continue
            
            logger.info(f"Excel processing complete: {len(dabs_items)} items from {len(df)} rows")
            
            return {
                'success': True,
                'dabs_items': dabs_items,
                'source_rows': len(df),
                'items_created': len(dabs_items),
                'processing_method': 'excel'
            }
            
        except Exception as e:
            logger.error(f"Excel processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processing_method': 'excel'
            }
    
    async def _process_csv_file(self, file_path: Path) -> Dict[str, Any]:
        """Process CSV file to DABS items"""
        try:
            logger.info(f"Processing CSV file: {file_path.name}")
            
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Use same logic as Excel processing
            excel_result = await self._process_excel_file_dataframe(df)
            excel_result['processing_method'] = 'csv'
            
            return excel_result
            
        except Exception as e:
            logger.error(f"CSV processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processing_method': 'csv'
            }
    
    async def _process_pdf_file(self, file_path: Path) -> Dict[str, Any]:
        """Process PDF file to DABS items"""
        try:
            logger.info(f"Processing PDF file: {file_path.name}")
            
            # Use PDF converter
            conversion_result = await self.pdf_converter.convert_pdf_to_naxml(file_path)
            
            if not conversion_result['success']:
                return {
                    'success': False,
                    'error': conversion_result.get('error', 'PDF conversion failed'),
                    'processing_method': 'pdf',
                    'conversion_result': conversion_result
                }
            
            # Extract DABS items from the conversion result
            # Since PDF converter generates NAXML, we need to extract items differently
            extraction_result = conversion_result.get('extraction_result')
            
            if not extraction_result or not extraction_result.success:
                return {
                    'success': False,
                    'error': 'PDF text extraction failed',
                    'processing_method': 'pdf'
                }
            
            # Parse items from PDF text using enhanced patterns
            dabs_items = await self._parse_items_from_pdf_text(extraction_result.raw_text)
            
            return {
                'success': True,
                'dabs_items': dabs_items,
                'items_created': len(dabs_items),
                'processing_method': 'pdf',
                'extraction_result': extraction_result
            }
            
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processing_method': 'pdf'
            }
    
    async def _process_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Process JSON file to DABS items"""
        try:
            logger.info(f"Processing JSON file: {file_path.name}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            items_data = []
            if isinstance(data, list):
                items_data = data
            elif isinstance(data, dict):
                # Look for items in common keys
                for key in ['items', 'products', 'data', 'dabs_items']:
                    if key in data and isinstance(data[key], list):
                        items_data = data[key]
                        break
                
                if not items_data:
                    items_data = [data]  # Single item
            
            # Convert to DABS items
            dabs_items = []
            for item_data in items_data:
                try:
                    item = DABSItem(
                        csc_code=str(item_data.get('csc_code', item_data.get('code', ''))),
                        description=str(item_data.get('description', ''))[:50],
                        retail_price=float(item_data.get('retail_price', item_data.get('price', 0))),
                        cost=float(item_data.get('cost', item_data.get('retail_price', 0) * 0.75)),
                        category=str(item_data.get('category', 'SPIRITS')).upper(),
                        size=str(item_data.get('size', '750ml')),
                        upc=item_data.get('upc'),
                        vendor_item_code=str(item_data.get('vendor_item_code', item_data.get('csc_code', '')))
                    )
                    
                    if item.csc_code and item.description and item.retail_price > 0:
                        dabs_items.append(item)
                    
                except (ValueError, TypeError, KeyError) as e:
                    logger.warning(f"Error processing JSON item: {e}")
                    continue
            
            logger.info(f"JSON processing complete: {len(dabs_items)} items")
            
            return {
                'success': True,
                'dabs_items': dabs_items,
                'items_created': len(dabs_items),
                'processing_method': 'json'
            }
            
        except Exception as e:
            logger.error(f"JSON processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processing_method': 'json'
            }
    
    async def _parse_items_from_pdf_text(self, text: str) -> List[DABSItem]:
        """Enhanced PDF text parsing for DABS items"""
        items = []
        
        # Enhanced patterns for DABS PDFs
        patterns = [
            # Pattern 1: CSC Code followed by description and price
            r'(\d{4,6})\s+([^$\n]+?)\s+\$?([0-9,]+\.\d{2})',
            # Pattern 2: Description - Code format
            r'([^-\n]+)\s*-\s*(\d{4,6})\s+\$?([0-9,]+\.\d{2})',
            # Pattern 3: Table format with pipes
            r'(\d{4,6})\s*\|\s*([^|]+)\s*\|\s*\$?([0-9,]+\.\d{2})',
            # Pattern 4: Simple code description price
            r'(\d{4,6})\s+(.+?)\s+([0-9,]+\.\d{2})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            
            for match in matches:
                try:
                    if len(match) >= 3:
                        # Determine which element is which based on pattern
                        if match[0].isdigit() and len(match[0]) >= 4:  # CSC code first
                            csc_code = match[0]
                            description = match[1].strip()
                            price = float(match[2].replace(',', ''))
                        elif match[1].isdigit() and len(match[1]) >= 4:  # CSC code second
                            description = match[0].strip()
                            csc_code = match[1]
                            price = float(match[2].replace(',', ''))
                        else:
                            continue
                        
                        # Skip if already found this item
                        if any(item.csc_code == csc_code for item in items):
                            continue
                        
                        # Create DABS item
                        item = DABSItem(
                            csc_code=csc_code,
                            description=description[:50],
                            retail_price=price,
                            cost=price * 0.75,  # Estimate cost
                            category=self._determine_category_from_description(description),
                            size=self._extract_size_from_description(description),
                            vendor_item_code=csc_code
                        )
                        
                        items.append(item)
                        
                except (ValueError, IndexError) as e:
                    continue
        
        logger.info(f"Parsed {len(items)} items from PDF text")
        return items
    
    def _determine_category_from_description(self, description: str) -> str:
        """Determine category from description"""
        description_lower = description.lower()
        
        spirits_keywords = ['vodka', 'whiskey', 'rum', 'gin', 'tequila', 'brandy', 'bourbon']
        wine_keywords = ['wine', 'chardonnay', 'cabernet', 'merlot', 'pinot', 'sauvignon']
        beer_keywords = ['beer', 'ale', 'lager', 'ipa', 'stout', 'porter']
        
        if any(keyword in description_lower for keyword in spirits_keywords):
            return 'SPIRITS'
        elif any(keyword in description_lower for keyword in wine_keywords):
            return 'WINE'
        elif any(keyword in description_lower for keyword in beer_keywords):
            return 'BEER'
        else:
            return 'SPIRITS'  # Default
    
    def _extract_size_from_description(self, description: str) -> str:
        """Extract size from description"""
        import re
        
        size_patterns = [
            r'(\d+(?:\.\d+)?\s*(?:ML|ml|L|l|OZ|oz))',
            r'(\d+\.\d+L)',
            r'(\d+ML)'
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, description)
            if match:
                return match.group(1)
        
        return '750ml'  # Default
    
    async def batch_process_directory(self, directory_path: Union[str, Path], 
                                    send_edi: bool = True) -> Dict[str, Any]:
        """
        Process all supported files in a directory
        
        Args:
            directory_path: Directory containing DABS files
            send_edi: Whether to send EDI emails for each file
            
        Returns:
            Batch processing results
        """
        directory_path = Path(directory_path)
        logger.info(f"Batch processing directory: {directory_path}")
        
        if not directory_path.exists():
            return {
                'success': False,
                'error': f'Directory not found: {directory_path}'
            }
        
        # Find all supported files
        supported_files = []
        for extension in self.supported_formats.keys():
            supported_files.extend(directory_path.glob(f"*{extension}"))
        
        if not supported_files:
            return {
                'success': False,
                'error': f'No supported files found in {directory_path}',
                'supported_formats': list(self.supported_formats.keys())
            }
        
        # Process each file
        results = {
            'success': True,
            'directory': str(directory_path),
            'files_found': len(supported_files),
            'files_processed': 0,
            'files_successful': 0,
            'files_failed': 0,
            'total_items': 0,
            'processing_results': [],
            'failed_files': []
        }
        
        for file_path in supported_files:
            try:
                logger.info(f"Processing: {file_path.name}")
                
                result = await self.process_dabs_file(file_path, send_edi=send_edi)
                results['processing_results'].append(result)
                results['files_processed'] += 1
                
                if result['success']:
                    results['files_successful'] += 1
                    results['total_items'] += result['items_processed']
                else:
                    results['files_failed'] += 1
                    results['failed_files'].append({
                        'file': str(file_path),
                        'error': result.get('error', 'Unknown error')
                    })
                
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
                results['files_failed'] += 1
                results['failed_files'].append({
                    'file': str(file_path),
                    'error': str(e)
                })
        
        logger.info(f"Batch processing complete: {results['files_successful']}/{results['files_processed']} successful")
        return results

# Example usage
async def main():
    """Example usage of complete DABS EDI system"""
    
    # Initialize system
    system = DABSEDICompleteSystem()
    
    # Test with different file types
    test_files = [
        "data/DABS_Monthly_Update.xlsx",
        "data/dabs_orders/pdfs/sample_invoice.pdf",
        "data/dabs_export.csv"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"\nProcessing: {test_file}")
            result = await system.process_dabs_file(test_file, send_edi=False)
            
            if result['success']:
                print(f"✅ Success: {result['items_processed']} items processed")
                print(f"   NAXML file: {result['naxml_file_path']}")
            else:
                print(f"❌ Failed: {result['error']}")
        else:
            print(f"⚠️  File not found: {test_file}")

if __name__ == "__main__":
    asyncio.run(main())
