#!/usr/bin/env python3
"""
ARCHON-TO-CHAT TODO SYNCHRONIZATION TOOL
Reusable script to sync Archon tasks to Cursor chat todos

This tool provides one-command synchronization between Archon project tasks
and Cursor chat todo interface, ensuring perfect alignment and up-to-date visibility.

Usage:
    python scripts/sync_archon_to_chat_todos.py                    # Sync default project
    python scripts/sync_archon_to_chat_todos.py --project-id UUID  # Sync specific project
    python scripts/sync_archon_to_chat_todos.py --status           # Show current status
    python scripts/sync_archon_to_chat_todos.py --dry-run          # Preview changes only

Author: DABS Automation System
Created: 2025-08-23
Project: HH DABS Automation Complete (d010ff76-0202-48e4-8362-40c45e9de39a)
"""

import asyncio
import json
import httpx
import argparse
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class ArchonChatTodoSync:
    """Synchronizes Archon tasks with Cursor chat todos"""
    
    def __init__(self, project_id: str = "d010ff76-0202-48e4-8362-40c45e9de39a"):
        self.project_id = project_id
        self.archon_server = "http://localhost:8281"
        self.archon_ui = "http://localhost:3837"
        
        # Status mapping from Archon to Chat Todo format
        self.status_mapping = {
            "todo": "pending",
            "doing": "in_progress",
            "review": "in_progress",  # Keep review tasks as in_progress since they're active
            "done": "completed",
            "cancelled": "cancelled"
        }
        
        # Priority emoji mapping for visual clarity
        self.priority_emojis = {
            "CRITICAL": "🚨",
            "HIGH": "⚡",
            "MEDIUM": "📊", 
            "LOW": "📝"
        }
    
    async def get_archon_tasks(self) -> Tuple[bool, List[Dict], str]:
        """Retrieve tasks from Archon MCP API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.archon_server}/api/tasks",
                    params={
                        "project_id": self.project_id,
                        "include_closed": "false",
                        "page": 1,
                        "per_page": 100
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        tasks = data.get("tasks", [])
                        return True, tasks, f"Successfully retrieved {len(tasks)} tasks"
                    else:
                        return False, [], f"API error: {data.get('error', 'Unknown error')}"
                else:
                    return False, [], f"HTTP error {response.status_code}: {response.text}"
                    
        except httpx.ConnectError:
            return False, [], "Cannot connect to Archon server. Ensure server is running on http://localhost:8281"
        except Exception as e:
            return False, [], f"Unexpected error: {str(e)}"
    
    def transform_task_to_todo(self, task: Dict) -> Dict:
        """Transform Archon task to chat todo format"""
        
        # Extract priority from title or description
        title = task.get("title", "Untitled Task")
        description = task.get("description", "")
        priority = "MEDIUM"  # default
        
        for p in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if p in title.upper() or p in description.upper():
                priority = p
                break
        
        # Create descriptive content with priority indicator
        priority_indicator = self.priority_emojis.get(priority, "📝")
        
        # Shorten description for todo display (first 100 chars)
        brief_desc = description.split('\\n')[0][:100]
        if len(brief_desc) == 100:
            brief_desc += "..."
        
        content = f"{priority_indicator} {title}"
        if brief_desc:
            content += f" - {brief_desc}"
        
        # Add assignee if present
        assignee = task.get("assignee")
        if assignee and assignee != "User":
            content += f" (Assigned: {assignee})"
        
        # Map status
        archon_status = task.get("status", "todo").lower()
        todo_status = self.status_mapping.get(archon_status, "pending")
        
        return {
            "id": task["id"],  # Keep original Archon ID for reference
            "content": content,
            "status": todo_status
        }
    
    def generate_todo_write_command(self, todos: List[Dict]) -> str:
        """Generate the todo_write command that can be used in chat"""
        
        # Format todos for command
        todos_json = json.dumps(todos, indent=2)
        
        command = f'''todo_write {{
    "merge": false,
    "todos": {todos_json}
}}'''
        
        return command
    
    async def sync_tasks_to_todos(self, dry_run: bool = False) -> Tuple[bool, str]:
        """Main synchronization function"""
        
        print(f"🔄 Starting Archon → Chat Todo synchronization...")
        print(f"📋 Project: {self.project_id}")
        print(f"🌐 Archon UI: {self.archon_ui}/projects/{self.project_id}")
        print()
        
        # Step 1: Get tasks from Archon
        success, tasks, message = await self.get_archon_tasks()
        if not success:
            return False, message
        
        if not tasks:
            return False, "No tasks found in Archon project"
        
        print(f"✅ Retrieved {len(tasks)} tasks from Archon")
        
        # Step 2: Transform tasks to todos
        todos = []
        status_counts = {"pending": 0, "in_progress": 0, "completed": 0}
        
        for task in tasks:
            todo = self.transform_task_to_todo(task)
            todos.append(todo)
            status_counts[todo["status"]] = status_counts.get(todo["status"], 0) + 1
        
        print(f"🔄 Transformed to {len(todos)} chat todos:")
        print(f"   📋 Pending: {status_counts['pending']}")
        print(f"   🔄 In Progress: {status_counts['in_progress']}")  
        print(f"   ✅ Completed: {status_counts['completed']}")
        print()
        
        # Step 3: Generate command or actually sync
        if dry_run:
            print("🧪 DRY RUN MODE - Preview of todo_write command:")
            print("─" * 80)
            command = self.generate_todo_write_command(todos)
            print(command)
            print("─" * 80)
            return True, f"Dry run complete. {len(todos)} todos ready for sync."
        else:
            # In a real implementation, you'd call the todo_write function here
            # For now, we'll output the command that needs to be executed
            command = self.generate_todo_write_command(todos)
            
            # Save command to file for easy execution
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            command_file = f"todo_sync_command_{timestamp}.json"
            
            with open(command_file, 'w') as f:
                json.dump({
                    "timestamp": timestamp,
                    "project_id": self.project_id,
                    "todo_count": len(todos),
                    "command": "todo_write",
                    "parameters": {
                        "merge": False,
                        "todos": todos
                    }
                }, f, indent=2)
            
            print(f"💾 Sync command saved to: {command_file}")
            print(f"🚀 Ready to execute todo synchronization!")
            print()
            print("To execute in chat, use:")
            print(f"todo_write({{'merge': False, 'todos': {json.dumps(todos)}}})")
            
            return True, f"Synchronization prepared. {len(todos)} todos ready to sync."
    
    async def show_status(self) -> str:
        """Show current Archon project status"""
        success, tasks, message = await self.get_archon_tasks()
        
        if not success:
            return f"❌ Error getting status: {message}"
        
        status_counts = {}
        for task in tasks:
            status = task.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        result = f"📊 Archon Project Status ({self.project_id}):\\n"
        result += f"📋 Total Tasks: {len(tasks)}\\n"
        result += f"🌐 Archon UI: {self.archon_ui}/projects/{self.project_id}\\n\\n"
        
        for status, count in sorted(status_counts.items()):
            emoji = {"todo": "📋", "doing": "🔄", "review": "👀", "done": "✅"}.get(status, "❓")
            result += f"   {emoji} {status.upper()}: {count}\\n"
        
        return result

async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Sync Archon tasks to Cursor chat todos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python sync_archon_to_chat_todos.py                    # Sync default DABS project
    python sync_archon_to_chat_todos.py --status          # Show current status
    python sync_archon_to_chat_todos.py --dry-run         # Preview sync only
    python sync_archon_to_chat_todos.py --project-id UUID # Sync specific project
        """
    )
    
    parser.add_argument(
        "--project-id",
        default="d010ff76-0202-48e4-8362-40c45e9de39a",
        help="Archon project ID to sync (default: DABS project)"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current Archon project status only"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview synchronization without executing"
    )
    
    args = parser.parse_args()
    
    # Create sync instance
    sync = ArchonChatTodoSync(project_id=args.project_id)
    
    try:
        if args.status:
            # Show status only
            result = await sync.show_status()
            print(result)
        else:
            # Perform synchronization
            success, message = await sync.sync_tasks_to_todos(dry_run=args.dry_run)
            
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\\n🛑 Synchronization cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
