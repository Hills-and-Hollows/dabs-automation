#!/usr/bin/env python3
"""
Add Demonstration Task via MCP Server
Demonstrates MCP server integration by creating a new task through the DABS task management system
"""

import sys
import asyncio
import json
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append('./src')

from integration_hub.task_manager import get_dabs_task_manager, DABSTask, TaskType, TaskPriority, TaskStatus

async def demonstrate_mcp_task_creation():
    """Create a demonstration task to show MCP server integration"""
    print("🚀 Demonstrating MCP Server Task Creation")
    print("=" * 60)
    
    # Get the DABS task manager
    task_manager = get_dabs_task_manager()
    
    # Test MCP connectivity first
    print("📡 Testing MCP Server Connectivity...")
    connected = await task_manager.check_archon_connectivity()
    print(f"MCP Server Status: {'✅ Connected' if connected else '❌ Not Available'}")
    
    # Create a demonstration task
    print("\n📝 Creating Demonstration Task...")
    
    demo_task = DABSTask(
        task_id=f"demo_mcp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        title="MCP Server Integration Demonstration",
        description="Demonstration task created via MCP server integration to validate task synchronization between DABS system and frontend interface. This task shows successful MCP server communication.",
        task_type=TaskType.PERFORMANCE_VALIDATION,
        priority=TaskPriority.HIGH,
        status=TaskStatus.TODO,
        phase="core_integrations",
        assignee="MCP Demo System",
        due_date=datetime.now() + timedelta(days=7),
        acceptance_criteria=[
            "Task appears in frontend interface at localhost:3837/projects",
            "Task data correctly synchronized between systems",
            "MCP server communication validated",
            "Task management workflow confirmed operational"
        ],
        performance_requirements={
            "max_processing_time": 60,  # 1 minute
            "max_response_time": 2,     # 2 seconds
            "sync_verification": True
        }
    )
    
    # Validate performance requirements
    print("🔍 Validating Performance Requirements...")
    is_valid = await task_manager.validate_performance_requirements(demo_task)
    print(f"Performance Validation: {'✅ Passed' if is_valid else '❌ Failed'}")
    
    # Create the task
    print("🏗️  Creating Task via MCP Server...")
    task_id = await task_manager.create_dabs_task(demo_task)
    print(f"✅ Task Created Successfully!")
    print(f"   Task ID: {task_id}")
    print(f"   Title: {demo_task.title}")
    print(f"   Priority: {demo_task.priority.value}")
    print(f"   Phase: {demo_task.phase}")
    
    # Get current tasks to verify creation
    print("\n📋 Verifying Task in System...")
    current_tasks = await task_manager.get_current_tasks()
    
    # Find our demo task
    demo_task_found = None
    for task in current_tasks:
        if task.task_id == task_id:
            demo_task_found = task
            break
    
    if demo_task_found:
        print("✅ Task Successfully Added to Local System")
        print(f"   Status: {demo_task_found.status.value}")
        print(f"   Created: {demo_task_found.created_at.isoformat()}")
    else:
        print("❌ Task not found in local system")
    
    # Get phase progress to show integration
    print("\n📊 Phase Progress After Task Addition...")
    phase_progress = await task_manager.get_phase_progress("core_integrations")
    print(f"Phase: {phase_progress['phase']}")
    print(f"Total Tasks: {phase_progress['total_tasks']}")
    print(f"Progress: {phase_progress['progress']}%")
    print(f"Status Breakdown: {json.dumps(phase_progress['status_breakdown'], indent=2)}")
    
    print("\n🎉 MCP Server Integration Demonstration Complete!")
    print("📍 Task should now be visible at: http://localhost:3837/projects")
    print(f"🔧 Task ID for verification: {task_id}")
    
    return {
        "task_id": task_id,
        "task_title": demo_task.title,
        "mcp_connected": connected,
        "performance_valid": is_valid,
        "phase_progress": phase_progress
    }

if __name__ == "__main__":
    try:
        result = asyncio.run(demonstrate_mcp_task_creation())
        print(f"\n📊 Demo Results: {json.dumps(result, indent=2, default=str)}")
    except Exception as e:
        print(f"❌ Demo failed: {e}")