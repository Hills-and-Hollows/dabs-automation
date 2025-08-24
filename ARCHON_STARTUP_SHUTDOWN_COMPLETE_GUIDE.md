# 🚀 ARCHON STARTUP/SHUTDOWN COMPLETE GUIDE
## Hills & Hollows LLC - Reliable Service Management

**Guide Created**: January 11, 2025  
**Status**: ✅ **COMPREHENSIVE SERVICE MANAGEMENT PROCEDURES**  
**Tested Methods**: Multiple deployment approaches with validation  

---

## 🎯 **COMPLETE STARTUP PROCEDURES**

### **🔥 METHOD 1: LOCAL DEVELOPMENT SERVER (RECOMMENDED)**

#### **📋 Prerequisites Check:**
```bash
# 1. Verify Dependencies
cd /Volumes/Expansion/4.\ CURSOR/DABC\ Pricing\ -\ Inventory/archon-mcp
python3 -c "import fastapi, uvicorn, supabase; print('✅ Dependencies OK')"

# 2. Verify Database Connection
python3 -c "
from dotenv import load_dotenv
load_dotenv()
import os
print('SUPABASE_URL:', os.getenv('SUPABASE_URL'))
print('SUPABASE_SERVICE_KEY:', 'SET' if os.getenv('SUPABASE_SERVICE_KEY') else 'NOT SET')
"

# 3. Verify Database Tables (run in Supabase SQL Editor)
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'archon_%';
```

#### **🚀 Startup Commands:**
```bash
# Option A: Direct Python execution
cd /Volumes/Expansion/4.\ CURSOR/DABC\ Pricing\ -\ Inventory/archon-mcp
python3 local_server.py

# Option B: Using startup script
./start_local.sh

# Option C: With virtual environment
source venv/bin/activate
python3 local_server.py

# Option D: Background execution
nohup python3 local_server.py > logs/archon_server.log 2>&1 &
```

#### **✅ Validation Steps:**
```bash
# 1. Health Check (wait 30 seconds for startup)
sleep 30
curl -f http://localhost:8151/health

# 2. MCP Endpoint Check
curl -f http://localhost:8151/mcp/sse

# 3. Projects API Check
curl -f http://localhost:8151/projects

# 4. Service Info
curl -f http://localhost:8151/ | jq .
```

### **🔥 METHOD 2: DOCKER COMPOSE DEPLOYMENT (PRODUCTION)**

#### **📋 Prerequisites Check:**
```bash
# 1. Docker Status
docker --version
docker compose version
docker info

# 2. Service Configuration
cd /Volumes/Expansion/4.\ CURSOR/DABC\ Pricing\ -\ Inventory/archon-mcp
cat .env | grep SUPABASE

# 3. Compose File Validation
docker compose config
```

#### **🚀 Startup Commands:**
```bash
# Option A: Full build and start
docker compose up --build -d

# Option B: Start existing services
docker compose up -d

# Option C: Start specific services
docker compose up archon-server archon-mcp -d

# Option D: Development mode with logs
docker compose up --build
```

#### **✅ Validation Steps:**
```bash
# 1. Container Status
docker compose ps

# 2. Service Health Checks
curl -f http://localhost:3837/    # UI (custom port)
curl -f http://localhost:8281/health  # Server (custom port)
curl -f http://localhost:8151/health  # MCP (custom port)
curl -f http://localhost:8152/health  # Agents (custom port)

# 3. Service Logs
docker compose logs archon-server
docker compose logs archon-mcp
```

---

## 🧪 **COMPREHENSIVE E2E TESTING PROCEDURES**

### **📋 TEST SUITE 1: Service Connectivity**

#### **🔍 Basic Connectivity Tests:**
```bash
#!/bin/bash
# Save as: scripts/test_archon_connectivity.sh

echo "🔍 ARCHON CONNECTIVITY TEST SUITE"
echo "=================================="

# Test all service endpoints
ENDPOINTS=(
  "http://localhost:8151/health|MCP Server Health"
  "http://localhost:8151/mcp/sse|MCP SSE Endpoint"
  "http://localhost:8151/projects|Projects API"
  "http://localhost:8151/|Server Info"
)

for endpoint_info in "${ENDPOINTS[@]}"; do
  IFS='|' read -r url description <<< "$endpoint_info"
  echo "Testing: $description"
  
  if curl -f -s "$url" > /dev/null 2>&1; then
    echo "✅ $description: PASS"
  else
    echo "❌ $description: FAIL"
  fi
done

echo "=================================="
echo "Connectivity test complete"
```

