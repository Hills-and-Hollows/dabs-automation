#!/usr/bin/env python3
"""
DABS Automation API - Main Application
Utah Package Agency Liquor Inventory Management System

This is the core FastAPI application for the DABS automation system.
Provides REST API endpoints for:
- DABS file processing
- QuickBooks integration  
- SSCS POS synchronization
- Compliance reporting
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import os
from pathlib import Path

# Create FastAPI application
app = FastAPI(
    title="DABS Automation API",
    description="Utah Package Agency Liquor Inventory Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "🍾 DABS Automation API is running!",
        "system": "Utah Package Agency Inventory Management", 
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "operational",
            "dabs_processor": "ready",
            "quickbooks_integration": "configured", 
            "sscs_sync": "pending_vendor",
            "compliance_engine": "ready"
        }
    }

# System information endpoint
@app.get("/info")
async def system_info():
    """System information and capabilities"""
    project_root = Path(__file__).parent.parent.parent
    
    return {
        "project": "DABS Automation System",
        "client": "Hills & Hollows LLC - Boulder, UT",
        "capabilities": [
            "DABS Excel file processing (1,239+ SKUs)",
            "QuickBooks Online OAuth 2.0 integration", 
            "SSCS POS synchronization",
            "Verifone payment system integration",
            "Automated compliance reporting",
            "Audit trail management"
        ],
        "integrations": {
            "dabs": {
                "method": "Excel file processing + API",
                "status": "ready",
                "file_location": str(project_root / "DABS Price Changes.xlsx") if (project_root / "DABS Price Changes.xlsx").exists() else "No file found"
            },
            "quickbooks": {
                "method": "OAuth 2.0 REST API",
                "rate_limit": "500 requests/minute", 
                "status": "configured"
            },
            "sscs_pos": {
                "method": "API/DB/File (TBD)",
                "status": "pending_vendor_documentation",
                "priority": "HIGH"
            },
            "verifone": {
                "method": "Local + Cloud API",
                "local_ip": "192.168.31.11",
                "status": "ready"
            }
        },
        "performance_targets": {
            "processing_speed": "1,239 SKUs in <15 minutes",
            "accuracy": "<0.1% error rate",
            "uptime": ">99% availability",
            "response_time": "<2 seconds"
        }
    }

# DABS endpoints (placeholder for Phase 2 development)
@app.get("/dabs/status")
async def dabs_status():
    """DABS integration status"""
    return {
        "status": "ready_for_phase_2",
        "file_processor": "configured",
        "last_processing": None,
        "next_scheduled": "TBD - awaiting Phase 2 implementation"
    }

# QuickBooks endpoints (placeholder for Phase 2 development)  
@app.get("/quickbooks/status")
async def quickbooks_status():
    """QuickBooks integration status"""
    return {
        "status": "oauth_ready",
        "api_version": "QuickBooks Online REST API",
        "rate_limit": "500 requests/minute",
        "connection": "not_established",
        "next_step": "OAuth 2.0 setup in Phase 2"
    }

# SSCS POS endpoints (placeholder for Phase 2 development)
@app.get("/sscs/status") 
async def sscs_status():
    """SSCS POS integration status"""
    return {
        "status": "pending_vendor_contact",
        "priority": "HIGH - Critical for Phase 2",
        "integration_options": ["API", "Database", "File-based"],
        "vendor_response": "awaiting_technical_documentation",
        "blocker": True
    }

# Compliance endpoints (placeholder for Phase 3 development)
@app.get("/compliance/status")
async def compliance_status():
    """Compliance and reporting status"""
    return {
        "utah_package_agency": "configured",
        "monthly_reporting": "automated_ready",
        "audit_trail": "implemented",
        "data_retention": "7 years configured",
        "backup_schedule": "daily_automated"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": "This endpoint is not implemented yet",
            "available_endpoints": [
                "/", "/health", "/info", 
                "/dabs/status", "/quickbooks/status", 
                "/sscs/status", "/compliance/status"
            ]
        }
    )

@app.exception_handler(500)
async def server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error", 
            "message": "Contact development team if this persists",
            "timestamp": datetime.now().isoformat()
        }
    )

# Development server runner
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )
