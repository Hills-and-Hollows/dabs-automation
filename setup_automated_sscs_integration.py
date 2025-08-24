#!/usr/bin/env python3
"""
Automated SSCS Integration Setup
Configures automated EDI file drop integration after manual CPB test success

This script sets up the production automation that will run monthly
to process DABS files and automatically upload to SSCS via EDI directory.
"""
import sys
sys.path.append('./src')

import asyncio
import json
from pathlib import Path
from datetime import datetime
import shutil
from processors.dabs_processor import DABSProcessor
from processors.sscs_integration import create_sscs_integrator

class AutomatedSSCSIntegration:
    def __init__(self, edi_directory_path: str):
        self.edi_directory = Path(edi_directory_path)
        self.processor = DABSProcessor()
        self.export_dir = Path("exports")
        self.cpb_dir = Path("exports/sscs_cpb")
        
        # Ensure directories exist
        self.cpb_dir.mkdir(parents=True, exist_ok=True)
        
    async def setup_automation(self):
        """Set up complete DABS to SSCS automation workflow"""
        print("🤖 SETTING UP AUTOMATED SSCS INTEGRATION")
        print("=" * 50)
        
        print("📋 Configuration:")
        print(f"   📁 EDI Directory: {self.edi_directory}")
        print(f"   📁 Export Directory: {self.export_dir}")
        print(f"   📁 CPB Staging: {self.cpb_dir}")
        
        # Create automation configuration
        config = {
            "integration_type": "automated_edi_drop",
            "edi_directory": str(self.edi_directory),
            "file_naming": "DABS_{timestamp}_ItemPrice.xml",
            "processing_schedule": "monthly",
            "schedule_day": 25,
            "schedule_time": "03:00",
            "validation_enabled": True,
            "backup_enabled": True,
            "notifications_enabled": True
        }
        
        config_file = Path("config/sscs_automation_config.json")
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Configuration saved: {config_file}")
        
        return config
    
    async def test_edi_integration(self, test_file_path: str):
        """Test EDI directory integration with existing NAXML file"""
        print("\n🧪 TESTING EDI INTEGRATION")
        print("=" * 30)
        
        test_file = Path(test_file_path)
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return False
            
        print(f"📁 Test File: {test_file}")
        print(f"📊 File Size: {test_file.stat().st_size:,} bytes")
        
        # Create timestamp-based filename for EDI drop
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        edi_filename = f"DABS_{timestamp}_ItemPrice.xml"
        edi_target = self.edi_directory / edi_filename
        
        try:
            # Simulate EDI directory drop
            print(f"📤 Simulating EDI drop: {edi_target}")
            
            # For testing, copy to CPB directory (simulates EDI drop)
            test_target = self.cpb_dir / edi_filename
            shutil.copy2(test_file, test_target)
            
            print(f"✅ EDI simulation successful: {test_target}")
            print("⚠️  ACTUAL EDI: Replace simulation with real EDI path after manual test")
            
            return True
            
        except Exception as e:
            print(f"❌ EDI simulation failed: {e}")
            return False
    
    async def create_monthly_automation_script(self):
        """Create the monthly automation script for cron/scheduler"""
        
        automation_script = '''#!/usr/bin/env python3
"""
DABS Monthly Automation Script
Runs on 25th of each month at 3:00 AM

Processes latest DABS file and uploads to SSCS via EDI directory
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append('/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/src')

from processors.dabs_processor import DABSProcessor
import json
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/logs/monthly_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def run_monthly_automation():
    """Run complete monthly DABS automation"""
    logger.info("🚀 Starting monthly DABS automation")
    
    try:
        # Load configuration
        with open('/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/config/sscs_automation_config.json', 'r') as f:
            config = json.load(f)
        
        edi_directory = Path(config['edi_directory'])
        
        # Initialize processor
        processor = DABSProcessor()
        
        # Find latest DABS file
        dabs_files = list(Path('.').glob('DABS*.xlsx'))
        if not dabs_files:
            logger.error("❌ No DABS Excel files found")
            return False
            
        latest_dabs = max(dabs_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"📁 Processing file: {latest_dabs}")
        
        # Process DABS file
        result = await processor.process_dabs_file(latest_dabs)
        
        if not result.success:
            logger.error(f"❌ DABS processing failed: {result.errors}")
            return False
            
        logger.info(f"✅ DABS processing complete: {result.processed_skus} SKUs in {result.processing_time:.2f}s")
        
        # Find generated NAXML file
        naxml_files = [f for f in result.output_files if f.endswith('.xml') and 'itemsynch' in f.lower()]
        if not naxml_files:
            logger.error("❌ No NAXML file generated")
            return False
            
        naxml_file = Path(naxml_files[0])
        
        # Copy to EDI directory with proper naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        edi_filename = f"DABS_{timestamp}_ItemPrice.xml"
        edi_target = edi_directory / edi_filename
        
        shutil.copy2(naxml_file, edi_target)
        logger.info(f"✅ File uploaded to EDI: {edi_target}")
        
        # Send success notification (implement as needed)
        logger.info("🎉 Monthly DABS automation completed successfully")
        logger.info(f"📊 Results: {result.processed_skus} SKUs processed and uploaded")
        
        return True
        
    except Exception as e:
        logger.error(f"💥 Monthly automation failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_monthly_automation())
    exit(0 if success else 1)
'''
        
        script_file = Path("scripts/monthly_dabs_automation.py")
        script_file.parent.mkdir(exist_ok=True)
        
        with open(script_file, 'w') as f:
            f.write(automation_script)
        
        # Make executable
        script_file.chmod(0o755)
        
        print(f"✅ Monthly automation script created: {script_file}")
        return script_file
    
    async def create_cron_schedule(self):
        """Create cron schedule for monthly automation"""
        
        cron_entry = """# DABS Monthly Automation - Hills & Hollows LLC
# Runs 25th of each month at 3:00 AM
# Processes DABS files and uploads to SSCS via EDI

0 3 25 * * /usr/bin/python3 "/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/scripts/monthly_dabs_automation.py" >> "/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/logs/cron.log" 2>&1
"""
        
        cron_file = Path("config/dabs_monthly_cron.txt")
        with open(cron_file, 'w') as f:
            f.write(cron_entry)
            
        print(f"✅ Cron schedule created: {cron_file}")
        print("📋 To install: crontab -e and add the entry from this file")
        
        return cron_file

