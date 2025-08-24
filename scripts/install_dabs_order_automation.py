#!/usr/bin/env python3
"""
DABS Order Automation Installation and Setup Script
Hills & Hollows LLC - Utah Package Agency

Installs and configures complete DABS order automation system including:
- Python dependencies
- Chrome/ChromeDriver setup
- Directory structure validation
- Configuration validation
- Initial system testing

Author: DABS Automation System
Created: 2025-01-11
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DABS_INSTALL - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class DABSOrderAutomationInstaller:
    """Complete installation and setup system for DABS order automation"""
    
    def __init__(self):
        self.project_root = Path('/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory')
        self.requirements_file = self.project_root / 'requirements_dabs_orders.txt'
        
        logger.info("DABS Order Automation Installer initialized")
    
    async def validate_system_prerequisites(self) -> Dict[str, bool]:
        """Validate system prerequisites for DABS automation"""
        
        logger.info("Validating system prerequisites...")
        
        checks = {
            'python_version': False,
            'pip_available': False,
            'chrome_browser': False,
            'project_structure': False,
            'config_files': False,
            'write_permissions': False
        }
        
        try:
            # Check Python version (3.8+)
            python_version = sys.version_info
            if python_version.major == 3 and python_version.minor >= 8:
                checks['python_version'] = True
                logger.info(f"✅ Python {python_version.major}.{python_version.minor} detected")
            else:
                logger.error(f"❌ Python 3.8+ required, found {python_version.major}.{python_version.minor}")
            
            # Check pip availability
            try:
                subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                             capture_output=True, check=True)
                checks['pip_available'] = True
                logger.info("✅ pip available")
            except subprocess.CalledProcessError:
                logger.error("❌ pip not available")
            
            # Check Chrome browser
            chrome_paths = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '/usr/bin/google-chrome',
                '/usr/bin/chromium-browser'
            ]
            
            for chrome_path in chrome_paths:
                if Path(chrome_path).exists():
                    checks['chrome_browser'] = True
                    logger.info(f"✅ Chrome browser found: {chrome_path}")
                    break
            
            if not checks['chrome_browser']:
                logger.error("❌ Chrome browser not found")
            
            # Check project structure
            required_dirs = [
                'src/automation',
                'data/dabs_orders',
                'config',
                'logs'
            ]
            
            structure_valid = True
            for dir_path in required_dirs:
                full_path = self.project_root / dir_path
                if not full_path.exists():
                    full_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"📁 Created directory: {dir_path}")
                
                if full_path.exists():
                    logger.info(f"✅ Directory exists: {dir_path}")
                else:
                    structure_valid = False
                    logger.error(f"❌ Failed to create directory: {dir_path}")
            
            checks['project_structure'] = structure_valid
            
            # Check configuration files
            config_files = [
                'config/dabs_ordering.env',
                'config/secure_credentials.json'
            ]
            
            config_valid = True
            for config_file in config_files:
                config_path = self.project_root / config_file
                if config_path.exists():
                    logger.info(f"✅ Config file exists: {config_file}")
                else:
                    config_valid = False
                    logger.error(f"❌ Config file missing: {config_file}")
            
            checks['config_files'] = config_valid
            
            # Check write permissions
            try:
                test_file = self.project_root / 'data/test_write_permissions.tmp'
                test_file.write_text('test')
                test_file.unlink()
                checks['write_permissions'] = True
                logger.info("✅ Write permissions verified")
            except Exception as e:
                checks['write_permissions'] = False
                logger.error(f"❌ Write permissions failed: {e}")
            
        except Exception as e:
            logger.error(f"Prerequisites validation failed: {e}")
        
        return checks
    
    async def install_python_dependencies(self) -> bool:
        """Install required Python dependencies"""
        
        logger.info("Installing Python dependencies...")
        
        try:
            if not self.requirements_file.exists():
                logger.error("Requirements file not found")
                return False
            
            # Install requirements
            install_cmd = [
                sys.executable, '-m', 'pip', 'install', '-r', str(self.requirements_file)
            ]
            
            logger.info(f"Running: {' '.join(install_cmd)}")
            
            result = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("✅ Python dependencies installed successfully")
            logger.info(f"Installation output: {result.stdout}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Dependency installation failed: {e}")
            logger.error(f"Error output: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during installation: {e}")
            return False
    
    async def setup_chrome_driver(self) -> bool:
        """Setup ChromeDriver for automated browsing"""
        
        logger.info("Setting up ChromeDriver...")
        
        try:
            # Try to install webdriver-manager for automatic ChromeDriver management
            try:
                import webdriver_manager
                from selenium import webdriver
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                
                # Test ChromeDriver setup
                service = Service(ChromeDriverManager().install())
                options = webdriver.ChromeOptions()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                
                # Test driver creation
                driver = webdriver.Chrome(service=service, options=options)
                driver.get('https://www.google.com')
                driver.quit()
                
                logger.info("✅ ChromeDriver setup and tested successfully")
                return True
                
            except ImportError:
                logger.warning("webdriver-manager not available, manual ChromeDriver setup required")
                return False
                
        except Exception as e:
            logger.error(f"❌ ChromeDriver setup failed: {e}")
            return False
    
    async def validate_configuration(self) -> Dict[str, Any]:
        """Validate DABS automation configuration"""
        
        logger.info("Validating DABS automation configuration...")
        
        validation_result = {
            'config_valid': True,
            'missing_configs': [],
            'invalid_configs': [],
            'recommendations': []
        }
        
        # Check environment file
        env_file = self.project_root / 'config/dabs_ordering.env'
        if env_file.exists():
            env_content = env_file.read_text()
            
            required_vars = [
                'DABS_ORDERING_LOGIN_URL',
                'DABS_ORDERING_USERNAME', 
                'DABS_ORDERING_PASSWORD'
            ]
            
            for var in required_vars:
                if var not in env_content:
                    validation_result['missing_configs'].append(var)
                    validation_result['config_valid'] = False
                elif f'{var}=' in env_content and env_content.split(f'{var}=')[1].split('\n')[0].strip() == '':
                    validation_result['invalid_configs'].append(f"{var} is empty")
                    validation_result['config_valid'] = False
        else:
            validation_result['missing_configs'].append('dabs_ordering.env')
            validation_result['config_valid'] = False
        
        # Check secure credentials
        creds_file = self.project_root / 'config/secure_credentials.json'
        if creds_file.exists():
            try:
                with open(creds_file, 'r') as f:
                    creds = json.load(f)
                
                if 'dabs_ordering_system' not in creds.get('credentials', {}):
                    validation_result['missing_configs'].append('dabs_ordering_system in secure_credentials.json')
                    validation_result['config_valid'] = False
                
            except json.JSONDecodeError:
                validation_result['invalid_configs'].append('secure_credentials.json - invalid JSON')
                validation_result['config_valid'] = False
        else:
            validation_result['missing_configs'].append('secure_credentials.json')
            validation_result['config_valid'] = False
        
        # Generate recommendations
        if validation_result['missing_configs']:
            validation_result['recommendations'].append(
                "Create missing configuration files using provided templates"
            )
        
        if validation_result['invalid_configs']:
            validation_result['recommendations'].append(
                "Update configuration values with actual DABS credentials"
            )
        
        return validation_result
    
    async def run_system_test(self) -> Dict[str, Any]:
        """Run comprehensive system test for DABS automation"""
        
        logger.info("Running DABS automation system test...")
        
        test_result = {
            'test_date': datetime.now().isoformat(),
            'overall_success': True,
            'test_results': {},
            'performance_metrics': {},
            'recommendations': []
        }
        
        try:
            # Test 1: Configuration loading
            logger.info("Test 1: Configuration loading...")
            from src.automation.dabs_order_automation import DABSOrderAutomation
            
            automation = DABSOrderAutomation()
            test_result['test_results']['config_loading'] = True
            logger.info("✅ Configuration loading successful")
            
            # Test 2: Chrome driver initialization
            logger.info("Test 2: Chrome driver initialization...")
            from selenium import webdriver
            
            options = automation._setup_chrome_options()
            options.add_argument('--headless')  # Headless for testing
            
            driver = webdriver.Chrome(options=options)
            driver.get('https://www.google.com')
            driver.quit()
            
            test_result['test_results']['chrome_driver'] = True
            logger.info("✅ Chrome driver initialization successful")
            
            # Test 3: PDF processing capabilities
            logger.info("Test 3: PDF processing capabilities...")
            
            # Create test PDF content if sample exists
            test_pdf_path = self.project_root / 'dabs/Licensee Order_id_233811.pdf'
            if test_pdf_path.exists():
                analyzer = DABSInvoiceAnalyzer()
                pdf_text = await analyzer._extract_pdf_text(test_pdf_path)
                
                if pdf_text and len(pdf_text) > 100:
                    test_result['test_results']['pdf_processing'] = True
                    logger.info("✅ PDF processing successful")
                else:
                    test_result['test_results']['pdf_processing'] = False
                    logger.warning("⚠️ PDF processing returned minimal content")
            else:
                test_result['test_results']['pdf_processing'] = 'skipped_no_sample'
                logger.warning("⚠️ No sample PDF for testing")
            
            # Test 4: Data analysis capabilities
            logger.info("Test 4: Data analysis capabilities...")
            
            # Test DataFrame operations
            import pandas as pd
            test_df = pd.DataFrame({
                'order_id': ['233811', '233812'],
                'total_cost': [2508.06, 1234.56],
                'delivery_date': ['2025-08-22', '2025-08-23']
            })
            
            test_analysis = test_df['total_cost'].sum()
            if test_analysis > 0:
                test_result['test_results']['data_analysis'] = True
                logger.info("✅ Data analysis capabilities verified")
            
            # Test 5: File I/O operations
            logger.info("Test 5: File I/O operations...")
            
            test_file = self.project_root / 'data/dabs_orders/test_output.json'
            test_file.parent.mkdir(parents=True, exist_ok=True)
            
            test_data = {'test': 'data', 'timestamp': datetime.now().isoformat()}
            with open(test_file, 'w') as f:
                json.dump(test_data, f, indent=2)
            
            if test_file.exists():
                test_file.unlink()  # Clean up
                test_result['test_results']['file_operations'] = True
                logger.info("✅ File I/O operations successful")
            
        except Exception as e:
            logger.error(f"❌ System test failed: {e}")
            test_result['overall_success'] = False
            test_result['test_results']['error'] = str(e)
        
        # Generate recommendations based on test results
        failed_tests = [test for test, result in test_result['test_results'].items() 
                       if result is False]
        
        if failed_tests:
            test_result['overall_success'] = False
            test_result['recommendations'].append(
                f"Address failed tests: {', '.join(failed_tests)}"
            )
        
        if test_result['test_results'].get('chrome_driver') is False:
            test_result['recommendations'].append(
                "Install Chrome browser and ensure ChromeDriver compatibility"
            )
        
        return test_result
    
    async def generate_installation_summary(self, 
                                          prereq_check: Dict[str, bool],
                                          install_success: bool,
                                          driver_setup: bool,
                                          config_validation: Dict[str, Any],
                                          test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive installation summary"""
        
        summary = {
            'installation_date': datetime.now().isoformat(),
            'overall_status': 'SUCCESS' if all([
                all(prereq_check.values()),
                install_success,
                driver_setup,
                config_validation['config_valid'],
                test_results['overall_success']
            ]) else 'NEEDS_ATTENTION',
            'installation_steps': {
                'prerequisites': {
                    'status': 'PASSED' if all(prereq_check.values()) else 'FAILED',
                    'details': prereq_check
                },
                'dependencies': {
                    'status': 'PASSED' if install_success else 'FAILED'
                },
                'chrome_driver': {
                    'status': 'PASSED' if driver_setup else 'FAILED'
                },
                'configuration': {
                    'status': 'PASSED' if config_validation['config_valid'] else 'NEEDS_CONFIG',
                    'details': config_validation
                },
                'system_test': {
                    'status': 'PASSED' if test_results['overall_success'] else 'FAILED',
                    'details': test_results
                }
            },
            'next_steps': [],
            'automation_capabilities': {
                'ready_for_deployment': False,
                'capabilities': []
            }
        }
        
        # Generate next steps based on installation results
        if summary['overall_status'] == 'SUCCESS':
            summary['next_steps'] = [
                "✅ All systems ready - automation can be deployed",
                "🚀 Run test extraction: python src/automation/dabs_order_automation.py --extract --days 7",
                "📊 Run test analysis: python src/automation/dabs_invoice_analyzer.py --analyze",
                "⚙️ Setup scheduling: python src/automation/dabs_order_manager.py --setup",
                "📅 Deploy daily automation for immediate Tessa relief"
            ]
            
            summary['automation_capabilities'] = {
                'ready_for_deployment': True,
                'capabilities': [
                    'Automated DABS order data extraction',
                    'PDF invoice processing and analysis',
                    'Purchase pattern and price trend analysis',
                    'Automated reporting and notifications',
                    'Integration with existing DABS processing system'
                ]
            }
        else:
            # Generate specific fix recommendations
            if not all(prereq_check.values()):
                summary['next_steps'].append("🔧 Fix system prerequisites")
            
            if not install_success:
                summary['next_steps'].append("📦 Resolve dependency installation issues")
            
            if not driver_setup:
                summary['next_steps'].append("🌐 Install Chrome browser and setup ChromeDriver")
            
            if not config_validation['config_valid']:
                summary['next_steps'].append("⚙️ Complete configuration setup")
            
            if not test_results['overall_success']:
                summary['next_steps'].append("🧪 Address system test failures")
        
        return summary

