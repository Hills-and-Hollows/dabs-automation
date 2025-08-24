#!/usr/bin/env python3
"""
DABS Archon Local Development Setup
Quick setup without Docker for immediate testing
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class LocalArchonSetup:
    def __init__(self):
        self.archon_dir = Path(__file__).parent
        self.venv_dir = self.archon_dir / "venv"
        self.src_dir = self.archon_dir / "python" / "src"
        
    def check_python(self):
        """Check Python version"""
        print("🐍 Checking Python version...")
        if sys.version_info < (3, 9):
            print("❌ Python 3.9+ required")
            return False
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
        return True
    
    def create_virtual_environment(self):
        """Create Python virtual environment"""
        print("📦 Creating virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_dir)], check=True)
            print("✅ Virtual environment created")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
    
    def install_dependencies(self):
        """Install required Python packages"""
        print("📚 Installing dependencies...")
        
        # Determine pip path based on OS
        if os.name == 'nt':  # Windows
            pip_path = self.venv_dir / "Scripts" / "pip"
        else:  # macOS/Linux
            pip_path = self.venv_dir / "bin" / "pip"
        
        try:
            # Install basic requirements
            requirements = [
                "fastapi==0.104.1",
                "uvicorn==0.24.0",
                "python-socketio==5.10.0",
                "supabase==2.0.2",
                "openai==1.3.5",
                "python-dotenv==1.0.0",
                "pydantic==2.5.0",
                "httpx==0.25.2",
                "aiofiles==23.2.1"
            ]
            
            for req in requirements:
                subprocess.run([str(pip_path), "install", req], check=True, capture_output=True)
                print(f"✅ Installed {req.split('==')[0]}")
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def create_minimal_server(self):
        """Create minimal Archon server for local development"""
        print("🔧 Creating minimal Archon server...")
        
        server_code = '''#!/usr/bin/env python3
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
'''
        
        server_file = self.archon_dir / "local_server.py"
        server_file.write_text(server_code)
        server_file.chmod(0o755)
        print("✅ Minimal server created")
        return True
    
    def create_startup_script(self):
        """Create startup script for local development"""
        print("📝 Creating startup script...")
        
        if os.name == 'nt':  # Windows
            python_path = self.venv_dir / "Scripts" / "python"
            script_ext = ".bat"
            script_content = f'''@echo off
echo Starting DABS Archon Local Development Server...
"{python_path}" local_server.py
'''
        else:  # macOS/Linux
            python_path = self.venv_dir / "bin" / "python"
            script_ext = ".sh"
            script_content = f'''#!/bin/bash
echo "🚀 Starting DABS Archon Local Development Server..."
echo "📍 Server: http://localhost:8151"
echo "🔧 MCP endpoint: http://localhost:8151/mcp/sse"
echo "📊 Health: http://localhost:8151/health"
echo ""
"{python_path}" local_server.py
'''
        
        script_file = self.archon_dir / f"start_local{script_ext}"
        script_file.write_text(script_content)
        script_file.chmod(0o755)
        print(f"✅ Startup script created: {script_file.name}")
        return True
    
    def run_setup(self):
        """Run the complete local setup"""
        print("🏗️  DABS Archon Local Development Setup")
        print("=" * 50)
        
        if not self.check_python():
            sys.exit(1)
        
        if not self.create_virtual_environment():
            sys.exit(1)
        
        if not self.install_dependencies():
            sys.exit(1)
        
        if not self.create_minimal_server():
            sys.exit(1)
        
        if not self.create_startup_script():
            sys.exit(1)
        
        print("\n🎉 Local development setup complete!")
        print("\n📋 Next Steps:")
        print("1. 🚀 Start the server:")
        if os.name == 'nt':
            print("   start_local.bat")
        else:
            print("   ./start_local.sh")
        print("2. 🌐 Test the server: http://localhost:8151/health")
        print("3. 🤖 Configure Cursor MCP: http://localhost:8151/mcp/sse")
        print("\n💡 This is a minimal setup for immediate testing.")
        print("   For full features, install Docker and run the complete setup.")

if __name__ == "__main__":
    setup = LocalArchonSetup()
    setup.run_setup()
