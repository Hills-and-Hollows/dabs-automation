# Archon MCP Server Setup for DABS Workspace

## 🎯 Overview
This guide sets up Archon MCP Server customized for the DABS (Utah Package Agency Liquor Inventory Management System) workspace, providing AI coding task management and knowledge base capabilities.

## 🔧 Custom Configuration for DABS

### Port Configuration (Modified to Avoid Conflicts)
- **Archon UI**: Port 3837 (instead of 3737)
- **Archon Server**: Port 8281 (instead of 8181) 
- **Archon MCP**: Port 8151 (instead of 8051)
- **Archon Agents**: Port 8152 (instead of 8052)
- **Archon Docs**: Port 3938 (instead of 3838)

### Integration with Existing DABS Services
- **DABS API**: Port 8000 (existing FastAPI service)
- **PostgreSQL**: Existing database (will use separate Supabase for Archon)
- **Redis**: Existing caching layer

## 📋 Prerequisites

### Required Services
1. **Supabase Account**: Free tier or local Supabase
   - Sign up at: https://supabase.com/
   - Create a new project for Archon

2. **OpenAI API Key**: For embeddings and AI features
   - Get from: https://platform.openai.com/api-keys
   - Alternative: Ollama or Google Gemini supported

3. **Docker Desktop**: For containerized services
   - Download: https://www.docker.com/products/docker-desktop/

## 🚀 Setup Instructions

### Step 1: Database Setup
1. **Create Supabase Project**:
   - Go to https://supabase.com/dashboard
   - Click "New Project"
   - Name it "DABS-Archon" or similar

2. **Get Credentials**:
   - Go to Project Settings → API
   - Copy the Project URL
   - Copy the **service_role** key (NOT the anon key!)

3. **Initialize Database**:
   - Open Supabase SQL Editor
   - Copy and paste contents of `migration/complete_setup.sql`
   - Execute the script

### Step 2: Environment Configuration
1. **Edit .env file**:
   ```bash
   cd archon-mcp
   nano .env
   ```

2. **Add your credentials**:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your-service-role-key-here
   ```

### Step 3: Start Services
```bash
# From the archon-mcp directory
docker-compose up --build -d
```

### Step 4: Verify Installation
1. **Check Services**:
   - Archon UI: http://localhost:3837
   - Archon Server: http://localhost:8281/health
   - Archon MCP: http://localhost:8151

2. **Configure API Keys**:
   - Open http://localhost:3837
   - Go to Settings
   - Add OpenAI API key
   - Test with a document upload

## 🔗 DABS Integration Points

### Knowledge Base Setup
1. **Import DABS Documentation**:
   - Upload all files from `docs/` directory
   - Crawl QuickBooks API documentation
   - Add Verifone API documentation

2. **Project Structure**:
   - Create "DABS Integration" project
   - Add phases: Foundation, SSCS Integration, QuickBooks, Verifone
   - Import existing tasks from acceptance criteria

### MCP Tools for DABS
The following MCP tools will be available for AI coding assistants:

1. **Knowledge Search**: Query DABS documentation and API specs
2. **Task Management**: Create and track integration tasks
3. **Project Operations**: Manage DABS phases and milestones
4. **Document Management**: Version control for specifications
5. **Code Context**: Search and reference existing DABS codebase

## 🤖 AI Client Configuration

### Claude Desktop
Add to your Claude Desktop config:
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

### Cursor/VS Code
Configure MCP extension with:
- **Server URL**: http://localhost:8151
- **Transport**: SSE (Server-Sent Events)

## 🔄 Development Workflow

### Hot Reload Setup
For development with automatic reloading:

```bash
# Backend services (with auto-reload)
docker-compose up archon-server archon-mcp archon-agents --build

# Frontend (with hot reload)
cd archon-ui-main && npm run dev
```

### Integration with DABS Development
1. **Knowledge Base**: Keep DABS docs synchronized
2. **Task Tracking**: Use for integration milestones
3. **Code Context**: Reference existing DABS patterns
4. **API Documentation**: Maintain up-to-date integration specs

## 🛠️ Troubleshooting

### Common Issues
1. **Port Conflicts**: Check if ports 3837, 8281, 8151, 8152 are available
2. **Database Connection**: Verify Supabase credentials and service_role key
3. **Docker Issues**: Ensure Docker Desktop is running

### Reset Database
If you need to start fresh:
```sql
-- Run in Supabase SQL Editor
-- Contents of migration/RESET_DB.sql
-- Then re-run migration/complete_setup.sql
```

## 📚 Next Steps
1. Configure knowledge base with DABS documentation
2. Set up project structure for integration phases
3. Connect AI coding assistant via MCP
4. Import existing tasks and requirements
