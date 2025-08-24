#!/usr/bin/env python3
"""
SSCS Computer Daily Books (CCB) Client
Direct integration with SSCS core manager tool for UPC automation

Created: January 23, 2025
Purpose: Direct access to SSCS CCB system for real-time UPC management
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import json
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SSCSInventoryItem:
    """SSCS inventory item with UPC data"""
    upc_code: str
    sscs_item_id: str
    description: str
    department: str
    pack_size: str
    current_price: float
    case_pack: Optional[int] = None
    case_upc: Optional[str] = None
    last_updated: Optional[datetime] = None

@dataclass
class SSCSCaseUPC:
    """Case UPC configuration"""
    case_upc: str
    bottle_upc: str
    case_pack_size: int
    description: str
    configured_date: datetime
    validation_status: str

class SSCSCCBClient:
    """
    SSCS Computer Daily Books (CCB) Direct Client
    
    Provides direct access to SSCS core management system for:
    - Real-time inventory access with UPC data
    - Case UPC configuration and management
    - Direct backend integration for automation
    """
    
    def __init__(self, credentials_path: str = "config/sscs_production.env"):
        """Initialize CCB client with credentials from environment file"""
        # ✅ CORRECTED URLs based on discovery validation
        self.ccb_url = "https://sscsta.sscsinc.com/CStore.Web/CDB"
        self.transaction_url = "https://sscsta.sscsinc.com/TransactionAnalysis.App/"
        self.physical_inventory_url = "https://sscsta.sscsinc.com/PhysicalInventory/Home/FetchInventory"
        
        # Load credentials from secure environment file
        self._load_credentials(credentials_path)
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        self.authenticated: bool = False
        self.session_expires: Optional[datetime] = None
        
        # UPC data cache
        self.upc_cache: Dict[str, SSCSInventoryItem] = {}
        self.cache_updated: Optional[datetime] = None
        self.cache_ttl_hours: int = 4  # 4-hour cache TTL for real-time operations
        
        logger.info("SSCS CCB Client initialized with direct system access")

    def _load_credentials(self, credentials_path: str):
        """Load SSCS credentials from environment file"""
        try:
            if os.path.exists(credentials_path):
                from dotenv import load_dotenv
                load_dotenv(credentials_path)
                
            self.username = os.getenv('SSCS_CCB_USERNAME', 'v6242shawn')
            self.password = os.getenv('SSCS_CCB_PASSWORD', 'Notone2016!')
            
            if not self.password or self.password == 'YOUR_PASSWORD_HERE':
                raise ValueError("SSCS CCB credentials not properly configured")
                
            logger.info("SSCS CCB credentials loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load SSCS credentials: {e}")
            raise

    async def authenticate_ccb(self) -> bool:
        """
        Authenticate with SSCS Computer Daily Books system
        
        Returns:
            bool: True if authentication successful
        """
        try:
            if not self.session:
                timeout = aiohttp.ClientTimeout(total=300)  # 5-minute timeout
                self.session = aiohttp.ClientSession(timeout=timeout)
            
            # CCB authentication request
            auth_data = {
                'username': self.username,
                'password': self.password,
                'rememberMe': True
            }
            
            async with self.session.post(f"{self.ccb_url}/login", data=auth_data) as response:
                if response.status == 200:
                    self.authenticated = True
                    self.session_expires = datetime.now() + timedelta(hours=8)  # 8-hour session
                    logger.info("SSCS CCB authentication successful")
                    return True
                else:
                    logger.error(f"SSCS CCB authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"CCB authentication error: {e}")
            return False

    async def get_complete_inventory_with_upcs(self) -> List[SSCSInventoryItem]:
        """
        Get complete inventory with UPC data from SSCS CCB
        
        Uses both direct CCB access and Physical Inventory exports
        for comprehensive UPC data retrieval
        
        Returns:
            List[SSCSInventoryItem]: Complete inventory with UPC codes
        """
        try:
            # Ensure authentication
            if not self.authenticated or datetime.now() > self.session_expires:
                await self.authenticate_ccb()
            
            # Primary: Direct CCB inventory access
            ccb_inventory = await self._get_ccb_inventory_direct()
            
            # Secondary: Physical Inventory export validation
            export_inventory = await self._get_physical_inventory_export()
            
            # Merge and validate data sources
            complete_inventory = self._merge_inventory_sources(ccb_inventory, export_inventory)
            
            # Cache results for performance
            self._update_upc_cache(complete_inventory)
            
            logger.info(f"Retrieved {len(complete_inventory)} items with UPC data from SSCS CCB")
            return complete_inventory
            
        except Exception as e:
            logger.error(f"Failed to retrieve SSCS inventory: {e}")
            return []

    async def _get_ccb_inventory_direct(self) -> List[SSCSInventoryItem]:
        """Direct CCB inventory access via Computer Daily Books interface"""
        try:
            # CCB inventory query endpoint
            inventory_endpoint = f"{self.ccb_url}/api/inventory/complete"
            
            async with self.session.get(inventory_endpoint) as response:
                if response.status == 200:
                    inventory_data = await response.json()
                    
                    items = []
                    for item_data in inventory_data.get('items', []):
                        item = SSCSInventoryItem(
                            upc_code=item_data.get('upc_code', ''),
                            sscs_item_id=item_data.get('item_id', ''),
                            description=item_data.get('description', ''),
                            department=item_data.get('department', ''),
                            pack_size=item_data.get('pack_size', ''),
                            current_price=float(item_data.get('current_price', 0.0)),
                            case_pack=item_data.get('case_pack'),
                            last_updated=datetime.now()
                        )
                        items.append(item)
                    
                    logger.info(f"CCB direct access: {len(items)} items retrieved")
                    return items
                else:
                    logger.warning(f"CCB inventory access failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"CCB direct inventory access error: {e}")
            return []

    async def _get_physical_inventory_export(self) -> List[SSCSInventoryItem]:
        """
        Get Physical Inventory export data for UPC validation
        
        Uses the ProcessInventory.csv structure we discovered in /dabs folder
        """
        try:
            # Check for existing ProcessInventory.csv export
            export_path = Path("data/exports/ProcessInventory.csv")
            
            if export_path.exists():
                # Process existing export file
                items = self._process_inventory_csv(export_path)
                logger.info(f"Physical Inventory export: {len(items)} items processed")
                return items
            else:
                # Request new Physical Inventory export via automation
                logger.info("Requesting new Physical Inventory export")
                await self._request_physical_inventory_export()
                return []
                
        except Exception as e:
            logger.error(f"Physical Inventory export error: {e}")
            return []

    def _process_inventory_csv(self, csv_path: Path) -> List[SSCSInventoryItem]:
        """
        Process ProcessInventory.csv export file
        
        Based on structure discovered: UPC + Description + Price + Department + UPC_Validation
        """
        try:
            # Load ProcessInventory.csv with tab delimiter
            df = pd.read_csv(csv_path, sep='\t', header=None)
            
            # Map columns based on discovered structure
            df.columns = [
                'upc_code', 'description', 'cost_1', 'cost_2', 'retail_price',
                'department', 'dept_code', 'tax_code', 'margin', 'unknown_1',
                'status', 'upc_validation'
            ]
            
            items = []
            for _, row in df.iterrows():
                # Filter for liquor/beer/wine departments
                if any(dept in str(row['department']).upper() for dept in ['LIQUOR', 'BEER', 'WINE']):
                    item = SSCSInventoryItem(
                        upc_code=str(row['upc_code']).strip(),
                        sscs_item_id=f"SSCS-{row['upc_code']}",
                        description=str(row['description']).strip(),
                        department=str(row['department']).strip(),
                        pack_size=self._extract_pack_size(str(row['description'])),
                        current_price=float(row['retail_price']) if pd.notna(row['retail_price']) else 0.0,
                        last_updated=datetime.now()
                    )
                    items.append(item)
            
            logger.info(f"Processed {len(items)} liquor/beer/wine items from ProcessInventory.csv")
            return items
            
        except Exception as e:
            logger.error(f"Error processing ProcessInventory.csv: {e}")
            return []

    def _extract_pack_size(self, description: str) -> str:
        """Extract pack size from product description"""
        import re
        
        # Common patterns for liquor bottle sizes
        size_patterns = [
            r'(\d+(?:\.\d+)?L)',      # 1.75L, 0.75L
            r'(\d+ml)',               # 750ml, 1750ml
            r'(\d+oz)',               # 12oz, 16oz  
            r'(\d+pk)',               # 6pk, 12pk
            r'(\d+pack)',             # 6pack, 12pack
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Unknown"

    def _merge_inventory_sources(self, ccb_data: List[SSCSInventoryItem], 
                                export_data: List[SSCSInventoryItem]) -> List[SSCSInventoryItem]:
        """
        Merge CCB direct access data with Physical Inventory export data
        
        Prioritizes CCB data as primary source, uses export for validation
        """
        try:
            # Create lookup by UPC code
            ccb_lookup = {item.upc_code: item for item in ccb_data}
            export_lookup = {item.upc_code: item for item in export_data}
            
            merged_items = []
            
            # Start with CCB data as primary source
            for item in ccb_data:
                # Validate against export data if available
                if item.upc_code in export_lookup:
                    export_item = export_lookup[item.upc_code]
                    # Cross-validate critical fields
                    if abs(item.current_price - export_item.current_price) > 0.01:
                        logger.warning(f"Price variance detected for {item.upc_code}: "
                                     f"CCB={item.current_price}, Export={export_item.current_price}")
                
                merged_items.append(item)
            
            # Add export-only items not found in CCB
            for item in export_data:
                if item.upc_code not in ccb_lookup:
                    logger.info(f"Export-only item found: {item.upc_code} - {item.description}")
                    merged_items.append(item)
            
            logger.info(f"Merged inventory: {len(merged_items)} total items")
            return merged_items
            
        except Exception as e:
            logger.error(f"Error merging inventory sources: {e}")
            return ccb_data if ccb_data else export_data

    async def configure_case_upc_ccb(self, case_upc_config: SSCSCaseUPC) -> bool:
        """
        Configure case UPC directly in SSCS CCB backend
        
        Args:
            case_upc_config: Case UPC configuration details
            
        Returns:
            bool: True if configuration successful
        """
        try:
            if not self.authenticated:
                await self.authenticate_ccb()
            
            # CCB case UPC configuration endpoint
            config_endpoint = f"{self.ccb_url}/api/inventory/case-upc/configure"
            
            config_data = {
                'case_upc': case_upc_config.case_upc,
                'bottle_upc': case_upc_config.bottle_upc,
                'case_pack_size': case_upc_config.case_pack_size,
                'description': case_upc_config.description,
                'auto_calculate_quantities': True,
                'enable_case_scanning': True
            }
            
            async with self.session.post(config_endpoint, json=config_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Case UPC configured: {case_upc_config.case_upc} → {case_upc_config.bottle_upc}")
                    return True
                else:
                    logger.error(f"Case UPC configuration failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Case UPC configuration error: {e}")
            return False

    async def validate_case_upc_setup(self, case_upc: str) -> bool:
        """
        Validate case UPC configuration in SSCS CCB
        
        Args:
            case_upc: Case UPC to validate
            
        Returns:
            bool: True if case UPC properly configured
        """
        try:
            validation_endpoint = f"{self.ccb_url}/api/inventory/case-upc/validate/{case_upc}"
            
            async with self.session.get(validation_endpoint) as response:
                if response.status == 200:
                    validation_data = await response.json()
                    is_valid = validation_data.get('is_configured', False)
                    
                    if is_valid:
                        logger.info(f"Case UPC validation successful: {case_upc}")
                    else:
                        logger.warning(f"Case UPC not properly configured: {case_upc}")
                    
                    return is_valid
                else:
                    logger.error(f"Case UPC validation failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Case UPC validation error: {e}")
            return False

    async def get_liquor_beer_wine_inventory(self) -> List[SSCSInventoryItem]:
        """
        Get filtered inventory for liquor, beer, and wine items only
        
        Returns:
            List[SSCSInventoryItem]: Filtered items for DABS processing
        """
        try:
            complete_inventory = await self.get_complete_inventory_with_upcs()
            
            # Filter for alcohol departments based on ProcessInventory.csv analysis
            alcohol_departments = ['LIQUOR STORE', 'BEER-GS', 'WINE', 'SPIRITS']
            
            filtered_items = [
                item for item in complete_inventory
                if any(dept in item.department.upper() for dept in alcohol_departments)
            ]
            
            logger.info(f"Filtered inventory: {len(filtered_items)} liquor/beer/wine items")
            return filtered_items
            
        except Exception as e:
            logger.error(f"Error filtering liquor inventory: {e}")
            return []

    def _update_upc_cache(self, inventory_items: List[SSCSInventoryItem]):
        """Update internal UPC cache for performance optimization"""
        self.upc_cache = {item.upc_code: item for item in inventory_items}
        self.cache_updated = datetime.now()
        logger.info(f"UPC cache updated: {len(self.upc_cache)} items cached")

    def get_upc_by_description(self, description: str, confidence_threshold: float = 0.8) -> Optional[SSCSInventoryItem]:
        """
        Get UPC by product description matching
        
        Args:
            description: Product description to match
            confidence_threshold: Minimum confidence score for match
            
        Returns:
            SSCSInventoryItem: Matched item with UPC or None
        """
        try:
            from difflib import SequenceMatcher
            
            best_match = None
            best_score = 0.0
            
            # Search cached inventory for description matches
            for upc_code, item in self.upc_cache.items():
                similarity = SequenceMatcher(None, description.upper(), item.description.upper()).ratio()
                
                if similarity > best_score and similarity >= confidence_threshold:
                    best_score = similarity
                    best_match = item
            
            if best_match:
                logger.info(f"UPC match found: '{description}' → {best_match.upc_code} (confidence: {best_score:.2f})")
                return best_match
            else:
                logger.warning(f"No UPC match found for: '{description}' (threshold: {confidence_threshold})")
                return None
                
        except Exception as e:
            logger.error(f"UPC description matching error: {e}")
            return None

    async def generate_case_upc_for_item(self, bottle_item: SSCSInventoryItem, case_pack_size: int) -> Optional[SSCSCaseUPC]:
        """
        Generate case UPC configuration for bottle item
        
        Args:
            bottle_item: Bottle item with UPC
            case_pack_size: Number of bottles in case
            
        Returns:
            SSCSCaseUPC: Case UPC configuration
        """
        try:
            # Generate case UPC using industry standard pattern
            case_upc = f"{bottle_item.upc_code}C{case_pack_size}"
            
            # Create case UPC configuration
            case_config = SSCSCaseUPC(
                case_upc=case_upc,
                bottle_upc=bottle_item.upc_code,
                case_pack_size=case_pack_size,
                description=f"{bottle_item.description} ({case_pack_size}-pack case)",
                configured_date=datetime.now(),
                validation_status="pending"
            )
            
            # Configure in CCB backend
            success = await self.configure_case_upc_ccb(case_config)
            
            if success:
                case_config.validation_status = "configured"
                logger.info(f"Case UPC generated and configured: {case_upc}")
                return case_config
            else:
                case_config.validation_status = "failed"
                logger.error(f"Case UPC configuration failed: {case_upc}")
                return None
                
        except Exception as e:
            logger.error(f"Case UPC generation error: {e}")
            return None

    async def prepare_restaurant_order_upcs(self, restaurant_order_items: List[Dict]) -> Dict[str, SSCSCaseUPC]:
        """
        Pre-configure case UPCs for restaurant order items before delivery
        
        Args:
            restaurant_order_items: List of restaurant order items with descriptions and case packs
            
        Returns:
            Dict[str, SSCSCaseUPC]: Configured case UPCs by item description
        """
        try:
            configured_cases = {}
            
            for order_item in restaurant_order_items:
                description = order_item.get('description', '')
                case_pack = order_item.get('case_pack', 6)  # Default 6-pack
                
                # Find matching bottle item with UPC
                bottle_item = self.get_upc_by_description(description)
                
                if bottle_item:
                    # Generate and configure case UPC
                    case_config = await self.generate_case_upc_for_item(bottle_item, case_pack)
                    
                    if case_config:
                        configured_cases[description] = case_config
                        logger.info(f"Restaurant order UPC ready: {description} → {case_config.case_upc}")
                    else:
                        logger.warning(f"Failed to configure case UPC for: {description}")
                else:
                    logger.warning(f"No UPC found for restaurant order item: {description}")
            
            logger.info(f"Restaurant order UPCs configured: {len(configured_cases)}/{len(restaurant_order_items)} items")
            return configured_cases
            
        except Exception as e:
            logger.error(f"Restaurant order UPC preparation error: {e}")
            return {}

    async def close(self):
        """Clean up session resources"""
        if self.session:
            await self.session.close()
            self.session = None
            self.authenticated = False
            logger.info("SSCS CCB client session closed")

# Example usage and testing
async def main():
    """Test SSCS CCB client functionality"""
    client = SSCSCCBClient()
    
    try:
        # Test authentication
        auth_success = await client.authenticate_ccb()
        if auth_success:
            print("✅ SSCS CCB authentication successful")
            
            # Test inventory retrieval
            inventory = await client.get_liquor_beer_wine_inventory()
            print(f"✅ Retrieved {len(inventory)} liquor/beer/wine items")
            
            # Test UPC lookup
            if inventory:
                test_item = inventory[0]
                print(f"✅ Sample item: {test_item.description} → UPC: {test_item.upc_code}")
                
                # Test case UPC generation
                case_config = await client.generate_case_upc_for_item(test_item, 6)
                if case_config:
                    print(f"✅ Case UPC generated: {case_config.case_upc}")
                    
                    # Test case UPC validation
                    is_valid = await client.validate_case_upc_setup(case_config.case_upc)
                    print(f"✅ Case UPC validation: {is_valid}")
        
    except Exception as e:
        print(f"❌ SSCS CCB client test failed: {e}")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
