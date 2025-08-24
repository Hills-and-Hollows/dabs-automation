#!/bin/bash
# PRE-COMMIT ARCHON ENFORCEMENT HOOK
# Prevents commits if Archon-first workflow is not followed

set -e

echo "🔒 PRE-COMMIT: Archon-First Workflow Check"
echo "=========================================="

# Check if Archon enforcement script exists
if [ ! -f ".cursor/enforce-archon.py" ]; then
    echo "❌ ERROR: Archon enforcement script missing!"
    echo "   Required: .cursor/enforce-archon.py"
    exit 1
fi

# Run Archon enforcement check
echo "🔍 Running Archon workflow enforcement..."
if python3 .cursor/enforce-archon.py; then
    echo "✅ PRE-COMMIT: Archon enforcement passed"
    echo "🚀 Commit allowed - Archon-first workflow verified!"
    exit 0
else
    echo "❌ PRE-COMMIT: Archon enforcement failed" 
    echo "🚨 COMMIT BLOCKED - Fix Archon issues before committing!"
    echo ""
    echo "Required actions:"
    echo "1. Ensure Archon services are running: cd archon-mcp && docker-compose up -d"
    echo "2. Verify task synchronization with Archon API"
    echo "3. Fix any configuration inconsistencies"
    echo "4. Re-run: python3 .cursor/enforce-archon.py"
    exit 1
fi
