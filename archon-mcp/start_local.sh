#!/bin/bash
echo "🚀 Starting DABS Archon Local Development Server..."
echo "📍 Server: http://localhost:8151"
echo "🔧 MCP endpoint: http://localhost:8151/mcp/sse"
echo "📊 Health: http://localhost:8151/health"
echo ""
"/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/archon-mcp/venv/bin/python" local_server.py
