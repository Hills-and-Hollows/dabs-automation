#!/usr/bin/env python3
"""
Enhanced Free UPC Verification System for DABS Items
Specialized for alcohol products with Utah DABS integration
"""

import asyncio
import aiohttp
import sqlite3
import json
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
from urllib.parse import quote_plus, urljoin
import time
from bs4 import BeautifulSoup

from verifone_formatter import VerifoneFormatter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedUPCResult:
    """Enhanced UPC verification result with Verifone formatting"""
    item_name: str
    dabs_code: str
    upc_code: Optional[str] = None
    verifone_upc: Optional[str] = None
    confidence: float = 0.0
    sources: List[str] = None
    verified: bool = False
    error: Optional[str] = None
    dabs_product_info: Optional[Dict] = None
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        
        # Auto-format for Verifone if UPC found
        if self.upc_code:
            self.verifone_upc = VerifoneFormatter.format_for_verifone(self.upc_code)

class EnhancedUPCVerifier:
    """Enhanced free multi-source UPC verification system"""
    
    def __init__(self, db_path: str = "data/upc_cache.db"):
        self.db_path = db_path
        self.session = None
        self.init_database()
        
        # Enhanced free endpoints for alcohol products
        self.endpoints = {
            'dabs_locator': 'https://webapps2.abc.utah.gov/ProdApps/ProductLocatorCore',
            'openfoodfacts': 'https://world.openfoodfacts.org',
            'wine_searcher': 'https://www.wine-searcher.com',  # Free search
            'vivino': 'https://www.vivino.com',  # Free wine database
            'untappd': 'https://untappd.com',  # Free beer database
            'distiller': 'https://distiller.com',  # Free spirits database
        }
        
        # Rate limiting (respect free APIs)
        self.rate_limits = {
            'dabs_locator': 3.0,   # More conservative for official site
            'openfoodfacts': 1.0,
            'wine_searcher': 4.0,  # Be respectful
            'vivino': 3.0,
            'untappd': 2.0,
            'distiller': 3.0,
        }
        self.last_request = {}
    
    def init_database(self):
        """Initialize enhanced SQLite cache database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enhanced_upc_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dabs_code TEXT UNIQUE NOT NULL,
                    item_name TEXT NOT NULL,
                    upc_code TEXT,
                    verifone_upc TEXT,
                    confidence REAL,
                    sources TEXT,
                    verified BOOLEAN,
                    dabs_product_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_enhanced_dabs_code ON enhanced_upc_cache(dabs_code)
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Enhanced UPC cache database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced database: {e}")
            raise
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=45),
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def get_cached_upc(self, dabs_code: str) -> Optional[EnhancedUPCResult]:
        """Get UPC from enhanced local cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT item_name, upc_code, verifone_upc, confidence, sources, verified, dabs_product_info
                FROM enhanced_upc_cache 
                WHERE dabs_code = ? AND updated_at > datetime('now', '-7 days')
            ''', (dabs_code,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                item_name, upc_code, verifone_upc, confidence, sources_json, verified, product_info_json = row
                sources = json.loads(sources_json) if sources_json else []
                product_info = json.loads(product_info_json) if product_info_json else None
                
                logger.info(f"Enhanced cache hit for {dabs_code}: {upc_code}")
                return EnhancedUPCResult(
                    item_name=item_name,
                    dabs_code=dabs_code,
                    upc_code=upc_code,
                    verifone_upc=verifone_upc,
                    confidence=confidence,
                    sources=sources,
                    verified=bool(verified),
                    dabs_product_info=product_info
                )
                
        except Exception as e:
            logger.error(f"Enhanced cache lookup error for {dabs_code}: {e}")
        
        return None
    
    def cache_upc(self, result: EnhancedUPCResult):
        """Cache enhanced UPC result"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO enhanced_upc_cache 
                (dabs_code, item_name, upc_code, verifone_upc, confidence, sources, verified, dabs_product_info, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                result.dabs_code,
                result.item_name,
                result.upc_code,
                result.verifone_upc,
                result.confidence,
                json.dumps(result.sources),
                result.verified,
                json.dumps(result.dabs_product_info) if result.dabs_product_info else None
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Enhanced cached UPC for {result.dabs_code}: {result.upc_code} → {result.verifone_upc}")
            
        except Exception as e:
            logger.error(f"Enhanced cache save error for {result.dabs_code}: {e}")
    
    async def rate_limit_wait(self, source: str):
        """Implement rate limiting for free APIs"""
        if source in self.last_request:
            elapsed = time.time() - self.last_request[source]
            wait_time = self.rate_limits.get(source, 2.0)
            
            if elapsed < wait_time:
                sleep_time = wait_time - elapsed
                logger.info(f"Rate limiting {source}: waiting {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
        
        self.last_request[source] = time.time()
    
    async def search_dabs_locator_enhanced(self, item_name: str, dabs_code: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Enhanced Utah DABS Product Locator search with product details"""
        try:
            await self.rate_limit_wait('dabs_locator')
            
            # Clean item name for search
            search_term = re.sub(r'[^\w\s]', ' ', item_name).strip()
            search_words = search_term.split()[:4]  # Use first 4 words
            
            # Try direct DABS code search first
            search_url = f"{self.endpoints['dabs_locator']}/Search"
            
            # Search by DABS code
            async with self.session.get(search_url, params={
                'searchTerm': dabs_code,
                'searchType': 'code'
            }) as response:
                
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for product details
                    product_info = self.extract_dabs_product_info(soup, dabs_code)
                    
                    # Look for UPC patterns in HTML
                    upc_patterns = [
                        r'UPC[:\s]*(\d{12})',
                        r'barcode[:\s]*(\d{12})',
                        r'product[_\s]code[:\s]*(\d{12})',
                        r'(\d{12})',  # Generic 12-digit pattern
                    ]
                    
                    for pattern in upc_patterns:
                        matches = re.findall(pattern, html, re.IGNORECASE)
                        for match in matches:
                            if len(match) == 12 and match.isdigit():
                                # Validate UPC checksum
                                if VerifoneFormatter.validate_upc_checksum(match):
                                    logger.info(f"DABS Locator found valid UPC for {dabs_code}: {match}")
                                    return match, product_info
            
            # If code search fails, try name search
            await asyncio.sleep(1)  # Additional delay between searches
            
            async with self.session.get(search_url, params={
                'searchTerm': ' '.join(search_words),
                'searchType': 'product'
            }) as response:
                
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for matching product in results
                    product_rows = soup.find_all('tr', class_='product-row')  # Hypothetical class
                    
                    for row in product_rows:
                        row_text = row.get_text().upper()
                        if any(word.upper() in row_text for word in search_words[:2]):
                            # Found potential match, extract UPC
                            for pattern in upc_patterns:
                                matches = re.findall(pattern, str(row), re.IGNORECASE)
                                for match in matches:
                                    if len(match) == 12 and match.isdigit():
                                        if VerifoneFormatter.validate_upc_checksum(match):
                                            logger.info(f"DABS Locator found UPC via name search for {dabs_code}: {match}")
                                            return match, None
                
        except Exception as e:
            logger.error(f"Enhanced DABS Locator search error for {dabs_code}: {e}")
        
        return None, None
    
    def extract_dabs_product_info(self, soup: BeautifulSoup, dabs_code: str) -> Optional[Dict]:
        """Extract product information from DABS page"""
        try:
            product_info = {
                'dabs_code': dabs_code,
                'found_on_dabs': True
            }
            
            # Look for common product detail patterns
            detail_patterns = {
                'size': r'(\d+(?:\.\d+)?\s*(?:ml|l|oz))',
                'abv': r'(\d+(?:\.\d+)?%\s*(?:abv|alc))',
                'type': r'(wine|beer|spirit|vodka|whiskey|tequila|rum|gin)',
                'brand': r'brand[:\s]*([^\n\r]+)',
                'description': r'description[:\s]*([^\n\r]+)'
            }
            
            page_text = soup.get_text().lower()
            
            for key, pattern in detail_patterns.items():
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    product_info[key] = match.group(1).strip()
            
            return product_info if len(product_info) > 2 else None
            
        except Exception as e:
            logger.error(f"Error extracting DABS product info: {e}")
            return None
    
    async def search_specialized_alcohol_db(self, item_name: str, product_type: str) -> Optional[str]:
        """Search specialized alcohol databases based on product type"""
        try:
            # Determine product type from name
            name_lower = item_name.lower()
            
            if any(wine_term in name_lower for wine_term in ['pinot', 'chardonnay', 'cabernet', 'merlot', 'rosé', 'rose', 'brut']):
                return await self.search_wine_database(item_name)
            elif any(spirit_term in name_lower for spirit_term in ['tequila', 'vodka', 'whiskey', 'bourbon', 'rum', 'gin']):
                return await self.search_spirits_database(item_name)
            elif any(beer_term in name_lower for beer_term in ['beer', 'ale', 'lager', 'ipa', 'stout']):
                return await self.search_beer_database(item_name)
            else:
                # Try wine database as default for unknown types
                return await self.search_wine_database(item_name)
                
        except Exception as e:
            logger.error(f"Specialized alcohol DB search error: {e}")
            return None
    
    async def search_wine_database(self, item_name: str) -> Optional[str]:
        """Search wine-specific databases"""
        try:
            await self.rate_limit_wait('vivino')
            
            # Extract wine-specific search terms
            brand, varietal = self.extract_wine_info(item_name)
            
            # Search Vivino (free wine database)
            search_url = "https://www.vivino.com/search/wines"
            
            async with self.session.get(search_url, params={
                'q': f"{brand} {varietal}".strip()
            }) as response:
                
                if response.status == 200:
                    html = await response.text()
                    
                    # Look for UPC patterns in wine database results
                    upc_patterns = [
                        r'upc["\']:\s*["\'](\d{12})["\']',
                        r'barcode["\']:\s*["\'](\d{12})["\']',
                        r'(\d{12})'
                    ]
                    
                    for pattern in upc_patterns:
                        matches = re.findall(pattern, html, re.IGNORECASE)
                        for match in matches:
                            if len(match) == 12 and match.isdigit():
                                if VerifoneFormatter.validate_upc_checksum(match):
                                    logger.info(f"Wine database found UPC: {match}")
                                    return match
                
        except Exception as e:
            logger.error(f"Wine database search error: {e}")
        
        return None
    
    async def search_spirits_database(self, item_name: str) -> Optional[str]:
        """Search spirits-specific databases"""
        try:
            await self.rate_limit_wait('distiller')
            
            # Extract spirits-specific search terms
            brand, spirit_type = self.extract_spirits_info(item_name)
            
            # This would search spirits databases
            # For now, we'll use a generic approach
            logger.info(f"Searching spirits database for: {brand} {spirit_type}")
            
            # Placeholder for spirits database search
            # In production, you could integrate with distiller.com or similar
            
        except Exception as e:
            logger.error(f"Spirits database search error: {e}")
        
        return None
    
    async def search_beer_database(self, item_name: str) -> Optional[str]:
        """Search beer-specific databases"""
        try:
            await self.rate_limit_wait('untappd')
            
            # Extract beer-specific search terms
            brewery, beer_style = self.extract_beer_info(item_name)
            
            # This would search beer databases
            logger.info(f"Searching beer database for: {brewery} {beer_style}")
            
            # Placeholder for beer database search
            
        except Exception as e:
            logger.error(f"Beer database search error: {e}")
        
        return None
    
    def extract_wine_info(self, item_name: str) -> Tuple[str, str]:
        """Extract wine brand and varietal"""
        parts = item_name.upper().split()
        
        # Common wine varietals
        varietals = ['PINOT', 'CHARDONNAY', 'CABERNET', 'MERLOT', 'SAUVIGNON', 'RIESLING', 'SYRAH', 'SHIRAZ']
        
        brand_parts = []
        varietal_parts = []
        
        for part in parts:
            if any(varietal in part for varietal in varietals):
                varietal_parts.append(part)
            elif part not in ['750ML', 'ML', 'WINE', 'RED', 'WHITE']:
                brand_parts.append(part)
        
        brand = ' '.join(brand_parts[:2])  # First 2 words as brand
        varietal = ' '.join(varietal_parts[:2])  # First 2 varietal words
        
        return brand, varietal
    
    def extract_spirits_info(self, item_name: str) -> Tuple[str, str]:
        """Extract spirits brand and type"""
        parts = item_name.upper().split()
        
        spirit_types = ['TEQUILA', 'VODKA', 'WHISKEY', 'BOURBON', 'RUM', 'GIN', 'BRANDY']
        
        brand_parts = []
        spirit_type = ""
        
        for part in parts:
            if any(spirit in part for spirit in spirit_types):
                spirit_type = part
            elif part not in ['750ML', 'ML', 'BLANCO', 'REPOSADO', 'AÑEJO']:
                brand_parts.append(part)
        
        brand = ' '.join(brand_parts[:2])
        
        return brand, spirit_type
    
    def extract_beer_info(self, item_name: str) -> Tuple[str, str]:
        """Extract beer brewery and style"""
        parts = item_name.upper().split()
        
        beer_styles = ['IPA', 'ALE', 'LAGER', 'STOUT', 'PORTER', 'WHEAT', 'PILSNER']
        
        brewery_parts = []
        beer_style = ""
        
        for part in parts:
            if any(style in part for style in beer_styles):
                beer_style = part
            elif part not in ['BEER', '12OZ', 'OZ', 'CAN', 'BOTTLE']:
                brewery_parts.append(part)
        
        brewery = ' '.join(brewery_parts[:2])
        
        return brewery, beer_style
    
    async def lookup_single_upc_enhanced(self, item_name: str, dabs_code: str) -> EnhancedUPCResult:
        """Enhanced UPC lookup for a single item"""
        
        # Check cache first
        cached = self.get_cached_upc(dabs_code)
        if cached:
            return cached
        
        result = EnhancedUPCResult(item_name=item_name, dabs_code=dabs_code)
        
        try:
            # Try multiple sources with enhanced methods
            tasks = [
                self.search_dabs_locator_enhanced(item_name, dabs_code),
                self.search_openfoodfacts(item_name),
                self.search_specialized_alcohol_db(item_name, "auto-detect")
            ]
            
            # Wait for all searches with timeout
            search_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            valid_upcs = []
            
            # Handle DABS locator result (returns tuple)
            dabs_result = search_results[0]
            if isinstance(dabs_result, tuple) and dabs_result[0]:
                upc, product_info = dabs_result
                valid_upcs.append((upc, 'dabs_locator'))
                result.dabs_product_info = product_info
            
            # Handle other results
            for i, upc_result in enumerate(search_results[1:], 1):
                if isinstance(upc_result, str) and await self.verify_upc_format(upc_result):
                    source_names = ['openfoodfacts', 'specialized_alcohol_db']
                    valid_upcs.append((upc_result, source_names[i-1]))
            
            if valid_upcs:
                # Use the most common UPC if multiple found
                upc_counts = {}
                for upc, source in valid_upcs:
                    if upc not in upc_counts:
                        upc_counts[upc] = {'count': 0, 'sources': []}
                    upc_counts[upc]['count'] += 1
                    upc_counts[upc]['sources'].append(source)
                
                # Select best UPC (prioritize DABS official)
                best_upc = None
                for upc, data in upc_counts.items():
                    if 'dabs_locator' in data['sources']:
                        best_upc = upc
                        break
                
                if not best_upc:
                    best_upc = max(upc_counts.keys(), key=lambda x: upc_counts[x]['count'])
                
                result.upc_code = best_upc
                result.sources = upc_counts[best_upc]['sources']
                result.confidence = min(0.95, 0.4 * len(result.sources))
                result.verified = len(result.sources) >= 2 or 'dabs_locator' in result.sources
                
                # Auto-format for Verifone
                result.verifone_upc = VerifoneFormatter.format_for_verifone(best_upc)
                
                logger.info(f"Enhanced UPC found for {dabs_code}: {best_upc} → {result.verifone_upc} (confidence: {result.confidence:.2f})")
            
            else:
                result.error = "No valid UPC found in any enhanced source"
                logger.warning(f"No enhanced UPC found for {dabs_code}: {item_name}")
        
        except Exception as e:
            result.error = f"Enhanced lookup error: {str(e)}"
            logger.error(f"Enhanced UPC lookup error for {dabs_code}: {e}")
        
        # Cache result
        self.cache_upc(result)
        
        return result
    
    async def search_openfoodfacts(self, item_name: str) -> Optional[str]:
        """Enhanced OpenFoodFacts search"""
        try:
            await self.rate_limit_wait('openfoodfacts')
            
            # Clean and prepare search term
            search_term = re.sub(r'[^\w\s]', ' ', item_name.lower())
            search_words = search_term.split()[:3]  # Use first 3 words
            
            search_url = "https://world.openfoodfacts.org/cgi/search.pl"
            
            async with self.session.get(search_url, params={
                'search_terms': ' '.join(search_words),
                'search_simple': 1,
                'action': 'process',
                'json': 1
            }) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if 'products' in data and data['products']:
                        for product in data['products'][:5]:  # Check first 5 results
                            if 'code' in product:
                                upc = product['code']
                                if len(upc) == 13 and upc.isdigit():
                                    # Convert EAN-13 to UPC-12 if needed
                                    if upc.startswith('0'):
                                        upc = upc[1:]
                                
                                if len(upc) == 12 and upc.isdigit():
                                    if VerifoneFormatter.validate_upc_checksum(upc):
                                        logger.info(f"Enhanced OpenFoodFacts found valid UPC: {upc}")
                                        return upc
                
        except Exception as e:
            logger.error(f"Enhanced OpenFoodFacts search error: {e}")
        
        return None
    
    async def verify_upc_format(self, upc: str) -> bool:
        """Enhanced UPC format verification"""
        return VerifoneFormatter.validate_upc_checksum(upc)
    
    async def lookup_batch_upcs_enhanced(self, items: List[Tuple[str, str]]) -> List[EnhancedUPCResult]:
        """Enhanced batch UPC lookup"""
        logger.info(f"Starting enhanced batch UPC lookup for {len(items)} items")
        
        # Process items with controlled concurrency
        semaphore = asyncio.Semaphore(2)  # More conservative for enhanced version
        
        async def lookup_with_semaphore(item_name: str, dabs_code: str):
            async with semaphore:
                return await self.lookup_single_upc_enhanced(item_name, dabs_code)
        
        tasks = [lookup_with_semaphore(name, code) for name, code in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, EnhancedUPCResult):
                valid_results.append(result)
            else:
                logger.error(f"Enhanced batch lookup error: {result}")
        
        logger.info(f"Completed enhanced batch lookup: {len(valid_results)} results")
        return valid_results

# Test function
async def test_enhanced_upc_verification():
    """Test the enhanced UPC verification system"""
    
    # Test items from user's DABS order
    test_items = [
        ("ARETTE CLASICA BLANCO TEQUILA", "039593"),
        ("WILLAMETTE VLY PINOT NOIR WL", "087123"),
        ("KING ESTATE PINOT GRIS SIGNATURE", "523110"),
        ("SEGURA VIUDAS BRUT 750ml", "580790"),
        ("POE ROSÉ'23 750ml", "908418"),
    ]
    
    async with EnhancedUPCVerifier() as verifier:
        results = await verifier.lookup_batch_upcs_enhanced(test_items)
        
        print("\n🎯 Enhanced UPC Verification Results:")
        print("=" * 70)
        
        for result in results:
            status = "✅ VERIFIED" if result.verified else "⚠️  FOUND" if result.upc_code else "❌ NOT FOUND"
            
            print(f"\n{status}")
            print(f"Item: {result.item_name}")
            print(f"DABS Code: {result.dabs_code}")
            print(f"UPC-12: {result.upc_code or 'Not found'}")
            print(f"Verifone UPC-11: {result.verifone_upc or 'Not available'}")
            print(f"Confidence: {result.confidence:.2f}")
            print(f"Sources: {', '.join(result.sources) if result.sources else 'None'}")
            if result.dabs_product_info:
                print(f"DABS Info: {result.dabs_product_info}")
            if result.error:
                print(f"Error: {result.error}")
        
        # Summary
        verified_count = sum(1 for r in results if r.verified)
        found_count = sum(1 for r in results if r.upc_code)
        verifone_count = sum(1 for r in results if r.verifone_upc)
        
        print(f"\n📊 Enhanced Summary:")
        print(f"Total items: {len(results)}")
        print(f"UPCs found: {found_count}")
        print(f"Verified (2+ sources or DABS official): {verified_count}")
        print(f"Verifone formatted: {verifone_count}")
        print(f"Success rate: {(found_count/len(results)*100):.1f}%")
        print(f"Verification rate: {(verified_count/len(results)*100):.1f}%")

if __name__ == "__main__":
    asyncio.run(test_enhanced_upc_verification())
