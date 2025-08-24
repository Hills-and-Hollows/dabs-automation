#!/usr/bin/env python3
"""
Simple Archon Documentation Setup
Upload key documentation files to Archon project using the project docs endpoint
"""

import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Any
import time

class SimpleArchonDocsSetup:
    def __init__(self):
        self.base_url = "http://localhost:8281"
        self.project_id = "d010ff76-0202-48e4-8362-40c45e9de39a"  # HH DABS Automation
        self.workspace_root = Path("/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory")
        
    def create_project_document(self, file_path: Path, doc_type: str = "technical") -> Dict[str, Any]:
        """Create a document directly in the project"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Prepare document data
            doc_data = {
                "document_type": doc_type,
                "title": file_path.name,
                "content": {"text": content, "source_path": str(file_path.relative_to(self.workspace_root))},
                "tags": [file_path.parent.name, doc_type],
                "author": "DABS Automation System"
            }
            
            # Create document in project
            response = requests.post(
                f"{self.base_url}/api/projects/{self.project_id}/docs",
                json=doc_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"✅ Created: {file_path.name}")
                return {"success": True, "data": response.json()}
            else:
                print(f"❌ Failed to create {file_path.name}: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"💥 Error creating {file_path.name}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_key_documentation_files(self) -> List[tuple]:
        """Get the most important documentation files"""
        key_docs = [
            # Core project documentation
            ("README.md", "business"),
            ("PROJECT_SUMMARY.md", "business"),
            
            # Archon setup and integration
            ("ARCHON_SETUP_COMPLETE_SUCCESS.md", "technical"),
            ("ARCHON_INTEGRATION_README.md", "technical"),
            ("ARCHON_TASK_MANAGEMENT_GUIDE.md", "technical"),
            ("CURSOR_MCP_SETUP.md", "technical"),
            
            # SSCS Integration (key technical docs)
            ("SSCS_COMPLETE_INTEGRATION_REQUIREMENTS.md", "technical"),
            ("SSCS_CPB_MANUAL_TEST_GUIDE.md", "technical"),
            ("SSCS_VENDOR_REQUIREMENTS.md", "business"),
            
            # Tessa's automation (key business docs)
            ("TESSA_MVP_FINAL_SOLUTION.md", "business"),
            ("TESSA_AUTOMATION_BREAKTHROUGH_UPDATE.md", "business"),
            ("BREAKTHROUGH_SSCS_NO_VENDOR_CONTACT.md", "business"),
            
            # Technical architecture
            ("docs/TECHNICAL_ARCHITECTURE.md", "technical"),
            ("docs/FUNCTIONAL_REQUIREMENTS.md", "business"),
            ("docs/USER_STORIES.md", "business"),
            ("docs/ACCEPTANCE_CRITERIA.md", "business"),
            
            # Configuration
            ("cursor_mcp_config.json", "technical"),
            ("config/dabs_config.json", "technical"),
        ]
        
        # Convert to actual file paths and filter existing files
        existing_docs = []
        for file_path, doc_type in key_docs:
            full_path = self.workspace_root / file_path
            if full_path.exists():
                existing_docs.append((full_path, doc_type))
            else:
                print(f"⚠️  File not found: {file_path}")
        
        return existing_docs
    
    def setup_key_documentation(self):
        """Setup key documentation in Archon"""
        print("🎯 ARCHON KEY DOCUMENTATION SETUP")
        print("=" * 60)
        print(f"📁 Workspace: {self.workspace_root}")
        print(f"🎯 Project ID: {self.project_id}")
        print()
        
        # Get key documentation files
        print("📊 Discovering key documentation files...")
        key_docs = self.get_key_documentation_files()
        print(f"✅ Found {len(key_docs)} key documentation files")
        print()
        
        # Categorize files
        technical_docs = [doc for doc, doc_type in key_docs if doc_type == "technical"]
        business_docs = [doc for doc, doc_type in key_docs if doc_type == "business"]
        
        print(f"📋 Categorization:")
        print(f"   🔧 Technical Knowledge: {len(technical_docs)} files")
        print(f"   💼 Business Knowledge: {len(business_docs)} files")
        print()
        
        # Upload technical documents
        print("🔧 Creating Technical Knowledge Documents...")
        technical_success = 0
        for doc_file in technical_docs:
            result = self.create_project_document(doc_file, "technical")
            if result["success"]:
                technical_success += 1
            time.sleep(0.2)  # Rate limiting
        
        print()
        
        # Upload business documents  
        print("💼 Creating Business Knowledge Documents...")
        business_success = 0
        for doc_file in business_docs:
            result = self.create_project_document(doc_file, "business")
            if result["success"]:
                business_success += 1
            time.sleep(0.2)  # Rate limiting
        
        print()
        print("=" * 60)
        print("🎊 KEY DOCUMENTATION SETUP COMPLETE")
        print("=" * 60)
        print(f"✅ Technical Documents: {technical_success}/{len(technical_docs)} created")
        print(f"✅ Business Documents: {business_success}/{len(business_docs)} created")
        print(f"📊 Total Success: {technical_success + business_success}/{len(key_docs)}")
        print()
        
        if technical_success + business_success > 0:
            print("🚀 Your Archon knowledge base now has key documentation!")
            print("   • Technical Knowledge: Setup guides, architecture, integration")
            print("   • Business Knowledge: Requirements, user stories, solutions")
            print()
            print("🔍 Access via Archon UI: http://localhost:3837")
            print("📋 Check Project Docs section for uploaded documents")
        else:
            print("⚠️  No documents were successfully uploaded.")
            print("   Check Archon server status and API endpoints.")

def main():
    """Main execution function"""
    setup = SimpleArchonDocsSetup()
    setup.setup_key_documentation()

if __name__ == "__main__":
    main()