#### **🧪 Database Connectivity Tests:**
```sql
-- Run in Supabase SQL Editor
-- Test 1: Verify all tables exist
SELECT 
  table_name, 
  table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name LIKE 'archon_%'
ORDER BY table_name;

-- Test 2: Verify extensions are enabled
SELECT 
  extname, 
  extversion
FROM pg_extension 
WHERE extname IN ('vector', 'pgcrypto');

-- Test 3: Test settings table
SELECT key, category, description 
FROM archon_settings 
LIMIT 5;
```

### **📋 TEST SUITE 2: PLAYWRIGHT E2E TESTING**

#### **🎭 Enhanced Playwright Test Script:**
```python
#!/usr/bin/env python3
# Save as: scripts/comprehensive_playwright_test.py

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError

class ComprehensiveArchonTester:
    """Complete E2E testing for Archon system"""
    
    def __init__(self):
        self.test_results = {
            "test_start": datetime.now().isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": []
        }
        
        # Test multiple possible endpoints
        self.test_endpoints = [
            {"url": "http://localhost:8151", "name": "Local Server"},
            {"url": "http://localhost:3837", "name": "UI (Custom Port)"},
            {"url": "http://localhost:3737", "name": "UI (Default Port)"},
            {"url": "http://localhost:8281", "name": "Server (Custom Port)"},
            {"url": "http://localhost:8181", "name": "Server (Default Port)"}
        ]
    
    async def run_comprehensive_tests(self):
        """Run complete E2E test suite"""
        
        print("🎭 COMPREHENSIVE ARCHON E2E TEST SUITE")
        print("=" * 60)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Test each endpoint
            for endpoint in self.test_endpoints:
                await self._test_endpoint(page, endpoint)
            
            # Generate comprehensive report
            await self._generate_test_report()
            
            # Keep browser open for inspection
            print("⏸️  Browser open for 20 seconds for inspection...")
            await asyncio.sleep(20)
            
            await browser.close()
    
    async def _test_endpoint(self, page, endpoint):
        """Test individual endpoint"""
        
        test_name = f"Endpoint: {endpoint['name']}"
        print(f"🧪 Testing: {test_name}")
        
        try:
            await page.goto(endpoint["url"], timeout=10000)
            
            # Take screenshot
            screenshot_path = Path("data/playwright_screenshots") / f"test_{endpoint['name'].lower().replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.png"
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screenshot_path))
            
            # Test passed
            self.test_results["tests_passed"] += 1
            self.test_results["test_details"].append({
                "test": test_name,
                "status": "PASS",
                "endpoint": endpoint["url"],
                "screenshot": str(screenshot_path)
            })
            print(f"   ✅ {test_name}: PASS")
            
        except TimeoutError:
            # Test failed - connection timeout
            self.test_results["tests_failed"] += 1
            self.test_results["test_details"].append({
                "test": test_name,
                "status": "FAIL",
                "endpoint": endpoint["url"],
                "error": "Connection timeout"
            })
            print(f"   ❌ {test_name}: FAIL - Connection timeout")
            
        except Exception as e:
            # Test failed - other error
            self.test_results["tests_failed"] += 1
            self.test_results["test_details"].append({
                "test": test_name,
                "status": "FAIL", 
                "endpoint": endpoint["url"],
                "error": str(e)
            })
            print(f"   ❌ {test_name}: FAIL - {e}")
    
    async def _generate_test_report(self):
        """Generate comprehensive test report"""
        
        self.test_results["test_end"] = datetime.now().isoformat()
        self.test_results["total_tests"] = self.test_results["tests_passed"] + self.test_results["tests_failed"]
        self.test_results["success_rate"] = (self.test_results["tests_passed"] / max(self.test_results["total_tests"], 1)) * 100
        
        # Save test report
        report_file = Path("data/test_results/archon_e2e_test_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📊 TEST RESULTS SUMMARY:")
        print(f"   Total Tests: {self.test_results['total_tests']}")
        print(f"   Passed: {self.test_results['tests_passed']}")
        print(f"   Failed: {self.test_results['tests_failed']}")
        print(f"   Success Rate: {self.test_results['success_rate']:.1f}%")
        print(f"   Report: {report_file}")

if __name__ == "__main__":
    tester = ComprehensiveArchonTester()
    asyncio.run(tester.run_comprehensive_tests())
```

### **📋 TEST SUITE 3: MCP PROTOCOL TESTING**

