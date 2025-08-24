#!/usr/bin/env python3
"""
DABS Product Catalog API - Hills & Hollows LLC
Searchable product catalog for restaurant order system

Provides live DABS pricing data with search functionality
for the Restaurant Order Automation System
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import re
import logging
from dataclasses import dataclass, asdict
import xml.etree.ElementTree as ET

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class DABSCatalogProduct:
    """Simplified product data for restaurant catalog"""
    sku: str
    vendor_item_code: str
    product_name: str
    description: str
    category: str
    price: float
    size: str
    status: str
    effective_date: str
    search_terms: str  # Concatenated searchable text

class DABSCatalogAPI:
    """
    DABS Product Catalog API for Restaurant Orders
    
    Features:
    - Live DABS product search
    - Real-time pricing data
    - Product filtering by category
    - Search functionality for product descriptions
    """
    
    def __init__(self):
        self.project_root = Path('/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory')
        self.products_cache: List[DABSCatalogProduct] = []
        self.last_updated: Optional[datetime] = None
        self.cache_duration_minutes = 30  # Refresh cache every 30 minutes
        
        logger.info("DABS Catalog API initialized")
    
    async def get_products(self, search_query: Optional[str] = None, 
                          category_filter: Optional[str] = None,
                          limit: int = 50) -> Dict[str, Any]:
        """
        Get searchable DABS products with optional filtering
        
        Args:
            search_query: Search term for product names/descriptions
            category_filter: Filter by product category
            limit: Maximum number of results to return
            
        Returns:
            Dict containing products and metadata
        """
        try:
            # Refresh cache if needed
            await self._refresh_cache_if_needed()
            
            products = self.products_cache.copy()
            
            # Apply search filter
            if search_query:
                search_query = search_query.lower().strip()
                products = [
                    p for p in products 
                    if search_query in p.search_terms.lower()
                ]
            
            # Apply category filter
            if category_filter:
                products = [
                    p for p in products 
                    if category_filter.upper() in p.category.upper()
                ]
            
            # Limit results
            products = products[:limit]
            
            # Get unique categories for filtering UI
            all_categories = list(set(p.category for p in self.products_cache))
            
            return {
                "success": True,
                "products": [asdict(p) for p in products],
                "total_found": len(products),
                "total_available": len(self.products_cache),
                "categories": sorted(all_categories),
                "last_updated": self.last_updated.isoformat() if self.last_updated else None,
                "search_query": search_query,
                "category_filter": category_filter
            }
            
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return {
                "success": False,
                "error": str(e),
                "products": [],
                "total_found": 0,
                "total_available": 0,
                "categories": []
            }
    
    async def get_product_by_sku(self, sku: str) -> Dict[str, Any]:
        """Get specific product by SKU"""
        try:
            await self._refresh_cache_if_needed()
            
            product = next((p for p in self.products_cache if p.sku == sku), None)
            
            if product:
                return {
                    "success": True,
                    "product": asdict(product)
                }
            else:
                return {
                    "success": False,
                    "error": f"Product with SKU {sku} not found"
                }
                
        except Exception as e:
            logger.error(f"Error getting product by SKU {sku}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_categories(self) -> Dict[str, Any]:
        """Get all available product categories"""
        try:
            await self._refresh_cache_if_needed()
            
            categories = {}
            for product in self.products_cache:
                cat = product.category
                if cat not in categories:
                    categories[cat] = 0
                categories[cat] += 1
            
            return {
                "success": True,
                "categories": [
                    {"name": cat, "count": count} 
                    for cat, count in sorted(categories.items())
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return {
                "success": False,
                "error": str(e),
                "categories": []
            }
    
    async def _refresh_cache_if_needed(self):
        """Refresh product cache if expired or empty"""
        if (not self.products_cache or 
            not self.last_updated or 
            (datetime.now() - self.last_updated).total_seconds() > (self.cache_duration_minutes * 60)):
            
            await self._load_products_from_sources()
    
    async def _load_products_from_sources(self):
        """Load products from available DABS data sources"""
        try:
            logger.info("Loading DABS products from data sources")
            
            products = []
            
            # Load from Excel backup data first (full catalog)
            excel_products = await self._load_from_excel_backups()
            if excel_products:
                products.extend(excel_products)
                logger.info(f"Loaded {len(excel_products)} products from Excel backups")
            
            # Supplement with XML export data for any pricing updates
            xml_products = await self._load_from_xml_exports()
            if xml_products:
                # Update existing products with XML pricing, add new ones
                existing_skus = {p.sku for p in products}
                for xml_product in xml_products:
                    if xml_product.sku in existing_skus:
                        # Update existing product with XML pricing
                        for i, product in enumerate(products):
                            if product.sku == xml_product.sku:
                                products[i] = xml_product  # XML has more current pricing
                                break
                    else:
                        # Add new product from XML
                        products.append(xml_product)
                logger.info(f"Updated/added {len(xml_products)} products from XML exports")
            
            self.products_cache = sorted(products, key=lambda x: x.product_name)
            self.last_updated = datetime.now()
            
            logger.info(f"DABS catalog updated with {len(self.products_cache)} total products")
            
        except Exception as e:
            logger.error(f"Error loading DABS products: {e}")
            if not self.products_cache:  # Only raise if no cache exists
                raise
    
    async def _load_from_xml_exports(self) -> List[DABSCatalogProduct]:
        """Load products from XML export files"""
        products = []
        
        try:
            exports_dir = self.project_root / 'exports'
            xml_files = list(exports_dir.glob('DABS_*_ItemPrice.xml'))
            
            if not xml_files:
                return products
            
            # Get the most recent XML file
            latest_xml = max(xml_files, key=lambda x: x.stat().st_mtime)
            
            tree = ET.parse(latest_xml)
            root = tree.getroot()
            
            for item in root.findall('.//Item'):
                vendor_code = item.find('VendorItemCode')
                description = item.find('Description')
                category = item.find('Category')
                status = item.find('Status')
                
                pricing = item.find('Pricing')
                price = 0.0
                effective_date = ""
                
                if pricing is not None:
                    price_elem = pricing.find('VendorListPrice')
                    date_elem = pricing.find('EffectiveDate')
                    
                    if price_elem is not None:
                        try:
                            price = float(price_elem.text)
                        except (ValueError, TypeError):
                            price = 0.0
                    
                    if date_elem is not None:
                        effective_date = date_elem.text or ""
                
                if vendor_code is not None and description is not None and price > 0:
                    # Extract size information from description
                    size = self._extract_size_from_description(description.text or "")
                    
                    # Create comprehensive searchable terms
                    search_terms = f"{vendor_code.text} {description.text} {category.text or ''} {size}"
                    
                    product = DABSCatalogProduct(
                        sku=vendor_code.text,
                        vendor_item_code=vendor_code.text,
                        product_name=description.text or "",
                        description=description.text or "",
                        category=category.text or "GENERAL",
                        price=price,
                        size=size,
                        status=status.text or "Active",
                        effective_date=effective_date,
                        search_terms=search_terms
                    )
                    
                    products.append(product)
            
            logger.info(f"Loaded {len(products)} products from XML file: {latest_xml.name}")
            
        except Exception as e:
            logger.error(f"Error loading from XML exports: {e}")
        
        return products
    
    async def _load_from_excel_backups(self) -> List[DABSCatalogProduct]:
        """Load products from Excel backup files"""
        products = []
        
        try:
            backups_dir = self.project_root / 'data/dabs_backups'
            excel_files = list(backups_dir.glob('DABS Price Changes*.xlsx'))
            
            if not excel_files:
                return products
            
            # Get the most recent Excel file
            latest_excel = max(excel_files, key=lambda x: x.stat().st_mtime)
            
            # Read Excel file - first row contains headers but pandas isn't detecting them
            df_raw = pd.read_excel(latest_excel)
            
            # Check if first row contains headers
            if len(df_raw) > 0 and 'SKU' in str(df_raw.iloc[0].values):
                # Use first row as column names
                new_columns = df_raw.iloc[0].fillna('Unknown').astype(str).tolist()
                df = df_raw[1:].copy()  # Skip header row
                df.columns = new_columns
                df = df.reset_index(drop=True)
            else:
                df = df_raw
                
            logger.info(f"Excel file columns: {list(df.columns)}")
            logger.info(f"Excel file has {len(df)} rows")
            
            # Map common column names to standardized format (try multiple variations)
            column_mapping = {
                'SKU': 'sku',
                'ITEM NAME': 'product_name', 
                'Item Name': 'product_name',
                'Product Name': 'product_name',
                'Description': 'product_name',
                'PRICE': 'price',
                'Price': 'price', 
                'Current Price': 'price',
                'Retail Price': 'price',
                'ITEM TYPE': 'category',
                'Item Type': 'category',
                'Category': 'category',
                'FROM DATE': 'effective_date',
                'Effective Date': 'effective_date',
                'Date': 'effective_date',
                'ITEM STATUS': 'status',
                'Status': 'status',
                'Item Status': 'status'
            }
            
            # Rename columns to standardized names
            df = df.rename(columns=column_mapping)
            
            valid_products = 0
            for _, row in df.iterrows():
                try:
                    sku = str(row.get('sku', '')).strip()
                    product_name = str(row.get('product_name', '')).strip()
                    price = float(pd.to_numeric(row.get('price', 0), errors='coerce') or 0)
                    
                    if sku and product_name and price > 0:
                        valid_products += 1
                        size = self._extract_size_from_description(product_name)
                        category = str(row.get('category', 'GENERAL')).strip()
                        status = str(row.get('status', 'Active')).strip()
                        effective_date = str(row.get('effective_date', '')).strip()
                        
                        # Create comprehensive searchable terms with individual words
                        search_terms = f"{sku} {product_name} {category} {size}"
                        # Add individual words for better partial matching
                        words = product_name.replace('-', ' ').replace('_', ' ').split()
                        search_terms += f" {' '.join(words)}"
                        
                        product = DABSCatalogProduct(
                            sku=sku.zfill(6),  # Pad SKU to 6 digits
                            vendor_item_code=sku.zfill(6),
                            product_name=product_name,
                            description=product_name,
                            category=category,
                            price=price,
                            size=size,
                            status=status,
                            effective_date=effective_date,
                            search_terms=search_terms
                        )
                        
                        products.append(product)
                
                except Exception as e:
                    logger.warning(f"Error processing Excel row: {e}")
                    continue
            
            logger.info(f"Loaded {len(products)} products from Excel file: {latest_excel.name}")
            logger.info(f"Valid products found: {valid_products}, Total Excel rows: {len(df)}")
            
        except Exception as e:
            logger.error(f"Error loading from Excel backups: {e}")
        
        return products
    
    def _extract_size_from_description(self, description: str) -> str:
        """Extract size information from product description"""
        if not description:
            return ""
        
        # Common size patterns in DABS descriptions
        size_patterns = [
            r'(\d+(?:\.\d+)?)\s*ML',  # 750ML, 1.75ML
            r'(\d+(?:\.\d+)?)\s*L',   # 1.75L, 0.75L
            r'(\d+)\s*OZ',            # 12OZ
            r'(\d+)\s*PK',            # 6PK, 12PK
            r'(\d+)\s*PACK',          # 6PACK
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, description.upper())
            if match:
                return match.group(0)
        
        return ""
    
    async def get_search_suggestions(self, partial_query: str, limit: int = 10) -> Dict[str, Any]:
        """Get search suggestions based on partial query"""
        try:
            await self._refresh_cache_if_needed()
            
            if not partial_query or len(partial_query) < 2:
                return {"success": True, "suggestions": []}
            
            partial_query = partial_query.lower().strip()
            suggestions = []
            
            for product in self.products_cache:
                if partial_query in product.search_terms.lower():
                    suggestions.append({
                        "text": product.product_name,
                        "sku": product.sku,
                        "category": product.category
                    })
                
                if len(suggestions) >= limit:
                    break
            
            return {
                "success": True,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return {
                "success": False,
                "error": str(e),
                "suggestions": []
            }

# Global instance for FastAPI integration
dabs_catalog = DABSCatalogAPI()
