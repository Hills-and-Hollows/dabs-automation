#!/bin/bash
# DABS Monitoring System Launcher
# Hills & Hollows LLC - Utah Package Agency

echo "🎯 DABS Monitoring System - Hills & Hollows LLC"
echo "================================================"
echo "Monitoring Utah DABS Licensee Ordering System"
echo "Automated testing of 13 MCP tools"
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs
mkdir -p logs/monitoring_results

# Check if virtual environment is active
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment detected - activating..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Virtual environment not found - please create one first"
        exit 1
    fi
fi

# Check required dependencies
echo "🔍 Checking system dependencies..."
python3 -c "import asyncio, json, logging, subprocess, smtplib, pathlib" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Python dependencies available"
else
    echo "❌ Missing Python dependencies"
    exit 1
fi

# Check if requests module is available
python3 -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing requests module..."
    pip install requests
fi

echo ""
echo "🚀 Starting DABS Monitoring System..."
echo "   - Monitoring interval: 5 minutes" 
echo "   - Log file: logs/dabs_monitoring.log"
echo "   - Results: logs/monitoring_results/"
echo "   - Email notifications: shawn@owenent.com"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

# Start the monitoring system
python3 scripts/dabs_monitoring_system.py
