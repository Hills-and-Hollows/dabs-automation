#!/usr/bin/env python3
"""
DABS Task Management Server
Standalone task management system for DABS project without Supabase dependency
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    TODO = "todo"
    DOING = "doing" 
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class DABSTask:
    task_id: str
    title: str
    description: str
    task_type: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.TODO
    phase: str = "foundation"
    assignee: str = "team"
    created_at: datetime = None
    updated_at: datetime = None
    due_date: Optional[datetime] = None
    dependencies: List[str] = None
    acceptance_criteria: List[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.dependencies is None:
            self.dependencies = []
        if self.acceptance_criteria is None:
            self.acceptance_criteria = []

class DABSTaskManager:
    def __init__(self, db_path: str = "dabs_tasks.json"):
        self.db_path = Path(db_path)
        self.tasks: Dict[str, DABSTask] = {}
        self.load_tasks()
        
    def load_tasks(self):
        """Load tasks from JSON file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r') as f:
                    tasks_data = json.load(f)
                
                self.tasks = {}
                for task_id, task_data in tasks_data.items():
                    task = DABSTask(
                        task_id=task_data['task_id'],
                        title=task_data['title'],
                        description=task_data['description'],
                        task_type=task_data['task_type'],
                        priority=TaskPriority(task_data['priority']),
                        status=TaskStatus(task_data['status']),
                        phase=task_data.get('phase', 'foundation'),
                        assignee=task_data.get('assignee', 'team'),
                        created_at=datetime.fromisoformat(task_data['created_at']) if task_data.get('created_at') else datetime.now(),
                        updated_at=datetime.fromisoformat(task_data['updated_at']) if task_data.get('updated_at') else datetime.now(),
                        dependencies=task_data.get('dependencies', []),
                        acceptance_criteria=task_data.get('acceptance_criteria', [])
                    )
                    self.tasks[task_id] = task
                    
                logger.info(f"Loaded {len(self.tasks)} tasks from {self.db_path}")
            except Exception as e:
                logger.error(f"Failed to load tasks: {e}")
        else:
            logger.info("No existing task database found, starting fresh")
    
    def save_tasks(self):
        """Save tasks to JSON file"""
        try:
            tasks_data = {}
            for task_id, task in self.tasks.items():
                tasks_data[task_id] = {
                    'task_id': task.task_id,
                    'title': task.title,
                    'description': task.description,
                    'task_type': task.task_type,
                    'priority': task.priority.value,
                    'status': task.status.value,
                    'phase': task.phase,
                    'assignee': task.assignee,
                    'created_at': task.created_at.isoformat(),
                    'updated_at': task.updated_at.isoformat(),
                    'dependencies': task.dependencies,
                    'acceptance_criteria': task.acceptance_criteria
                }
            
            with open(self.db_path, 'w') as f:
                json.dump(tasks_data, f, indent=2)
                
            logger.info(f"Saved {len(self.tasks)} tasks to {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")
    
    def create_task(self, task_data: Dict) -> str:
        """Create a new task"""
        task_id = f"dabs_{len(self.tasks) + 1:03d}"
        
        task = DABSTask(
            task_id=task_id,
            title=task_data['title'],
            description=task_data['description'],
            task_type=task_data.get('task_type', 'development'),
            priority=TaskPriority(task_data.get('priority', 'medium')),
            phase=task_data.get('phase', 'foundation'),
            assignee=task_data.get('assignee', 'team'),
            dependencies=task_data.get('dependencies', []),
            acceptance_criteria=task_data.get('acceptance_criteria', [])
        )
        
        self.tasks[task_id] = task
        self.save_tasks()
        
        return task_id
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        if task_id not in self.tasks:
            return False
            
        self.tasks[task_id].status = TaskStatus(status)
        self.tasks[task_id].updated_at = datetime.now()
        self.save_tasks()
        
        return True
    
    def get_tasks(self, status_filter: Optional[str] = None, phase_filter: Optional[str] = None) -> List[Dict]:
        """Get tasks with optional filtering"""
        tasks = list(self.tasks.values())
        
        if status_filter:
            tasks = [t for t in tasks if t.status.value == status_filter]
        if phase_filter:
            tasks = [t for t in tasks if t.phase == phase_filter]
            
        # Sort by priority and created date
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        tasks.sort(key=lambda t: (priority_order.get(t.priority.value, 0), t.created_at), reverse=True)
        
        return [self._task_to_dict(t) for t in tasks]
    
    def get_phase_progress(self, phase: str) -> Dict:
        """Get progress for a specific phase"""
        phase_tasks = [t for t in self.tasks.values() if t.phase == phase]
        
        if not phase_tasks:
            return {
                "phase": phase,
                "total_tasks": 0,
                "completed_tasks": 0,
                "progress": 0,
                "status_breakdown": {}
            }
        
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = len([t for t in phase_tasks if t.status == status])
        
        completed_tasks = status_counts.get("done", 0)
        total_tasks = len(phase_tasks)
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "phase": phase,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress": round(progress, 1),
            "status_breakdown": status_counts
        }
    
    def _task_to_dict(self, task: DABSTask) -> Dict:
        """Convert task to dictionary"""
        return {
            'task_id': task.task_id,
            'title': task.title,
            'description': task.description,
            'task_type': task.task_type,
            'priority': task.priority.value,
            'status': task.status.value,
            'phase': task.phase,
            'assignee': task.assignee,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat(),
            'dependencies': task.dependencies,
            'acceptance_criteria': task.acceptance_criteria
        }

