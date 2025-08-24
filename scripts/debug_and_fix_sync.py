#!/usr/bin/env python3
"""
Debug and Fix DABS Task Synchronization Issues
Comprehensive debugging and resolution script for task sync problems
"""

import requests
import json
import subprocess
import time
import os
import signal
from pathlib import Path

def kill_existing_servers():
    """Kill any existing DABS task server processes"""
    try:
        result = subprocess.run(['pkill', '-f', 'dabs_task_server.py'], 
                              capture_output=True, text=True)
        print(f"🔧 Killed existing server processes (exit code: {result.returncode})")
        time.sleep(2)
    except Exception as e:
        print(f"⚠️  Error killing processes: {e}")

def check_port_usage():
    """Check what's using port 8151"""
    try:
        result = subprocess.run(['lsof', '-i', ':8151'], 
                              capture_output=True, text=True)
        print(f"📍 Port 8151 usage:")
        print(result.stdout if result.stdout else "No processes found")
        return result.stdout
    except Exception as e:
        print(f"❌ Error checking port: {e}")
        return ""

def test_server_startup():
    """Test server startup with full output"""
    print("🚀 Testing DABS Task Server Startup...")
    
    archon_dir = Path("../archon-mcp").resolve()
    server_file = archon_dir / "dabs_task_server.py"
    
    if not server_file.exists():
        print(f"❌ Server file not found: {server_file}")
        return False
    
    try:
        # Change to archon-mcp directory and start server
        print(f"📂 Starting server from: {archon_dir}")
        proc = subprocess.Popen(
            ['python3', 'dabs_task_server.py'],
            cwd=str(archon_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for startup
        print("⏳ Waiting for server startup (10 seconds)...")
        time.sleep(10)
        
        # Test endpoints
        print("🧪 Testing endpoints...")
        
        endpoints = [
            ("Health", "http://localhost:8151/health"),
            ("Root", "http://localhost:8151/"),
            ("Tasks", "http://localhost:8151/tasks"),
            ("Project Status", "http://localhost:8151/mcp/tools/get_dabs_project_status")
        ]
        
        working_endpoints = []
        
        for name, url in endpoints:
            try:
                response = requests.get(url, timeout=5)
                status = f"{response.status_code}"
                if response.status_code == 200:
                    try:
                        data = response.json()
                        status += f" ✅ (JSON: {type(data).__name__})"
                        working_endpoints.append((name, url, data))
                    except:
                        status += f" ✅ (Text: {len(response.text)} chars)"
                        working_endpoints.append((name, url, response.text))
                else:
                    status += f" ❌ ({response.text[:50]})"
                
                print(f"  {name}: {status}")
            except Exception as e:
                print(f"  {name}: ❌ Connection failed - {e}")
        
        # Show server output
        try:
            stdout, stderr = proc.communicate(timeout=2)
            if stdout:
                print(f"\n📄 Server Output:")
                print(stdout)
            if stderr:
                print(f"\n⚠️  Server Errors:")
                print(stderr)
        except subprocess.TimeoutExpired:
            print("\n🔄 Server still running...")
            proc.kill()
            stdout, stderr = proc.communicate()
            if stdout:
                print(f"📄 Server Output (after kill):")
                print(stdout)
            if stderr:
                print(f"⚠️  Server Errors (after kill):")
                print(stderr)
        
        return len(working_endpoints) > 0
        
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False

def verify_task_data():
    """Verify task data exists in JSON file"""
    try:
        task_file = Path("../archon-mcp/dabs_tasks.json").resolve()
        if task_file.exists():
            with open(task_file, 'r') as f:
                tasks = json.load(f)
            print(f"📋 Task file found: {len(tasks)} tasks in {task_file}")
            
            # Show sample tasks
            for i, (task_id, task) in enumerate(list(tasks.items())[:3]):
                print(f"  {i+1}. {task.get('title', 'No title')} (Priority: {task.get('priority', 'unknown')})")
            
            return len(tasks)
        else:
            print(f"❌ Task file not found: {task_file}")
            return 0
    except Exception as e:
        print(f"❌ Error reading task file: {e}")
        return 0

def check_frontend_api():
    """Check frontend API endpoints"""
    print("\n🌐 Frontend API Check:")
    
    try:
        # Get projects
        response = requests.get("http://localhost:3837/api/projects", timeout=5)
        if response.status_code == 200:
            projects = response.json()
            print(f"  ✅ Projects API: {len(projects)} projects")
            
            if projects:
                project = projects[0]
                project_id = project["id"]
                print(f"  📋 Project: {project['title']} ({project_id})")
                
                # Get tasks for project
                task_response = requests.get(f"http://localhost:3837/api/projects/{project_id}/tasks", timeout=5)
                if task_response.status_code == 200:
                    tasks = task_response.json()
                    print(f"  📝 Project tasks: {len(tasks)} tasks")
                    return project_id, len(tasks)
                else:
                    print(f"  ❌ Tasks API error: {task_response.status_code}")
            
            return None, 0
        else:
            print(f"  ❌ Projects API error: {response.status_code}")
            return None, 0
            
    except Exception as e:
        print(f"  ❌ Frontend API error: {e}")
        return None, 0

def main():
    """Main debugging function"""
    print("🔍 DABS Task Synchronization Debug & Fix")
    print("=" * 60)
    
    # Step 1: Check current port usage
    print("\n📍 Step 1: Port Analysis")
    check_port_usage()
    
    # Step 2: Verify task data exists
    print("\n📋 Step 2: Task Data Verification")
    task_count = verify_task_data()
    
    # Step 3: Check frontend
    print("\n🌐 Step 3: Frontend API Verification")
    project_id, frontend_task_count = check_frontend_api()
    
    # Step 4: Kill existing servers and test fresh startup
    print("\n🔧 Step 4: Fresh Server Startup")
    kill_existing_servers()
    server_working = test_server_startup()
    
    # Summary
    print("\n📊 SYNCHRONIZATION SUMMARY")
    print("=" * 40)
    print(f"Task data file: {task_count} tasks")
    print(f"Frontend tasks: {frontend_task_count} tasks")
    print(f"DABS server: {'✅ Working' if server_working else '❌ Not working'}")
    print(f"Sync status: {'✅ In sync' if task_count == frontend_task_count else '❌ Out of sync'}")
    
    if task_count > 0 and frontend_task_count == 0:
        print(f"\n🚨 CRITICAL: {task_count} tasks exist but not visible in frontend!")
        print("🔧 Recommended action: Implement task import from DABS to frontend")
    
    return {
        "task_file_count": task_count,
        "frontend_count": frontend_task_count,
        "server_working": server_working,
        "project_id": project_id
    }

if __name__ == "__main__":
    results = main()