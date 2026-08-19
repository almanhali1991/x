"""
Analytics models.

Defines analytics snapshots for performance tracking.
"""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AnalyticsSnapshot(Base):
    """Periodic analytics snapshot for trend analysis."""
    
    __tablename__ = "analytics_snapshots"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Snapshot Period
    snapshot_type: Mapped[str] = mapped_column(String(50), nullable=False)  # daily, weekly, monthly
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Account Metrics
    followers_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    following_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tweets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Content Metrics
    posts_published: Mapped[int] = mapped_column(Integer, default=0)
    threads_published: Mapped[int] = mapped_column(Integer, default=0)
    
    # Aggregated Performance
    total_impressions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_engagements: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_engagement_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Top Performers (stored as JSON)
    top_posts_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Top 10 posts with metrics
    bottom_posts_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Bottom 10 posts
    
    # Topic Performance
    topic_performance_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Performance by topic
    format_performance_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Performance by format
    time_performance_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Performance by time window
    
    # Trend Performance
    trend_opportunity_performance_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Key Learnings
    key_observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