# Initialize task manager
task_manager = DABSTaskManager()

# Create FastAPI app
app = FastAPI(
    title="DABS Task Management Server",
    description="Standalone task management for DABS automation project",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "DABS Task Management Server",
        "status": "running",
        "tasks_count": len(task_manager.tasks)
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "tasks": len(task_manager.tasks)}

@app.post("/mcp/tools/create_dabs_task")
async def create_dabs_task(task_data: Dict[str, Any]):
    """Create a new DABS task"""
    try:
        task_id = task_manager.create_task(task_data)
        return {
            "task": {"id": task_id},
            "message": "Task created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/mcp/tools/get_dabs_project_status")
async def get_dabs_project_status(phase: str = "all"):
    """Get DABS project status"""
    if phase == "all":
        phases = ["foundation", "core_integrations", "compliance_reporting", "optimization"]
        status = {
            "project": "DABS Integration System",
            "overall_progress": 0,
            "phases": {},
            "total_tasks": len(task_manager.tasks)
        }
        
        total_completed = 0
        total_tasks = 0
        
        for p in phases:
            progress = task_manager.get_phase_progress(p)
            status["phases"][p] = {
                "status": "completed" if progress["progress"] == 100 else "in_progress" if progress["progress"] > 0 else "planned",
                "progress": progress["progress"]
            }
            total_completed += progress["completed_tasks"]
            total_tasks += progress["total_tasks"]
        
        status["overall_progress"] = round((total_completed / total_tasks * 100) if total_tasks > 0 else 0, 1)
        return status
    else:
        return task_manager.get_phase_progress(phase)

@app.get("/tasks")
async def get_tasks(status: Optional[str] = None, phase: Optional[str] = None):
    """Get all tasks with optional filtering"""
    return {
        "tasks": task_manager.get_tasks(status, phase),
        "total": len(task_manager.tasks)
    }

@app.put("/tasks/{task_id}/status")
async def update_task_status(task_id: str, status_data: Dict[str, str]):
    """Update task status"""
    success = task_manager.update_task_status(task_id, status_data["status"])
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"message": "Task status updated", "task_id": task_id}

@app.get("/mcp/sse") 
async def mcp_sse():
    """MCP Server-Sent Events endpoint"""
    return {"message": "DABS Task Management MCP endpoint", "transport": "sse"}

