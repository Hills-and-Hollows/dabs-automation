# Archon MCP Server Setup Walkthrough for DABS Project

## 🎯 Complete Step-by-Step Guide

This walkthrough will get you from zero to fully operational Archon MCP Server with your DABS project tasks loaded and ready for AI-assisted development.

## 📋 Prerequisites Checklist

- [ ] Docker Desktop installed and running
- [ ] Supabase account created (free tier is fine)
- [ ] OpenAI API key obtained
- [ ] DABS workspace accessible

## 🚀 Phase 1: Initial Setup (15 minutes)

### Step 1: Start Archon Services
```bash
# From your DABS workspace root
./start_archon_dabs.sh
```

**Expected Output:**
- ✅ Port availability check
- ✅ Docker containers building and starting
- ✅ Service health verification
- 🌐 Archon UI available at http://localhost:3837

### Step 2: Configure Supabase Database
1. **Create Supabase Project**:
   - Go to https://supabase.com/dashboard
   - Click "New Project"
   - Name: "DABS-Archon"
   - Choose region closest to you

2. **Get Credentials**:
   - Go to Project Settings → API
   - Copy **Project URL**
   - Copy **service_role** key (the longer one, NOT anon key!)

3. **Initialize Database**:
   - Open Supabase SQL Editor
   - Copy contents of `archon-mcp/migration/complete_setup.sql`
   - Execute the script

### Step 3: Configure Environment
```bash
cd archon-mcp
nano .env
```

Add your credentials:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

### Step 4: Restart Services
```bash
docker-compose restart
```

## 📚 Phase 2: Knowledge Base Setup (10 minutes)

### Step 1: Access Archon UI
1. Open http://localhost:3837
2. Go to **Settings** tab
3. Add your **OpenAI API Key**
4. Test connection (should show green checkmark)

### Step 2: Upload DABS Documentation
Go to **Knowledge Base** → **Upload Documents**

Upload these files in order:
1. `PROJECT_SUMMARY.md` - Project overview
2. `docs/FUNCTIONAL_REQUIREMENTS.md` - Core requirements
3. `docs/TECHNICAL_ARCHITECTURE.md` - System design
4. `docs/ACCEPTANCE_CRITERIA.md` - Success criteria
5. `docs/USER_STORIES.md` - User requirements
6. `research-paper-qbo-mcp.md` - Integration research

### Step 3: Test Knowledge Search
1. Go to **Knowledge Base** → **Search**
2. Try searching: "QuickBooks integration requirements"
3. Verify you get relevant results from uploaded docs

## 🏗️ Phase 3: Project Structure Setup (15 minutes)

### Step 1: Create Main Project
1. Go to **Projects** tab
2. Click **"Create Project"**
3. Fill in details:
   - **Name**: "DABS Integration System"
   - **Description**: "Utah Package Agency Liquor Inventory Management System - Complete PRD Implementation"
   - **Priority**: Critical
   - **Status**: Active

### Step 2: Create Phase 1 (Foundation) - COMPLETED
1. Click **"Add Feature"** under your project
2. **Feature Name**: "Phase 1: Foundation"
3. **Status**: Completed
4. **Description**: "Business requirements, research, and technical specifications"

Add these tasks (mark as completed):
- Business Requirements Analysis
- DABS Data Structure Analysis (1,239 SKUs)
- QuickBooks API Research
- Verifone Access Verification
- Technical Specifications

### Step 3: Create Phase 2 (Core Integrations) - IN PROGRESS
1. **Feature Name**: "Phase 2: Core Integrations"
2. **Status**: In Progress
3. **Description**: "Implement core system integrations"

Add these tasks:
- **SSCS POS Integration Research** (In Progress)
  - Priority: Critical
  - Blocker: "Waiting for SSCS vendor response"
- **QuickBooks OAuth 2.0 Implementation** (Not Started)
  - Priority: High
- **DABS File Processing Engine** (Not Started)
  - Priority: Critical
- **Integration Hub Development** (Not Started)
  - Priority: High

### Step 4: Create Phase 3 (Compliance) - PLANNED
1. **Feature Name**: "Phase 3: Compliance & Reporting"
2. **Status**: Planned

Add these tasks:
- Automated DABS Monthly Reporting
- Complete Audit Trail System
- Compliance Dashboard

### Step 5: Create Phase 4 (Analytics) - PLANNED
1. **Feature Name**: "Phase 4: Analytics & Optimization"
2. **Status**: Planned

Add these tasks:
- Predictive Analytics for Demand Forecasting
- Inventory Optimization Recommendations
- Mobile Dashboard for Remote Management

## 🤖 Phase 4: AI Assistant Integration (10 minutes)

### Option A: Claude Desktop
1. Open `~/.config/claude-desktop/config.json`
2. Add this configuration:
```json
{
  "mcpServers": {
    "dabs-archon": {
      "command": "curl",
      "args": ["-N", "http://localhost:8151/sse"]
    }
  }
}
```
3. Restart Claude Desktop

### Option B: Cursor/VS Code
1. Install MCP extension
2. Configure server:
   - **Name**: DABS Archon
   - **URL**: http://localhost:8151
   - **Transport**: SSE

### Test AI Integration
Ask your AI assistant:
```
"Search the DABS knowledge base for QuickBooks integration requirements"
```

You should get results from your uploaded documentation.

## 🎯 Phase 5: Daily Workflow Setup (5 minutes)

### Morning Routine
1. **Check Project Status**:
   ```
   Ask AI: "What's the current status of DABS Phase 2 tasks?"
   ```

2. **Review Today's Priorities**:
   ```
   Ask AI: "What are the highest priority DABS tasks for today?"
   ```

### During Development
1. **Get Context**:
   ```
   Ask AI: "Show me the acceptance criteria for US-001 Store Manager story"
   ```

2. **Generate Code**:
   ```
   Ask AI: "Generate Python code for QuickBooks OAuth authentication using the DABS requirements"
   ```

3. **Update Progress**:
   - Use Archon UI to update task status
   - Add notes and blockers

### End of Day
1. **Update Tasks**: Mark completed work
2. **Plan Tomorrow**: Ask AI for next priorities

## ✅ Verification Checklist

After setup, verify these work:

- [ ] Archon UI loads at http://localhost:3837
- [ ] Knowledge base search returns DABS documentation
- [ ] Project structure shows all phases and tasks
- [ ] AI assistant connects via MCP (http://localhost:8151)
- [ ] AI can search DABS knowledge and create tasks
- [ ] Task status updates work in Archon UI

## 🎉 Success! You're Ready to Go

You now have:
- ✅ **Archon MCP Server** running with DABS-specific configuration
- ✅ **Knowledge Base** loaded with all DABS documentation
- ✅ **Project Structure** matching your PRD phases and acceptance criteria
- ✅ **AI Assistant** connected and ready to help with DABS development
- ✅ **Task Management** system for tracking PRD completion

## 🚀 Next Steps

1. **Start with Phase 2**: Focus on SSCS POS integration research
2. **Use AI Assistance**: Ask for help breaking down complex tasks
3. **Track Progress**: Update task status daily
4. **Generate Code**: Use AI to create integration code
5. **Monitor Acceptance Criteria**: Track progress toward PRD completion

## 🆘 Need Help?

- **Service Issues**: Check `archon-mcp/DABS_SETUP_GUIDE.md`
- **Task Management**: See `ARCHON_TASK_MANAGEMENT_GUIDE.md`
- **Integration Problems**: Review `archon-mcp/dabs_integration_config.json`

**You're now ready to use AI-powered project management for your DABS system!** 🎯
