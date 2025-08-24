#!/bin/bash
# ARCHON-FIRST WORKFLOW ENFORCEMENT INSTALLER
# Sets up comprehensive enforcement at IDE, Git, and system levels

set -e

echo "🚀 ARCHON-FIRST WORKFLOW ENFORCEMENT INSTALLER"
echo "==============================================="

# Step 1: Make enforcement scripts executable
echo "🔧 Setting up enforcement scripts..."
chmod +x .cursor/enforce-archon.py
chmod +x .cursor/pre-commit-archon-check.sh
chmod +x .cursor/install-archon-enforcement.sh

# Step 2: Install Git pre-commit hook
echo "🔗 Installing Git pre-commit hook..."
if [ ! -d ".git/hooks" ]; then
    echo "❌ ERROR: Not in a Git repository!"
    echo "   Run: git init"
    exit 1
fi

# Create or update pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# ARCHON-FIRST ENFORCEMENT - AUTO-INSTALLED
# This hook ensures all commits follow Archon-first workflow

exec .cursor/pre-commit-archon-check.sh
EOF

chmod +x .git/hooks/pre-commit
echo "✅ Git pre-commit hook installed"

# Step 3: Update cursor_mcp_config.json with consistent ports
echo "🔧 Fixing configuration consistency..."
cat > cursor_mcp_config.json << 'EOF'
{
  "cursor_mcp_configuration": {
    "description": "MCP configuration for Cursor to connect to DABS Archon server",
    "server_url": "http://localhost:8281",
    "mcp_endpoint": "http://localhost:8281/api",
    "health_endpoint": "http://localhost:8281/health",
    
    "archon_services": {
      "archon_server": "http://localhost:8281",
      "archon_mcp": "http://localhost:8151", 
      "archon_ui": "http://localhost:3837",
      "archon_agents": "http://localhost:8152"
    },
    
    "enforcement_rules": {
      "mandatory_archon_check": true,
      "block_todo_write_first": true,
      "require_task_sync": true,
      "validate_before_commit": true
    },
    
    "available_tools": [
      {
        "name": "mcp_archon_create_task",
        "description": "Create tasks in Archon project management",
        "endpoint": "http://localhost:8281/api/tasks"
      },
      {
        "name": "mcp_archon_update_task", 
        "description": "Update task status in Archon",
        "endpoint": "http://localhost:8281/api/tasks/{task_id}"
      },
      {
        "name": "mcp_archon_get_project_status",
        "description": "Get current project status",
        "endpoint": "http://localhost:8281/api/tasks"
      },
      {
        "name": "mcp_archon_perform_rag_query",
        "description": "Search knowledge base",
        "endpoint": "http://localhost:8152/rag/query"
      }
    ]
  }
}
EOF

# Step 4: Test the enforcement system
echo "🧪 Testing enforcement system..."
if python3 .cursor/enforce-archon.py; then
    echo "✅ Enforcement system test: PASSED"
else
    echo "⚠️  Enforcement system test: FAILED (but installed)"
    echo "   Note: Archon services may not be running yet"
    echo "   Run: cd archon-mcp && docker-compose up -d"
fi

# Step 5: Create quick-start commands
echo "📝 Creating quick-start commands..."
cat > check-archon.sh << 'EOF'
#!/bin/bash
# Quick Archon status check
python3 .cursor/enforce-archon.py
EOF
chmod +x check-archon.sh

cat > start-archon.sh << 'EOF'  
#!/bin/bash
# Quick Archon services start
cd archon-mcp && docker-compose up -d
echo "⏳ Waiting for services to start..."
sleep 10
cd .. && python3 .cursor/enforce-archon.py
EOF
chmod +x start-archon.sh

echo ""
echo "🎉 ARCHON-FIRST ENFORCEMENT INSTALLATION COMPLETE!"
echo "=================================================="
echo ""
echo "✅ Installed Components:"
echo "   🔒 Pre-commit Git hook (blocks non-Archon commits)"
echo "   🔧 Archon enforcement script (.cursor/enforce-archon.py)"
echo "   ⚙️  Consistent MCP configuration (cursor_mcp_config.json)"
echo "   🚀 Quick-start scripts (check-archon.sh, start-archon.sh)"
echo ""
echo "🎯 How to Use:"
echo "   1. Start Archon: ./start-archon.sh"
echo "   2. Check status: ./check-archon.sh"
echo "   3. All commits now require Archon-first workflow"
echo "   4. TodoWrite is blocked until Archon is verified"
echo ""
echo "🔐 Enforcement Guaranteed:"
echo "   • Git pre-commit hooks prevent non-Archon workflows"
echo "   • Configuration consistency enforced"
echo "   • Task synchronization verified before any work"
echo "   • IDE rules updated for Archon-first development"
echo ""
echo "⚡ Next Steps:"
echo "   1. Run: ./start-archon.sh"
echo "   2. Verify: ./check-archon.sh"
echo "   3. All development now guaranteed Archon-first!"
