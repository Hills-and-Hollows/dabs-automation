#!/usr/bin/env python3
"""
Vendor Item Number Integration System
Maps between DABS product codes and SSCS vendor numbers

This system ensures accurate EDI processing by maintaining comprehensive
mapping between DABS product identifiers and SSCS vendor item numbers.

Business Context:
- DABS uses internal product codes (PLU numbers)
- SSCS requires vendor-specific item numbers for import
- Mapping errors cause EDI delivery failures
- Utah Package Agency compliance requires accurate product identification
"""

import logging
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import re
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VendorMapping:
    """Vendor item mapping record"""
    dabs_plu: str
    dabs_name: str
    vendor_item_code: str
    vendor_name: str
    upc: Optional[str] = None
    category: Optional[str] = None
    size: Optional[str] = None
    confidence: float = 1.0
    last_verified: Optional[str] = None
    verification_source: Optional[str] = None
    notes: Optional[str] = None

@dataclass
class MappingResult:
    """Result of vendor mapping lookup"""
    success: bool
    dabs_plu: str
    vendor_item_code: Optional[str] = None
    confidence: float = 0.0
    mapping_source: Optional[str] = None
    suggestions: List[VendorMapping] = None
    error_message: Optional[str] = None

class VendorMappingSystem:
    """
    Vendor item number integration system
    
    Provides:
    1. Comprehensive mapping database between DABS and SSCS
    2. Automatic vendor number lookup during processing
    3. Fuzzy matching for similar items
    4. Manual resolution workflow for unmapped items
    """
    
    def __init__(self, db_path: str = "data/vendor_mappings.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.mapping_cache = {}
        self._init_database()
        self._load_default_mappings()
        
    def _init_database(self):
        """Initialize vendor mapping database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS vendor_mappings (
                    dabs_plu TEXT PRIMARY KEY,
                    dabs_name TEXT NOT NULL,
                    vendor_item_code TEXT NOT NULL,
                    vendor_name TEXT NOT NULL,
                    upc TEXT,
                    category TEXT,
                    size TEXT,
                    confidence REAL DEFAULT 1.0,
                    last_verified TEXT,
                    verification_source TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS mapping_attempts (
                    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dabs_plu TEXT NOT NULL,
                    dabs_name TEXT,
                    attempted_mapping TEXT,
                    success BOOLEAN,
                    confidence REAL,
                    timestamp TEXT,
                    notes TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS manual_resolutions (
                    resolution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dabs_plu TEXT NOT NULL,
                    dabs_name TEXT,
                    resolved_vendor_code TEXT,
                    resolution_method TEXT,
                    resolved_by TEXT,
                    resolution_notes TEXT,
                    timestamp TEXT
                )
            ''')
            
            # Create indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_vendor_code ON vendor_mappings(vendor_item_code)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_upc ON vendor_mappings(upc)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_category ON vendor_mappings(category)')
            
            conn.commit()
    
    def _load_default_mappings(self):
        """Load default vendor mappings for common items"""
        default_mappings = [
            # Example mappings based on Order 233813 items
            VendorMapping(
                dabs_plu="917817",
                dabs_name="RED ROCK ELEPHINO IPA 500ml",
                vendor_item_code="RR-ELEPHINO-500",
                vendor_name="Red Rock Brewing",
                category="Beer",
                size="500ml",
                confidence=0.9,
                verification_source="manual_entry",
                notes="Red Rock brewery product"
            ),
            VendorMapping(
                dabs_plu="039271",
                dabs_name="SUGAR HOUSE VODKA 1000ml",
                vendor_item_code="SH-VODKA-1000",
                vendor_name="Sugar House Distillery",
                category="Spirits",
                size="1000ml",
                confidence=0.9,
                verification_source="manual_entry",
                notes="Local Utah distillery"
            ),
            VendorMapping(
                dabs_plu="419961",
                dabs_name="19 CRIMES CABERNET SAUVIGNON 750ml",
                vendor_item_code="19C-CAB-750",
                vendor_name="19 Crimes",
                category="Wine",
                size="750ml",
                confidence=0.9,
                verification_source="manual_entry",
                notes="Treasury Wine Estates brand"
            ),
            VendorMapping(
                dabs_plu="581015",
                dabs_name="BOTA BOX PINOT GRIGIO 3000ml",
                vendor_item_code="BOTA-PG-3L",
                vendor_name="Bota Box",
                category="Wine",
                size="3000ml",
                confidence=0.9,
                verification_source="manual_entry",
                notes="Box wine format"
            ),
            VendorMapping(
                dabs_plu="068838",
                dabs_name="ST GERMAIN ELDERFLOWER LIQUEUR 750ml",
                vendor_item_code="STG-ELDER-750",
                vendor_name="St-Germain",
                category="Liqueur",
                size="750ml",
                confidence=0.9,
                verification_source="manual_entry",
                notes="Premium elderflower liqueur"
            )
        ]
        
        # Insert default mappings if they don't exist
        for mapping in default_mappings:
            self.add_mapping(mapping, update_if_exists=False)
    
    def add_mapping(self, mapping: VendorMapping, update_if_exists: bool = True) -> bool:
        """Add or update vendor mapping"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if update_if_exists:
                    conn.execute('''
                        INSERT OR REPLACE INTO vendor_mappings 
                        (dabs_plu, dabs_name, vendor_item_code, vendor_name, upc, category, 
                         size, confidence, last_verified, verification_source, notes, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        mapping.dabs_plu, mapping.dabs_name, mapping.vendor_item_code,
                        mapping.vendor_name, mapping.upc, mapping.category, mapping.size,
                        mapping.confidence, mapping.last_verified, mapping.verification_source,
                        mapping.notes, datetime.now().isoformat()
                    ))
                else:
                    conn.execute('''
                        INSERT OR IGNORE INTO vendor_mappings 
                        (dabs_plu, dabs_name, vendor_item_code, vendor_name, upc, category, 
                         size, confidence, last_verified, verification_source, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        mapping.dabs_plu, mapping.dabs_name, mapping.vendor_item_code,
                        mapping.vendor_name, mapping.upc, mapping.category, mapping.size,
                        mapping.confidence, mapping.last_verified, mapping.verification_source,
                        mapping.notes
                    ))
                
                conn.commit()
                
                # Update cache
                self.mapping_cache[mapping.dabs_plu] = mapping
                
                logger.info(f"✅ Mapping added: {mapping.dabs_plu} → {mapping.vendor_item_code}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to add mapping for {mapping.dabs_plu}: {e}")
            return False
    
    def lookup_vendor_code(self, dabs_plu: str, dabs_name: str = None) -> MappingResult:
        """
        Lookup vendor item code for DABS PLU
        
        Args:
            dabs_plu: DABS product lookup number
            dabs_name: Optional product name for fuzzy matching
            
        Returns:
            MappingResult with vendor code or suggestions
        """
        # Check cache first
        if dabs_plu in self.mapping_cache:
            mapping = self.mapping_cache[dabs_plu]
            return MappingResult(
                success=True,
                dabs_plu=dabs_plu,
                vendor_item_code=mapping.vendor_item_code,
                confidence=mapping.confidence,
                mapping_source="cache"
            )
        
        # Database lookup
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT * FROM vendor_mappings WHERE dabs_plu = ?
                ''', (dabs_plu,))
                
                row = cursor.fetchone()
                
                if row:
                    mapping = self._row_to_mapping(row)
                    self.mapping_cache[dabs_plu] = mapping
                    
                    return MappingResult(
                        success=True,
                        dabs_plu=dabs_plu,
                        vendor_item_code=mapping.vendor_item_code,
                        confidence=mapping.confidence,
                        mapping_source="database"
                    )
                
                # No exact match found - try fuzzy matching
                if dabs_name:
                    suggestions = self._fuzzy_match_by_name(dabs_name)
                    if suggestions:
                        return MappingResult(
                            success=False,
                            dabs_plu=dabs_plu,
                            confidence=0.0,
                            mapping_source="fuzzy_match",
                            suggestions=suggestions,
                            error_message=f"No exact match found for PLU {dabs_plu}, but found {len(suggestions)} similar items"
                        )
                
                # No match found
                self._log_mapping_attempt(dabs_plu, dabs_name, None, False, 0.0, "No mapping found")
                
                return MappingResult(
                    success=False,
                    dabs_plu=dabs_plu,
                    confidence=0.0,
                    error_message=f"No vendor mapping found for PLU {dabs_plu}"
                )
                
        except Exception as e:
            logger.error(f"❌ Mapping lookup error for {dabs_plu}: {e}")
            return MappingResult(
                success=False,
                dabs_plu=dabs_plu,
                error_message=f"Database error: {e}"
            )
    
    def _fuzzy_match_by_name(self, dabs_name: str, limit: int = 5) -> List[VendorMapping]:
        """Find similar items by name fuzzy matching"""
        suggestions = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT * FROM vendor_mappings
                ''')
                
                rows = cursor.fetchall()
                
                # Simple fuzzy matching based on common words
                name_words = set(dabs_name.upper().split())
                
                for row in rows:
                    mapping = self._row_to_mapping(row)
                    mapping_words = set(mapping.dabs_name.upper().split())
                    
                    # Calculate word overlap
                    common_words = name_words & mapping_words
                    if common_words:
                        similarity = len(common_words) / max(len(name_words), len(mapping_words))
                        
                        if similarity >= 0.3:  # 30% word overlap threshold
                            mapping.confidence = similarity
                            suggestions.append(mapping)
                
                # Sort by confidence and limit results
                suggestions.sort(key=lambda x: x.confidence, reverse=True)
                return suggestions[:limit]
                
        except Exception as e:
            logger.error(f"❌ Fuzzy matching error: {e}")
            return []
    
    def _row_to_mapping(self, row) -> VendorMapping:
        """Convert database row to VendorMapping object"""
        return VendorMapping(
            dabs_plu=row[0],
            dabs_name=row[1],
            vendor_item_code=row[2],
            vendor_name=row[3],
            upc=row[4],
            category=row[5],
            size=row[6],
            confidence=row[7] or 1.0,
            last_verified=row[8],
            verification_source=row[9],
            notes=row[10]
        )
    
    def _log_mapping_attempt(self, dabs_plu: str, dabs_name: str, attempted_mapping: str, 
                           success: bool, confidence: float, notes: str):
        """Log mapping attempt for analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO mapping_attempts 
                    (dabs_plu, dabs_name, attempted_mapping, success, confidence, timestamp, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    dabs_plu, dabs_name, attempted_mapping, success, confidence,
                    datetime.now().isoformat(), notes
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Failed to log mapping attempt: {e}")
    
    def batch_lookup(self, items: List[Dict[str, Any]]) -> List[MappingResult]:
        """Batch lookup vendor codes for multiple items"""
        results = []
        
        logger.info(f"🔍 Batch vendor lookup for {len(items)} items")
        
        for item in items:
            dabs_plu = str(item.get('plu', item.get('id', '')))
            dabs_name = item.get('name', item.get('description', ''))
            
            result = self.lookup_vendor_code(dabs_plu, dabs_name)
            results.append(result)
            
            if result.success:
                logger.info(f"✅ Mapped: {dabs_plu} → {result.vendor_item_code}")
            else:
                logger.warning(f"⚠️ No mapping: {dabs_plu} ({dabs_name})")
        
        successful_mappings = sum(1 for r in results if r.success)
        logger.info(f"📊 Batch lookup complete: {successful_mappings}/{len(items)} mapped")
        
        return results
    
    def create_manual_resolution(self, dabs_plu: str, dabs_name: str, 
                               vendor_code: str, resolution_method: str,
                               resolved_by: str, notes: str = None) -> bool:
        """Create manual resolution for unmapped item"""
        try:
            # Add the mapping
            mapping = VendorMapping(
                dabs_plu=dabs_plu,
                dabs_name=dabs_name,
                vendor_item_code=vendor_code,
                vendor_name="Manual Resolution",
                confidence=0.8,  # Manual resolutions have lower confidence
                last_verified=datetime.now().isoformat(),
                verification_source="manual_resolution",
                notes=notes
            )
            
            if self.add_mapping(mapping):
                # Log the manual resolution
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        INSERT INTO manual_resolutions 
                        (dabs_plu, dabs_name, resolved_vendor_code, resolution_method, 
                         resolved_by, resolution_notes, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        dabs_plu, dabs_name, vendor_code, resolution_method,
                        resolved_by, notes, datetime.now().isoformat()
                    ))
                    conn.commit()
                
                logger.info(f"✅ Manual resolution created: {dabs_plu} → {vendor_code}")
                return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create manual resolution: {e}")
        
        return False
    
    def validate_vendor_code_format(self, vendor_code: str) -> Tuple[bool, str]:
        """Validate vendor code format for SSCS compatibility"""
        if not vendor_code:
            return False, "Vendor code cannot be empty"
        
        # SSCS vendor code requirements
        if len(vendor_code) > 20:
            return False, "Vendor code exceeds 20 character limit"
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r'^[A-Za-z0-9_-]+$', vendor_code):
            return False, "Vendor code contains invalid characters (use only A-Z, 0-9, -, _)"
        
        return True, "Valid vendor code format"
    
    def get_mapping_statistics(self) -> Dict[str, Any]:
        """Get mapping database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT COUNT(*) FROM vendor_mappings')
                total_mappings = cursor.fetchone()[0]
                
                cursor = conn.execute('''
                    SELECT category, COUNT(*) FROM vendor_mappings 
                    WHERE category IS NOT NULL 
                    GROUP BY category
                ''')
                category_counts = dict(cursor.fetchall())
                
                cursor = conn.execute('''
                    SELECT AVG(confidence) FROM vendor_mappings 
                    WHERE confidence IS NOT NULL
                ''')
                avg_confidence = cursor.fetchone()[0] or 0.0
                
                cursor = conn.execute('''
                    SELECT COUNT(*) FROM mapping_attempts WHERE success = 0
                ''')
                failed_attempts = cursor.fetchone()[0]
                
                cursor = conn.execute('SELECT COUNT(*) FROM manual_resolutions')
                manual_resolutions = cursor.fetchone()[0]
                
                return {
                    'total_mappings': total_mappings,
                    'category_distribution': category_counts,
                    'average_confidence': round(avg_confidence, 3),
                    'failed_lookup_attempts': failed_attempts,
                    'manual_resolutions': manual_resolutions,
                    'cache_size': len(self.mapping_cache)
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get mapping statistics: {e}")
            return {'error': str(e)}
    
    def export_mappings(self, output_file: str) -> bool:
        """Export all mappings to JSON file"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT * FROM vendor_mappings')
                rows = cursor.fetchall()
                
                mappings = [asdict(self._row_to_mapping(row)) for row in rows]
                
                with open(output_file, 'w') as f:
                    json.dump({
                        'export_timestamp': datetime.now().isoformat(),
                        'total_mappings': len(mappings),
                        'mappings': mappings
                    }, f, indent=2, default=str)
                
                logger.info(f"📁 Mappings exported to {output_file}: {len(mappings)} records")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to export mappings: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    # Initialize vendor mapping system
    vendor_system = VendorMappingSystem()
    
    # Example Order 233813 items for testing
    test_items = [
        {'plu': '917817', 'name': 'RED ROCK ELEPHINO IPA 500ml'},
        {'plu': '039271', 'name': 'SUGAR HOUSE VODKA 1000ml'},
        {'plu': '419961', 'name': '19 CRIMES CABERNET SAUVIGNON 750ml'},
        {'plu': '999999', 'name': 'UNKNOWN PRODUCT TEST'}  # This should fail
    ]
    
    print("🧪 Testing vendor mapping system...")
    
    # Batch lookup
    results = vendor_system.batch_lookup(test_items)
    
    print(f"\n📊 Mapping Results:")
    for result in results:
        if result.success:
            print(f"  ✅ {result.dabs_plu}: {result.vendor_item_code} (confidence: {result.confidence:.1%})")
        else:
            print(f"  ❌ {result.dabs_plu}: {result.error_message}")
            if result.suggestions:
                print(f"     Suggestions: {len(result.suggestions)} similar items found")
    
    # Show statistics
    print(f"\n📊 Mapping Statistics:")
    stats = vendor_system.get_mapping_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test manual resolution
    print(f"\n🔧 Testing manual resolution...")
    success = vendor_system.create_manual_resolution(
        dabs_plu="999999",
        dabs_name="UNKNOWN PRODUCT TEST",
        vendor_code="TEST-UNKNOWN-001",
        resolution_method="manual_entry",
        resolved_by="system_test",
        notes="Test manual resolution"
    )
    print(f"Manual resolution: {'✅ Success' if success else '❌ Failed'}")
    
    # Test the resolved item
    resolved_result = vendor_system.lookup_vendor_code("999999")
    print(f"Resolved lookup: {'✅ Success' if resolved_result.success else '❌ Failed'}")
    if resolved_result.success:
        print(f"  Vendor code: {resolved_result.vendor_item_code}")
