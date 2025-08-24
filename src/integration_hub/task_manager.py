#!/usr/bin/env python3
"""
Task Manager for Integration Hub - Hills & Hollows LLC
Task management integration with Archon MCP server and DABS workflows

Manages task coordination between:
- Archon MCP server task management
- DABS automation workflows
- Integration hub coordination
- Utah Package Agency compliance tracking

Author: DABS Automation System
Created: 2025-08-23
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


class TaskStatus(Enum):
    """Task execution status"""
    TODO = "todo"
    DOING = "doing"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """DABS-specific task types"""
    DABS_PROCESSING = "dabs_processing"
    SSCS_INTEGRATION = "sscs_integration"
    QUICKBOOKS_SYNC = "quickbooks_sync"
    COMPLIANCE_CHECK = "compliance_check"
    PERFORMANCE_VALIDATION = "performance_validation"
    UTAH_REPORTING = "utah_reporting"


@dataclass
class DABSTask:
    """DABS-specific task with Utah Package Agency context"""
    task_id: str
    title: str
    description: str
    task_type: TaskType
    priority: TaskPriority
    status: TaskStatus = TaskStatus.TODO
    assignee: str = "User"
    phase: str = "foundation"
    feature: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    utah_compliance_required: bool = True
    performance_requirements: Dict[str, Any] = field(default_factory=dict)
    
    def to_archon_format(self) -> Dict[str, Any]:
        """Convert to Archon MCP server format"""
        return {
            "title": self.title,
            "description": self.description,
            "assignee": self.assignee,
            "task_order": self._get_priority_order(),
            "feature": self.feature or self.task_type.value,
            "sources": self._generate_sources(),
            "code_examples": self._generate_code_examples()
        }
    
    def _get_priority_order(self) -> int:
        """Convert priority to numeric order"""
        priority_map = {
            TaskPriority.URGENT: 100,
            TaskPriority.CRITICAL: 90,
            TaskPriority.HIGH: 80,
            TaskPriority.MEDIUM: 50,
            TaskPriority.LOW: 20
        }
        return priority_map.get(self.priority, 50)
    
    def _generate_sources(self) -> List[Dict[str, str]]:
        """Generate source references based on task type"""
        base_sources = [
            {
                "url": "docs/FUNCTIONAL_REQUIREMENTS.md",
                "type": "requirements",
                "relevance": "Core business requirements for DABS system"
            },
            {
                "url": "docs/ACCEPTANCE_CRITERIA.md", 
                "type": "validation",
                "relevance": "Success criteria and validation requirements"
            }
        ]
        
        # Add task-type specific sources
        type_sources = {
            TaskType.DABS_PROCESSING: [
                {
                    "url": "config/dabs_config.json",
                    "type": "configuration",
                    "relevance": "DABS processing configuration and validation rules"
                }
            ],
            TaskType.QUICKBOOKS_SYNC: [
                {
                    "url": "research reports/research-paper-qbo-mcp.md",
                    "type": "research",
                    "relevance": "QuickBooks OAuth 2.0 and MCP integration patterns"
                }
            ],
            TaskType.UTAH_REPORTING: [
                {
                    "url": "docs/NON_FUNCTIONAL_REQUIREMENTS.md",
                    "type": "compliance",
                    "relevance": "Utah Package Agency compliance requirements"
                }
            ]
        }
        
        return base_sources + type_sources.get(self.task_type, [])
    
    def _generate_code_examples(self) -> List[Dict[str, str]]:
        """Generate code example references based on task type"""
        base_examples = [
            {
                "file": "src/integration_hub/coordinator.py",
                "function": "IntegrationCoordinator",
                "purpose": "Central coordination pattern for all integrations"
            }
        ]
        
        type_examples = {
            TaskType.DABS_PROCESSING: [
                {
                    "file": "src/processors/dabs_processor.py",
                    "function": "DABSProcessor.process_dabs_file",
                    "purpose": "DABS Excel file processing pattern"
                }
            ],
            TaskType.QUICKBOOKS_SYNC: [
                {
                    "file": "src/automation/workflows/quickbooks_integration/qb_oauth_manager.py",
                    "function": "QuickBooksOAuthManager",
                    "purpose": "OAuth 2.0 authentication and token management"
                }
            ]
        }
        
        return base_examples + type_examples.get(self.task_type, [])


class DABSTaskManager:
    """
    DABS Task Manager with Archon MCP Integration
    
    Manages task coordination between local DABS workflows and Archon MCP server.
    Ensures all tasks follow Utah Package Agency compliance and performance requirements.
    """
    
    def __init__(self, archon_mcp_url: str = "http://localhost:8152"):
        self.archon_mcp_url = archon_mcp_url
        self.local_tasks: Dict[str, DABSTask] = {}
        self.archon_project_id: Optional[str] = None
        self.timeout = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
        
        # Utah Package Agency specific settings
        self.utah_compliance_enabled = True
        self.performance_monitoring = True
        
        logger.info("DABS Task Manager initialized with Archon MCP integration")
    
    async def check_archon_connectivity(self) -> bool:
        """Check if Archon MCP server is available (MANDATORY per .cursorrules)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.archon_mcp_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Archon MCP server not available: {e}")
            return False
    
    async def initialize_dabs_project(self, force_create: bool = False) -> str:
        """Initialize DABS project in Archon MCP server (simplified for basic server)"""
        if not await self.check_archon_connectivity():
            logger.warning("Archon MCP server not available - running in local-only mode")
            # Generate a local project ID instead of failing
            self.archon_project_id = f"local_dabs_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return self.archon_project_id
        
        # For basic DABS server, we don't need explicit project creation
        # Tasks are created directly and the server handles project context
        self.archon_project_id = "dabs_integration_system"
        logger.info(f"DABS project initialized: {self.archon_project_id}")
        return self.archon_project_id
    
    async def create_dabs_task(self, task: DABSTask) -> str:
        """Create task in both local storage and Archon MCP server"""
        # Store locally first
        self.local_tasks[task.task_id] = task
        
        # Sync with Archon if available
        if await self.check_archon_connectivity():
            try:
                if not self.archon_project_id:
                    await self.initialize_dabs_project()
                
                # Use working create_dabs_task endpoint
                archon_task_data = task.to_archon_format()
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.archon_mcp_url}/mcp/tools/create_dabs_task",
                        json=archon_task_data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        archon_task_id = result.get("task", {}).get("id")
                        if archon_task_id:
                            task.archon_task_id = archon_task_id
                            logger.info(f"Task synced with Archon: {archon_task_id}")
                    
            except Exception as e:
                logger.warning(f"Failed to sync task with Archon: {e}")
        
        return task.task_id
    
    async def update_task_status(self, task_id: str, status: TaskStatus, notes: Optional[str] = None) -> bool:
        """Update task status in both local storage and Archon"""
        if task_id not in self.local_tasks:
            logger.error(f"Task {task_id} not found in local storage")
            return False
        
        # Update local task
        task = self.local_tasks[task_id]
        task.status = status
        task.updated_at = datetime.now()
        
        if notes:
            task.description += f"\n\nUpdate {datetime.now().isoformat()}: {notes}"
        
        # Sync with Archon if available (limited in basic server)
        if await self.check_archon_connectivity() and hasattr(task, 'archon_task_id'):
            try:
                # Basic DABS server doesn't have task update endpoint
                # We'll log the status change locally and rely on task recreation for major updates
                logger.info(f"Task {task_id} status updated to {status.value} (local update only)")
                    
            except Exception as e:
                logger.warning(f"Failed to sync task status with Archon: {e}")
        
        return True
    
    async def get_current_tasks(self, status_filter: Optional[TaskStatus] = None) -> List[DABSTask]:
        """Get current tasks with optional status filtering"""
        tasks = list(self.local_tasks.values())
        
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
        
        # Sort by priority and creation date
        tasks.sort(key=lambda t: (t._get_priority_order(), t.created_at), reverse=True)
        
        return tasks
    
    async def get_phase_progress(self, phase: str) -> Dict[str, Any]:
        """Get progress for specific DABS phase"""
        phase_tasks = [t for t in self.local_tasks.values() if t.phase == phase]
        
        if not phase_tasks:
            return {"phase": phase, "total_tasks": 0, "progress": 0}
        
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
            "status_breakdown": status_counts,
            "utah_compliance_tasks": len([t for t in phase_tasks if t.utah_compliance_required])
        }
    
    async def validate_performance_requirements(self, task: DABSTask) -> bool:
        """Validate task meets DABS performance requirements"""
        if not task.performance_requirements:
            return True
        
        # Check against performance gates from .cursor/rules/performance-gates.mdc
        required_processing_time = task.performance_requirements.get("max_processing_time", 900)  # 15 minutes
        required_response_time = task.performance_requirements.get("max_response_time", 2)  # 2 seconds
        
        # Validate against DABS requirements
        if task.task_type == TaskType.DABS_PROCESSING:
            # Must process 1,239 SKUs within 15 minutes
            if required_processing_time > 900:
                logger.error(f"Task {task.task_id} exceeds DABS processing time requirement")
                return False
        
        logger.info(f"Task {task.task_id} meets performance requirements")
        return True
    
    async def create_phase_tasks(self, phase: str) -> List[str]:
        """Create standard tasks for DABS project phase"""
        phase_templates = {
            "foundation": [
                {
                    "title": "Business Requirements Analysis",
                    "description": "Complete analysis of Hills & Hollows LLC business requirements and Utah Package Agency compliance needs",
                    "task_type": TaskType.COMPLIANCE_CHECK,
                    "priority": TaskPriority.CRITICAL
                },
                {
                    "title": "DABS Data Structure Analysis", 
                    "description": "Analyze 1,239 SKU data structure and processing requirements",
                    "task_type": TaskType.DABS_PROCESSING,
                    "priority": TaskPriority.HIGH
                }
            ],
            "core_integrations": [
                {
                    "title": "SSCS POS Integration",
                    "description": "Implement SSCS POS system integration via CPB vendor import",
                    "task_type": TaskType.SSCS_INTEGRATION,
                    "priority": TaskPriority.CRITICAL,
                    "performance_requirements": {"max_processing_time": 900}
                },
                {
                    "title": "QuickBooks OAuth Implementation",
                    "description": "Implement OAuth 2.0 authentication for QuickBooks Online API",
                    "task_type": TaskType.QUICKBOOKS_SYNC,
                    "priority": TaskPriority.HIGH
                }
            ],
            "compliance_reporting": [
                {
                    "title": "Automated DABS Monthly Reporting",
                    "description": "Implement automated monthly reporting to Utah DABS system",
                    "task_type": TaskType.UTAH_REPORTING,
                    "priority": TaskPriority.CRITICAL,
                    "utah_compliance_required": True
                }
            ]
        }
        
        template_tasks = phase_templates.get(phase, [])
        created_task_ids = []
        
        for template in template_tasks:
            task = DABSTask(
                task_id=f"{phase}_{len(self.local_tasks)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=template["title"],
                description=template["description"],
                task_type=template["task_type"],
                priority=template["priority"],
                status=TaskStatus.TODO,
                phase=phase,
                utah_compliance_required=template.get("utah_compliance_required", True),
                performance_requirements=template.get("performance_requirements", {})
            )
            
            task_id = await self.create_dabs_task(task)
            created_task_ids.append(task_id)
        
        logger.info(f"Created {len(created_task_ids)} tasks for phase: {phase}")
        return created_task_ids
    
    async def sync_with_archon(self) -> Dict[str, Any]:
        """Sync all local tasks with Archon MCP server"""
        if not await self.check_archon_connectivity():
            return {"success": False, "error": "Archon MCP server not available"}
        
        sync_results = {
            "tasks_synced": 0,
            "tasks_failed": 0,
            "errors": []
        }
        
        for task in self.local_tasks.values():
            try:
                if not hasattr(task, 'archon_task_id'):
                    # Create in Archon
                    await self.create_dabs_task(task)
                    sync_results["tasks_synced"] += 1
                else:
                    # Update in Archon
                    await self.update_task_status(task.task_id, task.status)
                    sync_results["tasks_synced"] += 1
                    
            except Exception as e:
                sync_results["tasks_failed"] += 1
                sync_results["errors"].append(f"Task {task.task_id}: {str(e)}")
        
        return sync_results
    
    async def generate_utah_compliance_report(self) -> Dict[str, Any]:
        """Generate Utah Package Agency compliance report for all tasks"""
        compliance_tasks = [t for t in self.local_tasks.values() if t.utah_compliance_required]
        
        compliance_status = {
            "total_compliance_tasks": len(compliance_tasks),
            "completed_compliance_tasks": len([t for t in compliance_tasks if t.status == TaskStatus.DONE]),
            "blocked_compliance_tasks": len([t for t in compliance_tasks if t.status == TaskStatus.BLOCKED]),
            "critical_deadlines": [],
            "compliance_percentage": 0
        }
        
        if compliance_tasks:
            completed = compliance_status["completed_compliance_tasks"] 
            total = compliance_status["total_compliance_tasks"]
            compliance_status["compliance_percentage"] = round((completed / total) * 100, 1)
        
        # Check for critical deadlines (Utah monthly reporting deadline: 10th of following month)
        current_date = datetime.now()
        for task in compliance_tasks:
            if task.due_date and task.status != TaskStatus.DONE:
                days_until_due = (task.due_date - current_date).days
                if days_until_due <= 5:  # Within 5 days
                    compliance_status["critical_deadlines"].append({
                        "task_id": task.task_id,
                        "title": task.title,
                        "due_date": task.due_date.isoformat(),
                        "days_remaining": days_until_due
                    })
        
        return compliance_status


