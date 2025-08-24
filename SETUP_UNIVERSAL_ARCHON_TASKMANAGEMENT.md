# 🎯 UNIVERSAL ARCHON TASK MANAGEMENT SETUP

**Goal**: Establish Archon as the central task management system for ALL agents and development platforms  
**Platforms**: Cursor, Augment, Roo Code, and all future development tools  
**Timeline**: 10 minutes setup → Universal task management for entire DABS project

---

## 🔥 **WHY UNIVERSAL ARCHON TASK MANAGEMENT?**

### **Current Problem**: 
- ❌ Tasks scattered across different tools and documents
- ❌ No central coordination between agents
- ❌ Limited local development server functionality
- ❌ No persistent task tracking or collaboration

### **Archon Solution**:
- ✅ **Central Database**: All tasks in one Supabase-backed system
- ✅ **Multi-Agent Coordination**: Cursor, Augment, Roo Code all use same system
- ✅ **Persistent Storage**: Task history, progress tracking, audit trails
- ✅ **Real-time Sync**: All agents see current task status
- ✅ **Workflow Management**: todo → doing → review → done lifecycle
- ✅ **MCP Protocol**: Universal integration standard

---

## ⚡ **IMMEDIATE SETUP (10 MINUTES)**

### **Step 1: Create Supabase Account** (3 minutes)
```bash
1. 🌐 Go to: https://supabase.com/dashboard
2. 📝 Sign up (free account - no credit card required)
3. 🆕 Click "New Project"
4. 📛 Name: "dabs-archon-universal-tasks"
5. 🎯 Choose region: US East (closest to your location)
6. 🔑 Set strong database password (save this!)
7. ⏱️ Wait 2 minutes for project creation
```

### **Step 2: Get Database Credentials** (1 minute)
```bash
1. 📊 In Supabase Dashboard → Project Settings → API
2. 📋 Copy these values:
   • Project URL: https://[your-project-id].supabase.co
   • service_role key: eyJ... (starts with eyJ)
3. 💾 Save both values - you'll need them next
```

### **Step 3: Configure Archon Environment** (2 minutes)
Replace the placeholder values in your `.env` file:

```bash
# Update archon-mcp/.env with your real Supabase credentials:
SUPABASE_URL=https://your-actual-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-actual-service-key-starting-with-eyJ
```

### **Step 4: Initialize Database Schema** (2 minutes)
```bash
1. 🗄️ Supabase Dashboard → SQL Editor → New Query
2. 📄 Copy contents of: archon-mcp/migration/complete_setup.sql
3. 📋 Paste into SQL Editor
4. ▶️ Click "Run" to create all tables and functions
5. ✅ Verify: Should see "Success" message
```

### **Step 5: Start Universal Archon System** (2 minutes)
```bash
1. 🐳 Run: docker-compose up --build -d
2. ⏱️ Wait 1-2 minutes for all services to start
3. 🌐 Verify: http://localhost:3837 (Archon UI)
4. 🤖 Verify: http://localhost:8151/health (MCP endpoint)
```

---

## 🎯 **UNIVERSAL ACCESS CONFIGURATION**

### **Multi-Agent Integration Points**

#### **For Cursor IDE**:
```json
// .cursor/mcp.json already configured:
{
  "archon": {
    "command": "mcp",
    "args": ["http://localhost:8151/mcp/sse"],
    "env": {}
  }
}
```

#### **For Augment**:
```bash
# Augment MCP Configuration:
MCP_SERVER_URL=http://localhost:8151/mcp/sse
MCP_TRANSPORT=sse
PROJECT_CONTEXT=dabs-automation
```

#### **For Roo Code**:
```bash
# Roo Code Integration:
ARCHON_ENDPOINT=http://localhost:8151
TASK_MANAGEMENT_URL=http://localhost:8151/mcp/tools
PROJECT_ID=dabs-universal-project
```

#### **For Any MCP-Compatible Tool**:
```bash
# Universal MCP Configuration:
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8151  
MCP_TRANSPORT=sse
MCP_PROTOCOL=json-rpc-2.0
```

---

## 📋 **DABS PROJECT SETUP IN ARCHON**

### **Create Universal DABS Project**
Once Archon is running, execute these MCP commands:

```bash
# 1. Create DABS Project in Archon
archon:manage_project(
  action="create",
  title="DABS Universal Automation System",
  description="Hills & Hollows LLC Utah Package Agency Complete Business Automation - Universal Task Management for All Agents",
  github_repo="https://github.com/your-org/dabs-pricing-inventory",
  prd={
    "business_context": "Utah Package Agency (1,239 SKUs)",
    "primary_user": "Tessa Brakan (Store Manager)", 
    "success_metrics": {
      "time_reduction": "90% (10+ hours → <1 hour monthly)",
      "error_rate": "<0.1% (vs current 2%)",
      "processing_speed": "<15 minutes for 1,239 SKUs",
      "staff_relief": "Return to 40-hour work weeks"
    },
    "compliance": "Utah Package Agency 3-year contract requirements",
    "integrations": ["DABS", "SSCS POS", "QuickBooks", "Verifone"]
  }
)
```

