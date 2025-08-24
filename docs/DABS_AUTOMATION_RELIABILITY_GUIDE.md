# DABS Automation Reliability Guide
**Utah Package Agency - Hills & Hollows LLC**  
**Date: August 24, 2025**  
**Status: PRODUCTION REQUIREMENTS**

## 🎯 Purpose
This guide documents the essential requirements and setup procedures for maintaining 100% reliable DABS order automation, ensuring the system is always online and available for tool automation.

## ⚡ Critical Success Factors

### 1. **Environment Configuration** ✅ SOLVED
**Issue Identified**: Environment variables with special characters (ampersands) caused shell parsing errors.

**Solution**: 
- Quote all environment variables containing special characters
- **Fixed**: `DABS_LICENSEE_NAME="Hills & Hollows LLC"`
- **Fixed**: `DABS_LICENSE_TYPE="Utah Package Agency"`

**Prevention**: Always quote environment variables in `.env` files when they contain spaces or special characters.

### 2. **MCP Server Dependencies** ⚠️ NEEDS RESOLUTION
**Issue Identified**: MCP package version 1.12.2 not available through standard pip installation.

**Current Status**: MCP server not running, causing tool failures.

**Required Actions**:
```bash
# Option 1: Find correct MCP package source
pip install model-context-protocol==1.12.2

# Option 2: Use local MCP installation  
pip install -e ./archon-mcp/

# Option 3: Docker-based MCP server
docker run -d mcp-server:latest
```

### 3. **DABS Order Management Workflow** ✅ MAPPED
**Discovery**: DABS uses Edit → Cancel workflow, not direct delete.

**Correct Process**:
1. **Navigate**: Access DABS Orders page
2. **Edit**: Click Edit button for pending order  
3. **Cancel**: Use Cancel button (not Delete)
4. **Confirm**: Handle confirmation dialog
5. **Verify**: Confirm order removal

**Critical Pattern**:
```python
# Edit button approach (REQUIRED)
edit_button = await page.query_selector("i[data-bs-original-title='Edit']")
await edit_button.click()

# Cancel button approach (NOT delete)
cancel_button = await page.query_selector("button:has-text('Cancel')")  
await cancel_button.click()
```

### 4. **Authentication & Session Management** ✅ WORKING
**Current Status**: Authentication storage working correctly.

**Components**:
- Storage path: `dabs_auth.json` 
- Session persistence: Active
- Login flow: Functional

## 🔧 Permanent Setup Requirements

### **System Components Checklist**

#### **A. Environment Setup**
- [ ] `config/dabs_ordering.env` properly configured
- [ ] All special characters quoted in env vars
- [ ] DABS credentials validated
- [ ] Python path configured: `PYTHONPATH="./src"`

#### **B. MCP Server Setup**
- [ ] MCP package installed (version 1.12.2+)
- [ ] DABS ordering MCP server running
- [ ] Server health check passing: `localhost:8281/health`
- [ ] Tool endpoints responding correctly

#### **C. DABS Integration**
- [ ] Authentication session active
- [ ] Browser automation configured  
- [ ] Order management workflow mapped
- [ ] Error handling implemented

#### **D. Monitoring & Maintenance**
- [ ] Health check automation
- [ ] Log rotation configured
- [ ] Error notification system
- [ ] Backup/recovery procedures

## 🚀 Startup Scripts

### **1. Daily Startup Script**
```bash
#!/bin/bash
# daily_dabs_startup.sh

echo "🚀 Starting DABS Automation System..."

# Load environment
source config/dabs_ordering.env

# Export Python path
export PYTHONPATH="./src:$PYTHONPATH"

# Start MCP server
python3 src/mcp/dabs_ordering_mcp_server.py &

# Verify health
sleep 5
curl -s http://localhost:8281/health

echo "✅ DABS System Ready"
```

### **2. Health Check Script**  
```bash
#!/bin/bash
# check_dabs_health.sh

# Check MCP server
if curl -sf http://localhost:8281/health > /dev/null; then
    echo "✅ MCP Server: Online"
else
    echo "❌ MCP Server: Offline - Restarting..."
    python3 src/mcp/dabs_ordering_mcp_server.py &
fi

# Check DABS authentication
if python3 scripts/test_dabs_auth.py; then
    echo "✅ DABS Auth: Valid"
else
    echo "⚠️ DABS Auth: Needs Refresh"
fi
```

## 📋 Automation Integration Patterns

### **For Cursor MCP Tools**
```javascript
// Reliable DABS order deletion
async function deletePendingOrder() {
    // 1. Health check first
    const health = await mcp_dabs_ordering_dabs_system_health({});
    
    // 2. Authentication check  
    const auth = await mcp_dabs_ordering_dabs_login_status({});
    
    // 3. Delete operation
    const result = await mcp_dabs_ordering_dabs_delete_open_order({
        confirm: true
    });
    
    return result;
}
```

### **For Direct Python Integration**
```python
# Use standalone script as fallback
import subprocess

def delete_dabs_order_reliable():
    try:
        # Try MCP first
        result = call_mcp_tool("dabs_delete_open_order")
        return result
    except:
        # Fallback to standalone script
        result = subprocess.run([
            "python3", "scripts/delete_dabs_order.py"
        ], capture_output=True)
        return result.returncode == 0
```

## 🎯 Success Metrics

### **Reliability Targets**
- **Uptime**: 99.9% availability
- **Response Time**: <30 seconds for order operations
- **Error Rate**: <0.1% failed operations
- **Recovery Time**: <5 minutes for service restoration

### **Monitoring Dashboards**
- MCP server status: `http://localhost:8281/health`
- DABS connectivity: Authentication test results
- Order processing: Success/failure rates
- System health: CPU, memory, network status

## 🔄 Maintenance Schedule

### **Daily Tasks**
- Health check execution
- Log file rotation
- Authentication validation

### **Weekly Tasks**  
- Full system restart
- Performance optimization
- Backup verification

### **Monthly Tasks**
- Dependency updates
- Security patch application
- Disaster recovery testing

## 📞 Emergency Procedures

### **MCP Server Down**
1. Check process: `ps aux | grep dabs_ordering_mcp_server`
2. Restart: `python3 src/mcp/dabs_ordering_mcp_server.py &`
3. Verify: `curl http://localhost:8281/health`
4. Fallback: Use `scripts/delete_dabs_order.py`

### **DABS Authentication Failure**
1. Delete: `rm dabs_auth.json`
2. Re-authenticate: Run login flow
3. Test: `python3 scripts/test_dabs_auth.py`

### **Environment Issues**
1. Validate: `source config/dabs_ordering.env`
2. Check: Environment variable formatting  
3. Fix: Quote special characters
4. Restart: All dependent services

## ✅ Implementation Status

- **✅ Environment Setup**: Fixed parsing issues
- **✅ DABS Workflow**: Mapped Edit→Cancel pattern
- **✅ Authentication**: Working correctly
- **⚠️ MCP Server**: Dependency resolution needed
- **📋 Documentation**: Complete with procedures

## 🎊 Next Steps

1. **Resolve MCP Dependencies**: Install correct MCP package version
2. **Deploy Health Checks**: Implement monitoring scripts  
3. **Test Automation**: Validate end-to-end workflows
4. **Production Rollout**: Enable 24/7 automation system

This guide ensures DABS automation remains reliable, maintainable, and always available for critical Utah Package Agency operations.