# Global task manager instance
_task_manager = None


def get_dabs_task_manager() -> DABSTaskManager:
    """Get or create global DABS task manager"""
    global _task_manager
    if _task_manager is None:
        _task_manager = DABSTaskManager()
    return _task_manager


async def main():
    """Example usage and testing"""
    task_manager = get_dabs_task_manager()
    
    # Test Archon connectivity
    is_connected = await task_manager.check_archon_connectivity()
    print(f"Archon MCP connectivity: {'✅ Connected' if is_connected else '❌ Not available'}")
    
    # Create sample DABS task
    sample_task = DABSTask(
        task_id="dabs_test_001",
        title="Test SSCS Integration",
        description="Validate SSCS CPB vendor import functionality",
        task_type=TaskType.SSCS_INTEGRATION,
        priority=TaskPriority.HIGH,
        phase="core_integrations",
        performance_requirements={"max_processing_time": 300}  # 5 minutes
    )
    
    # Validate performance requirements
    is_valid = await task_manager.validate_performance_requirements(sample_task)
    print(f"Performance validation: {'✅ Passed' if is_valid else '❌ Failed'}")
    
    # Create task
    task_id = await task_manager.create_dabs_task(sample_task)
    print(f"Task created: {task_id}")
    
    # Get phase progress
    progress = await task_manager.get_phase_progress("core_integrations")
    print(f"Phase progress: {json.dumps(progress, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())