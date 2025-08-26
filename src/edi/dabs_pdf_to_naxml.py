"""
DABS PDF to NAXML Converter
Consistent conversion of DABS PDF invoices/orders to NAXML format for EDI delivery

Business Context:
- Handles DABS PDF invoices, order confirmations, and price lists
- Converts to SSCS-compatible NAXML format
- Maintains Utah Package Agency compliance
- Enables automated EDI processing from PDF sources
"""

import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from decimal import Decimal
import pdfplumber
import pandas as pd

from dabs_edi_generator import DABSEDIGenerator, DABSItem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PDFExtractionResult:
    """Result of PDF text extraction and parsing"""
    success: bool
    document_type: str  # 'invoice', 'order', 'price_list', 'unknown'
    items_found: int
    total_value: float
    extraction_timestamp: str
    source_file: str
    error_message: Optional[str] = None
    raw_text: Optional[str] = None

class DABSPDFToNAXMLConverter:
    """Convert DABS PDF documents to NAXML format for EDI processing"""
    
    def __init__(self):
        self.edi_generator = DABSEDIGenerator()
        
        # PDF parsing patterns for different DABS document types
        self.patterns = {
            'invoice': {
                'header_patterns': {
                    'invoice_number': r'Invoice\s*#?\s*:?\s*([A-Z0-9\-]+)',
                    'invoice_date': r'Invoice\s*Date\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                    'order_id': r'Order\s*(?:ID|#)\s*:?\s*(\d+)',
                    'delivery_date': r'Delivery\s*Date\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                    'store_info': r'Store\s*:?\s*([^\n]+)',
                    'total_amount': r'Total\s*:?\s*\$?([0-9,]+\.?\d{0,2})'
                },
                'line_item_patterns': [
                    # Pattern 1: Description - Code, Price, Qty, Extended
                    r'([^-\n]+)\s*-\s*(\d+)\s+\$?([0-9,]+\.\d{2})\s+(\d+)\s+\$?([0-9,]+\.\d{2})',
                    # Pattern 2: Code | Description | Price | Qty | Total
                    r'(\d+)\s*\|\s*([^|]+)\s*\|\s*\$?([0-9,]+\.\d{2})\s*\|\s*(\d+)\s*\|\s*\$?([0-9,]+\.\d{2})',
                    # Pattern 3: CSC Code Description $Price Qty $Extended
                    r'(\d{4,6})\s+([^$]+)\s+\$([0-9,]+\.\d{2})\s+(\d+)\s+\$([0-9,]+\.\d{2})'
                ]
            },
            'order': {
                'header_patterns': {
                    'order_id': r'Order\s*(?:ID|#)\s*:?\s*(\d+)',
                    'sales_order': r'Sales\s*Order\s*:?\s*(SOO\d+)',
                    'delivery_date': r'Delivery\s*Date\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                    'status': r'Status\s*:?\s*([^\n]+)',
                    'store': r'Store\s*:?\s*([^\n]+)',
                    'reference': r'Reference\s*:?\s*([^\n]+)'
                },
                'line_item_patterns': [
                    # DABS order format
                    r'([^-\n]+)\s*-\s*(\d+)\s+\$?([0-9,]+\.\d{2})\s+(\d+)\s+\$?([0-9,]+\.\d{2})',
                    # Alternative format
                    r'(\d{4,6})\s+([^$\n]+)\s+\$([0-9,]+\.\d{2})\s+(\d+)\s+\$([0-9,]+\.\d{2})'
                ]
            },
            'price_list': {
                'header_patterns': {
                    'effective_date': r'Effective\s*Date\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                    'price_list_id': r'Price\s*List\s*(?:ID|#)\s*:?\s*([A-Z0-9\-]+)',
                    'category': r'Category\s*:?\s*([^\n]+)'
                },
                'line_item_patterns': [
                    # Price list format: Code Description Size Category Price
                    r'(\d{4,6})\s+([^$\n]+?)\s+(\d+(?:\.\d+)?(?:ML|L|OZ)?)\s+([A-Z]+)\s+\$([0-9,]+\.\d{2})',
                    # Alternative format
                    r'(\d{4,6})\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*\$?([0-9,]+\.\d{2})'
                ]
            }
        }
        
        logger.info("DABS PDF to NAXML converter initialized")
    
    async def convert_pdf_to_naxml(self, pdf_path: Union[str, Path], 
                                  document_type: Optional[str] = None,
                                  invoice_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert DABS PDF to NAXML format
        
        Args:
            pdf_path: Path to PDF file
            document_type: Optional document type hint ('invoice', 'order', 'price_list')
            invoice_number: Optional custom invoice number
            
        Returns:
            Dictionary with conversion results and NAXML content
        """
        pdf_path = Path(pdf_path)
        logger.info(f"Converting DABS PDF to NAXML: {pdf_path.name}")
        
        try:
            # Extract text from PDF
            extraction_result = await self._extract_pdf_content(pdf_path)
            
            if not extraction_result.success:
                return {
                    'success': False,
                    'error': extraction_result.error_message,
                    'extraction_result': extraction_result
                }
            
            # Parse items from extracted text
            dabs_items = await self._parse_items_from_text(
                extraction_result.raw_text, 
                extraction_result.document_type
            )
            
            if not dabs_items:
                return {
                    'success': False,
                    'error': 'No valid items found in PDF',
                    'extraction_result': extraction_result
                }
            
            # Generate NAXML
            naxml_invoice_number = invoice_number or f"PDF_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            naxml_content = self.edi_generator.generate_naxml(dabs_items, naxml_invoice_number)
            
            # Validate NAXML
            validation = self.edi_generator.validate_naxml(naxml_content)
            
            if not validation['valid']:
                return {
                    'success': False,
                    'error': f"NAXML validation failed: {validation['errors']}",
                    'extraction_result': extraction_result,
                    'validation_result': validation
                }
            
            # Save NAXML file
            naxml_file_path = self.edi_generator.save_naxml_file(naxml_content)
            
            logger.info(f"PDF to NAXML conversion successful: {len(dabs_items)} items converted")
            
            return {
                'success': True,
                'naxml_content': naxml_content,
                'naxml_file_path': naxml_file_path,
                'items_converted': len(dabs_items),
                'extraction_result': extraction_result,
                'validation_result': validation,
                'invoice_number': naxml_invoice_number
            }
            
        except Exception as e:
            logger.error(f"PDF to NAXML conversion failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'extraction_result': None
            }
    
    async def _extract_pdf_content(self, pdf_path: Path) -> PDFExtractionResult:
        """
        Extract and analyze content from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            PDFExtractionResult with extracted content and metadata
        """
        try:
            # Extract text using pdfplumber
            text_content = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num + 1}: {e}")
                        continue
            
            if not text_content:
                return PDFExtractionResult(
                    success=False,
                    document_type='unknown',
                    items_found=0,
                    total_value=0.0,
                    extraction_timestamp=datetime.now().isoformat(),
                    source_file=str(pdf_path),
                    error_message="No text content extracted from PDF"
                )
            
            raw_text = '\n\n'.join(text_content)
            
            # Determine document type
            document_type = self._identify_document_type(raw_text)
            
            # Count potential items
            items_found = self._count_potential_items(raw_text, document_type)
            
            # Extract total value if available
            total_value = self._extract_total_value(raw_text)
            
            return PDFExtractionResult(
                success=True,
                document_type=document_type,
                items_found=items_found,
                total_value=total_value,
                extraction_timestamp=datetime.now().isoformat(),
                source_file=str(pdf_path),
                raw_text=raw_text
            )
            
        except Exception as e:
            logger.error(f"PDF content extraction failed: {str(e)}")
            return PDFExtractionResult(
                success=False,
                document_type='unknown',
                items_found=0,
                total_value=0.0,
                extraction_timestamp=datetime.now().isoformat(),
                source_file=str(pdf_path),
                error_message=str(e)
            )
    
    def _identify_document_type(self, text: str) -> str:
        """
        Identify the type of DABS document based on text content
        
        Args:
            text: Extracted PDF text
            
        Returns:
            Document type string
        """
        text_lower = text.lower()
        
        # Check for invoice indicators
        invoice_indicators = ['invoice', 'bill', 'amount due', 'payment terms']
        if any(indicator in text_lower for indicator in invoice_indicators):
            return 'invoice'
        
        # Check for order indicators
        order_indicators = ['order id', 'sales order', 'delivery date', 'order status']
        if any(indicator in text_lower for indicator in order_indicators):
            return 'order'
        
        # Check for price list indicators
        price_list_indicators = ['price list', 'effective date', 'retail price', 'category']
        if any(indicator in text_lower for indicator in price_list_indicators):
            return 'price_list'
        
        return 'unknown'
    
    def _count_potential_items(self, text: str, document_type: str) -> int:
        """Count potential line items in the text"""
        if document_type not in self.patterns:
            return 0
        
        total_matches = 0
        for pattern in self.patterns[document_type]['line_item_patterns']:
            matches = re.findall(pattern, text, re.MULTILINE)
            total_matches += len(matches)
        
        return total_matches
    
    def _extract_total_value(self, text: str) -> float:
        """Extract total value from document if available"""
        total_patterns = [
            r'Total\s*:?\s*\$?([0-9,]+\.?\d{0,2})',
            r'Grand\s*Total\s*:?\s*\$?([0-9,]+\.?\d{0,2})',
            r'Amount\s*Due\s*:?\s*\$?([0-9,]+\.?\d{0,2})'
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    continue
        
        return 0.0
    
    async def _parse_items_from_text(self, text: str, document_type: str) -> List[DABSItem]:
        """
        Parse DABS items from extracted text
        
        Args:
            text: Extracted PDF text
            document_type: Type of document being processed
            
        Returns:
            List of DABSItem objects
        """
        if document_type not in self.patterns:
            logger.warning(f"Unknown document type: {document_type}")
            return []
        
        items = []
        patterns = self.patterns[document_type]['line_item_patterns']
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            
            for match in matches:
                try:
                    item = self._create_dabs_item_from_match(match, document_type, pattern)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.warning(f"Error creating item from match {match}: {e}")
                    continue
        
        # Remove duplicates based on CSC code
        unique_items = {}
        for item in items:
            if item.csc_code not in unique_items:
                unique_items[item.csc_code] = item
        
        logger.info(f"Parsed {len(unique_items)} unique items from {document_type}")
        return list(unique_items.values())
    
    def _create_dabs_item_from_match(self, match: tuple, document_type: str, pattern: str) -> Optional[DABSItem]:
        """
        Create DABSItem from regex match based on document type and pattern
        
        Args:
            match: Regex match tuple
            document_type: Type of document
            pattern: Pattern that was matched
            
        Returns:
            DABSItem object or None if creation fails
        """
        try:
            if document_type == 'invoice' or document_type == 'order':
                if len(match) >= 5:
                    # Standard format: description, code, price, qty, extended
                    if match[1].isdigit():  # Code is second element
                        description = match[0].strip()
                        csc_code = match[1]
                        unit_price = float(match[2].replace(',', ''))
                        quantity = int(match[3])
                        extended_price = float(match[4].replace(',', ''))
                        cost = unit_price * 0.75  # Estimate cost at 75% of retail
                    else:  # Code is first element
                        csc_code = match[0]
                        description = match[1].strip()
                        unit_price = float(match[2].replace(',', ''))
                        quantity = int(match[3])
                        extended_price = float(match[4].replace(',', ''))
                        cost = unit_price * 0.75
                    
                    # Determine category from description
                    category = self._determine_category(description)
                    
                    return DABSItem(
                        csc_code=csc_code,
                        description=description[:50],  # Limit description length
                        retail_price=unit_price,
                        cost=cost,
                        category=category,
                        size=self._extract_size(description),
                        vendor_item_code=csc_code
                    )
            
            elif document_type == 'price_list':
                if len(match) >= 5:
                    # Price list format: code, description, size, category, price
                    csc_code = match[0]
                    description = match[1].strip()
                    size = match[2] if len(match) > 2 else ''
                    category = match[3] if len(match) > 3 else 'SPIRITS'
                    price = float(match[4].replace(',', ''))
                    cost = price * 0.75  # Estimate cost
                    
                    return DABSItem(
                        csc_code=csc_code,
                        description=description[:50],
                        retail_price=price,
                        cost=cost,
                        category=category.upper(),
                        size=size,
                        vendor_item_code=csc_code
                    )
            
            return None
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Error creating DABS item from match: {e}")
            return None
    
    def _determine_category(self, description: str) -> str:
        """Determine product category from description"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['vodka', 'whiskey', 'rum', 'gin', 'tequila', 'brandy']):
            return 'SPIRITS'
        elif any(word in description_lower for word in ['wine', 'chardonnay', 'cabernet', 'merlot', 'pinot']):
            return 'WINE'
        elif any(word in description_lower for word in ['beer', 'ale', 'lager', 'ipa', 'stout']):
            return 'BEER'
        else:
            return 'SPIRITS'  # Default category
    
    def _extract_size(self, description: str) -> str:
        """Extract size information from description"""
        size_patterns = [
            r'(\d+(?:\.\d+)?\s*(?:ML|ml|L|l|OZ|oz))',
            r'(\d+(?:\.\d+)?\s*(?:LITER|liter|OUNCE|ounce))',
            r'(\d+\.\d+L)',
            r'(\d+ML)'
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return '750ml'  # Default size
    
    async def batch_convert_pdfs(self, pdf_directory: Union[str, Path], 
                                output_directory: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Convert multiple PDF files to NAXML format
        
        Args:
            pdf_directory: Directory containing PDF files
            output_directory: Optional output directory for NAXML files
            
        Returns:
            Batch conversion results
        """
        pdf_directory = Path(pdf_directory)
        output_directory = Path(output_directory) if output_directory else Path("data/edi_output/batch")
        output_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Starting batch PDF conversion from: {pdf_directory}")
        
        # Find all PDF files
        pdf_files = list(pdf_directory.glob("*.pdf"))
        
        if not pdf_files:
            return {
                'success': False,
                'error': f'No PDF files found in {pdf_directory}',
                'files_processed': 0
            }
        
        results = {
            'success': True,
            'files_processed': 0,
            'files_successful': 0,
            'files_failed': 0,
            'total_items': 0,
            'conversion_results': [],
            'failed_files': []
        }
        
        for pdf_file in pdf_files:
            try:
                logger.info(f"Processing: {pdf_file.name}")
                
                conversion_result = await self.convert_pdf_to_naxml(pdf_file)
                results['conversion_results'].append({
                    'file': str(pdf_file),
                    'result': conversion_result
                })
                
                results['files_processed'] += 1
                
                if conversion_result['success']:
                    results['files_successful'] += 1
                    results['total_items'] += conversion_result['items_converted']
                else:
                    results['files_failed'] += 1
                    results['failed_files'].append({
                        'file': str(pdf_file),
                        'error': conversion_result.get('error', 'Unknown error')
                    })
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {e}")
                results['files_failed'] += 1
                results['failed_files'].append({
                    'file': str(pdf_file),
                    'error': str(e)
                })
        
        logger.info(f"Batch conversion complete: {results['files_successful']}/{results['files_processed']} successful")
        return results

# Example usage and testing
async def main():
    """Example usage of DABS PDF to NAXML converter"""
    converter = DABSPDFToNAXMLConverter()
    
    # Example single file conversion
    pdf_file = "data/dabs_orders/pdfs/sample_dabs_invoice.pdf"
    
    if Path(pdf_file).exists():
        print(f"Converting {pdf_file} to NAXML...")
        result = await converter.convert_pdf_to_naxml(pdf_file)
        
        if result['success']:
            print(f"✅ Conversion successful!")
            print(f"   Items converted: {result['items_converted']}")
            print(f"   NAXML file: {result['naxml_file_path']}")
            print(f"   Invoice number: {result['invoice_number']}")
        else:
            print(f"❌ Conversion failed: {result['error']}")
    else:
        print(f"⚠️  Sample PDF file not found: {pdf_file}")
        print("Creating test scenario with available PDFs...")
        
        # Look for any PDF files in common directories
        search_dirs = [
            Path("data"),
            Path("dabs"),
            Path("docs")
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                pdf_files = list(search_dir.rglob("*.pdf"))
                if pdf_files:
                    print(f"Found {len(pdf_files)} PDF files in {search_dir}")
                    # Test with first PDF found
                    test_result = await converter.convert_pdf_to_naxml(pdf_files[0])
                    print(f"Test conversion result: {test_result['success']}")
                    break

if __name__ == "__main__":
    asyncio.run(main())
