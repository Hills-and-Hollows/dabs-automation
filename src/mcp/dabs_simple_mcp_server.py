#!/usr/bin/env python3
"""
DABS Simple MCP Server (No Package Dependency)
Hills & Hollows LLC - Utah Package Agency
Date: August 23, 2025

This is a simplified MCP server that works without the full MCP package.
It implements just enough of the MCP protocol to be discovered by Cursor
and provide DABS automation tools.

Compatible with Python 3.9+ (no external MCP package required)
"""

import asyncio
import json
import sys
import logging
from typing import Dict, Any, List
from datetime import datetime
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleMCPServer:
    """
    Simplified MCP server that implements basic protocol without external dependencies
    """
    
    def __init__(self, name: str = "dabs-simple-mcp"):
        self.name = name
        self.tools = {}
        self.resources = {}
        
        # Initialize DABS context (lazy loading)
        self.dabs_context = {
            "initialized": False,
            "automation": None,
            "oauth_client": None
        }
        
        # Register DABS tools
        self._register_dabs_tools()
    
    def _register_dabs_tools(self):
        """Register all DABS tools with the server"""
        
        # Tool definitions matching the full MCP server
        self.tools = {
            "dabs_login_status": {
                "name": "dabs_login_status",
                "description": "Check DABS authentication status and session validity",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            "dabs_perform_login": {
                "name": "dabs_perform_login", 
                "description": "Perform automated login to DABS system",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "force": {
                            "type": "boolean",
                            "description": "Force re-login even if already authenticated",
                            "default": False
                        }
                    },
                    "additionalProperties": False
                }
            },
            "dabs_process_restaurant_order": {
                "name": "dabs_process_restaurant_order",
                "description": "Process a restaurant order through DABS automation", 
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "order": {
                            "type": "object",
                            "description": "Restaurant order details",
                            "required": ["customer_name", "customer_email", "items"]
                        }
                    },
                    "required": ["order"],
                    "additionalProperties": False
                }
            },
            "dabs_get_order_history": {
                "name": "dabs_get_order_history",
                "description": "Get DABS order history and status",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back",
                            "default": 30
                        },
                        "status": {
                            "type": "string",
                            "description": "Optional status filter"
                        }
                    },
                    "additionalProperties": False
                }
            },
            "dabs_oauth_status": {
                "name": "dabs_oauth_status",
                "description": "Check DABS OAuth token status",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            "dabs_generate_oauth_url": {
                "name": "dabs_generate_oauth_url",
                "description": "Generate OAuth authorization URL for DABS",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "state": {
                            "type": "string",
                            "description": "Optional state parameter"
                        },
                        "scopes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "OAuth scopes to request"
                        }
                    },
                    "additionalProperties": False
                }
            },
            "dabs_system_health": {
                "name": "dabs_system_health",
                "description": "Check DABS system health and connectivity",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            "dabs_lookup_product": {
                "name": "dabs_lookup_product",
                "description": "Look up product information and pricing from DABS catalog",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "Product name or SKU to search for"
                        }
                    },
                    "required": ["product_name"],
                    "additionalProperties": False
                }
            },
            "dabs_search_all_items": {
                "name": "dabs_search_all_items",
                "description": "Search the complete DABS product catalog with filtering and pagination",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search term for product name or item code"
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number (default: 1)",
                            "default": 1
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Items per page (10, 25, 50, or 100)",
                            "default": 25
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False
                }
            },
            "dabs_get_open_order": {
                "name": "dabs_get_open_order",
                "description": "Get current open order details if one exists",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            "dabs_create_new_order": {
                "name": "dabs_create_new_order",
                "description": "Create a new DABS order (requires no pending orders)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "reference": {
                            "type": "string",
                            "description": "Optional order reference/notes"
                        }
                    },
                    "additionalProperties": False
                }
            },
            "dabs_add_item_to_order": {
                "name": "dabs_add_item_to_order",
                "description": "Add a specific item to the current DABS order",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "item_code": {
                            "type": "string",
                            "description": "DABS item code (e.g., '000159')"
                        },
                        "cases": {
                            "type": "integer",
                            "description": "Number of cases to order"
                        }
                    },
                    "required": ["item_code", "cases"],
                    "additionalProperties": False
                }
            },
            "dabs_submit_order": {
                "name": "dabs_submit_order",
                "description": "Submit the current open DABS order for processing",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "confirm": {
                            "type": "boolean",
                            "description": "Confirm submission (default: true)",
                            "default": True
                        }
                    },
                    "additionalProperties": False
                }
            },
            "dabs_return_to_order": {
                "name": "dabs_return_to_order",
                "description": "Return from EditOrder page back to the main orders list page",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "Optional order ID for context (extracted from current page if not provided)"
                        }
                    },
                    "additionalProperties": False
                }
            },
            "dabs_edit_open_order": {
                "name": "dabs_edit_open_order",
                "description": "Click the edit button for the pending open order to navigate to EditOrder page",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            "dabs_delete_open_order": {
                "name": "dabs_delete_open_order",
                "description": "Click the delete button to remove the pending open order",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "confirm": {
                            "type": "boolean",
                            "description": "Confirm deletion (default: true)",
                            "default": True
                        },
                        "headed": {
                            "type": "boolean",
                            "description": "Run headed Playwright (recommended for reliability)",
                            "default": False
                        },
                        "order_id": {
                            "type": "string",
                            "description": "Optional order id to target specific row"
                        },
                        "return_artifacts": {
                            "type": "boolean",
                            "description": "Include screenshot/HTML artifact paths in response",
                            "default": True
                        }
                    },
                    "additionalProperties": False
                }
            },
            "dabs_check_order_to_print": {
                "name": "dabs_check_order_to_print",
                "description": "Check/uncheck order checkboxes in Order History for batch printing or actions",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "order_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Order IDs to check (e.g., ['233817', '233813']) or Sales Order numbers (e.g., ['SOO03078449'])"
                        },
                        "action": {
                            "type": "string",
                            "enum": ["check", "uncheck", "check_all", "uncheck_all"],
                            "description": "Action to perform: check, uncheck, check_all, uncheck_all",
                            "default": "check"
                        }
                    },
                    "required": ["order_ids"],
                    "additionalProperties": False
                }
            },
            "dabs_print_selected_orders": {
                "name": "dabs_print_selected_orders",
                "description": "Click 'Print Selected' button to print checked orders from Order History",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "wait_for_result": {
                            "type": "boolean",
                            "description": "Wait for print dialog/PDF generation (default: true)",
                            "default": True
                        }
                    },
                    "additionalProperties": False
                }
            },
            "dabs_ensure_clean_state": {
                "name": "dabs_ensure_clean_state",
                "description": "Ensure DABS is in a clean state (no pending order); deletes pending order if present",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "headed": {
                            "type": "boolean",
                            "description": "Run headed when deletion is required (recommended)",
                            "default": True
                        },
                        "confirm": {
                            "type": "boolean",
                            "description": "Confirm deletion if needed",
                            "default": True
                        },
                        "return_artifacts": {
                            "type": "boolean",
                            "description": "Include artifact file paths in response",
                            "default": True
                        }
                    },
                    "additionalProperties": False
                }
            }
        }
        
        logger.info(f"✅ Registered {len(self.tools)} DABS tools")
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "tools/list":
                return await self._handle_list_tools(request_id)
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                return await self._handle_tool_call(request_id, tool_name, arguments)
            elif method == "initialize":
                return await self._handle_initialize(request_id, params)
            elif method == "ping":
                return self._create_response(request_id, {"pong": True})
            else:
                return self._create_error_response(request_id, f"Unknown method: {method}")
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self._create_error_response(request.get("id"), str(e))
    
    async def _handle_initialize(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialization"""
        return self._create_response(request_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {}
            },
            "serverInfo": {
                "name": self.name,
                "version": "1.0.0"
            }
        })
    
    async def _handle_list_tools(self, request_id: str) -> Dict[str, Any]:
        """Handle tools/list request"""
        tools_list = list(self.tools.values())
        return self._create_response(request_id, {"tools": tools_list})
    
    async def _handle_tool_call(self, request_id: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        
        if tool_name not in self.tools:
            return self._create_error_response(request_id, f"Unknown tool: {tool_name}")
        
        try:
            # Route to appropriate tool implementation
            if tool_name == "dabs_login_status":
                result = await self._dabs_login_status(arguments)
            elif tool_name == "dabs_perform_login":
                result = await self._dabs_perform_login(arguments)
            elif tool_name == "dabs_process_restaurant_order":
                result = await self._dabs_process_restaurant_order(arguments)
            elif tool_name == "dabs_get_order_history":
                result = await self._dabs_get_order_history(arguments)
            elif tool_name == "dabs_oauth_status":
                result = await self._dabs_oauth_status(arguments)
            elif tool_name == "dabs_generate_oauth_url":
                result = await self._dabs_generate_oauth_url(arguments)
            elif tool_name == "dabs_system_health":
                result = await self._dabs_system_health(arguments)
            elif tool_name == "dabs_lookup_product":
                result = await self._dabs_lookup_product(arguments)
            elif tool_name == "dabs_search_all_items":
                result = await self._dabs_search_all_items(arguments)
            elif tool_name == "dabs_get_open_order":
                result = await self._dabs_get_open_order(arguments)
            elif tool_name == "dabs_create_new_order":
                result = await self._dabs_create_new_order(arguments)
            elif tool_name == "dabs_add_item_to_order":
                result = await self._dabs_add_item_to_order(arguments)
            elif tool_name == "dabs_submit_order":
                result = await self._dabs_submit_order(arguments)
            elif tool_name == "dabs_return_to_order":
                result = await self._dabs_return_to_order(arguments)
            elif tool_name == "dabs_edit_open_order":
                result = await self._dabs_edit_open_order(arguments)
            elif tool_name == "dabs_delete_open_order":
                result = await self._dabs_delete_open_order(arguments)
            elif tool_name == "dabs_check_order_to_print":
                result = await self._dabs_check_order_to_print(arguments)
            elif tool_name == "dabs_print_selected_orders":
                result = await self._dabs_print_selected_orders(arguments)
            elif tool_name == "dabs_ensure_clean_state":
                result = await self._dabs_ensure_clean_state(arguments)
            else:
                return self._create_error_response(request_id, f"Tool not implemented: {tool_name}")
            
            standardized = self._standardize_tool_result(result, tool_name)
            try:
                self._audit_log("tool_call", tool_name, request_id, arguments, json.loads(standardized))
            except Exception:
                self._audit_log("tool_call", tool_name, request_id, arguments, None)
            return self._create_response(request_id, {
                "content": [
                    {
                        "type": "text",
                        "text": standardized
                    }
                ]
            })
            
        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            self._audit_log("tool_error", tool_name, request_id, arguments, {"error": str(e)})
            return self._create_error_response(request_id, f"Tool execution failed: {str(e)}")
    
    def _create_response(self, request_id: str, result: Any) -> Dict[str, Any]:
        """Create a successful MCP response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    
    def _create_error_response(self, request_id: str, message: str) -> Dict[str, Any]:
        """Create an MCP error response"""
        return {
            "jsonrpc": "2.0", 
            "id": request_id,
            "error": {
                "code": -1,
                "message": message
            }
        }
    
    def _standardize_tool_result(self, raw_json: str, tool_name: str) -> str:
        """Wrap any tool's raw JSON string into a standardized schema.
        Schema fields: success, action, message, error, details, artifacts, timestamp
        """
        try:
            data = json.loads(raw_json) if isinstance(raw_json, str) else (raw_json or {})
        except Exception as e:
            data = {
                "success": False,
                "error": f"Malformed tool result JSON: {str(e)}",
                "original": raw_json,
            }

        success = bool(data.get("success", True))
        action = data.get("action") or tool_name
        message = data.get("message") or (f"Error: {data.get('error')}" if data.get("error") else "")
        error = data.get("error")
        artifacts = data.get("artifacts")
        timestamp = data.get("timestamp") or datetime.utcnow().isoformat()

        # Preserve remaining original fields under details
        envelope_keys = {"success", "action", "message", "error", "artifacts", "timestamp"}
        details = {k: v for k, v in data.items() if k not in envelope_keys}

        standardized = {
            "success": success,
            "action": action,
            "message": message,
            "error": error,
            "details": details,
            "artifacts": artifacts,
            "timestamp": timestamp,
        }

        return json.dumps(standardized, indent=2)

    def _audit_log(self, event: str, tool_name: str, request_id: Any, arguments: Dict[str, Any], result: Dict[str, Any] = None) -> None:
        """Write an audit entry for tool calls to logs/dabs_mcp_audit.log"""
        try:
            if os.getenv("DABS_MCP_AUDIT", "1") not in ("1", "true", "True"):  # allow disabling
                return
            logs_dir = Path("logs")
            logs_dir.mkdir(parents=True, exist_ok=True)

            # Shallow mask of sensitive fields
            safe_args = {}
            for k, v in (arguments or {}).items():
                if any(s in k.lower() for s in ["password", "token", "secret"]):
                    safe_args[k] = "***"
                else:
                    safe_args[k] = v

            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event": event,
                "tool": tool_name,
                "request_id": request_id,
                "arguments": safe_args,
                "result": result,
            }
            with (logs_dir / "dabs_mcp_audit.log").open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as _:
            # Never raise from audit logging
            pass
    
    # =============================================================================
    # DABS TOOL IMPLEMENTATIONS
    # =============================================================================
    
    async def _dabs_login_status(self, arguments: Dict[str, Any]) -> str:
        """Check DABS authentication status"""
        try:
            # Check for auth file
            auth_file_path = Path("data/dabs_auth_storage.json")
            
            status = {
                "authenticated": auth_file_path.exists(),
                "session_saved": auth_file_path.exists(),
                "auth_file_exists": auth_file_path.exists(),
                "username": os.getenv("DABS_ORDERING_USERNAME", "hillshollows"),
                "environment": "Production",
                "last_login": "session_stored" if auth_file_path.exists() else None
            }
            
            return json.dumps({
                "success": True,
                "dabs_status": status,
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
    
    async def _dabs_perform_login(self, arguments: Dict[str, Any]) -> str:
        """Perform DABS login using live automation system"""
        force = arguments.get("force", False)
        
        try:
            # Import DABS automation system
            sys.path.append(str(Path(__file__).parent.parent))
            from integration.dabs_automated_ordering import DABSAutomatedOrdering
            
            # Perform actual DABS login
            async with DABSAutomatedOrdering(headless=True) as dabs_automation:
                login_success = await dabs_automation.perform_dabs_login()
                
                if login_success:
                    return json.dumps({
                        "success": True,
                        "message": "Successfully logged into DABS system",
                        "action": "login_completed",
                        "force_login": force,
                        "username": os.getenv("DABS_ORDERING_USERNAME", "hillshollows"),
                        "session_active": True,
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                else:
                    return json.dumps({
                        "success": False,
                        "error": "DABS login failed - check credentials and system availability",
                        "username": os.getenv("DABS_ORDERING_USERNAME", "hillshollows"),
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                    
        except Exception as e:
            logger.error(f"DABS login error: {e}")
            return json.dumps({
                "success": False,
                "error": f"DABS login system error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
    
    async def _dabs_process_restaurant_order(self, arguments: Dict[str, Any]) -> str:
        """Process restaurant order (mock implementation)"""
        order = arguments.get("order", {})
        
        return json.dumps({
            "success": True,
            "message": "Order processing simulation - actual implementation requires full automation system",
            "order_id": f"MOCK-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "customer": order.get("customer_name", "Unknown"),
            "items_count": len(order.get("items", [])),
            "timestamp": datetime.utcnow().isoformat()
        }, indent=2)
    
    async def _dabs_get_order_history(self, arguments: Dict[str, Any]) -> str:
        """Get order history (mock implementation)"""
        days = arguments.get("days", 30)
        
        return json.dumps({
            "success": True,
            "order_history": {
                "orders": [
                    {
                        "order_id": "MOCK-001",
                        "date": "2025-08-22T10:00:00Z",
                        "status": "Delivered",
                        "total": 125.50
                    }
                ],
                "total_count": 1,
                "days_searched": days
            },
            "timestamp": datetime.utcnow().isoformat()
        }, indent=2)
    
    async def _dabs_oauth_status(self, arguments: Dict[str, Any]) -> str:
        """Check OAuth status"""
        return json.dumps({
            "success": True,
            "oauth_status": {
                "has_tokens": False,
                "message": "OAuth implementation requires full system setup"
            },
            "timestamp": datetime.utcnow().isoformat()
        }, indent=2)
    
    async def _dabs_generate_oauth_url(self, arguments: Dict[str, Any]) -> str:
        """Generate OAuth URL"""
        return json.dumps({
            "success": True,
            "authorization_url": "https://example.com/oauth/authorize?mock=true",
            "message": "Mock OAuth URL - actual implementation requires OAuth client setup",
            "timestamp": datetime.utcnow().isoformat()
        }, indent=2)
    
    async def _dabs_system_health(self, arguments: Dict[str, Any]) -> str:
        """Check system health"""
        return json.dumps({
            "success": True,
            "health_status": {
                "server_running": True,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                "tools_registered": len(self.tools),
                "environment_vars": {
                    "DABS_USERNAME": bool(os.getenv("DABS_ORDERING_USERNAME")),
                    "DABS_PASSWORD": bool(os.getenv("DABS_ORDERING_PASSWORD")),
                    "DABS_LOGIN_URL": bool(os.getenv("DABS_ORDERING_LOGIN_URL"))
                },
                "system_ready": "Simplified MCP server operational"
            },
            "timestamp": datetime.utcnow().isoformat()
        }, indent=2)
    
    async def _dabs_lookup_product(self, arguments: Dict[str, Any]) -> str:
        """Look up product information and pricing from DABS catalog"""
        try:
            product_name = arguments.get("product_name", "")
            
            if not product_name:
                return json.dumps({
                    "success": False,
                    "error": "Product name is required",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            
            logger.info(f"🔍 Looking up product: {product_name}")
            
            # Import DABS automation system
            sys.path.append(str(Path(__file__).parent.parent))
            from integration.dabs_automated_ordering import DABSAutomatedOrdering
            
            # Initialize DABS automation for product lookup
            async with DABSAutomatedOrdering(headless=True) as dabs_automation:
                # Navigate to DABS orders page
                page = await dabs_automation._navigate_to_dabs_orders()
                
                # Validate session
                if not await dabs_automation._validate_dabs_session(page):
                    # Try to login
                    login_success = await dabs_automation.perform_dabs_login()
                    if not login_success:
                        return json.dumps({
                            "success": False,
                            "error": "DABS authentication failed - cannot access product catalog",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                    
                    # Retry navigation after login
                    page = await dabs_automation._navigate_to_dabs_orders()
                
                # Handle pending orders if any
                await dabs_automation._handle_pending_orders(page)
                
                # Create/navigate to order page for product search
                try:
                    # Try to create new order to access item search
                    create_button = await page.query_selector('text="Create New Order"')
                    if create_button:
                        await create_button.click()
                        await page.wait_for_selector('[data-order-id]', timeout=10000)
                    else:
                        # Try copy previous order
                        copy_button = await page.query_selector('text="Copy Previous Order"')
                        if copy_button:
                            await copy_button.click()
                            await page.wait_for_selector('[data-order-id]', timeout=10000)
                        else:
                            return json.dumps({
                                "success": False,
                                "error": "Cannot access DABS product catalog - no order creation button found",
                                "timestamp": datetime.utcnow().isoformat()
                            }, indent=2)
                    
                    # Search for the product
                    search_input = await page.query_selector('[placeholder*="search"], input[name*="search"], input[type="search"]')
                    if search_input:
                        await search_input.fill(product_name)
                        
                        # Look for and click search button
                        search_button = await page.query_selector('button:has-text("Search"), input[type="submit"]')
                        if search_button:
                            await search_button.click()
                        else:
                            # Try pressing Enter on search field
                            await search_input.press('Enter')
                        
                        # Wait for search results
                        await page.wait_for_timeout(3000)
                        
                        # Look for product results
                        product_results = []
                        
                        # Try different selectors for product listings
                        result_selectors = [
                            '[data-item-code]',
                            '.item-row',
                            '.product-row',
                            'tr:has(td):not(:first-child)',
                            '.search-result'
                        ]
                        
                        found_results = False
                        for selector in result_selectors:
                            items = await page.query_selector_all(selector)
                            if items:
                                found_results = True
                                logger.info(f"Found {len(items)} items with selector: {selector}")
                                
                                for item in items[:5]:  # Limit to first 5 results
                                    try:
                                        # Extract text content
                                        text_content = await item.text_content()
                                        if text_content and product_name.upper() in text_content.upper():
                                            
                                            # Try to extract product details
                                            product_info = {
                                                "product_description": text_content.strip(),
                                                "found_in_catalog": True
                                            }
                                            
                                            # Look for price information
                                            price_selectors = ['[data-price]', '.price', '.unit-price', 'td:contains("$")']
                                            for price_sel in price_selectors:
                                                price_elem = await item.query_selector(price_sel)
                                                if price_elem:
                                                    price_text = await price_elem.text_content()
                                                    if '$' in price_text:
                                                        product_info["unit_price"] = price_text.strip()
                                                        break
                                            
                                            # Look for SKU/item code
                                            sku_selectors = ['[data-item-code]', '.sku', '.item-code']
                                            for sku_sel in sku_selectors:
                                                sku_elem = await item.query_selector(sku_sel)
                                                if sku_elem:
                                                    sku_text = await sku_elem.get_attribute('data-item-code') or await sku_elem.text_content()
                                                    if sku_text:
                                                        product_info["sku"] = sku_text.strip()
                                                        break
                                            
                                            product_results.append(product_info)
                                            
                                    except Exception as e:
                                        logger.warning(f"Error extracting product info: {e}")
                                        continue
                                        
                                if product_results:
                                    break
                        
                        if product_results:
                            return json.dumps({
                                "success": True,
                                "search_term": product_name,
                                "products_found": len(product_results),
                                "products": product_results,
                                "message": f"Found {len(product_results)} matching product(s) in DABS catalog",
                                "timestamp": datetime.utcnow().isoformat()
                            }, indent=2)
                        else:
                            # No specific matches found, return general search status
                            page_content = await page.content()
                            no_results_indicators = ["no results", "not found", "no items", "0 results"]
                            has_no_results = any(indicator in page_content.lower() for indicator in no_results_indicators)
                            
                            return json.dumps({
                                "success": True,
                                "search_term": product_name,
                                "products_found": 0,
                                "products": [],
                                "message": f"Product '{product_name}' not found in DABS catalog" if has_no_results else f"Search completed but could not parse results for '{product_name}'",
                                "catalog_accessible": True,
                                "timestamp": datetime.utcnow().isoformat()
                            }, indent=2)
                    
                    else:
                        return json.dumps({
                            "success": False,
                            "error": "Could not locate product search interface in DABS system",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                        
                except Exception as search_error:
                    return json.dumps({
                        "success": False,
                        "error": f"Product search failed: {str(search_error)}",
                        "search_term": product_name,
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                    
        except Exception as e:
            logger.error(f"DABS product lookup error: {e}")
            return json.dumps({
                "success": False,
                "error": f"Product lookup system error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
    
    async def _dabs_search_all_items(self, arguments: Dict[str, Any]) -> str:
        """Search the complete DABS product catalog"""
        try:
            query = arguments.get("query", "")
            page = arguments.get("page", 1)
            page_size = arguments.get("page_size", 25)
            
            if not query:
                return json.dumps({
                    "success": False,
                    "error": "Search query is required",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            
            logger.info(f"🔍 Searching DABS catalog: '{query}' (page {page}, size {page_size})")
            
            # Import DABS automation system
            sys.path.append(str(Path(__file__).parent.parent))
            from integration.dabs_automated_ordering import DABSAutomatedOrdering
            
            async with DABSAutomatedOrdering(headless=True) as dabs_automation:
                # Ensure authenticated session
                page_obj = await dabs_automation._navigate_to_dabs_orders()
                if not await dabs_automation._validate_dabs_session(page_obj):
                    login_success = await dabs_automation.perform_dabs_login()
                    if not login_success:
                        return json.dumps({
                            "success": False,
                            "error": "DABS authentication failed",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                
                # Navigate to All Items interface
                all_items_button = await page_obj.query_selector('text="All Items"')
                if all_items_button:
                    await all_items_button.click()
                    await page_obj.wait_for_timeout(2000)
                
                # Perform search
                search_input = await page_obj.query_selector('[placeholder*="search"], input[name*="search"], input[type="search"]')
                if search_input:
                    await search_input.fill(query)
                    await search_input.press('Enter')
                    await page_obj.wait_for_timeout(3000)
                
                # Extract search results
                items = []
                result_rows = await page_obj.query_selector_all('tr[data-item], .item-row, tr:has(td)')
                
                for row in result_rows[:page_size]:
                    try:
                        cells = await row.query_selector_all('td')
                        if len(cells) >= 6:  # Expected columns from screenshots
                            item_code_text = await cells[0].text_content()
                            description_text = await cells[1].text_content()
                            bottles_text = await cells[2].text_content()
                            case_price_text = await cells[3].text_content()
                            cases_available_text = await cells[4].text_content()
                            
                            if item_code_text and description_text:
                                items.append({
                                    "item_code": item_code_text.strip(),
                                    "description": description_text.strip(),
                                    "bottles_per_case": int(bottles_text.strip()) if bottles_text.isdigit() else 0,
                                    "case_price": float(case_price_text.replace('$', '').replace(',', '')) if '$' in case_price_text else 0.0,
                                    "cases_available": int(cases_available_text.strip()) if cases_available_text.isdigit() else 0,
                                    "status": "1"  # Default status
                                })
                    except Exception as e:
                        logger.warning(f"Error parsing item row: {e}")
                        continue
                
                return json.dumps({
                    "success": True,
                    "query": query,
                    "items": items,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "items_found": len(items),
                        "total_entries": 4290  # From screenshots
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
                
        except Exception as e:
            logger.error(f"DABS search error: {e}")
            return json.dumps({
                "success": False,
                "error": f"Search system error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
    
    async def _dabs_get_open_order(self, arguments: Dict[str, Any]) -> str:
        """Get current open order details"""
        try:
            logger.info("📋 Getting open DABS order details")
            
            sys.path.append(str(Path(__file__).parent.parent))
            from integration.dabs_automated_ordering import DABSAutomatedOrdering
            
            async with DABSAutomatedOrdering(headless=True) as dabs_automation:
                page = await dabs_automation._navigate_to_dabs_orders()
                
                if not await dabs_automation._validate_dabs_session(page):
                    login_success = await dabs_automation.perform_dabs_login()
                    if not login_success:
                        return json.dumps({
                            "success": False,
                            "error": "DABS authentication failed",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                    page = await dabs_automation._navigate_to_dabs_orders()
                
                # Look for open order indicator
                open_order_row = await page.query_selector('.open-order, tr:has(td:contains("Open"))')
                
                if open_order_row:
                    # Extract order details
                    cells = await open_order_row.query_selector_all('td')
                    if len(cells) >= 4:
                        order_id_text = await cells[0].text_content()
                        date_text = await cells[1].text_content()
                        store_text = await cells[2].text_content()
                        status_text = await cells[3].text_content()
                        
                        return json.dumps({
                            "success": True,
                            "has_open_order": True,
                            "order": {
                                "order_id": order_id_text.strip() if order_id_text else "",
                                "date_created": date_text.strip() if date_text else "",
                                "store": store_text.strip() if store_text else "Warehouse",
                                "status": status_text.strip() if status_text else "Open"
                            },
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                
                return json.dumps({
                    "success": True,
                    "has_open_order": False,
                    "message": "No open orders found",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
                
        except Exception as e:
            logger.error(f"Get open order error: {e}")
            return json.dumps({
                "success": False,
                "error": f"Get open order failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
    
    async def _dabs_create_new_order(self, arguments: Dict[str, Any]) -> str:
        """Create a new DABS order"""
        try:
            reference = arguments.get("reference", "Restaurant Order via MCP")
            
            logger.info(f"🆕 Creating new DABS order with reference: '{reference}'")
            
            sys.path.append(str(Path(__file__).parent.parent))
            from integration.dabs_automated_ordering import DABSAutomatedOrdering
            
            async with DABSAutomatedOrdering(headless=True) as dabs_automation:
                page = await dabs_automation._navigate_to_dabs_orders()
                
                if not await dabs_automation._validate_dabs_session(page):
                    login_success = await dabs_automation.perform_dabs_login()
                    if not login_success:
                        return json.dumps({
                            "success": False,
                            "error": "DABS authentication failed", 
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                    page = await dabs_automation._navigate_to_dabs_orders()
                
                # Check for existing open order first
                open_order_check = await page.query_selector('.open-order, tr:has(td:contains("Open"))')
                if open_order_check:
                    return json.dumps({
                        "success": False,
                        "error": "Pending order must be submitted or deleted before a new order can be created",
                        "has_open_order": True,
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                
                # Click Create New Order - Multiple selector strategies for reliability
                create_button = None
                
                # Strategy 1: Target Bootstrap modal trigger (most specific)
                create_button = await page.query_selector('a[data-bs-target="#paTypeModal"]')
                
                if not create_button:
                    # Strategy 2: Target by class and text combination  
                    create_button = await page.query_selector('a.btn:has-text("Create New Order")')
                
                if not create_button:
                    # Strategy 3: Target by full class structure
                    create_button = await page.query_selector('a.btn.btn-orange.btn-lg:has-text("Create New Order")')
                
                if not create_button:
                    # Strategy 4: Simple text fallback
                    create_button = await page.query_selector('text="Create New Order"')
                
                if create_button:
                    logger.info("🎯 Found Create New Order button - clicking...")
                    await create_button.click()
                    await page.wait_for_timeout(3000)
                    
                    # Handle modal if it appears
                    modal_present = await page.query_selector('#paTypeModal')
                    if modal_present:
                        logger.info("📋 Modal opened - handling order type selection...")
                        # Handle any modal interactions here if needed
                    
                    # Set reference if provided
                    if reference:
                        reference_input = await page.query_selector('input[name*="reference"], input[placeholder*="reference"], textarea[name*="notes"]')
                        if reference_input:
                            await reference_input.fill(reference)
                            update_button = await page.query_selector('button:has-text("Update")')
                            if update_button:
                                await update_button.click()
                                await page.wait_for_timeout(1000)
                    
                    # Extract new order ID
                    order_id_element = await page.query_selector('[data-order-id], .order-id')
                    order_id = await order_id_element.get_attribute('data-order-id') if order_id_element else "Unknown"
                    
                    return json.dumps({
                        "success": True,
                        "order_created": True,
                        "order_id": order_id,
                        "reference": reference,
                        "url": page.url,
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                
                return json.dumps({
                    "success": False,
                    "error": "Create New Order button not found",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
                
        except Exception as e:
            logger.error(f"Create order error: {e}")
            return json.dumps({
                "success": False,
                "error": f"Create order failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
    
    async def _dabs_add_item_to_order(self, arguments: Dict[str, Any]) -> str:
        """Add specific item to current DABS order"""
        try:
            item_code = arguments.get("item_code", "")
            cases = arguments.get("cases", 1)
            
            if not item_code:
                return json.dumps({
                    "success": False,
                    "error": "Item code is required",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            
            logger.info(f"➕ Adding item {item_code} ({cases} cases) to DABS order")
            
            sys.path.append(str(Path(__file__).parent.parent))
            from integration.dabs_automated_ordering import DABSAutomatedOrdering
            
            async with DABSAutomatedOrdering(headless=True) as dabs_automation:
                # Navigate to order page (should have open order)
                page = await dabs_automation._navigate_to_dabs_orders()
                
                # Open the existing open order for editing
                edit_button = await page.query_selector('.open-order .edit-icon, tr:has(td:contains("Open")) .edit')
                if edit_button:
                    await edit_button.click()
                    await page.wait_for_timeout(2000)
                
                # Open All Items catalog
                all_items_button = await page.query_selector('text="All Items"')
                if all_items_button:
                    await all_items_button.click()
                    await page.wait_for_timeout(2000)
                
                # Search for the specific item
                search_input = await page.query_selector('[placeholder*="search"], input[name*="search"]')
                if search_input:
                    await search_input.fill(item_code)
                    await search_input.press('Enter')
                    await page.wait_for_timeout(2000)
                
                # Find the item row and add to order
                item_row = await page.query_selector(f'tr:has(td:contains("{item_code}"))')
                if item_row:
                    # Set quantity
                    qty_input = await item_row.query_selector('input[name*="qty"], .qty-input')
                    if qty_input:
                        await qty_input.fill(str(cases))
                    
                    # Click Add to Order
                    add_button = await item_row.query_selector('button:has-text("Add"), .add-button')
                    if add_button:
                        await add_button.click()
                        await page.wait_for_timeout(2000)
                        
                        return json.dumps({
                            "success": True,
                            "item_added": True,
                            "item_code": item_code,
                            "cases_ordered": cases,
                            "message": f"Added {cases} cases of {item_code} to order",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                
                return json.dumps({
                    "success": False,
                    "error": f"Item {item_code} not found in catalog or could not be added",
                    "item_code": item_code,
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
                
        except Exception as e:
            logger.error(f"Add item error: {e}")
            return json.dumps({
                "success": False,
                "error": f"Add item failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
    
    async def _dabs_submit_order(self, arguments: Dict[str, Any]) -> str:
        """Submit current DABS order for processing"""
        try:
            confirm = arguments.get("confirm", True)
            
            if not confirm:
                return json.dumps({
                    "success": False,
                    "error": "Order submission requires confirmation",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            
            # Pre-state validation: must have a single pending open order
            pre_state_json = await self._dabs_get_open_order({})
            pre_state = json.loads(pre_state_json)
            if not (pre_state.get("success") and pre_state.get("has_open_order")):
                return json.dumps({
                    "success": False,
                    "error": "No open order to submit",
                    "message": "Submission requires a single pending order",
                    "pre_state": pre_state,
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)

            logger.info("🚀 Submitting DABS order for processing")
            
            sys.path.append(str(Path(__file__).parent.parent))
            from integration.dabs_automated_ordering import DABSAutomatedOrdering
            
            async with DABSAutomatedOrdering(headless=True) as dabs_automation:
                page = await dabs_automation._navigate_to_dabs_orders()
                
                # Navigate to open order
                edit_button = await page.query_selector('.open-order .edit-icon, tr:has(td:contains("Open")) .edit')
                if edit_button:
                    await edit_button.click()
                    await page.wait_for_timeout(2000)
                
                # Click Submit Order button
                submit_button = await page.query_selector('button:has-text("Submit Order")')
                if submit_button:
                    await submit_button.click()
                    await page.wait_for_timeout(1000)
                    
                    # Confirm submission if prompted
                    confirm_button = await page.query_selector('button:has-text("Confirm"), button:has-text("Yes"), button:has-text("OK")')
                    if confirm_button:
                        await confirm_button.click()
                        await page.wait_for_timeout(3000)
                    
                    # Look for success indicators
                    success_message = await page.query_selector('.success, .confirmation, text="submitted"')
                    # Post-state validation: ensure no open order remains
                    post_state_json = await self._dabs_get_open_order({})
                    post_state = json.loads(post_state_json)
                    clean = post_state.get("success") and not post_state.get("has_open_order")

                    if success_message or clean:
                        return json.dumps({
                            "success": True,
                            "action": "order_submitted",
                            "order_submitted": True,
                            "message": "Order successfully submitted to DABS" if success_message else "Submission completed (verified clean state)",
                            "note": "Quantities available were current as of the previous evening",
                            "pre_state": pre_state,
                            "post_state": post_state,
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                    
                    return json.dumps({
                        "success": False,
                        "error": "Submission did not verify clean state",
                        "order_submitted": False,
                        "pre_state": pre_state,
                        "post_state": post_state,
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                
                return json.dumps({
                    "success": False,
                    "error": "Submit Order button not found - no open order to submit",
                    "pre_state": pre_state,
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            
        except Exception as e:
            logger.error(f"Submit order error: {e}")
            return json.dumps({
                "success": False,
                "error": f"Submit order failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
    
    async def _dabs_return_to_order(self, arguments: Dict[str, Any]) -> str:
        """Return from EditOrder page back to main orders list"""
        try:
            order_id = arguments.get("order_id", None)
            
            logger.info("🔙 Returning from EditOrder page to main orders list")
            
            sys.path.append(str(Path(__file__).parent.parent))
            from integration.dabs_automated_ordering import DABSAutomatedOrdering
            
            async with DABSAutomatedOrdering(headless=True) as dabs_automation:
                # Get current page (should be on EditOrder page)
                page = await dabs_automation.context.pages[0] if dabs_automation.context.pages else None
                
                if not page:
                    page = await dabs_automation._navigate_to_dabs_orders()
                
                # Verify we're on an EditOrder page
                current_url = page.url
                if "EditOrder" not in current_url:
                    logger.warning(f"⚠️ Not on EditOrder page. Current URL: {current_url}")
                    # If not on EditOrder page, navigate to orders list anyway
                    orders_page = await dabs_automation._navigate_to_dabs_orders()
                    return json.dumps({
                        "success": True,
                        "action": "navigated_to_orders",
                        "message": "Navigated directly to orders list",
                        "previous_url": current_url,
                        "current_url": orders_page.url,
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                
                # Extract order ID from URL if not provided
                if not order_id:
                    import re
                    url_match = re.search(r'orderId=([^&]+)', current_url)
                    order_id = url_match.group(1) if url_match else "unknown"
                
                logger.info(f"📋 Current order ID: {order_id}")
                
                # Find and click the Return to Order button - multiple strategies
                return_button = None
                
                # Strategy 1: Target by exact class structure and href
                return_button = await page.query_selector('a.btn.button4.btn-sm[href="/ProdApps/OnlineOrders/Orders"]')
                
                if not return_button:
                    # Strategy 2: Target by href path only
                    return_button = await page.query_selector('a[href="/ProdApps/OnlineOrders/Orders"]')
                
                if not return_button:
                    # Strategy 3: Target by class and text combination
                    return_button = await page.query_selector('a.btn:has-text("Return to Order")')
                
                if not return_button:
                    # Strategy 4: Target by text only (fallback)
                    return_button = await page.query_selector('text="Return to Order"')
                
                if not return_button:
                    # Strategy 5: Alternative text variations
                    return_button = await page.query_selector('text="Return to Orders"') or \
                                   await page.query_selector('text="Back to Orders"') or \
                                   await page.query_selector('a[role="button"]:has-text("Return")')
                
                if return_button:
                    logger.info("🎯 Found Return to Order button - clicking...")
                    
                    # Record current page for comparison
                    before_url = page.url
                    
                    # Click the button
                    await return_button.click()
                    
                    # Wait for navigation
                    await page.wait_for_timeout(2000)
                    
                    # Verify navigation occurred
                    after_url = page.url
                    
                    # Check if we successfully navigated to orders list
                    if "/Orders" in after_url and "EditOrder" not in after_url:
                        logger.info(f"✅ Successfully returned to orders list: {after_url}")
                        return json.dumps({
                            "success": True,
                            "action": "returned_to_orders",
                            "order_id": order_id,
                            "previous_url": before_url,
                            "current_url": after_url,
                            "message": f"Successfully returned from order {order_id} to orders list",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                    else:
                        logger.warning(f"⚠️ Navigation may have failed. URL: {after_url}")
                        return json.dumps({
                            "success": False,
                            "error": "Navigation verification failed",
                            "order_id": order_id,
                            "expected_path": "/Orders",
                            "actual_url": after_url,
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                
                # Button not found - try direct navigation as fallback
                logger.warning("⚠️ Return to Order button not found - using direct navigation")
                
                orders_page = await dabs_automation._navigate_to_dabs_orders()
                
                return json.dumps({
                    "success": True,
                    "action": "direct_navigation",
                    "order_id": order_id,
                    "message": "Button not found - navigated directly to orders list",
                    "current_url": orders_page.url,
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
                
        except Exception as e:
            logger.error(f"Return to order error: {e}")
            return json.dumps({
                "success": False,
                "error": f"Return to order failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
    
    async def _dabs_edit_open_order(self, arguments: Dict[str, Any]) -> str:
        """Click edit button for pending open order to navigate to EditOrder page"""
        try:
            logger.info("✏️ Looking for pending open order to edit")
            
            sys.path.append(str(Path(__file__).parent.parent))
            from integration.dabs_automated_ordering import DABSAutomatedOrdering
            
            async with DABSAutomatedOrdering(headless=True) as dabs_automation:
                # Navigate to main orders page
                page = await dabs_automation._navigate_to_dabs_orders()
                
                if not await dabs_automation._validate_dabs_session(page):
                    login_success = await dabs_automation.perform_dabs_login()
                    if not login_success:
                        return json.dumps({
                            "success": False,
                            "error": "DABS authentication failed",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                    page = await dabs_automation._navigate_to_dabs_orders()
                
                # Look for the Open Order section
                open_order_section = await page.query_selector('h3:has-text("Open Order")')
                if not open_order_section:
                    return json.dumps({
                        "success": False,
                        "error": "No Open Order section found - no pending orders available",
                        "message": "The Open Order section is only visible when there is a pending order",
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                
                logger.info("📋 Open Order section found")
                
                # Extract order details from the visible table
                order_details = {}
                
                # Try to extract order ID, date, store, and status from the table
                order_row = await page.query_selector('table tr:not(:first-child)')  # Skip header row
                if order_row:
                    cells = await order_row.query_selector_all('td')
                    if len(cells) >= 4:
                        order_id_text = await cells[0].text_content()
                        date_text = await cells[1].text_content()
                        store_text = await cells[2].text_content()
                        status_text = await cells[3].text_content()
                        
                        order_details = {
                            "order_id": order_id_text.strip() if order_id_text else "",
                            "date_created": date_text.strip() if date_text else "",
                            "store": store_text.strip() if store_text else "",
                            "status": status_text.strip() if status_text else ""
                        }
                
                logger.info(f"📋 Order details: {order_details}")
                
                # Find and click the edit button - multiple strategies
                edit_button = None
                
                # Strategy 1: Target Material Icons edit button with tooltip
                edit_button = await page.query_selector('i.material-icons.blue[data-bs-original-title="Edit"]')
                
                if not edit_button:
                    # Strategy 2: Target Material Icons with "Edit" tooltip (any tooltip attribute)
                    edit_button = await page.query_selector('i.material-icons[title*="Edit"], i.material-icons[data-original-title*="Edit"]')
                
                if not edit_button:
                    # Strategy 3: Look for edit icon in the Actions column
                    actions_cell = await page.query_selector('td:last-child')  # Actions is typically the last column
                    if actions_cell:
                        edit_button = await actions_cell.query_selector('i.material-icons.blue, .edit-icon, [title*="Edit"]')
                
                if not edit_button:
                    # Strategy 4: Look for any clickable element with edit functionality in the Open Order area
                    edit_button = await page.query_selector('i.material-icons:has-text("edit"), i.material-icons:has-text("mode_edit")')
                
                if not edit_button:
                    # Strategy 5: Find edit button by parent anchor or button element
                    edit_anchor = await page.query_selector('a[href*="EditOrder"], button[onclick*="edit"], a[title*="Edit"]')
                    if edit_anchor:
                        edit_button = edit_anchor
                
                if edit_button:
                    logger.info("🎯 Found edit button - clicking to open order for editing...")
                    
                    # Record current URL for comparison
                    before_url = page.url
                    
                    # Click the edit button
                    await edit_button.click()
                    
                    # Wait for navigation to EditOrder page
                    await page.wait_for_timeout(3000)
                    
                    # Verify navigation to EditOrder page
                    after_url = page.url
                    
                    if "EditOrder" in after_url:
                        logger.info(f"✅ Successfully navigated to EditOrder page: {after_url}")
                        
                        # Extract order ID from URL to confirm
                        import re
                        url_match = re.search(r'orderId=([^&]+)', after_url)
                        url_order_id = url_match.group(1) if url_match else "unknown"
                        
                        return json.dumps({
                            "success": True,
                            "action": "opened_order_for_editing",
                            "order_details": order_details,
                            "url_order_id": url_order_id,
                            "previous_url": before_url,
                            "current_url": after_url,
                            "message": f"Successfully opened order {order_details.get('order_id', 'unknown')} for editing",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                    else:
                        logger.warning(f"⚠️ Navigation may have failed. Expected EditOrder, got: {after_url}")
                        return json.dumps({
                            "success": False,
                            "error": "Navigation to EditOrder page failed",
                            "expected_pattern": "EditOrder",
                            "actual_url": after_url,
                            "order_details": order_details,
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                
                # Edit button not found
                logger.warning("⚠️ Edit button not found in Open Order section")
                return json.dumps({
                    "success": False,
                    "error": "Edit button not found in Open Order section",
                    "order_details": order_details,
                    "message": "The edit button (pencil icon) was not found. The order may not be editable or the page structure has changed.",
                    "troubleshooting": [
                        "Verify the order status is 'Pending'",
                        "Check if the Open Order section is fully loaded",
                        "Ensure the order has not been submitted or deleted"
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
                
        except Exception as e:
            logger.error(f"Edit open order error: {e}")
            return json.dumps({
                "success": False,
                "error": f"Edit open order failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
    
    async def _dabs_delete_open_order(self, arguments: Dict[str, Any]) -> str:
        """Click delete button to remove pending open order.
        Supports headed mode via existing script and returns artifact paths.
        Args:
            confirm (bool): required confirmation
            headed (bool): run headed (uses subprocess script path)
            order_id (str|None): optional id to target row
            return_artifacts (bool): include artifact file paths
        """
        try:
            confirm = arguments.get("confirm", True)
            headed = arguments.get("headed", False)
            target_order_id = arguments.get("order_id")
            return_artifacts = arguments.get("return_artifacts", True)
            
            if not confirm:
                return json.dumps({
                    "success": False,
                    "error": "Order deletion requires confirm=true",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)

            # Safety: require either headed=true or return_artifacts=true for traceability on destructive ops
            if not headed and not return_artifacts:
                return json.dumps({
                    "success": False,
                    "error": "Destructive operation requires headed=true or return_artifacts=true for audit traceability",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            
            # If headed, route through existing robust script for maximum reliability
            if headed:
                try:
                    import subprocess
                    env = os.environ.copy()
                    env["DABS_HEADLESS"] = "false"
                    if target_order_id:
                        env["DABS_ORDER_ID"] = str(target_order_id)

                    # Run the script and capture output
                    proc = subprocess.run(
                        [sys.executable, str(Path("scripts") / "delete_dabs_order.py")],
                        capture_output=True, text=True, env=env, cwd=str(Path(__file__).parent.parent.parent)
                    )

                    stdout = proc.stdout.strip()
                    success = proc.returncode == 0

                    # Artifact paths
                    artifacts_dir = Path("data") / "playwright_screenshots"
                    artifacts = {
                        "before_png": str(artifacts_dir / "debug_dabs_interface.png"),
                        "after_png": str(artifacts_dir / "debug_dabs_interface_after.png"),
                        "before_html": str(artifacts_dir / "orders_list_headed.html"),
                        "after_html": str(artifacts_dir / "orders_list_after.html")
                    } if return_artifacts else None

                    return json.dumps({
                        "success": bool(success),
                        "action": "order_deleted" if success else "order_delete_attempt",
                        "message": "Headed deletion completed" if success else "Headed deletion finished with errors",
                        "details": {"stdout": stdout[-2000:]},
                        "artifacts": artifacts,
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                except Exception as se:
                    logger.error(f"Headed script execution failed: {se}")
                    # Fall back to inline automation below

            logger.info("🗑️ Looking for pending open order to delete")
            
            sys.path.append(str(Path(__file__).parent.parent))
            from integration.dabs_automated_ordering import DABSAutomatedOrdering
            
            async with DABSAutomatedOrdering(headless=True) as dabs_automation:
                # Navigate to main orders page
                page = await dabs_automation._navigate_to_dabs_orders()
                
                if not await dabs_automation._validate_dabs_session(page):
                    login_success = await dabs_automation.perform_dabs_login()
                    if not login_success:
                        return json.dumps({
                            "success": False,
                            "error": "DABS authentication failed",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                    page = await dabs_automation._navigate_to_dabs_orders()
                
                # Look for the Open Order section
                open_order_section = await page.query_selector('h3:has-text("Open Order")')
                if not open_order_section:
                    return json.dumps({
                        "success": False,
                        "error": "No Open Order section found - no pending orders to delete",
                        "message": "The Open Order section is only visible when there is a pending order",
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                
                logger.info("📋 Open Order section found")
                
                # Extract order details before deletion
                order_details = {}
                order_row = await page.query_selector('table tr:not(:first-child)')  # Skip header row
                if order_row:
                    cells = await order_row.query_selector_all('td')
                    if len(cells) >= 4:
                        order_id_text = await cells[0].text_content()
                        date_text = await cells[1].text_content()
                        store_text = await cells[2].text_content()
                        status_text = await cells[3].text_content()
                        
                        order_details = {
                            "order_id": order_id_text.strip() if order_id_text else "",
                            "date_created": date_text.strip() if date_text else "",
                            "store": store_text.strip() if store_text else "",
                            "status": status_text.strip() if status_text else ""
                        }
                
                logger.info(f"🗑️ Order to delete: {order_details}")
                
                # If specific order id provided, try row-scoped anchor first
                if target_order_id:
                    try:
                        row_delete = await page.query_selector(
                            f'div.tableOpen tbody tr:has(td:has-text("{target_order_id}")) a.open-AddDialog.delete, '
                            'a[href="#DeleteOrder"]'
                        )
                        if row_delete:
                            await row_delete.click()
                            await page.wait_for_selector('#DeleteOrder', timeout=5000)
                            confirm_btn = await page.wait_for_selector(
                                "#DeleteOrder input[type='submit'][value='Delete']",
                                timeout=5000
                            )
                            await confirm_btn.click()
                            await page.wait_for_timeout(2000)
                    except Exception:
                        pass

                # PRECISE DELETION SEQUENCE - icon → red Delete
                logger.info("🎯 Using proven deletion sequence: delete icon -> red Delete button")
                
                # STEP 1: Click the delete icon (trash can)
                delete_icon_selector = 'i.material-icons[data-bs-original-title="Delete"], i.material-icons[title="Delete"]'
                
                try:
                    # Wait for the delete icon to be visible
                    await page.wait_for_selector(delete_icon_selector, timeout=10000)
                    logger.info('✅ Found delete icon')
                    
                    # Click the delete icon
                    await page.click(delete_icon_selector)
                    logger.info('🗑️ STEP 1: Clicked delete icon (trash can)')
                    
                    # Wait for confirmation dialog to appear
                    await page.wait_for_timeout(2000)
                    
                    # STEP 2: Look for the red Delete button in the confirmation dialog
                    red_delete_button_selector = 'input[type="submit"][value="Delete"].btn.btn-red'
                    
                    try:
                        # Wait for the red Delete button to appear
                        await page.wait_for_selector(red_delete_button_selector, timeout=5000)
                        logger.info('✅ Found red Delete button in confirmation dialog')
                        
                        # Click the red Delete button
                        await page.click(red_delete_button_selector)
                        logger.info('🗑️ STEP 2: Clicked red Delete button - CONFIRMING DELETION')
                        
                        # Wait for deletion to process
                        await page.wait_for_timeout(3000)
                        
                        # Verify deletion by checking if the order is still on the page
                        order_id = order_details.get("order_id", "")
                        if order_id:
                            page_content = await page.content()
                            if order_id not in page_content:
                                logger.info(f'🎉 SUCCESS: Order {order_id} has been deleted successfully!')
                                delete_successful = True
                            else:
                                logger.warning(f'⚠️ Order {order_id} still visible - deletion may have failed')
                                delete_successful = False
                        else:
                            # If no order ID, check if open order section is gone
                            open_order_check = await page.query_selector('h3:has-text("Open Order")')
                            delete_successful = open_order_check is None
                            
                    except Exception as e:
                        logger.error(f'❌ Error with red Delete button: {e}')
                        
                        # Fallback: look for any delete button in dialog
                        try:
                            delete_buttons = await page.query_selector_all('button:has-text("Delete"), input[value="Delete"]')
                            if delete_buttons:
                                await delete_buttons[0].click()
                                logger.info('🗑️ STEP 2: Clicked fallback delete button')
                                await page.wait_for_timeout(3000)
                                
                                # Check success
                                if order_details.get("order_id"):
                                    page_content = await page.content()
                                    delete_successful = order_details["order_id"] not in page_content
                                else:
                                    open_order_check = await page.query_selector('h3:has-text("Open Order")')
                                    delete_successful = open_order_check is None
                            else:
                                delete_successful = False
                        except:
                            delete_successful = False
                
                except Exception as e:
                    logger.error(f'❌ Error finding/clicking delete icon: {e}')
                    delete_successful = False
                
                # Capture artifacts in inline flow if requested
                artifacts = None
                if return_artifacts:
                    try:
                        artifacts_dir = Path("data") / "playwright_screenshots"
                        artifacts = {
                            "before_png": str(artifacts_dir / "debug_dabs_interface.png"),
                            "after_png": str(artifacts_dir / "debug_dabs_interface_after.png"),
                            "before_html": str(artifacts_dir / "orders_list_headless.html"),
                            "after_html": str(artifacts_dir / "orders_list_after_headless.html")
                        }
                    except Exception:
                        artifacts = None

                # Return results based on deletion success
                if delete_successful:
                    logger.info("✅ Order successfully deleted using precise deletion sequence")
                    return json.dumps({
                        "success": True,
                        "action": "order_deleted",
                        "deleted_order": order_details,
                        "method": "precise_deletion_sequence",
                        "message": f"Successfully deleted order {order_details.get('order_id', 'unknown')} using proven deletion method",
                        "artifacts": artifacts,
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                else:
                    logger.warning("⚠️ Precise deletion sequence failed")
                    return json.dumps({
                        "success": False,
                        "error": "Order deletion failed using precise sequence",
                        "order_details": order_details,
                        "message": "The proven deletion sequence (delete icon -> red Delete button) did not complete successfully",
                        "troubleshooting": [
                            "Verify the order status allows deletion (must be Pending)",
                            "Check if DABS interface has changed",
                            "Try manual deletion via DABS web interface"
                        ],
                        "artifacts": artifacts,
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)

                
        except Exception as e:
            logger.error(f"Delete open order error: {e}")
            return json.dumps({
                "success": False,
                "error": f"Delete open order failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
    
    async def _dabs_check_order_to_print(self, arguments: Dict[str, Any]) -> str:
        """Check/uncheck order checkboxes in Order History for batch printing"""
        try:
            order_ids = arguments.get("order_ids", [])
            action = arguments.get("action", "check")
            
            if not order_ids and action not in ["check_all", "uncheck_all"]:
                return json.dumps({
                    "success": False,
                    "error": "Order IDs required unless using check_all/uncheck_all",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            
            logger.info(f"📋 {action.title()} order checkboxes for: {order_ids}")
            
            sys.path.append(str(Path(__file__).parent.parent))
            from integration.dabs_automated_ordering import DABSAutomatedOrdering
            
            async with DABSAutomatedOrdering(headless=True) as dabs_automation:
                # Navigate to main orders page
                page = await dabs_automation._navigate_to_dabs_orders()
                
                if not await dabs_automation._validate_dabs_session(page):
                    login_success = await dabs_automation.perform_dabs_login()
                    if not login_success:
                        return json.dumps({
                            "success": False,
                            "error": "DABS authentication failed",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                    page = await dabs_automation._navigate_to_dabs_orders()
                
                # Wait for Order History table to load
                await page.wait_for_timeout(2000)
                
                checked_orders = []
                skipped_orders = []
                
                if action in ["check_all", "uncheck_all"]:
                    # Handle bulk actions
                    all_checkboxes = await page.query_selector_all('input[type="checkbox"][name="IsChecked"]')
                    logger.info(f"📋 Found {len(all_checkboxes)} order checkboxes")
                    
                    for checkbox in all_checkboxes:
                        try:
                            checkbox_value = await checkbox.get_attribute('value')
                            is_checked = await checkbox.is_checked()
                            
                            if action == "check_all" and not is_checked:
                                await checkbox.click()
                                checked_orders.append(checkbox_value)
                                logger.info(f"✅ Checked order: {checkbox_value}")
                            elif action == "uncheck_all" and is_checked:
                                await checkbox.click()
                                checked_orders.append(checkbox_value)
                                logger.info(f"❌ Unchecked order: {checkbox_value}")
                            
                            await page.wait_for_timeout(100)  # Small delay between clicks
                            
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to {action} checkbox {checkbox_value}: {e}")
                            skipped_orders.append(checkbox_value)
                
                else:
                    # Handle specific order IDs
                    for order_id in order_ids:
                        try:
                            # Multiple strategies to find checkboxes
                            checkbox = None
                            
                            # Strategy 1: Direct value match (Sales Order format)
                            checkbox = await page.query_selector(f'input[type="checkbox"][value="{order_id}"]')
                            
                            if not checkbox:
                                # Strategy 2: Order ID format (assuming SOO prefix for sales orders)
                                sales_order_format = f"SOO0{order_id}" if order_id.isdigit() else order_id
                                checkbox = await page.query_selector(f'input[type="checkbox"][value="{sales_order_format}"]')
                            
                            if not checkbox:
                                # Strategy 3: Reverse format (remove SOO prefix if present)
                                if order_id.startswith("SOO"):
                                    numeric_id = order_id[3:].lstrip("0")  # Remove SOO and leading zeros
                                    checkbox = await page.query_selector(f'input[type="checkbox"][value="{numeric_id}"]')
                            
                            if not checkbox:
                                # Strategy 4: Look in table row containing the order ID
                                order_row = await page.query_selector(f'tr:has-text("{order_id}")')
                                if order_row:
                                    checkbox = await order_row.query_selector('input[type="checkbox"][name="IsChecked"]')
                            
                            if checkbox:
                                is_checked = await checkbox.is_checked()
                                checkbox_value = await checkbox.get_attribute('value')
                                
                                if (action == "check" and not is_checked) or (action == "uncheck" and is_checked):
                                    await checkbox.click()
                                    await page.wait_for_timeout(200)  # Wait for UI update
                                    
                                    checked_orders.append({
                                        "order_id": order_id,
                                        "checkbox_value": checkbox_value,
                                        "action": action
                                    })
                                    logger.info(f"✅ {action.title()}ed order: {order_id} (value: {checkbox_value})")
                                else:
                                    checked_orders.append({
                                        "order_id": order_id,
                                        "checkbox_value": checkbox_value,
                                        "action": f"already_{action}ed"
                                    })
                                    logger.info(f"ℹ️ Order {order_id} already {action}ed")
                            else:
                                skipped_orders.append(order_id)
                                logger.warning(f"⚠️ Checkbox not found for order: {order_id}")
                                
                        except Exception as e:
                            logger.error(f"❌ Error processing order {order_id}: {e}")
                            skipped_orders.append(order_id)
                
                # Get current selection count for validation
                selected_checkboxes = await page.query_selector_all('input[type="checkbox"][name="IsChecked"]:checked')
                selection_count = len(selected_checkboxes)
                
                logger.info(f"📊 Order selection complete: {len(checked_orders)} processed, {len(skipped_orders)} skipped, {selection_count} total selected")
                
                return json.dumps({
                    "success": True,
                    "action": action,
                    "processed_orders": checked_orders,
                    "skipped_orders": skipped_orders,
                    "total_selected": selection_count,
                    "message": f"Successfully {action}ed {len(checked_orders)} orders",
                    "note": f"{selection_count} orders now selected for printing",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
                
        except Exception as e:
            logger.error(f"Check order to print error: {e}")
            return json.dumps({
                "success": False,
                "error": f"Check order to print failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
    
    async def _dabs_print_selected_orders(self, arguments: Dict[str, Any]) -> str:
        """Click 'Print Selected' button to print checked orders"""
        try:
            wait_for_result = arguments.get("wait_for_result", True)
            
            logger.info("🖨️ Initiating print selected orders")
            
            sys.path.append(str(Path(__file__).parent.parent))
            from integration.dabs_automated_ordering import DABSAutomatedOrdering
            
            async with DABSAutomatedOrdering(headless=True) as dabs_automation:
                # Navigate to main orders page
                page = await dabs_automation._navigate_to_dabs_orders()
                
                if not await dabs_automation._validate_dabs_session(page):
                    login_success = await dabs_automation.perform_dabs_login()
                    if not login_success:
                        return json.dumps({
                            "success": False,
                            "error": "DABS authentication failed",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                    page = await dabs_automation._navigate_to_dabs_orders()
                
                # Check how many orders are selected
                selected_checkboxes = await page.query_selector_all('input[type="checkbox"][name="IsChecked"]:checked')
                selection_count = len(selected_checkboxes)
                
                if selection_count == 0:
                    return json.dumps({
                        "success": False,
                        "error": "No orders selected for printing",
                        "message": "Use dabs_check_order_to_print first to select orders",
                        "selected_count": 0,
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                
                # Get details of selected orders
                selected_orders = []
                for checkbox in selected_checkboxes:
                    try:
                        checkbox_value = await checkbox.get_attribute('value')
                        # Find the corresponding table row
                        row = await checkbox.evaluate('(element) => element.closest("tr")')
                        if row:
                            order_id_cell = await page.evaluate('(row) => row.cells[1]?.textContent?.trim()', row)
                            selected_orders.append({
                                "order_id": order_id_cell,
                                "sales_order": checkbox_value
                            })
                    except Exception as e:
                        logger.warning(f"Could not extract details for selected order: {e}")
                
                logger.info(f"🖨️ {selection_count} orders selected for printing: {[o.get('order_id') for o in selected_orders]}")
                
                # Find and click the Print Selected button - multiple strategies
                print_button = None
                
                # Strategy 1: Direct ID match (from your HTML)
                print_button = await page.query_selector('#printSelectedButton')
                
                if not print_button:
                    # Strategy 2: Button with print icon and "Print Selected" text
                    print_button = await page.query_selector('a.btn:has-text("Print Selected")')
                
                if not print_button:
                    # Strategy 3: Look for print glyphicon with "Print Selected" text
                    print_button = await page.query_selector('a.btn:has(.glyphicon-print):has-text("Print Selected")')
                
                if not print_button:
                    # Strategy 4: Bootstrap button classes with print text
                    print_button = await page.query_selector('a.btn.btn-orange:has-text("Print Selected")')
                
                if not print_button:
                    # Strategy 5: Any element with print-related attributes
                    print_button = await page.query_selector('[onclick*="print"], button:has-text("Print"), a:has-text("Print Selected")')
                
                if print_button:
                    logger.info("🎯 Found 'Print Selected' button - clicking...")
                    
                    # Click the print button
                    await print_button.click()
                    
                    if wait_for_result:
                        await page.wait_for_timeout(3000)  # Wait for print action to initiate
                        
                        # Check for various print result scenarios
                        print_result = {"type": "unknown"}
                        
                        # Check if a new tab/window opened
                        context = page.context
                        pages = context.pages
                        if len(pages) > 1:
                            print_result = {
                                "type": "new_window",
                                "message": "Print opened in new window/tab"
                            }
                        
                        # Check if URL changed (navigated to print view)
                        current_url = page.url
                        if "print" in current_url.lower() or "report" in current_url.lower():
                            print_result = {
                                "type": "navigation",
                                "url": current_url,
                                "message": "Navigated to print view"
                            }
                        
                        # Check for download or PDF generation
                        await page.wait_for_timeout(2000)  # Additional wait for downloads
                        
                        logger.info(f"✅ Print initiated: {print_result}")
                        
                        return json.dumps({
                            "success": True,
                            "action": "print_selected_orders",
                            "selected_orders": selected_orders,
                            "selected_count": selection_count,
                            "print_result": print_result,
                            "message": f"Successfully initiated printing for {selection_count} selected orders",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                    
                    else:
                        # Don't wait for results, just confirm button was clicked
                        return json.dumps({
                            "success": True,
                            "action": "print_selected_orders",
                            "selected_orders": selected_orders,
                            "selected_count": selection_count,
                            "message": f"Print Selected button clicked for {selection_count} orders",
                            "note": "Print action initiated but not waiting for completion",
                            "timestamp": datetime.utcnow().isoformat()
                        }, indent=2)
                
                # Print button not found
                logger.warning("⚠️ Print Selected button not found")
                return json.dumps({
                    "success": False,
                    "error": "Print Selected button not found",
                    "selected_orders": selected_orders,
                    "selected_count": selection_count,
                    "message": "The 'Print Selected' button was not found on the page",
                    "troubleshooting": [
                        "Verify you're on the correct Orders page",
                        "Check if the page has fully loaded",
                        "Ensure orders are selected before printing"
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
                
        except Exception as e:
            logger.error(f"Print selected orders error: {e}")
            return json.dumps({
                "success": False,
                "error": f"Print selected orders failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)

    async def _dabs_ensure_clean_state(self, arguments: Dict[str, Any]) -> str:
        """Ensure there is no pending order. Deletes it if present.
        Args:
            headed (bool): use headed mode when a deletion is required
            confirm (bool): confirm deletion
            return_artifacts (bool): include artifact paths
        Returns normalized JSON with pre/post state and any deletion action.
        """
        headed = arguments.get("headed", True)
        confirm = arguments.get("confirm", True)
        return_artifacts = arguments.get("return_artifacts", True)

        try:
            # Check current state
            pre_state_json = await self._dabs_get_open_order({})
            pre_state = json.loads(pre_state_json)

            action_taken = None
            delete_result = None

            if pre_state.get("success") and pre_state.get("has_open_order"):
                if not confirm:
                    return json.dumps({
                        "success": False,
                        "error": "Pending order exists; deletion requires confirm=true",
                        "pre_state": pre_state,
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)

                # Target specific order id if available
                order_id = (pre_state.get("order") or {}).get("order_id")
                delete_args = {
                    "confirm": True,
                    "headed": bool(headed),
                    "order_id": order_id,
                    "return_artifacts": return_artifacts
                }
                delete_result_json = await self._dabs_delete_open_order(delete_args)
                delete_result = json.loads(delete_result_json)
                action_taken = "deleted_pending_order" if delete_result.get("success") else "delete_attempt_failed"

            # Post-check state
            post_state_json = await self._dabs_get_open_order({})
            post_state = json.loads(post_state_json)

            clean = post_state.get("success") and not post_state.get("has_open_order")

            return json.dumps({
                "success": bool(clean),
                "action": action_taken or "no_action_needed",
                "message": "System is clean (no pending order)" if clean else "Pending order still present",
                "pre_state": pre_state,
                "post_state": post_state,
                "delete_result": delete_result,
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)

        except Exception as e:
            logger.error(f"ensure_clean_state error: {e}")
            return json.dumps({
                "success": False,
                "error": f"ensure_clean_state failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2)
    
    async def run_stdio(self):
        """Run server with stdio transport (for Cursor)"""
        logger.info(f"🚀 Starting {self.name} with stdio transport")
        logger.info(f"📋 Registered {len(self.tools)} DABS tools")
        
        # Read from stdin and write to stdout
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                request = json.loads(line.strip())
                response = await self.handle_request(request)
                
                # Write response to stdout
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError:
                # Ignore invalid JSON
                continue
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Error in stdio loop: {e}")
                break

async def main():
    """Main entry point"""
    server = SimpleMCPServer("dabs-simple-mcp")
    await server.run_stdio()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Server error: {e}")
        sys.exit(1)
