#!/usr/bin/env python3
"""
Switch QuickBooks Configuration to Sandbox
==========================================

Switch from production to sandbox environment for safe development testing.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

def switch_to_sandbox():
    """Switch QuickBooks configuration to sandbox environment"""
    
    print("🧪 SWITCHING TO QUICKBOOKS SANDBOX")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    
    # Load current environment
    load_dotenv(project_root / '.env')
    load_dotenv(project_root / 'config/quickbooks_config.env')
    
    # Current configuration
    current_base_url = os.getenv('QB_BASE_URL', 'https://quickbooks.api.intuit.com')
    client_id = os.getenv('QB_CLIENT_ID')
    
    print("📋 Current Configuration:")
    print("-" * 30)
    print(f"   🌐 Base URL: {current_base_url}")
    print(f"   🔑 Client ID: {client_id}")
    
    if 'sandbox' in current_base_url.lower():
        print("   ✅ Already using sandbox environment")
        return
    else:
        print("   🏭 Currently using production environment")
    
    print()
    
    # Update environment files
    print("🔧 Updating Configuration Files:")
    print("-" * 30)
    
    # 1. Update .env file
    env_file = project_root / '.env'
    if env_file.exists():
        print("   📝 Updating .env file...")
        
        # Read current content
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Replace production URL with sandbox URL
        updated_content = content.replace(
            'QB_BASE_URL=https://quickbooks.api.intuit.com',
            'QB_BASE_URL=https://sandbox-quickbooks.api.intuit.com'
        )
        
        # Add sandbox URL if not present
        if 'QB_BASE_URL=' not in updated_content:
            updated_content += '\nQB_BASE_URL=https://sandbox-quickbooks.api.intuit.com\n'
        
        # Write updated content
        with open(env_file, 'w') as f:
            f.write(updated_content)
        
        print("   ✅ .env file updated")
    
    # 2. Update quickbooks_config.env
    config_file = project_root / 'config/quickbooks_config.env'
    if config_file.exists():
        print("   📝 Updating quickbooks_config.env...")
        
        # Read current content
        with open(config_file, 'r') as f:
            lines = f.readlines()
        
        # Update lines
        updated_lines = []
        base_url_updated = False
        
        for line in lines:
            if line.startswith('QB_BASE_URL='):
                updated_lines.append('QB_BASE_URL=https://sandbox-quickbooks.api.intuit.com\n')
                base_url_updated = True
            elif line.startswith('QB_SANDBOX_BASE_URL='):
                # Update sandbox URL too
                updated_lines.append('QB_SANDBOX_BASE_URL=https://sandbox-quickbooks.api.intuit.com\n')
            else:
                updated_lines.append(line)
        
        # Add base URL if not found
        if not base_url_updated:
            updated_lines.append('QB_BASE_URL=https://sandbox-quickbooks.api.intuit.com\n')
        
        # Write updated content
        with open(config_file, 'w') as f:
            f.writelines(updated_lines)
        
        print("   ✅ quickbooks_config.env updated")
    
    # 3. Update secure_credentials.json
    creds_file = project_root / 'config/secure_credentials.json'
    if creds_file.exists():
        print("   📝 Updating secure_credentials.json...")
        
        try:
            with open(creds_file, 'r') as f:
                creds_data = json.load(f)
            
            # Update base URL in credentials
            if 'credentials' in creds_data and 'quickbooks_online' in creds_data['credentials']:
                qb_config = creds_data['credentials']['quickbooks_online']
                if 'api_settings' in qb_config:
                    qb_config['api_settings']['base_url'] = 'https://sandbox-quickbooks.api.intuit.com'
                else:
                    qb_config['api_settings'] = {
                        'base_url': 'https://sandbox-quickbooks.api.intuit.com',
                        'rate_limit': 500,
                        'timeout_seconds': 30
                    }
            
            # Write updated credentials
            with open(creds_file, 'w') as f:
                json.dump(creds_data, f, indent=2)
            
            print("   ✅ secure_credentials.json updated")
            
        except Exception as e:
            print(f"   ⚠️  Could not update secure_credentials.json: {e}")
    
    print()
    
    # Clear existing tokens (they're for production)
    print("🗑️  Clearing Production Tokens:")
    print("-" * 30)
    
    tokens_file = project_root / 'config/qb_tokens.json'
    if tokens_file.exists():
        tokens_file.unlink()
        print("   ✅ Production tokens cleared")
    else:
        print("   ℹ️  No existing tokens to clear")
    
    print()
    
    # Show next steps
    print("🎯 NEXT STEPS:")
    print("-" * 30)
    print("   1. ✅ Configuration updated for sandbox")
    print("   2. 🧪 Create sandbox company in developer dashboard:")
    print("      - Go to: https://developer.intuit.com/")
    print("      - Navigate: My Hub → Sandboxes")
    print("      - Click: Add → QuickBooks Online Plus")
    print("      - Select: United States")
    print("      - Click: Create")
    print()
    print("   3. 🔐 Run OAuth setup for sandbox:")
    print("      python3 scripts/setup_quickbooks_oauth.py")
    print()
    print("   4. 🧪 Test sandbox connection:")
    print("      python3 scripts/test_quickbooks_connection.py")
    
    print()
    
    # Show updated configuration
    print("📋 UPDATED CONFIGURATION:")
    print("-" * 30)
    print("   🌐 Base URL: https://sandbox-quickbooks.api.intuit.com")
    print("   🧪 Environment: SANDBOX")
    print("   🔑 Client ID: (unchanged)")
    print("   🔒 Client Secret: (unchanged)")
    print("   🔄 Redirect URI: (unchanged)")
    print("   📊 Data: Sample/test data only")
    
    print()
    print("✅ SANDBOX CONFIGURATION COMPLETE!")
    print("🎯 Ready for safe development testing")

if __name__ == "__main__":
    switch_to_sandbox()
