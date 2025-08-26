#!/usr/bin/env python3
"""
Update restaurant portal to use official DABS catalog

This script updates the restaurant portal HTML to load from the official DABS catalog
instead of the demo catalog.
"""

import re
from pathlib import Path

def update_restaurant_portal():
    """Update restaurant portal to use official DABS catalog"""
    
    portal_path = Path('archon-mcp/archon-ui-main/public/src/web_portal/restaurant_portal_with_catalog.html')
    
    if not portal_path.exists():
        print(f"❌ Restaurant portal not found: {portal_path}")
        return False
    
    # Read the current file
    with open(portal_path, 'r') as f:
        content = f.read()
    
    # Update catalog references
    updates = [
        # Update fetch URLs to use official catalog
        (r'fetch\(\'/src/web_portal/full_dabs_catalog\.json\'\)', 
         "fetch('/src/web_portal/official_dabs_catalog.json')"),
        
        # Update console log messages
        (r'Loading categories from full DABS catalog\.\.\.', 
         'Loading categories from official DABS catalog...'),
        
        # Update any other references
        (r'full_dabs_catalog\.json', 
         'official_dabs_catalog.json')
    ]
    
    changes_made = 0
    for pattern, replacement in updates:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            changes_made += 1
    
    if changes_made > 0:
        # Write the updated file
        with open(portal_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated restaurant portal with {changes_made} changes")
        print("🔄 Restaurant portal now uses official DABS catalog")
        return True
    else:
        print("ℹ️  No changes needed - portal already configured correctly")
        return True

def main():
    """Main function"""
    print("🔄 Updating restaurant portal to use official DABS catalog...")
    
    success = update_restaurant_portal()
    
    if success:
        print("✅ Restaurant portal update complete!")
        print("📋 Portal now loads from official_dabs_catalog.json")
        print("🚀 Deploy changes to see official DABS products")
    else:
        print("❌ Failed to update restaurant portal")

if __name__ == "__main__":
    main()