#### **🔧 MCP Tools Validation:**
```bash
#!/bin/bash
# Save as: scripts/test_mcp_tools.sh

echo "🔧 MCP TOOLS VALIDATION SUITE"
echo "============================="

# Test MCP Server endpoint
echo "Testing MCP Server connectivity..."
curl -f http://localhost:8151/mcp/sse || echo "MCP endpoint not available"

# Test health endpoint
echo "Testing health endpoint..."
curl -f http://localhost:8151/health || echo "Health endpoint not available"

# Test projects endpoint
echo "Testing projects API..."
curl -f http://localhost:8151/projects || echo "Projects API not available"

echo "============================="
echo "MCP tools validation complete"
```

---

## 🔄 **SHUTDOWN PROCEDURES**

### **🛑 GRACEFUL SHUTDOWN METHODS:**

#### **🔥 LOCAL SERVER SHUTDOWN:**
```bash
# Method 1: Find and kill process
ps aux | grep local_server
kill <process_id>

# Method 2: Ctrl+C if running in foreground
# Press Ctrl+C in the terminal running the server

# Method 3: Kill by port
lsof -ti:8151 | xargs kill

# Method 4: Graceful shutdown script
pkill -f "python3 local_server.py"
```

#### **🔥 DOCKER COMPOSE SHUTDOWN:**
```bash
# Method 1: Stop all services
docker compose down

# Method 2: Stop and remove volumes
docker compose down -v

# Method 3: Stop specific service
docker compose stop archon-server

# Method 4: Complete cleanup
docker compose down --rmi all --volumes --remove-orphans
```

---

## 🧪 **COMPLETE STARTUP/SHUTDOWN CYCLE TEST**

### **📋 FULL CYCLE VALIDATION SCRIPT:**
```bash
#!/bin/bash
# Save as: scripts/test_full_cycle.sh

echo "🔄 ARCHON FULL CYCLE TEST"
echo "========================"

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
cd /Volumes/Expansion/4.\ CURSOR/DABC\ Pricing\ -\ Inventory/archon-mcp

# Start local server
echo "Starting Archon local server..."
python3 local_server.py &
SERVER_PID=$!

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
    
    echo ""
    echo "🛑 PHASE 3: SHUTDOWN TEST"
    echo "-------------------------"
    
    # Graceful shutdown
    echo "Sending shutdown signal..."
    kill $SERVER_PID
    
    # Wait for shutdown
    sleep 5
    
    # Verify shutdown
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        echo "✅ SHUTDOWN: SUCCESS"
    else
        echo "❌ SHUTDOWN: FAILED (force killing)"
        kill -9 $SERVER_PID
    fi
    
else
    echo "❌ STARTUP: FAILED"
    kill $SERVER_PID 2>/dev/null
fi

echo ""
echo "🎊 FULL CYCLE TEST COMPLETE"
echo "==========================="
```

---

## 📚 **TROUBLESHOOTING GUIDE**

### **❌ COMMON STARTUP ISSUES:**

#### **🔧 Issue 1: "ModuleNotFoundError"**
```bash
# Solution: Install dependencies
cd /Volumes/Expansion/4.\ CURSOR/DABC\ Pricing\ -\ Inventory/archon-mcp
python3 -m pip install -r requirements.server.txt
```

#### **🔧 Issue 2: "SUPABASE_URL not set"**
```bash
# Solution: Check environment configuration
cat .env | grep SUPABASE
# Ensure both SUPABASE_URL and SUPABASE_SERVICE_KEY are set
```

#### **🔧 Issue 3: "Database connection failed"**
```bash
# Solution: Verify database migration
# In Supabase SQL Editor, run:
SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'archon_%';
# Should return multiple tables
```

#### **🔧 Issue 4: "Port already in use"**
```bash
# Solution: Find and kill existing process
lsof -ti:8151 | xargs kill
# Or use different port in .env file
```

#### **🔧 Issue 5: "Docker daemon not running"**
```bash
# Solution: Start Docker Desktop
open -a Docker
sleep 30  # Wait for startup
docker --version  # Verify working
```

---

## 🎯 **DEPLOYMENT OPTIONS MATRIX**

### **📊 DEPLOYMENT COMPARISON:**

| Method | Startup Time | Resource Usage | Development | Production | Reliability |
|--------|--------------|----------------|-------------|-----------|-------------|
| **Local Server** | 10-30 seconds | Low | ✅ Excellent | ⚠️ Manual | Good |
| **Docker Compose** | 2-5 minutes | Medium | ✅ Good | ✅ Excellent | Excellent |
| **Docker Individual** | 1-3 minutes | Medium | ✅ Good | ✅ Good | Good |
| **Hybrid (Local+Docker)** | Variable | Low-Medium | ✅ Excellent | ✅ Good | Good |

