from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class GlobalStatsResponse(BaseModel):
    """Schema for global API statistics"""
    total_users: int = Field(..., title="Total Users", description="Total number of registered users")
    active_users: int = Field(..., title="Active Users", description="Number of users active in the last 30 days")
    total_downloads: int = Field(..., title="Total Downloads", description="Total number of download attempts")
    successful_downloads: int = Field(..., title="Successful Downloads", description="Number of successful downloads")
    failed_downloads: int = Field(..., title="Failed Downloads", description="Number of failed downloads")
    success_rate: float = Field(..., title="Success Rate", description="Overall download success rate as percentage")
    total_unique_assets: int = Field(..., title="Unique Assets", description="Number of unique assets downloaded")
    api_version: str = Field(..., title="API Version", description="Current API version")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_users": 1250,
                "active_users": 345,
                "total_downloads": 15750,
                "successful_downloads": 14890,
                "failed_downloads": 860,
                "success_rate": 94.54,
                "total_unique_assets": 8640,
                "api_version": "1.0.0"
            }
        }
    }


class PopularAssetResponse(BaseModel):
    """Schema for popular asset information"""
    asset_id: int = Field(..., title="Asset ID", description="Roblox asset ID")
    asset_name: str = Field(..., title="Asset Name", description="Name of the audio asset")
    creator: str = Field(..., title="Creator", description="Creator of the audio asset")
    download_count: int = Field(..., title="Download Count", description="Number of times this asset was downloaded")
    unique_users: int = Field(..., title="Unique Users", description="Number of unique users who downloaded this asset")
    success_rate: float = Field(..., title="Success Rate", description="Download success rate for this asset")
    last_downloaded: datetime = Field(..., title="Last Downloaded", description="Most recent download timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "asset_id": 1234567890,
                "asset_name": "Epic Background Music",
                "creator": "MusicMaker123",
                "download_count": 456,
                "unique_users": 234,
                "success_rate": 98.25,
                "last_downloaded": "2024-07-13T14:22:30"
            }
        }
    }


class UserRankingResponse(BaseModel):
    """Schema for user ranking information"""
    username: str = Field(..., title="Username", description="User's username")
    total_downloads: int = Field(..., title="Total Downloads", description="Total number of downloads by this user")
    successful_downloads: int = Field(..., title="Successful Downloads", description="Number of successful downloads")
    success_rate: float = Field(..., title="Success Rate", description="User's download success rate")
    rank: int = Field(..., title="Rank", description="User's ranking position")
    last_active: datetime = Field(..., title="Last Active", description="User's last activity timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "power_user_123",
                "total_downloads": 2340,
                "successful_downloads": 2298,
                "success_rate": 98.21,
                "rank": 1,
                "last_active": "2024-07-13T14:22:30"
            }
        }
    }


class TimeSeriesData(BaseModel):
    """Schema for time-series statistics data"""
    date: str = Field(..., title="Date", description="Date in YYYY-MM-DD format")
    downloads: int = Field(..., title="Downloads", description="Number of downloads on this date")
    successful: int = Field(..., title="Successful", description="Number of successful downloads on this date")
    failed: int = Field(..., title="Failed", description="Number of failed downloads on this date")
    unique_users: int = Field(..., title="Unique Users", description="Number of unique users active on this date")

    model_config = {
        "json_schema_extra": {
            "example": {
                "date": "2024-07-13",
                "downloads": 145,
                "successful": 138,
                "failed": 7,
                "unique_users": 23
            }
        }
    }


class TimeSeriesResponse(BaseModel):
    """Schema for time-series statistics response"""
    period: str = Field(..., title="Period", description="Time period covered (e.g., '7 days', '30 days')")
    data: List[TimeSeriesData] = Field(..., title="Data", description="Time-series data points")

    model_config = {
        "json_schema_extra": {
            "example": {
                "period": "7 days",
                "data": [
                    {
                        "date": "2024-07-13",
                        "downloads": 145,
                        "successful": 138,
                        "failed": 7,
                        "unique_users": 23
                    },
                    {
                        "date": "2024-07-12",
                        "downloads": 167,
                        "successful": 159,
                        "failed": 8,
                        "unique_users": 28
                    }
                ]
            }
        }
    }


class HealthStatus(BaseModel):
    """Schema for API health status"""
    status: str = Field(..., title="Status", description="Overall API status")
    version: str = Field(..., title="Version", description="API version")
    uptime: str = Field(..., title="Uptime", description="API uptime duration")
    database_status: str = Field(..., title="Database Status", description="Database connection status")
    last_check: datetime = Field(..., title="Last Check", description="Last health check timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": "5 days, 12 hours, 34 minutes",
                "database_status": "connected",
                "last_check": "2024-07-13T14:22:30"
            }
        }
    }
