#!/usr/bin/env python3
"""
Task Synchronization Verification Script
Compares tasks between DABS Task Server (localhost:8151) and Project Frontend (localhost:3837)
"""

import requests
import json
from typing import Dict, List, Any
from datetime import datetime

def check_endpoint_connectivity():
    """Check connectivity to both endpoints"""
    results = {
        "dabs_server": {"url": "http://localhost:8151", "status": "unknown"},
        "frontend": {"url": "http://localhost:3837", "status": "unknown"}
    }
    
    # Check DABS Task Server
    try:
        response = requests.get("http://localhost:8151/health", timeout=5)
        if response.status_code == 200:
            results["dabs_server"]["status"] = "connected"
            results["dabs_server"]["health"] = response.json()
        else:
            results["dabs_server"]["status"] = f"error_{response.status_code}"
    except Exception as e:
        results["dabs_server"]["status"] = f"connection_failed: {str(e)}"
    
    # Check Frontend
    try:
        response = requests.get("http://localhost:3837/api/projects", timeout=5)
        if response.status_code == 200:
            results["frontend"]["status"] = "connected"
            results["frontend"]["projects"] = response.json()
        else:
            results["frontend"]["status"] = f"error_{response.status_code}"
    except Exception as e:
        results["frontend"]["status"] = f"connection_failed: {str(e)}"
    
    return results

def get_dabs_tasks():
    """Get tasks from DABS Task Server"""
    try:
        response = requests.get("http://localhost:8151/tasks", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "tasks": [], "total": 0}
    except Exception as e:
        return {"error": str(e), "tasks": [], "total": 0}

def get_frontend_tasks(project_id: str):
    """Get tasks from Frontend API"""
    try:
        response = requests.get(f"http://localhost:3837/api/projects/{project_id}/tasks", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def analyze_task_sync():
    """Analyze synchronization between both systems"""
    print("🔍 DABS Task Synchronization Verification")
    print("=" * 60)
    
    # Check connectivity
    connectivity = check_endpoint_connectivity()
    print(f"\n📡 Endpoint Connectivity:")
    print(f"  DABS Server (8151): {connectivity['dabs_server']['status']}")
    print(f"  Frontend (3837): {connectivity['frontend']['status']}")
    
    if connectivity["dabs_server"]["status"] != "connected":
        print("\n❌ DABS Task Server not accessible - cannot verify synchronization")
        return
    
    if connectivity["frontend"]["status"] != "connected":
        print("\n❌ Frontend not accessible - cannot verify synchronization")
        return
    
    # Get DABS tasks
    dabs_data = get_dabs_tasks()
    print(f"\n📋 DABS Task Server:")
    print(f"  Total tasks: {dabs_data.get('total', 0)}")
    
    if "error" in dabs_data:
        print(f"  Error: {dabs_data['error']}")
    else:
        print(f"  Tasks loaded: {len(dabs_data.get('tasks', []))}")
    
    # Get frontend project and tasks
    frontend_projects = connectivity["frontend"].get("projects", [])
    print(f"\n📋 Frontend Projects:")
    print(f"  Total projects: {len(frontend_projects)}")
    
    if frontend_projects:
        project = frontend_projects[0]  # First project
        project_id = project["id"]
        project_title = project["title"]
        print(f"  Project: {project_title} ({project_id})")
        
        # Get tasks for this project
        frontend_tasks = get_frontend_tasks(project_id)
        if isinstance(frontend_tasks, list):
            print(f"  Tasks in project: {len(frontend_tasks)}")
        else:
            print(f"  Error getting tasks: {frontend_tasks.get('error', 'unknown')}")
    
    # Detailed comparison
    print(f"\n🔍 Synchronization Analysis:")
    
    if "error" not in dabs_data and len(dabs_data.get("tasks", [])) > 0:
        dabs_tasks = dabs_data["tasks"]
        print(f"\n📊 DABS Server Task Breakdown:")
        
        # Group by status
        status_counts = {}
        priority_counts = {}
        phase_counts = {}
        
        for task in dabs_tasks:
            status = task.get("status", "unknown")
            priority = task.get("priority", "unknown")
            phase = task.get("phase", "unknown")
            
            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            phase_counts[phase] = phase_counts.get(phase, 0) + 1
        
        print(f"  Status breakdown: {status_counts}")
        print(f"  Priority breakdown: {priority_counts}")
        print(f"  Phase breakdown: {phase_counts}")
        
        # Show sample tasks
        print(f"\n📝 Sample DABS Tasks:")
        for i, task in enumerate(dabs_tasks[:3]):
            print(f"  {i+1}. {task.get('title', 'No title')} ({task.get('status', 'unknown')})")
            print(f"     Priority: {task.get('priority', 'unknown')}, Phase: {task.get('phase', 'unknown')}")
    
    # Synchronization verdict
    print(f"\n🎯 Synchronization Status:")
    
    dabs_task_count = dabs_data.get("total", 0) if "error" not in dabs_data else 0
    frontend_task_count = len(frontend_tasks) if isinstance(frontend_tasks, list) else 0
    
    if dabs_task_count > 0 and frontend_task_count == 0:
        print(f"  ❌ CRITICAL SYNC ISSUE:")
        print(f"     - DABS Server has {dabs_task_count} tasks")
        print(f"     - Frontend shows {frontend_task_count} tasks")
        print(f"     - Systems are completely out of sync")
        print(f"  🔧 Resolution needed: Import DABS tasks into frontend system")
    elif dabs_task_count == frontend_task_count == 0:
        print(f"  ⚠️  Both systems have 0 tasks - may need task initialization")
    elif dabs_task_count == frontend_task_count:
        print(f"  ✅ Task counts match ({dabs_task_count} tasks)")
    else:
        print(f"  ⚠️  Task count mismatch:")
        print(f"     - DABS Server: {dabs_task_count} tasks")
        print(f"     - Frontend: {frontend_task_count} tasks")
    
    print(f"\n📊 Summary:")
    print(f"  - DABS Task Server (localhost:8151): {dabs_task_count} tasks")
    print(f"  - Frontend (localhost:3837): {frontend_task_count} tasks")
    print(f"  - Sync Status: {'✅ In Sync' if dabs_task_count == frontend_task_count else '❌ Out of Sync'}")

if __name__ == "__main__":
    analyze_task_sync()