"""
Brand and Strategy models.

Defines brand identity, voice, rules, audience, and content pillars.
"""

from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class BrandProfile(Base):
    """Brand identity and voice configuration."""
    
    __tablename__ = "brand_profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Brand Voice
    voice: Mapped[str | None] = mapped_column(Text, nullable=True)  # e.g., "Professional, Friendly, Authoritative"
    tone: Mapped[str | None] = mapped_column(Text, nullable=True)  # e.g., "Warm, Confident, Respectful"
    
    # Vocabulary
    preferred_vocabulary: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    forbidden_vocabulary: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    
    # Writing Rules
    writing_rules: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    cta_rules: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    
    # Examples
    approved_examples: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    rejected_examples: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rules: Mapped[list["BrandRule"]] = relationship(back_populates="brand", cascade="all, delete-orphan")
    audience: Mapped["AudienceProfile"] = relationship(back_populates="brand", uselist=False, cascade="all, delete-orphan")
    pillars: Mapped[list["ContentPillar"]] = relationship(back_populates="brand", cascade="all, delete-orphan")


class BrandRule(Base):
    """Specific brand rules for content generation."""
    
    __tablename__ = "brand_rules"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(Integer, ForeignKey("brand_profiles.id"), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "style", "topic", "format"
    rule_description: Mapped[str] = mapped_column(Text, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    brand: Mapped["BrandProfile"] = relationship(back_populates="rules")


class AudienceProfile(Base):
    """Target audience definition."""
    
    __tablename__ = "audience_profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(Integer, ForeignKey("brand_profiles.id"), nullable=False, unique=True)
    
    # Demographics
    primary_region: Mapped[str] = mapped_column(String(100), default="Saudi Arabia")
    secondary_regions: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    age_range: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gender_focus: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Interests
    interests: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    pain_points: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    aspirations: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    
    # Language
    primary_language: Mapped[str] = mapped_column(String(10), default="ar")
    secondary_languages: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    brand: Mapped["BrandProfile"] = relationship(back_populates="audience")


class ContentPillar(Base):
    """Content pillar/thematic area for the brand."""
    
    __tablename__ = "content_pillars"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(Integer, ForeignKey("brand_profiles.id"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Priority (1 = highest)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    weight: Mapped[float] = mapped_column(Float, default=1.0)  # For content distribution
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    brand: Mapped["BrandProfile"] = relationship(back_populates="pillars")
