#!/usr/bin/env python3
"""
QuickBooks OAuth 2.0 Local Server
Simple HTTP server to handle OAuth callback for QuickBooks integration

This server:
1. Starts a local server on port 8000
2. Handles the OAuth callback from QuickBooks
3. Extracts authorization code and company ID
4. Exchanges code for tokens
5. Saves tokens securely

Author: DABS Automation System
Created: 2025-08-22
"""

import asyncio
import json
import os
import sys
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
import webbrowser

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from automation.workflows.quickbooks_integration.qb_oauth_manager import QuickBooksOAuthManager

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback"""
    
    def do_GET(self):
        """Handle GET request from QuickBooks OAuth callback"""
        
        # Parse the callback URL
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # Extract authorization code and company ID
        auth_code = query_params.get('code', [None])[0]
        company_id = query_params.get('realmId', [None])[0]
        state = query_params.get('state', [None])[0]
        error = query_params.get('error', [None])[0]
        
        if error:
            self.send_error_response(f"OAuth Error: {error}")
            return
            
        if not auth_code or not company_id:
            self.send_error_response("Missing authorization code or company ID")
            return
            
        # Store the results for the main process
        self.server.auth_code = auth_code
        self.server.company_id = company_id
        self.server.state = state
        
        # Send success response
        self.send_success_response(auth_code, company_id)
        
        # Signal that we're done
        self.server.callback_received = True
    
    def send_success_response(self, auth_code, company_id):
        """Send success response to browser"""
        
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>QuickBooks OAuth Success</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .success {{ color: #28a745; font-size: 24px; margin-bottom: 20px; }}
                .info {{ background-color: #e9ecef; padding: 15px; border-radius: 4px; margin: 10px 0; }}
                .code {{ font-family: monospace; background-color: #f8f9fa; padding: 10px; border-radius: 4px; word-break: break-all; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="success">✅ QuickBooks OAuth Authorization Successful!</h1>
                
                <div class="info">
                    <h3>Authorization Details:</h3>
                    <p><strong>Company ID:</strong> <span class="code">{company_id}</span></p>
                    <p><strong>Authorization Code:</strong> <span class="code">{auth_code[:20]}...</span></p>
                </div>
                
                <div class="info">
                    <h3>Next Steps:</h3>
                    <ol>
                        <li>The authorization code has been captured automatically</li>
                        <li>Token exchange will begin shortly</li>
                        <li>You can close this browser window</li>
                        <li>Return to your terminal to see the results</li>
                    </ol>
                </div>
                
                <p><em>Hills & Hollows LLC - DABS Automation System</em></p>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_response.encode())
    
    def send_error_response(self, error_message):
        """Send error response to browser"""
        
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>QuickBooks OAuth Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .error {{ color: #dc3545; font-size: 24px; margin-bottom: 20px; }}
                .info {{ background-color: #f8d7da; padding: 15px; border-radius: 4px; margin: 10px 0; border: 1px solid #f5c6cb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error">❌ QuickBooks OAuth Error</h1>
                
                <div class="info">
                    <h3>Error Details:</h3>
                    <p>{error_message}</p>
                </div>
                
                <div class="info">
                    <h3>Troubleshooting:</h3>
                    <ol>
                        <li>Check that the redirect URI is correctly configured in your QuickBooks app</li>
                        <li>Ensure the app has the correct scopes enabled</li>
                        <li>Verify your Client ID and Client Secret are correct</li>
                        <li>Try the authorization process again</li>
                    </ol>
                </div>
                
                <p><em>Hills & Hollows LLC - DABS Automation System</em></p>
            </div>
        </body>
        </html>
        """
        
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_response.encode())
    
    def log_message(self, format, *args):
        """Suppress default HTTP server logging"""
        pass