async def run_complete_installation():
    """Run complete DABS order automation installation"""
    
    print("🚀 DABS Order Automation Installation System")
    print("=" * 60)
    print(f"📅 Installation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Goal: Complete DABS order automation setup")
    print()
    
    installer = DABSOrderAutomationInstaller()
    
    # Step 1: Validate prerequisites
    print("🔍 Step 1: Validating system prerequisites...")
    prereq_check = await installer.validate_system_prerequisites()
    
    for check, result in prereq_check.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {check}: {status}")
    
    # Step 2: Install dependencies
    print("\n📦 Step 2: Installing Python dependencies...")
    install_success = await installer.install_python_dependencies()
    
    if install_success:
        print("   ✅ Dependencies installed successfully")
    else:
        print("   ❌ Dependency installation failed")
    
    # Step 3: Setup Chrome driver
    print("\n🌐 Step 3: Setting up ChromeDriver...")
    driver_setup = await installer.setup_chrome_driver()
    
    if driver_setup:
        print("   ✅ ChromeDriver setup successful")
    else:
        print("   ⚠️ ChromeDriver setup needs manual configuration")
    
    # Step 4: Validate configuration
    print("\n⚙️ Step 4: Validating configuration...")
    config_validation = await installer.validate_configuration()
    
    if config_validation['config_valid']:
        print("   ✅ Configuration valid")
    else:
        print("   ❌ Configuration issues detected")
        for issue in config_validation['missing_configs'] + config_validation['invalid_configs']:
            print(f"      - {issue}")
    
    # Step 5: Run system test
    print("\n🧪 Step 5: Running system test...")
    test_results = await installer.run_system_test()
    
    if test_results['overall_success']:
        print("   ✅ All system tests passed")
    else:
        print("   ❌ System test issues detected")
        for test, result in test_results['test_results'].items():
            if result is False:
                print(f"      - {test}: FAILED")
    
    # Generate installation summary
    print("\n📋 Generating installation summary...")
    summary = await installer.generate_installation_summary(
        prereq_check, install_success, driver_setup, config_validation, test_results
    )
    
    # Save installation summary
    summary_file = installer.project_root / 'data/automation_results/dabs_order_automation_installation.json'
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Display final results
    print(f"\n🎊 INSTALLATION SUMMARY:")
    print(f"   Status: {summary['overall_status']}")
    print(f"   Ready for deployment: {summary['automation_capabilities']['ready_for_deployment']}")
    
    if summary['automation_capabilities']['capabilities']:
        print(f"\n🚀 AUTOMATION CAPABILITIES:")
        for capability in summary['automation_capabilities']['capabilities']:
            print(f"   ✅ {capability}")
    
    if summary['next_steps']:
        print(f"\n📋 NEXT STEPS:")
        for step in summary['next_steps']:
            print(f"   {step}")
    
    print(f"\n📄 Installation summary saved: {summary_file}")
    
    return summary['overall_status'] == 'SUCCESS'

async def main():
    """Main installation execution"""
    
    success = await run_complete_installation()
    
    if success:
        print(f"\n🎉 DABS ORDER AUTOMATION INSTALLATION COMPLETE!")
        print(f"🚀 System ready for automated order data extraction and analysis")
        print(f"💼 Tessa's purchase tracking is now fully automated!")
    else:
        print(f"\n⚠️ Installation completed with issues")
        print(f"🔧 Address the items listed above before deployment")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
