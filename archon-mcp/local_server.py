#!/usr/bin/env python3
"""
Minimal Archon MCP Server for Local Development
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from pathlib import Path
import json
from typing import Dict, List, Any

app = FastAPI(
    title="DABS Archon MCP Server (Local Dev)",
    description="Minimal MCP server for DABS project development",
    version="1.0.0-dev"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for development
projects = {}
tasks = {}
knowledge_base = []

@app.get("/")
async def root():
    return {"message": "DABS Archon MCP Server (Local Dev)", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "mode": "local_development"}

@app.post("/mcp/tools/search_dabs_knowledge")
async def search_dabs_knowledge(query: Dict[str, Any]):
    """Search DABS knowledge base"""
    search_term = query.get("query", "")
    source_filter = query.get("source_filter", "all")
    
    # Simple search simulation
    results = [
        {
            "title": "DABS Integration Requirements",
            "content": f"Found information about: {search_term}",
            "source": "docs/FUNCTIONAL_REQUIREMENTS.md",
            "relevance": 0.95
        },
        {
            "title": "QuickBooks API Integration",
            "content": "OAuth 2.0 authentication required for QuickBooks Online API",
            "source": "research-paper-qbo-mcp.md", 
            "relevance": 0.87
        }
    ]
    
    return {"results": results, "query": search_term}

@app.post("/mcp/tools/create_dabs_task")
async def create_dabs_task(task_data: Dict[str, Any]):
    """Create a new DABS task"""
    task_id = f"task_{len(tasks) + 1}"
    
    task = {
        "id": task_id,
        "title": task_data.get("title", "New Task"),
        "description": task_data.get("description", ""),
        "phase": task_data.get("phase", "foundation"),
        "priority": task_data.get("priority", "medium"),
        "status": "not_started",
        "created_at": "2025-01-21T10:00:00Z"
    }
    
    tasks[task_id] = task
    return {"task": task, "message": "Task created successfully"}

@app.get("/mcp/tools/get_dabs_project_status")
async def get_dabs_project_status(phase: str = "all"):
    """Get DABS project status"""
    status = {
        "project": "DABS Integration System",
        "overall_progress": 25,
        "phases": {
            "foundation": {"status": "completed", "progress": 100},
            "sscs_integration": {"status": "in_progress", "progress": 25},
            "quickbooks": {"status": "planned", "progress": 0},
            "verifone": {"status": "planned", "progress": 0}
        },
        "active_tasks": len([t for t in tasks.values() if t["status"] == "in_progress"]),
        "total_tasks": len(tasks)
    }
    
    if phase != "all" and phase in status["phases"]:
        return {"phase": phase, "details": status["phases"][phase]}
    
    return status

@app.get("/mcp/sse")
async def mcp_sse():
    """MCP Server-Sent Events endpoint"""
    return {"message": "MCP SSE endpoint ready", "transport": "sse"}

@app.get("/projects")
async def list_projects():
    """List all projects"""
    return {"projects": list(projects.values())}

@app.get("/tasks")
async def list_tasks():
    """List all tasks"""
    return {"tasks": list(tasks.values())}

if __name__ == "__main__":
    print("🚀 Starting DABS Archon MCP Server (Local Dev)")
    print("📍 Server will be available at: http://localhost:8151")
    print("🔧 MCP endpoint: http://localhost:8151/mcp/sse")
    print("📊 Health check: http://localhost:8151/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8151,
        log_level="info"
    )
