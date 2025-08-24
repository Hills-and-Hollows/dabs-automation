#!/bin/bash

# DABS Archon Advanced MCP Server Startup Script
# This script starts the advanced local development MCP server for DABS project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting DABS Archon Advanced MCP Server...${NC}"
echo "=================================================="

# Change to the archon-mcp directory
cd "$(dirname "$0")/archon-mcp" || exit 1

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}📦 Upgrading pip...${NC}"
python -m pip install --upgrade pip

# Check if required packages are installed
echo -e "${YELLOW}📦 Installing/checking required packages...${NC}"
pip install fastapi uvicorn python-multipart pydantic

# Set environment variables for local development
export DABS_ENV=local
export DABS_DEBUG=true
export ARCHON_MODE=advanced

# Start the advanced server
echo ""
echo -e "${GREEN}✨ DABS Archon Advanced MCP Server Starting...${NC}"
echo "=================================================="
echo -e "${BLUE}📍 Server:${NC} http://localhost:8151"
echo -e "${BLUE}🔧 MCP endpoint:${NC} http://localhost:8151/mcp/sse"
echo -e "${BLUE}📊 Health check:${NC} http://localhost:8151/health"
echo ""
echo -e "${GREEN}✨ Advanced Features:${NC}"
echo "   • Advanced Project Management"
echo "   • Task Management with Status Tracking"
echo "   • RAG Knowledge Base Search"
echo "   • Document Management"
echo "   • DABS Integration Support"
echo ""
echo -e "${YELLOW}🔧 Configure in Cursor:${NC}"
echo "   Command: curl -N -H \"Accept: text/event-stream\" http://localhost:8151/mcp/sse"
echo ""

python advanced_local_server.py
