#!/bin/bash
# DABS Server Monitoring Script
# Usage: ./monitor_servers.sh [interval_seconds]

INTERVAL=${1:-5}  # Default 5 seconds
echo "🍾 DABS Server Monitor - Refreshing every ${INTERVAL} seconds"
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "======================================="
    echo "🍾 DABS AUTOMATION - SERVER MONITOR"
    echo "======================================="
    echo "📅 $(date)"
    echo ""
    
    # Process Information
    echo "📊 PROCESS STATUS:"
    echo "-------------------"
    ps aux | grep -E "(uvicorn|streamlit)" | grep -v grep | while read line; do
        pid=$(echo "$line" | awk '{print $2}')
        cpu=$(echo "$line" | awk '{print $3}')
        mem=$(echo "$line" | awk '{print $4}')
        cmd=$(echo "$line" | awk '{print $11 " " $12 " " $13}')
        
        if [[ $cmd == *"uvicorn"* ]]; then
            echo "🔥 FastAPI Server - PID: $pid, CPU: ${cpu}%, MEM: ${mem}%"
        elif [[ $cmd == *"streamlit"* ]]; then
            echo "📊 Streamlit Dashboard - PID: $pid, CPU: ${cpu}%, MEM: ${mem}%"
        fi
    done
    echo ""
    
    # API Health Check
    echo "❤️  API HEALTH:"
    echo "---------------"
    api_response=$(curl -s --max-time 3 http://localhost:8001/health 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✅ FastAPI Server: HEALTHY"
        echo "   Status: $(echo $api_response | grep -o '"status":"[^"]*' | cut -d'"' -f4)"
        echo "   Timestamp: $(echo $api_response | grep -o '"timestamp":"[^"]*' | cut -d'"' -f4 | cut -d'T' -f2 | cut -d'.' -f1)"
    else
        echo "❌ FastAPI Server: UNREACHABLE"
    fi
    
    # Streamlit Check
    streamlit_response=$(curl -s --max-time 3 http://localhost:8502/ 2>/dev/null | head -1)
    if [ $? -eq 0 ] && [[ $streamlit_response == *"doctype html"* ]]; then
        echo "✅ Streamlit Dashboard: HEALTHY"
    else
        echo "❌ Streamlit Dashboard: UNREACHABLE"
    fi
    echo ""
    
    # Port Information
    echo "🔌 PORT STATUS:"
    echo "---------------"
    netstat -an | grep -E ":800[12]" | while read line; do
        if [[ $line == *":8001"* ]]; then
            echo "🔥 Port 8001 (FastAPI): $line"
        elif [[ $line == *":8002"* ]] || [[ $line == *":8502"* ]]; then
            echo "📊 Port 8502 (Streamlit): $line" 
        fi
    done
    echo ""
    
    # System Resources
    echo "💻 SYSTEM RESOURCES:"
    echo "--------------------"
    echo "🖥️  Memory Usage: $(vm_stat | grep 'free' | awk '{print $3}' | sed 's/.$//')k free"
    echo "⚡ Load Average: $(uptime | awk -F'load averages: ' '{print $2}')"
    echo ""
    
    # Recent Log Activity (if logs exist)
    if [ -f "logs/api.log" ]; then
        echo "📝 RECENT API LOGS:"
        echo "-------------------"
        tail -3 logs/api.log
        echo ""
    fi
    
    echo "======================================="
    echo "Next refresh in ${INTERVAL} seconds... (Ctrl+C to stop)"
    
    sleep $INTERVAL
done
