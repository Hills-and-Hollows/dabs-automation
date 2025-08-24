#!/bin/bash

# DABS Archon MCP Server Quick Start Script
# Integrates Archon with existing DABS workspace

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ARCHON_DIR="archon-mcp"
DABS_ROOT="$(pwd)"

echo -e "${BLUE}🏗️  DABS Archon MCP Server Quick Start${NC}"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "PROJECT_SUMMARY.md" ] || [ ! -d "src" ]; then
    echo -e "${RED}❌ Error: This script must be run from the DABS workspace root${NC}"
    echo "   Expected files: PROJECT_SUMMARY.md, src/ directory"
    exit 1
fi

# Check if Archon directory exists
if [ ! -d "$ARCHON_DIR" ]; then
    echo -e "${RED}❌ Error: Archon directory not found: $ARCHON_DIR${NC}"
    echo "   Please run the Archon setup first"
    exit 1
fi

echo -e "${GREEN}✅ DABS workspace detected${NC}"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Check for port conflicts
echo -e "\n${YELLOW}🔌 Checking port availability...${NC}"
PORTS=(3837 8281 8151 8152)
PORT_CONFLICTS=false

for port in "${PORTS[@]}"; do
    if check_port $port; then
        echo -e "${RED}⚠️  Port $port is already in use${NC}"
        PORT_CONFLICTS=true
    else
        echo -e "${GREEN}✅ Port $port is available${NC}"
    fi
done

if [ "$PORT_CONFLICTS" = true ]; then
    echo -e "\n${YELLOW}💡 Tip: Stop conflicting services or modify ports in archon-mcp/.env${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if .env file is configured
echo -e "\n${YELLOW}🔧 Checking Archon configuration...${NC}"
if [ ! -f "$ARCHON_DIR/.env" ]; then
    echo -e "${RED}❌ .env file not found in $ARCHON_DIR${NC}"
    echo "   Please run: cd $ARCHON_DIR && python3 setup_dabs_archon.py"
    exit 1
fi

# Check if Supabase is configured
if ! grep -q "SUPABASE_URL=https://" "$ARCHON_DIR/.env" 2>/dev/null; then
    echo -e "${RED}❌ Supabase not configured in .env file${NC}"
    echo "   Please run: cd $ARCHON_DIR && python3 setup_dabs_archon.py"
    exit 1
fi

echo -e "${GREEN}✅ Archon configuration found${NC}"

# Start Archon services
echo -e "\n${YELLOW}🚀 Starting Archon services...${NC}"
cd "$ARCHON_DIR"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "   Please start Docker Desktop and try again"
    exit 1
fi

# Start services with docker-compose
echo -e "${BLUE}📦 Building and starting containers...${NC}"
docker-compose up --build -d

# Wait for services to start
echo -e "${YELLOW}⏳ Waiting for services to start (30 seconds)...${NC}"
sleep 30

# Check service health
echo -e "\n${YELLOW}🔍 Checking service health...${NC}"
SERVICES=(
    "Archon UI:http://localhost:3837"
    "Archon Server:http://localhost:8281/health"
    "Archon MCP:http://localhost:8151"
)

ALL_HEALTHY=true
for service in "${SERVICES[@]}"; do
    IFS=':' read -r name url <<< "$service"
    if curl -s -f "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is running${NC}"
    else
        echo -e "${RED}❌ $name is not responding${NC}"
        ALL_HEALTHY=false
    fi
done

# Return to DABS root
cd "$DABS_ROOT"

# Display results
echo -e "\n=================================================="
if [ "$ALL_HEALTHY" = true ]; then
    echo -e "${GREEN}🎉 Archon MCP Server is running successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  Some services may still be starting up${NC}"
    echo -e "   Please wait a few more minutes and check manually"
fi

echo -e "\n${BLUE}📊 Service URLs:${NC}"
echo -e "   🖥️  Archon UI: ${GREEN}http://localhost:3837${NC}"
echo -e "   🔧 Archon Server: ${GREEN}http://localhost:8281${NC}"
echo -e "   🤖 Archon MCP: ${GREEN}http://localhost:8151${NC}"
echo -e "   ⚡ Archon Agents: ${GREEN}http://localhost:8152${NC}"

echo -e "\n${BLUE}📋 Next Steps:${NC}"
echo -e "1. 🌐 Open Archon UI: ${GREEN}http://localhost:3837${NC}"
echo -e "2. ⚙️  Configure API keys in Settings"
echo -e "3. 📚 Upload DABS documentation:"
echo -e "   • docs/FUNCTIONAL_REQUIREMENTS.md"
echo -e "   • docs/TECHNICAL_ARCHITECTURE.md"
echo -e "   • docs/ACCEPTANCE_CRITERIA.md"
echo -e "   • research-paper-qbo-mcp.md"
echo -e "4. 🤖 Configure AI coding assistant:"
echo -e "   • MCP Server URL: ${GREEN}http://localhost:8151${NC}"
echo -e "   • Transport: SSE"

echo -e "\n${BLUE}🛠️  Management Commands:${NC}"
echo -e "   Stop services: ${YELLOW}cd $ARCHON_DIR && docker-compose down${NC}"
echo -e "   View logs: ${YELLOW}cd $ARCHON_DIR && docker-compose logs -f${NC}"
echo -e "   Restart: ${YELLOW}cd $ARCHON_DIR && docker-compose restart${NC}"

echo -e "\n${BLUE}📖 Documentation:${NC}"
echo -e "   Setup Guide: ${GREEN}$ARCHON_DIR/DABS_SETUP_GUIDE.md${NC}"
echo -e "   Integration Config: ${GREEN}$ARCHON_DIR/dabs_integration_config.json${NC}"

echo -e "\n${GREEN}✨ Happy coding with AI assistance!${NC}"