### **Create All Critical Tasks**
Migrate all 15 critical tasks to Archon system:

```bash
# CRITICAL BLOCKER TASKS
archon:manage_task(
  action="create", 
  project_id="[dabs-project-id]",
  title="🚨 CRITICAL: Contact SSCS Vendor for Integration Documentation",
  description="BLOCKING ALL POS AUTOMATION - Must obtain technical integration specifications from SSCS vendor to enable price sync and inventory management. Without this, no automation systems can connect to POS.",
  assignee="User",
  task_order=100,
  feature="sscs_integration",
  sources=[
    {"url": "research reports/notes for manager workflow.md", "type": "requirements", "relevance": "SSCS integration requirements"}
  ]
)

archon:manage_task(
  action="create",
  project_id="[dabs-project-id]", 
  title="🚨 CRITICAL: Build DABS Excel Processing Engine",
  description="Core automation system to process 1,239+ SKUs from monthly DABS Excel files. Must complete processing in <15 minutes with <0.1% error rate. This IS the 90% time reduction for Tessa.",
  assignee="AI IDE Agent",
  task_order=95,
  feature="dabs_processing",
  sources=[
    {"file": "src/processors/dabs_processor.py", "type": "implementation_target", "relevance": "DABS processing specification"}
  ]
)

# Continue for all 15 critical tasks...
```

---

## 🌐 **UNIVERSAL WORKFLOW INTEGRATION**

### **Standard Task Lifecycle for ALL Agents**
```bash
1. 📋 DISCOVERY: Any agent queries tasks via archon:manage_task(action="list")
2. 🎯 ASSIGNMENT: Agent moves task to "doing" via archon:manage_task(action="update") 
3. 🔧 EXECUTION: Agent implements solution using their preferred tools
4. 📤 COMPLETION: Agent moves to "review" with implementation notes
5. ✅ VALIDATION: QA agent validates and moves to "done" or back to "doing"
6. 📊 TRACKING: All agents see real-time progress across entire project
```

### **Cross-Agent Coordination Rules**
- **One Agent Per Task**: Only one agent can have a task in "doing" status
- **Status Updates Required**: All agents must update task status when starting/stopping work
- **Context Sharing**: Implementation notes and code examples shared via task updates
- **Progress Visibility**: All agents can see what others are working on

---

## 🎯 **IMMEDIATE BENEFITS**

### **For Project Management**:
- ✅ **Single Source of Truth**: All 15+ DABS tasks in one system
- ✅ **Real-time Coordination**: No duplicate work between agents
- ✅ **Progress Tracking**: Visual dashboard of project completion
- ✅ **Audit Trail**: Complete history of who did what when

### **For Development Teams**:
- ✅ **Tool Agnostic**: Works with Cursor, Augment, Roo Code, any MCP client
- ✅ **Persistent Context**: Task details, code examples, requirements always available
- ✅ **Dependency Management**: Clear task ordering and prerequisites
- ✅ **Quality Gates**: Review process ensures code quality

### **For Business Stakeholders**:
- ✅ **Visibility**: Real-time project status without technical details
- ✅ **Accountability**: Clear assignment and completion tracking
- ✅ **Timeline Predictability**: Data-driven completion estimates
- ✅ **Risk Management**: Early identification of blockers and delays

---

## 📊 **SUCCESS METRICS**

### **Universal Task Management KPIs**:
- **Task Completion Rate**: Target >90% on-time completion
- **Agent Coordination**: Zero duplicate work incidents
- **Context Sharing**: 100% tasks have complete requirements
- **Tool Integration**: All development platforms connected
- **Progress Visibility**: Real-time status for all stakeholders

### **DABS Project Specific**:
- **15 Critical Tasks**: Tracked from todo → done
- **Phase Completion**: Clear milestone tracking
- **Tessa's Relief**: Progress toward 90% time reduction
- **Business Impact**: ROI tracking and validation

---

## 🚀 **NEXT STEPS (After Setup Complete)**

1. **✅ Verify Archon Health**: All services running and accessible
2. **📋 Create DABS Project**: Universal project container in Archon
3. **📝 Import All Tasks**: Migrate 15 critical tasks to Archon system
4. **🔗 Configure All Agents**: Ensure Cursor, Augment, Roo Code can access
5. **🎯 Begin Coordinated Development**: All agents use same task system
6. **📊 Monitor Progress**: Real-time tracking of manager user story completion

---

## ⚠️ **CRITICAL SUCCESS FACTORS**

1. **Database Reliability**: Supabase must be properly configured
2. **Network Connectivity**: All agents must reach localhost:8151
3. **Task Discipline**: All agents must update task status consistently
4. **Single Coordination Point**: No bypass of Archon for DABS tasks
5. **Regular Sync**: Daily standup review of Archon task board

---

**🎯 BOTTOM LINE**: With Universal Archon Task Management, every agent working on DABS will have the same context, avoid duplicate work, and contribute to the single goal of delivering Tessa's 90% time reduction relief.**

**This is the foundation for coordinated, efficient development across all platforms.**
