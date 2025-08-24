#!/usr/bin/env python3
"""
DABS Project Structure Enforcer
Prevents ANY deviation from defined architecture
"""
import os
import sys
from pathlib import Path
import json
import hashlib

class StructureEnforcer:
    def __init__(self):
        self.rules = self.load_structure_rules()
        
    def enforce_compliance(self):
        """Run all compliance checks - ZERO tolerance"""
        violations = []
        violations.extend(self.check_directory_structure())
        violations.extend(self.check_file_naming())
        violations.extend(self.check_duplicates())
        violations.extend(self.check_orphans())
        
        if violations:
            self.block_operation(violations)
        return True
    
    def block_operation(self, violations):
        """STOP everything if violations found"""
        print("🚫 STRUCTURE VIOLATION DETECTED - OPERATION BLOCKED")
        for v in violations:
            print(f"❌ {v}")
        sys.exit(1)