#!/usr/bin/env python3
"""
Manual UPC Lookup Tool for DABS Product Locator
Enhanced search for items not found by automated system
"""

import asyncio
import aiohttp
import re
import logging
from typing import Optional, Dict, List, Tuple
from bs4 import BeautifulSoup
import json
from urllib.parse import quote_plus

import sys
import os
sys.path.append(os.path.dirname(__file__))
from verifone_formatter import VerifoneFormatter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ManualUPCLookup:
    """Enhanced manual UPC lookup using DABS Product Locator"""
    
    def __init__(self):
        self.session = None
        self.base_url = "https://webapps2.abc.utah.gov/ProdApps/ProductLocatorCore"
        
        # Enhanced search strategies
        self.search_strategies = [
            'exact_code',      # Search by exact DABS code
            'product_name',    # Search by product name
            'brand_only',      # Search by brand name only
            'partial_name',    # Search by partial name
            'category_brand'   # Search by category + brand
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def extract_search_terms(self, item_name: str, dabs_code: str) -> Dict[str, List[str]]:
        """Extract various search terms from item name"""
        
        # Clean the item name
        clean_name = re.sub(r'[^\w\s]', ' ', item_name.upper()).strip()
        words = clean_name.split()
        
        # Extract brand (usually first 1-2 words)
        brand_words = []
        product_words = []
        size_words = []
        
        # Common size patterns
        size_patterns = ['ML', 'L', 'OZ', '750ML', '1000ML', '1750ML', '473ML']
        
        # Common product type words
        product_types = ['VODKA', 'TEQUILA', 'WINE', 'BEER', 'WHISKEY', 'GIN', 'RUM', 'IPA', 'ALE']
        
        for word in words:
            if any(size in word for size in size_patterns):
                size_words.append(word)
            elif word in product_types:
                product_words.append(word)
            elif len(brand_words) < 2:  # First 2 words likely brand
                brand_words.append(word)
            else:
                product_words.append(word)
        
        return {
            'brand': brand_words,
            'product': product_words,
            'size': size_words,
            'full_name': words,
            'dabs_code': [dabs_code]
        }
    
    async def search_dabs_by_code(self, dabs_code: str) -> Optional[Dict]:
        """Search DABS by exact code"""
        try:
            search_url = f"{self.base_url}/Search"
            
            # Try different code search approaches
            code_variations = [
                dabs_code,
                dabs_code.zfill(6),  # Pad with zeros
                dabs_code.lstrip('0'),  # Remove leading zeros
            ]
            
            for code in code_variations:
                await asyncio.sleep(2)  # Rate limiting
                
                async with self.session.get(search_url, params={
                    'searchTerm': code,
                    'searchType': 'ProductCode'
                }) as response:
                    
                    if response.status == 200:
                        html = await response.text()
                        result = self.extract_product_info(html, dabs_code)
                        if result:
                            logger.info(f"Found product by code {code}: {result}")
                            return result
            
        except Exception as e:
            logger.error(f"Error searching by code {dabs_code}: {e}")
        
        return None
    
    async def search_dabs_by_name(self, search_terms: Dict[str, List[str]], dabs_code: str) -> Optional[Dict]:
        """Search DABS by product name variations"""
        try:
            search_url = f"{self.base_url}/Search"
            
            # Create search variations
            search_variations = []
            
            # Brand + product type
            if search_terms['brand'] and search_terms['product']:
                search_variations.append(' '.join(search_terms['brand'][:1] + search_terms['product'][:1]))
            
            # Brand only
            if search_terms['brand']:
                search_variations.append(' '.join(search_terms['brand'][:2]))
            
            # Product type only
            if search_terms['product']:
                search_variations.append(' '.join(search_terms['product'][:2]))
            
            # Full name (first 3 words)
            if search_terms['full_name']:
                search_variations.append(' '.join(search_terms['full_name'][:3]))
            
            for search_term in search_variations:
                await asyncio.sleep(2)  # Rate limiting
                
                logger.info(f"Searching DABS for: '{search_term}'")
                
                async with self.session.get(search_url, params={
                    'searchTerm': search_term,
                    'searchType': 'ProductName'
                }) as response:
                    
                    if response.status == 200:
                        html = await response.text()
                        result = self.extract_product_info(html, dabs_code, search_term)
                        if result:
                            logger.info(f"Found product by name '{search_term}': {result}")
                            return result
            
        except Exception as e:
            logger.error(f"Error searching by name: {e}")
        
        return None
    
    def extract_product_info(self, html: str, dabs_code: str, search_term: str = None) -> Optional[Dict]:
        """Extract product information and UPC from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for product information in various formats
            product_info = {
                'dabs_code': dabs_code,
                'search_term': search_term,
                'found_on_page': True
            }
            
            # Search for UPC patterns in the HTML
            upc_patterns = [
                r'UPC[:\s]*(\d{12})',
                r'barcode[:\s]*(\d{12})',
                r'product[_\s]code[:\s]*(\d{12})',
                r'item[_\s]code[:\s]*(\d{12})',
                r'(\d{12})',  # Generic 12-digit pattern
            ]
            
            page_text = soup.get_text()
            
            for pattern in upc_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    if len(match) == 12 and match.isdigit():
                        # Validate UPC checksum
                        if VerifoneFormatter.validate_upc_checksum(match):
                            product_info['upc'] = match
                            product_info['verifone_upc'] = VerifoneFormatter.format_for_verifone(match)
                            logger.info(f"Found valid UPC: {match} → {product_info['verifone_upc']}")
                            return product_info
            
            # Look for product details even if no UPC found
            detail_patterns = {
                'name': r'product[_\s]name[:\s]*([^\n\r]+)',
                'brand': r'brand[:\s]*([^\n\r]+)',
                'size': r'size[:\s]*([^\n\r]+)',
                'category': r'category[:\s]*([^\n\r]+)',
                'price': r'price[:\s]*\$?([0-9,.]+)'
            }
            
            for key, pattern in detail_patterns.items():
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    product_info[key] = match.group(1).strip()
            
            # Return info even without UPC for manual review
            if len(product_info) > 3:  # More than just basic fields
                return product_info
            
        except Exception as e:
            logger.error(f"Error extracting product info: {e}")
        
        return None
    
    async def comprehensive_lookup(self, item_name: str, dabs_code: str) -> Dict:
        """Perform comprehensive UPC lookup using all strategies"""
        
        logger.info(f"\n🔍 Starting comprehensive lookup for: {item_name} ({dabs_code})")
        
        result = {
            'item_name': item_name,
            'dabs_code': dabs_code,
            'upc': None,
            'verifone_upc': None,
            'found_method': None,
            'product_info': None,
            'search_attempts': []
        }
        
        # Extract search terms
        search_terms = self.extract_search_terms(item_name, dabs_code)
        logger.info(f"Search terms: {search_terms}")
        
        # Strategy 1: Search by exact DABS code
        logger.info("🎯 Strategy 1: Searching by DABS code...")
        code_result = await self.search_dabs_by_code(dabs_code)
        result['search_attempts'].append(('dabs_code', code_result is not None))
        
        if code_result and code_result.get('upc'):
            result.update({
                'upc': code_result['upc'],
                'verifone_upc': code_result['verifone_upc'],
                'found_method': 'dabs_code',
                'product_info': code_result
            })
            return result
        
        # Strategy 2: Search by product name variations
        logger.info("🎯 Strategy 2: Searching by product name...")
        name_result = await self.search_dabs_by_name(search_terms, dabs_code)
        result['search_attempts'].append(('product_name', name_result is not None))
        
        if name_result and name_result.get('upc'):
            result.update({
                'upc': name_result['upc'],
                'verifone_upc': name_result['verifone_upc'],
                'found_method': 'product_name',
                'product_info': name_result
            })
            return result
        
        # If no UPC found, return the best available info
        if code_result or name_result:
            result['product_info'] = code_result or name_result
            result['found_method'] = 'partial_info'
        
        return result

# Test function for the remaining items
async def lookup_remaining_items():
    """Lookup UPCs for the 2 remaining items from Order 233811"""
    
    remaining_items = [
        ("SUGAR HOUSE VODKA 1750ml", "039593"),
        ("HELPER BEER CIRCLE BACK IPA 473ml", "926272")
    ]
    
    print("🔍 Manual UPC Lookup for Remaining Items - Order 233811")
    print("=" * 60)
    
    async with ManualUPCLookup() as lookup:
        results = []
        
        for item_name, dabs_code in remaining_items:
            result = await lookup.comprehensive_lookup(item_name, dabs_code)
            results.append(result)
            
            # Display result
            print(f"\n📋 {item_name} ({dabs_code})")
            print("-" * 40)
            
            if result['upc']:
                print(f"✅ UPC Found: {result['upc']}")
                print(f"✅ Verifone UPC: {result['verifone_upc']}")
                print(f"✅ Found via: {result['found_method']}")
            else:
                print(f"❌ UPC Not Found")
                print(f"🔍 Search attempts: {len(result['search_attempts'])}")
                
                if result['product_info']:
                    print(f"📋 Product info found:")
                    for key, value in result['product_info'].items():
                        if key not in ['dabs_code', 'search_term']:
                            print(f"   {key}: {value}")
                else:
                    print(f"⚠️  No product information found")
                    print(f"💡 Manual search recommended at:")
                    print(f"   https://webapps2.abc.utah.gov/ProdApps/ProductLocatorCore")
        
        # Summary
        found_count = sum(1 for r in results if r['upc'])
        print(f"\n📊 Manual Lookup Summary:")
        print(f"   Items processed: {len(results)}")
        print(f"   UPCs found: {found_count}")
        print(f"   Success rate: {(found_count/len(results)*100):.1f}%")
        
        return results

if __name__ == "__main__":
    asyncio.run(lookup_remaining_items())
