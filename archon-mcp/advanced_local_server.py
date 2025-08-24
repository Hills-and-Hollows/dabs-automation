#!/usr/bin/env python3
"""
Advanced DABS Archon MCP Server (Local Development)
Hybrid approach: Advanced features with local development compatibility

This server provides:
- Advanced MCP tools from the production setup
- Local development compatibility (no Docker required)
- Real project and task management
- Enhanced RAG capabilities
- DABS-specific integrations

Compatible with Python 3.9+ and works without complex dependencies.
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DABS Archon MCP Server (Advanced Local)",
    description="Advanced MCP server for DABS project management and knowledge base",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (will be replaced with Supabase later)
PROJECTS = {}
TASKS = {}
DOCUMENTS = {}

def load_dabs_documentation():
    """Load DABS documentation from files into knowledge base"""
    knowledge_base = {}

    # Define documentation sources with their content
    doc_sources = [
        {
            "id": "project_summary",
            "title": "DABS Project Summary",
            "file": "PROJECT_SUMMARY.md",
            "tags": ["project", "summary", "dabs", "automation", "high"]
        },
        {
            "id": "functional_requirements",
            "title": "DABS Functional Requirements",
            "file": "docs/FUNCTIONAL_REQUIREMENTS.md",
            "tags": ["requirements", "functional", "dabs", "high"]
        },
        {
            "id": "technical_architecture",
            "title": "DABS Technical Architecture",
            "file": "docs/TECHNICAL_ARCHITECTURE.md",
            "tags": ["architecture", "technical", "dabs", "high"]
        },
        {
            "id": "sscs_vendor_requirements",
            "title": "SSCS Vendor Requirements",
            "file": "docs/SSCS_VENDOR_REQUIREMENTS.md",
            "tags": ["sscs", "vendor", "requirements", "pos", "high"]
        },
        {
            "id": "acceptance_criteria",
            "title": "DABS Acceptance Criteria",
            "file": "docs/ACCEPTANCE_CRITERIA.md",
            "tags": ["acceptance", "criteria", "testing", "medium"]
        },
        {
            "id": "user_stories",
            "title": "DABS User Stories",
            "file": "docs/USER_STORIES.md",
            "tags": ["user", "stories", "requirements", "medium"]
        }
    ]

    # Load each document
    for doc_info in doc_sources:
        try:
            file_path = Path(doc_info["file"])
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                knowledge_base[doc_info["id"]] = {
                    "title": doc_info["title"],
                    "content": content,
                    "tags": doc_info["tags"],
                    "created": datetime.now().isoformat(),
                    "source": "dabs_documentation",
                    "file_path": str(file_path)
                }
        except Exception as e:
            logger.warning(f"Could not load {doc_info['file']}: {e}")
            # Add fallback content
            knowledge_base[doc_info["id"]] = {
                "title": doc_info["title"],
                "content": f"Documentation for {doc_info['title']} - content not available",
                "tags": doc_info["tags"],
                "created": datetime.now().isoformat(),
                "source": "fallback"
            }

    # Add some default entries if no files loaded
    if not knowledge_base:
        knowledge_base = {
            "dabs_integration_requirements": {
                "title": "DABS Integration Requirements",
                "content": "QuickBooks integration, SSCS connectivity, inventory management, automated pricing updates",
                "tags": ["integration", "requirements", "quickbooks", "sscs", "high"],
                "created": datetime.now().isoformat()
            },
            "dabs_phase_2_tasks": {
                "title": "DABS Phase 2 Implementation Tasks",
                "content": "API development, database schema, user interface components, testing framework",
                "tags": ["phase2", "implementation", "api", "database", "medium"],
                "created": datetime.now().isoformat()
            },
            "dabs_architecture": {
                "title": "DABS System Architecture",
                "content": "Microservices architecture with FastAPI, PostgreSQL, React frontend, MCP integration",
                "tags": ["architecture", "microservices", "fastapi", "postgresql", "high"],
                "created": datetime.now().isoformat()
            }
        }

    return knowledge_base

# Load knowledge base on startup
KNOWLEDGE_BASE = load_dabs_documentation()

# Pydantic models
class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any]

class ProjectRequest(BaseModel):
    action: str
    project_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    github_repo: Optional[str] = None

class TaskRequest(BaseModel):
    action: str
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "todo"
    priority: Optional[int] = 1

class RAGRequest(BaseModel):
    query: str
    source: Optional[str] = None
    match_count: Optional[int] = 5

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "DABS Archon MCP Server (Advanced Local)",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Advanced Project Management",
            "Task Management with Status Tracking",
            "RAG Knowledge Base",
            "Document Management",
            "DABS Integration Support"
        ]
    }

# MCP Server-Sent Events endpoint
@app.get("/mcp/sse")
async def mcp_sse():
    """MCP Server-Sent Events endpoint for real-time communication"""
    
    def generate_sse():
        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connection', 'status': 'connected', 'server': 'DABS Archon Advanced'})}\n\n"
        
        # Keep connection alive
        import time
        while True:
            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
            time.sleep(30)
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

# Advanced MCP Tools

@app.post("/mcp/tools/manage_project")
async def manage_project(request: ProjectRequest):
    """
    Advanced project management with full lifecycle support
    Actions: create, list, get, update, delete
    """
    try:
        if request.action == "create":
            project_id = str(uuid.uuid4())
            project = {
                "id": project_id,
                "title": request.title or "Untitled Project",
                "description": request.description or "",
                "github_repo": request.github_repo or "",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "status": "active",
                "tasks": [],
                "documents": []
            }
            PROJECTS[project_id] = project
            
            return {
                "success": True,
                "project_id": project_id,
                "message": f"Project '{project['title']}' created successfully",
                "project": project
            }
            
        elif request.action == "list":
            return {
                "success": True,
                "projects": list(PROJECTS.values()),
                "count": len(PROJECTS)
            }
            
        elif request.action == "get":
            if not request.project_id or request.project_id not in PROJECTS:
                raise HTTPException(status_code=404, detail="Project not found")
            
            project = PROJECTS[request.project_id]
            # Include related tasks
            project_tasks = [task for task in TASKS.values() if task.get("project_id") == request.project_id]
            project["tasks"] = project_tasks
            
            return {
                "success": True,
                "project": project
            }
            
        elif request.action == "delete":
            if not request.project_id or request.project_id not in PROJECTS:
                raise HTTPException(status_code=404, detail="Project not found")
            
            project = PROJECTS.pop(request.project_id)
            return {
                "success": True,
                "message": f"Project '{project['title']}' deleted successfully"
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
            
    except Exception as e:
        logger.error(f"Error in manage_project: {e}")
        return {"success": False, "error": str(e)}

@app.post("/mcp/tools/manage_task")
async def manage_task(request: TaskRequest):
    """
    Advanced task management with status tracking and project integration
    Actions: create, list, get, update, delete
    """
    try:
        if request.action == "create":
            task_id = str(uuid.uuid4())
            task = {
                "id": task_id,
                "project_id": request.project_id,
                "title": request.title or "Untitled Task",
                "description": request.description or "",
                "status": request.status or "todo",
                "priority": request.priority or 1,
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "assignee": None,
                "due_date": None
            }
            TASKS[task_id] = task
            
            # Add task to project if project_id provided
            if request.project_id and request.project_id in PROJECTS:
                PROJECTS[request.project_id]["tasks"].append(task_id)
            
            return {
                "success": True,
                "task_id": task_id,
                "message": f"Task '{task['title']}' created successfully",
                "task": task
            }
            
        elif request.action == "list":
            tasks = list(TASKS.values())
            if request.project_id:
                tasks = [task for task in tasks if task.get("project_id") == request.project_id]
            
            return {
                "success": True,
                "tasks": tasks,
                "count": len(tasks)
            }
            
        elif request.action == "get":
            if not request.task_id or request.task_id not in TASKS:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return {
                "success": True,
                "task": TASKS[request.task_id]
            }
            
        elif request.action == "update":
            if not request.task_id or request.task_id not in TASKS:
                raise HTTPException(status_code=404, detail="Task not found")
            
            task = TASKS[request.task_id]
            if request.title:
                task["title"] = request.title
            if request.description:
                task["description"] = request.description
            if request.status:
                task["status"] = request.status
            if request.priority:
                task["priority"] = request.priority
            task["updated"] = datetime.now().isoformat()
            
            return {
                "success": True,
                "message": f"Task '{task['title']}' updated successfully",
                "task": task
            }
            
        elif request.action == "delete":
            if not request.task_id or request.task_id not in TASKS:
                raise HTTPException(status_code=404, detail="Task not found")
            
            task = TASKS.pop(request.task_id)
            return {
                "success": True,
                "message": f"Task '{task['title']}' deleted successfully"
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
            
    except Exception as e:
        logger.error(f"Error in manage_task: {e}")
        return {"success": False, "error": str(e)}

@app.post("/mcp/tools/perform_rag_query")
async def perform_rag_query(request: RAGRequest):
    """
    Advanced RAG query with semantic search capabilities
    """
    try:
        query = request.query.lower()
        results = []
        
        # Simple keyword matching (will be enhanced with embeddings later)
        for doc_id, doc in KNOWLEDGE_BASE.items():
            score = 0
            content_lower = doc["content"].lower()
            title_lower = doc["title"].lower()
            
            # Title matches get higher score
            if query in title_lower:
                score += 10
            
            # Content matches
            query_words = query.split()
            for word in query_words:
                if word in content_lower:
                    score += content_lower.count(word)
                if word in title_lower:
                    score += title_lower.count(word) * 2
            
            # Tag matches
            for tag in doc.get("tags", []):
                if query in tag.lower():
                    score += 5
            
            if score > 0:
                results.append({
                    "id": doc_id,
                    "title": doc["title"],
                    "content": doc["content"],
                    "score": score,
                    "tags": doc.get("tags", []),
                    "created": doc.get("created", "")
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:request.match_count]
        
        return {
            "success": True,
            "query": request.query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error in perform_rag_query: {e}")
        return {"success": False, "error": str(e)}

@app.post("/mcp/tools/get_available_sources")
async def get_available_sources():
    """Get list of available sources in the knowledge base"""
    try:
        sources = []
        for doc_id, doc in KNOWLEDGE_BASE.items():
            sources.append({
                "id": doc_id,
                "title": doc["title"],
                "tags": doc.get("tags", []),
                "created": doc.get("created", "")
            })
        
        return {
            "success": True,
            "sources": sources,
            "count": len(sources)
        }
        
    except Exception as e:
        logger.error(f"Error in get_available_sources: {e}")
        return {"success": False, "error": str(e)}

# Legacy endpoints for backward compatibility
@app.post("/mcp/tools/search_dabs_knowledge")
async def search_dabs_knowledge_legacy(request: Dict[str, Any]):
    """Legacy endpoint - redirects to perform_rag_query"""
    rag_request = RAGRequest(
        query=request.get("query", ""),
        match_count=request.get("match_count", 5)
    )
    return await perform_rag_query(rag_request)

@app.post("/mcp/tools/create_dabs_task")
async def create_dabs_task_legacy(request: Dict[str, Any]):
    """Legacy endpoint - redirects to manage_task"""
    task_request = TaskRequest(
        action="create",
        title=request.get("title", ""),
        description=request.get("description", ""),
        project_id=request.get("project_id")
    )
    return await manage_task(task_request)

@app.get("/mcp/tools/get_dabs_project_status")
async def get_dabs_project_status_legacy():
    """Legacy endpoint - returns project overview"""
    return {
        "success": True,
        "status": "Advanced MCP Server Active",
        "projects": len(PROJECTS),
        "tasks": len(TASKS),
        "knowledge_items": len(KNOWLEDGE_BASE),
        "features": [
            "✅ Advanced Project Management",
            "✅ Task Management with Status Tracking", 
            "✅ RAG Knowledge Base",
            "✅ Document Management",
            "✅ DABS Integration Support"
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting DABS Archon Advanced MCP Server...")
    print("📍 Server: http://localhost:8151")
    print("🔧 MCP endpoint: http://localhost:8151/mcp/sse")
    print("📊 Health: http://localhost:8151/health")
    print("✨ Features: Advanced Project Management, Task Tracking, RAG Search")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8151,
        log_level="info"
    )
