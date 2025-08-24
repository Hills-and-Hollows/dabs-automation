#!/bin/bash
# Archon Full Cycle Test Script
# Tests complete startup, validation, and shutdown cycle

echo "🔄 ARCHON FULL CYCLE TEST"
echo "========================"
echo "Date: $(date)"
echo ""

# Function to test endpoint
test_endpoint() {
    local url=$1
    local name=$2
    
    if curl -f -s "$url" > /dev/null 2>&1; then
        echo "✅ $name: RESPONSIVE"
        return 0
    else
        echo "❌ $name: NOT RESPONSIVE"
        return 1
    fi
}

# Function to wait for service startup
wait_for_service() {
    local url=$1
    local name=$2
    local timeout=60
    local count=0
    
    echo "⏳ Waiting for $name to start..."
    
    while [ $count -lt $timeout ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo "✅ $name: STARTED (${count}s)"
            return 0
        fi
        sleep 2
        count=$((count + 2))
    done
    
    echo "❌ $name: TIMEOUT after ${timeout}s"
    return 1
}

echo "🚀 PHASE 1: STARTUP TEST"
echo "------------------------"

# Navigate to archon directory
cd "/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory/archon-mcp"

# Kill any existing processes
pkill -f "local_server.py" 2>/dev/null || true

# Start local server
echo "Starting Archon local server..."
python3 local_server.py > logs/test_startup.log 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for startup
wait_for_service "http://localhost:8151/health" "Archon Server"
STARTUP_SUCCESS=$?

if [ $STARTUP_SUCCESS -eq 0 ]; then
    echo "✅ STARTUP: SUCCESS"
    
    # Test all endpoints
    echo ""
    echo "🧪 PHASE 2: ENDPOINT VALIDATION"
    echo "-------------------------------"
    
    test_endpoint "http://localhost:8151/health" "Health Check"
    test_endpoint "http://localhost:8151/mcp/sse" "MCP SSE"
    test_endpoint "http://localhost:8151/projects" "Projects API"
    test_endpoint "http://localhost:8151/" "Server Info"
    
    # Test response content
    echo ""
    echo "📊 PHASE 3: RESPONSE VALIDATION"
    echo "-------------------------------"
    
    echo "Health endpoint response:"
    curl -s http://localhost:8151/health | jq . 2>/dev/null || curl -s http://localhost:8151/health
    
    echo ""
    echo "🛑 PHASE 4: SHUTDOWN TEST"
    echo "-------------------------"
    
    # Graceful shutdown
    echo "Sending shutdown signal to PID $SERVER_PID..."
    kill $SERVER_PID
    
    # Wait for shutdown
    sleep 5
    
    # Verify shutdown
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        echo "✅ SHUTDOWN: SUCCESS"
        SHUTDOWN_SUCCESS=0
    else
        echo "❌ SHUTDOWN: FAILED (force killing)"
        kill -9 $SERVER_PID
        SHUTDOWN_SUCCESS=1
    fi
    
    # Test restart capability
    echo ""
    echo "🔄 PHASE 5: RESTART TEST"
    echo "------------------------"
    
    echo "Testing restart capability..."
    python3 local_server.py > logs/test_restart.log 2>&1 &
    RESTART_PID=$!
    
    wait_for_service "http://localhost:8151/health" "Archon Server (Restart)"
    RESTART_SUCCESS=$?
    
    if [ $RESTART_SUCCESS -eq 0 ]; then
        echo "✅ RESTART: SUCCESS"
        kill $RESTART_PID
        sleep 2
    else
        echo "❌ RESTART: FAILED"
        kill $RESTART_PID 2>/dev/null
    fi
    
else
    echo "❌ STARTUP: FAILED"
    kill $SERVER_PID 2>/dev/null
    SHUTDOWN_SUCCESS=1
    RESTART_SUCCESS=1
fi

echo ""
echo "🎊 FULL CYCLE TEST COMPLETE"
echo "==========================="
echo "Startup:  $([ $STARTUP_SUCCESS -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Shutdown: $([ $SHUTDOWN_SUCCESS -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Restart:  $([ $RESTART_SUCCESS -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo ""

# Overall result
if [ $STARTUP_SUCCESS -eq 0 ] && [ $SHUTDOWN_SUCCESS -eq 0 ] && [ $RESTART_SUCCESS -eq 0 ]; then
    echo "🎊 OVERALL: ALL TESTS PASSED"
    exit 0
else
    echo "⚠️ OVERALL: SOME TESTS FAILED"
    exit 1
fi
