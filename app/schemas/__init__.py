# Schemas package

# Authentication schemas
from .auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserStats,
    Token,
    TokenData,
    APIKeyResponse
)

# Audio schemas
from .audio import (
    AssetInfo,
    AudioDownloadRequest,
    AudioBatchRequest,
    AudioDownloadResponse,
    AudioBatchResponse,
    AudioDownloadLog,
    AssetStatsResponse
)

# Statistics schemas
from .stats import (
    GlobalStatsResponse,
    PopularAssetResponse,
    UserRankingResponse,
    TimeSeriesData,
    TimeSeriesResponse,
    HealthStatus
)

__all__ = [
    # Auth schemas
    "UserCreate",
    "UserLogin", 
    "UserResponse",
    "UserStats",
    "Token",
    "TokenData",
    "APIKeyResponse",
    # Audio schemas
    "AssetInfo",
    "AudioDownloadRequest",
    "AudioBatchRequest", 
    "AudioDownloadResponse",
    "AudioBatchResponse",
    "AudioDownloadLog",
    "AssetStatsResponse",
    # Stats schemas
    "GlobalStatsResponse",
    "PopularAssetResponse",
    "UserRankingResponse",
    "TimeSeriesData",
    "TimeSeriesResponse",
    "HealthStatus"
]
