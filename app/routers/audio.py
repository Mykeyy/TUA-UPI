from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import structlog

from app.database import get_async_session
from app.schemas.audio import (
    AssetInfo, AudioDownloadRequest, AudioBatchRequest, 
    AudioDownloadResponse, AudioBatchResponse
)
from app.services.audio import AudioService
from app.dependencies import get_current_user, rate_limit_check
from app.schemas.auth import UserResponse

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/info/{asset_id}", response_model=AssetInfo)
async def get_asset_info(
    asset_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    _: None = Depends(rate_limit_check)
):
    """Get information about a Roblox audio asset"""
    try:
        audio_service = AudioService(db)
        asset_info = await audio_service.get_asset_info(asset_id)
        
        logger.info("Asset info retrieved", 
                   user_id=current_user.id, 
                   asset_id=asset_id)
        
        return asset_info
    except ValueError as e:
        logger.warning("Invalid asset ID", 
                      user_id=current_user.id, 
                      asset_id=asset_id, 
                      error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {asset_id} not found or invalid"
        )
    except Exception as e:
        logger.error("Error retrieving asset info", 
                    user_id=current_user.id, 
                    asset_id=asset_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve asset information"
        )


@router.post("/download", response_model=AudioDownloadResponse)
async def download_audio(
    request: AudioDownloadRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    _: None = Depends(rate_limit_check)
):
    """Download a single Roblox audio file"""
    try:
        audio_service = AudioService(db)
        result = await audio_service.download_audio(
            user_id=current_user.id,
            asset_id=request.asset_id,
            place_id=request.place_id
        )
        
        logger.info("Audio download completed", 
                   user_id=current_user.id, 
                   asset_id=request.asset_id,
                   success=result.success)
        
        return result
    except ValueError as e:
        logger.warning("Invalid download request", 
                      user_id=current_user.id, 
                      asset_id=request.asset_id, 
                      error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error downloading audio", 
                    user_id=current_user.id, 
                    asset_id=request.asset_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download audio"
        )


@router.post("/batch", response_model=AudioBatchResponse)
async def download_audio_batch(
    request: AudioBatchRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    _: None = Depends(rate_limit_check)
):
    """Download multiple Roblox audio files"""
    try:
        audio_service = AudioService(db)
        result = await audio_service.download_audio_batch(
            user_id=current_user.id,
            asset_ids=request.asset_ids,
            place_id=request.place_id
        )
        
        logger.info("Batch download completed", 
                   user_id=current_user.id, 
                   total_requested=len(request.asset_ids),
                   successful=result.successful_downloads,
                   failed=result.failed_downloads)
        
        return result
    except ValueError as e:
        logger.warning("Invalid batch request", 
                      user_id=current_user.id, 
                      error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error in batch download", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process batch download"
        )
