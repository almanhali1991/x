"""
Rate Limiter - Advanced rate limiting for X API
Implements token bucket algorithm with per-endpoint limits
"""

import asyncio
import time
from typing import Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Advanced rate limiter using token bucket algorithm
    Supports multiple endpoints with different rate limits
    """
    
    # X API v2 rate limits (requests per 15-minute window)
    RATE_LIMITS = {
        "tweets_post": {"limit": 200, "window": 900},
        "tweets_get": {"limit": 300, "window": 900},
        "users": {"limit": 300, "window": 900},
        "search_recent": {"limit": 450, "window": 900},
        "search_all": {"limit": 300, "window": 900},
        "likes_post": {"limit": 50, "window": 900},
        "likes_delete": {"limit": 50, "window": 900},
        "retweets_post": {"limit": 50, "window": 900},
        "retweets_delete": {"limit": 50, "window": 900},
        "media_upload": {"limit": 50, "window": 900},
        "default": {"limit": 300, "window": 900}
    }
    
    def __init__(self, safety_factor: float = 0.8):
        """
        Initialize rate limiter
        
        Args:
            safety_factor: Factor to stay below limit (0.8 = use only 80% of limit)
        """
        self.safety_factor = safety_factor
        self.buckets: Dict[str, TokenBucket] = {}
        self.stats: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
        # Initialize buckets for each endpoint category
        for category, config in self.RATE_LIMITS.items():
            effective_limit = int(config["limit"] * self.safety_factor)
            self.buckets[category] = TokenBucket(
                capacity=effective_limit,
                refill_rate=effective_limit / config["window"]  # tokens per second
            )
            self.stats[category] = {
                "total_requests": 0,
                "rate_limited_waits": 0,
                "last_request": None
            }
    
    async def acquire(self, endpoint: str = "default") -> bool:
        """
        Acquire a token for the specified endpoint
        
        Args:
            endpoint: Endpoint category
            
        Returns:
            True when token is acquired
        """
        category = self._categorize_endpoint(endpoint)
        bucket = self.buckets.get(category, self.buckets["default"])
        
        async with self._lock:
            # Wait if no tokens available
            while not bucket.has_tokens():
                self.stats[category]["rate_limited_waits"] += 1
                wait_time = bucket.time_until_token()
                logger.debug(f"Rate limited on {category}, waiting {wait_time:.2f}s")
                await asyncio.sleep(min(wait_time, 1.0))
            
            # Consume token
            bucket.consume()
            self.stats[category]["total_requests"] += 1
            self.stats[category]["last_request"] = datetime.utcnow().isoformat()
            
            return True
    
    async def wait_if_needed(self, endpoint: str = "default"):
        """Wait if approaching rate limit"""
        await self.acquire(endpoint)
    
    def _categorize_endpoint(self, endpoint: str) -> str:
        """Map endpoint URL to category"""
        endpoint_lower = endpoint.lower()
        
        if "tweets" in endpoint_lower and "POST" in endpoint:
            return "tweets_post"
        elif "tweets" in endpoint_lower:
            return "tweets_get"
        elif "users" in endpoint_lower:
            return "users"
        elif "search" in endpoint_lower and "all" in endpoint_lower:
            return "search_all"
        elif "search" in endpoint_lower:
            return "search_recent"
        elif "likes" in endpoint_lower and "DELETE" in endpoint:
            return "likes_delete"
        elif "likes" in endpoint_lower:
            return "likes_post"
        elif "retweets" in endpoint_lower and "DELETE" in endpoint:
            return "retweets_delete"
        elif "retweets" in endpoint_lower:
            return "retweets_post"
        elif "media" in endpoint_lower or "upload" in endpoint_lower:
            return "media_upload"
        
        return "default"
    
    def get_status(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get rate limit status
        
        Args:
            category: Specific category or None for all
            
        Returns:
            Status information including remaining tokens and reset time
        """
        if category:
            bucket = self.buckets.get(category, self.buckets["default"])
            stats = self.stats.get(category, {})
            return {
                "category": category,
                "tokens_available": bucket.tokens,
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate,
                "time_until_full": bucket.time_until_full(),
                "stats": stats
            }
        
        # Return all categories
        return {
            cat: {
                "tokens_available": bucket.tokens,
                "capacity": bucket.capacity,
                "utilization": 1 - (bucket.tokens / bucket.capacity) if bucket.capacity > 0 else 0,
                "stats": self.stats.get(cat, {})
            }
            for cat, bucket in self.buckets.items()
        }
    
    def update_from_headers(self, headers: Dict[str, str], endpoint: str):
        """
        Update rate limit info from API response headers
        
        Args:
            headers: Response headers from X API
            endpoint: Endpoint that was called
        """
        category = self._categorize_endpoint(endpoint)
        
        # Parse X-Rate-Limit headers
        remaining = headers.get("x-rate-limit-remaining")
        limit = headers.get("x-rate-limit-limit")
        reset = headers.get("x-rate-limit-reset")
        
        if remaining and limit:
            remaining_int = int(remaining)
            limit_int = int(limit)
            
            # Adjust bucket based on actual remaining
            bucket = self.buckets.get(category, self.buckets["default"])
            bucket.tokens = min(bucket.tokens, remaining_int)
            
            logger.debug(f"Updated rate limit for {category}: {remaining_int}/{limit_int}")
        
        if reset:
            reset_time = int(reset)
            # Could use this to reset bucket at the right time
            pass
    
    def reset(self, category: Optional[str] = None):
        """Reset rate limit buckets"""
        if category:
            if category in self.buckets:
                self.buckets[category].reset()
        else:
            for bucket in self.buckets.values():
                bucket.reset()
        
        logger.info(f"Rate limiter reset for {category or 'all categories'}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        total_requests = sum(s["total_requests"] for s in self.stats.values())
        total_waits = sum(s["rate_limited_waits"] for s in self.stats.values())
        
        return {
            "total_requests": total_requests,
            "total_rate_limited_waits": total_waits,
            "rate_limit_efficiency": 1 - (total_waits / max(total_requests, 1)),
            "categories": self.stats.copy(),
            "buckets": self.get_status()
        }


class TokenBucket:
    """
    Token bucket implementation for rate limiting
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
    
    def has_tokens(self, count: int = 1) -> bool:
        """Check if bucket has enough tokens"""
        self._refill()
        return self.tokens >= count
    
    def consume(self, count: int = 1) -> bool:
        """
        Consume tokens from bucket
        
        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        self._refill()
        
        if self.tokens >= count:
            self.tokens -= count
            return True
        
        return False
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def time_until_token(self) -> float:
        """Calculate time until next token is available"""
        self._refill()
        
        if self.tokens >= 1:
            return 0.0
        
        tokens_needed = 1 - self.tokens
        return tokens_needed / self.refill_rate
    
    def time_until_full(self) -> float:
        """Calculate time until bucket is full"""
        self._refill()
        
        tokens_needed = self.capacity - self.tokens
        if tokens_needed <= 0:
            return 0.0
        
        return tokens_needed / self.refill_rate
    
    def reset(self):
        """Reset bucket to full capacity"""
        self.tokens = float(self.capacity)
        self.last_refill = time.time()
