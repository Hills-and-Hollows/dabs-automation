#!/bin/bash
# Quick Archon services start
cd archon-mcp && docker-compose up -d
echo "⏳ Waiting for services to start..."
sleep 10
cd .. && python3 .cursor/enforce-archon.py
