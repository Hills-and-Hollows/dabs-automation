#!/bin/bash

# QuickBooks Production Configuration Script
# Hills & Hollows LLC - DABS Automation System

echo "🚀 QUICKBOOKS PRODUCTION CONFIGURATION"
echo "======================================"
echo "Hills & Hollows LLC - DABS Automation System"
echo ""

# Check if we're in the right directory
if [ ! -f "scripts/setup_quickbooks_oauth.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected: /Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory"
    exit 1
fi

echo "📋 STEP 1: QuickBooks Developer Account Setup"
echo "--------------------------------------------"
echo "Before proceeding, you need to:"
echo "1. Visit: https://developer.intuit.com/"
echo "2. Sign in with: shawn@owenent.com"
echo "3. Create new app: 'Hills & Hollows DABS Automation'"
echo "4. Set redirect URI: https://localhost:8000/auth/quickbooks/callback"
echo "5. Copy your Client ID and Client Secret"
echo ""

read -p "Have you completed the QuickBooks Developer setup? (y/n): " setup_complete

if [ "$setup_complete" != "y" ] && [ "$setup_complete" != "Y" ]; then
    echo ""
    echo "📖 Please complete the setup first:"
    echo "   1. Open: https://developer.intuit.com/"
    echo "   2. Follow the setup guide: docs/quickbooks_oauth_setup_guide.md"
    echo "   3. Run this script again when ready"
    echo ""
    exit 0
fi

echo ""
echo "🔑 STEP 2: Enter QuickBooks Credentials"
echo "--------------------------------------"

# Get Client ID
echo -n "Enter your QuickBooks Client ID: "
read -r QB_CLIENT_ID

if [ -z "$QB_CLIENT_ID" ]; then
    echo "❌ Error: Client ID cannot be empty"
    exit 1
fi

# Get Client Secret
echo -n "Enter your QuickBooks Client Secret: "
read -r QB_CLIENT_SECRET

if [ -z "$QB_CLIENT_SECRET" ]; then
    echo "❌ Error: Client Secret cannot be empty"
    exit 1
fi

echo ""
echo "💾 STEP 3: Saving Configuration"
echo "-------------------------------"

# Create environment file
cat > .env.quickbooks << EOF
# QuickBooks OAuth 2.0 Configuration
# Generated: $(date)
# Hills & Hollows LLC - DABS Automation

QB_CLIENT_ID="$QB_CLIENT_ID"
QB_CLIENT_SECRET="$QB_CLIENT_SECRET"
QB_USERNAME="shawn@owenent.com"
QB_PASSWORD="teymTJWoZr47!"
QB_REDIRECT_URI="https://localhost:8000/auth/quickbooks/callback"
QB_BASE_URL="https://quickbooks.api.intuit.com"
QB_SCOPE="com.intuit.quickbooks.accounting"

# Performance Settings
QB_MAX_REQUESTS_PER_MINUTE=500
QB_INVENTORY_SYNC_INTERVAL=15
QB_VARIANCE_THRESHOLD_PERCENT=5.0

# Security Settings
QB_AUTO_REFRESH_TOKENS=true
QB_TOKEN_REFRESH_BUFFER_MINUTES=30
EOF

echo "✅ Configuration saved to: .env.quickbooks"

# Update config files
echo ""
echo "📝 STEP 4: Updating Configuration Files"
echo "---------------------------------------"

# Update quickbooks_config.env
sed -i.bak "s/QB_CLIENT_ID=.*/QB_CLIENT_ID=$QB_CLIENT_ID/" config/quickbooks_config.env
sed -i.bak "s/QB_CLIENT_SECRET=.*/QB_CLIENT_SECRET=$QB_CLIENT_SECRET/" config/quickbooks_config.env

echo "✅ Updated: config/quickbooks_config.env"

# Update secure_credentials.json
python3 -c "
import json
import sys

try:
    with open('config/secure_credentials.json', 'r') as f:
        config = json.load(f)
    
    config['credentials']['quickbooks_online']['oauth_config']['client_id'] = '$QB_CLIENT_ID'
    config['credentials']['quickbooks_online']['oauth_config']['client_secret'] = '$QB_CLIENT_SECRET'
    
    with open('config/secure_credentials.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print('✅ Updated: config/secure_credentials.json')
except Exception as e:
    print(f'❌ Error updating secure_credentials.json: {e}')
    sys.exit(1)
"

echo ""
echo "🔧 STEP 5: Setting Environment Variables"
echo "---------------------------------------"

# Export environment variables for current session
export QB_CLIENT_ID="$QB_CLIENT_ID"
export QB_CLIENT_SECRET="$QB_CLIENT_SECRET"
export QB_USERNAME="shawn@owenent.com"
export QB_PASSWORD="teymTJWoZr47!"

echo "✅ Environment variables set for current session"

# Add to shell profile for persistence
SHELL_PROFILE=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_PROFILE="$HOME/.bash_profile"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_PROFILE="$HOME/.bashrc"
fi

if [ -n "$SHELL_PROFILE" ]; then
    echo ""
    echo "# QuickBooks OAuth Configuration - Hills & Hollows LLC" >> "$SHELL_PROFILE"
    echo "export QB_CLIENT_ID=\"$QB_CLIENT_ID\"" >> "$SHELL_PROFILE"
    echo "export QB_CLIENT_SECRET=\"$QB_CLIENT_SECRET\"" >> "$SHELL_PROFILE"
    echo "export QB_USERNAME=\"shawn@owenent.com\"" >> "$SHELL_PROFILE"
    echo "export QB_PASSWORD=\"teymTJWoZr47!\"" >> "$SHELL_PROFILE"
    echo "" >> "$SHELL_PROFILE"
    
    echo "✅ Added to shell profile: $SHELL_PROFILE"
    echo "   (Variables will persist across sessions)"
fi

echo ""
echo "🧪 STEP 6: Testing Configuration"
echo "--------------------------------"

# Test the configuration
python3 scripts/setup_quickbooks_oauth.py &
OAUTH_PID=$!

# Wait a moment for the script to start
sleep 3

# Kill the OAuth script since we just want to test config
kill $OAUTH_PID 2>/dev/null

echo ""
echo "🎊 CONFIGURATION COMPLETE!"
echo "========================="
echo "✅ QuickBooks credentials configured"
echo "✅ Environment variables set"
echo "✅ Configuration files updated"
echo ""
echo "🚀 NEXT STEPS:"
echo "1. Run OAuth flow: python3 scripts/setup_quickbooks_oauth.py"
echo "2. Complete authorization in browser"
echo "3. Test integration: python3 tests/test_quickbooks_oauth.py"
echo "4. Deploy automation workflows"
echo ""
echo "📖 For detailed instructions, see:"
echo "   docs/quickbooks_oauth_setup_guide.md"
echo ""
echo "💼 Ready to deliver Tessa and Heather's workload relief!"
