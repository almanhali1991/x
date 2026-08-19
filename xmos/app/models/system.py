"""
System models.

Defines system-level models for API usage, jobs, audit logs, settings, and OAuth tokens.
"""

from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, Integer, Float, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class APIUsage(Base):
    """Track API usage and costs."""
    
    __tablename__ = "api_usage"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Provider
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # "deepseek", "x_api"
    
    # Usage Details
    endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    request_type: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g., "chat", "publish", "metrics"
    
    # Token/Request Counts
    requests_count: Mapped[int] = mapped_column(Integer, default=1)
    input_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # For AI APIs
    output_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # For AI APIs
    
    # Cost Estimation
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    
    # Period
    usage_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SystemJob(Base):
    """Scheduled job tracking."""
    
    __tablename__ = "system_jobs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Job Identification
    job_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)  # trend_scan, watchlist_scan, content_generation, etc.
    
    # Scheduling
    schedule_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Cron-like expression
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Status
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(50), default="idle")  # idle, running, completed, failed
    
    # Execution Tracking
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_execution_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Statistics
    total_runs: Mapped[int] = mapped_column(Integer, default=0)
    successful_runs: Mapped[int] = mapped_column(Integer, default=0)
    failed_runs: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """Audit trail for important system events."""
    
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Event Details
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_category: Mapped[str] = mapped_column(String(50), nullable=False)  # content, strategy, settings, security
    
    # Actor
    actor: Mapped[str] = mapped_column(String(100), default="system")  # user, ai, system
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Entity
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g., "content_item", "strategy"
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Action
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # created, edited, approved, rejected, deleted
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Changes (for updates)
    old_values_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_values_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Setting(Base):
    """Application settings stored in database."""
    
    __tablename__ = "settings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(50), default="string")  # string, int, float, bool, json
    
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True)
    
    updated_by: Mapped[str] = mapped_column(String(100), default="system")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OAuthToken(Base):
    """OAuth token storage for X API authentication."""
    
    __tablename__ = "oauth_tokens"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Token Type
    token_type: Mapped[str] = mapped_column(String(50), nullable=False)  # access_token, refresh_token
    
    # Token Values (encrypted in application layer)
    token_value_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Expiration
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Scope
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    provider: Mapped[str] = mapped_column(String(50), default="x")  # "x" for X/Twitter
    account_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
