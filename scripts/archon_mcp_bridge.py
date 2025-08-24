#!/usr/bin/env python3
"""
Archon MCP Bridge for Cursor Integration

This script acts as a bridge between Cursor's MCP client and Archon's
session-based MCP server, handling the session management automatically.
"""
import json
import sys
import requests
import os
from datetime import datetime

class ArchonMCPBridge:
    def __init__(self):
        self.server_url = os.getenv('ARCHON_SERVER_URL', 'http://localhost:8281')
        self.mcp_url = os.getenv('ARCHON_MCP_URL', 'http://localhost:8151')
        self.project_id = os.getenv('ARCHON_PROJECT_ID', 'd010ff76-0202-48e4-8362-40c45e9de39a')
        self.session_id = None
        
    def initialize_session(self):
        """Initialize MCP session with Archon server"""
        try:
            # Try to initialize a session
            response = requests.post(
                f"{self.mcp_url}/session",
                json={"project_id": self.project_id},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get('session_id')
                return True
        except:
            pass
        
        # If session initialization fails, generate a simple session ID
        self.session_id = f"cursor-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return True
    
    def handle_mcp_request(self, request):
        """Handle MCP JSON-RPC request from Cursor"""
        method = request.get('method', '')
        params = request.get('params', {})
        
        if method == 'tools/list':
            return self.list_tools()
        elif method == 'tools/call':
            return self.call_tool(params)
        elif method == 'resources/list':
            return self.list_resources()
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get('id'),
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
    
    def list_tools(self):
        """Return list of available Archon MCP tools"""
        tools = [
            {
                "name": "archon_get_project",
                "description": "Get current project information and status"
            },
            {
                "name": "archon_list_tasks", 
                "description": "List all tasks in the current project"
            },
            {
                "name": "archon_create_task",
                "description": "Create a new task in the project"
            },
            {
                "name": "archon_update_task",
                "description": "Update an existing task status or description"
            },
            {
                "name": "archon_perform_rag_query",
                "description": "Perform RAG query on project knowledge base"
            },
            {
                "name": "archon_upload_document",
                "description": "Upload a document to the project knowledge base"
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "result": {"tools": tools}
        }
    
    def call_tool(self, params):
        """Execute tool call via Archon API"""
        tool_name = params.get('name', '')
        arguments = params.get('arguments', {})
        
        if tool_name == 'archon_get_project':
            return self.get_project()
        elif tool_name == 'archon_list_tasks':
            return self.list_tasks()
        elif tool_name == 'archon_perform_rag_query':
            return self.perform_rag_query(arguments.get('query', ''))
        elif tool_name == 'archon_upload_document':
            return self.upload_document(arguments)
        else:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}
            }
    
    def get_project(self):
        """Get project information"""
        try:
            response = requests.get(f"{self.server_url}/api/projects/{self.project_id}")
            if response.status_code == 200:
                return {
                    "jsonrpc": "2.0",
                    "result": {"content": [{"type": "text", "text": json.dumps(response.json(), indent=2)}]}
                }
        except Exception as e:
            pass
        
        return {
            "jsonrpc": "2.0",
            "result": {"content": [{"type": "text", "text": "Project information not available"}]}
        }
    
    def list_tasks(self):
        """List project tasks"""
        try:
            response = requests.get(f"{self.server_url}/api/tasks")
            if response.status_code == 200:
                data = response.json()
                tasks = [t for t in data.get('tasks', []) if t.get('project_id') == self.project_id]
                return {
                    "jsonrpc": "2.0",
                    "result": {"content": [{"type": "text", "text": json.dumps(tasks, indent=2)}]}
                }
        except Exception as e:
            pass
        
        return {
            "jsonrpc": "2.0",
            "result": {"content": [{"type": "text", "text": "Tasks not available"}]}
        }
    
    def perform_rag_query(self, query):
        """Perform RAG query on knowledge base"""
        try:
            response = requests.post(
                f"{self.server_url}/api/rag/query",
                json={"query": query, "project_id": self.project_id}
            )
            if response.status_code == 200:
                return {
                    "jsonrpc": "2.0",
                    "result": {"content": [{"type": "text", "text": json.dumps(response.json(), indent=2)}]}
                }
        except Exception as e:
            pass
        
        return {
            "jsonrpc": "2.0",
            "result": {"content": [{"type": "text", "text": f"RAG query failed for: {query}"}]}
        }
    
    def upload_document(self, arguments):
        """Upload document to knowledge base"""
        try:
            file_path = arguments.get('file_path', '')
            if not file_path:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32602, "message": "file_path required"}
                }
            
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'project_id': self.project_id}
                response = requests.post(
                    f"{self.server_url}/api/documents/upload",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                return {
                    "jsonrpc": "2.0",
                    "result": {"content": [{"type": "text", "text": f"Document uploaded: {file_path}"}]}
                }
        except Exception as e:
            pass
        
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": "Document upload failed"}
        }
    
    def list_resources(self):
        """List available resources"""
        return {
            "jsonrpc": "2.0",
            "result": {"resources": []}
        }

def main():
    """Main MCP server loop"""
    bridge = ArchonMCPBridge()
    bridge.initialize_session()
    
    # Handle MCP protocol over stdin/stdout
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = bridge.handle_mcp_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"}
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0", 
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()