if __name__ == "__main__":
    print("🚀 Starting DABS Task Management Server")
    print("📍 Server: http://localhost:8151")
    print("🔧 MCP endpoint: http://localhost:8151/mcp/sse")
    print("📋 Health check: http://localhost:8151/health")
    
    # Initialize with the 18 critical manager tasks if no tasks exist
    if len(task_manager.tasks) == 0:
        logger.info("Initializing with critical manager tasks...")
        critical_tasks = [
            {
                "title": "Contact SSCS vendor for technical integration documentation",
                "description": "Get technical specs and API documentation from SSCS vendor for POS integration",
                "task_type": "vendor_integration",
                "priority": "critical",
                "phase": "foundation"
            },
            {
                "title": "Build DABS Processing Engine for 1,239 SKU automation system",
                "description": "Core automation engine for processing monthly DABS Excel files with 1,239+ SKUs",
                "task_type": "core_development",
                "priority": "critical",
                "phase": "core_integrations"
            },
            {
                "title": "Develop SSCS Integration System for automated POS price sync",
                "description": "Automated price synchronization between DABS and SSCS POS system",
                "task_type": "integration",
                "priority": "critical",
                "phase": "core_integrations"
            },
            {
                "title": "Implement restaurant credit card processing fee solution",
                "description": "Automated fee calculation and collection for restaurant credit card orders",
                "task_type": "payment_processing",
                "priority": "high",
                "phase": "core_integrations"
            },
            {
                "title": "Create validation and alert dashboard for real-time progress tracking",
                "description": "Dashboard for Tessa to monitor processing status and handle exceptions",
                "task_type": "dashboard",
                "priority": "high",
                "phase": "core_integrations"
            },
            {
                "title": "Build restaurant order automation to replace manual email processing",
                "description": "Automated restaurant order processing system replacing manual email workflow",
                "task_type": "automation",
                "priority": "high",
                "phase": "core_integrations"
            },
            {
                "title": "Develop UPC resolution system for new item management",
                "description": "Automated UPC lookup and resolution for new DABS items",
                "task_type": "data_processing",
                "priority": "high",
                "phase": "core_integrations"
            },
            {
                "title": "Implement secure PCI-compliant payment system for restaurants",
                "description": "Secure payment processing system meeting PCI compliance standards",
                "task_type": "security",
                "priority": "high",
                "phase": "core_integrations"
            },
            {
                "title": "Set up QuickBooks OAuth integration and inventory sync",
                "description": "Bidirectional inventory synchronization with QuickBooks Online",
                "task_type": "integration",
                "priority": "medium",
                "phase": "compliance_reporting"
            },
            {
                "title": "Create Utah compliance automation for monthly DABS reporting",
                "description": "Automated monthly reporting system for Utah Package Agency compliance",
                "task_type": "compliance",
                "priority": "medium",
                "phase": "compliance_reporting"
            },
            {
                "title": "Build case vs bottle handling improvements for POS scanning",
                "description": "Enhanced POS scanning for case-level vs individual bottle transactions",
                "task_type": "pos_enhancement",
                "priority": "medium",
                "phase": "optimization"
            },
            {
                "title": "Implement ACH and financial tracking for bank reconciliation",
                "description": "Automated financial tracking and bank reconciliation system",
                "task_type": "financial_automation",
                "priority": "medium",
                "phase": "compliance_reporting"
            },
            {
                "title": "Migrate from local development to production-ready systems",
                "description": "Production deployment and infrastructure setup",
                "task_type": "deployment",
                "priority": "medium",
                "phase": "optimization"
            },
            {
                "title": "Establish proper development team and budget allocation",
                "description": "Resource planning and team allocation for project completion",
                "task_type": "project_management",
                "priority": "medium",
                "phase": "foundation"
            }
        ]
        
        for task_data in critical_tasks:
            task_manager.create_task(task_data)
        
        logger.info(f"Initialized with {len(critical_tasks)} critical tasks")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8152,
        log_level="info"
    )