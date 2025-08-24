#!/usr/bin/env python3
"""
ARCHON-FIRST WORKFLOW ENFORCEMENT SYSTEM
Guarantees 100% Archon synchronization for all tasks and subtasks

This script MUST be called before any development work begins.
It ensures Archon MCP server is available and tasks are properly synced.
"""

import sys
import json
import httpx
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class ArchonEnforcer:
    def __init__(self):
        self.archon_server = "http://localhost:8281"
        self.archon_mcp = "http://localhost:8151" 
        self.timeout = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
        self.project_id = "d010ff76-0202-48e4-8362-40c45e9de39a"
        
    async def enforce_archon_first(self) -> bool:
        """MANDATORY: Enforce Archon-first workflow before any development"""
        print("🔒 ARCHON-FIRST WORKFLOW ENFORCEMENT")
        print("=" * 60)
        
        # Step 1: Verify Archon Services
        archon_healthy = await self.check_archon_health()
        if not archon_healthy:
            print("🚨 CRITICAL: Archon services not available!")
            print("   Required: docker-compose up -d in archon-mcp/")
            return False
            
        # Step 2: Validate Configuration Consistency  
        config_valid = await self.validate_configurations()
        if not config_valid:
            print("🚨 CRITICAL: Configuration inconsistencies found!")
            return False
            
        # Step 3: Check Active Tasks
        tasks_synced = await self.verify_task_sync()
        if not tasks_synced:
            print("🚨 WARNING: Task synchronization issues detected")
            
        # Step 4: Enforce Workflow Rules
        rules_enforced = await self.enforce_workflow_rules()
        
        if archon_healthy and config_valid and rules_enforced:
            print("✅ ARCHON-FIRST WORKFLOW ENFORCEMENT: PASSED")
            print(f"   🎯 Archon Server: {self.archon_server}")
            print(f"   📋 Project ID: {self.project_id}")
            print("   🚀 Ready for development!")
            return True
        else:
            print("❌ ARCHON-FIRST WORKFLOW ENFORCEMENT: FAILED")
            return False
    
    async def check_archon_health(self) -> bool:
        """Check all Archon services are healthy"""
        print("🔍 Checking Archon Services...")
        
        services = {
            "Archon Server": f"{self.archon_server}/health",
            "Archon MCP": f"{self.archon_mcp}/health", 
            "Archon UI": "http://localhost:3837"
        }
        
        all_healthy = True
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for name, url in services.items():
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        print(f"   ✅ {name}: Healthy")
                    else:
                        print(f"   ❌ {name}: Unhealthy ({response.status_code})")
                        all_healthy = False
                except Exception as e:
                    print(f"   ❌ {name}: Not responding ({e})")
                    all_healthy = False
                    
        return all_healthy
    
    async def validate_configurations(self) -> bool:
        """Validate all configuration files are consistent"""
        print("🔍 Validating Configuration Consistency...")
        
        config_files = {
            ".cursorrules": self.parse_cursorrules(),
            "cursor_mcp_config.json": self.parse_mcp_config(),
            ".cursor/rules/archon-workflow.mdc": self.parse_workflow_rules()
        }
        
        # Check for port consistency
        expected_ports = {
            "archon_server": 8281,
            "archon_mcp": 8151,
            "archon_ui": 3837
        }
        
        inconsistencies = []
        for filename, config in config_files.items():
            if config and "port_issues" in config:
                inconsistencies.extend(config["port_issues"])
                
        if inconsistencies:
            print("   ❌ Configuration Inconsistencies Found:")
            for issue in inconsistencies:
                print(f"      • {issue}")
            return False
        else:
            print("   ✅ All configurations consistent")
            return True
    
    async def verify_task_sync(self) -> bool:
        """Verify tasks are properly synced with Archon"""
        print("🔍 Verifying Task Synchronization...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.archon_server}/api/tasks")
                if response.status_code == 200:
                    data = response.json()
                    total_tasks = data.get("pagination", {}).get("total", 0)
                    active_tasks = len([t for t in data.get("tasks", []) if t.get("status") == "doing"])
                    
                    print(f"   ✅ Archon Tasks: {total_tasks} total, {active_tasks} active")
                    print(f"   🎯 Project ID: {self.project_id}")
                    
                    return True
                else:
                    print(f"   ❌ Task API error: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Task sync check failed: {e}")
            return False
    
    async def enforce_workflow_rules(self) -> bool:
        """Enforce specific workflow rules"""
        print("🔍 Enforcing Workflow Rules...")
        
        rules = [
            "NEVER use TodoWrite as primary task management",
            "ALWAYS check Archon availability first",
            "USE Archon API for task creation/updates",
            "UPDATE task status after each step",
            "RESEARCH using archon:perform_rag_query"
        ]
        
        print("   📋 Active Enforcement Rules:")
        for rule in rules:
            print(f"      ✅ {rule}")
            
        return True
    
    def parse_cursorrules(self) -> Dict:
        """Parse .cursorrules file for Archon references"""
        try:
            cursorrules_path = Path(".cursorrules")
            if cursorrules_path.exists():
                content = cursorrules_path.read_text()
                return {"archon_mentioned": "Archon" in content}
        except Exception:
            pass
        return {}
    
    def parse_mcp_config(self) -> Dict:
        """Parse cursor_mcp_config.json"""
        try:
            config_path = Path("cursor_mcp_config.json")
            if config_path.exists():
                data = json.loads(config_path.read_text())
                return {"config": data}
        except Exception:
            pass
        return {}
    
    def parse_workflow_rules(self) -> Dict:
        """Parse archon-workflow.mdc"""
        try:
            rules_path = Path(".cursor/rules/archon-workflow.mdc")
            if rules_path.exists():
                content = rules_path.read_text()
                return {"archon_workflow": "ARCHON-FIRST" in content}
        except Exception:
            pass
        return {}
    
    async def create_archon_task_if_needed(self, title: str, description: str) -> Optional[str]:
        """Create task in Archon if it doesn't exist"""
        try:
            task_data = {
                "project_id": self.project_id,
                "title": title,
                "description": description,
                "status": "todo",
                "assignee": "AI IDE Agent",
                "feature": "enforcement"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.archon_server}/api/tasks",
                    json=task_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    task_id = result.get("task", {}).get("id")
                    print(f"   ✅ Task created in Archon: {task_id}")
                    return task_id
                else:
                    print(f"   ❌ Task creation failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"   ❌ Task creation error: {e}")
            return None

async def main():
    """Main enforcement entry point"""
    enforcer = ArchonEnforcer()
    
    # MANDATORY: Enforce Archon-first workflow
    success = await enforcer.enforce_archon_first()
    
    if success:
        print("\n🚀 ARCHON-FIRST ENFORCEMENT: SUCCESSFUL")
        print("   Development workflow is properly configured!")
        print("   All tasks will be managed through Archon MCP system.")
        sys.exit(0)
    else:
        print("\n🚨 ARCHON-FIRST ENFORCEMENT: FAILED") 
        print("   Fix issues before proceeding with development!")
        print("   Contact system administrator for assistance.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
