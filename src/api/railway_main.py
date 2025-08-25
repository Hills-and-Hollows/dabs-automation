#!/usr/bin/env python3
"""
Railway-Optimized DABS API - Hills & Hollows LLC
Minimal FastAPI app for Railway deployment testing

This is a simplified version to ensure Railway deployment succeeds.
Once deployed, we can gradually add complexity.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import os

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="DABS Automation System",
    description="Utah Package Agency Liquor Inventory Management - Hills & Hollows LLC",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "project": "DABS Automation System",
        "client": "Hills & Hollows LLC - Boulder, UT",
        "description": "Utah Package Agency Liquor Inventory Management",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENV", "development"),
        "port": os.getenv("PORT", "8000")
    }

@app.get("/health")
async def health_check():
    """Lightweight health check endpoint for Railway deployment"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENV", "development"),
        "port": os.getenv("PORT", "8000")
    }

@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "api": "DABS Automation System",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "root": "/",
            "health": "/health",
            "status": "/api/status"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