class QuickBooksOAuthServer:
    """OAuth server for QuickBooks integration"""
    
    def __init__(self, port=8000):
        self.port = port
        self.oauth_manager = QuickBooksOAuthManager()
        self.server = None
        
    async def start_oauth_flow(self):
        """Start the complete OAuth flow"""
        
        print("🚀 QUICKBOOKS OAUTH 2.0 SETUP")
        print("=" * 50)
        print("Hills & Hollows LLC - DABS Automation")
        print()
        
        # Check existing tokens first
        existing_tokens = await self.oauth_manager.load_tokens()
        if existing_tokens and not existing_tokens.is_expired:
            print("✅ Valid tokens already exist!")
            print(f"   Company ID: {existing_tokens.company_id}")
            print(f"   Expires: {existing_tokens.expires_at}")
            
            # Test the tokens
            try:
                access_token = await self.oauth_manager.get_valid_access_token()
                print("✅ Tokens are working correctly")
                return True
            except Exception as e:
                print(f"⚠️  Token validation failed: {e}")
                print("   Proceeding with re-authorization...")
        
        # Start local server
        print(f"🌐 Starting local OAuth server on port {self.port}...")
        
        try:
            # Create server
            self.server = HTTPServer(('localhost', self.port), OAuthCallbackHandler)
            self.server.callback_received = False
            self.server.auth_code = None
            self.server.company_id = None
            self.server.state = None
            
            # Start server in background thread
            server_thread = Thread(target=self.server.serve_forever, daemon=True)
            server_thread.start()
            
            print(f"✅ Server started at http://localhost:{self.port}")
            
            # Generate authorization URL
            auth_url = self.oauth_manager.generate_authorization_url()
            
            print("\n🔗 Opening QuickBooks authorization in your browser...")
            print(f"   URL: {auth_url}")
            
            # Open browser automatically
            webbrowser.open(auth_url)
            
            print("\n📋 Please complete the following steps:")
            print("   1. Sign in to QuickBooks Online")
            print("   2. Select your company: Hills & Hollows LLC")
            print("   3. Authorize the application")
            print("   4. Wait for automatic redirect...")
            
            # Wait for callback
            print("\n⏳ Waiting for authorization callback...")
            
            timeout = 300  # 5 minutes
            elapsed = 0
            
            while not self.server.callback_received and elapsed < timeout:
                await asyncio.sleep(1)
                elapsed += 1
                
                if elapsed % 30 == 0:  # Progress update every 30 seconds
                    print(f"   Still waiting... ({elapsed}s elapsed)")
            
            if not self.server.callback_received:
                print("❌ Timeout waiting for authorization callback")
                return False
            
            # Process the callback
            print("✅ Authorization callback received!")
            print(f"   Company ID: {self.server.company_id}")
            
            # Exchange code for tokens
            print("🔄 Exchanging authorization code for tokens...")
            
            try:
                tokens = await self.oauth_manager.exchange_code_for_tokens(
                    self.server.auth_code, 
                    self.server.company_id
                )
                
                print("✅ Tokens obtained successfully!")
                print(f"   Access Token: {tokens.access_token[:20]}...")
                print(f"   Expires: {tokens.expires_at}")
                print(f"   Company ID: {tokens.company_id}")
                
                # Test the new tokens
                print("\n🧪 Testing API connectivity...")
                access_token = await self.oauth_manager.get_valid_access_token()
                print("✅ API connectivity test passed!")
                
                print("\n🎯 QuickBooks OAuth setup complete!")
                print("   Ready for DABS automation integration")
                
                return True
                
            except Exception as e:
                print(f"❌ Token exchange failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Server startup failed: {e}")
            return False
            
        finally:
            if self.server:
                self.server.shutdown()
                print("🛑 OAuth server stopped")

async def main():
    """Main execution function"""
    
    # Check environment
    client_id = os.getenv('QB_CLIENT_ID')
    client_secret = os.getenv('QB_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Missing QuickBooks OAuth credentials")
        print("   Please set QB_CLIENT_ID and QB_CLIENT_SECRET environment variables")
        return
    
    print(f"🔑 Using Client ID: {client_id[:20]}...")
    
    # Start OAuth flow
    oauth_server = QuickBooksOAuthServer()
    success = await oauth_server.start_oauth_flow()
    
    if success:
        print("\n✅ SUCCESS: QuickBooks OAuth 2.0 setup complete!")
    else:
        print("\n❌ FAILED: QuickBooks OAuth 2.0 setup failed")

if __name__ == "__main__":
    asyncio.run(main())
