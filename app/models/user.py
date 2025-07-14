from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional

from app.database import Base


class User(Base):
    """User model for authentication and tracking"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # User profile
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Usage tracking
    total_commands = Column(Integer, default=0)
    total_downloads = Column(Integer, default=0)
    successful_downloads = Column(Integer, default=0)
    failed_downloads = Column(Integer, default=0)
    daily_downloads = Column(Integer, default=0)
    last_daily_reset = Column(DateTime(timezone=True), nullable=True)
    
    # Usage limits
    daily_limit = Column(Integer, default=1000)  # Free tier limit
    is_premium = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True))
    last_login = Column(DateTime(timezone=True))
    
    # API Key for authentication
    api_key = Column(String(255), unique=True, index=True, nullable=True)
    api_key_created_at = Column(DateTime(timezone=True), nullable=True)
    api_key_name = Column(String(100), nullable=True)
    api_key_last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Email verification
    email_verification_token = Column(String(255), nullable=True)
    email_verification_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Client information (for Discord bot users)
    client_id = Column(String(100), nullable=True)  # Discord bot client ID
    client_secret = Column(String(255), nullable=True)  # Hashed client secret
    client_name = Column(String(100), nullable=True)  # Bot/app name
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
