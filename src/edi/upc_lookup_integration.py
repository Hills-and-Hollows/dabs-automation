#!/usr/bin/env python3
"""
UPC Lookup Integration for DABS EDI System
Provides automated UPC barcode lookup for SSCS integration

Business Context:
- SSCS requires UPC barcodes for POS scanning (Verifone registers)
- UPC format: 12-digit barcode, may need last digit dropped for Verifone
- Separate from Vendor Item Code (DABS SKU)
- Critical for automated inventory management
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sqlite3
from pathlib import Path
import json
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UPCLookupResult:
    """UPC lookup result structure"""
    dabs_sku: str
    product_name: str
    upc_12_digit: Optional[str] = None
    upc_11_digit: Optional[str] = None  # For Verifone compatibility
    brand: Optional[str] = None
    size: Optional[str] = None
    category: Optional[str] = None
    confidence_score: float = 0.0
    lookup_source: str = "unknown"

class UPCLookupManager:
    """Manages UPC lookup for DABS items"""
    
    def __init__(self, db_path: str = "data/upc_database.sqlite"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
    def _init_database(self):
        """Initialize UPC lookup database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS upc_lookup (
                    dabs_sku TEXT PRIMARY KEY,
                    product_name TEXT NOT NULL,
                    upc_12_digit TEXT,
                    upc_11_digit TEXT,
                    brand TEXT,
                    size TEXT,
                    category TEXT,
                    confidence_score REAL DEFAULT 0.0,
                    lookup_source TEXT DEFAULT 'manual',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_upc_12 ON upc_lookup(upc_12_digit)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_product_name ON upc_lookup(product_name)
            """)
            
        logger.info(f"UPC database initialized: {self.db_path}")
    
    async def lookup_upc(self, dabs_sku: str, product_name: str) -> UPCLookupResult:
        """
        Lookup UPC for DABS item using multiple sources
        
        Args:
            dabs_sku: DABS SKU/CSC code
            product_name: Product description
            
        Returns:
            UPCLookupResult with UPC data
        """
        logger.info(f"Looking up UPC for SKU: {dabs_sku}, Product: {product_name}")
        
        # 1. Check local database first
        result = await self._lookup_local_database(dabs_sku, product_name)
        if result.upc_12_digit:
            logger.info(f"Found UPC in local database: {result.upc_12_digit}")
            return result
        
        # 2. Try SSCS integration lookup (if available)
        result = await self._lookup_sscs_integration(dabs_sku, product_name)
        if result.upc_12_digit:
            logger.info(f"Found UPC via SSCS integration: {result.upc_12_digit}")
            await self._save_to_database(result)
            return result
        
        # 3. Try external UPC lookup services
        result = await self._lookup_external_services(dabs_sku, product_name)
        if result.upc_12_digit:
            logger.info(f"Found UPC via external service: {result.upc_12_digit}")
            await self._save_to_database(result)
            return result
        
        # 4. Return empty result for manual lookup
        logger.warning(f"No UPC found for SKU: {dabs_sku}")
        return UPCLookupResult(
            dabs_sku=dabs_sku,
            product_name=product_name,
            lookup_source="not_found"
        )
    
    async def _lookup_local_database(self, dabs_sku: str, product_name: str) -> UPCLookupResult:
        """Lookup UPC in local database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT dabs_sku, product_name, upc_12_digit, upc_11_digit, 
                       brand, size, category, confidence_score, lookup_source
                FROM upc_lookup 
                WHERE dabs_sku = ? OR product_name LIKE ?
                ORDER BY confidence_score DESC
                LIMIT 1
            """, (dabs_sku, f"%{product_name}%"))
            
            row = cursor.fetchone()
            if row:
                return UPCLookupResult(
                    dabs_sku=row[0],
                    product_name=row[1],
                    upc_12_digit=row[2],
                    upc_11_digit=row[3],
                    brand=row[4],
                    size=row[5],
                    category=row[6],
                    confidence_score=row[7],
                    lookup_source=row[8]
                )
        
        return UPCLookupResult(dabs_sku=dabs_sku, product_name=product_name)
    
    async def _lookup_sscs_integration(self, dabs_sku: str, product_name: str) -> UPCLookupResult:
        """Lookup UPC via SSCS integration"""
        # TODO: Integrate with SSCS CDB system for UPC lookup
        # This would query existing SSCS inventory for matching products
        logger.info("SSCS integration lookup not yet implemented")
        return UPCLookupResult(dabs_sku=dabs_sku, product_name=product_name)
    
    async def _lookup_external_services(self, dabs_sku: str, product_name: str) -> UPCLookupResult:
        """Lookup UPC via external services"""
        # TODO: Integrate with UPC lookup APIs (UPCDatabase.org, etc.)
        logger.info("External UPC lookup services not yet implemented")
        return UPCLookupResult(dabs_sku=dabs_sku, product_name=product_name)
    
    async def _save_to_database(self, result: UPCLookupResult):
        """Save UPC lookup result to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO upc_lookup 
                (dabs_sku, product_name, upc_12_digit, upc_11_digit, brand, size, 
                 category, confidence_score, lookup_source, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                result.dabs_sku,
                result.product_name,
                result.upc_12_digit,
                result.upc_11_digit,
                result.brand,
                result.size,
                result.category,
                result.confidence_score,
                result.lookup_source
            ))
        
        logger.info(f"Saved UPC lookup result for SKU: {result.dabs_sku}")
    
    def format_upc_for_verifone(self, upc_12_digit: str) -> str:
        """
        Format UPC for Verifone register compatibility
        
        Based on user feedback: "Verifone registers are specific in the barcode format.
        So if you send me a 12 digit barcode like for the Buffalo Trace one (080244000923) 
        the last digit (3) likely needs to be dropped for it to work."
        
        Args:
            upc_12_digit: 12-digit UPC barcode
            
        Returns:
            11-digit UPC for Verifone compatibility
        """
        if not upc_12_digit or len(upc_12_digit) != 12:
            return upc_12_digit
        
        # Drop the last digit for Verifone compatibility
        upc_11_digit = upc_12_digit[:-1]
        logger.info(f"Formatted UPC for Verifone: {upc_12_digit} → {upc_11_digit}")
        return upc_11_digit
    
    async def bulk_lookup_upcs(self, items: List[Tuple[str, str]]) -> Dict[str, UPCLookupResult]:
        """
        Bulk lookup UPCs for multiple items
        
        Args:
            items: List of (dabs_sku, product_name) tuples
            
        Returns:
            Dictionary mapping DABS SKU to UPCLookupResult
        """
        logger.info(f"Starting bulk UPC lookup for {len(items)} items")
        
        results = {}
        
        # Process in batches to avoid overwhelming external services
        batch_size = 10
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = [
                self.lookup_upc(sku, name) for sku, name in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks)
            
            for (sku, _), result in zip(batch, batch_results):
                results[sku] = result
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        logger.info(f"Completed bulk UPC lookup: {len(results)} results")
        return results
    
    def add_manual_upc(self, dabs_sku: str, product_name: str, upc_12_digit: str, 
                      brand: str = None, size: str = None, category: str = None):
        """
        Manually add UPC mapping to database
        
        Args:
            dabs_sku: DABS SKU/CSC code
            product_name: Product description
            upc_12_digit: 12-digit UPC barcode
            brand: Product brand (optional)
            size: Product size (optional)
            category: Product category (optional)
        """
        upc_11_digit = self.format_upc_for_verifone(upc_12_digit)
        
        result = UPCLookupResult(
            dabs_sku=dabs_sku,
            product_name=product_name,
            upc_12_digit=upc_12_digit,
            upc_11_digit=upc_11_digit,
            brand=brand,
            size=size,
            category=category,
            confidence_score=1.0,
            lookup_source="manual"
        )
        
        # Save synchronously for manual additions
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO upc_lookup 
                (dabs_sku, product_name, upc_12_digit, upc_11_digit, brand, size, 
                 category, confidence_score, lookup_source, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                result.dabs_sku,
                result.product_name,
                result.upc_12_digit,
                result.upc_11_digit,
                result.brand,
                result.size,
                result.category,
                result.confidence_score,
                result.lookup_source
            ))
        
        logger.info(f"Added manual UPC mapping: {dabs_sku} → {upc_12_digit}")

# Example usage and testing
if __name__ == "__main__":
    async def test_upc_lookup():
        manager = UPCLookupManager()
        
        # Add some sample UPC mappings
        manager.add_manual_upc(
            dabs_sku="080244",
            product_name="Buffalo Trace Bourbon 750ml",
            upc_12_digit="080244000923",
            brand="Buffalo Trace",
            size="750ml",
            category="SPIRITS"
        )
        
        # Test lookup
        result = await manager.lookup_upc("080244", "Buffalo Trace Bourbon 750ml")
        print(f"UPC Lookup Result:")
        print(f"  12-digit UPC: {result.upc_12_digit}")
        print(f"  11-digit UPC (Verifone): {result.upc_11_digit}")
        print(f"  Confidence: {result.confidence_score}")
        print(f"  Source: {result.lookup_source}")
    
    asyncio.run(test_upc_lookup())
