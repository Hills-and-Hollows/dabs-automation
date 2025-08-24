#!/usr/bin/env python3
"""
Test script for DABS Archon Advanced MCP Server
Tests all advanced MCP tools and validates functionality
"""

import json
import requests
import time

BASE_URL = "http://localhost:8151"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health check passed: {data['service']} v{data['version']}")
        print(f"   Features: {', '.join(data['features'])}")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False

def test_rag_query():
    """Test RAG query functionality"""
    print("\n🔍 Testing RAG query...")
    payload = {
        "query": "QuickBooks integration requirements",
        "match_count": 3
    }
    response = requests.post(f"{BASE_URL}/mcp/tools/perform_rag_query", json=payload)
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print(f"✅ RAG query successful: Found {data['count']} results")
            for result in data["results"]:
                print(f"   📄 {result['title']} (score: {result['score']})")
            return True
        else:
            print(f"❌ RAG query failed: {data.get('error', 'Unknown error')}")
            return False
    else:
        print(f"❌ RAG query failed: {response.status_code}")
        return False

def test_project_management():
    """Test project management functionality"""
    print("\n🔍 Testing project management...")
    
    # Create project
    payload = {
        "action": "create",
        "title": "Test DABS Project",
        "description": "Test project for validating advanced MCP functionality",
        "github_repo": "https://github.com/test/dabs-test"
    }
    response = requests.post(f"{BASE_URL}/mcp/tools/manage_project", json=payload)
    if response.status_code != 200:
        print(f"❌ Project creation failed: {response.status_code}")
        return False
    
    data = response.json()
    if not data["success"]:
        print(f"❌ Project creation failed: {data.get('error', 'Unknown error')}")
        return False
    
    project_id = data["project_id"]
    print(f"✅ Project created: {data['project']['title']} (ID: {project_id[:8]}...)")
    
    # List projects
    payload = {"action": "list"}
    response = requests.post(f"{BASE_URL}/mcp/tools/manage_project", json=payload)
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print(f"✅ Project list retrieved: {data['count']} projects found")
        else:
            print(f"❌ Project list failed: {data.get('error', 'Unknown error')}")
            return False
    else:
        print(f"❌ Project list failed: {response.status_code}")
        return False
    
    return project_id

def test_task_management(project_id):
    """Test task management functionality"""
    print("\n🔍 Testing task management...")
    
    # Create task
    payload = {
        "action": "create",
        "project_id": project_id,
        "title": "Test Task Implementation",
        "description": "Implement test functionality for MCP validation",
        "status": "todo",
        "priority": 1
    }
    response = requests.post(f"{BASE_URL}/mcp/tools/manage_task", json=payload)
    if response.status_code != 200:
        print(f"❌ Task creation failed: {response.status_code}")
        return False
    
    data = response.json()
    if not data["success"]:
        print(f"❌ Task creation failed: {data.get('error', 'Unknown error')}")
        return False
    
    task_id = data["task_id"]
    print(f"✅ Task created: {data['task']['title']} (ID: {task_id[:8]}...)")
    
    # Update task status
    payload = {
        "action": "update",
        "task_id": task_id,
        "status": "in_progress"
    }
    response = requests.post(f"{BASE_URL}/mcp/tools/manage_task", json=payload)
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print(f"✅ Task updated: Status changed to {data['task']['status']}")
        else:
            print(f"❌ Task update failed: {data.get('error', 'Unknown error')}")
            return False
    else:
        print(f"❌ Task update failed: {response.status_code}")
        return False
    
    # List tasks
    payload = {"action": "list", "project_id": project_id}
    response = requests.post(f"{BASE_URL}/mcp/tools/manage_task", json=payload)
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print(f"✅ Task list retrieved: {data['count']} tasks found for project")
        else:
            print(f"❌ Task list failed: {data.get('error', 'Unknown error')}")
            return False
    else:
        print(f"❌ Task list failed: {response.status_code}")
        return False
    
    return True

def test_knowledge_sources():
    """Test knowledge source listing"""
    print("\n🔍 Testing knowledge sources...")
    response = requests.post(f"{BASE_URL}/mcp/tools/get_available_sources")
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print(f"✅ Knowledge sources retrieved: {data['count']} sources available")
            for source in data["sources"]:
                print(f"   📚 {source['title']} (tags: {', '.join(source['tags'])})")
            return True
        else:
            print(f"❌ Knowledge sources failed: {data.get('error', 'Unknown error')}")
            return False
    else:
        print(f"❌ Knowledge sources failed: {response.status_code}")
        return False

def test_legacy_compatibility():
    """Test legacy endpoint compatibility"""
    print("\n🔍 Testing legacy compatibility...")
    
    # Test legacy search
    payload = {"query": "DABS Phase 2", "match_count": 2}
    response = requests.post(f"{BASE_URL}/mcp/tools/search_dabs_knowledge", json=payload)
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print(f"✅ Legacy search working: {data['count']} results")
        else:
            print(f"❌ Legacy search failed: {data.get('error', 'Unknown error')}")
            return False
    else:
        print(f"❌ Legacy search failed: {response.status_code}")
        return False
    
    # Test legacy status
    response = requests.get(f"{BASE_URL}/mcp/tools/get_dabs_project_status")
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print(f"✅ Legacy status working: {data['projects']} projects, {data['tasks']} tasks")
        else:
            print(f"❌ Legacy status failed: {data.get('error', 'Unknown error')}")
            return False
    else:
        print(f"❌ Legacy status failed: {response.status_code}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 DABS Archon Advanced MCP Server Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 6
    
    # Test 1: Health check
    if test_health():
        tests_passed += 1
    
    # Test 2: RAG query
    if test_rag_query():
        tests_passed += 1
    
    # Test 3: Project management
    project_id = test_project_management()
    if project_id:
        tests_passed += 1
    
    # Test 4: Task management
    if project_id and test_task_management(project_id):
        tests_passed += 1
    
    # Test 5: Knowledge sources
    if test_knowledge_sources():
        tests_passed += 1
    
    # Test 6: Legacy compatibility
    if test_legacy_compatibility():
        tests_passed += 1
    
    # Results
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Advanced MCP server is fully functional.")
        print("\n✨ Ready for Cursor integration:")
        print("   Command: curl -N -H \"Accept: text/event-stream\" http://localhost:8151/mcp/sse")
        return True
    else:
        print(f"⚠️  {total_tests - tests_passed} tests failed. Please check the server configuration.")
        return False

if __name__ == "__main__":
    main()
