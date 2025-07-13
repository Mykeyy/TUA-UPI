from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime


class AssetInfo(BaseModel):
    """Schema for Roblox audio asset information"""
    asset_id: int = Field(..., title="Asset ID", description="Roblox asset identifier")
    name: str = Field(..., title="Asset Name", description="Name of the audio asset")
    creator: str = Field(..., title="Creator", description="Creator of the audio asset")
    description: Optional[str] = Field(None, title="Description", description="Asset description")
    created: Optional[str] = Field(None, title="Created Date", description="Asset creation date")
    updated: Optional[str] = Field(None, title="Updated Date", description="Asset last update date")

    model_config = {
        "json_schema_extra": {
            "example": {
                "asset_id": 1234567890,
                "name": "Epic Background Music",
                "creator": "MusicMaker123",
                "description": "An epic orchestral piece perfect for action scenes",
                "created": "2024-01-15",
                "updated": "2024-02-20"
            }
        }
    }


class AudioDownloadRequest(BaseModel):
    """Schema for single audio download request"""
    asset_id: int = Field(..., gt=0, title="Asset ID", description="Roblox asset ID to download")
    place_id: str = Field(..., min_length=1, title="Place ID", description="Roblox place ID for authentication")

    model_config = {
        "json_schema_extra": {
            "example": {
                "asset_id": 1234567890,
                "place_id": "9876543210"
            }
        }
    }


class AudioBatchRequest(BaseModel):
    """Schema for batch audio download request"""
    asset_ids: List[int] = Field(..., min_length=1, max_length=10, title="Asset IDs", description="List of Roblox asset IDs to download")
    place_id: str = Field(..., min_length=1, title="Place ID", description="Roblox place ID for authentication")

    model_config = {
        "json_schema_extra": {
            "example": {
                "asset_ids": [1234567890, 1234567891, 1234567892],
                "place_id": "9876543210"
            }
        }
    }


class AudioDownloadResponse(BaseModel):
    """Schema for single audio download response"""
    success: bool = Field(..., title="Success", description="Whether the download was successful")
    asset_id: int = Field(..., title="Asset ID", description="Roblox asset ID that was processed")
    asset_name: str = Field(..., title="Asset Name", description="Name of the audio asset")
    creator: str = Field(..., title="Creator", description="Creator of the audio asset")
    file_size: Optional[int] = Field(None, title="File Size", description="Size of the downloaded file in bytes")
    download_url: Optional[str] = Field(None, title="Download URL", description="URL to download the audio file")
    error_message: Optional[str] = Field(None, title="Error Message", description="Error message if download failed")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "asset_id": 1234567890,
                "asset_name": "Epic Background Music",
                "creator": "MusicMaker123",
                "file_size": 2048576,
                "download_url": "https://api.example.com/download/1234567890.mp3",
                "error_message": None
            }
        }
    }


class AudioBatchResponse(BaseModel):
    """Schema for batch audio download response"""
    total_requested: int = Field(..., title="Total Requested", description="Total number of assets requested")
    successful_downloads: int = Field(..., title="Successful Downloads", description="Number of successful downloads")
    failed_downloads: int = Field(..., title="Failed Downloads", description="Number of failed downloads")
    downloads: List[AudioDownloadResponse] = Field(..., title="Downloads", description="List of individual download results")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_requested": 3,
                "successful_downloads": 2,
                "failed_downloads": 1,
                "downloads": [
                    {
                        "success": True,
                        "asset_id": 1234567890,
                        "asset_name": "Epic Background Music",
                        "creator": "MusicMaker123",
                        "file_size": 2048576,
                        "download_url": "https://api.example.com/download/1234567890.mp3",
                        "error_message": None
                    }
                ]
            }
        }
    }


class AudioDownloadLog(BaseModel):
    """Schema for audio download log entry"""
    id: int = Field(..., title="Log ID", description="Unique log entry identifier")
    asset_id: int = Field(..., title="Asset ID", description="Roblox asset ID that was downloaded")
    asset_name: str = Field(..., title="Asset Name", description="Name of the audio asset")
    creator: str = Field(..., title="Creator", description="Creator of the audio asset")
    success: bool = Field(..., title="Success", description="Whether the download was successful")
    file_size: Optional[int] = Field(None, title="File Size", description="Size of the downloaded file in bytes")
    error_message: Optional[str] = Field(None, title="Error Message", description="Error message if download failed")
    created_at: datetime = Field(..., title="Created At", description="Log entry creation timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "asset_id": 1234567890,
                "asset_name": "Epic Background Music",
                "creator": "MusicMaker123",
                "success": True,
                "file_size": 2048576,
                "error_message": None,
                "created_at": "2024-07-13T14:22:30"
            }
        }
    }


class AssetStatsResponse(BaseModel):
    """Schema for asset download statistics"""
    asset_id: int = Field(..., title="Asset ID", description="Roblox asset ID")
    asset_name: str = Field(..., title="Asset Name", description="Name of the audio asset")
    creator: str = Field(..., title="Creator", description="Creator of the audio asset")
    total_downloads: int = Field(..., title="Total Downloads", description="Total number of download attempts")
    successful_downloads: int = Field(..., title="Successful Downloads", description="Number of successful downloads")
    failed_downloads: int = Field(..., title="Failed Downloads", description="Number of failed downloads")
    unique_users: int = Field(..., title="Unique Users", description="Number of unique users who downloaded this asset")
    success_rate: float = Field(..., title="Success Rate", description="Download success rate as percentage")
    first_downloaded: datetime = Field(..., title="First Downloaded", description="First download timestamp")
    last_downloaded: datetime = Field(..., title="Last Downloaded", description="Most recent download timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "asset_id": 1234567890,
                "asset_name": "Epic Background Music",
                "creator": "MusicMaker123",
                "total_downloads": 150,
                "successful_downloads": 145,
                "failed_downloads": 5,
                "unique_users": 75,
                "success_rate": 96.67,
                "first_downloaded": "2024-01-15T10:30:00",
                "last_downloaded": "2024-07-13T14:22:30"
            }
        }
    }
