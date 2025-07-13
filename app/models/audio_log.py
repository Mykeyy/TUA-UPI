from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class AudioDownloadLog(Base):
    """Log of audio download attempts"""
    __tablename__ = "audio_download_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Asset information
    asset_id = Column(Integer, nullable=False, index=True)
    asset_name = Column(String(255), nullable=False)
    creator = Column(String(100), nullable=False)
    
    # Download details
    success = Column(Boolean, nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    error_message = Column(Text, nullable=True)
    
    # Request details
    place_id = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("User", backref="download_logs")
    
    def __repr__(self):
        return f"<AudioDownloadLog(id={self.id}, asset_id={self.asset_id}, success={self.success})>"


class AssetStats(Base):
    """Statistics for audio assets"""
    __tablename__ = "asset_stats"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, unique=True, nullable=False, index=True)
    asset_name = Column(String(255), nullable=False)
    creator = Column(String(100), nullable=False)
    
    # Download statistics
    total_downloads = Column(Integer, default=0)
    successful_downloads = Column(Integer, default=0)
    failed_downloads = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    
    # Timestamps
    first_downloaded = Column(DateTime(timezone=True), server_default=func.now())
    last_downloaded = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AssetStats(asset_id={self.asset_id}, total_downloads={self.total_downloads})>"


class DailyStats(Base):
    """Daily usage statistics"""
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), unique=True, nullable=False, index=True)
    
    # Usage statistics
    commands_used = Column(Integer, default=0)
    downloads_attempted = Column(Integer, default=0)
    successful_downloads = Column(Integer, default=0)
    failed_downloads = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    
    # Performance metrics
    avg_response_time = Column(Float, default=0.0)
    total_requests = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<DailyStats(date={self.date}, downloads={self.downloads_attempted})>"
