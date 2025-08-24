# Cursor MCP Setup for DABS Archon Server

## 🎉 **SUCCESS! Archon MCP Server is Running**

Your DABS Archon MCP server is now running at:
- **Server**: http://localhost:8151
- **Health Check**: http://localhost:8151/health ✅
- **MCP Endpoint**: http://localhost:8151/mcp/sse

## 🔧 **Configure Cursor to Use Archon MCP**

### **Option 1: Using Cursor's Built-in MCP Support**

1. **Open Cursor Settings**:
   - Press `Cmd+,` (Mac) or `Ctrl+,` (Windows/Linux)
   - Go to Extensions or search for "MCP"

2. **Add MCP Server**:
   - Look for MCP or Model Context Protocol settings
   - Add new server with these details:
     - **Name**: DABS Archon
     - **URL**: `http://localhost:8151/mcp/sse`
     - **Transport**: SSE (Server-Sent Events)

### **Option 2: Using MCP Extension**

1. **Install MCP Extension**:
   - Open Extensions panel (`Cmd+Shift+X`)
   - Search for "MCP" or "Model Context Protocol"
   - Install the MCP extension

2. **Configure Server**:
   - Open Command Palette (`Cmd+Shift+P`)
   - Type "MCP: Add Server"
   - Enter server details:
     ```
     Name: DABS Archon
     URL: http://localhost:8151/mcp/sse
     Transport: SSE
     ```

### **Option 3: Manual Configuration**

If Cursor uses a config file, add this to your MCP configuration:

```json
{
  "mcpServers": {
    "dabs-archon": {
      "command": "curl",
      "args": ["-N", "http://localhost:8151/mcp/sse"],
      "env": {
        "DABS_WORKSPACE": "/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory"
      }
    }
  }
}
```

## 🧪 **Test the Integration**

Once configured, test these commands in Cursor's AI chat:

### **1. Search DABS Knowledge**
```
Search the DABS knowledge base for QuickBooks integration requirements
```

### **2. Create DABS Tasks**
```
Create a task for implementing QuickBooks OAuth 2.0 authentication in Phase 2
```

### **3. Check Project Status**
```
What's the current status of DABS Phase 2 tasks?
```

### **4. Get Acceptance Criteria**
```
Show me the acceptance criteria for US-001 Store Manager story
```

## 🎯 **Available DABS Tools**

Your AI assistant now has access to these DABS-specific tools:

| Tool | Purpose | Example Usage |
|------|---------|---------------|
| `search_dabs_knowledge` | Search documentation | "Find QuickBooks API requirements" |
| `create_dabs_task` | Create project tasks | "Create SSCS integration task" |
| `get_dabs_project_status` | Check progress | "Show Phase 2 status" |

## 🚀 **Enhanced Cursor Workflow**

With Archon MCP integrated, you can now:

### **1. Context-Aware Code Generation**
```
Generate Python code for QuickBooks OAuth based on DABS requirements
```

### **2. Task-Driven Development**
```
What's the next highest priority task in Phase 2?
```

### **3. Requirements-Based Coding**
```
Show me the acceptance criteria for the current task and generate implementation code
```

### **4. Project Management**
```
Update task status and create subtasks for SSCS integration
```

## 🔍 **Verification Steps**

1. **Check Server Status**:
   ```bash
   curl http://localhost:8151/health
   ```
   Should return: `{"status":"healthy","mode":"local_development"}`

2. **Test MCP Tools**:
   In Cursor, ask: "Search DABS knowledge for integration requirements"

3. **Verify Connection**:
   Look for MCP server status in Cursor's status bar or settings

## 🛠️ **Troubleshooting**

### **Server Not Responding**
```bash
# Check if server is running
curl http://localhost:8151/health

# If not running, restart:
cd archon-mcp
./start_local.sh
```

### **Cursor Can't Connect**
- Verify URL: `http://localhost:8151/mcp/sse`
- Check firewall settings
- Try restarting Cursor

### **Tools Not Working**
- Verify MCP extension is installed and enabled
- Check server logs in terminal
- Test direct API calls with curl

## 🎉 **You're Ready!**

Your Cursor workspace is now augmented with:
- ✅ **DABS-specific AI assistance**
- ✅ **Project task management**
- ✅ **Knowledge base search**
- ✅ **Requirements-driven development**

## 🚀 **Next Steps**

1. **Test the integration** with the commands above
2. **Start using AI assistance** for DABS development
3. **Create tasks** for Phase 2 implementation
4. **Generate code** based on your requirements

**Your DABS development workflow is now supercharged with AI! 🎯**
