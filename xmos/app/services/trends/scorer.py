"""Trend scorer service for evaluating and ranking trends."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.trends import Trend
from app.models.brand import BrandVoice

logger = logging.getLogger(__name__)


class RelevanceScore(Enum):
    """Relevance score levels."""
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


class TrendScorer:
    """Service for scoring and ranking trends based on relevance."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_trend_score(
        self,
        trend: Trend,
        brand_voice: Optional[BrandVoice] = None
    ) -> float:
        """
        Calculate a comprehensive score for a trend.
        
        Scoring factors:
        - Volume score (0-30 points): Based on tweet volume
        - Velocity score (0-20 points): Rate of growth
        - Recency score (0-15 points): How recent the trend is
        - Relevance score (0-35 points): Match with brand voice
        
        Args:
            trend: Trend object to score
            brand_voice: Optional brand voice for relevance calculation
            
        Returns:
            Total score (0-100)
        """
        # Volume score (0-30 points)
        volume_score = self._calculate_volume_score(trend.tweet_volume)
        
        # Velocity score (0-20 points)
        velocity_score = self._calculate_velocity_score(trend)
        
        # Recency score (0-15 points)
        recency_score = self._calculate_recency_score(trend.collected_at)
        
        # Relevance score (0-35 points)
        relevance_score = 17.5  # Default medium relevance
        if brand_voice:
            relevance_score = self._calculate_relevance_score(
                trend, 
                brand_voice
            )
        
        total_score = volume_score + velocity_score + recency_score + relevance_score
        
        # Update trend score in database
        trend.score = total_score
        self.db.commit()
        
        logger.debug(
            f"Scored trend '{trend.name}': {total_score:.2f} "
            f"(vol={volume_score:.1f}, vel={velocity_score:.1f}, "
            f"rec={recency_score:.1f}, rel={relevance_score:.1f})"
        )
        
        return total_score

    def _calculate_volume_score(self, tweet_volume: int) -> float:
        """
        Calculate score based on tweet volume.
        
        Args:
            tweet_volume: Number of tweets
            
        Returns:
            Score from 0-30
        """
        if tweet_volume <= 0:
            return 0
        
        # Logarithmic scaling for volume
        import math
        base_score = math.log10(tweet_volume + 1) * 7.5
        
        # Cap at 30 points
        return min(base_score, 30.0)

    def _calculate_velocity_score(self, trend: Trend) -> float:
        """
        Calculate score based on trend velocity (growth rate).
        
        Args:
            trend: Trend object
            
        Returns:
            Score from 0-20
        """
        # Look for previous instances of this trend
        previous = self.db.query(Trend).filter(
            Trend.name == trend.name,
            Trend.id != trend.id,
            Trend.collected_at < trend.collected_at
        ).order_by(desc(Trend.collected_at)).first()
        
        if not previous or previous.tweet_volume == 0:
            # No previous data or cannot calculate growth
            return 10.0  # Neutral score
        
        # Calculate growth rate
        growth_rate = (trend.tweet_volume - previous.tweet_volume) / previous.tweet_volume
        
        # Convert to score (0-20)
        # 100% growth = 20 points, 0% growth = 10 points, -50% growth = 0 points
        velocity_score = 10.0 + (growth_rate * 10.0)
        
        return max(0.0, min(20.0, velocity_score))

    def _calculate_recency_score(self, collected_at: datetime) -> float:
        """
        Calculate score based on how recent the trend is.
        
        Args:
            collected_at: When the trend was collected
            
        Returns:
            Score from 0-15
        """
        now = datetime.utcnow()
        age_hours = (now - collected_at).total_seconds() / 3600
        
        # Fresh trends (< 1 hour) get full points
        if age_hours < 1:
            return 15.0
        
        # Linear decay over 24 hours
        decay_score = 15.0 * (1 - (age_hours / 24.0))
        
        return max(0.0, decay_score)

    def _calculate_relevance_score(
        self,
        trend: Trend,
        brand_voice: BrandVoice
    ) -> float:
        """
        Calculate relevance score based on brand voice match.
        
        Args:
            trend: Trend object
            brand_voice: Brand voice configuration
            
        Returns:
            Score from 0-35
        """
        score = 0.0
        trend_name_lower = trend.name.lower()
        
        # Check keyword matches (0-15 points)
        if brand_voice.keywords:
            keyword_matches = sum(
                1 for kw in brand_voice.keywords 
                if kw.lower() in trend_name_lower
            )
            keyword_score = min(15.0, keyword_matches * 3.0)
            score += keyword_score
        
        # Check category alignment (0-10 points)
        if brand_voice.industry:
            industry_lower = brand_voice.industry.lower()
            if (industry_lower in trend_name_lower or 
                trend.category.lower() == industry_lower):
                score += 10.0
        
        # Check tone alignment (0-10 points)
        # This would require more sophisticated NLP analysis
        # For now, give partial credit based on simple heuristics
        tone_keywords = {
            "professional": ["business", "corporate", "industry"],
            "casual": ["fun", "lol", "haha", "meme"],
            "technical": ["tech", "code", "dev", "api"],
            "creative": ["art", "design", "creative", "inspiration"]
        }
        
        if brand_voice.tone:
            tone_lower = brand_voice.tone.lower()
            if tone_lower in tone_keywords:
                tone_matches = any(
                    kw in trend_name_lower 
                    for kw in tone_keywords[tone_lower]
                )
                if tone_matches:
                    score += 10.0
        
        return min(35.0, score)

    def score_all_recent_trends(
        self,
        brand_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Trend]:
        """
        Score all recent trends.
        
        Args:
            brand_id: Optional brand ID for relevance calculation
            limit: Maximum number of trends to score
            
        Returns:
            List of scored trends
        """
        # Get recent trends (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        trends = self.db.query(Trend).filter(
            Trend.collected_at > cutoff
        ).limit(limit).all()
        
        # Get brand voice if brand_id provided
        brand_voice = None
        if brand_id:
            from app.models.brand import BrandVoice
            brand_voice = self.db.query(BrandVoice).filter(
                BrandVoice.brand_id == brand_id
            ).first()
        
        # Score each trend
        for trend in trends:
            self.calculate_trend_score(trend, brand_voice)
        
        logger.info(f"Scored {len(trends)} recent trends")
        return trends

    def get_top_trends(
        self,
        limit: int = 20,
        category: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Trend]:
        """
        Get top scoring trends.
        
        Args:
            limit: Maximum number of trends to return
            category: Filter by category
            min_score: Minimum score threshold
            
        Returns:
            List of top trends
        """
        query = self.db.query(Trend).filter(
            Trend.score >= min_score
        )
        
        if category:
            query = query.filter(Trend.category == category)
        
        return query.order_by(desc(Trend.score)).limit(limit).all()

    def get_trends_by_relevance(
        self,
        brand_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get trends ranked by relevance to a specific brand.
        
        Args:
            brand_id: Brand ID
            limit: Maximum number of trends to return
            
        Returns:
            List of trend dictionaries with relevance info
        """
        from app.models.brand import BrandVoice, Brand
        
        # Get brand and voice
        brand = self.db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            logger.error(f"Brand {brand_id} not found")
            return []
        
        brand_voice = self.db.query(BrandVoice).filter(
            BrandVoice.brand_id == brand_id
        ).first()
        
        # Get recent trends
        cutoff = datetime.utcnow() - timedelta(hours=24)
        trends = self.db.query(Trend).filter(
            Trend.collected_at > cutoff
        ).order_by(desc(Trend.collected_at)).limit(50).all()
        
        # Calculate relevance for each
        results = []
        for trend in trends:
            relevance_score = self._calculate_relevance_score(
                trend, 
                brand_voice
            ) if brand_voice else 0.0
            
            results.append({
                "trend": trend,
                "relevance_score": relevance_score,
                "relevance_level": self._get_relevance_level(relevance_score)
            })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return results[:limit]

    def _get_relevance_level(self, score: float) -> str:
        """
        Convert relevance score to level string.
        
        Args:
            score: Relevance score
            
        Returns:
            Level string
        """
        if score >= 28:
            return "VERY_HIGH"
        elif score >= 21:
            return "HIGH"
        elif score >= 14:
            return "MEDIUM"
        elif score >= 7:
            return "LOW"
        else:
            return "VERY_LOW"
