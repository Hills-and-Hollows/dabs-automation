#!/usr/bin/env python3
"""
Environment Debug Script
========================

Debug environment variables and configuration loading.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def debug_environment():
    """Debug environment variables and configuration"""
    
    print("🔍 ENVIRONMENT CONFIGURATION DEBUG")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Environment Variables:")
    print("-" * 30)
    
    env_vars = [
        'QB_CLIENT_ID',
        'QB_CLIENT_SECRET', 
        'QB_USERNAME',
        'QB_PASSWORD',
        'QB_REDIRECT_URI',
        'QB_BASE_URL',
        'QB_SCOPE'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'SECRET' in var or 'PASSWORD' in var:
                print(f"   ✅ {var}: {value[:10]}... (hidden)")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: NOT SET")
    
    print()
    
    # Check configuration files
    print("📁 Configuration Files:")
    print("-" * 30)
    
    config_files = [
        'config/quickbooks_config.env',
        'config/secure_credentials.json',
        '.env',
        '.env.quickbooks'
    ]
    
    for file_path in config_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}: EXISTS")
            
            # Show first few lines if it's an env file
            if file_path.endswith('.env'):
                try:
                    with open(full_path, 'r') as f:
                        lines = f.readlines()[:5]
                    print(f"      📄 First 5 lines:")
                    for line in lines:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            if 'SECRET' in key or 'PASSWORD' in key:
                                print(f"         {key}={value[:10]}... (hidden)")
                            else:
                                print(f"         {key}={value.strip()}")
                except:
                    print(f"      ⚠️  Could not read file")
        else:
            print(f"   ❌ {file_path}: NOT FOUND")
    
    print()
    
    # Check if dotenv is loading
    print("🔧 Environment Loading:")
    print("-" * 30)
    
    try:
        from dotenv import load_dotenv
        
        # Try loading different env files
        env_files = ['.env', '.env.quickbooks', 'config/quickbooks_config.env']
        
        for env_file in env_files:
            full_path = project_root / env_file
            if full_path.exists():
                print(f"   📂 Loading {env_file}...")
                load_dotenv(full_path)
                
                # Check if QB_CLIENT_ID is now set
                client_id = os.getenv('QB_CLIENT_ID')
                if client_id:
                    print(f"      ✅ QB_CLIENT_ID loaded: {client_id[:20]}...")
                else:
                    print(f"      ❌ QB_CLIENT_ID still not set")
            else:
                print(f"   ⚠️  {env_file} not found")
                
    except ImportError:
        print("   ⚠️  python-dotenv not available")
    
    print()
    
    # Final check
    print("🎯 Final Environment State:")
    print("-" * 30)
    
    client_id = os.getenv('QB_CLIENT_ID')
    client_secret = os.getenv('QB_CLIENT_SECRET')
    
    if client_id and client_secret:
        print(f"   ✅ OAuth credentials available")
        print(f"   🔑 Client ID: {client_id}")
        print(f"   🔒 Client Secret: {client_secret[:10]}...")
        
        # Check if these match the expected values from config
        expected_client_id = "AB1HJvz2KjreJxLEhZCV2KwNE2jU8V84nnE4EoITbsj2jzy8SF"
        if client_id == expected_client_id:
            print("   ✅ Client ID matches configuration")
        else:
            print("   ⚠️  Client ID does NOT match configuration")
            print(f"      Expected: {expected_client_id}")
            print(f"      Actual:   {client_id}")
    else:
        print("   ❌ OAuth credentials missing")

if __name__ == "__main__":
    debug_environment()
