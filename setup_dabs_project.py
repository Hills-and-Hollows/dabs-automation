#!/usr/bin/env python3
"""
Setup DABS Project Structure in Advanced MCP Server
Creates the complete DABS project with phases and tasks
"""

import json
import requests
from datetime import datetime

BASE_URL = "http://localhost:8151"

def create_dabs_project():
    """Create the main DABS project"""
    print("🏗️ Creating DABS Project...")
    
    payload = {
        "action": "create",
        "title": "DABS Pricing & Inventory Automation",
        "description": "Automated Pricing & Inventory Sync System for Hills & Hollows LLC (Utah Package Agency). Eliminates 10+ hours/week of manual data entry by creating automated sync between DABS (state system), SSCS POS, and QuickBooks.",
        "github_repo": "https://github.com/dabs/pricing-inventory"
    }
    
    response = requests.post(f"{BASE_URL}/mcp/tools/manage_project", json=payload)
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            project_id = data["project_id"]
            print(f"✅ DABS Project created: {project_id[:8]}...")
            return project_id
        else:
            print(f"❌ Project creation failed: {data.get('error', 'Unknown error')}")
            return None
    else:
        print(f"❌ Project creation failed: {response.status_code}")
        return None

def create_phase_1_tasks(project_id):
    """Create Phase 1 tasks (Requirements & Research)"""
    print("\n📋 Creating Phase 1 Tasks (Requirements & Research)...")
    
    phase_1_tasks = [
        {
            "title": "Complete PRD Documentation",
            "description": "Finalize Product Requirements Document with all functional and non-functional requirements",
            "status": "completed",
            "priority": 1
        },
        {
            "title": "SSCS POS System Analysis",
            "description": "Complete analysis of SSCS POS system integration capabilities and API documentation",
            "status": "completed", 
            "priority": 1
        },
        {
            "title": "QuickBooks Integration Research",
            "description": "Research QuickBooks API capabilities and integration requirements for automated sync",
            "status": "completed",
            "priority": 1
        },
        {
            "title": "DABS System Integration Analysis",
            "description": "Analyze DABS system for automated data extraction and reporting capabilities",
            "status": "completed",
            "priority": 1
        },
        {
            "title": "Technical Architecture Design",
            "description": "Design complete system architecture for automated pricing and inventory sync",
            "status": "completed",
            "priority": 2
        },
        {
            "title": "Risk Assessment & Mitigation",
            "description": "Complete risk assessment and develop mitigation strategies for project implementation",
            "status": "completed",
            "priority": 2
        }
    ]
    
    created_tasks = []
    for task_info in phase_1_tasks:
        payload = {
            "action": "create",
            "project_id": project_id,
            "title": f"Phase 1: {task_info['title']}",
            "description": task_info["description"],
            "status": task_info["status"],
            "priority": task_info["priority"]
        }
        
        response = requests.post(f"{BASE_URL}/mcp/tools/manage_task", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                created_tasks.append(data["task_id"])
                print(f"   ✅ {task_info['title']}")
            else:
                print(f"   ❌ {task_info['title']}: {data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ {task_info['title']}: HTTP {response.status_code}")
    
    return created_tasks

def create_phase_2_tasks(project_id):
    """Create Phase 2 tasks (Core Development)"""
    print("\n🔧 Creating Phase 2 Tasks (Core Development)...")
    
    phase_2_tasks = [
        {
            "title": "SSCS POS API Integration",
            "description": "Implement API integration with SSCS POS system for inventory and pricing data sync",
            "status": "todo",
            "priority": 1
        },
        {
            "title": "QuickBooks API Integration", 
            "description": "Implement QuickBooks API integration for automated financial data sync",
            "status": "todo",
            "priority": 1
        },
        {
            "title": "DABS Data Processing Module",
            "description": "Develop module to process DABS Excel files and extract pricing/inventory data",
            "status": "todo",
            "priority": 1
        },
        {
            "title": "Database Schema Implementation",
            "description": "Implement PostgreSQL database schema for storing and managing sync data",
            "status": "todo",
            "priority": 2
        },
        {
            "title": "Automated Sync Engine",
            "description": "Develop core sync engine to coordinate data flow between all systems",
            "status": "todo",
            "priority": 1
        },
        {
            "title": "Error Handling & Logging",
            "description": "Implement comprehensive error handling and logging for all sync operations",
            "status": "todo",
            "priority": 2
        },
        {
            "title": "Data Validation Framework",
            "description": "Implement data validation to ensure accuracy across all system integrations",
            "status": "todo",
            "priority": 2
        }
    ]
    
    created_tasks = []
    for task_info in phase_2_tasks:
        payload = {
            "action": "create",
            "project_id": project_id,
            "title": f"Phase 2: {task_info['title']}",
            "description": task_info["description"],
            "status": task_info["status"],
            "priority": task_info["priority"]
        }
        
        response = requests.post(f"{BASE_URL}/mcp/tools/manage_task", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                created_tasks.append(data["task_id"])
                print(f"   ✅ {task_info['title']}")
            else:
                print(f"   ❌ {task_info['title']}: {data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ {task_info['title']}: HTTP {response.status_code}")
    
    return created_tasks

def create_phase_3_tasks(project_id):
    """Create Phase 3 tasks (Testing & Deployment)"""
    print("\n🧪 Creating Phase 3 Tasks (Testing & Deployment)...")
    
    phase_3_tasks = [
        {
            "title": "Unit Testing Implementation",
            "description": "Develop comprehensive unit tests for all system components",
            "status": "todo",
            "priority": 2
        },
        {
            "title": "Integration Testing",
            "description": "Test all system integrations with SSCS, QuickBooks, and DABS",
            "status": "todo",
            "priority": 1
        },
        {
            "title": "User Acceptance Testing",
            "description": "Conduct UAT with Hills & Hollows LLC to validate system functionality",
            "status": "todo",
            "priority": 1
        },
        {
            "title": "Performance Testing",
            "description": "Test system performance under expected load conditions",
            "status": "todo",
            "priority": 2
        },
        {
            "title": "Security Testing",
            "description": "Conduct security testing and vulnerability assessment",
            "status": "todo",
            "priority": 2
        },
        {
            "title": "Production Deployment",
            "description": "Deploy system to production environment with monitoring",
            "status": "todo",
            "priority": 1
        },
        {
            "title": "User Training & Documentation",
            "description": "Provide user training and create operational documentation",
            "status": "todo",
            "priority": 2
        }
    ]
    
    created_tasks = []
    for task_info in phase_3_tasks:
        payload = {
            "action": "create",
            "project_id": project_id,
            "title": f"Phase 3: {task_info['title']}",
            "description": task_info["description"],
            "status": task_info["status"],
            "priority": task_info["priority"]
        }
        
        response = requests.post(f"{BASE_URL}/mcp/tools/manage_task", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                created_tasks.append(data["task_id"])
                print(f"   ✅ {task_info['title']}")
            else:
                print(f"   ❌ {task_info['title']}: {data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ {task_info['title']}: HTTP {response.status_code}")
    
    return created_tasks

def get_project_summary(project_id):
    """Get project summary with all tasks"""
    print("\n📊 Project Summary...")
    
    # Get project details
    payload = {"action": "get", "project_id": project_id}
    response = requests.post(f"{BASE_URL}/mcp/tools/manage_project", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            project = data["project"]
            print(f"📋 Project: {project['title']}")
            print(f"   Created: {project['created'][:10]}")
            print(f"   Status: {project['status']}")
            
            # Get all tasks
            payload = {"action": "list", "project_id": project_id}
            response = requests.post(f"{BASE_URL}/mcp/tools/manage_task", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    tasks = data["tasks"]
                    
                    # Group by status
                    completed = [t for t in tasks if t["status"] == "completed"]
                    todo = [t for t in tasks if t["status"] == "todo"]
                    in_progress = [t for t in tasks if t["status"] == "in_progress"]
                    
                    print(f"\n📈 Task Summary:")
                    print(f"   ✅ Completed: {len(completed)}")
                    print(f"   🔄 In Progress: {len(in_progress)}")
                    print(f"   📋 To Do: {len(todo)}")
                    print(f"   📊 Total: {len(tasks)}")
                    
                    # Calculate progress
                    if tasks:
                        progress = (len(completed) / len(tasks)) * 100
                        print(f"   🎯 Progress: {progress:.1f}%")
                    
                    return True
    
    print("❌ Could not retrieve project summary")
    return False

def main():
    """Setup complete DABS project structure"""
    print("🚀 Setting up DABS Project Structure in Advanced MCP Server")
    print("=" * 60)
    
    # Create main project
    project_id = create_dabs_project()
    if not project_id:
        print("❌ Failed to create project. Exiting.")
        return False
    
    # Create all phases
    phase_1_tasks = create_phase_1_tasks(project_id)
    phase_2_tasks = create_phase_2_tasks(project_id)
    phase_3_tasks = create_phase_3_tasks(project_id)
    
    # Summary
    total_tasks = len(phase_1_tasks) + len(phase_2_tasks) + len(phase_3_tasks)
    print(f"\n🎉 DABS Project Setup Complete!")
    print(f"   Project ID: {project_id}")
    print(f"   Total Tasks Created: {total_tasks}")
    print(f"   Phase 1 (Requirements): {len(phase_1_tasks)} tasks")
    print(f"   Phase 2 (Development): {len(phase_2_tasks)} tasks")
    print(f"   Phase 3 (Testing): {len(phase_3_tasks)} tasks")
    
    # Get detailed summary
    get_project_summary(project_id)
    
    print(f"\n✨ Ready for development!")
    print(f"🔧 Use Cursor with MCP endpoint: http://localhost:8151/mcp/sse")
    
    return True

if __name__ == "__main__":
    main()
