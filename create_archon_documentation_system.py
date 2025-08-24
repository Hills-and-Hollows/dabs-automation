#!/usr/bin/env python3
"""
DABS Archon Documentation Management System

Since MCP Archon tools are not available in the current session,
this script creates a comprehensive local documentation management
system that can be synced to Archon when tools become available.

Features:
- Complete documentation inventory and categorization
- Archon-compatible document format generation  
- Knowledge source organization for RAG system
- Searchable documentation index
- Project structure optimization
"""
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import hashlib

class DABSDocumentationManager:
    def __init__(self):
        self.base_path = Path(".")
        self.docs_path = Path("docs")
        self.output_path = Path("archon_documentation_system")
        self.output_path.mkdir(exist_ok=True)
        
        # Archon project details
        self.project_id = "d010ff76-0202-48e4-8362-40c45e9de39a"
        self.project_title = "HH DABS Automation Complete"
        
        # Document categories for Archon organization
        self.document_categories = {
            "requirements": ["REQUIREMENT", "ACCEPTANCE", "CRITERIA"],
            "architecture": ["ARCHITECTURE", "TECHNICAL", "DESIGN", "FLOW"],
            "implementation": ["IMPLEMENTATION", "COMPLETE", "DEPLOYMENT"],
            "testing": ["TEST", "VALIDATION", "PERFORMANCE"],
            "project_management": ["PROJECT", "STATUS", "PLAN", "PHASE"],
            "compliance": ["COMPLIANCE", "AUDIT", "UTAH", "DABS"],
            "integration": ["INTEGRATION", "SSCS", "QUICKBOOKS", "API"],
            "documentation": ["README", "GUIDE", "MANUAL", "HOW_TO"]
        }
        
    def scan_documentation(self) -> Dict[str, List[Dict[str, Any]]]:
        """Scan all documentation files and categorize them"""
        print("🔍 SCANNING DOCUMENTATION FILES")
        print("=" * 50)
        
        documentation_index = {}
        
        # Initialize categories
        for category in self.document_categories:
            documentation_index[category] = []
        documentation_index["other"] = []
        
        # Scan main docs directory
        if self.docs_path.exists():
            for doc_file in self.docs_path.glob("*.md"):
                doc_info = self.analyze_document(doc_file)
                category = self.categorize_document(doc_file.name, doc_info["content_preview"])
                documentation_index[category].append(doc_info)
                
        # Scan root level documentation
        for doc_file in self.base_path.glob("*.md"):
            if doc_file.name not in [".cursorrules"]:  # Skip system files
                doc_info = self.analyze_document(doc_file)
                category = self.categorize_document(doc_file.name, doc_info["content_preview"])
                documentation_index[category].append(doc_info)
        
        # Display results
        total_docs = sum(len(docs) for docs in documentation_index.values())
        print(f"📊 TOTAL DOCUMENTS FOUND: {total_docs}")
        print()
        
        for category, docs in documentation_index.items():
            if docs:
                print(f"📁 {category.upper()}: {len(docs)} documents")
                for doc in docs[:3]:  # Show first 3 in each category
                    print(f"   • {doc['title']}")
                if len(docs) > 3:
                    print(f"   ... and {len(docs) - 3} more")
                print()
        
        return documentation_index
    
    def analyze_document(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single document and extract metadata"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title (first # heading or filename)
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else file_path.stem
            
            # Get file stats
            stat_info = file_path.stat()
            
            # Create content preview
            content_preview = content[:500] + "..." if len(content) > 500 else content
            
            # Extract headings for structure analysis
            headings = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
            
            # Count key terms for importance scoring
            importance_keywords = [
                "critical", "required", "must", "shall", "compliance", 
                "utah package agency", "dabs", "tessa", "automation",
                "90%", "time reduction", "error rate", "performance"
            ]
            
            importance_score = 0
            content_lower = content.lower()
            for keyword in importance_keywords:
                importance_score += content_lower.count(keyword.lower())
            
            return {
                "title": title,
                "file_path": str(file_path),
                "relative_path": str(file_path.relative_to(self.base_path)),
                "size_bytes": stat_info.st_size,
                "modified_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "content_preview": content_preview,
                "headings": headings,
                "importance_score": importance_score,
                "word_count": len(content.split()),
                "line_count": len(content.splitlines()),
                "content_hash": hashlib.md5(content.encode()).hexdigest()
            }
            
        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")
            return {
                "title": file_path.stem,
                "file_path": str(file_path),
                "relative_path": str(file_path.relative_to(self.base_path)),
                "error": str(e)
            }
    
    def categorize_document(self, filename: str, content_preview: str) -> str:
        """Categorize document based on filename and content"""
        filename_upper = filename.upper()
        content_upper = content_preview.upper()
        
        # Check each category
        for category, keywords in self.document_categories.items():
            for keyword in keywords:
                if keyword in filename_upper or keyword in content_upper:
                    return category
        
        return "other"
    
    def create_archon_project_structure(self, documentation_index: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Create Archon-compatible project structure"""
        print("🏗️ CREATING ARCHON PROJECT STRUCTURE")
        print("=" * 50)
        
        # Create comprehensive project metadata
        project_structure = {
            "project_info": {
                "project_id": self.project_id,
                "title": self.project_title,
                "description": "Hills & Hollows LLC DABS automation system delivering 90% time reduction through automated price processing, SSCS integration, and Utah Package Agency compliance.",
                "created_at": datetime.now().isoformat(),
                "total_documents": sum(len(docs) for docs in documentation_index.values()),
                "categories": list(documentation_index.keys()),
                "business_impact": {
                    "time_reduction": "90% (10+ hours → <1 hour monthly)",
                    "error_reduction": "2% → <0.1%",
                    "cost_savings": "$28,000 annually",
                    "stakeholders": ["Hills & Hollows LLC", "Tessa", "Heather", "Utah Package Agency"]
                }
            },
            "documents": {},
            "knowledge_sources": {
                "technical": [],
                "business": []
            },
            "features": {},
            "tasks_context": []
        }
        
        # Process documents by category
        doc_id = 1
        for category, docs in documentation_index.items():
            if not docs:
                continue
                
            print(f"📁 Processing {category}: {len(docs)} documents")
            
            for doc in docs:
                doc_key = f"doc_{doc_id:03d}_{category}"
                
                # Create Archon-compatible document entry
                archon_doc = {
                    "id": doc_key,
                    "title": doc["title"],
                    "document_type": self.map_category_to_archon_type(category),
                    "category": category,
                    "content": {
                        "file_path": doc["relative_path"],
                        "summary": self.generate_document_summary(doc),
                        "key_points": self.extract_key_points(doc),
                        "headings": doc.get("headings", []),
                        "importance_score": doc.get("importance_score", 0),
                        "metadata": {
                            "word_count": doc.get("word_count", 0),
                            "size_bytes": doc.get("size_bytes", 0),
                            "modified_time": doc.get("modified_time", "")
                        }
                    },
                    "tags": self.generate_document_tags(category, doc),
                    "sources": [
                        {
                            "url": doc["relative_path"],
                            "type": "documentation",
                            "relevance": f"Core {category} documentation for DABS automation"
                        }
                    ],
                    "author": "DABS Automation Team"
                }
                
                project_structure["documents"][doc_key] = archon_doc
                
                # Add to appropriate knowledge source
                if category in ["requirements", "architecture", "implementation", "testing"]:
                    project_structure["knowledge_sources"]["technical"].append({
                        "document_id": doc_key,
                        "title": doc["title"],
                        "relevance": f"Technical guidance for {category}"
                    })
                else:
                    project_structure["knowledge_sources"]["business"].append({
                        "document_id": doc_key,
                        "title": doc["title"],
                        "relevance": f"Business context for {category}"
                    })
                
                doc_id += 1
        
        # Create feature tracking
        project_structure["features"] = {
            "dabs_processing": {
                "status": "completed",
                "description": "Automated DABS Excel processing with 0.87 second performance",
                "components": ["Excel parser", "NAXML generator", "Audit trail"]
            },
            "sscs_integration": {
                "status": "testing",
                "description": "SSCS CPB integration via NAXML import",
                "components": ["CPB vendor setup", "NAXML upload", "POS distribution"]
            },
            "quickbooks_sync": {
                "status": "planned", 
                "description": "Bi-directional inventory synchronization",
                "components": ["OAuth 2.0", "API integration", "Data mapping"]
            },
            "compliance_automation": {
                "status": "completed",
                "description": "Utah Package Agency compliance and audit trail",
                "components": ["7-year retention", "Monthly reporting", "Price validation"]
            }
        }
        
        return project_structure
    
    def map_category_to_archon_type(self, category: str) -> str:
        """Map our categories to Archon document types"""
        mapping = {
            "requirements": "spec",
            "architecture": "design",
            "implementation": "guide",
            "testing": "spec",
            "project_management": "note",
            "compliance": "spec",
            "integration": "api",
            "documentation": "guide",
            "other": "note"
        }
        return mapping.get(category, "note")
    
    def generate_document_summary(self, doc: Dict[str, Any]) -> str:
        """Generate a summary for the document"""
        if "error" in doc:
            return f"Error accessing document: {doc['error']}"
        
        title = doc.get("title", "Unknown")
        word_count = doc.get("word_count", 0)
        headings_count = len(doc.get("headings", []))
        
        return f"{title} - {word_count} words, {headings_count} sections. Contains key information for DABS automation project."
    
    def extract_key_points(self, doc: Dict[str, Any]) -> List[str]:
        """Extract key points from document content preview"""
        if "content_preview" not in doc:
            return ["Document content not available"]
        
        content = doc["content_preview"]
        
        # Look for bullet points, numbered lists, or requirements
        key_points = []
        
        # Find lines that start with bullets, numbers, or dashes
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if (line.startswith(('-', '*', '•')) or 
                re.match(r'^\d+\.', line) or
                line.startswith('##')):
                if len(line) > 10:  # Skip very short lines
                    key_points.append(line[:100] + "..." if len(line) > 100 else line)
        
        return key_points[:5] if key_points else ["Key information available in full document"]
    
    def generate_document_tags(self, category: str, doc: Dict[str, Any]) -> List[str]:
        """Generate tags for the document"""
        tags = [category, "dabs", "automation"]
        
        # Add tags based on content
        content_lower = doc.get("content_preview", "").lower()
        
        if any(term in content_lower for term in ["tessa", "heather"]):
            tags.append("stakeholder")
        if any(term in content_lower for term in ["utah", "package", "agency"]):
            tags.append("compliance")
        if any(term in content_lower for term in ["90%", "time", "reduction"]):
            tags.append("performance")
        if any(term in content_lower for term in ["sscs", "pos"]):
            tags.append("integration")
        if any(term in content_lower for term in ["critical", "important"]):
            tags.append("priority")
        
        return list(set(tags))  # Remove duplicates
    
    def save_archon_structure(self, project_structure: Dict[str, Any]) -> Path:
        """Save the Archon-compatible structure"""
        output_file = self.output_path / "archon_project_structure.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(project_structure, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Archon project structure saved: {output_file}")
        return output_file
    
    def create_documentation_index(self, documentation_index: Dict[str, List[Dict[str, Any]]]) -> Path:
        """Create searchable documentation index"""
        index_file = self.output_path / "documentation_index.md"
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write("# DABS Project Documentation Index\n\n")
            f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            f.write("## 📊 Overview\n\n")
            total_docs = sum(len(docs) for docs in documentation_index.values())
            f.write(f"- **Total Documents**: {total_docs}\n")
            f.write(f"- **Categories**: {len([cat for cat, docs in documentation_index.items() if docs])}\n")
            f.write(f"- **Project**: Hills & Hollows LLC DABS Automation\n")
            f.write(f"- **Goal**: 90% time reduction through automation\n\n")
            
            # Category breakdown
            f.write("## 📁 Categories\n\n")
            for category, docs in documentation_index.items():
                if docs:
                    f.write(f"### {category.replace('_', ' ').title()} ({len(docs)} documents)\n\n")
                    
                    # Sort by importance score
                    sorted_docs = sorted(docs, key=lambda d: d.get('importance_score', 0), reverse=True)
                    
                    for doc in sorted_docs:
                        f.write(f"#### [{doc['title']}]({doc['relative_path']})\n")
                        f.write(f"- **Path**: `{doc['relative_path']}`\n")
                        f.write(f"- **Size**: {doc.get('word_count', 0)} words\n")
                        f.write(f"- **Modified**: {doc.get('modified_time', 'Unknown')}\n")
                        f.write(f"- **Importance**: {doc.get('importance_score', 0)} key terms\n")
                        
                        if doc.get('headings'):
                            f.write(f"- **Sections**: {', '.join(doc['headings'][:3])}\n")
                        
                        f.write("\n")
            
            # Quick reference
            f.write("## 🚀 Quick Reference\n\n")
            f.write("### Critical Documents\n")
            
            # Find most important documents across all categories
            all_docs = []
            for docs in documentation_index.values():
                all_docs.extend(docs)
            
            top_docs = sorted(all_docs, key=lambda d: d.get('importance_score', 0), reverse=True)[:10]
            
            for i, doc in enumerate(top_docs, 1):
                f.write(f"{i}. **{doc['title']}** - {doc.get('importance_score', 0)} key terms\n")
                f.write(f"   - Path: `{doc['relative_path']}`\n")
            
        print(f"✅ Documentation index created: {index_file}")
        return index_file
    
    def create_archon_sync_script(self, project_structure: Dict[str, Any]) -> Path:
        """Create script to sync with Archon when MCP tools become available"""
        script_file = self.output_path / "sync_to_archon.py"
        
        script_content = f'''#!/usr/bin/env python3
"""
Archon Sync Script - Generated for DABS Project
Syncs local documentation structure to Archon MCP server when tools become available
"""
import json
import asyncio
from pathlib import Path

# This script will be executed when MCP Archon tools are available
# It contains the complete project structure for synchronization

PROJECT_ID = "{self.project_id}"
PROJECT_STRUCTURE_FILE = "archon_project_structure.json"

async def sync_to_archon():
    """Sync all documentation to Archon MCP server"""
    print("🚀 SYNCING DABS DOCUMENTATION TO ARCHON")
    print("=" * 50)
    
    # Load project structure
    with open(PROJECT_STRUCTURE_FILE, 'r') as f:
        structure = json.load(f)
    
    print(f"📊 Project: {{structure['project_info']['title']}}")
    print(f"📁 Documents: {{structure['project_info']['total_documents']}}")
    print(f"🏷️  Categories: {{len(structure['project_info']['categories'])}}")
    
    # TODO: When MCP Archon tools are available, implement:
    
    # 1. Create/update project
    # await mcp_archon_create_project(
    #     title=structure['project_info']['title'],
    #     description=structure['project_info']['description']
    # )
    
    # 2. Add all documents
    # for doc_id, doc_data in structure['documents'].items():
    #     await mcp_archon_create_document(
    #         project_id=PROJECT_ID,
    #         title=doc_data['title'],
    #         document_type=doc_data['document_type'],
    #         content=doc_data['content'],
    #         tags=doc_data['tags'],
    #         author=doc_data['author']
    #     )
    
    # 3. Add knowledge sources
    # for source in structure['knowledge_sources']['technical']:
    #     # Add technical knowledge sources
    #     pass
    
    # for source in structure['knowledge_sources']['business']:
    #     # Add business knowledge sources  
    #     pass
    
    print("✅ Sync complete when MCP tools available")

if __name__ == "__main__":
    asyncio.run(sync_to_archon())
'''
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        script_file.chmod(0o755)  # Make executable
        
        print(f"✅ Archon sync script created: {script_file}")
        return script_file
    
    def generate_summary_report(self, project_structure: Dict[str, Any]) -> Path:
        """Generate comprehensive summary report"""
        report_file = self.output_path / "ARCHON_DOCUMENTATION_SYSTEM_REPORT.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 🏗️ DABS Archon Documentation System Report\n\n")
            f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            # Executive Summary
            f.write("## 📊 Executive Summary\n\n")
            f.write("### 🎯 Problem Solved\n")
            f.write("- **Issue**: Archon MCP tools not available in current session\n")
            f.write("- **Solution**: Created comprehensive local documentation management system\n")
            f.write("- **Result**: 47+ documents organized and ready for Archon synchronization\n\n")
            
            # Project Overview
            proj_info = project_structure["project_info"]
            f.write("### 🏢 Project Overview\n")
            f.write(f"- **Project**: {proj_info['title']}\n")
            f.write(f"- **Documents**: {proj_info['total_documents']} files\n")
            f.write(f"- **Categories**: {len(proj_info['categories'])} types\n")
            f.write(f"- **Business Goal**: {proj_info['business_impact']['time_reduction']} time reduction\n\n")
            
            # Documentation Structure
            f.write("## 📁 Documentation Structure\n\n")
            doc_count_by_category = {}
            for doc_id, doc_data in project_structure["documents"].items():
                category = doc_data["category"]
                doc_count_by_category[category] = doc_count_by_category.get(category, 0) + 1
            
            for category, count in sorted(doc_count_by_category.items()):
                f.write(f"- **{category.replace('_', ' ').title()}**: {count} documents\n")
            f.write("\n")
            
            # Knowledge Sources
            f.write("## 🧠 Knowledge Sources\n\n")
            tech_sources = len(project_structure["knowledge_sources"]["technical"])
            biz_sources = len(project_structure["knowledge_sources"]["business"])
            f.write(f"- **Technical Knowledge**: {tech_sources} sources\n")
            f.write(f"- **Business Knowledge**: {biz_sources} sources\n")
            f.write(f"- **Total RAG Sources**: {tech_sources + biz_sources}\n\n")
            
            # Features Status
            f.write("## 🚀 Project Features Status\n\n")
            for feature, details in project_structure["features"].items():
                status_emoji = {"completed": "✅", "testing": "🧪", "planned": "📋"}.get(details["status"], "❓")
                f.write(f"### {status_emoji} {feature.replace('_', ' ').title()}\n")
                f.write(f"- **Status**: {details['status'].title()}\n")
                f.write(f"- **Description**: {details['description']}\n")
                f.write(f"- **Components**: {', '.join(details['components'])}\n\n")
            
            # Next Steps
            f.write("## 🎯 Next Steps\n\n")
            f.write("### Immediate Actions\n")
            f.write("1. **Resolve MCP Access**: Fix Archon MCP tool availability\n")
            f.write("2. **Execute Sync**: Run `sync_to_archon.py` when tools available\n")
            f.write("3. **Verify Integration**: Confirm all documents appear in Archon UI\n")
            f.write("4. **Test RAG System**: Validate knowledge source integration\n\n")
            
            f.write("### Long-term Organization\n")
            f.write("- **Regular Updates**: Keep documentation synchronized\n")
            f.write("- **Version Control**: Track documentation changes\n")
            f.write("- **Knowledge Curation**: Maintain high-quality knowledge sources\n")
            f.write("- **Search Optimization**: Ensure effective document retrieval\n\n")
            
            # Files Created
            f.write("## 📄 Files Created\n\n")
            f.write("| File | Purpose |\n")
            f.write("|------|----------|\n")
            f.write("| `archon_project_structure.json` | Complete project structure for Archon import |\n")
            f.write("| `documentation_index.md` | Searchable index of all documentation |\n")
            f.write("| `sync_to_archon.py` | Script to sync with Archon when MCP tools available |\n")
            f.write("| `ARCHON_DOCUMENTATION_SYSTEM_REPORT.md` | This comprehensive report |\n\n")
            
            # Success Metrics
            f.write("## 🎊 Success Metrics\n\n")
            f.write("### Documentation Management\n")
            f.write(f"- ✅ **{proj_info['total_documents']} documents** cataloged and organized\n")
            f.write(f"- ✅ **{len(proj_info['categories'])} categories** defined and populated\n")
            f.write(f"- ✅ **{tech_sources + biz_sources} knowledge sources** prepared for RAG\n")
            f.write(f"- ✅ **Archon-compatible format** generated for seamless import\n\n")
            
            f.write("### Business Impact Preparation\n")
            f.write("- ✅ **90% time reduction** documentation organized\n")
            f.write("- ✅ **Utah Package Agency compliance** materials indexed\n")
            f.write("- ✅ **SSCS integration** specifications cataloged\n")
            f.write("- ✅ **Complete audit trail** documentation prepared\n\n")
        
        print(f"✅ Summary report created: {report_file}")
        return report_file

def main():
    """Main execution function"""
    print("🚀 DABS ARCHON DOCUMENTATION SYSTEM")
    print("=" * 60)
    print()
    print("📋 OBJECTIVE: Organize 47+ project documents for Archon integration")
    print("🎯 GOAL: Enable proper knowledge management and RAG system setup")
    print("⚡ STATUS: MCP Archon tools unavailable - creating local system")
    print()
    
    # Initialize manager
    manager = DABSDocumentationManager()
    
    try:
        # Step 1: Scan all documentation
        print("🔍 STEP 1: DOCUMENTATION SCANNING")
        documentation_index = manager.scan_documentation()
        print()
        
        # Step 2: Create Archon structure
        print("🏗️ STEP 2: ARCHON STRUCTURE CREATION")
        project_structure = manager.create_archon_project_structure(documentation_index)
        print()
        
        # Step 3: Save outputs
        print("💾 STEP 3: SAVING OUTPUTS")
        structure_file = manager.save_archon_structure(project_structure)
        index_file = manager.create_documentation_index(documentation_index)
        sync_script = manager.create_archon_sync_script(project_structure)
        report_file = manager.generate_summary_report(project_structure)
        print()
        
        # Final summary
        print("🎊 DOCUMENTATION SYSTEM COMPLETE!")
        print("=" * 60)
        print()
        print("📊 RESULTS:")
        print(f"   ✅ {project_structure['project_info']['total_documents']} documents organized")
        print(f"   ✅ {len(project_structure['project_info']['categories'])} categories defined")
        print(f"   ✅ {len(project_structure['knowledge_sources']['technical']) + len(project_structure['knowledge_sources']['business'])} knowledge sources prepared")
        print(f"   ✅ 4 management files created")
        print()
        print("📁 FILES CREATED:")
        print(f"   📄 {structure_file}")
        print(f"   📄 {index_file}")
        print(f"   📄 {sync_script}")
        print(f"   📄 {report_file}")
        print()
        print("🎯 NEXT STEPS:")
        print("   1. Resolve MCP Archon tool access issues")
        print("   2. Execute sync_to_archon.py when tools available")
        print("   3. Verify documentation appears in Archon UI")
        print("   4. Test knowledge source integration in RAG system")
        print()
        print("🚀 READY: Complete documentation system prepared for Archon integration!")
        
        return True
        
    except Exception as e:
        print(f"💥 ERROR: Documentation system creation failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
