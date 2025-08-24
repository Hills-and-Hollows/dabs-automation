# ⚡ QUICK START: Universal Archon Task Management

**Time**: 10 minutes → Universal task management for all agents  
**Result**: Cursor, Augment, Roo Code all using same task system

---

## 🚀 **STEP 1: Get Supabase Credentials (3 minutes)**

### **Go to Supabase**:
```
https://supabase.com/dashboard
```

### **Create Free Account & Project**:
1. Sign up (no credit card required)
2. Click "New Project" 
3. **Name**: `dabs-archon-universal-tasks`
4. **Region**: Choose closest to you
5. **Password**: Create strong database password (save it!)
6. Click "Create new project"
7. ⏱️ Wait 2 minutes for setup

### **Get Your Credentials**:
1. Go to **Project Settings** → **API**
2. **Copy these 2 values**:
   - **Project URL**: `https://[your-id].supabase.co`
   - **service_role key**: `eyJ...` (long token starting with eyJ)

---

## 🔧 **STEP 2: Configure Archon (2 minutes)**

### **Update .env File**:
Replace the placeholder values:

```bash
# Edit archon-mcp/.env:
SUPABASE_URL=https://your-actual-project-id.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...your-actual-key
```

---

## 🗄️ **STEP 3: Initialize Database (2 minutes)**

### **Set up Database Schema**:
1. In Supabase Dashboard → **SQL Editor** 
2. Click **"New Query"**
3. Copy **ALL contents** from: `archon-mcp/migration/complete_setup.sql`
4. Paste into SQL Editor
5. Click **"Run"**
6. ✅ Should see: "Success. No rows returned"

---

## 🐳 **STEP 4: Start Universal Archon (2 minutes)**

```bash
# From archon-mcp directory:
docker-compose up --build -d
```

### **Verify All Services Running**:
```bash
# Check status:
docker-compose ps

# Should see all services "healthy":
# - Archon-Server (port 8281)  
# - Archon-MCP (port 8151)
# - Archon-Agents (port 8152)
# - Archon-UI (port 3837)
```

---

## 🌐 **STEP 5: Verify Universal Access (1 minute)**

### **Test Endpoints**:
```bash
# Archon UI (human interface):
http://localhost:3837

# MCP Endpoint (agent interface):  
http://localhost:8151/health
# Should return: {"status": "healthy", "database": "connected"}

# Cursor Integration:
# Already configured in .cursor/mcp.json ✅
```

---

## 📋 **STEP 6: Create DABS Project & Tasks**

### **Access Task Management**:
1. 🌐 **Open**: http://localhost:3837
2. 🏗️ **Create Project**: "DABS Universal Automation System"  
3. 📝 **Add Description**: "Hills & Hollows LLC Utah Package Agency Complete Business Automation"
4. ✅ **Confirm**: Project appears in dashboard

### **Add Critical Tasks**:
```bash
# Via MCP (from any agent):
archon:manage_task(
  action="create",
  project_id="[your-project-id]",
  title="🚨 CRITICAL: Contact SSCS Vendor for Integration Documentation", 
  assignee="User",
  status="todo"
)

# Continue adding all 15 critical DABS tasks...
```

---

## 🎯 **UNIVERSAL AGENT INTEGRATION**

### **All Agents Now Use Same System**:

#### **✅ Cursor IDE** (already configured):
- MCP endpoint: `http://localhost:8151/mcp/sse`
- Commands: `archon:manage_task()`, `archon:manage_project()`

#### **✅ Augment** (configure):
```bash
MCP_SERVER_URL=http://localhost:8151/mcp/sse
PROJECT_CONTEXT=dabs-automation
```

#### **✅ Roo Code** (configure):
```bash
ARCHON_ENDPOINT=http://localhost:8151
TASK_MANAGEMENT_URL=http://localhost:8151/mcp/tools
```

#### **✅ Any MCP-Compatible Tool**:
```bash
MCP_HOST=localhost
MCP_PORT=8151
MCP_TRANSPORT=sse
```

---

## 📊 **SUCCESS VERIFICATION**

### **✅ All Systems Working When**:
- [ ] Archon UI accessible at http://localhost:3837
- [ ] MCP health check returns "healthy" + "database connected"  
- [ ] DABS project visible in Archon dashboard
- [ ] Tasks can be created via MCP commands
- [ ] All agents can query task status
- [ ] Docker containers all show "healthy" status

### **🎯 Ready for Universal Development**:
- [ ] 15 DABS critical tasks loaded in Archon
- [ ] Task assignments clear (User/AI IDE Agent/Archon)
- [ ] All development platforms connected  
- [ ] Real-time task coordination active
- [ ] Progress tracking visible to all stakeholders

---

## 🚨 **TROUBLESHOOTING**

### **If Archon UI won't load**:
```bash
# Check service status:
docker-compose logs archon-server

# Common fix - restart services:
docker-compose down
docker-compose up --build -d
```

### **If MCP endpoint returns errors**:
```bash
# Verify database connection:
curl http://localhost:8151/health

# Check Supabase credentials:
grep SUPABASE .env
```

### **If database setup failed**:
1. Go back to Supabase SQL Editor
2. Re-run complete_setup.sql  
3. Check for any error messages
4. Restart Docker containers

---

## 🎯 **IMMEDIATE BENEFITS ONCE RUNNING**

### **✅ Universal Coordination**:
- All agents see same task list
- No duplicate work across platforms
- Real-time progress updates
- Single source of truth for DABS project

### **✅ Enhanced Productivity**:  
- Task context shared across agents
- Code examples and requirements attached to tasks
- Clear assignment and ownership
- Workflow tracking (todo → doing → review → done)

### **✅ Project Visibility**:
- Manager can see progress without technical details
- Stakeholders get real-time status updates
- Clear milestone tracking toward Tessa's 90% time reduction
- Audit trail for compliance and troubleshooting

---

**🎯 RESULT: 10 minutes → Universal task management system supporting Cursor, Augment, Roo Code and any future development platforms working on the DABS automation project.**

**All agents now coordinate through Archon for maximum efficiency and zero duplicate work.**
