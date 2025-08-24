# Archon MCP Server Integration for DABS Workspace

## 🎯 Overview

This integration adds **Archon MCP Server** to your DABS (Utah Package Agency Liquor Inventory Management System) workspace, providing AI coding task management and knowledge base capabilities.

## 🏗️ What's Been Set Up

### ✅ **Archon MCP Server Infrastructure**
- **Location**: `archon-mcp/` directory
- **Custom Ports**: Modified to avoid conflicts with existing DABS services
- **Integration**: Configured specifically for DABS workflow

### ✅ **Custom Port Configuration**
| Service | Default Port | DABS Port | Purpose |
|---------|-------------|-----------|---------|
| Archon UI | 3737 | **3837** | Web interface |
| Archon Server | 8181 | **8281** | Core API |
| Archon MCP | 8051 | **8151** | MCP protocol |
| Archon Agents | 8052 | **8152** | AI agents |

### ✅ **DABS-Specific Configuration Files**
- `archon-mcp/DABS_SETUP_GUIDE.md` - Detailed setup instructions
- `archon-mcp/dabs_integration_config.json` - Integration configuration
- `archon-mcp/dabs_mcp_config.json` - MCP tools and capabilities
- `archon-mcp/setup_dabs_archon.py` - Automated setup script
- `start_archon_dabs.sh` - Quick start script

## 🚀 Quick Start

### 1. **Prerequisites Setup**
You'll need:
- **Supabase Account**: Free tier at https://supabase.com/
- **OpenAI API Key**: From https://platform.openai.com/api-keys
- **Docker Desktop**: Running and available

### 2. **Database Configuration**
```bash
# 1. Create Supabase project named "DABS-Archon"
# 2. Get Project URL and service_role key from Settings → API
# 3. Run database setup in Supabase SQL Editor:
#    Copy/paste contents of archon-mcp/migration/complete_setup.sql
```

### 3. **Automated Setup**
```bash
# Run the automated setup script
cd archon-mcp
python3 setup_dabs_archon.py
```

### 4. **Quick Start**
```bash
# From DABS workspace root
./start_archon_dabs.sh
```

## 🔧 Manual Setup (Alternative)

If you prefer manual setup:

```bash
# 1. Configure environment
cd archon-mcp
cp .env.example .env
# Edit .env with your Supabase credentials

# 2. Start services
docker-compose up --build -d

# 3. Verify services
curl http://localhost:3837  # Archon UI
curl http://localhost:8281/health  # Archon Server
curl http://localhost:8151  # Archon MCP
```

## 🤖 AI Client Configuration

### **Claude Desktop**
Add to `~/.config/claude-desktop/config.json`:
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

### **Cursor/VS Code**
Install MCP extension and configure:
- **Server URL**: `http://localhost:8151`
- **Transport**: SSE (Server-Sent Events)
- **Name**: DABS Archon

## 📚 DABS-Specific MCP Tools

Once connected, your AI assistant will have access to:

### **Knowledge Management**
- `search_dabs_knowledge` - Search DABS docs and API specs
- `get_dabs_api_reference` - Get API documentation
- `update_dabs_documentation` - Update project docs

### **Task Management**
- `create_dabs_task` - Create integration tasks
- `get_dabs_project_status` - Check project phases
- `track_dabs_compliance` - Monitor compliance requirements

### **Code Generation**
- `generate_dabs_code` - Generate integration code
- `analyze_dabs_integration` - Analyze requirements
- `validate_dabs_requirements` - Validate against criteria

### **Performance & Optimization**
- `optimize_dabs_performance` - Performance analysis
- `dabs_testing_strategy` - Generate test strategies

## 📋 Integration Workflow

### **Phase 1: Knowledge Base Setup**
1. Open Archon UI: http://localhost:3837
2. Go to Settings → Add OpenAI API key
3. Upload DABS documentation:
   - `docs/FUNCTIONAL_REQUIREMENTS.md`
   - `docs/TECHNICAL_ARCHITECTURE.md`
   - `docs/ACCEPTANCE_CRITERIA.md`
   - `research-paper-qbo-mcp.md`

### **Phase 2: Project Structure**
1. Create "DABS Integration" project
2. Set up phases:
   - ✅ Foundation (Complete)
   - 🔄 SSCS Integration (In Progress)
   - 📋 QuickBooks Integration (Planned)
   - 📋 Verifone Integration (Planned)

### **Phase 3: AI-Assisted Development**
1. Connect AI coding assistant via MCP
2. Use DABS-specific tools for:
   - Requirements analysis
   - Code generation
   - Integration planning
   - Testing strategies

## 🔄 Development Commands

### **Service Management**
```bash
# Start all services
./start_archon_dabs.sh

# Stop services
cd archon-mcp && docker-compose down

# View logs
cd archon-mcp && docker-compose logs -f

# Restart specific service
cd archon-mcp && docker-compose restart archon-server
```

### **Development Mode (Hot Reload)**
```bash
# Backend with hot reload
cd archon-mcp
docker-compose up archon-server archon-mcp archon-agents --build

# Frontend with hot reload (separate terminal)
cd archon-mcp/archon-ui-main
npm run dev
```

## 🛠️ Troubleshooting

### **Common Issues**

1. **Port Conflicts**
   - Check: `lsof -i :3837,8281,8151,8152`
   - Solution: Stop conflicting services or modify ports in `.env`

2. **Database Connection Failed**
   - Check: Supabase credentials in `.env`
   - Verify: Using service_role key (not anon key)

3. **Docker Services Not Starting**
   - Check: Docker Desktop is running
   - Verify: Sufficient disk space and memory

4. **MCP Server Not Responding**
   - Wait: Services need 60+ seconds to fully start
   - Check: Dependencies are healthy

### **Service Health Check**
```bash
# Check all services
curl http://localhost:3837      # UI
curl http://localhost:8281/health  # Server
curl http://localhost:8151      # MCP
curl http://localhost:8152/health  # Agents
```

## 📖 Documentation

- **Setup Guide**: `archon-mcp/DABS_SETUP_GUIDE.md`
- **Integration Config**: `archon-mcp/dabs_integration_config.json`
- **MCP Tools**: `archon-mcp/dabs_mcp_config.json`
- **Official Archon Docs**: `archon-mcp/README.md`

## 🎉 Success Indicators

You'll know the integration is working when:

1. ✅ All services respond to health checks
2. ✅ Archon UI loads at http://localhost:3837
3. ✅ AI assistant connects via MCP at http://localhost:8151
4. ✅ DABS documentation is searchable in knowledge base
5. ✅ AI assistant can create and manage DABS tasks

## 🚀 Next Steps

1. **Upload Documentation**: Add all DABS docs to knowledge base
2. **Create Project Structure**: Set up DABS integration phases
3. **Configure AI Assistant**: Connect via MCP for enhanced coding
4. **Start Development**: Use AI assistance for integration tasks

---

**🎯 Goal**: Transform your DABS development workflow with AI-powered task management and intelligent code assistance!
