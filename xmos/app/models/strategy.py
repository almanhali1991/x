"""
Strategy models.

Defines strategy documents and insights for continuous improvement.
"""

from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class Strategy(Base):
    """Content strategy document (daily/weekly/monthly)."""
    
    __tablename__ = "strategies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Strategy Type
    strategy_type: Mapped[str] = mapped_column(String(50), nullable=False)  # daily, weekly, monthly
    
    # Period
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Strategy Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Key Sections (stored as JSON)
    top_topics_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Top performing topics
    weak_topics_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Underperforming topics
    top_hooks_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Best hooks
    top_formats_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Best formats
    best_time_windows_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Optimal posting times
    
    # Strategic Direction
    focus_areas_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Priority focus areas
    recommended_changes_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Suggested changes
    strategic_direction: Mapped[str | None] = mapped_column(Text, nullable=True)  # Overall direction
    
    # Content Plan
    planned_content_count: Mapped[int] = mapped_column(Integer, default=0)
    planned_threads_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Performance Context
    audience_growth: Mapped[float | None] = mapped_column(Float, nullable=True)
    content_growth: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft, active, completed
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    insights: Mapped[list["StrategyInsight"]] = relationship(back_populates="strategy", cascade="all, delete-orphan")


class StrategyInsight(Base):
    """Individual insight that informs strategy."""
    
    __tablename__ = "strategy_insights"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("strategies.id"), nullable=True)
    
    # Insight Details
    insight_type: Mapped[str] = mapped_column(String(100), nullable=False)  # topic, format, timing, audience, trend
    
    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Evidence
    supporting_data_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON with metrics/evidence
    
    # Impact
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-1
    impact_level: Mapped[str] = mapped_column(String(50), default="medium")  # low, medium, high
    
    # Actionability
    is_actionable: Mapped[bool] = mapped_column(Boolean, default=False)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    implemented: Mapped[bool] = mapped_column(Boolean, default=False)
    
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    strategy: Mapped["Strategy"] = relationship(back_populates="insights")
