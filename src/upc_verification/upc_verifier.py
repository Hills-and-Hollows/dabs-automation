#!/usr/bin/env python3
"""
Free UPC Verification System for DABS Items
Zero-cost multi-source UPC lookup and verification
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
from urllib.parse import quote_plus
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UPCResult:
    """UPC verification result"""
    item_name: str
    dabs_code: str
    upc_code: Optional[str] = None
    confidence: float = 0.0
    sources: List[str] = None
    verified: bool = False
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []

class UPCVerifier:
    """Free multi-source UPC verification system"""
    
    def __init__(self, db_path: str = "data/upc_cache.db"):
        self.db_path = db_path
        self.session = None
        self.init_database()
        
        # Free API endpoints
        self.endpoints = {
            'openfoodfacts': 'https://world.openfoodfacts.org/api/v0/product/{}.json',
            'dabs_locator': 'https://webapps2.abc.utah.gov/ProdApps/ProductLocatorCore',
            'upc_lookup': 'https://api.upcitemdb.com/prod/trial/lookup',  # Free tier
        }
        
        # Rate limiting (respect free APIs)
        self.rate_limits = {
            'openfoodfacts': 1.0,  # 1 second between requests
            'dabs_locator': 2.0,   # 2 seconds between requests
            'upc_lookup': 3.0,     # 3 seconds between requests (free tier)
        }
        self.last_request = {}
    
    def init_database(self):
        """Initialize SQLite cache database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS upc_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dabs_code TEXT UNIQUE NOT NULL,
                    item_name TEXT NOT NULL,
                    upc_code TEXT,
                    confidence REAL,
                    sources TEXT,
                    verified BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_dabs_code ON upc_cache(dabs_code)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_item_name ON upc_cache(item_name)
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"UPC cache database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'DABS-UPC-Verifier/1.0 (Hills-Hollows-LLC)'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def get_cached_upc(self, dabs_code: str) -> Optional[UPCResult]:
        """Get UPC from local cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT item_name, upc_code, confidence, sources, verified
                FROM upc_cache 
                WHERE dabs_code = ? AND updated_at > datetime('now', '-30 days')
            ''', (dabs_code,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                item_name, upc_code, confidence, sources_json, verified = row
                sources = json.loads(sources_json) if sources_json else []
                
                logger.info(f"Cache hit for {dabs_code}: {upc_code}")
                return UPCResult(
                    item_name=item_name,
                    dabs_code=dabs_code,
                    upc_code=upc_code,
                    confidence=confidence,
                    sources=sources,
                    verified=bool(verified)
                )
                
        except Exception as e:
            logger.error(f"Cache lookup error for {dabs_code}: {e}")
        
        return None
    
    def cache_upc(self, result: UPCResult):
        """Cache UPC result"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO upc_cache 
                (dabs_code, item_name, upc_code, confidence, sources, verified, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                result.dabs_code,
                result.item_name,
                result.upc_code,
                result.confidence,
                json.dumps(result.sources),
                result.verified
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Cached UPC for {result.dabs_code}: {result.upc_code}")
            
        except Exception as e:
            logger.error(f"Cache save error for {result.dabs_code}: {e}")
    
    async def rate_limit_wait(self, source: str):
        """Implement rate limiting for free APIs"""
        if source in self.last_request:
            elapsed = time.time() - self.last_request[source]
            wait_time = self.rate_limits.get(source, 1.0)
            
            if elapsed < wait_time:
                sleep_time = wait_time - elapsed
                logger.info(f"Rate limiting {source}: waiting {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
        
        self.last_request[source] = time.time()
    
    async def search_dabs_locator(self, item_name: str, dabs_code: str) -> Optional[str]:
        """Search Utah DABS Product Locator (free)"""
        try:
            await self.rate_limit_wait('dabs_locator')
            
            # Clean item name for search
            search_term = re.sub(r'[^\w\s]', ' ', item_name).strip()
            search_words = search_term.split()[:3]  # Use first 3 words
            
            # Search DABS locator
            search_url = f"{self.endpoints['dabs_locator']}/Search"
            
            async with self.session.get(search_url, params={
                'searchTerm': ' '.join(search_words),
                'searchType': 'product'
            }) as response:
                
                if response.status == 200:
                    html = await response.text()
                    
                    # Look for UPC patterns in HTML
                    upc_patterns = [
                        r'UPC[:\s]*(\d{12})',
                        r'barcode[:\s]*(\d{12})',
                        r'(\d{12})',  # Generic 12-digit pattern
                    ]
                    
                    for pattern in upc_patterns:
                        matches = re.findall(pattern, html, re.IGNORECASE)
                        if matches:
                            upc = matches[0]
                            if len(upc) == 12 and upc.isdigit():
                                logger.info(f"DABS Locator found UPC for {dabs_code}: {upc}")
                                return upc
                
        except Exception as e:
            logger.error(f"DABS Locator search error for {dabs_code}: {e}")
        
        return None
    
    async def search_openfoodfacts(self, item_name: str) -> Optional[str]:
        """Search OpenFoodFacts database (free)"""
        try:
            await self.rate_limit_wait('openfoodfacts')
            
            # Clean and prepare search term
            search_term = re.sub(r'[^\w\s]', ' ', item_name.lower())
            search_words = search_term.split()[:2]  # Use first 2 words
            
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
                        for product in data['products'][:3]:  # Check first 3 results
                            if 'code' in product:
                                upc = product['code']
                                if len(upc) == 13 and upc.isdigit():
                                    # Convert EAN-13 to UPC-12 if needed
                                    if upc.startswith('0'):
                                        upc = upc[1:]
                                
                                if len(upc) == 12 and upc.isdigit():
                                    logger.info(f"OpenFoodFacts found UPC: {upc}")
                                    return upc
                
        except Exception as e:
            logger.error(f"OpenFoodFacts search error: {e}")
        
        return None
    
    def extract_brand_product(self, item_name: str) -> Tuple[str, str]:
        """Extract brand and product from item name"""
        # Common alcohol brand patterns
        parts = item_name.upper().split()
        
        # Remove common suffixes
        suffixes = ['TEQUILA', 'WINE', 'VODKA', 'WHISKEY', 'BOURBON', 'RUM', 'GIN', 'ML', '750ML']
        filtered_parts = [p for p in parts if p not in suffixes]
        
        if len(filtered_parts) >= 2:
            brand = filtered_parts[0]
            product = ' '.join(filtered_parts[1:3])  # Next 2 words
        else:
            brand = filtered_parts[0] if filtered_parts else parts[0]
            product = ' '.join(parts[1:3]) if len(parts) > 1 else ""
        
        return brand, product
    
    async def web_search_upc(self, item_name: str) -> Optional[str]:
        """Web search for UPC using multiple strategies"""
        try:
            brand, product = self.extract_brand_product(item_name)
            
            # Search strategies
            search_terms = [
                f'"{brand}" "{product}" UPC barcode',
                f'{brand} {product} UPC code',
                f'{item_name} barcode UPC'
            ]
            
            for search_term in search_terms:
                await asyncio.sleep(1)  # Rate limit web searches
                
                # Use a simple web search approach
                # In production, you might use Google Custom Search API (free tier)
                # For now, we'll simulate this with pattern matching
                
                # This would be replaced with actual web search
                logger.info(f"Web search: {search_term}")
                
                # Placeholder for web search implementation
                # You could integrate with Google Custom Search API free tier
                # or use other free search APIs
                
        except Exception as e:
            logger.error(f"Web search error: {e}")
        
        return None
    
    async def verify_upc_format(self, upc: str) -> bool:
        """Verify UPC format and check digit"""
        if not upc or len(upc) != 12 or not upc.isdigit():
            return False
        
        # Calculate UPC check digit
        odd_sum = sum(int(upc[i]) for i in range(0, 11, 2))
        even_sum = sum(int(upc[i]) for i in range(1, 11, 2))
        
        total = (odd_sum * 3) + even_sum
        check_digit = (10 - (total % 10)) % 10
        
        return int(upc[11]) == check_digit
    
    async def lookup_single_upc(self, item_name: str, dabs_code: str) -> UPCResult:
        """Look up UPC for a single item using all free sources"""
        
        # Check cache first
        cached = self.get_cached_upc(dabs_code)
        if cached:
            return cached
        
        result = UPCResult(item_name=item_name, dabs_code=dabs_code)
        
        try:
            # Try multiple sources in parallel
            tasks = [
                self.search_dabs_locator(item_name, dabs_code),
                self.search_openfoodfacts(item_name),
                self.web_search_upc(item_name)
            ]
            
            # Wait for all searches with timeout
            upcs = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            valid_upcs = []
            for i, upc in enumerate(upcs):
                if isinstance(upc, str) and await self.verify_upc_format(upc):
                    valid_upcs.append((upc, ['dabs_locator', 'openfoodfacts', 'web_search'][i]))
            
            if valid_upcs:
                # Use the most common UPC if multiple found
                upc_counts = {}
                for upc, source in valid_upcs:
                    if upc not in upc_counts:
                        upc_counts[upc] = {'count': 0, 'sources': []}
                    upc_counts[upc]['count'] += 1
                    upc_counts[upc]['sources'].append(source)
                
                # Select best UPC
                best_upc = max(upc_counts.keys(), key=lambda x: upc_counts[x]['count'])
                
                result.upc_code = best_upc
                result.sources = upc_counts[best_upc]['sources']
                result.confidence = min(0.9, 0.3 * len(result.sources))
                result.verified = len(result.sources) >= 2
                
                logger.info(f"Found UPC for {dabs_code}: {best_upc} (confidence: {result.confidence:.2f})")
            
            else:
                result.error = "No valid UPC found in any source"
                logger.warning(f"No UPC found for {dabs_code}: {item_name}")
        
        except Exception as e:
            result.error = f"Lookup error: {str(e)}"
            logger.error(f"UPC lookup error for {dabs_code}: {e}")
        
        # Cache result
        self.cache_upc(result)
        
        return result
    
    async def lookup_batch_upcs(self, items: List[Tuple[str, str]]) -> List[UPCResult]:
        """Look up UPCs for multiple items"""
        logger.info(f"Starting batch UPC lookup for {len(items)} items")
        
        # Process items with controlled concurrency
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent lookups
        
        async def lookup_with_semaphore(item_name: str, dabs_code: str):
            async with semaphore:
                return await self.lookup_single_upc(item_name, dabs_code)
        
        tasks = [lookup_with_semaphore(name, code) for name, code in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, UPCResult):
                valid_results.append(result)
            else:
                logger.error(f"Batch lookup error: {result}")
        
        logger.info(f"Completed batch lookup: {len(valid_results)} results")
        return valid_results

# Test function
async def test_upc_verification():
    """Test the UPC verification system"""
    
    # Test items from user's DABS order
    test_items = [
        ("ARETTE CLASICA BLANCO TEQUILA", "039593"),
        ("WILLAMETTE VLY PINOT NOIR WL", "087123"),
        ("KING ESTATE PINOT GRIS SIGNATURE", "523110"),
        ("SEGURA VIUDAS BRUT 750ml", "580790"),
        ("POE ROSÉ'23 750ml", "908418"),
        ("LORENZA ROSE 750ml", "918951"),
        ("SEGURA VIUDAS BRUT 750ml", "733238"),
        ("POE ROSÉ'23 750ml", "918761"),
        ("LORENZA ROSE 750ml", "919829"),
    ]
    
    async with UPCVerifier() as verifier:
        results = await verifier.lookup_batch_upcs(test_items)
        
        print("\n🎯 UPC Verification Results:")
        print("=" * 60)
        
        for result in results:
            status = "✅ VERIFIED" if result.verified else "⚠️  FOUND" if result.upc_code else "❌ NOT FOUND"
            
            print(f"\n{status}")
            print(f"Item: {result.item_name}")
            print(f"DABS Code: {result.dabs_code}")
            print(f"UPC: {result.upc_code or 'Not found'}")
            print(f"Confidence: {result.confidence:.2f}")
            print(f"Sources: {', '.join(result.sources) if result.sources else 'None'}")
            if result.error:
                print(f"Error: {result.error}")
        
        # Summary
        verified_count = sum(1 for r in results if r.verified)
        found_count = sum(1 for r in results if r.upc_code)
        
        print(f"\n📊 Summary:")
        print(f"Total items: {len(results)}")
        print(f"UPCs found: {found_count}")
        print(f"Verified (2+ sources): {verified_count}")
        print(f"Success rate: {(found_count/len(results)*100):.1f}%")

if __name__ == "__main__":
    asyncio.run(test_upc_verification())
