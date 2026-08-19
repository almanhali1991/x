"""
X Authentication Manager - OAuth 2.0 authentication for X API
Handles token management, refresh, and multi-account support
"""

import os
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
import base64

logger = logging.getLogger(__name__)

class XAuthManager:
    """
    Manages OAuth 2.0 authentication for X API
    Supports multiple authentication flows and account switching
    """
    
    AUTH_URL = "https://api.twitter.com/oauth2/token"
    
    def __init__(self):
        self.accounts: Dict[str, Dict[str, Any]] = {}
        self.active_account: Optional[str] = None
        self.token_cache: Dict[str, Dict[str, Any]] = {}
        
    def add_account(
        self,
        account_id: str,
        api_key: str,
        api_secret: str,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        bearer_token: Optional[str] = None
    ):
        """
        Add an X account for authentication
        
        Args:
            account_id: Unique identifier for this account
            api_key: X API Key
            api_secret: X API Secret
            access_token: User access token (for OAuth 1.0a)
            access_token_secret: User access token secret
            bearer_token: Pre-generated bearer token
        """
        self.accounts[account_id] = {
            "api_key": api_key,
            "api_secret": api_secret,
            "access_token": access_token,
            "access_token_secret": access_token_secret,
            "bearer_token": bearer_token,
            "added_at": datetime.utcnow().isoformat()
        }
        
        if not self.active_account:
            self.active_account = account_id
        
        logger.info(f"Account {account_id} added successfully")
    
    def set_active_account(self, account_id: str):
        """Switch to a different account"""
        if account_id not in self.accounts:
            raise ValueError(f"Account {account_id} not found")
        
        self.active_account = account_id
        logger.info(f"Switched to account {account_id}")
    
    def get_active_credentials(self) -> Dict[str, Any]:
        """Get credentials for active account"""
        if not self.active_account:
            raise ValueError("No active account selected")
        
        return self.accounts[self.active_account]
    
    async def get_bearer_token(self, account_id: Optional[str] = None) -> str:
        """
        Get or generate bearer token for account
        
        Args:
            account_id: Account ID (uses active if not specified)
            
        Returns:
            Valid bearer token
        """
        account_id = account_id or self.active_account
        if not account_id:
            raise ValueError("No account specified")
        
        # Check cache first
        if account_id in self.token_cache:
            cached = self.token_cache[account_id]
            if not self._is_token_expired(cached):
                logger.debug(f"Using cached bearer token for {account_id}")
                return cached["token"]
        
        # Generate new bearer token
        account = self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        if account.get("bearer_token"):
            # Use pre-existing bearer token
            token = account["bearer_token"]
        else:
            # Generate from API key/secret
            token = await self._generate_bearer_token(
                account["api_key"],
                account["api_secret"]
            )
        
        # Cache the token
        self.token_cache[account_id] = {
            "token": token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24)  # Bearer tokens don't expire but we refresh periodically
        }
        
        return token
    
    async def _generate_bearer_token(self, api_key: str, api_secret: str) -> str:
        """Generate bearer token from API key and secret"""
        import aiohttp
        
        key_secret = f"{api_key}:{api_secret}"
        encoded = base64.b64encode(key_secret.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }
        
        data = {"grant_type": "client_credentials"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.AUTH_URL, headers=headers, data=data) as response:
                    result = await response.json()
                    
                    if response.status != 200:
                        logger.error(f"Failed to get bearer token: {result}")
                        raise ValueError(f"Token generation failed: {result}")
                    
                    token = result.get("access_token")
                    logger.info("Bearer token generated successfully")
                    return token
                    
        except Exception as e:
            logger.error(f"Error generating bearer token: {e}")
            # Fallback to environment variable
            return os.getenv("X_BEARER_TOKEN", "")
    
    def _is_token_expired(self, cached: Dict[str, Any]) -> bool:
        """Check if cached token is expired"""
        if "expires_at" not in cached:
            return False
        return datetime.utcnow() > cached["expires_at"]
    
    async def refresh_tokens(self, account_id: Optional[str] = None):
        """Refresh bearer tokens for account"""
        account_id = account_id or self.active_account
        if account_id and account_id in self.token_cache:
            del self.token_cache[account_id]
            logger.info(f"Token cache cleared for {account_id}")
            
            # Generate new token
            await self.get_bearer_token(account_id)
    
    def list_accounts(self) -> List[Dict[str, Any]]:
        """List all configured accounts"""
        return [
            {
                "account_id": acc_id,
                "active": acc_id == self.active_account,
                "has_bearer_token": bool(acc.get("bearer_token")),
                "has_oauth_tokens": bool(acc.get("access_token") and acc.get("access_token_secret")),
                "added_at": acc.get("added_at")
            }
            for acc_id, acc in self.accounts.items()
        ]
    
    def remove_account(self, account_id: str):
        """Remove an account"""
        if account_id in self.accounts:
            del self.accounts[account_id]
        
        if account_id in self.token_cache:
            del self.token_cache[account_id]
        
        if self.active_account == account_id:
            self.active_account = next(iter(self.accounts.keys()), None)
        
        logger.info(f"Account {account_id} removed")
    
    def export_account_config(self, account_id: str) -> Dict[str, Any]:
        """Export account configuration (without secrets)"""
        if account_id not in self.accounts:
            raise ValueError(f"Account {account_id} not found")
        
        account = self.accounts[account_id]
        return {
            "account_id": account_id,
            "has_api_key": bool(account.get("api_key")),
            "has_bearer_token": bool(account.get("bearer_token")),
            "has_oauth_tokens": bool(account.get("access_token")),
            "added_at": account.get("added_at")
        }
    
    @classmethod
    def from_environment(cls, account_id: str = "default") -> 'XAuthManager':
        """Create auth manager from environment variables"""
        manager = cls()
        
        api_key = os.getenv("X_API_KEY")
        api_secret = os.getenv("X_API_SECRET")
        access_token = os.getenv("X_ACCESS_TOKEN")
        access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
        bearer_token = os.getenv("X_BEARER_TOKEN")
        
        if api_key and api_secret:
            manager.add_account(
                account_id=account_id,
                api_key=api_key,
                api_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                bearer_token=bearer_token
            )
        
        return manager