async def main():
    """Main setup function"""
    print("🚀 AUTOMATED SSCS INTEGRATION SETUP")
    print("=" * 50)
    print()
    print("⚠️  IMPORTANT: Run this AFTER successful manual CPB test")
    print("📋 This script prepares automation for production deployment")
    print()
    
    # Placeholder EDI directory (update after manual test)
    edi_directory = input("📁 Enter SSCS EDI directory path (from manual test): ").strip()
    if not edi_directory:
        edi_directory = "/tmp/sscs_edi_placeholder"  # Placeholder
        print(f"⚠️  Using placeholder: {edi_directory}")
        print("   Update after discovering real EDI path in manual test")
    
    # Set up automation
    automation = AutomatedSSCSIntegration(edi_directory)
    
    # Configure automation
    config = await automation.setup_automation()
    print("✅ Automation configuration complete")
    
    # Test with existing file
    test_file = "exports/sscs_cpb/DABS_20250822_ItemPrice.xml"
    if Path(test_file).exists():
        await automation.test_edi_integration(test_file)
    
    # Create automation scripts
    await automation.create_monthly_automation_script()
    await automation.create_cron_schedule()
    
    print()
    print("🎊 AUTOMATION SETUP COMPLETE!")
    print("=" * 30)
    print("✅ Configuration files created")
    print("✅ Monthly automation script ready")  
    print("✅ Cron schedule prepared")
    print("⚠️  NEXT: Update EDI path after manual test")
    print("🚀 READY: Full automation after manual CPB test success")

if __name__ == "__main__":
    asyncio.run(main())
