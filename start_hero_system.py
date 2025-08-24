#!/usr/bin/env python3
"""
DABS Hero System Launcher
Double-click this file to start being awesome!

This script will:
1. Check if all dependencies are installed
2. Create necessary directories
3. Launch the hero dashboard
4. Make managers' lives easy!
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python():
    """Check if Python is installed and version is adequate"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    else:
        print(f"✅ Python {version.major}.{version.minor} detected")
        return True

def install_requirements():
    """Install required packages"""
    print("🔧 Installing required packages...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def setup_directories():
    """Create necessary directories"""
    print("📁 Setting up directories...")
    
    directories = [
        "data",
        "exports", 
        "logs",
        "data/dabs_backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   ✅ {directory}/")
    
    print("✅ Directory structure ready!")

def check_dabs_file():
    """Check if DABS file exists"""
    dabs_file = Path("DABS Price Changes.xlsx")
    if dabs_file.exists():
        print(f"✅ DABS file found: {dabs_file.name}")
        return True
    else:
        print("⚠️ No DABS file found - you can upload one through the dashboard")
        return False

def launch_dashboard():
    """Launch the hero dashboard"""
    print("🚀 Launching DABS Hero Dashboard...")
    print("🌟 Your browser should open automatically!")
    print("📱 If not, go to: http://localhost:8501")
    print()
    print("=" * 50)
    print("🍾 WELCOME TO HERO MODE! 🍾")
    print("=" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "hero_dashboard.py",
            "--server.port", "8501",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Hero dashboard stopped. Thanks for being awesome!")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        print("💡 Try running manually: streamlit run hero_dashboard.py")

def main():
    """Main launcher function"""
    print("🍾 DABS Hero System Launcher")
    print("=" * 40)
    print("🦸‍♂️ Preparing to make you a hero...")
    print()
    
    # Step 1: Check Python
    if not check_python():
        input("Press Enter to exit...")
        return
    
    # Step 2: Install requirements
    if not install_requirements():
        input("Press Enter to exit...")
        return
    
    # Step 3: Setup directories
    setup_directories()
    
    # Step 4: Check for DABS file
    check_dabs_file()
    
    # Step 5: Launch dashboard
    print("\n🚀 Ready to launch!")
    print("💫 The hero dashboard will open in your browser")
    print("🎯 Use it to upload DABS files and run automation")
    print()
    
    input("Press Enter to start the hero dashboard... ")
    launch_dashboard()

if __name__ == "__main__":
    main() 