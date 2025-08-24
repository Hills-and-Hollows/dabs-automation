#!/usr/bin/env python3
"""
UPC Master Database Manager
Comprehensive UPC management using SSCS CCB direct access + export validation

Created: January 23, 2025
Purpose: Central UPC database for DABS automation with real-time SSCS integration
"""

import asyncio
import sqlite3
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import json

from integration_hub.sscs_ccb_client import SSCSCCBClient, SSCSInventoryItem, SSCSCaseUPC

logger = logging.getLogger(__name__)

@dataclass
class UPCMasterRecord:
    """Master UPC record combining all data sources"""
    upc_code: str
    sscs_item_id: str
    description: str
    department: str
    pack_size: str
    current_price: float
    case_pack: Optional[int] = None
    case_upc: Optional[str] = None
    dabs_csc_code: Optional[str] = None
    dabs_mapped: bool = False
    last_ccb_update: Optional[datetime] = None
    last_export_validation: Optional[datetime] = None
    confidence_score: float = 1.0

class UPCMasterDatabase:
    """
    UPC Master Database Manager
    
    Centralizes UPC data from multiple SSCS sources:
    - SSCS CCB direct access (primary)
    - Physical Inventory exports (validation)
    - Transaction Line Items (verification)
    - DABS mapping integration
    """
    
    def __init__(self, db_path: str = "data/upc_master.db"):
        """Initialize UPC master database"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # SSCS CCB client for direct access
        self.ccb_client = SSCSCCBClient()
        
        # Database connection
        self.conn: Optional[sqlite3.Connection] = None
        
        # Initialize database schema
        self._init_database()
        
        logger.info(f"UPC Master Database initialized: {self.db_path}")

    def _init_database(self):
        """Initialize SQLite database schema for UPC management"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            cursor = self.conn.cursor()
            
            # UPC Master table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS upc_master (
                    upc_code TEXT PRIMARY KEY,
                    sscs_item_id TEXT,
                    description TEXT,
                    department TEXT,
                    pack_size TEXT,
                    current_price REAL,
                    case_pack INTEGER,
                    case_upc TEXT,
                    dabs_csc_code TEXT,
                    dabs_mapped BOOLEAN DEFAULT FALSE,
                    last_ccb_update TIMESTAMP,
                    last_export_validation TIMESTAMP,
                    confidence_score REAL DEFAULT 1.0,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # DABS mapping table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dabs_sscs_mapping (
                    dabs_csc_code TEXT PRIMARY KEY,
                    sscs_item_id TEXT,
                    upc_code TEXT,
                    description TEXT,
                    confidence_score REAL,
                    manual_verified BOOLEAN DEFAULT FALSE,
                    mapping_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (upc_code) REFERENCES upc_master (upc_code)
                )
            """)
            
            # Case UPC configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS case_upc_config (
                    case_upc TEXT PRIMARY KEY,
                    bottle_upc TEXT,
                    case_pack_size INTEGER,
                    description TEXT,
                    configured_date TIMESTAMP,
                    validation_status TEXT,
                    ccb_configured BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (bottle_upc) REFERENCES upc_master (upc_code)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_upc_department ON upc_master(department)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_upc_description ON upc_master(description)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dabs_mapping ON dabs_sscs_mapping(dabs_csc_code)")
            
            self.conn.commit()
            logger.info("UPC Master Database schema initialized")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    async def sync_with_ccb_inventory(self) -> int:
        """
        Sync UPC master database with SSCS CCB live inventory
        
        Returns:
            int: Number of items updated
        """
        try:
            logger.info("Starting CCB inventory sync...")
            
            # Get complete inventory from CCB
            ccb_inventory = await self.ccb_client.get_complete_inventory_with_upcs()
            
            updated_count = 0
            cursor = self.conn.cursor()
            
            for item in ccb_inventory:
                # Upsert UPC master record
                cursor.execute("""
                    INSERT OR REPLACE INTO upc_master 
                    (upc_code, sscs_item_id, description, department, pack_size, 
                     current_price, last_ccb_update, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.upc_code,
                    item.sscs_item_id,
                    item.description,
                    item.department,
                    item.pack_size,
                    item.current_price,
                    datetime.now(),
                    1.0  # CCB data has highest confidence
                ))
                updated_count += 1
            
            self.conn.commit()
            logger.info(f"CCB inventory sync complete: {updated_count} items updated")
            return updated_count
            
        except Exception as e:
            logger.error(f"CCB inventory sync error: {e}")
            return 0

    def validate_with_export_data(self, export_csv_path: str) -> Tuple[int, int]:
        """
        Validate UPC master database against ProcessInventory.csv export
        
        Args:
            export_csv_path: Path to ProcessInventory.csv export file
            
        Returns:
            Tuple[int, int]: (validated_count, variance_count)
        """
        try:
            logger.info(f"Validating UPC database against export: {export_csv_path}")
            
            # Process export file (using logic from CCB client)
            export_items = self.ccb_client._process_inventory_csv(Path(export_csv_path))
            
            cursor = self.conn.cursor()
            validated_count = 0
            variance_count = 0
            
            for export_item in export_items:
                # Check if item exists in master database
                cursor.execute("SELECT * FROM upc_master WHERE upc_code = ?", (export_item.upc_code,))
                master_record = cursor.fetchone()
                
                if master_record:
                    # Validate price and description consistency
                    master_price = master_record[5]  # current_price column
                    export_price = export_item.current_price
                    
                    if abs(master_price - export_price) > 0.01:
                        variance_count += 1
                        logger.warning(f"Price variance: {export_item.upc_code} - "
                                     f"Master: ${master_price}, Export: ${export_price}")
                    
                    # Update export validation timestamp
                    cursor.execute("""
                        UPDATE upc_master 
                        SET last_export_validation = ? 
                        WHERE upc_code = ?
                    """, (datetime.now(), export_item.upc_code))
                    
                    validated_count += 1
                else:
                    # Add export-only items to master database
                    cursor.execute("""
                        INSERT INTO upc_master 
                        (upc_code, sscs_item_id, description, department, pack_size, 
                         current_price, last_export_validation, confidence_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        export_item.upc_code,
                        export_item.sscs_item_id,
                        export_item.description,
                        export_item.department,
                        export_item.pack_size,
                        export_item.current_price,
                        datetime.now(),
                        0.9  # Export data has high confidence
                    ))
                    validated_count += 1
                    logger.info(f"Added export-only item: {export_item.upc_code}")
            
            self.conn.commit()
            logger.info(f"Export validation complete: {validated_count} validated, {variance_count} variances")
            return validated_count, variance_count
            
        except Exception as e:
            logger.error(f"Export validation error: {e}")
            return 0, 0

    def load_dabs_mapping(self, mapping_csv_path: str) -> int:
        """
        Load existing DABS to SSCS mapping from CSV file
        
        Args:
            mapping_csv_path: Path to DABS_to_SSCS_Mapping_Workbook.csv
            
        Returns:
            int: Number of mappings loaded
        """
        try:
            logger.info(f"Loading DABS mapping from: {mapping_csv_path}")
            
            import pandas as pd
            mapping_df = pd.read_csv(mapping_csv_path)
            
            cursor = self.conn.cursor()
            loaded_count = 0
            
            for _, row in mapping_df.iterrows():
                dabs_code = str(row.get('DABS_CSC_Code', '')).strip()
                sscs_item_id = str(row.get('SSCS_Item_ID', '')).strip()
                description = str(row.get('DABS_Product_Name', '')).strip()
                
                if dabs_code and sscs_item_id:
                    # Find corresponding UPC in master database
                    cursor.execute("SELECT upc_code FROM upc_master WHERE sscs_item_id = ?", (sscs_item_id,))
                    upc_result = cursor.fetchone()
                    
                    upc_code = upc_result[0] if upc_result else None
                    
                    # Insert DABS mapping
                    cursor.execute("""
                        INSERT OR REPLACE INTO dabs_sscs_mapping 
                        (dabs_csc_code, sscs_item_id, upc_code, description, confidence_score, manual_verified)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (dabs_code, sscs_item_id, upc_code, description, 1.0, True))
                    
                    # Update UPC master with DABS mapping
                    if upc_code:
                        cursor.execute("""
                            UPDATE upc_master 
                            SET dabs_csc_code = ?, dabs_mapped = TRUE 
                            WHERE upc_code = ?
                        """, (dabs_code, upc_code))
                    
                    loaded_count += 1
            
            self.conn.commit()
            logger.info(f"DABS mapping loaded: {loaded_count} mappings")
            return loaded_count
            
        except Exception as e:
            logger.error(f"DABS mapping load error: {e}")
            return 0

    def get_upc_by_dabs_code(self, dabs_csc_code: str) -> Optional[UPCMasterRecord]:
        """
        Get UPC record by DABS CSC code
        
        Args:
            dabs_csc_code: DABS CSC code to lookup
            
        Returns:
            UPCMasterRecord: Matched UPC record or None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM upc_master 
                WHERE dabs_csc_code = ?
            """, (dabs_csc_code,))
            
            record = cursor.fetchone()
            if record:
                return UPCMasterRecord(
                    upc_code=record[0],
                    sscs_item_id=record[1],
                    description=record[2],
                    department=record[3],
                    pack_size=record[4],
                    current_price=record[5],
                    case_pack=record[6],
                    case_upc=record[7],
                    dabs_csc_code=record[8],
                    dabs_mapped=bool(record[9]),
                    last_ccb_update=datetime.fromisoformat(record[10]) if record[10] else None,
                    last_export_validation=datetime.fromisoformat(record[11]) if record[11] else None,
                    confidence_score=record[12]
                )
            else:
                logger.warning(f"No UPC found for DABS code: {dabs_csc_code}")
                return None
                
        except Exception as e:
            logger.error(f"DABS UPC lookup error: {e}")
            return None

    def get_all_liquor_upcs(self) -> List[UPCMasterRecord]:
        """
        Get all liquor/beer/wine UPC records for DABS processing
        
        Returns:
            List[UPCMasterRecord]: All alcohol-related UPC records
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM upc_master 
                WHERE department IN ('LIQUOR STORE', 'BEER-GS', 'WINE', 'SPIRITS')
                ORDER BY description
            """)
            
            records = []
            for row in cursor.fetchall():
                record = UPCMasterRecord(
                    upc_code=row[0],
                    sscs_item_id=row[1],
                    description=row[2],
                    department=row[3],
                    pack_size=row[4],
                    current_price=row[5],
                    case_pack=row[6],
                    case_upc=row[7],
                    dabs_csc_code=row[8],
                    dabs_mapped=bool(row[9]),
                    last_ccb_update=datetime.fromisoformat(row[10]) if row[10] else None,
                    last_export_validation=datetime.fromisoformat(row[11]) if row[11] else None,
                    confidence_score=row[12]
                )
                records.append(record)
            
            logger.info(f"Retrieved {len(records)} liquor/beer/wine UPC records")
            return records
            
        except Exception as e:
            logger.error(f"Liquor UPC retrieval error: {e}")
            return []

    async def configure_case_upcs_bulk(self, upc_records: List[UPCMasterRecord], 
                                     default_case_pack: int = 6) -> List[SSCSCaseUPC]:
        """
        Configure case UPCs for multiple items in bulk
        
        Args:
            upc_records: UPC records to configure case UPCs for
            default_case_pack: Default case pack size if not specified
            
        Returns:
            List[SSCSCaseUPC]: Successfully configured case UPCs
        """
        try:
            configured_cases = []
            cursor = self.conn.cursor()
            
            for record in upc_records:
                case_pack_size = record.case_pack or default_case_pack
                
                # Generate case UPC configuration
                case_config = await self.ccb_client.generate_case_upc_for_item(
                    SSCSInventoryItem(
                        upc_code=record.upc_code,
                        sscs_item_id=record.sscs_item_id,
                        description=record.description,
                        department=record.department,
                        pack_size=record.pack_size,
                        current_price=record.current_price
                    ),
                    case_pack_size
                )
                
                if case_config:
                    # Update UPC master with case UPC
                    cursor.execute("""
                        UPDATE upc_master 
                        SET case_upc = ?, case_pack = ? 
                        WHERE upc_code = ?
                    """, (case_config.case_upc, case_pack_size, record.upc_code))
                    
                    # Insert case UPC configuration
                    cursor.execute("""
                        INSERT OR REPLACE INTO case_upc_config 
                        (case_upc, bottle_upc, case_pack_size, description, 
                         configured_date, validation_status, ccb_configured)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        case_config.case_upc,
                        case_config.bottle_upc,
                        case_config.case_pack_size,
                        case_config.description,
                        case_config.configured_date,
                        case_config.validation_status,
                        True
                    ))
                    
                    configured_cases.append(case_config)
                    logger.info(f"Case UPC configured: {record.description} → {case_config.case_upc}")
                else:
                    logger.warning(f"Failed to configure case UPC for: {record.description}")
            
            self.conn.commit()
            logger.info(f"Bulk case UPC configuration: {len(configured_cases)}/{len(upc_records)} successful")
            return configured_cases
            
        except Exception as e:
            logger.error(f"Bulk case UPC configuration error: {e}")
            return []

    def find_upc_by_description_fuzzy(self, description: str, 
                                    confidence_threshold: float = 0.8) -> Optional[UPCMasterRecord]:
        """
        Find UPC using fuzzy description matching
        
        Args:
            description: Product description to match
            confidence_threshold: Minimum confidence score
            
        Returns:
            UPCMasterRecord: Best match or None
        """
        try:
            from difflib import SequenceMatcher
            
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM upc_master WHERE department IN ('LIQUOR STORE', 'BEER-GS', 'WINE', 'SPIRITS')")
            
            best_match = None
            best_score = 0.0
            
            for row in cursor.fetchall():
                item_description = row[2]  # description column
                similarity = SequenceMatcher(None, description.upper(), item_description.upper()).ratio()
                
                if similarity > best_score and similarity >= confidence_threshold:
                    best_score = similarity
                    best_match = UPCMasterRecord(
                        upc_code=row[0],
                        sscs_item_id=row[1],
                        description=row[2],
                        department=row[3],
                        pack_size=row[4],
                        current_price=row[5],
                        case_pack=row[6],
                        case_upc=row[7],
                        dabs_csc_code=row[8],
                        dabs_mapped=bool(row[9]),
                        last_ccb_update=datetime.fromisoformat(row[10]) if row[10] else None,
                        last_export_validation=datetime.fromisoformat(row[11]) if row[11] else None,
                        confidence_score=best_score
                    )
            
            if best_match:
                logger.info(f"Fuzzy match found: '{description}' → {best_match.upc_code} (confidence: {best_score:.2f})")
                return best_match
            else:
                logger.warning(f"No fuzzy match found for: '{description}' (threshold: {confidence_threshold})")
                return None
                
        except Exception as e:
            logger.error(f"Fuzzy UPC matching error: {e}")
            return None

    def get_database_stats(self) -> Dict[str, int]:
        """Get UPC database statistics"""
        try:
            cursor = self.conn.cursor()
            
            stats = {}
            
            # Total UPC records
            cursor.execute("SELECT COUNT(*) FROM upc_master")
            stats['total_items'] = cursor.fetchone()[0]
            
            # Liquor/beer/wine items
            cursor.execute("""
                SELECT COUNT(*) FROM upc_master 
                WHERE department IN ('LIQUOR STORE', 'BEER-GS', 'WINE', 'SPIRITS')
            """)
            stats['liquor_items'] = cursor.fetchone()[0]
            
            # DABS mapped items
            cursor.execute("SELECT COUNT(*) FROM upc_master WHERE dabs_mapped = TRUE")
            stats['dabs_mapped'] = cursor.fetchone()[0]
            
            # Case UPC configured items
            cursor.execute("SELECT COUNT(*) FROM case_upc_config WHERE ccb_configured = TRUE")
            stats['case_upcs_configured'] = cursor.fetchone()[0]
            
            # Recent CCB updates
            cursor.execute("""
                SELECT COUNT(*) FROM upc_master 
                WHERE last_ccb_update > datetime('now', '-24 hours')
            """)
            stats['recent_ccb_updates'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Database stats error: {e}")
            return {}

    async def prepare_restaurant_delivery_upcs(self, restaurant_order_items: List[Dict]) -> Dict[str, SSCSCaseUPC]:
        """
        Prepare case UPCs for restaurant order delivery
        
        Args:
            restaurant_order_items: Restaurant order items needing case UPCs
            
        Returns:
            Dict[str, SSCSCaseUPC]: Case UPCs ready for delivery scanning
        """
        try:
            logger.info(f"Preparing UPCs for restaurant delivery: {len(restaurant_order_items)} items")
            
            prepared_upcs = {}
            cursor = self.conn.cursor()
            
            for order_item in restaurant_order_items:
                description = order_item.get('description', '')
                case_pack = order_item.get('case_pack', 6)
                
                # Find UPC record by description
                upc_record = self.find_upc_by_description_fuzzy(description)
                
                if upc_record:
                    # Check if case UPC already configured
                    cursor.execute("""
                        SELECT * FROM case_upc_config 
                        WHERE bottle_upc = ? AND case_pack_size = ?
                    """, (upc_record.upc_code, case_pack))
                    
                    existing_case = cursor.fetchone()
                    
                    if existing_case:
                        # Use existing case UPC configuration
                        case_config = SSCSCaseUPC(
                            case_upc=existing_case[0],
                            bottle_upc=existing_case[1],
                            case_pack_size=existing_case[2],
                            description=existing_case[3],
                            configured_date=datetime.fromisoformat(existing_case[4]),
                            validation_status=existing_case[5]
                        )
                        prepared_upcs[description] = case_config
                        logger.info(f"Existing case UPC ready: {description} → {case_config.case_upc}")
                    else:
                        # Generate new case UPC configuration
                        case_config = await self.ccb_client.generate_case_upc_for_item(
                            SSCSInventoryItem(
                                upc_code=upc_record.upc_code,
                                sscs_item_id=upc_record.sscs_item_id,
                                description=upc_record.description,
                                department=upc_record.department,
                                pack_size=upc_record.pack_size,
                                current_price=upc_record.current_price
                            ),
                            case_pack
                        )
                        
                        if case_config:
                            prepared_upcs[description] = case_config
                            logger.info(f"New case UPC configured: {description} → {case_config.case_upc}")
                else:
                    logger.warning(f"No UPC record found for restaurant item: {description}")
            
            logger.info(f"Restaurant delivery UPCs prepared: {len(prepared_upcs)}/{len(restaurant_order_items)} ready")
            return prepared_upcs
            
        except Exception as e:
            logger.error(f"Restaurant delivery UPC preparation error: {e}")
            return {}

    def export_upc_summary_report(self, output_path: str) -> bool:
        """
        Export comprehensive UPC database summary for management review
        
        Args:
            output_path: Path for summary report export
            
        Returns:
            bool: True if export successful
        """
        try:
            cursor = self.conn.cursor()
            
            # Get comprehensive UPC data
            cursor.execute("""
                SELECT 
                    upc_code, description, department, current_price,
                    case_upc, dabs_csc_code, dabs_mapped,
                    last_ccb_update, confidence_score
                FROM upc_master 
                WHERE department IN ('LIQUOR STORE', 'BEER-GS', 'WINE', 'SPIRITS')
                ORDER BY department, description
            """)
            
            records = cursor.fetchall()
            
            # Create summary report
            summary_data = []
            for row in records:
                summary_data.append({
                    'UPC_Code': row[0],
                    'Description': row[1],
                    'Department': row[2],
                    'Current_Price': row[3],
                    'Case_UPC': row[4] or 'Not Configured',
                    'DABS_Code': row[5] or 'Not Mapped',
                    'DABS_Mapped': 'Yes' if row[6] else 'No',
                    'Last_CCB_Update': row[7] or 'Never',
                    'Confidence_Score': row[8]
                })
            
            # Export to JSON for easy parsing
            with open(output_path, 'w') as f:
                json.dump({
                    'export_date': datetime.now().isoformat(),
                    'total_items': len(summary_data),
                    'database_stats': self.get_database_stats(),
                    'upc_records': summary_data
                }, f, indent=2, default=str)
            
            logger.info(f"UPC summary report exported: {output_path} ({len(summary_data)} items)")
            return True
            
        except Exception as e:
            logger.error(f"UPC summary export error: {e}")
            return False

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("UPC Master Database connection closed")

# Example usage and testing
async def main():
    """Test UPC Master Database functionality"""
    db = UPCMasterDatabase()
    
    try:
        print("=== UPC Master Database Test ===")
        
        # Test CCB inventory sync
        print("\n1. Testing CCB inventory sync...")
        sync_count = await db.sync_with_ccb_inventory()
        print(f"✅ Synced {sync_count} items from SSCS CCB")
        
        # Test export validation
        print("\n2. Testing export validation...")
        export_path = "/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/dabs/ProcessInventory.csv"
        if Path(export_path).exists():
            validated, variances = db.validate_with_export_data(export_path)
            print(f"✅ Validated {validated} items, {variances} price variances")
        
        # Test DABS mapping
        print("\n3. Testing DABS mapping load...")
        mapping_path = "/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/dabs/DABS_to_SSCS_Mapping_Workbook.csv"
        if Path(mapping_path).exists():
            mapped_count = db.load_dabs_mapping(mapping_path)
            print(f"✅ Loaded {mapped_count} DABS mappings")
        
        # Test database stats
        print("\n4. Database statistics...")
        stats = db.get_database_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Test UPC lookup
        print("\n5. Testing UPC lookup...")
        liquor_items = db.get_all_liquor_upcs()
        if liquor_items:
            sample_item = liquor_items[0]
            print(f"✅ Sample UPC: {sample_item.description} → {sample_item.upc_code}")
            
            # Test fuzzy matching
            fuzzy_match = db.find_upc_by_description_fuzzy(sample_item.description[:20])
            if fuzzy_match:
                print(f"✅ Fuzzy match: {fuzzy_match.confidence_score:.2f} confidence")
        
        # Export summary report
        print("\n6. Exporting summary report...")
        report_path = "data/exports/upc_master_summary.json"
        success = db.export_upc_summary_report(report_path)
        print(f"✅ Summary exported: {report_path}" if success else "❌ Export failed")
        
        print("\n✅ UPC Master Database test complete!")
        
    except Exception as e:
        print(f"❌ UPC Master Database test failed: {e}")
    
    finally:
        await db.ccb_client.close()
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
