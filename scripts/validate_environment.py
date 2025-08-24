#!/usr/bin/env python3
"""
Environment Configuration Validation Script
Validates that all environment configurations are aligned and conflict-free
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

class EnvironmentValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.archon_dir = self.project_root / "archon-mcp"
        self.config_dir = self.project_root / "config"
        
    def check_archon_env(self) -> Tuple[bool, str]:
        """Check if Archon MCP .env file exists and has correct port"""
        env_file = self.archon_dir / ".env"
        
        if not env_file.exists():
            return False, "❌ archon-mcp/.env file missing"
            
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                
            # Check for required port configuration
            if "ARCHON_MCP_PORT=8151" not in content:
                return False, "❌ ARCHON_MCP_PORT not set to 8151"
                
            if "ARCHON_SERVER_PORT=8281" not in content:
                return False, "❌ ARCHON_SERVER_PORT not set to 8281"
                
            return True, "✅ Archon MCP .env configuration correct"
            
        except Exception as e:
            return False, f"❌ Error reading archon-mcp/.env: {e}"
    
    def check_port_alignment(self) -> Tuple[bool, str]:
        """Check that all configuration files reference the same ports"""
        expected_mcp_port = "8151"
        issues = []
        
        # Check cursor_mcp_config.json
        cursor_config = self.project_root / "cursor_mcp_config.json"
        if cursor_config.exists():
            try:
                with open(cursor_config, 'r') as f:
                    data = json.load(f)
                    
                if "localhost:8151" not in str(data):
                    issues.append("cursor_mcp_config.json doesn't reference port 8151")
                    
            except Exception as e:
                issues.append(f"Error reading cursor_mcp_config.json: {e}")
        
        # Check dabs_integration_config.json
        integration_config = self.archon_dir / "dabs_integration_config.json"
        if integration_config.exists():
            try:
                with open(integration_config, 'r') as f:
                    data = json.load(f)
                    
                archon_mcp = data.get("dabs_archon_integration", {}).get("services", {}).get("archon_mcp", {})
                if archon_mcp.get("port") != 8151:
                    issues.append("dabs_integration_config.json has wrong MCP port")
                    
            except Exception as e:
                issues.append(f"Error reading dabs_integration_config.json: {e}")
        
        if issues:
            return False, "❌ Port alignment issues: " + "; ".join(issues)
        
        return True, "✅ All configuration files reference port 8151"
    
    def check_credential_conflicts(self) -> Tuple[bool, str]:
        """Check for duplicate or conflicting credentials"""
        config_files = list(self.config_dir.glob("*.env"))
        
        # Look for SSCS credential duplicates
        sscs_files = []
        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                    if "SSCS_CCB_USERNAME" in content or "SSCS_USERNAME" in content:
                        sscs_files.append(config_file.name)
            except Exception:
                continue
        
        issues = []
        if len(sscs_files) > 1:
            issues.append(f"SSCS credentials duplicated in: {', '.join(sscs_files)}")
        
        # Check for plain text passwords (security risk)
        password_files = []
        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                    if any(keyword in content for keyword in ["_PASSWORD=", "_SECRET="]):
                        password_files.append(config_file.name)
            except Exception:
                continue
        
        if password_files:
            issues.append(f"Plain text passwords found in: {', '.join(password_files)}")
        
        if issues:
            return False, "⚠️  Security/conflict issues: " + "; ".join(issues)
        
        return True, "✅ No credential conflicts detected"
    
    def check_required_files(self) -> Tuple[bool, str]:
        """Check that all required configuration files exist"""
        required_files = [
            (self.archon_dir / ".env", "Archon MCP environment file"),
            (self.project_root / "cursor_mcp_config.json", "Cursor MCP configuration"),
            (self.config_dir / "dabs_config.json", "DABS system configuration"),
        ]
        
        missing = []
        for file_path, description in required_files:
            if not file_path.exists():
                missing.append(f"{description} ({file_path})")
        
        if missing:
            return False, f"❌ Missing files: {'; '.join(missing)}"
        
        return True, "✅ All required configuration files present"
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks"""
        results = {
            "archon_env": self.check_archon_env(),
            "port_alignment": self.check_port_alignment(), 
            "credential_conflicts": self.check_credential_conflicts(),
            "required_files": self.check_required_files()
        }
        
        all_passed = all(result[0] for result in results.values())
        
        return {
            "overall_status": "✅ PASS" if all_passed else "❌ FAIL",
            "results": results,
            "ready_for_integration": all_passed
        }

def main():
    """Main validation function"""
    validator = EnvironmentValidator()
    validation_results = validator.validate_all()
    
    print("🔍 ENVIRONMENT CONFIGURATION VALIDATION")
    print("=" * 50)
    
    for check_name, (passed, message) in validation_results["results"].items():
        print(f"{check_name.replace('_', ' ').title()}: {message}")
    
    print("\n" + "=" * 50)
    print(f"OVERALL STATUS: {validation_results['overall_status']}")
    
    if validation_results["ready_for_integration"]:
        print("\n🚀 Environment is ready for Archon MCP integration!")
        print("Next step: Run 'start_archon_dabs.sh' to test the connection")
    else:
        print("\n⚠️  Fix the issues above before proceeding")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
