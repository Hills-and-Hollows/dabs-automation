#!/usr/bin/env python3
"""
UPC Management Tool for DABS EDI System
Provides comprehensive UPC barcode management for SSCS integration

Features:
- Manual UPC entry and management
- Bulk UPC import from CSV/Excel
- UPC validation and Verifone formatting
- SSCS integration readiness reporting
- UPC database maintenance
"""

import asyncio
import csv
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime

from upc_lookup_integration import UPCLookupManager, UPCLookupResult

class UPCManagementTool:
    """Comprehensive UPC management for DABS EDI system"""
    
    def __init__(self, db_path: str = "data/upc_database.sqlite"):
        self.upc_manager = UPCLookupManager(db_path)
        self.db_path = Path(db_path)
    
    def add_upc_mapping(self, dabs_sku: str, product_name: str, upc_12_digit: str,
                       brand: str = None, size: str = None, category: str = None) -> bool:
        """
        Add single UPC mapping
        
        Args:
            dabs_sku: DABS SKU/CSC code
            product_name: Product description
            upc_12_digit: 12-digit UPC barcode
            brand: Product brand (optional)
            size: Product size (optional)
            category: Product category (optional)
            
        Returns:
            Success status
        """
        try:
            self.upc_manager.add_manual_upc(
                dabs_sku=dabs_sku,
                product_name=product_name,
                upc_12_digit=upc_12_digit,
                brand=brand,
                size=size,
                category=category
            )
            print(f"✅ Added UPC mapping: {dabs_sku} → {upc_12_digit}")
            return True
        except Exception as e:
            print(f"❌ Failed to add UPC mapping: {e}")
            return False
    
    def bulk_import_upcs_from_csv(self, csv_file_path: str) -> Dict[str, int]:
        """
        Import UPC mappings from CSV file
        
        Expected CSV format:
        dabs_sku,product_name,upc_12_digit,brand,size,category
        
        Args:
            csv_file_path: Path to CSV file
            
        Returns:
            Import statistics
        """
        csv_path = Path(csv_file_path)
        if not csv_path.exists():
            print(f"❌ CSV file not found: {csv_path}")
            return {'success': 0, 'failed': 0, 'skipped': 0}
        
        stats = {'success': 0, 'failed': 0, 'skipped': 0}
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    dabs_sku = row.get('dabs_sku', '').strip()
                    product_name = row.get('product_name', '').strip()
                    upc_12_digit = row.get('upc_12_digit', '').strip()
                    
                    if not all([dabs_sku, product_name, upc_12_digit]):
                        stats['skipped'] += 1
                        continue
                    
                    # Validate UPC format
                    if not self._validate_upc_format(upc_12_digit):
                        print(f"⚠️  Invalid UPC format for {dabs_sku}: {upc_12_digit}")
                        stats['failed'] += 1
                        continue
                    
                    success = self.add_upc_mapping(
                        dabs_sku=dabs_sku,
                        product_name=product_name,
                        upc_12_digit=upc_12_digit,
                        brand=row.get('brand', '').strip() or None,
                        size=row.get('size', '').strip() or None,
                        category=row.get('category', '').strip() or None
                    )
                    
                    if success:
                        stats['success'] += 1
                    else:
                        stats['failed'] += 1
        
        except Exception as e:
            print(f"❌ CSV import failed: {e}")
        
        print(f"\n📊 Import Results:")
        print(f"✅ Success: {stats['success']}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"⏭️  Skipped: {stats['skipped']}")
        
        return stats
    
    def export_upcs_to_csv(self, output_file: str = None) -> str:
        """
        Export all UPC mappings to CSV
        
        Args:
            output_file: Output CSV file path (optional)
            
        Returns:
            Path to exported CSV file
        """
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"data/upc_export_{timestamp}.csv"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT dabs_sku, product_name, upc_12_digit, upc_11_digit,
                       brand, size, category, confidence_score, lookup_source,
                       created_at, updated_at
                FROM upc_lookup
                ORDER BY dabs_sku
            """)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'dabs_sku', 'product_name', 'upc_12_digit', 'upc_11_digit',
                    'brand', 'size', 'category', 'confidence_score', 'lookup_source',
                    'created_at', 'updated_at'
                ])
                
                # Write data
                writer.writerows(cursor.fetchall())
        
        print(f"✅ UPC database exported to: {output_path}")
        return str(output_path)
    
    def get_upc_statistics(self) -> Dict[str, any]:
        """Get comprehensive UPC database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Total mappings
            total_count = conn.execute("SELECT COUNT(*) FROM upc_lookup").fetchone()[0]
            
            # Mappings with UPCs
            upc_count = conn.execute(
                "SELECT COUNT(*) FROM upc_lookup WHERE upc_12_digit IS NOT NULL AND upc_12_digit != ''"
            ).fetchone()[0]
            
            # By category
            category_stats = conn.execute("""
                SELECT category, COUNT(*) 
                FROM upc_lookup 
                WHERE category IS NOT NULL 
                GROUP BY category 
                ORDER BY COUNT(*) DESC
            """).fetchall()
            
            # By lookup source
            source_stats = conn.execute("""
                SELECT lookup_source, COUNT(*) 
                FROM upc_lookup 
                GROUP BY lookup_source 
                ORDER BY COUNT(*) DESC
            """).fetchall()
            
            # Recent additions
            recent_count = conn.execute("""
                SELECT COUNT(*) FROM upc_lookup 
                WHERE created_at >= datetime('now', '-7 days')
            """).fetchone()[0]
        
        return {
            'total_mappings': total_count,
            'with_upcs': upc_count,
            'coverage_percentage': (upc_count / total_count * 100) if total_count > 0 else 0,
            'category_breakdown': dict(category_stats),
            'source_breakdown': dict(source_stats),
            'recent_additions': recent_count
        }
    
    def find_missing_upcs(self, limit: int = 50) -> List[Tuple[str, str]]:
        """
        Find items missing UPC mappings
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of (dabs_sku, product_name) tuples missing UPCs
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT dabs_sku, product_name
                FROM upc_lookup 
                WHERE upc_12_digit IS NULL OR upc_12_digit = ''
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit,))
            
            return cursor.fetchall()
    
    def validate_verifone_compatibility(self) -> Dict[str, List[str]]:
        """
        Validate UPC compatibility with Verifone registers
        
        Returns:
            Dictionary with compatible and incompatible UPCs
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT dabs_sku, upc_12_digit, upc_11_digit
                FROM upc_lookup 
                WHERE upc_12_digit IS NOT NULL AND upc_12_digit != ''
            """)
            
            compatible = []
            incompatible = []
            
            for sku, upc_12, upc_11 in cursor.fetchall():
                if self._validate_upc_format(upc_12) and upc_11:
                    compatible.append(f"{sku}: {upc_12} → {upc_11}")
                else:
                    incompatible.append(f"{sku}: {upc_12} (invalid format)")
        
        return {
            'compatible': compatible,
            'incompatible': incompatible
        }
    
    def _validate_upc_format(self, upc: str) -> bool:
        """Validate UPC format (12 digits)"""
        return upc.isdigit() and len(upc) == 12
    
    def generate_sscs_readiness_report(self) -> str:
        """Generate comprehensive SSCS integration readiness report"""
        stats = self.get_upc_statistics()
        missing_upcs = self.find_missing_upcs(20)
        verifone_compat = self.validate_verifone_compatibility()
        
        report = f"""
# SSCS Integration Readiness Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## UPC Database Statistics
- **Total Items**: {stats['total_mappings']:,}
- **Items with UPCs**: {stats['with_upcs']:,}
- **Coverage**: {stats['coverage_percentage']:.1f}%
- **Recent Additions**: {stats['recent_additions']} (last 7 days)

## Category Breakdown
"""
        
        for category, count in stats['category_breakdown'].items():
            report += f"- **{category}**: {count:,} items\n"
        
        report += f"""
## Verifone Register Compatibility
- **Compatible UPCs**: {len(verifone_compat['compatible']):,}
- **Incompatible UPCs**: {len(verifone_compat['incompatible']):,}

## Items Missing UPCs (Top 20)
"""
        
        for sku, product in missing_upcs[:20]:
            report += f"- **{sku}**: {product}\n"
        
        report += f"""
## SSCS Integration Status
- **Barcode Scanning Ready**: {'✅ Yes' if stats['coverage_percentage'] > 80 else '⚠️ Partial'}
- **EDI Delivery Ready**: ✅ Yes
- **Verifone Compatible**: {'✅ Yes' if len(verifone_compat['incompatible']) == 0 else '⚠️ Some Issues'}

## Recommendations
"""
        
        if stats['coverage_percentage'] < 80:
            report += "- 🎯 **Priority**: Increase UPC coverage to >80% for optimal SSCS integration\n"
        
        if len(verifone_compat['incompatible']) > 0:
            report += "- 🔧 **Fix**: Resolve invalid UPC formats for Verifone compatibility\n"
        
        if len(missing_upcs) > 50:
            report += "- 📋 **Action**: Focus on high-volume items for UPC mapping\n"
        
        return report

# CLI Interface
def main():
    """Command-line interface for UPC management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='UPC Management Tool for DABS EDI System')
    parser.add_argument('--add', nargs=3, metavar=('SKU', 'PRODUCT', 'UPC'), 
                       help='Add single UPC mapping')
    parser.add_argument('--import-csv', metavar='FILE', help='Import UPCs from CSV file')
    parser.add_argument('--export-csv', metavar='FILE', help='Export UPCs to CSV file')
    parser.add_argument('--stats', action='store_true', help='Show UPC database statistics')
    parser.add_argument('--missing', type=int, default=20, help='Show items missing UPCs')
    parser.add_argument('--report', action='store_true', help='Generate SSCS readiness report')
    
    args = parser.parse_args()
    
    tool = UPCManagementTool()
    
    if args.add:
        sku, product, upc = args.add
        tool.add_upc_mapping(sku, product, upc)
    
    elif args.import_csv:
        tool.bulk_import_upcs_from_csv(args.import_csv)
    
    elif args.export_csv:
        tool.export_upcs_to_csv(args.export_csv)
    
    elif args.stats:
        stats = tool.get_upc_statistics()
        print(f"\n📊 UPC Database Statistics:")
        print(f"Total Mappings: {stats['total_mappings']:,}")
        print(f"With UPCs: {stats['with_upcs']:,}")
        print(f"Coverage: {stats['coverage_percentage']:.1f}%")
        print(f"Recent Additions: {stats['recent_additions']}")
    
    elif args.missing:
        missing = tool.find_missing_upcs(args.missing)
        print(f"\n📋 Items Missing UPCs (Top {len(missing)}):")
        for sku, product in missing:
            print(f"  {sku}: {product}")
    
    elif args.report:
        report = tool.generate_sscs_readiness_report()
        print(report)
        
        # Save report to file
        report_file = f"data/sscs_readiness_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        Path(report_file).parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_file}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
