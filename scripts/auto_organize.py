#!/usr/bin/env python3
"""
Auto-organizer that FORCES correct placement
"""
import shutil
from pathlib import Path

class AutoOrganizer:
    RULES = {
        '.py': 'src/',
        '.md': 'docs/',
        '.csv': 'data/',
        '.xlsx': 'data/',
        'test_*.py': 'tests/',
        '*_test.py': 'tests/'
    }
    
    def organize_file(self, filepath):
        """Move file to correct location automatically"""
        file_path = Path(filepath)
        
        # Determine correct location
        target_dir = self.get_target_directory(file_path)
        
        if target_dir:
            target_path = Path(target_dir) / file_path.name
            shutil.move(str(file_path), str(target_path))
            print(f"📁 Moved {file_path} → {target_path}")
            
    def get_target_directory(self, file_path):
        """Determine where file belongs"""
        for pattern, target in self.RULES.items():
            if file_path.match(pattern):
                return target
        return None