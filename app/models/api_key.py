from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional

from app.database import Base


class APIKey(Base):
    """API Key model for user authentication"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # API Key details
    key_hash = Column(String(255), unique=True, index=True, nullable=False)  # Hashed for security
    key_preview = Column(String(20), nullable=False)  # First 8 chars for display
    name = Column(String(100), nullable=False)
    
    # Status and tracking
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration
    revoked_at = Column(DateTime(timezone=True), nullable=True)  # When key was revoked
    
    # Relationship
    user = relationship("User", back_populates="api_keys")
