"""
Content models.

Defines content items, versions, history, and validation states.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Float, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class ContentState(str, Enum):
    """Content lifecycle states."""
    IDEA = "idea"
    DRAFT = "draft"
    REVIEW = "review"
    REWRITE_REQUIRED = "rewrite_required"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ContentType(str, Enum):
    """Type of content."""
    POST = "post"
    THREAD = "thread"


class ContentCategory(str, Enum):
    """Content categories (configurable)."""
    EDUCATIONAL = "educational"
    TREND = "trend"
    OPINION = "opinion"
    CONVERSATION = "conversation"
    AUTHORITY = "authority"
    NEWS_ANALYSIS = "news_analysis"


class SourceType(str, Enum):
    """Source of content inspiration."""
    TREND = "trend"
    WATCHLIST = "watchlist"
    STRATEGY = "strategy"
    SPONTANEOUS = "spontaneous"


class ContentItem(Base):
    """Main content item record."""
    
    __tablename__ = "content_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Type and Category
    type: Mapped[ContentType] = mapped_column(SQLEnum(ContentType), nullable=False)
    category: Mapped[ContentCategory] = mapped_column(SQLEnum(ContentCategory), nullable=False)
    
    # Content Details
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    angle: Mapped[str] = mapped_column(Text, nullable=False)
    pillar_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("content_pillars.id"), nullable=True)
    
    # Source Tracking
    source_type: Mapped[SourceType] = mapped_column(SQLEnum(SourceType), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g., trend_id or watchlist_account
    
    # Content Body
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    thread_items_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array for threads
    
    # Scoring
    score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # State Machine
    state: Mapped[ContentState] = mapped_column(SQLEnum(ContentState), default=ContentState.IDEA)
    
    # Scheduling & Publishing
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    x_post_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # X API post ID
    x_thread_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array for thread post IDs
    
    # Validation
    validation_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON validation result
    
    # Metadata
    language: Mapped[str] = mapped_column(String(10), default="ar")
    character_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pillar: Mapped["ContentPillar"] = relationship(back_populates="content_items")
    versions: Mapped[list["ContentVersion"]] = relationship(back_populates="content", cascade="all, delete-orphan")
    validations: Mapped[list["ContentValidation"]] = relationship(back_populates="content", cascade="all, delete-orphan")
    publish_attempts: Mapped[list["PublishAttempt"]] = relationship(back_populates="content", cascade="all, delete-orphan")


class ContentVersion(Base):
    """Track content revisions/edits."""
    
    __tablename__ = "content_versions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[int] = mapped_column(Integer, ForeignKey("content_items.id"), nullable=False)
    
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    
    # Version Content
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    thread_items_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Change Reason
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[str] = mapped_column(String(100), default="system")  # "system", "ai", "user"
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content: Mapped["ContentItem"] = relationship(back_populates="versions")


class ContentHistory(Base):
    """Historical record of all content for repetition prevention."""
    
    __tablename__ = "content_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Reference to original content
    content_id: Mapped[int] = mapped_column(Integer, ForeignKey("content_items.id"), nullable=True)
    
    # Snapshot of key fields for comparison
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    angle: Mapped[str] = mapped_column(Text, nullable=False)
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    pillar_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Performance tracking
    impressions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engagements: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engagement_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ContentValidation(Base):
    """Quality gate validation results."""
    
    __tablename__ = "content_validations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[int] = mapped_column(Integer, ForeignKey("content_items.id"), nullable=False)
    
    # Validation Criteria Scores (0-10 or boolean)
    originality_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-10
    relevance_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-10
    clarity_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-10
    accuracy_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-10
    audience_value_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-10
    hook_strength_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-10
    brand_voice_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-10
    spam_risk_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-10 (lower is better)
    x_policy_compliance: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Overall Result
    overall_result: Mapped[str] = mapped_column(String(50), default="pending")  # approved, rewrite_required, rejected
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    validated_by: Mapped[str] = mapped_column(String(100), default="system")  # "ai", "user"
    validated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content: Mapped["ContentItem"] = relationship(back_populates="validations")
