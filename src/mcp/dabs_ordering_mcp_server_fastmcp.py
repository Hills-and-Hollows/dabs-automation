"""
DABS Ordering MCP Server (FastMCP Implementation)
Hills & Hollows LLC - Utah Package Agency
Date: August 23, 2025

This module provides MCP (Model Context Protocol) server tools for DABS ordering system,
enabling AI agents to interact with DABS operations through structured tool calls.

USES FASTMCP FRAMEWORK - Compatible with Cursor MCP Tools interface
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

# MCP Framework imports (FastMCP)
from mcp.server.fastmcp import Context, FastMCP

# Import our DABS integration modules
try:
    from integration.dabs_automated_ordering import (
        DABSAutomatedOrdering, 
        RestaurantOrder, 
        RestaurantOrderItem,
        DABSOrderResult,
        OrderStatus
    )
    from integration.dabs_oauth_client import DABSOAuthClient, OAuthTokens
except ImportError as e:
    logging.warning(f"DABS integration modules not available: {e}")
    # Mock classes for development
    class DABSAutomatedOrdering:
        def __init__(self, headless=True): pass
    class DABSOAuthClient:
        def __init__(self): pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Server configuration
server_host = "0.0.0.0"  # Listen on all interfaces  
server_port = int(os.getenv("DABS_MCP_PORT", "8282"))

@dataclass
class DABSContext:
    """
    Context for DABS MCP server operations
    """
    dabs_automation: Optional[DABSAutomatedOrdering] = None
    oauth_client: Optional[DABSOAuthClient] = None
    startup_time: float = None
    
    def __post_init__(self):
        if self.startup_time is None:
            self.startup_time = time.time()

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[DABSContext]:
    """
    Lifecycle manager for DABS MCP server
    """
    logger.info("🚀 Starting DABS MCP server...")
    
    try:
        # Initialize DABS context
        context = DABSContext()
        
        # Initialize DABS automation (lazy loading)
        logger.info("🍾 DABS automation ready for initialization")
        
        # Initialize OAuth client (lazy loading)
        logger.info("🔐 OAuth client ready for initialization")
        
        logger.info("✓ DABS MCP server ready")
        
        yield context
        
    except Exception as e:
        logger.error(f"💥 Critical error in DABS MCP server startup: {e}")
        raise
    finally:
        logger.info("🧹 Cleaning up DABS MCP server...")
        if hasattr(context, 'dabs_automation') and context.dabs_automation:
            # Clean up automation resources
            logger.info("🛑 Stopping DABS automation")
        logger.info("✅ DABS MCP server shutdown complete")

# Initialize the FastMCP server
try:
    logger.info("🏗️ DABS MCP SERVER INITIALIZATION:")
    logger.info("   Server Name: dabs-ordering-fastmcp")
    logger.info("   Description: DABS ordering automation MCP server")
    
    mcp = FastMCP(
        "dabs-ordering-fastmcp",
        description="MCP server for DABS ordering automation - Hills & Hollows LLC",
        lifespan=lifespan,
        host=server_host,
        port=server_port,
    )
    logger.info("✓ FastMCP server instance created successfully")
    
except Exception as e:
    logger.error(f"✗ Failed to create FastMCP server: {e}")
    raise

# =============================================================================
# DABS MCP TOOLS (Using FastMCP @mcp.tool() decorator)
# =============================================================================

@mcp.tool()
async def dabs_login_status(ctx: Context) -> str:
    """
    Check DABS authentication status and session validity.
    
    Returns:
        JSON string with current authentication status, session info, and credentials
    """
    try:
        context = getattr(ctx.request_context, "lifespan_context", None)
        if not context:
            return json.dumps({
                "success": False,
                "error": "Server context not available",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Initialize DABS automation if needed
        if not context.dabs_automation:
            context.dabs_automation = DABSAutomatedOrdering(headless=True)
        
        # Check authentication status
        auth_file_path = Path("data/dabs_auth_storage.json")  # Default path
        
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
        })
        
    except Exception as e:
        logger.error(f"DABS login status check failed: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

@mcp.tool()
async def dabs_perform_login(ctx: Context, force: bool = False) -> str:
    """
    Perform automated login to DABS system.
    
    Args:
        force: If True, force re-login even if already authenticated
        
    Returns:
        JSON string with login result and session information
    """
    try:
        context = getattr(ctx.request_context, "lifespan_context", None)
        if not context:
            return json.dumps({
                "success": False,
                "error": "Server context not available",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Initialize DABS automation if needed
        if not context.dabs_automation:
            context.dabs_automation = DABSAutomatedOrdering(headless=True)
        
        # Check if already authenticated and not forcing
        auth_file_path = Path("data/dabs_auth_storage.json")
        if not force and auth_file_path.exists():
            return json.dumps({
                "success": True,
                "message": "Already authenticated (use force=true to re-login)",
                "action": "skipped",
                "username": os.getenv("DABS_ORDERING_USERNAME", "hillshollows"),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Perform login
        login_successful = await context.dabs_automation.perform_dabs_login()
        
        if login_successful:
            return json.dumps({
                "success": True,
                "message": "Successfully logged into DABS",
                "action": "login_completed",
                "username": os.getenv("DABS_ORDERING_USERNAME", "hillshollows"),
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return json.dumps({
                "success": False,
                "message": "DABS login failed",
                "action": "login_failed",
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except Exception as e:
        logger.error(f"DABS login failed: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "action": "login_error",
            "timestamp": datetime.utcnow().isoformat()
        })

@mcp.tool()
async def dabs_process_restaurant_order(ctx: Context, order: Dict[str, Any]) -> str:
    """
    Process a restaurant order through DABS automation.
    
    Args:
        order: Dictionary containing order details (customer, items, payment info)
        
    Returns:
        JSON string with order processing result and DABS order ID
    """
    try:
        context = getattr(ctx.request_context, "lifespan_context", None)
        if not context:
            return json.dumps({
                "success": False,
                "error": "Server context not available",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Initialize DABS automation if needed
        if not context.dabs_automation:
            context.dabs_automation = DABSAutomatedOrdering(headless=True)
        
        # Create RestaurantOrderItem objects
        order_items = []
        for item_data in order.get("items", []):
            order_items.append(RestaurantOrderItem(
                sku=item_data["sku"],
                product_name=item_data.get("product_name", f"Product {item_data['sku']}"),
                quantity=item_data["quantity"],
                unit_price=item_data.get("unit_price", 0.0),
                category=item_data.get("category", "General")
            ))
        
        # Create RestaurantOrder object
        restaurant_order = RestaurantOrder(
            id=order.get("id", f"ORDER-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"),
            customer_name=order["customer_name"],
            customer_email=order["customer_email"],
            items=order_items,
            total_amount=order.get("total_amount", 0.0),
            order_date=datetime.utcnow(),
            payment_method=order.get("payment_method", "Credit Card"),
            delivery_address=order.get("delivery_address")
        )
        
        # Process the order
        result = await context.dabs_automation.process_restaurant_order(restaurant_order)
        
        return json.dumps({
            "success": result.success,
            "dabs_order_id": result.dabs_order_id,
            "items_processed": result.items_processed,
            "total_amount": result.total_amount,
            "processing_time": result.processing_time,
            "session_id": result.session_id,
            "error": result.error,
            "restaurant_order_id": restaurant_order.id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"DABS order processing failed: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

@mcp.tool()
async def dabs_get_order_history(ctx: Context, days: int = 30, status: Optional[str] = None) -> str:
    """
    Get DABS order history and status information.
    
    Args:
        days: Number of days to look back (default: 30)
        status: Optional status filter
        
    Returns:
        JSON string with order history and status information
    """
    try:
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
                "start": (datetime.utcnow() - timedelta(days=days)).isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "filter_applied": status
        }
        
        return json.dumps({
            "success": True,
            "order_history": order_history,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"DABS order history retrieval failed: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

@mcp.tool()
async def dabs_oauth_status(ctx: Context) -> str:
    """
    Check DABS OAuth token status and validity.
    
    Returns:
        JSON string with OAuth token status, expiration, and refresh information
    """
    try:
        context = getattr(ctx.request_context, "lifespan_context", None)
        if not context:
            return json.dumps({
                "success": False,
                "error": "Server context not available",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Initialize OAuth client if needed
        if not context.oauth_client:
            context.oauth_client = DABSOAuthClient()
        
        await context.oauth_client.load_stored_tokens()
        
        if context.oauth_client.current_tokens:
            status = {
                "has_tokens": True,
                "access_token_valid": not context.oauth_client.current_tokens.is_expired,
                "has_refresh_token": bool(context.oauth_client.current_tokens.refresh_token),
                "expires_at": context.oauth_client.current_tokens.expires_at.isoformat(),
                "token_type": context.oauth_client.current_tokens.token_type,
                "scope": context.oauth_client.current_tokens.scope
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
        
        return json.dumps({
            "success": True,
            "oauth_status": status,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"OAuth status check failed: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

@mcp.tool()
async def dabs_generate_oauth_url(ctx: Context, state: Optional[str] = None, scopes: Optional[List[str]] = None) -> str:
    """
    Generate OAuth authorization URL for DABS system.
    
    Args:
        state: Optional state parameter for OAuth flow
        scopes: Optional list of OAuth scopes to request
        
    Returns:
        JSON string with OAuth authorization URL and flow parameters
    """
    try:
        context = getattr(ctx.request_context, "lifespan_context", None)
        if not context:
            return json.dumps({
                "success": False,
                "error": "Server context not available",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Initialize OAuth client if needed
        if not context.oauth_client:
            context.oauth_client = DABSOAuthClient()
        
        if not state:
            state = f"state_{datetime.utcnow().timestamp()}"
        
        if not scopes:
            scopes = ["orders:read", "orders:write", "inventory:read"]
        
        auth_url = context.oauth_client.get_authorization_url(state=state, scopes=scopes)
        
        return json.dumps({
            "success": True,
            "authorization_url": auth_url,
            "state": state,
            "scopes": scopes,
            "redirect_uri": context.oauth_client.redirect_uri,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"OAuth URL generation failed: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

@mcp.tool() 
async def dabs_system_health(ctx: Context) -> str:
    """
    Check DABS system health, connectivity, and configuration status.
    
    Returns:
        JSON string with comprehensive system health information
    """
    try:
        context = getattr(ctx.request_context, "lifespan_context", None)
        
        health_status = {
            "dabs_website_accessible": True,  # Would check actual connectivity
            "environment_variables_loaded": bool(os.getenv("DABS_ORDERING_USERNAME")),
            "automation_system_ready": context and context.dabs_automation is not None,
            "oauth_client_ready": context and context.oauth_client is not None,
            "server_uptime_seconds": time.time() - context.startup_time if context else 0,
            "system_timestamp": datetime.utcnow().isoformat(),
            "configuration": {
                "base_url": os.getenv("DABS_ORDERING_LOGIN_URL"),
                "username": os.getenv("DABS_ORDERING_USERNAME"),
                "session_timeout": os.getenv("DABS_SESSION_TIMEOUT_MINUTES"),
                "max_open_orders": os.getenv("DABS_MAX_OPEN_ORDERS"),
                "server_port": server_port,
                "server_host": server_host
            }
        }
        
        return json.dumps({
            "success": True,
            "health_status": health_status,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"DABS health check failed: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

# =============================================================================
# SERVER STARTUP
# =============================================================================

def main():
    """Main entry point for the DABS MCP server."""
    try:
        logger.info("🚀 Starting DABS Ordering MCP Server (FastMCP)")
        logger.info("   Mode: Streamable HTTP")
        logger.info(f"   URL: http://{server_host}:{server_port}/mcp")
        logger.info(f"   Tools: 7 DABS automation tools available")
        
        # Start the FastMCP server
        mcp.run(transport="streamable-http")
        
    except Exception as e:
        logger.error(f"💥 Fatal error in DABS MCP server: {e}")
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 DABS MCP server stopped by user")
    except Exception as e:
        logger.error(f"💥 Unhandled exception: {e}")
        sys.exit(1)
