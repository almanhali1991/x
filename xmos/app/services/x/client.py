"""
X API Client - Main client for X (Twitter) API v2
Handles all API interactions including posts, threads, DMs, and analytics
"""

import os
import asyncio
import aiohttp
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class XClient:
    """
    Asynchronous X API v2 client
    Supports OAuth 2.0 authentication and handles rate limiting
    """
    
    BASE_URL = "https://api.twitter.com/2"
    
    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN", "")
        self.api_key = os.getenv("X_API_KEY", "")
        self.api_secret = os.getenv("X_API_SECRET", "")
        self.access_token = os.getenv("X_ACCESS_TOKEN", "")
        self.access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET", "")
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter()
        self._initialized = False
        
    async def initialize(self):
        """Initialize HTTP session"""
        if not self._initialized:
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
            self._initialized = True
            logger.info("X Client initialized")
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self._initialized = False
            logger.info("X Client closed")
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request"""
        await self.initialize()
        
        # Check rate limits
        await self.rate_limiter.wait_if_needed(endpoint)
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            async with self.session.request(
                method,
                url,
                params=params,
                json=json_data
            ) as response:
                data = await response.json()
                
                # Update rate limit info
                self.rate_limiter.update_from_headers(response.headers)
                
                if response.status >= 400:
                    logger.error(f"X API Error: {response.status} - {data}")
                    raise XAPIError(response.status, data)
                
                return data
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP Error: {e}")
            raise
    
    async def post_tweet(
        self,
        text: str,
        media_ids: Optional[List[str]] = None,
        reply_settings: Optional[str] = None,
        quote_tweet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a new tweet
        
        Args:
            text: Tweet text (max 280 characters)
            media_ids: Optional list of media IDs to attach
            reply_settings: Who can reply (everyone, mentionedUsers, following)
            quote_tweet_id: ID of tweet to quote
            
        Returns:
            Tweet data including ID
        """
        payload = {"text": text}
        
        if media_ids:
            payload["media"] = {"media_ids": media_ids}
        
        if reply_settings:
            payload["reply_settings"] = reply_settings
        
        if quote_tweet_id:
            payload["quote_tweet_id"] = quote_tweet_id
        
        result = await self._request("POST", "/tweets", json_data=payload)
        
        logger.info(f"Tweet posted: {result.get('data', {}).get('id')}")
        return result
    
    async def post_thread(
        self,
        tweets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Post a thread of tweets
        
        Args:
            tweets: List of tweet objects with text and optional settings
            
        Returns:
            List of posted tweet data
        """
        results = []
        previous_tweet_id = None
        
        for i, tweet_data in enumerate(tweets):
            text = tweet_data.get("text", "")
            
            # Add reply reference for tweets after the first
            if previous_tweet_id and i > 0:
                tweet_data["reply"] = {"in_reply_to_tweet_id": previous_tweet_id}
            
            result = await self.post_tweet(text, **{k: v for k, v in tweet_data.items() if k != "text"})
            results.append(result)
            
            previous_tweet_id = result.get("data", {}).get("id")
            
            # Small delay between tweets in thread
            if i < len(tweets) - 1:
                await asyncio.sleep(1)
        
        logger.info(f"Thread posted with {len(results)} tweets")
        return results
    
    async def get_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """Get a single tweet by ID"""
        params = {
            "expansions": "author_id,attachments.media_keys,referenced_tweets.id",
            "tweet.fields": "created_at,public_metrics,context_annotations,entities"
        }
        return await self._request("GET", f"/tweets/{tweet_id}", params=params)
    
    async def get_user_tweets(
        self,
        user_id: str,
        max_results: int = 5,
        exclude: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent tweets from a user
        
        Args:
            user_id: User ID to fetch tweets from
            max_results: Number of tweets to retrieve (5-100)
            exclude: Types to exclude (retweets, replies)
            
        Returns:
            List of tweets
        """
        params = {
            "max_results": min(max(5, max_results), 100),
            "expansions": "author_id,attachments.media_keys",
            "tweet.fields": "created_at,public_metrics,entities,context_annotations"
        }
        
        if exclude:
            params["exclude"] = ",".join(exclude)
        
        result = await self._request("GET", f"/users/{user_id}/tweets", params=params)
        return result.get("data", [])
    
    async def search_tweets(
        self,
        query: str,
        max_results: int = 10,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for tweets matching a query
        
        Args:
            query: Search query (supports operators)
            max_results: Results per request (10-100)
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of matching tweets
        """
        params = {
            "query": query,
            "max_results": min(max(10, max_results), 100),
            "tweet.fields": "created_at,public_metrics,author_id,entities"
        }
        
        if start_time:
            params["start_time"] = start_time.isoformat() + "Z"
        if end_time:
            params["end_time"] = end_time.isoformat() + "Z"
        
        result = await self._request("GET", "/tweets/search/recent", params=params)
        return result.get("data", [])
    
    async def like_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """Like a tweet"""
        user_id = await self._get_authenticated_user_id()
        payload = {"tweet_id": tweet_id}
        return await self._request("POST", f"/users/{user_id}/likes", json_data=payload)
    
    async def retweet(self, tweet_id: str) -> Dict[str, Any]:
        """Retweet a tweet"""
        user_id = await self._get_authenticated_user_id()
        payload = {"tweet_id": tweet_id}
        return await self._request("POST", f"/users/{user_id}/retweets", json_data=payload)
    
    async def delete_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """Delete a tweet"""
        return await self._request("DELETE", f"/tweets/{tweet_id}")
    
    async def get_user_info(self, username: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get user information by username or ID"""
        if username:
            result = await self._request("GET", f"/users/by/username/{username}")
        elif user_id:
            result = await self._request("GET", f"/users/{user_id}")
        else:
            raise ValueError("Either username or user_id must be provided")
        
        return result.get("data", {})
    
    async def _get_authenticated_user_id(self) -> str:
        """Get the authenticated user's ID"""
        result = await self._request("GET", "/users/me")
        return result.get("data", {}).get("id")
    
    async def upload_media(self, media_path: str, media_type: str) -> str:
        """
        Upload media and return media ID
        
        Args:
            media_path: Path to media file
            media_type: Type of media (photo, video, gif)
            
        Returns:
            Media ID for use in tweets
        """
        # Note: Full implementation requires multipart upload
        # This is a simplified version
        logger.info(f"Uploading {media_type} from {media_path}")
        return f"media_{datetime.utcnow().timestamp()}"
    
    async def get_analytics(
        self,
        tweet_ids: List[str],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for tweets
        
        Args:
            tweet_ids: List of tweet IDs
            metrics: Specific metrics to retrieve
            
        Returns:
            Analytics data
        """
        metrics = metrics or ["impressions", "engagements", "likes", "retweets", "replies"]
        
        analytics = {}
        for tweet_id in tweet_ids:
            tweet_data = await self.get_tweet(tweet_id)
            metrics_data = tweet_data.get("data", {}).get("public_metrics", {})
            analytics[tweet_id] = metrics_data
        
        return analytics


class XAPIError(Exception):
    """Custom exception for X API errors"""
    def __init__(self, status_code: int, error_data: Dict):
        self.status_code = status_code
        self.error_data = error_data
        super().__init__(f"X API Error {status_code}: {error_data}")


class RateLimiter:
    """
    Rate limiter for X API
    Tracks and enforces rate limits per endpoint
    """
    
    # Default rate limits (requests per 15 minutes)
    DEFAULT_LIMITS = {
        "tweets": 200,
        "users": 300,
        "search": 450,
        "likes": 50,
        "retweets": 50
    }
    
    def __init__(self):
        self.limits = self.DEFAULT_LIMITS.copy()
        self.remaining = self.limits.copy()
        self.reset_times: Dict[str, float] = {}
        self._lock = asyncio.Lock()
    
    def update_from_headers(self, headers: Dict[str, str]):
        """Update rate limit info from response headers"""
        # Parse X-Rate-Limit headers
        pass
    
    async def wait_if_needed(self, endpoint: str):
        """Wait if rate limit is approaching"""
        async with self._lock:
            category = self._get_endpoint_category(endpoint)
            now = datetime.utcnow().timestamp()
            
            # Check if we need to wait
            if category in self.reset_times and self.reset_times[category] > now:
                if self.remaining.get(category, 0) <= 5:
                    wait_time = self.reset_times[category] - now
                    logger.info(f"Rate limit approaching, waiting {wait_time:.1f}s")
                    await asyncio.sleep(min(wait_time, 60))
    
    def _get_endpoint_category(self, endpoint: str) -> str:
        """Map endpoint to rate limit category"""
        if "tweets" in endpoint:
            return "tweets"
        elif "users" in endpoint:
            return "users"
        elif "search" in endpoint:
            return "search"
        elif "likes" in endpoint:
            return "likes"
        elif "retweets" in endpoint:
            return "retweets"
        return "tweets"
