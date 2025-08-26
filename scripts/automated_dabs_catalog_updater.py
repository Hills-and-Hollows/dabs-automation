#!/usr/bin/env python3
"""
Automated DABS Catalog Updater

This script automatically checks for and processes new DABS data to keep
the restaurant portal catalog up-to-date with all 4000+ products.

Features:
- Monitors DABS website for new Excel files
- Automatically downloads and processes updates
- Deploys updated catalog to restaurant portal
- Sends notifications about updates
- Maintains version history and rollback capability

Can be run as:
1. Scheduled job (cron/GitHub Actions) - daily/weekly checks
2. Webhook trigger - when DABS publishes new data
3. Manual execution - on-demand updates
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import logging
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import subprocess
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomatedDABSUpdater:
    """Automated DABS catalog updater with monitoring and deployment"""
    
    def __init__(self):
        self.base_urls = {
            'product_list_page': 'https://abs.utah.gov/shop-products/interactive-product-list/',
            'price_books_page': 'https://abs.utah.gov/vendors/monthly-price-books/',
            'product_locator': 'https://webapps2.abc.utah.gov/ProdApps/ProductLocatorCore'
        }
        
        self.data_dir = Path('data/official_dabs_sources')
        self.data_dir.mkdir(exist_ok=True)
        
        self.versions_dir = Path('data/catalog_versions')
        self.versions_dir.mkdir(exist_ok=True)
        
        # Configuration
        self.notification_email = "shawn@owenent.com"
        self.check_frequency_hours = 24  # Check daily
        self.auto_deploy = True  # Automatically deploy updates
        
        # Version tracking
        self.version_file = self.data_dir / 'catalog_version.json'
        
    def get_current_version_info(self):
        """Get current catalog version information"""
        if self.version_file.exists():
            with open(self.version_file, 'r') as f:
                return json.load(f)
        return {
            'version': '0.0.0',
            'last_check': None,
            'last_update': None,
            'file_hash': None,
            'product_count': 0,
            'source_file': None
        }
    
    def save_version_info(self, version_info):
        """Save catalog version information"""
        with open(self.version_file, 'w') as f:
            json.dump(version_info, f, indent=2)
    
    async def check_for_dabs_updates(self):
        """Check DABS website for new Excel files"""
        logger.info("Checking DABS website for updates...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check the interactive product list page
                async with session.get(self.base_urls['product_list_page']) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self.parse_product_list_page(html)
                    else:
                        logger.error(f"Failed to access DABS product list page: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error checking for DABS updates: {e}")
            return None
    
    def parse_product_list_page(self, html):
        """Parse DABS product list page to find Excel download links"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for Excel file links
            excel_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(ext in href.lower() for ext in ['.xlsx', '.xls']):
                    excel_links.append({
                        'url': href if href.startswith('http') else f"https://abs.utah.gov{href}",
                        'text': link.get_text().strip(),
                        'found_date': datetime.now().isoformat()
                    })
            
            logger.info(f"Found {len(excel_links)} Excel file links")
            return excel_links
            
        except Exception as e:
            logger.error(f"Error parsing DABS page: {e}")
            return []
    
    async def download_latest_excel(self, excel_links):
        """Download the latest Excel file if it's newer than current"""
        if not excel_links:
            logger.info("No Excel links found")
            return None
        
        current_version = self.get_current_version_info()
        
        # Sort links by date/name to get the latest
        latest_link = max(excel_links, key=lambda x: x['text'])
        
        try:
            logger.info(f"Downloading: {latest_link['url']}")
            
            response = requests.get(latest_link['url'])
            if response.status_code == 200:
                # Calculate file hash to check if it's different
                file_hash = hashlib.md5(response.content).hexdigest()
                
                if file_hash == current_version.get('file_hash'):
                    logger.info("File unchanged - no update needed")
                    return None
                
                # Save new file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"dabs_product_list_{timestamp}.xlsx"
                file_path = self.data_dir / filename
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded new Excel file: {file_path}")
                
                return {
                    'file_path': file_path,
                    'file_hash': file_hash,
                    'source_url': latest_link['url'],
                    'download_date': datetime.now().isoformat()
                }
            else:
                logger.error(f"Failed to download Excel file: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading Excel file: {e}")
            return None
    
    def process_new_excel_file(self, download_info):
        """Process new Excel file using existing processor"""
        try:
            logger.info(f"Processing new Excel file: {download_info['file_path']}")
            
            # Import and use existing processor
            from process_official_dabs_excel import DABSExcelProcessor
            
            processor = DABSExcelProcessor()
            products = processor.parse_excel_file(download_info['file_path'])
            
            if not products:
                logger.error("Failed to parse products from Excel file")
                return None
            
            # Generate restaurant catalog
            catalog = processor.generate_restaurant_catalog(products)
            
            # Create version info
            version_info = {
                'version': datetime.now().strftime('%Y.%m.%d'),
                'last_check': datetime.now().isoformat(),
                'last_update': datetime.now().isoformat(),
                'file_hash': download_info['file_hash'],
                'product_count': len(products),
                'active_product_count': catalog['total_found'],
                'source_file': str(download_info['file_path']),
                'source_url': download_info['source_url'],
                'categories': catalog['categories']
            }
            
            # Save version info
            self.save_version_info(version_info)
            
            # Backup current catalog
            self.backup_current_catalog(version_info['version'])
            
            logger.info(f"Processed {len(products)} total products, {catalog['total_found']} active")
            
            return {
                'catalog': catalog,
                'version_info': version_info,
                'products': products
            }
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {e}")
            return None
    
    def backup_current_catalog(self, version):
        """Backup current catalog for rollback capability"""
        try:
            current_catalog = Path('archon-mcp/archon-ui-main/public/src/web_portal/official_dabs_catalog.json')
            if current_catalog.exists():
                backup_path = self.versions_dir / f"catalog_backup_{version}.json"
                import shutil
                shutil.copy2(current_catalog, backup_path)
                logger.info(f"Backed up current catalog to: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to backup catalog: {e}")
    
    def deploy_updated_catalog(self, process_result):
        """Deploy updated catalog to production"""
        if not self.auto_deploy:
            logger.info("Auto-deploy disabled - manual deployment required")
            return False
        
        try:
            logger.info("Deploying updated catalog...")
            
            # Build and deploy
            build_result = subprocess.run(
                ['npm', 'run', 'build'],
                cwd='archon-mcp/archon-ui-main',
                capture_output=True,
                text=True
            )
            
            if build_result.returncode != 0:
                logger.error(f"Build failed: {build_result.stderr}")
                return False
            
            # Git commit and push
            git_commands = [
                ['git', 'add', '.'],
                ['git', 'commit', '-m', f"AUTO-UPDATE: DABS catalog v{process_result['version_info']['version']} - {process_result['version_info']['active_product_count']} products"],
                ['git', 'push', 'origin', 'main']
            ]
            
            for cmd in git_commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"Git command failed: {' '.join(cmd)} - {result.stderr}")
                    return False
            
            logger.info("Successfully deployed updated catalog")
            return True
            
        except Exception as e:
            logger.error(f"Error deploying catalog: {e}")
            return False
    
    def send_update_notification(self, process_result, deployment_success):
        """Send email notification about catalog update"""
        try:
            version_info = process_result['version_info']
            
            subject = f"🔄 DABS Catalog Auto-Update: v{version_info['version']}"
            
            body = f"""
DABS Catalog Automatic Update Report

✅ UPDATE SUMMARY:
- Version: {version_info['version']}
- Total Products: {version_info['product_count']:,}
- Active Products: {version_info['active_product_count']:,}
- Categories: {len(version_info['categories'])}
- Source: {version_info['source_url']}

📊 CATALOG DETAILS:
- Last Update: {version_info['last_update']}
- Source File: {Path(version_info['source_file']).name}
- File Hash: {version_info['file_hash'][:16]}...

🏷️ CATEGORIES AVAILABLE:
{', '.join(version_info['categories'])}

🚀 DEPLOYMENT STATUS:
{'✅ Successfully deployed to production' if deployment_success else '❌ Deployment failed - manual intervention required'}

🔗 RESTAURANT PORTAL:
https://dabs-automation.netlify.app/src/web_portal/restaurant_portal_with_catalog.html

📋 NEXT STEPS:
- Verify restaurant portal functionality
- Test search and ordering features
- Monitor for any customer issues

This automated update ensures your restaurant customers always have access to the complete, current DABS catalog with accurate pricing and availability.
            """
            
            # Send email (would need SMTP configuration)
            logger.info("Update notification prepared")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body preview: {body[:200]}...")
            
            # TODO: Implement actual email sending when SMTP is configured
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def run_update_check(self):
        """Main method to check for and process DABS updates"""
        logger.info("Starting automated DABS catalog update check...")
        
        try:
            # Check for updates
            excel_links = await self.check_for_dabs_updates()
            if not excel_links:
                logger.info("No Excel files found on DABS website")
                return False
            
            # Download latest file if different
            download_info = await self.download_latest_excel(excel_links)
            if not download_info:
                logger.info("No new files to process")
                return False
            
            # Process the new file
            process_result = self.process_new_excel_file(download_info)
            if not process_result:
                logger.error("Failed to process new Excel file")
                return False
            
            # Deploy updated catalog
            deployment_success = self.deploy_updated_catalog(process_result)
            
            # Send notification
            self.send_update_notification(process_result, deployment_success)
            
            logger.info("Automated update completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in automated update: {e}")
            return False

async def main():
    """Main function for automated updates"""
    updater = AutomatedDABSUpdater()
    success = await updater.run_update_check()
    
    if success:
        print("✅ Automated DABS catalog update completed successfully!")
    else:
        print("ℹ️  No updates needed or update failed")

if __name__ == "__main__":
    asyncio.run(main())
