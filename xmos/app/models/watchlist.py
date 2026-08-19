"""
Watchlist models.

Defines watchlist accounts, scans, posts, and insights for competitive intelligence.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class WatchlistPriority(str, Enum):
    """Watchlist account priority levels."""
    TIER_1 = "tier_1"  # High - scan 3x/day
    TIER_2 = "tier_2"  # Medium - scan 2x/day
    TIER_3 = "tier_3"  # Low - scan 1x/day


class WatchlistAccount(Base):
    """X account to monitor for intelligence."""
    
    __tablename__ = "watchlist_accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Account Information
    x_username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    x_user_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # X user ID
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Priority
    priority: Mapped[WatchlistPriority] = mapped_column(SQLEnum(WatchlistPriority), default=WatchlistPriority.TIER_2)
    
    # Scan Configuration
    scan_frequency_per_day: Mapped[int] = mapped_column(Integer, default=2)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Tracking
    last_scan_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_post_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # For incremental retrieval
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scans: Mapped[list["WatchlistScan"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    posts: Mapped[list["WatchlistPost"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    insights: Mapped[list["WatchlistInsight"]] = relationship(back_populates="account", cascade="all, delete-orphan")


class WatchlistScan(Base):
    """Record of a watchlist scan operation."""
    
    __tablename__ = "watchlist_scans"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("watchlist_accounts.id"), nullable=False)
    
    # Scan Details
    scan_type: Mapped[str] = mapped_column(String(50), default="posts")  # posts, trends, general
    posts_found: Mapped[int] = mapped_column(Integer, default=0)
    new_posts: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="completed")  # pending, completed, failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    account: Mapped["WatchlistAccount"] = relationship(back_populates="scans")


class WatchlistPost(Base):
    """Post from a watchlist account."""
    
    __tablename__ = "watchlist_posts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("watchlist_accounts.id"), nullable=False)
    
    # Post Information
    external_post_id: Mapped[str] = mapped_column(String(100), nullable=False)  # X post ID
    text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Timestamps
    post_created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # When post was created on X
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Metrics (if available)
    impressions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retweets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    replies: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Analysis
    topics_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of detected topics
    is_relevant: Mapped[bool] = mapped_column(Boolean, default=False)
    relevance_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account: Mapped["WatchlistAccount"] = relationship(back_populates="posts")


class WatchlistInsight(Base):
    """Derived insight from watchlist analysis."""
    
    __tablename__ = "watchlist_insights"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("watchlist_accounts.id"), nullable=False)
    
    # Insight Details
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)  # topic, format, timing, theme
    
    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Evidence
    related_post_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of post IDs
    
    # Actionability
    is_actionable: Mapped[bool] = mapped_column(Boolean, default=False)
    suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Tracking
    acted_upon: Mapped[bool] = mapped_column(Boolean, default=False)
    content_item_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Reference to created content
    
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account: Mapped["WatchlistAccount"] = relationship(back_populates="insights")
