from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import structlog

from app.database import get_async_session
from app.services.stats import StatsService
from app.dependencies import get_current_user
from app.schemas.auth import UserResponse, UserStats

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/user", response_model=UserStats)
async def get_user_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get statistics for the current user"""
    try:
        stats_service = StatsService(db)
        user_stats = await stats_service.get_user_stats(current_user.id)
        return user_stats
    except Exception as e:
        logger.error("Error retrieving user stats", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@router.get("/global")
async def get_global_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get global platform statistics"""
    try:
        stats_service = StatsService(db)
        global_stats = await stats_service.get_global_stats()
        return global_stats
    except Exception as e:
        logger.error("Error retrieving global stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve global statistics"
        )


@router.get("/assets")
async def get_asset_stats(
    limit: int = Query(10, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get statistics for popular assets"""
    try:
        stats_service = StatsService(db)
        asset_stats = await stats_service.get_popular_assets(limit=limit)
        return asset_stats
    except Exception as e:
        logger.error("Error retrieving asset stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve asset statistics"
        )


@router.get("/daily")
async def get_daily_stats(
    days: int = Query(7, ge=1, le=30),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get daily statistics for the specified number of days"""
    try:
        stats_service = StatsService(db)
        daily_stats = await stats_service.get_daily_stats(days=days)
        return daily_stats
    except Exception as e:
        logger.error("Error retrieving daily stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve daily statistics"
        )
