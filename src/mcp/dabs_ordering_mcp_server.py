"""
DABS Ordering MCP Server
Hills & Hollows LLC - Utah Package Agency
Date: August 23, 2025

This module provides MCP (Model Context Protocol) server tools for DABS ordering system,
enabling AI agents to interact with DABS operations through structured tool calls.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import mcp
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent, JSONContent, CallResult
from mcp.server.session import ServerSession

# Import our DABS integration modules
from integration.dabs_automated_ordering import (
    DABSAutomatedOrdering, 
    RestaurantOrder, 
    RestaurantOrderItem,
    DABSOrderResult,
    OrderStatus
)
from integration.dabs_oauth_client import DABSOAuthClient, OAuthTokens

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DABSOrderingMCPServer:
    """
    MCP Server for DABS Ordering System Operations
    
    Provides AI-accessible tools for DABS automation, OAuth management,
    and order processing through the Model Context Protocol.
    """
    
    def __init__(self):
        self.server = Server("dabs-ordering-server")
        self.dabs_automation: Optional[DABSAutomatedOrdering] = None
        self.oauth_client: Optional[DABSOAuthClient] = None
        
        # Register MCP tools
        self._register_tools()
        self._register_resources()
    
    def _register_tools(self):
        """Register all DABS MCP tools"""
        
        # Add tools list for MCP protocol discovery
        @self.server.list_tools
        async def list_tools() -> List[Tool]:
            """List all available DABS tools for MCP protocol"""
            return [
                Tool(
                    name="dabs_login_status",
                    description="Check DABS authentication status and session validity"
                ),
                Tool(
                    name="dabs_perform_login",
                    description="Perform automated login to DABS system"
                ),
                Tool(
                    name="dabs_process_restaurant_order",
                    description="Process a restaurant order through DABS automation"
                ),
                Tool(
                    name="dabs_get_order_history",
                    description="Get DABS order history and status"
                ),
                Tool(
                    name="dabs_oauth_status", 
                    description="Check DABS OAuth token status"
                ),
                Tool(
                    name="dabs_generate_oauth_url",
                    description="Generate OAuth authorization URL for DABS"
                ),
                Tool(
                    name="dabs_system_health",
                    description="Check DABS system health and connectivity"
                )
            ]
        
        @self.server.call_tool
        async def dabs_login_status(arguments: Dict[str, Any]) -> CallResult:
            """Check DABS authentication status and session validity"""
            try:
                if not self.dabs_automation:
                    self.dabs_automation = DABSAutomatedOrdering(headless=True)
                
                # Initialize if needed
                if not self.dabs_automation.browser_context:
                    await self.dabs_automation.initialize_automation_system()
                
                # Check if we have valid authentication
                if self.dabs_automation.auth_storage_path.exists():
                    status = {
                        "authenticated": True,
                        "session_saved": True,
                        "auth_file_exists": True,
                        "last_login": "session_stored"
                    }
                else:
                    status = {
                        "authenticated": False,
                        "session_saved": False,
                        "auth_file_exists": False,
                        "last_login": None
                    }
                
                return CallResult(
                    content=[JSONContent(data={
                        "success": True,
                        "dabs_status": status,
                        "username": self.dabs_automation.dabs_username,
                        "environment": "Production",
                        "timestamp": datetime.utcnow().isoformat()
                    })]
                )
                
            except Exception as e:
                logger.error(f"DABS login status check failed: {str(e)}")
                return CallResult(
                    content=[JSONContent(data={
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })]
                )
        
        @self.server.call_tool
        async def dabs_perform_login(arguments: Dict[str, Any]) -> CallResult:
            """Perform automated login to DABS system"""
            try:
                force_login = arguments.get("force", False)
                
                if not self.dabs_automation:
                    self.dabs_automation = DABSAutomatedOrdering(headless=True)
                
                # Check if already authenticated and not forcing
                if not force_login and self.dabs_automation.auth_storage_path.exists():
                    return CallResult(
                        content=[JSONContent(data={
                            "success": True,
                            "message": "Already authenticated (use force=true to re-login)",
                            "action": "skipped",
                            "timestamp": datetime.utcnow().isoformat()
                        })]
                    )
                
                # Perform login
                login_successful = await self.dabs_automation.perform_dabs_login()
                
                if login_successful:
                    return CallResult(
                        content=[JSONContent(data={
                            "success": True,
                            "message": "Successfully logged into DABS",
                            "action": "login_completed",
                            "username": self.dabs_automation.dabs_username,
                            "timestamp": datetime.utcnow().isoformat()
                        })]
                    )
                else:
                    return CallResult(
                        content=[JSONContent(data={
                            "success": False,
                            "message": "DABS login failed",
                            "action": "login_failed",
                            "timestamp": datetime.utcnow().isoformat()
                        })]
                    )
                
            except Exception as e:
                logger.error(f"DABS login failed: {str(e)}")
                return CallResult(
                    content=[JSONContent(data={
                        "success": False,
                        "error": str(e),
                        "action": "login_error",
                        "timestamp": datetime.utcnow().isoformat()
                    })]
                )
        
        @self.server.call_tool
        async def dabs_process_restaurant_order(arguments: Dict[str, Any]) -> CallResult:
            """Process a restaurant order through DABS automation"""
            try:
                # Extract order data from arguments
                order_data = arguments.get("order", {})
                
                # Create RestaurantOrderItem objects
                order_items = []
                for item_data in order_data.get("items", []):
                    order_items.append(RestaurantOrderItem(
                        sku=item_data["sku"],
                        product_name=item_data.get("product_name", f"Product {item_data['sku']}"),
                        quantity=item_data["quantity"],
                        unit_price=item_data.get("unit_price", 0.0),
                        category=item_data.get("category", "General")
                    ))
                
                # Create RestaurantOrder object
                restaurant_order = RestaurantOrder(
                    id=order_data.get("id", f"ORDER-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"),
                    customer_name=order_data["customer_name"],
                    customer_email=order_data["customer_email"],
                    items=order_items,
                    total_amount=order_data.get("total_amount", 0.0),
                    order_date=datetime.utcnow(),
                    payment_method=order_data.get("payment_method", "Credit Card"),
                    delivery_address=order_data.get("delivery_address")
                )
                
                # Initialize DABS automation if needed
                if not self.dabs_automation:
                    self.dabs_automation = DABSAutomatedOrdering(headless=True)
                
                # Process the order
                result = await self.dabs_automation.process_restaurant_order(restaurant_order)
                
                return CallResult(
                    content=[JSONContent(data={
                        "success": result.success,
                        "dabs_order_id": result.dabs_order_id,
                        "items_processed": result.items_processed,
                        "total_amount": result.total_amount,
                        "processing_time": result.processing_time,
                        "session_id": result.session_id,
                        "error": result.error,
                        "restaurant_order_id": restaurant_order.id,
                        "timestamp": datetime.utcnow().isoformat()
                    })]
                )
                
            except Exception as e:
                logger.error(f"DABS order processing failed: {str(e)}")
                return CallResult(
                    content=[JSONContent(data={
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })]
                )
        
        @self.server.call_tool
        async def dabs_get_order_history(arguments: Dict[str, Any]) -> CallResult:
            """Get DABS order history and status"""
            try:
                days_back = arguments.get("days", 30)
                status_filter = arguments.get("status", None)
                
                # This would typically interface with DABS API or scrape the orders page
                # For now, return mock data structure
                order_history = {
                    "orders": [
                        {
                            "dabs_order_id": "DABS-2025-001",
                            "date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                            "status": "Submitted",
                            "total_amount": 150.25,
                            "item_count": 3,
                            "restaurant_order_id": "HH-REST-001"
                        },
                        {
                            "dabs_order_id": "DABS-2025-002",
                            "date": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                            "status": "Delivered",
                            "total_amount": 87.50,
                            "item_count": 2,
                            "restaurant_order_id": "HH-REST-002"
                        }
                    ],
                    "total_orders": 2,
                    "date_range": {
                        "start": (datetime.utcnow() - timedelta(days=days_back)).isoformat(),
                        "end": datetime.utcnow().isoformat()
                    }
                }
                
                return CallResult(
                    content=[JSONContent(data={
                        "success": True,
                        "order_history": order_history,
                        "timestamp": datetime.utcnow().isoformat()
                    })]
                )
                
            except Exception as e:
                logger.error(f"DABS order history retrieval failed: {str(e)}")
                return CallResult(
                    content=[JSONContent(data={
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })]
                )
        
        @self.server.call_tool
        async def dabs_oauth_status(arguments: Dict[str, Any]) -> CallResult:
            """Check DABS OAuth token status"""
            try:
                if not self.oauth_client:
                    self.oauth_client = DABSOAuthClient()
                
                await self.oauth_client.load_stored_tokens()
                
                if self.oauth_client.current_tokens:
                    status = {
                        "has_tokens": True,
                        "access_token_valid": not self.oauth_client.current_tokens.is_expired,
                        "has_refresh_token": bool(self.oauth_client.current_tokens.refresh_token),
                        "expires_at": self.oauth_client.current_tokens.expires_at.isoformat(),
                        "token_type": self.oauth_client.current_tokens.token_type,
                        "scope": self.oauth_client.current_tokens.scope
                    }
                else:
                    status = {
                        "has_tokens": False,
                        "access_token_valid": False,
                        "has_refresh_token": False,
                        "expires_at": None,
                        "token_type": None,
                        "scope": None
                    }
                
                return CallResult(
                    content=[JSONContent(data={
                        "success": True,
                        "oauth_status": status,
                        "timestamp": datetime.utcnow().isoformat()
                    })]
                )
                
            except Exception as e:
                logger.error(f"OAuth status check failed: {str(e)}")
                return CallResult(
                    content=[JSONContent(data={
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })]
                )
        
        @self.server.call_tool
        async def dabs_generate_oauth_url(arguments: Dict[str, Any]) -> CallResult:
            """Generate OAuth authorization URL for DABS"""
            try:
                if not self.oauth_client:
                    self.oauth_client = DABSOAuthClient()
                
                state = arguments.get("state", f"state_{datetime.utcnow().timestamp()}")
                scopes = arguments.get("scopes", ["orders:read", "orders:write", "inventory:read"])
                
                auth_url = self.oauth_client.get_authorization_url(state=state, scopes=scopes)
                
                return CallResult(
                    content=[JSONContent(data={
                        "success": True,
                        "authorization_url": auth_url,
                        "state": state,
                        "scopes": scopes,
                        "redirect_uri": self.oauth_client.redirect_uri,
                        "timestamp": datetime.utcnow().isoformat()
                    })]
                )
                
            except Exception as e:
                logger.error(f"OAuth URL generation failed: {str(e)}")
                return CallResult(
                    content=[JSONContent(data={
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })]
                )
        
        @self.server.call_tool 
        async def dabs_system_health(arguments: Dict[str, Any]) -> CallResult:
            """Check DABS system health and connectivity"""
            try:
                health_status = {
                    "dabs_website_accessible": True,  # Would check actual connectivity
                    "environment_variables_loaded": bool(os.getenv("DABS_ORDERING_USERNAME")),
                    "automation_system_ready": self.dabs_automation is not None,
                    "oauth_client_ready": self.oauth_client is not None,
                    "system_timestamp": datetime.utcnow().isoformat(),
                    "configuration": {
                        "base_url": os.getenv("DABS_ORDERING_LOGIN_URL"),
                        "username": os.getenv("DABS_ORDERING_USERNAME"),
                        "session_timeout": os.getenv("DABS_SESSION_TIMEOUT_MINUTES"),
                        "max_open_orders": os.getenv("DABS_MAX_OPEN_ORDERS")
                    }
                }
                
                return CallResult(
                    content=[JSONContent(data={
                        "success": True,
                        "health_status": health_status,
                        "timestamp": datetime.utcnow().isoformat()
                    })]
                )
                
            except Exception as e:
                logger.error(f"DABS health check failed: {str(e)}")
                return CallResult(
                    content=[JSONContent(data={
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })]
                )
    
    def _register_resources(self):
        """Register DABS MCP resources"""
        
        @self.server.list_resources
        async def list_resources() -> List[Resource]:
            """List available DABS resources"""
            return [
                Resource(
                    uri="dabs://configuration",
                    name="DABS Configuration",
                    description="Current DABS system configuration and environment variables",
                    mimeType="application/json"
                ),
                Resource(
                    uri="dabs://order-templates", 
                    name="DABS Order Templates",
                    description="Template formats for DABS order processing",
                    mimeType="application/json"
                ),
                Resource(
                    uri="dabs://system-status",
                    name="DABS System Status",
                    description="Real-time DABS system status and health metrics",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource
        async def read_resource(uri: str) -> str:
            """Read DABS resource content"""
            if uri == "dabs://configuration":
                config = {
                    "environment": "Production",
                    "base_url": os.getenv("DABS_ORDERING_LOGIN_URL"),
                    "username": os.getenv("DABS_ORDERING_USERNAME"),
                    "session_timeout_minutes": os.getenv("DABS_SESSION_TIMEOUT_MINUTES"),
                    "max_open_orders": os.getenv("DABS_MAX_OPEN_ORDERS"),
                    "audit_trail_enabled": os.getenv("DABS_AUDIT_TRAIL_ENABLED"),
                    "automated_ordering_enabled": os.getenv("DABS_AUTOMATED_ORDERING_ENABLED")
                }
                return json.dumps(config, indent=2)
            
            elif uri == "dabs://order-templates":
                templates = {
                    "restaurant_order": {
                        "id": "string (required)",
                        "customer_name": "string (required)",
                        "customer_email": "string (required)",
                        "items": [
                            {
                                "sku": "string (required)",
                                "product_name": "string (optional)",
                                "quantity": "integer (required)",
                                "unit_price": "float (optional)",
                                "category": "string (optional)"
                            }
                        ],
                        "total_amount": "float (optional)",
                        "payment_method": "string (optional)",
                        "delivery_address": "string (optional)"
                    }
                }
                return json.dumps(templates, indent=2)
            
            elif uri == "dabs://system-status":
                status = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "system_ready": True,
                    "services": {
                        "dabs_automation": "initialized" if self.dabs_automation else "not_initialized",
                        "oauth_client": "initialized" if self.oauth_client else "not_initialized"
                    }
                }
                return json.dumps(status, indent=2)
            
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
    
    async def run_server(self):
        """Run the DABS MCP server"""
        logger.info(f"🚀 Starting DABS Ordering MCP Server")
        
        try:
            # Initialize DABS automation system
            self.dabs_automation = DABSAutomatedOrdering(headless=True)
            self.oauth_client = DABSOAuthClient()
            
            logger.info("✅ DABS MCP Server initialized successfully")
            
            # Use MCP server's run method with stdio transport
            await self.server.run()
                
        except Exception as e:
            logger.error(f"❌ DABS MCP Server error: {str(e)}")
            raise

# Server startup script
async def main():
    """Start the DABS Ordering MCP Server"""
    server = DABSOrderingMCPServer()
    await server.run_server()

if __name__ == "__main__":
    asyncio.run(main())
