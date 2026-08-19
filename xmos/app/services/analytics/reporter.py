"""Analytics and reporting service for tracking performance."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.models.analytics import PostPerformance, AccountMetrics, CampaignMetrics
from app.models.content import Post
from app.models.publishing import PublishLog

logger = logging.getLogger(__name__)


class TimeRange(Enum):
    """Time range options for analytics."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    ALL = "all"


class AnalyticsReporter:
    """Service for generating analytics reports."""

    def __init__(self, db: Session):
        self.db = db

    def get_post_performance(
        self,
        post_id: int
    ) -> Optional[PostPerformance]:
        """
        Get performance metrics for a specific post.
        
        Args:
            post_id: Post ID
            
        Returns:
            PostPerformance object or None
        """
        return self.db.query(PostPerformance).filter(
            PostPerformance.post_id == post_id
        ).first()

    def get_brand_metrics(
        self,
        brand_id: int,
        time_range: TimeRange = TimeRange.WEEK
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for a brand.
        
        Args:
            brand_id: Brand ID
            time_range: Time range for metrics
            
        Returns:
            Dictionary with aggregated metrics
        """
        # Calculate date cutoff
        cutoff = self._get_date_cutoff(time_range)
        
        # Get all posts for the brand in the time range
        posts = self.db.query(Post).filter(
            Post.brand_id == brand_id,
            Post.created_at > cutoff
        ).all()
        
        if not posts:
            return self._empty_metrics()
        
        # Aggregate metrics
        total_impressions = 0
        total_engagements = 0
        total_likes = 0
        total_retweets = 0
        total_replies = 0
        total_clicks = 0
        
        for post in posts:
            perf = self.get_post_performance(post.id)
            if perf:
                total_impressions += perf.impressions or 0
                total_engagements += perf.engagements or 0
                total_likes += perf.likes or 0
                total_retweets += perf.retweets or 0
                total_replies += perf.replies or 0
                total_clicks += perf.clicks or 0
        
        # Calculate engagement rate
        engagement_rate = (
            (total_engagements / total_impressions * 100) 
            if total_impressions > 0 else 0.0
        )
        
        return {
            "brand_id": brand_id,
            "time_range": time_range.value,
            "total_posts": len(posts),
            "total_impressions": total_impressions,
            "total_engagements": total_engagements,
            "total_likes": total_likes,
            "total_retweets": total_retweets,
            "total_replies": total_replies,
            "total_clicks": total_clicks,
            "engagement_rate": round(engagement_rate, 2),
            "avg_impressions_per_post": round(total_impressions / len(posts), 2) if posts else 0,
            "avg_engagements_per_post": round(total_engagements / len(posts), 2) if posts else 0
        }

    def _get_date_cutoff(self, time_range: TimeRange) -> datetime:
        """
        Get date cutoff based on time range.
        
        Args:
            time_range: Time range enum
            
        Returns:
            Cutoff datetime
        """
        now = datetime.utcnow()
        
        if time_range == TimeRange.DAY:
            return now - timedelta(days=1)
        elif time_range == TimeRange.WEEK:
            return now - timedelta(weeks=1)
        elif time_range == TimeRange.MONTH:
            return now - timedelta(days=30)
        elif time_range == TimeRange.QUARTER:
            return now - timedelta(days=90)
        elif time_range == TimeRange.YEAR:
            return now - timedelta(days=365)
        else:  # ALL
            return datetime.min

    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics dictionary."""
        return {
            "total_posts": 0,
            "total_impressions": 0,
            "total_engagements": 0,
            "total_likes": 0,
            "total_retweets": 0,
            "total_replies": 0,
            "total_clicks": 0,
            "engagement_rate": 0.0,
            "avg_impressions_per_post": 0,
            "avg_engagements_per_post": 0
        }

    def get_top_performing_posts(
        self,
        brand_id: Optional[int] = None,
        limit: int = 10,
        metric: str = "engagements",
        time_range: TimeRange = TimeRange.MONTH
    ) -> List[Dict[str, Any]]:
        """
        Get top performing posts.
        
        Args:
            brand_id: Filter by brand
            limit: Maximum number of posts to return
            metric: Metric to sort by (impressions, engagements, likes, etc.)
            time_range: Time range
            
        Returns:
            List of post performance dictionaries
        """
        cutoff = self._get_date_cutoff(time_range)
        
        query = self.db.query(PostPerformance).join(Post).filter(
            Post.created_at > cutoff
        )
        
        if brand_id:
            query = query.filter(Post.brand_id == brand_id)
        
        # Sort by specified metric
        if hasattr(PostPerformance, metric):
            query = query.order_by(desc(getattr(PostPerformance, metric)))
        else:
            query = query.order_by(desc(PostPerformance.engagements))
        
        results = []
        for perf in query.limit(limit).all():
            results.append({
                "post_id": perf.post_id,
                "content": perf.post.content[:100] if perf.post else "",
                "impressions": perf.impressions,
                "engagements": perf.engagements,
                "likes": perf.likes,
                "retweets": perf.retweets,
                "replies": perf.replies,
                "clicks": perf.clicks,
                "engagement_rate": perf.engagement_rate,
                "posted_at": perf.posted_at
            })
        
        return results

    def record_post_performance(
        self,
        post_id: int,
        impressions: int,
        engagements: int,
        likes: int,
        retweets: int,
        replies: int,
        clicks: int,
        posted_at: datetime
    ) -> PostPerformance:
        """
        Record performance metrics for a post.
        
        Args:
            post_id: Post ID
            impressions: Number of impressions
            engagements: Total engagements
            likes: Number of likes
            retweets: Number of retweets
            replies: Number of replies
            clicks: Number of clicks
            posted_at: When the post was published
            
        Returns:
            Created/updated PostPerformance object
        """
        # Check if already exists
        existing = self.db.query(PostPerformance).filter(
            PostPerformance.post_id == post_id
        ).first()
        
        # Calculate engagement rate
        engagement_rate = (
            (engagements / impressions * 100) if impressions > 0 else 0.0
        )
        
        if existing:
            # Update existing record
            existing.impressions = impressions
            existing.engagements = engagements
            existing.likes = likes
            existing.retweets = retweets
            existing.replies = replies
            existing.clicks = clicks
            existing.engagement_rate = engagement_rate
            existing.last_updated = datetime.utcnow()
        else:
            # Create new record
            perf = PostPerformance(
                post_id=post_id,
                impressions=impressions,
                engagements=engagements,
                likes=likes,
                retweets=retweets,
                replies=replies,
                clicks=clicks,
                engagement_rate=engagement_rate,
                posted_at=posted_at
            )
            self.db.add(perf)
        
        self.db.commit()
        
        logger.info(f"Recorded performance for post {post_id}: {engagements} engagements")
        
        if not existing:
            return perf
        return existing

    def get_publishing_stats(
        self,
        brand_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get publishing statistics.
        
        Args:
            brand_id: Filter by brand
            days: Number of days to analyze
            
        Returns:
            Publishing statistics dictionary
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(PublishLog)
        
        if brand_id:
            from app.models.content import Post
            query = query.join(Post).filter(Post.brand_id == brand_id)
        
        query = query.filter(PublishLog.published_at > cutoff)
        
        logs = query.all()
        
        # Count by status
        success_count = sum(1 for log in logs if log.status == "success")
        failed_count = sum(1 for log in logs if log.status == "failed")
        
        return {
            "total_published": len(logs),
            "successful": success_count,
            "failed": failed_count,
            "success_rate": round(success_count / len(logs) * 100, 2) if logs else 0,
            "avg_per_day": round(len(logs) / days, 2)
        }

    def generate_campaign_report(
        self,
        campaign_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a report for a specific campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Campaign report dictionary or None
        """
        campaign = self.db.query(CampaignMetrics).filter(
            CampaignMetrics.id == campaign_id
        ).first()
        
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            return None
        
        return {
            "campaign_id": campaign.id,
            "name": campaign.name,
            "start_date": campaign.start_date,
            "end_date": campaign.end_date,
            "total_posts": campaign.total_posts,
            "total_impressions": campaign.total_impressions,
            "total_engagements": campaign.total_engagements,
            "engagement_rate": campaign.engagement_rate,
            "reach": campaign.reach,
            "conversions": campaign.conversions,
            "roi": campaign.roi
        }

    def compare_periods(
        self,
        brand_id: int,
        period1_days: int = 7,
        period2_days: int = 7
    ) -> Dict[str, Any]:
        """
        Compare metrics between two periods.
        
        Args:
            brand_id: Brand ID
            period1_days: Days in period 1 (most recent)
            period2_days: Days in period 2 (older)
            
        Returns:
            Comparison dictionary
        """
        now = datetime.utcnow()
        
        # Period 1 (recent)
        period1_start = now - timedelta(days=period1_days)
        metrics1 = self.get_brand_metrics(brand_id, TimeRange.WEEK)
        # Adjust for custom period
        posts1 = self.db.query(Post).filter(
            Post.brand_id == brand_id,
            Post.created_at > period1_start
        ).count()
        metrics1["total_posts"] = posts1
        
        # Period 2 (older)
        period2_start = period1_start - timedelta(days=period2_days)
        period2_end = period1_start
        # Would need custom query for exact period
        
        return {
            "period1": {
                "days": period1_days,
                "metrics": metrics1
            },
            "period2": {
                "days": period2_days,
                "metrics": metrics1  # Placeholder
            },
            "growth_rate": 0.0  # Would calculate actual growth
        }
