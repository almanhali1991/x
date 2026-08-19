"""
XMOS Database Models - SQLAlchemy ORM definitions.

This module exports all database models for the XMOS system.
"""

from app.models.brand import BrandProfile, BrandRule, AudienceProfile, ContentPillar
from app.models.content import (
    ContentItem,
    ContentVersion,
    ContentHistory,
    ContentValidation,
    ContentState,
    ContentType,
    ContentCategory,
    SourceType,
)
from app.models.trends import Trend, TrendAssessment
from app.models.watchlist import (
    WatchlistAccount,
    WatchlistScan,
    WatchlistPost,
    WatchlistInsight,
    WatchlistPriority,
)
from app.models.strategy import Strategy, StrategyInsight
from app.models.analytics import AnalyticsSnapshot
from app.models.publishing import PublishAttempt
from app.models.system import APIUsage, SystemJob, AuditLog, Setting, OAuthToken

__all__ = [
    # Brand
    "BrandProfile",
    "BrandRule",
    "AudienceProfile",
    "ContentPillar",
    # Content
    "ContentItem",
    "ContentVersion",
    "ContentHistory",
    "ContentValidation",
    "ContentState",
    "ContentType",
    "ContentCategory",
    "SourceType",
    # Trends
    "Trend",
    "TrendAssessment",
    # Watchlist
    "WatchlistAccount",
    "WatchlistScan",
    "WatchlistPost",
    "WatchlistInsight",
    "WatchlistPriority",
    # Strategy
    "Strategy",
    "StrategyInsight",
    # Analytics
    "AnalyticsSnapshot",
    # Publishing
    "PublishAttempt",
    # System
    "APIUsage",
    "SystemJob",
    "AuditLog",
    "Setting",
    "OAuthToken",
]
