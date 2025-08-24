#!/usr/bin/env python3
"""
DABS Archon Setup Script
Automated setup for Archon MCP Server in DABS workspace
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional

class DABSArchonSetup:
    def __init__(self):
        self.archon_dir = Path(__file__).parent
        self.env_file = self.archon_dir / ".env"
        self.docker_compose = self.archon_dir / "docker-compose.yml"
        
    def check_prerequisites(self) -> bool:
        """Check if required tools are installed"""
        print("🔍 Checking prerequisites...")
        
        # Check Docker
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            print("✅ Docker is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker is not installed or not in PATH")
            print("   Please install Docker Desktop: https://www.docker.com/products/docker-desktop/")
            return False
            
        # Check Docker Compose
        try:
            subprocess.run(["docker-compose", "--version"], capture_output=True, check=True)
            print("✅ Docker Compose is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker Compose is not available")
            return False
            
        return True
    
    def setup_environment(self) -> bool:
        """Interactive environment setup"""
        print("\n🔧 Setting up environment configuration...")
        
        if not self.env_file.exists():
            print("❌ .env file not found. Please copy .env.example to .env first")
            return False
            
        # Read current .env
        env_content = self.env_file.read_text()
        
        print("\n📝 Please provide the following information:")
        print("   (You can get these from your Supabase project settings)")
        
        # Get Supabase URL
        supabase_url = input("\n🔗 Supabase Project URL (https://your-project.supabase.co): ").strip()
        if not supabase_url:
            print("❌ Supabase URL is required")
            return False
            
        # Get Supabase Service Key
        print("\n🔑 Supabase Service Role Key:")
        print("   ⚠️  IMPORTANT: Use the SERVICE ROLE key, NOT the anon key!")
        print("   📍 Find it in: Project Settings → API → Project API keys → service_role")
        service_key = input("   Enter service_role key: ").strip()
        if not service_key:
            print("❌ Supabase service key is required")
            return False
            
        # Update .env file
        env_content = env_content.replace("SUPABASE_URL=", f"SUPABASE_URL={supabase_url}")
        env_content = env_content.replace("SUPABASE_SERVICE_KEY=", f"SUPABASE_SERVICE_KEY={service_key}")
        
        self.env_file.write_text(env_content)
        print("✅ Environment configuration updated")
        
        return True
    
    def check_ports(self) -> bool:
        """Check if required ports are available"""
        print("\n🔌 Checking port availability...")
        
        ports = [3837, 8281, 8151, 8152]  # Custom DABS ports
        
        for port in ports:
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    print(f"⚠️  Port {port} is already in use")
                    print(f"   Please stop the service using port {port} or modify the port in .env")
                    return False
                else:
                    print(f"✅ Port {port} is available")
            except Exception as e:
                print(f"⚠️  Could not check port {port}: {e}")
                
        return True
    
    def start_services(self) -> bool:
        """Start Archon services with Docker Compose"""
        print("\n🚀 Starting Archon services...")
        
        try:
            # Build and start services
            cmd = ["docker-compose", "up", "--build", "-d"]
            result = subprocess.run(cmd, cwd=self.archon_dir, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Failed to start services:")
                print(result.stderr)
                return False
                
            print("✅ Services started successfully")
            print("\n📊 Service URLs:")
            print("   🖥️  Archon UI: http://localhost:3837")
            print("   🔧 Archon Server: http://localhost:8281")
            print("   🤖 Archon MCP: http://localhost:8151")
            print("   ⚡ Archon Agents: http://localhost:8152")
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting services: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """Verify that services are running correctly"""
        print("\n🔍 Verifying installation...")
        
        import time
        import urllib.request
        
        # Wait for services to start
        print("⏳ Waiting for services to start (30 seconds)...")
        time.sleep(30)
        
        # Check each service
        services = {
            "Archon UI": "http://localhost:3837",
            "Archon Server": "http://localhost:8281/health",
            "Archon MCP": "http://localhost:8151"
        }
        
        all_healthy = True
        for name, url in services.items():
            try:
                response = urllib.request.urlopen(url, timeout=10)
                if response.status == 200:
                    print(f"✅ {name} is running")
                else:
                    print(f"⚠️  {name} returned status {response.status}")
                    all_healthy = False
            except Exception as e:
                print(f"❌ {name} is not responding: {e}")
                all_healthy = False
                
        return all_healthy
    
    def show_next_steps(self):
        """Display next steps for the user"""
        print("\n🎉 Archon MCP Server setup complete!")
        print("\n📋 Next Steps:")
        print("1. 🌐 Open Archon UI: http://localhost:3837")
        print("2. ⚙️  Go to Settings and add your OpenAI API key")
        print("3. 📚 Upload DABS documentation to the knowledge base")
        print("4. 🤖 Configure your AI coding assistant with MCP server:")
        print("   📍 MCP Server URL: http://localhost:8151")
        print("   🔄 Transport: SSE (Server-Sent Events)")
        print("\n📖 For detailed instructions, see: DABS_SETUP_GUIDE.md")
    
    def run_setup(self):
        """Run the complete setup process"""
        print("🏗️  DABS Archon MCP Server Setup")
        print("=" * 50)
        
        if not self.check_prerequisites():
            sys.exit(1)
            
        if not self.setup_environment():
            sys.exit(1)
            
        if not self.check_ports():
            print("\n💡 Tip: You can modify ports in the .env file if needed")
            sys.exit(1)
            
        if not self.start_services():
            sys.exit(1)
            
        if not self.verify_installation():
            print("\n⚠️  Some services may not be fully ready yet.")
            print("   Please wait a few more minutes and check the URLs manually.")
            
        self.show_next_steps()

if __name__ == "__main__":
    setup = DABSArchonSetup()
    setup.run_setup()
