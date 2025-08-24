#!/usr/bin/env python3
"""
DABS Cursor Project Rules Validation Script
Validates all .mdc project rules files for proper format and completeness
"""
import os
import sys
from pathlib import Path
import re

def validate_cursor_project_rules():
    """Validate all Cursor project rules (.mdc files)"""
    rules_dir = Path(__file__).parent
    project_root = rules_dir.parent.parent
    
    print("🔍 DABS Cursor Project Rules Validation")
    print("=" * 60)
    
    # Expected .mdc files
    expected_rules = [
        "archon-workflow.mdc",
        "dabs-business-logic.mdc", 
        "project-structure.mdc",
        "security-compliance.mdc",
        "testing-requirements.mdc",
        "api-design.mdc",
        "performance-gates.mdc",
        "integration-hub.mdc"
    ]
    
    # Check master .cursorrules file
    master_rules = project_root / ".cursorrules"
    if master_rules.exists():
        print("✅ Master .cursorrules file exists")
    else:
        print("❌ Master .cursorrules file missing")
        return False
    
    # Validate each .mdc rules file
    all_valid = True
    for filename in expected_rules:
        file_path = rules_dir / filename
        
        if file_path.exists():
            if validate_mdc_file(file_path, filename):
                print(f"✅ {filename} - valid .mdc format and content")
            else:
                print(f"❌ {filename} - validation failed")
                all_valid = False
        else:
            print(f"❌ {filename} - file missing")
            all_valid = False
    
    # Check README exists
    readme_path = rules_dir / "README.md"
    if readme_path.exists():
        print("✅ README.md - documentation exists")
    else:
        print("❌ README.md - documentation missing")
        all_valid = False
    
    print("=" * 60)
    if all_valid:
        print("🎉 ALL CURSOR PROJECT RULES VALIDATION PASSED")
        print("Ready for DABS development with Cursor project rules enforcement")
        print("\nActive Rules:")
        for rule in expected_rules:
            print(f"  📋 {rule}")
    else:
        print("🚫 CURSOR PROJECT RULES VALIDATION FAILED")
        print("Fix issues before proceeding with development")
    
    return all_valid

def validate_mdc_file(file_path: Path, filename: str) -> bool:
    """Validate .mdc file format and content"""
    try:
        content = file_path.read_text()
        
        # Check for frontmatter
        if not content.startswith('---'):
            print(f"   ❌ {filename}: Missing frontmatter")
            return False
        
        # Extract frontmatter
        parts = content.split('---', 2)
        if len(parts) < 3:
            print(f"   ❌ {filename}: Invalid frontmatter format")
            return False
        
        frontmatter = parts[1].strip()
        content_body = parts[2].strip()
        
        # Validate frontmatter has required properties
        if not any(prop in frontmatter for prop in ['alwaysApply:', 'globs:', 'description:']):
            print(f"   ❌ {filename}: Missing required frontmatter properties")
            return False
        
        # Check content length
        if len(content_body) < 200:
            print(f"   ❌ {filename}: Content too short")
            return False
        
        # File-specific validations
        validation_rules = {
            "archon-workflow.mdc": [
                "ARCHON-FIRST", "Serena MCP", "archon:manage_task", "MANDATORY"
            ],
            "dabs-business-logic.mdc": [
                "Utah Package Agency", "1,239 SKUs", "90% reduction", "<0.1% error"
            ],
            "project-structure.mdc": [
                "src/", "docs/", "tests/", "ZERO tolerance"
            ],
            "security-compliance.mdc": [
                "OAuth 2.0", "AES-256", "TLS 1.3", "audit trail"
            ],
            "testing-requirements.mdc": [
                "90% code coverage", "pytest", "test pyramid"
            ],
            "api-design.mdc": [
                "FastAPI", "RESTful", "Pydantic", "rate limiting"
            ],
            "performance-gates.mdc": [
                "15 minutes", "performance gates", "<2 seconds", "99% uptime"
            ],
            "integration-hub.mdc": [
                "IntegrationCoordinator", "DABS", "SSCS", "QuickBooks"
            ]
        }
        
        if filename in validation_rules:
            required_terms = validation_rules[filename]
            for term in required_terms:
                if term not in content_body:
                    print(f"   ❌ {filename}: Missing required term '{term}'")
                    return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ {filename}: Error reading file - {e}")
        return False

if __name__ == "__main__":
    success = validate_cursor_project_rules()
    sys.exit(0 if success else 1)
