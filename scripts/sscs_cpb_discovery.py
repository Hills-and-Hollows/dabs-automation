#!/usr/bin/env python3
"""
SSCS CPB Discovery Script - Hills & Hollows LLC
Comprehensive exploration of SSCS Central Price Book for Tessa's automation

Focuses on:
1. CPB Vendor Import configuration
2. NAXML support validation
3. DTS automation options
4. Hills & Hollows inventory extraction

Author: DABS Automation System
Created: 2024-12-19
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page

# Load environment variables
load_dotenv()

class SSCSCPBDiscovery:
    """Comprehensive SSCS CPB discovery for Tessa's automation"""
    
    def __init__(self):
        self.username = os.getenv('SSCS_USERNAME')
        self.password = os.getenv('SSCS_PASSWORD')
        self.base_url = os.getenv('SSCS_LOGIN_URL')
        self.results_dir = Path('data/sscs_discovery')
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🔍 SSCS CPB Discovery for Tessa's Automation")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Goal: Extract all data needed for monthly price automation")
        print("=" * 60)
    
    async def login_to_sscs(self, page: Page) -> bool:
        """Login to SSCS with proven method"""
        try:
            print("🌐 Logging into SSCS...")
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # Fill login form
            await page.fill('input[name="username"]', self.username)
            await page.fill('input[name="password"]', self.password)
            await page.click('button:has-text("login")')
            
            # Wait for successful login
            await page.wait_for_url(lambda url: 'CStore.Web/CDB' in url, timeout=15000)
            print("✅ Successfully logged into SSCS CDB interface")
            return True
            
        except Exception as e:
            print(f"❌ Login failed: {str(e)}")
            return False
    
    async def discover_cpb_interface(self, page: Page) -> Dict:
        """Discover Central Price Book interface and capabilities"""
        print("\n🔍 Discovering CPB Interface...")
        
        try:
            # Look for price book or CPB navigation
            cpb_selectors = [
                'text=price book',
                'text=Price Book', 
                'text=central price',
                'text=Central Price',
                'text=CPB',
                'text=vendor',
                'text=Vendor'
            ]
            
            cpb_found = False
            for selector in cpb_selectors:
                try:
                    element = page.locator(selector)
                    if await element.is_visible():
                        print(f"🎯 Found CPB link: {selector}")
                        await element.click()
                        await page.wait_for_load_state('networkidle')
                        cpb_found = True
                        break
                except:
                    continue
            
            if not cpb_found:
                # Extract all navigation to find CPB
                all_links = await page.locator('a, button, .nav-item').all()
                nav_data = []
                
                for link in all_links[:50]:  # Limit for performance
                    try:
                        text = await link.text_content()
                        href = await link.get_attribute('href')
                        if text and text.strip():
                            nav_data.append({
                                'text': text.strip().lower(),
                                'href': href
                            })
                    except:
                        continue
                
                # Look for price/vendor related links
                price_links = [item for item in nav_data if any(word in item['text'] for word in ['price', 'vendor', 'import', 'book'])]
                
                print(f"💰 Price-related navigation found: {[item['text'] for item in price_links]}")
                
                return {
                    'cpb_direct_access': False,
                    'all_navigation': nav_data[:20],
                    'price_related_links': price_links
                }
            
            # If CPB found, explore vendor import options
            vendor_import_data = await self._explore_vendor_import(page)
            
            return {
                'cpb_direct_access': True,
                'vendor_import_data': vendor_import_data
            }
            
        except Exception as e:
            print(f"❌ CPB discovery error: {str(e)}")
            return {'error': str(e)}
    
    async def _explore_vendor_import(self, page: Page) -> Dict:
        """Explore vendor import functionality in CPB"""
        print("🔍 Exploring Vendor Import functionality...")
        
        try:
            # Look for vendor import, import, or file upload options
            import_selectors = [
                'text=vendor import',
                'text=Vendor Import',
                'text=import',
                'text=Import',
                'text=file',
                'text=File',
                'text=upload',
                'text=Upload'
            ]
            
            import_options = []
            for selector in import_selectors:
                try:
                    elements = await page.locator(selector).all()
                    for element in elements:
                        text = await element.text_content()
                        if text and text.strip():
                            import_options.append(text.strip())
                except:
                    continue
            
            print(f"📥 Import options found: {import_options}")
            
            # Look for NAXML or XML support
            page_content = await page.content()
            naxml_support = {
                'naxml_mentioned': 'naxml' in page_content.lower(),
                'xml_support': 'xml' in page_content.lower(),
                'itemsynch_support': 'itemsynch' in page_content.lower(),
                'itemprice_support': 'itemprice' in page_content.lower(),
                'mclane_profile': 'mclane' in page_content.lower()
            }
            
            print(f"🔧 NAXML support indicators: {naxml_support}")
            
            # Take screenshot of current interface
            await page.screenshot(path=str(self.results_dir / 'sscs_cpb_interface.png'))
            
            return {
                'import_options': import_options,
                'naxml_support': naxml_support,
                'current_url': page.url,
                'interface_screenshot': 'sscs_cpb_interface.png'
            }
            
        except Exception as e:
            print(f"❌ Vendor import exploration error: {str(e)}")
            return {'error': str(e)}
    
    async def discover_inventory_data(self, page: Page) -> Dict:
        """Discover Hills & Hollows inventory in SSCS"""
        print("\n📦 Discovering Inventory Data...")
        
        try:
            # Look for inventory, merchandise, or product navigation
            inventory_selectors = [
                'text=inventory',
                'text=Inventory',
                'text=merchandise', 
                'text=Merchandise',
                'text=products',
                'text=Products',
                'text=items',
                'text=Items'
            ]
            
            inventory_found = False
            for selector in inventory_selectors:
                try:
                    element = page.locator(selector)
                    if await element.is_visible():
                        print(f"📦 Found inventory link: {selector}")
                        await element.click()
                        await page.wait_for_load_state('networkidle')
                        inventory_found = True
                        break
                except:
                    continue
            
            if inventory_found:
                # Extract product data from current page
                inventory_data = await self._extract_product_table_data(page)
            else:
                # Try to find product data on current page
                inventory_data = await self._search_for_product_data(page)
            
            return inventory_data
            
        except Exception as e:
            print(f"❌ Inventory discovery error: {str(e)}")
            return {'error': str(e)}
    
    async def _extract_product_table_data(self, page: Page) -> Dict:
        """Extract product data from SSCS tables"""
        try:
            # Look for data tables
            table_data = await page.evaluate('''() => {
                const tables = document.querySelectorAll('table, .data-grid, .product-grid');
                const results = [];
                
                tables.forEach((table, tableIndex) => {
                    const rows = table.querySelectorAll('tr, .row');
                    const tableData = [];
                    
                    rows.forEach((row, rowIndex) => {
                        const cells = row.querySelectorAll('td, th, .cell');
                        const rowData = Array.from(cells).map(cell => cell.textContent.trim());
                        if (rowData.length > 0) {
                            tableData.push(rowData);
                        }
                    });
                    
                    if (tableData.length > 0) {
                        results.push({
                            table_index: tableIndex,
                            row_count: tableData.length,
                            column_count: tableData[0] ? tableData[0].length : 0,
                            sample_data: tableData.slice(0, 5)  // First 5 rows
                        });
                    }
                });
                
                return results;
            }''')
            
            print(f"📊 Tables found: {len(table_data)}")
            if table_data:
                for table in table_data:
                    print(f"   Table {table['table_index']}: {table['row_count']} rows, {table['column_count']} columns")
            
            return {
                'tables_found': len(table_data),
                'table_data': table_data,
                'page_url': page.url
            }
            
        except Exception as e:
            print(f"❌ Table extraction error: {str(e)}")
            return {'error': str(e)}
    
    async def _search_for_product_data(self, page: Page) -> Dict:
        """Search for product data on current page"""
        try:
            # Get page content and search for product indicators
            page_text = await page.evaluate('() => document.body.innerText')
            
            product_indicators = {
                'sku_count': page_text.lower().count('sku'),
                'product_count': page_text.lower().count('product'),
                'price_count': page_text.lower().count('price'),
                'inventory_count': page_text.lower().count('inventory')
            }
            
            print(f"🔍 Product indicators: {product_indicators}")
            
            return {
                'product_indicators': product_indicators,
                'page_text_length': len(page_text),
                'page_url': page.url
            }
            
        except Exception as e:
            print(f"❌ Product search error: {str(e)}")
            return {'error': str(e)}
    
    async def comprehensive_discovery(self):
        """Run comprehensive SSCS discovery for Tessa's automation"""
        
        discovery_results = {
            'discovery_timestamp': datetime.now().isoformat(),
            'purpose': 'Tessa monthly price automation',
            'sscs_access_url': self.base_url,
            'user': self.username
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=500)
            page = await browser.new_page()
            page.set_default_timeout(30000)
            
            try:
                # Step 1: Login to SSCS
                login_success = await self.login_to_sscs(page)
                if not login_success:
                    raise Exception("SSCS login failed")
                
                discovery_results['login_successful'] = True
                discovery_results['cdb_url'] = page.url
                
                # Step 2: Discover CPB interface
                cpb_data = await self.discover_cpb_interface(page)
                discovery_results['cpb_discovery'] = cpb_data
                
                # Step 3: Discover inventory data
                inventory_data = await self.discover_inventory_data(page)
                discovery_results['inventory_discovery'] = inventory_data
                
                # Step 4: Comprehensive navigation mapping
                await self._map_complete_navigation(page)
                
                # Save results
                results_file = self.results_dir / f'sscs_comprehensive_discovery_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                with open(results_file, 'w') as f:
                    json.dump(discovery_results, f, indent=2, default=str)
                
                print(f"\n📄 Complete discovery results saved: {results_file}")
                
                return discovery_results
                
            except Exception as e:
                print(f"❌ Discovery failed: {str(e)}")
                return {'error': str(e)}
            
            finally:
                await browser.close()
    
    async def _map_complete_navigation(self, page: Page):
        """Map complete SSCS navigation structure"""
        print("\n🗺️ Mapping complete SSCS navigation...")
        
        try:
            # Extract comprehensive navigation data
            nav_data = await page.evaluate('''() => {
                const navigation = {
                    links: [],
                    menus: [],
                    forms: [],
                    buttons: []
                };
                
                // Extract all links
                document.querySelectorAll('a').forEach(link => {
                    const text = link.textContent.trim();
                    const href = link.href;
                    if (text && href) {
                        navigation.links.push({ text, href });
                    }
                });
                
                // Extract menu items
                document.querySelectorAll('.menu-item, .nav-item, .dropdown-item').forEach(item => {
                    const text = item.textContent.trim();
                    if (text) {
                        navigation.menus.push({ text });
                    }
                });
                
                // Extract forms
                document.querySelectorAll('form').forEach((form, index) => {
                    const inputs = form.querySelectorAll('input, select, textarea');
                    navigation.forms.push({
                        form_index: index,
                        input_count: inputs.length,
                        action: form.action || 'no action'
                    });
                });
                
                // Extract buttons
                document.querySelectorAll('button').forEach(button => {
                    const text = button.textContent.trim();
                    if (text) {
                        navigation.buttons.push({ text });
                    }
                });
                
                return navigation;
            }''')
            
            # Save navigation map
            nav_file = self.results_dir / 'sscs_navigation_map.json'
            with open(nav_file, 'w') as f:
                json.dump(nav_data, f, indent=2)
            
            print(f"📊 Navigation mapped: {len(nav_data['links'])} links, {len(nav_data['menus'])} menu items")
            print(f"🔍 Price-related links: {[link['text'] for link in nav_data['links'] if any(word in link['text'].lower() for word in ['price', 'vendor', 'import'])]}")
            
        except Exception as e:
            print(f"❌ Navigation mapping error: {str(e)}")

async def main():
    """Main CPB discovery execution"""
    discovery = SSCSCPBDiscovery()
    results = await discovery.comprehensive_discovery()
    
    if 'error' not in results:
        print("\n🎉 SSCS CPB DISCOVERY SUCCESSFUL!")
        print("✅ Login validated and interface mapped")
        print("📊 CPB capabilities assessed")
        print("📦 Inventory data structure discovered")
        print("🔧 Ready to configure DABS vendor import")
        
        print(f"\n🎯 Key Findings for Tessa's Automation:")
        if 'cpb_discovery' in results:
            cpb = results['cpb_discovery']
            if cpb.get('cpb_direct_access'):
                print("✅ CPB interface accessible")
            else:
                print("⚠️ CPB interface needs navigation")
                
        print(f"\n📋 Next Steps:")
        print("1. ✅ SSCS access confirmed")
        print("2. 🔧 Configure DABS vendor profile in CPB")
        print("3. 📄 Test NAXML file upload")
        print("4. ⚡ Setup DTS automation")
        print("5. 🎊 Deploy Tessa's monthly automation")
        
    else:
        print("\n❌ SSCS CPB DISCOVERY FAILED")
        print(f"Error: {results.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
