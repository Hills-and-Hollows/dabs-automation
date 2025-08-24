# 🌐 DABS Archon Endpoint Guide

## 🔍 **What You Should See Where**

### ✅ **FOR WEB BROWSERS** (Human Users)
```
http://localhost:3837 → Archon UI Web Interface
┌─────────────────────────────────────────────────────┐
│ 🎯 Archon - Knowledge Engine                       │
│                                                     │
│ 📚 Knowledge Base    🎯 Tasks    ⚙️ Settings        │
│                                                     │
│ • Upload Documents                                  │
│ • Search Knowledge                                  │
│ • Manage Projects                                   │
│ • View Task Status                                  │
└─────────────────────────────────────────────────────┘
```

### 🤖 **FOR AI CLIENTS** (Cursor IDE)
```
http://localhost:8151/mcp/sse → MCP Server Endpoint
┌─────────────────────────────────────────────────────┐
│ 📡 MCP Server (NOT for browsers!)                  │
│                                                     │
│ Protocol: Server-Sent Events (SSE)                 │
│ Format: JSON-RPC messages                          │
│                                                     │
│ Used by: Cursor IDE, Claude Desktop, etc.          │
│ Purpose: AI tool integration                       │
└─────────────────────────────────────────────────────┘
```

## 🌐 **Browser Test Results**

### ✅ **What Works in Browser:**
- `http://localhost:3837` → **Archon UI** (Beautiful web interface)
- `http://localhost:8281/health` → **{"status": "healthy"}** (When server starts)

### ❌ **What Doesn't Work in Browser:**
- `http://localhost:8151/mcp/sse` → **"Not Found"** (This is normal!)
  
  **Why?** This endpoint expects:
  - SSE (Server-Sent Events) headers
  - JSON-RPC protocol messages  
  - AI client connections (not human browsers)

## 🔧 **Current Status Check**

| Service | URL | Browser Result | Status |
|---------|-----|----------------|--------|
| Archon UI | http://localhost:3837 | ✅ Web Interface | Working |
| Archon Server | http://localhost:8281/health | ❌ Connection Error | Needs Supabase |
| Archon MCP | http://localhost:8151/mcp/sse | ❌ "Not Found" | ✅ Normal (Working) |
| Archon Agents | http://localhost:8152/health | ✅ {"status": "healthy"} | Working |

## 🔑 **Supabase Configuration Required**

### Current Placeholder Values:
```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

### How to Get Real Values:

1. **Visit**: https://supabase.com/dashboard
2. **Create Project**: Name it "DABS-Archon"
3. **Get Credentials**: Project Settings → API
4. **Copy**:
   - **Project URL**: `https://abcdefghijklmn.supabase.co`
   - **service_role key**: `eyJ0eXAiOiJKV1Qi...` (long string)

5. **Update .env file**:
   ```bash
   cd archon-mcp
   nano .env
   # Replace the placeholder values with real ones
   ```

6. **Restart server**:
   ```bash
   docker-compose restart archon-server
   ```

## 🧪 **How to Test MCP Connection (Proper Way)**

### ❌ **Wrong Way** (Browser):
```
Open http://localhost:8151/mcp/sse in browser
Result: "Not Found" (This is expected!)
```

### ✅ **Correct Way** (AI Client):
```
Configure Cursor IDE:
- Server URL: http://localhost:8151/mcp/sse
- Transport: sse
- Name: DABS Archon

Test command in Cursor:
"Search DABS knowledge for QuickBooks integration"
```

### 🔧 **Technical Test** (Command Line):
```bash
# Test with proper SSE headers
curl -H "Accept: text/event-stream" \
     -H "Cache-Control: no-cache" \
     http://localhost:8151/mcp

# Expected: JSON-RPC response (shows it's working)
```

## 🎯 **What You Should Do Next**

1. **✅ View Web Interface**: Open http://localhost:3837 in browser
2. **🔑 Configure Supabase**: Get real credentials and update .env
3. **🔄 Restart Services**: `docker-compose restart archon-server`
4. **🤖 Connect Cursor**: Add MCP server to Cursor IDE
5. **🚀 Start Development**: Begin Archon-first workflow

## 📋 **Expected Final State**

When everything is configured correctly:
- ✅ **Browser**: Beautiful Archon UI at http://localhost:3837
- ✅ **Cursor**: Connected to MCP server with DABS tools available
- ✅ **Knowledge Base**: Populated with DABS documentation
- ✅ **Development**: Ready for AI-assisted coding
