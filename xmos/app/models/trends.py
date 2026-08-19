"""
Trend models.

Defines trends, assessments, and scoring for content opportunities.
"""

from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class Trend(Base):
    """Trend/topic record from X or other sources."""
    
    __tablename__ = "trends"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Source Information
    source: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "x_trends", "x_search"
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)  # External trend ID
    
    # Trend Details
    title: Mapped[str] = mapped_column(String(500), nullable=False)  # Trend title/topic
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g., "SA", "AE", "KW"
    
    # Timestamps
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Scoring Components (0-100 scale components)
    saudi_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-30
    gulf_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-20
    audience_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-20
    timing_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-15
    content_potential_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-15
    
    # Total Score (0-100)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="new")  # new, monitoring, opportunity, ignored, used
    
    # AI-Generated Insights
    suggested_angle: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevance_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Additional trend data
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assessments: Mapped[list["TrendAssessment"]] = relationship(back_populates="trend", cascade="all, delete-orphan")


class TrendAssessment(Base):
    """Assessment/evaluation of a trend for content creation."""
    
    __tablename__ = "trend_assessments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trend_id: Mapped[int] = mapped_column(Integer, ForeignKey("trends.id"), nullable=False)
    
    # Assessment Details
    assessment_type: Mapped[str] = mapped_column(String(50), default="opportunity")  # opportunity, monitor, ignore
    
    # Content Opportunity
    content_angle: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_format: Mapped[str | None] = mapped_column(String(50), nullable=True)  # post, thread
    
    # Evaluation Notes
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-1
    
    # Outcome
    resulted_in_content: Mapped[bool] = mapped_column(Boolean, default=False)
    content_item_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Reference to created content
    
    assessed_by: Mapped[str] = mapped_column(String(100), default="ai")  # "ai", "user"
    assessed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    trend: Mapped["Trend"] = relationship(back_populates="assessments")
