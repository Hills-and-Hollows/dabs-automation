#!/usr/bin/env python3
"""
ARCHON SYNCHRONIZATION UTILITIES
Reusable functions for Archon-to-Chat todo synchronization

This module provides simple functions that can be imported and used
in other scripts, MCP tools, or interactive sessions.

Usage:
    from scripts.archon_sync_utils import sync_archon_to_chat_todos
    
    # Simple sync
    result = await sync_archon_to_chat_todos()
    
    # With custom project
    result = await sync_archon_to_chat_todos(project_id="custom-uuid")

Author: DABS Automation System
Created: 2025-08-23
"""

import asyncio
import json
import httpx
from typing import Dict, List, Tuple, Optional

# Default DABS project ID
DEFAULT_PROJECT_ID = "d010ff76-0202-48e4-8362-40c45e9de39a"

# Status mapping from Archon to Chat Todo format
STATUS_MAPPING = {
    "todo": "pending",
    "doing": "in_progress", 
    "review": "in_progress",  # Keep review as active
    "done": "completed",
    "cancelled": "cancelled"
}

# Priority indicators
PRIORITY_EMOJIS = {
    "CRITICAL": "🚨",
    "HIGH": "⚡", 
    "MEDIUM": "📊",
    "LOW": "📝"
}

async def get_archon_tasks(project_id: str = DEFAULT_PROJECT_ID) -> Tuple[bool, List[Dict], str]:
    """
    Retrieve all tasks from Archon project
    
    Args:
        project_id: Archon project UUID
        
    Returns:
        Tuple of (success, tasks_list, message)
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Using the correct API format that matches working MCP calls
            response = await client.get(
                "http://localhost:8281/api/tasks",
                params={
                    "project_id": project_id,
                    "include_closed": "false",
                    "page": 1,
                    "per_page": 100
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    tasks = data.get("tasks", [])
                    return True, tasks, f"Retrieved {len(tasks)} tasks"
                else:
                    return False, [], f"API error: {data.get('error')}"
            else:
                return False, [], f"HTTP {response.status_code}: {response.text}"
                
    except Exception as e:
        return False, [], f"Connection error: {str(e)}"

def transform_task_to_todo(task: Dict) -> Dict:
    """
    Transform single Archon task to chat todo format
    
    Args:
        task: Archon task dictionary
        
    Returns:
        Todo dictionary with id, content, status
    """
    title = task.get("title", "Untitled Task")
    description = task.get("description", "")
    
    # Detect priority from content
    priority = "MEDIUM"
    for p in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if p in title.upper() or p in description.upper():
            priority = p
            break
    
    # Build content with priority indicator
    priority_indicator = PRIORITY_EMOJIS.get(priority, "📝")
    
    # Get brief description (first sentence or 80 chars)
    brief_desc = description.split('.')[0][:80]
    if len(brief_desc) == 80:
        brief_desc += "..."
    
    content = f"{priority_indicator} {title}"
    if brief_desc and brief_desc.strip():
        content += f" - {brief_desc}"
    
    # Add assignee info
    assignee = task.get("assignee")
    if assignee and assignee != "User":
        content += f" ({assignee})"
    
    # Map status
    archon_status = task.get("status", "todo").lower()
    todo_status = STATUS_MAPPING.get(archon_status, "pending")
    
    return {
        "id": task["id"],
        "content": content,
        "status": todo_status
    }

def transform_tasks_to_todos(tasks: List[Dict]) -> List[Dict]:
    """
    Transform list of Archon tasks to chat todos format
    
    Args:
        tasks: List of Archon task dictionaries
        
    Returns:
        List of todo dictionaries
    """
    return [transform_task_to_todo(task) for task in tasks]

async def sync_archon_to_chat_todos(project_id: str = DEFAULT_PROJECT_ID, dry_run: bool = False) -> Dict:
    """
    Main synchronization function - get Archon tasks and return todos format
    
    Args:
        project_id: Archon project UUID  
        dry_run: If True, return data without executing
        
    Returns:
        Dictionary with success status, todos, and metadata
    """
    # Get tasks from Archon
    success, tasks, message = await get_archon_tasks(project_id)
    
    if not success:
        return {
            "success": False,
            "error": message,
            "todos": [],
            "metadata": {"project_id": project_id, "task_count": 0}
        }
    
    if not tasks:
        return {
            "success": False, 
            "error": "No tasks found in project",
            "todos": [],
            "metadata": {"project_id": project_id, "task_count": 0}
        }
    
    # Transform to todos
    todos = transform_tasks_to_todos(tasks)
    
    # Generate metadata
    status_counts = {}
    for todo in todos:
        status = todo["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    metadata = {
        "project_id": project_id,
        "task_count": len(tasks),
        "todo_count": len(todos),
        "status_distribution": status_counts,
        "archon_ui_url": f"http://localhost:3837/projects/{project_id}",
        "sync_timestamp": asyncio.get_event_loop().time()
    }
    
    return {
        "success": True,
        "todos": todos,
        "metadata": metadata,
        "todo_write_params": {
            "merge": False,
            "todos": todos
        }
    }

# Convenience functions for common use cases

async def quick_sync() -> List[Dict]:
    """Quick sync - just return the todos list"""
    result = await sync_archon_to_chat_todos()
    return result.get("todos", [])

async def get_sync_status(project_id: str = DEFAULT_PROJECT_ID) -> Dict:
    """Get current sync status without performing sync"""
    success, tasks, message = await get_archon_tasks(project_id)
    
    if not success:
        return {"success": False, "error": message}
    
    status_counts = {}
    for task in tasks:
        status = task.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "success": True,
        "project_id": project_id,
        "total_tasks": len(tasks),
        "status_distribution": status_counts,
        "archon_ui_url": f"http://localhost:3837/projects/{project_id}"
    }

# Example usage function
async def demo_sync():
    """Demo function showing how to use the sync utilities"""
    print("🔄 Starting Archon sync demo...")
    
    # Get sync status first
    status = await get_sync_status()
    print(f"📊 Project has {status['total_tasks']} tasks")
    
    # Perform sync
    result = await sync_archon_to_chat_todos()
    
    if result["success"]:
        print(f"✅ Sync successful: {result['metadata']['todo_count']} todos ready")
        print(f"📋 Status distribution: {result['metadata']['status_distribution']}")
        
        # The todos are now in result["todos"] and can be used with todo_write
        return result["todo_write_params"]
    else:
        print(f"❌ Sync failed: {result['error']}")
        return None

if __name__ == "__main__":
    # Run demo if called directly
    asyncio.run(demo_sync())
