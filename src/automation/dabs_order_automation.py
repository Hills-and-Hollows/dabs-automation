#!/usr/bin/env python3
"""
DABS Licensee Order Automation System - Hills & Hollows LLC
Utah Package Agency Automated Order Data Extraction and Analysis

Automates:
- Login to DABS Licensee Ordering system
- Download historical order invoices and data
- Extract structured data from PDF invoices
- Analyze purchase patterns, pricing trends, and invoice tracking
- Generate reports for purchase tracking and price analysis

Author: DABS Automation System
Created: 2025-01-11
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal

import aiofiles
import aiohttp
import pandas as pd
import pdfplumber
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Load environment configuration
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DABS_ORDER_AUTO - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/logs/dabs_order_automation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class OrderLineItem:
    """Individual line item from a DABS order"""
    description: str
    item_code: str
    unit_price: Decimal
    quantity: int
    extended_price: Decimal
    category: Optional[str] = None

@dataclass
class DABSOrder:
    """Complete DABS order information"""
    order_id: str
    delivery_date: str
    sales_order: str
    store: str
    status: str
    reference: str
    line_items: List[OrderLineItem]
    total_quantities: int
    total_cost: Decimal
    pdf_file_path: Optional[str] = None
    extraction_timestamp: Optional[str] = None

class DABSOrderAutomation:
    """
    Complete automation system for DABS order data extraction and analysis
    
    Features:
    - Automated login to Utah DABS system
    - Historical order data extraction  
    - PDF invoice download and processing
    - Structured data extraction and analysis
    - Purchase tracking and price trend analysis
    """
    
    def __init__(self):
        # Load configuration
        self.config = self._load_config()
        self.project_root = Path('/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory')
        
        # Setup directories
        self.pdf_storage_dir = self.project_root / 'data/dabs_orders/pdfs'
        self.data_storage_dir = self.project_root / 'data/dabs_orders/extracted_data'
        self.analysis_dir = self.project_root / 'data/dabs_orders/analysis'
        
        for dir_path in [self.pdf_storage_dir, self.data_storage_dir, self.analysis_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize web driver configuration
        self.driver_options = self._setup_chrome_options()
        
        logger.info("DABS Order Automation System initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load DABS ordering configuration"""
        return {
            'login_url': os.getenv('DABS_ORDERING_LOGIN_URL', 'https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/'),
            'username': os.getenv('DABS_ORDERING_USERNAME', 'hillshollows'),
            'password': os.getenv('DABS_ORDERING_PASSWORD', 'Hills2025!@'),
            'orders_url': 'https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders/PrintSelectedOrders',
            'session_timeout': int(os.getenv('DABS_SESSION_TIMEOUT_MINUTES', '30')),
            'processing_batch_size': 50,
            'max_historical_days': 365,  # 1 year of historical data
            'pdf_download_timeout': 60,
            'retry_attempts': 3
        }
    
    def _setup_chrome_options(self) -> Options:
        """Configure Chrome options for automated browsing"""
        options = Options()
        
        # PDF download configuration
        prefs = {
            'download.default_directory': str(self.pdf_storage_dir),
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'plugins.always_open_pdf_externally': True,
            'profile.default_content_settings.popups': 0
        }
        
        options.add_experimental_option('prefs', prefs)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # For headless operation (uncomment for production)
        # options.add_argument('--headless')
        
        return options
    
    async def authenticate_and_login(self, driver: webdriver.Chrome) -> bool:
        """Authenticate to DABS ordering system"""
        
        try:
            logger.info(f"Logging in to DABS system: {self.config['login_url']}")
            
            # Navigate to login page
            driver.get(self.config['login_url'])
            
            # Wait for login form to load
            wait = WebDriverWait(driver, 20)
            
            # Find and fill username field
            username_field = wait.until(
                EC.presence_of_element_located((By.NAME, "UserName"))
            )
            username_field.clear()
            username_field.send_keys(self.config['username'])
            
            # Find and fill password field
            password_field = driver.find_element(By.NAME, "Password")
            password_field.clear()
            password_field.send_keys(self.config['password'])
            
            # Submit login form
            login_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
            login_button.click()
            
            # Wait for login success (check for dashboard elements)
            try:
                wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Order History")),
                        EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "New Order")),
                        EC.presence_of_element_located((By.CLASS_NAME, "order-panel"))
                    )
                )
                logger.info("Successfully logged in to DABS system")
                return True
                
            except TimeoutException:
                logger.error("Login failed - dashboard elements not found")
                return False
        
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    async def extract_order_history(self, driver: webdriver.Chrome, days_back: int = 365) -> List[Dict[str, Any]]:
        """Extract complete order history from DABS system"""
        
        try:
            logger.info(f"Extracting order history for last {days_back} days")
            
            # Navigate to order history
            driver.get("https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders")
            
            wait = WebDriverWait(driver, 15)
            
            # Set date filter for historical range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Wait for and configure date filters
            try:
                # Find date input fields (adjust selectors based on actual page structure)
                start_date_field = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='date'], input[name*='start'], input[name*='from']"))
                )
                start_date_field.clear()
                start_date_field.send_keys(start_date.strftime("%m/%d/%Y"))
                
                end_date_field = driver.find_element(By.CSS_SELECTOR, "input[type='date'], input[name*='end'], input[name*='to']")
                end_date_field.clear()
                end_date_field.send_keys(end_date.strftime("%m/%d/%Y"))
                
            except NoSuchElementException:
                logger.warning("Date filters not found - using default range")
            
            # Set status filter to "All"
            try:
                status_dropdown = driver.find_element(By.NAME, "status")
                Select(status_dropdown).select_by_visible_text("All")
            except NoSuchElementException:
                logger.warning("Status filter not found")
            
            # Set entries per page to maximum
            try:
                entries_dropdown = driver.find_element(By.NAME, "entries")
                Select(entries_dropdown).select_by_visible_text("100")
            except NoSuchElementException:
                logger.warning("Entries dropdown not found")
            
            # Apply filters
            try:
                search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                search_button.click()
                time.sleep(3)  # Allow filter to apply
            except NoSuchElementException:
                logger.warning("Search button not found")
            
            # Extract order data from table
            orders = []
            page_num = 1
            
            while True:
                logger.info(f"Extracting orders from page {page_num}")
                
                # Get order table
                try:
                    order_table = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "table, .order-table, .data-table"))
                    )
                    
                    # Extract rows
                    rows = order_table.find_elements(By.CSS_SELECTOR, "tbody tr, tr")
                    
                    for row in rows:
                        try:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 5:  # Minimum expected columns
                                
                                # Extract order information
                                order_data = {
                                    'order_id': cells[1].text.strip() if len(cells) > 1 else '',
                                    'sales_order': cells[2].text.strip() if len(cells) > 2 else '',
                                    'date_submitted': cells[3].text.strip() if len(cells) > 3 else '',
                                    'store': cells[4].text.strip() if len(cells) > 4 else '',
                                    'status': cells[5].text.strip() if len(cells) > 5 else '',
                                    'page_number': page_num,
                                    'extracted_at': datetime.now().isoformat()
                                }
                                
                                # Find view/print action button
                                try:
                                    view_button = row.find_element(By.CSS_SELECTOR, "a[href*='DisplayOrder'], button[onclick*='print'], .view-action")
                                    order_data['view_url'] = view_button.get_attribute('href') or view_button.get_attribute('onclick')
                                except NoSuchElementException:
                                    order_data['view_url'] = None
                                
                                orders.append(order_data)
                                
                        except Exception as e:
                            logger.warning(f"Error extracting row data: {e}")
                            continue
                
                except TimeoutException:
                    logger.warning("Order table not found on page")
                    break
                
                # Check for next page
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, "a[aria-label='Next'], .pagination-next, button[onclick*='next']")
                    if 'disabled' in next_button.get_attribute('class') or next_button.get_attribute('disabled'):
                        break
                    
                    next_button.click()
                    time.sleep(2)
                    page_num += 1
                    
                except NoSuchElementException:
                    logger.info("No more pages available")
                    break
            
            logger.info(f"Extracted {len(orders)} orders from {page_num} pages")
            return orders
            
        except Exception as e:
            logger.error(f"Order history extraction failed: {e}")
            return []
    
    async def download_order_pdfs(self, driver: webdriver.Chrome, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Download PDF invoices for extracted orders"""
        
        logger.info(f"Downloading PDFs for {len(orders)} orders")
        downloaded_orders = []
        
        for i, order in enumerate(orders):
            try:
                if not order.get('order_id'):
                    continue
                
                logger.info(f"Downloading PDF for Order ID: {order['order_id']} ({i+1}/{len(orders)})")
                
                # Construct PDF filename
                pdf_filename = f"Licensee_Order_id_{order['order_id']}.pdf"
                pdf_path = self.pdf_storage_dir / pdf_filename
                
                # Skip if already downloaded
                if pdf_path.exists():
                    logger.info(f"PDF already exists: {pdf_filename}")
                    order['pdf_path'] = str(pdf_path)
                    downloaded_orders.append(order)
                    continue
                
                # Navigate to order print page
                if order.get('view_url'):
                    # Extract order ID from URL if needed
                    order_id = order['order_id']
                    print_url = f"https://webapps2.abc.utah.gov/ProdApps/OnlineOrders/Orders/DisplayOrder/{order_id}"
                    
                    driver.get(print_url)
                    time.sleep(2)
                    
                    # Wait for page to load
                    wait = WebDriverWait(driver, 15)
                    try:
                        wait.until(
                            EC.any_of(
                                EC.presence_of_element_located((By.CLASS_NAME, "order-details")),
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".order-info, .invoice")),
                                EC.presence_of_element_located((By.XPATH, "//text()[contains(., 'Order Id')]"))
                            )
                        )
                    except TimeoutException:
                        logger.warning(f"Order page failed to load for {order_id}")
                        continue
                    
                    # Print to PDF using browser's print function
                    driver.execute_script("window.print();")
                    
                    # Wait for PDF to be generated and downloaded
                    pdf_wait_time = 0
                    while pdf_wait_time < self.config['pdf_download_timeout']:
                        if pdf_path.exists():
                            logger.info(f"PDF downloaded successfully: {pdf_filename}")
                            order['pdf_path'] = str(pdf_path)
                            downloaded_orders.append(order)
                            break
                        
                        time.sleep(1)
                        pdf_wait_time += 1
                    
                    if pdf_wait_time >= self.config['pdf_download_timeout']:
                        logger.warning(f"PDF download timeout for order {order_id}")
                
            except Exception as e:
                logger.error(f"Error downloading PDF for order {order.get('order_id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Downloaded {len(downloaded_orders)} PDFs successfully")
        return downloaded_orders
    
    async def extract_data_from_pdfs(self, orders_with_pdfs: List[Dict[str, Any]]) -> List[DABSOrder]:
        """Extract structured data from downloaded PDF invoices"""
        
        logger.info(f"Extracting data from {len(orders_with_pdfs)} PDF files")
        extracted_orders = []
        
        for order_info in orders_with_pdfs:
            try:
                pdf_path = Path(order_info.get('pdf_path', ''))
                if not pdf_path.exists():
                    continue
                
                logger.info(f"Processing PDF: {pdf_path.name}")
                
                # Extract text from PDF
                pdf_text = await self._extract_pdf_text(pdf_path)
                if not pdf_text:
                    logger.warning(f"No text extracted from {pdf_path.name}")
                    continue
                
                # Parse order data from text
                order_data = await self._parse_order_from_text(pdf_text, str(pdf_path))
                if order_data:
                    extracted_orders.append(order_data)
                    logger.info(f"Successfully extracted data for Order ID: {order_data.order_id}")
                
            except Exception as e:
                logger.error(f"Error processing PDF {order_info.get('pdf_path', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully extracted data from {len(extracted_orders)} PDFs")
        return extracted_orders
    
    async def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF using pdfplumber"""
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_content = []
                
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                
                return '\n'.join(text_content)
                
        except Exception as e:
            logger.error(f"PDF text extraction failed for {pdf_path.name}: {e}")
            return ""
    
    async def _parse_order_from_text(self, pdf_text: str, pdf_file_path: str) -> Optional[DABSOrder]:
        """Parse structured order data from PDF text"""
        
        try:
            # Extract order header information using regex patterns
            order_id_match = re.search(r'Order Id:\s*(\d+)', pdf_text)
            delivery_date_match = re.search(r'Delivery Date:\s*(\d{1,2}/\d{1,2}/\d{4})', pdf_text)
            sales_order_match = re.search(r'Sales Order:\s*(SOO\d+)', pdf_text)
            store_match = re.search(r'Store:\s*(\w+)', pdf_text)
            status_match = re.search(r'Status:\s*(\w+)', pdf_text)
            reference_match = re.search(r'Reference:\s*([^\n]*)', pdf_text)
            
            if not order_id_match:
                logger.warning("Order ID not found in PDF text")
                return None
            
            order_id = order_id_match.group(1)
            delivery_date = delivery_date_match.group(1) if delivery_date_match else ''
            sales_order = sales_order_match.group(1) if sales_order_match else ''
            store = store_match.group(1) if store_match else ''
            status = status_match.group(1) if status_match else ''
            reference = reference_match.group(1).strip() if reference_match else ''
            
            # Extract line items using regex
            line_items = []
            
            # Pattern for line items: Description - Item Code, Unit Price, Quantity, Extended Price
            line_pattern = r'([^-]+) - (\d+)\s+\$([0-9,]+\.\d{2})\s+(\d+)\s+\$([0-9,]+\.\d{2})'
            
            line_matches = re.findall(line_pattern, pdf_text)
            
            for match in line_matches:
                try:
                    description = match[0].strip()
                    item_code = match[1]
                    unit_price = Decimal(match[2].replace(',', ''))
                    quantity = int(match[3])
                    extended_price = Decimal(match[4].replace(',', ''))
                    
                    line_item = OrderLineItem(
                        description=description,
                        item_code=item_code,
                        unit_price=unit_price,
                        quantity=quantity,
                        extended_price=extended_price
                    )
                    
                    line_items.append(line_item)
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing line item: {e}")
                    continue
            
            # Extract totals
            total_qty_match = re.search(r'Total Quantities:\s*(\d+)', pdf_text)
            total_cost_match = re.search(r'Total Cost:\s*\$([0-9,]+\.\d{2})', pdf_text)
            
            total_quantities = int(total_qty_match.group(1)) if total_qty_match else len(line_items)
            total_cost = Decimal(total_cost_match.group(1).replace(',', '')) if total_cost_match else Decimal('0.00')
            
            # Create DABSOrder object
            order = DABSOrder(
                order_id=order_id,
                delivery_date=delivery_date,
                sales_order=sales_order,
                store=store,
                status=status,
                reference=reference,
                line_items=line_items,
                total_quantities=total_quantities,
                total_cost=total_cost,
                pdf_file_path=pdf_file_path,
                extraction_timestamp=datetime.now().isoformat()
            )
            
            logger.info(f"Successfully parsed order {order_id} with {len(line_items)} line items")
            return order
            
        except Exception as e:
            logger.error(f"Error parsing order from PDF text: {e}")
            return None
    
    async def analyze_purchase_patterns(self, orders: List[DABSOrder]) -> Dict[str, Any]:
        """Analyze purchase patterns and pricing trends from extracted orders"""
        
        logger.info(f"Analyzing purchase patterns from {len(orders)} orders")
        
        # Convert to DataFrame for analysis
        order_records = []
        line_item_records = []
        
        for order in orders:
            # Order-level data
            order_record = {
                'order_id': order.order_id,
                'delivery_date': order.delivery_date,
                'sales_order': order.sales_order,
                'store': order.store,
                'status': order.status,
                'total_quantities': order.total_quantities,
                'total_cost': float(order.total_cost),
                'extraction_timestamp': order.extraction_timestamp
            }
            order_records.append(order_record)
            
            # Line item data
            for item in order.line_items:
                line_item_record = {
                    'order_id': order.order_id,
                    'delivery_date': order.delivery_date,
                    'item_code': item.item_code,
                    'description': item.description,
                    'unit_price': float(item.unit_price),
                    'quantity': item.quantity,
                    'extended_price': float(item.extended_price)
                }
                line_item_records.append(line_item_record)
        
        orders_df = pd.DataFrame(order_records)
        items_df = pd.DataFrame(line_item_records)
        
        # Perform analysis
        analysis = {
            'analysis_date': datetime.now().isoformat(),
            'total_orders': len(orders),
            'date_range': {
                'earliest': orders_df['delivery_date'].min() if not orders_df.empty else None,
                'latest': orders_df['delivery_date'].max() if not orders_df.empty else None
            },
            'order_summary': {
                'total_value': float(orders_df['total_cost'].sum()) if not orders_df.empty else 0,
                'avg_order_value': float(orders_df['total_cost'].mean()) if not orders_df.empty else 0,
                'total_items_ordered': int(orders_df['total_quantities'].sum()) if not orders_df.empty else 0,
                'avg_items_per_order': float(orders_df['total_quantities'].mean()) if not orders_df.empty else 0
            },
            'product_analysis': {},
            'pricing_trends': {},
            'purchase_frequency': {}
        }
        
        if not items_df.empty:
            # Product analysis
            product_stats = items_df.groupby('item_code').agg({
                'description': 'first',
                'unit_price': ['mean', 'min', 'max'],
                'quantity': 'sum',
                'extended_price': 'sum'
            }).round(2)
            
            analysis['product_analysis'] = {
                'top_products_by_quantity': product_stats.nlargest(10, ('quantity', 'sum')).to_dict(),
                'top_products_by_value': product_stats.nlargest(10, ('extended_price', 'sum')).to_dict(),
                'price_variance_products': product_stats[
                    (product_stats[('unit_price', 'max')] - product_stats[('unit_price', 'min')]) > 10
                ].to_dict()
            }
            
            # Purchase frequency analysis
            analysis['purchase_frequency'] = {
                'unique_products': len(items_df['item_code'].unique()),
                'repeat_purchases': len(items_df[items_df.duplicated('item_code', keep=False)]['item_code'].unique()),
                'single_purchase_items': len(items_df) - len(items_df[items_df.duplicated('item_code', keep=False)])
            }
        
        return analysis
    
    async def save_extracted_data(self, orders: List[DABSOrder], analysis: Dict[str, Any]) -> Dict[str, str]:
        """Save extracted order data and analysis results"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw order data
        orders_file = self.data_storage_dir / f"dabs_orders_{timestamp}.json"
        orders_data = [asdict(order) for order in orders]
        
        # Convert Decimal to float for JSON serialization
        for order_data in orders_data:
            order_data['total_cost'] = float(order_data['total_cost'])
            for item in order_data['line_items']:
                item['unit_price'] = float(item['unit_price'])
                item['extended_price'] = float(item['extended_price'])
        
        async with aiofiles.open(orders_file, 'w') as f:
            await f.write(json.dumps(orders_data, indent=2))
        
        # Save analysis results
        analysis_file = self.analysis_dir / f"purchase_analysis_{timestamp}.json"
        async with aiofiles.open(analysis_file, 'w') as f:
            await f.write(json.dumps(analysis, indent=2))
        
        # Save CSV for easy Excel analysis
        if orders:
            # Orders summary CSV
            orders_summary = []
            for order in orders:
                orders_summary.append({
                    'Order_ID': order.order_id,
                    'Delivery_Date': order.delivery_date,
                    'Sales_Order': order.sales_order,
                    'Store': order.store,
                    'Status': order.status,
                    'Total_Quantities': order.total_quantities,
                    'Total_Cost': float(order.total_cost),
                    'Line_Items_Count': len(order.line_items)
                })
            
            orders_csv = self.analysis_dir / f"orders_summary_{timestamp}.csv"
            pd.DataFrame(orders_summary).to_csv(orders_csv, index=False)
            
            # Line items detail CSV
            line_items_detail = []
            for order in orders:
                for item in order.line_items:
                    line_items_detail.append({
                        'Order_ID': order.order_id,
                        'Delivery_Date': order.delivery_date,
                        'Item_Code': item.item_code,
                        'Description': item.description,
                        'Unit_Price': float(item.unit_price),
                        'Quantity': item.quantity,
                        'Extended_Price': float(item.extended_price),
                        'Sales_Order': order.sales_order,
                        'Status': order.status
                    })
            
            items_csv = self.analysis_dir / f"line_items_detail_{timestamp}.csv"
            pd.DataFrame(line_items_detail).to_csv(items_csv, index=False)
            
            logger.info(f"Data export completed: {len(orders)} orders, {len(line_items_detail)} line items")
        
        return {
            'orders_json': str(orders_file),
            'analysis_json': str(analysis_file),
            'orders_csv': str(orders_csv) if orders else None,
            'items_csv': str(items_csv) if orders else None
        }
    
    async def run_complete_automation(self, days_back: int = 90) -> Dict[str, Any]:
        """Execute complete DABS order automation workflow"""
        
        start_time = datetime.now()
        logger.info(f"Starting complete DABS order automation - {days_back} days historical data")
        
        automation_result = {
            'automation_start': start_time.isoformat(),
            'status': 'running',
            'orders_extracted': 0,
            'pdfs_downloaded': 0,
            'data_files_created': [],
            'errors': [],
            'performance_metrics': {}
        }
        
        driver = None
        
        try:
            # Initialize Chrome driver
            logger.info("Initializing Chrome driver...")
            driver = webdriver.Chrome(options=self.driver_options)
            driver.set_page_load_timeout(30)
            
            # Step 1: Authenticate
            logger.info("Step 1: Authenticating to DABS system...")
            auth_success = await self.authenticate_and_login(driver)
            if not auth_success:
                raise Exception("Authentication failed")
            
            # Step 2: Extract order history
            logger.info("Step 2: Extracting order history...")
            orders = await self.extract_order_history(driver, days_back)
            automation_result['orders_extracted'] = len(orders)
            
            if not orders:
                logger.warning("No orders found in specified date range")
                automation_result['status'] = 'completed_no_data'
                return automation_result
            
            # Step 3: Download PDFs
            logger.info("Step 3: Downloading order PDFs...")
            orders_with_pdfs = await self.download_order_pdfs(driver, orders)
            automation_result['pdfs_downloaded'] = len(orders_with_pdfs)
            
            # Step 4: Extract structured data
            logger.info("Step 4: Extracting structured data from PDFs...")
            extracted_orders = await self.extract_data_from_pdfs(orders_with_pdfs)
            
            # Step 5: Analyze purchase patterns
            logger.info("Step 5: Analyzing purchase patterns...")
            analysis = await self.analyze_purchase_patterns(extracted_orders)
            
            # Step 6: Save all data
            logger.info("Step 6: Saving extracted data and analysis...")
            saved_files = await self.save_extracted_data(extracted_orders, analysis)
            automation_result['data_files_created'] = list(saved_files.values())
            
            # Calculate performance metrics
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            automation_result['performance_metrics'] = {
                'total_duration_seconds': total_duration,
                'total_duration_minutes': round(total_duration / 60, 2),
                'orders_per_minute': round(len(extracted_orders) / (total_duration / 60), 2),
                'avg_pdf_processing_time': round(total_duration / max(len(orders_with_pdfs), 1), 2)
            }
            
            automation_result['status'] = 'completed_success'
            automation_result['completion_time'] = end_time.isoformat()
            
            logger.info(f"DABS order automation completed successfully in {automation_result['performance_metrics']['total_duration_minutes']} minutes")
            
        except Exception as e:
            logger.error(f"DABS order automation failed: {e}")
            automation_result['status'] = 'failed'
            automation_result['errors'].append(str(e))
            
        finally:
            if driver:
                driver.quit()
        
        return automation_result
    
    async def schedule_regular_extraction(self) -> Dict[str, Any]:
        """Setup regular scheduled extraction of DABS order data"""
        
        schedule_config = {
            'workflow_name': 'DABS Order Data Extraction',
            'schedule': 'Daily at 2:00 AM',
            'cron_expression': '0 2 * * *',
            'script_path': 'src/automation/dabs_order_automation.py',
            'parameters': {
                'days_back': 7,  # Daily incremental updates
                'notification_email': 'tessa@hillshollows.com'
            },
            'performance_targets': {
                'max_duration_minutes': 30,
                'min_success_rate': 95,
                'max_error_rate': 5
            },
            'integration': {
                'triggers_price_analysis': True,
                'updates_inventory_tracking': True,
                'feeds_compliance_reporting': True
            }
        }
        
        # Save schedule configuration
        schedule_file = self.project_root / 'config/dabs_order_automation_schedule.json'
        async with aiofiles.open(schedule_file, 'w') as f:
            await f.write(json.dumps(schedule_config, indent=2))
        
        logger.info(f"Regular extraction schedule configured: {schedule_file}")
        return schedule_config

async def run_manual_extraction(days_back: int = 90):
    """Manual execution of DABS order extraction"""
    
    print(f"🚀 DABS Order Automation - Manual Execution")
    print(f"📅 Extracting {days_back} days of historical data")
    print("=" * 60)
    
    automation = DABSOrderAutomation()
    result = await automation.run_complete_automation(days_back)
    
    print(f"\n📊 AUTOMATION RESULTS:")
    print(f"   Status: {result['status']}")
    print(f"   Orders extracted: {result['orders_extracted']}")
    print(f"   PDFs downloaded: {result['pdfs_downloaded']}")
    print(f"   Duration: {result.get('performance_metrics', {}).get('total_duration_minutes', 0)} minutes")
    
    if result['data_files_created']:
        print(f"\n📁 DATA FILES CREATED:")
        for file_path in result['data_files_created']:
            if file_path:
                print(f"   ✅ {Path(file_path).name}")
    
    if result['errors']:
        print(f"\n❌ ERRORS:")
        for error in result['errors']:
            print(f"   {error}")
    
    return result['status'] == 'completed_success'

async def setup_automated_schedule():
    """Setup automated scheduling for regular data extraction"""
    
    automation = DABSOrderAutomation()
    schedule_config = await automation.schedule_regular_extraction()
    
    print(f"✅ Automated schedule configured:")
    print(f"   Schedule: {schedule_config['schedule']}")
    print(f"   Cron: {schedule_config['cron_expression']}")
    print(f"   Target duration: ≤{schedule_config['performance_targets']['max_duration_minutes']} minutes")

async def main():
    """Main execution with options"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='DABS Order Automation System')
    parser.add_argument('--days', type=int, default=90, help='Days of historical data to extract')
    parser.add_argument('--schedule', action='store_true', help='Setup automated scheduling')
    parser.add_argument('--extract', action='store_true', help='Run manual extraction')
    
    args = parser.parse_args()
    
    if args.schedule:
        await setup_automated_schedule()
    elif args.extract:
        success = await run_manual_extraction(args.days)
        return success
    else:
        # Default: run extraction
        success = await run_manual_extraction(args.days)
        return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit_code = 0 if success else 1
    sys.exit(exit_code)
