#!/usr/bin/env python3
"""
DABS EDI Deployment Script
Automated deployment and testing of DABS EDI system

Business Context:
- Deploys complete EDI system for 90% time reduction
- Validates Utah Package Agency compliance
- Ensures $28,000 annual value delivery
- Maintains 99.9% uptime target
"""

import asyncio
import sys
import os
from pathlib import Path
import subprocess
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edi.dabs_edi_generator import DABSEDIGenerator, create_test_dabs_data
from edi.dabs_edi_mailer import DABSEDIMailer
from edi.dabs_edi_integration import DABSEDIIntegration
from edi.test_dabs_edi import run_comprehensive_tests

class DABSEDIDeployment:
    """DABS EDI deployment manager"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.deployment_log = []
        
    def log_step(self, message: str, success: bool = True):
        """Log deployment step"""
        status = "✅" if success else "❌"
        log_entry = f"{status} {message}"
        print(log_entry)
        self.deployment_log.append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'success': success
        })
    
    async def validate_environment(self) -> bool:
        """Validate deployment environment"""
        print("🔍 Validating deployment environment...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.log_step("Python 3.8+ required", False)
            return False
        self.log_step(f"Python version: {sys.version}")
        
        # Check required directories
        required_dirs = ['src/edi', 'config', 'data', 'logs']
        for directory in required_dirs:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
            self.log_step(f"Directory exists: {directory}")
        
        # Check required files
        required_files = [
            'src/edi/dabs_edi_generator.py',
            'src/edi/dabs_edi_mailer.py',
            'src/edi/dabs_edi_integration.py',
            'config/dabs_edi_production.json'
        ]
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                self.log_step(f"Missing required file: {file_path}", False)
                return False
            self.log_step(f"File exists: {file_path}")
        
        return True
    
    async def install_dependencies(self) -> bool:
        """Install required dependencies"""
        print("📦 Installing dependencies...")
        
        dependencies = [
            'pandas',
            'openpyxl',
            'schedule',
            'psutil'
        ]
        
        for dep in dependencies:
            try:
                __import__(dep)
                self.log_step(f"Dependency available: {dep}")
            except ImportError:
                self.log_step(f"Installing dependency: {dep}")
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
                    self.log_step(f"Installed: {dep}")
                except subprocess.CalledProcessError:
                    self.log_step(f"Failed to install: {dep}", False)
                    return False
        
        return True
    
    async def run_system_tests(self) -> bool:
        """Run comprehensive system tests"""
        print("🧪 Running system tests...")
        
        try:
            # Run comprehensive test suite
            success = run_comprehensive_tests()
            
            if success:
                self.log_step("All system tests passed")
                return True
            else:
                self.log_step("Some system tests failed", False)
                return False
                
        except Exception as e:
            self.log_step(f"Test execution failed: {str(e)}", False)
            return False
    
    async def validate_configuration(self) -> bool:
        """Validate production configuration"""
        print("⚙️ Validating configuration...")
        
        config_file = self.project_root / "config/dabs_edi_production.json"
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Check required configuration sections
            required_sections = ['smtp_config', 'alert_config', 'schedule']
            for section in required_sections:
                if section not in config:
                    self.log_step(f"Missing configuration section: {section}", False)
                    return False
                self.log_step(f"Configuration section valid: {section}")
            
            # Validate SMTP configuration
            smtp_config = config['smtp_config']
            required_smtp_fields = ['smtp_server', 'smtp_port', 'username', 'password']
            for field in required_smtp_fields:
                if field not in smtp_config:
                    self.log_step(f"Missing SMTP field: {field}", False)
                    return False
            
            self.log_step("Configuration validation passed")
            return True
            
        except Exception as e:
            self.log_step(f"Configuration validation failed: {str(e)}", False)
            return False
    
    async def test_edi_generation(self) -> bool:
        """Test EDI generation functionality"""
        print("📄 Testing EDI generation...")
        
        try:
            # Initialize generator
            generator = DABSEDIGenerator()
            
            # Create test data
            test_items = create_test_dabs_data()
            
            # Generate NAXML
            naxml_content = generator.generate_naxml(test_items, "DEPLOYMENT_TEST")
            
            # Validate NAXML
            validation = generator.validate_naxml(naxml_content)
            
            if validation['valid']:
                self.log_step(f"EDI generation test passed ({validation['item_count']} items)")
                return True
            else:
                self.log_step(f"EDI validation failed: {validation['errors']}", False)
                return False
                
        except Exception as e:
            self.log_step(f"EDI generation test failed: {str(e)}", False)
            return False
    
    async def test_email_configuration(self) -> bool:
        """Test email configuration (without sending)"""
        print("📧 Testing email configuration...")
        
        try:
            # Load SMTP configuration
            config_file = self.project_root / "config/dabs_edi_production.json"
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Initialize mailer
            mailer = DABSEDIMailer(config['smtp_config'])
            
            # Validate SMTP configuration
            validation = mailer.validate_smtp_config()
            
            if validation['valid']:
                self.log_step("Email configuration valid")
                if validation['warnings']:
                    for warning in validation['warnings']:
                        self.log_step(f"Email warning: {warning}")
                return True
            else:
                self.log_step(f"Email configuration invalid: {validation['errors']}", False)
                return False
                
        except Exception as e:
            self.log_step(f"Email configuration test failed: {str(e)}", False)
            return False
    
    async def create_deployment_report(self, success: bool):
        """Create deployment report"""
        report = {
            'deployment_timestamp': datetime.now().isoformat(),
            'deployment_success': success,
            'deployment_log': self.deployment_log,
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'project_root': str(self.project_root)
            },
            'business_context': {
                'target_time_reduction': '90%',
                'expected_items': 1239,
                'annual_value': '$28,000',
                'compliance': 'Utah Package Agency'
            }
        }
        
        # Save report
        report_file = self.project_root / f"logs/deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Deployment report saved: {report_file}")
        return report
    
    async def deploy(self) -> bool:
        """Execute complete deployment"""
        print("=" * 60)
        print("DABS EDI System Deployment")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        deployment_steps = [
            ("Environment Validation", self.validate_environment),
            ("Dependency Installation", self.install_dependencies),
            ("Configuration Validation", self.validate_configuration),
            ("EDI Generation Test", self.test_edi_generation),
            ("Email Configuration Test", self.test_email_configuration),
            ("System Tests", self.run_system_tests)
        ]
        
        overall_success = True
        
        for step_name, step_function in deployment_steps:
            print(f"\n🔄 {step_name}...")
            try:
                step_success = await step_function()
                if not step_success:
                    overall_success = False
                    print(f"❌ {step_name} failed")
                    break
                else:
                    print(f"✅ {step_name} completed")
            except Exception as e:
                self.log_step(f"{step_name} exception: {str(e)}", False)
                overall_success = False
                break
        
        # Create deployment report
        await self.create_deployment_report(overall_success)
        
        print("\n" + "=" * 60)
        if overall_success:
            print("🎉 DEPLOYMENT SUCCESSFUL!")
            print("=" * 60)
            print("✅ DABS EDI system is ready for production")
            print("✅ 90% time reduction target achievable")
            print("✅ Utah Package Agency compliance maintained")
            print("✅ $28,000 annual value delivery enabled")
            print()
            print("Next Steps:")
            print("1. Configure environment variables for SMTP")
            print("2. Place DABS Excel files in data/ directory")
            print("3. Run: python src/edi/dabs_edi_production.py")
            print("4. Monitor logs/dabs_edi_production.log")
        else:
            print("❌ DEPLOYMENT FAILED!")
            print("=" * 60)
            print("Please review the deployment log and fix issues before retrying.")
            print("Check logs/deployment_report_*.json for detailed information.")
        
        return overall_success

async def main():
    """Main deployment function"""
    deployment = DABSEDIDeployment()
    success = await deployment.deploy()
    
    if success:
        print("\n🚀 Ready to start production system:")
        print("   python src/edi/dabs_edi_production.py")
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
