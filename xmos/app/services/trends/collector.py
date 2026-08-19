"""Trend collector service for gathering trending topics from X."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.trends import Trend, TrendCategory
from app.services.x.client import XClient

logger = logging.getLogger(__name__)


class TrendCollector:
    """Service for collecting and managing trends from X."""

    def __init__(self, db: Session, x_client: XClient):
        self.db = db
        self.x_client = x_client

    async def fetch_trending_topics(
        self, 
        location: str = "United States",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Fetch trending topics from X.
        
        Args:
            location: Location to fetch trends for
            limit: Maximum number of trends to fetch
            
        Returns:
            List of trend dictionaries
        """
        try:
            # Fetch trends from X API
            trends_data = await self.x_client.get_trends(location=location)
            
            processed_trends = []
            for trend in trends_data[:limit]:
                processed = {
                    "name": trend.get("name", ""),
                    "tweet_volume": trend.get("tweet_volume", 0),
                    "url": trend.get("url", ""),
                    "promoted_content": trend.get("promoted_content"),
                    "query": trend.get("query", ""),
                    "location": location,
                    "collected_at": datetime.utcnow()
                }
                processed_trends.append(processed)
                
            logger.info(f"Collected {len(processed_trends)} trends from {location}")
            return processed_trends
            
        except Exception as e:
            logger.error(f"Error fetching trends: {e}")
            return []

    def save_trend(
        self,
        name: str,
        tweet_volume: int = 0,
        category: str = "general",
        location: str = "Unknown",
        query: Optional[str] = None,
        url: Optional[str] = None
    ) -> Trend:
        """
        Save a trend to the database.
        
        Args:
            name: Trend name/hashtag
            tweet_volume: Number of tweets
            category: Trend category
            location: Geographic location
            query: Search query for the trend
            url: URL to the trend
            
        Returns:
            Saved Trend object
        """
        # Check if trend already exists (within last 24 hours)
        existing = self.db.query(Trend).filter(
            Trend.name == name,
            Trend.collected_at > datetime.utcnow() - timedelta(hours=24)
        ).first()
        
        if existing:
            # Update existing trend
            existing.tweet_volume = tweet_volume
            existing.location = location
            logger.debug(f"Updated existing trend: {name}")
            return existing
        
        # Determine category if not provided
        if category == "general":
            category = self._categorize_trend(name)
        
        # Create new trend
        trend = Trend(
            name=name,
            tweet_volume=tweet_volume,
            category=category,
            location=location,
            query=query,
            url=url,
            is_promoted=False,
            score=0.0  # Will be calculated by scorer
        )
        
        self.db.add(trend)
        self.db.commit()
        self.db.refresh(trend)
        
        logger.info(f"Saved new trend: {name} ({category})")
        return trend

    def _categorize_trend(self, name: str) -> str:
        """
        Automatically categorize a trend based on its name.
        
        Args:
            name: Trend name
            
        Returns:
            Category string
        """
        name_lower = name.lower()
        
        # Technology related
        tech_keywords = ["ai", "ml", "tech", "crypto", "bitcoin", "nft", "web3"]
        if any(kw in name_lower for kw in tech_keywords):
            return "technology"
        
        # Sports related
        sports_keywords = ["football", "basketball", "soccer", "nba", "nfl", "fifa"]
        if any(kw in name_lower for kw in sports_keywords):
            return "sports"
        
        # Entertainment related
        entertainment_keywords = ["movie", "film", "music", "celebrity", "tv", "show"]
        if any(kw in name_lower for kw in entertainment_keywords):
            return "entertainment"
        
        # Business related
        business_keywords = ["stock", "market", "business", "finance", "economy"]
        if any(kw in name_lower for kw in business_keywords):
            return "business"
        
        # Politics related
        politics_keywords = ["election", "politics", "government", "policy", "vote"]
        if any(kw in name_lower for kw in politics_keywords):
            return "politics"
        
        return "general"

    async def collect_all_trends(
        self,
        locations: List[str] = ["United States"],
        min_volume: int = 1000
    ) -> int:
        """
        Collect trends from multiple locations and save them.
        
        Args:
            locations: List of locations to fetch trends from
            min_volume: Minimum tweet volume to save
            
        Returns:
            Number of trends saved
        """
        total_saved = 0
        
        for location in locations:
            trends = await self.fetch_trending_topics(location=location)
            
            for trend_data in trends:
                if trend_data["tweet_volume"] >= min_volume:
                    self.save_trend(
                        name=trend_data["name"],
                        tweet_volume=trend_data["tweet_volume"],
                        location=trend_data["location"],
                        query=trend_data["query"],
                        url=trend_data["url"]
                    )
                    total_saved += 1
        
        logger.info(f"Total trends saved: {total_saved}")
        return total_saved

    def get_recent_trends(
        self,
        limit: int = 50,
        category: Optional[str] = None
    ) -> List[Trend]:
        """
        Get recent trends from database.
        
        Args:
            limit: Maximum number of trends to return
            category: Filter by category
            
        Returns:
            List of Trend objects
        """
        query = self.db.query(Trend).order_by(desc(Trend.collected_at))
        
        if category:
            query = query.filter(Trend.category == category)
        
        return query.limit(limit).all()
