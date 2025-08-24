"""
DABS OAuth 2.0 Client Implementation
Hills & Hollows LLC - Utah Package Agency
Date: August 23, 2025

This module provides OAuth 2.0 authentication capabilities for DABS integration,
including token management, refresh, and secure credential handling.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import aiohttp
import base64
from urllib.parse import urlencode, parse_qs, urlparse
from dataclasses import dataclass
from dotenv import load_dotenv

# Load DABS environment configuration
config_path = Path(__file__).parent.parent.parent / "config" / "dabs_ordering.env"
load_dotenv(config_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OAuthTokens:
    """OAuth 2.0 token container"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: Optional[str] = None
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    @property
    def is_expired(self) -> bool:
        """Check if access token is expired"""
        if not self.created_at or not self.expires_in:
            return True
        return time.time() > (self.created_at + self.expires_in - 300)  # 5 min buffer
    
    @property
    def expires_at(self) -> datetime:
        """Get expiration datetime"""
        return datetime.fromtimestamp(self.created_at + self.expires_in)

class DABSOAuthClient:
    """
    OAuth 2.0 client for DABS Licensee Ordering System
    
    Handles authentication, token management, and API access for Utah DABS system
    """
    
    def __init__(self):
        # Load OAuth configuration from environment
        self.client_id = os.getenv("DABS_OAUTH_CLIENT_ID", "dabs_licensee_client")
        self.client_secret = os.getenv("DABS_OAUTH_CLIENT_SECRET")
        self.redirect_uri = os.getenv("DABS_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/dabs/callback")
        
        # DABS OAuth endpoints (hypothetical - DABS uses form auth currently)
        self.auth_url = os.getenv("DABS_OAUTH_AUTH_URL", "https://webapps2.abc.utah.gov/oauth/authorize")
        self.token_url = os.getenv("DABS_OAUTH_TOKEN_URL", "https://webapps2.abc.utah.gov/oauth/token")
        self.api_base_url = os.getenv("DABS_API_BASE_URL", "https://webapps2.abc.utah.gov/api/v1")
        
        # Token storage
        self.token_storage_path = Path("config/dabs_oauth_tokens.json")
        self.current_tokens: Optional[OAuthTokens] = None
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        await self.load_stored_tokens()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def get_authorization_url(self, state: Optional[str] = None, scopes: list = None) -> str:
        """
        Generate OAuth 2.0 authorization URL for DABS
        
        Args:
            state: Optional state parameter for CSRF protection
            scopes: List of requested scopes
            
        Returns:
            str: Authorization URL for user to visit
        """
        if scopes is None:
            scopes = ["orders:read", "orders:write", "inventory:read"]
            
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
        }
        
        if state:
            params["state"] = state
            
        auth_url = f"{self.auth_url}?{urlencode(params)}"
        logger.info(f"🔐 Generated DABS OAuth authorization URL: {auth_url}")
        return auth_url
    
    async def exchange_code_for_tokens(self, authorization_code: str, state: Optional[str] = None) -> OAuthTokens:
        """
        Exchange authorization code for access tokens
        
        Args:
            authorization_code: Authorization code from callback
            state: State parameter for validation
            
        Returns:
            OAuthTokens: Token container with access/refresh tokens
        """
        try:
            logger.info("🔄 Exchanging authorization code for tokens...")
            
            token_data = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
            }
            
            # Add client authentication
            auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            async with self.session.post(self.token_url, data=token_data, headers=headers) as response:
                if response.status == 200:
                    token_response = await response.json()
                    
                    tokens = OAuthTokens(
                        access_token=token_response["access_token"],
                        refresh_token=token_response.get("refresh_token"),
                        token_type=token_response.get("token_type", "Bearer"),
                        expires_in=token_response.get("expires_in", 3600),
                        scope=token_response.get("scope")
                    )
                    
                    self.current_tokens = tokens
                    await self.save_tokens(tokens)
                    
                    logger.info("✅ Successfully obtained OAuth tokens")
                    return tokens
                    
                else:
                    error_data = await response.text()
                    raise Exception(f"Token exchange failed: {response.status} - {error_data}")
                    
        except Exception as e:
            logger.error(f"❌ OAuth token exchange error: {str(e)}")
            raise
    
    async def refresh_access_token(self) -> Optional[OAuthTokens]:
        """
        Refresh access token using refresh token
        
        Returns:
            OAuthTokens: Updated token container or None if failed
        """
        if not self.current_tokens or not self.current_tokens.refresh_token:
            logger.warning("⚠️ No refresh token available")
            return None
            
        try:
            logger.info("🔄 Refreshing access token...")
            
            refresh_data = {
                "grant_type": "refresh_token",
                "refresh_token": self.current_tokens.refresh_token,
                "client_id": self.client_id,
            }
            
            auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            async with self.session.post(self.token_url, data=refresh_data, headers=headers) as response:
                if response.status == 200:
                    token_response = await response.json()
                    
                    # Update tokens
                    self.current_tokens.access_token = token_response["access_token"]
                    self.current_tokens.created_at = time.time()
                    self.current_tokens.expires_in = token_response.get("expires_in", 3600)
                    
                    # Update refresh token if provided
                    if "refresh_token" in token_response:
                        self.current_tokens.refresh_token = token_response["refresh_token"]
                    
                    await self.save_tokens(self.current_tokens)
                    
                    logger.info("✅ Successfully refreshed access token")
                    return self.current_tokens
                    
                else:
                    error_data = await response.text()
                    logger.error(f"❌ Token refresh failed: {response.status} - {error_data}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Token refresh error: {str(e)}")
            return None
    
    async def ensure_valid_tokens(self) -> bool:
        """
        Ensure we have valid access tokens, refreshing if necessary
        
        Returns:
            bool: True if valid tokens available, False otherwise
        """
        if not self.current_tokens:
            logger.warning("⚠️ No OAuth tokens available")
            return False
            
        if self.current_tokens.is_expired:
            logger.info("🔄 Access token expired, attempting refresh...")
            refreshed_tokens = await self.refresh_access_token()
            return refreshed_tokens is not None
            
        return True
    
    async def make_authenticated_request(self, method: str, endpoint: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Make authenticated HTTP request to DABS API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to base URL)
            **kwargs: Additional arguments for aiohttp request
            
        Returns:
            aiohttp.ClientResponse: Response object
        """
        if not await self.ensure_valid_tokens():
            raise Exception("No valid OAuth tokens available")
            
        # Add authorization header
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"{self.current_tokens.token_type} {self.current_tokens.access_token}"
        kwargs["headers"] = headers
        
        url = f"{self.api_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        return await self.session.request(method, url, **kwargs)
    
    async def save_tokens(self, tokens: OAuthTokens):
        """Save tokens to secure storage"""
        try:
            token_data = {
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "token_type": tokens.token_type,
                "expires_in": tokens.expires_in,
                "scope": tokens.scope,
                "created_at": tokens.created_at,
            }
            
            # Ensure directory exists
            self.token_storage_path.parent.mkdir(exist_ok=True)
            
            with open(self.token_storage_path, 'w') as f:
                json.dump(token_data, f, indent=2)
                
            # Set restrictive permissions (owner read/write only)
            os.chmod(self.token_storage_path, 0o600)
            
            logger.info("💾 OAuth tokens saved securely")
            
        except Exception as e:
            logger.error(f"❌ Failed to save tokens: {str(e)}")
            raise
    
    async def load_stored_tokens(self) -> Optional[OAuthTokens]:
        """Load tokens from secure storage"""
        try:
            if not self.token_storage_path.exists():
                logger.info("📁 No stored OAuth tokens found")
                return None
                
            with open(self.token_storage_path, 'r') as f:
                token_data = json.load(f)
                
            self.current_tokens = OAuthTokens(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
                scope=token_data.get("scope"),
                created_at=token_data.get("created_at", time.time())
            )
            
            logger.info("📁 Loaded stored OAuth tokens")
            return self.current_tokens
            
        except Exception as e:
            logger.error(f"❌ Failed to load stored tokens: {str(e)}")
            return None
    
    async def revoke_tokens(self):
        """Revoke current tokens"""
        if not self.current_tokens:
            logger.info("ℹ️ No tokens to revoke")
            return
            
        try:
            # Revoke refresh token if available
            if self.current_tokens.refresh_token:
                revoke_data = {
                    "token": self.current_tokens.refresh_token,
                    "token_type_hint": "refresh_token"
                }
                
                auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
                headers = {"Authorization": f"Basic {auth_header}"}
                
                revoke_url = f"{self.token_url.replace('/token', '/revoke')}"
                async with self.session.post(revoke_url, data=revoke_data, headers=headers) as response:
                    if response.status == 200:
                        logger.info("✅ Successfully revoked refresh token")
                    else:
                        logger.warning(f"⚠️ Token revocation response: {response.status}")
            
            # Clear stored tokens
            if self.token_storage_path.exists():
                self.token_storage_path.unlink()
                
            self.current_tokens = None
            logger.info("🗑️ OAuth tokens cleared")
            
        except Exception as e:
            logger.error(f"❌ Token revocation error: {str(e)}")

# Example usage and testing
async def main():
    """Example OAuth flow for DABS"""
    async with DABSOAuthClient() as oauth_client:
        # Step 1: Get authorization URL
        auth_url = oauth_client.get_authorization_url(state="test_state")
        print(f"Visit this URL to authorize: {auth_url}")
        
        # Step 2: User visits URL, authorizes, gets redirected with code
        # In real implementation, this would be handled by web server callback
        # authorization_code = input("Enter authorization code from callback: ")
        
        # Step 3: Exchange code for tokens (simulated)
        # tokens = await oauth_client.exchange_code_for_tokens(authorization_code)
        
        # Step 4: Make authenticated requests
        # response = await oauth_client.make_authenticated_request("GET", "/orders")
        
        print("OAuth client initialized and ready for DABS integration")

if __name__ == "__main__":
    asyncio.run(main())
