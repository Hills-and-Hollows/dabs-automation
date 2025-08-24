#!/usr/bin/env python3
"""
Setup Archon Knowledge Base
Upload all project documentation to Archon for proper organization and retrieval
"""

import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Any
import time

class ArchonKnowledgeBaseSetup:
    def __init__(self):
        self.base_url = "http://localhost:8281"
        self.project_id = "d010ff76-0202-48e4-8362-40c45e9de39a"  # HH DABS Automation
        self.workspace_root = Path("/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory")
        
    def upload_document(self, file_path: Path, category: str = "technical") -> Dict[str, Any]:
        """Upload a single document to Archon"""
        try:
            # Prepare multipart form data
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_path.name, f, 'text/plain')
                }
                data = {
                    'knowledge_type': category,
                    'tags': f"source:{file_path.parent.name}"
                }

                # Upload to Archon
                response = requests.post(
                    f"{self.base_url}/api/documents/upload",
                    files=files,
                    data=data
                )

            if response.status_code == 200:
                print(f"✅ Uploaded: {file_path.name}")
                return {"success": True, "data": response.json()}
            else:
                print(f"❌ Failed to upload {file_path.name}: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}

        except Exception as e:
            print(f"💥 Error uploading {file_path.name}: {e}")
            return {"success": False, "error": str(e)}
    
    def categorize_document(self, file_path: Path) -> str:
        """Determine if document is technical or business knowledge"""
        file_name = file_path.name.upper()
        parent_dir = file_path.parent.name.lower()
        
        # Business Knowledge indicators
        business_keywords = [
            'TESSA', 'MVP', 'EXECUTIVE', 'MANAGER', 'REQUIREMENTS', 'USER_STORIES',
            'ACCEPTANCE_CRITERIA', 'BUSINESS', 'PLANNING', 'SUMMARY', 'PAIN_POINT',
            'AUTOMATION_COMPLETE', 'DELIVERY_TIMING', 'BREAKTHROUGH'
        ]
        
        # Technical Knowledge indicators  
        technical_keywords = [
            'ARCHON', 'SSCS', 'API', 'TECHNICAL', 'ARCHITECTURE', 'INTEGRATION',
            'SETUP', 'CONFIGURATION', 'TESTING', 'VALIDATION', 'IMPLEMENTATION',
            'DATABASE', 'EDI', 'ENDPOINT', 'MCP', 'CURSOR'
        ]
        
        # Check parent directory
        if parent_dir in ['research reports', 'prps']:
            return "business"
        elif parent_dir in ['docs', 'src', 'scripts', 'tests']:
            return "technical"
            
        # Check filename keywords
        for keyword in business_keywords:
            if keyword in file_name:
                return "business"
                
        for keyword in technical_keywords:
            if keyword in file_name:
                return "technical"
                
        # Default to technical for code-related files
        if file_path.suffix.lower() in ['.py', '.js', '.ts', '.json', '.yml', '.yaml', '.sh']:
            return "technical"
            
        return "business"  # Default for documentation
    
    def get_all_documentation_files(self) -> List[Path]:
        """Get all documentation files in the project"""
        doc_files = []
        
        # Root level markdown files
        for md_file in self.workspace_root.glob("*.md"):
            if not md_file.name.startswith('.'):
                doc_files.append(md_file)
        
        # Documentation directory
        docs_dir = self.workspace_root / "docs"
        if docs_dir.exists():
            for md_file in docs_dir.rglob("*.md"):
                doc_files.append(md_file)
        
        # PRPs directory
        prps_dir = self.workspace_root / "PRPs"
        if prps_dir.exists():
            for md_file in prps_dir.rglob("*.md"):
                doc_files.append(md_file)
        
        # Research reports
        research_dir = self.workspace_root / "research reports"
        if research_dir.exists():
            for md_file in research_dir.rglob("*.md"):
                doc_files.append(md_file)
        
        # Configuration files
        config_dir = self.workspace_root / "config"
        if config_dir.exists():
            for config_file in config_dir.glob("*.json"):
                doc_files.append(config_file)
        
        # Important setup and guide files
        important_files = [
            "README.md",
            "CURSOR_MCP_SETUP.md", 
            "cursor_mcp_config.json",
            "requirements.txt"
        ]
        
        for file_name in important_files:
            file_path = self.workspace_root / file_name
            if file_path.exists() and file_path not in doc_files:
                doc_files.append(file_path)
        
        return sorted(doc_files)
    
    def setup_knowledge_base(self):
        """Main function to setup the complete knowledge base"""
        print("🎯 ARCHON KNOWLEDGE BASE SETUP")
        print("=" * 60)
        print(f"📁 Workspace: {self.workspace_root}")
        print(f"🎯 Project ID: {self.project_id}")
        print()
        
        # Get all documentation files
        print("📊 Discovering documentation files...")
        doc_files = self.get_all_documentation_files()
        print(f"✅ Found {len(doc_files)} documentation files")
        print()
        
        # Categorize files
        technical_docs = []
        business_docs = []
        
        for doc_file in doc_files:
            category = self.categorize_document(doc_file)
            if category == "technical":
                technical_docs.append(doc_file)
            else:
                business_docs.append(doc_file)
        
        print(f"📋 Categorization:")
        print(f"   🔧 Technical Knowledge: {len(technical_docs)} files")
        print(f"   💼 Business Knowledge: {len(business_docs)} files")
        print()
        
        # Upload technical documents
        print("🔧 Uploading Technical Knowledge...")
        technical_success = 0
        for doc_file in technical_docs:
            result = self.upload_document(doc_file, "technical")
            if result["success"]:
                technical_success += 1
            time.sleep(0.1)  # Rate limiting
        
        print()
        
        # Upload business documents  
        print("💼 Uploading Business Knowledge...")
        business_success = 0
        for doc_file in business_docs:
            result = self.upload_document(doc_file, "business")
            if result["success"]:
                business_success += 1
            time.sleep(0.1)  # Rate limiting
        
        print()
        print("=" * 60)
        print("🎊 KNOWLEDGE BASE SETUP COMPLETE")
        print("=" * 60)
        print(f"✅ Technical Documents: {technical_success}/{len(technical_docs)} uploaded")
        print(f"✅ Business Documents: {business_success}/{len(business_docs)} uploaded")
        print(f"📊 Total Success: {technical_success + business_success}/{len(doc_files)}")
        print()
        print("🚀 Your Archon knowledge base is now populated!")
        print("   • Technical Knowledge: Architecture, APIs, Implementation")
        print("   • Business Knowledge: Requirements, Planning, User Stories")
        print()
        print("🔍 Access via Archon UI: http://localhost:3837")

def main():
    """Main execution function"""
    setup = ArchonKnowledgeBaseSetup()
    setup.setup_knowledge_base()

if __name__ == "__main__":
    main()
