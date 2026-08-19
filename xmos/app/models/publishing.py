"""
Publishing models.

Defines publish attempts for tracking publishing operations.
"""

from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class PublishAttempt(Base):
    """Record of a publish attempt with retry tracking."""
    
    __tablename__ = "publish_attempts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("content_items.id"), nullable=False)
    
    # Attempt Details
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    
    # Request Details
    request_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON of API request
    
    # Response
    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON of API response
    
    # Result
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    x_post_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Post ID if successful
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g., "rate_limit", "auth", "network"
    
    # Retry Information
    is_retry: Mapped[bool] = mapped_column(Boolean, default=False)
    previous_attempt_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retry_after_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Timing
    attempted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content: Mapped["ContentItem"] = relationship(back_populates="publish_attempts")