### **🎯 RECOMMENDED APPROACHES:**

**🔥 FOR DEVELOPMENT:**
```bash
# Use local server for fast iteration
cd archon-mcp
python3 local_server.py
```

**🚀 FOR PRODUCTION:**
```bash
# Use Docker Compose for reliability
cd archon-mcp
docker compose up --build -d
```

**⚡ FOR TESTING:**
```bash
# Use comprehensive test suite
./scripts/test_full_cycle.sh
python3 scripts/comprehensive_playwright_test.py
```

---

## 📋 **STARTUP CHECKLIST**

### **✅ PRE-STARTUP VALIDATION:**
- [ ] **Environment**: `.env` file exists with Supabase credentials
- [ ] **Dependencies**: Python packages installed (`pip install -r requirements.server.txt`)
- [ ] **Database**: Migration completed successfully in Supabase
- [ ] **Docker**: Docker Desktop running (if using containers)
- [ ] **Ports**: Target ports available (8151, 3837, 8281, 8152)

### **✅ STARTUP EXECUTION:**
- [ ] **Navigate**: `cd archon-mcp` directory
- [ ] **Choose Method**: Local server OR Docker Compose
- [ ] **Execute**: Run startup command
- [ ] **Wait**: Allow 30-60 seconds for initialization
- [ ] **Validate**: Test health endpoints

### **✅ POST-STARTUP VALIDATION:**
- [ ] **Health Check**: `curl http://localhost:8151/health`
- [ ] **MCP Endpoint**: `curl http://localhost:8151/mcp/sse`
- [ ] **Projects API**: `curl http://localhost:8151/projects`
- [ ] **Playwright Test**: Run E2E validation
- [ ] **Error Logs**: Check for any startup errors

---

## 🛑 **SHUTDOWN CHECKLIST**

### **✅ GRACEFUL SHUTDOWN:**
- [ ] **Save Work**: Ensure all data is saved
- [ ] **Stop Services**: Use appropriate shutdown method
- [ ] **Wait**: Allow services to terminate gracefully
- [ ] **Verify**: Confirm all processes stopped
- [ ] **Cleanup**: Remove temporary files if needed

### **✅ POST-SHUTDOWN VALIDATION:**
- [ ] **Process Check**: No Archon processes running
- [ ] **Port Check**: Target ports released
- [ ] **Data Integrity**: Database state preserved
- [ ] **Log Review**: Check shutdown logs for errors
- [ ] **Restart Test**: Verify can restart successfully

---

## 📊 **MONITORING & HEALTH CHECKS**

### **🔍 CONTINUOUS MONITORING:**
```bash
# Monitor service health
watch -n 30 'curl -s http://localhost:8151/health'

# Monitor resource usage
watch -n 10 'ps aux | grep -E "(local_server|python3)" | grep -v grep'

# Monitor logs
tail -f logs/archon_server.log

# Monitor database connections
# Run in Supabase dashboard: Dashboard → Database → Connections
```

### **📈 PERFORMANCE METRICS:**
```bash
# Response time testing
time curl -s http://localhost:8151/health

# Load testing (if needed)
for i in {1..10}; do
  curl -s http://localhost:8151/health &
done
wait

# Memory usage
ps -p $(pgrep -f local_server) -o pid,rss,vsz,pcpu,pmem
```

---

## 🎊 **FINAL VALIDATION STATUS**

### **✅ COMPLETE PROCEDURES DOCUMENTED:**
- ✅ **Multiple Startup Methods**: Local server, Docker, hybrid approaches
- ✅ **Comprehensive Testing**: Connectivity, E2E, MCP protocol validation
- ✅ **Shutdown Procedures**: Graceful termination and cleanup
- ✅ **Troubleshooting Guide**: Common issues and solutions
- ✅ **Monitoring Tools**: Health checks and performance monitoring
- ✅ **Full Cycle Scripts**: Automated testing and validation

### **🚀 DEPLOYMENT READINESS:**
With these procedures, you can reliably:
1. **Start Archon** using multiple methods
2. **Validate functionality** with comprehensive testing
3. **Monitor performance** with health checks
4. **Shutdown gracefully** with proper cleanup
5. **Restart successfully** after any shutdown
6. **Troubleshoot issues** with detailed guides

**Your Archon system now has complete operational procedures for reliable startup, testing, and shutdown! 🎊**
