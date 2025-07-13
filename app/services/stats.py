from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import structlog

from app.models.user import User
from app.models.audio_log import AudioDownloadLog, AssetStats, DailyStats
from app.schemas.auth import UserStats

logger = structlog.get_logger(__name__)


class StatsService:
    """Service for handling statistics operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_stats(self, user_id: int) -> UserStats:
        """Get statistics for a specific user"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        # Calculate success rate
        success_rate = 0.0
        if user.total_downloads > 0:
            success_rate = (user.successful_downloads / user.total_downloads) * 100
        
        return UserStats(
            total_commands=user.total_commands,
            total_downloads=user.total_downloads,
            successful_downloads=user.successful_downloads,
            failed_downloads=user.failed_downloads,
            success_rate=round(success_rate, 2),
            first_seen=user.created_at,
            last_seen=user.last_seen
        )
    
    async def get_global_stats(self) -> dict:
        """Get global platform statistics"""
        try:
            # Total users
            total_users_result = await self.db.execute(select(func.count(User.id)))
            total_users = total_users_result.scalar() or 0
            
            # Total downloads
            total_downloads_result = await self.db.execute(select(func.sum(User.total_downloads)))
            total_downloads = total_downloads_result.scalar() or 0
            
            # Successful downloads
            successful_downloads_result = await self.db.execute(select(func.sum(User.successful_downloads)))
            successful_downloads = successful_downloads_result.scalar() or 0
            
            # Failed downloads
            failed_downloads_result = await self.db.execute(select(func.sum(User.failed_downloads)))
            failed_downloads = failed_downloads_result.scalar() or 0
            
            # Success rate
            success_rate = 0.0
            if total_downloads > 0:
                success_rate = (successful_downloads / total_downloads) * 100
            
            # Most active user
            most_active_result = await self.db.execute(
                select(User).order_by(User.total_downloads.desc()).limit(1)
            )
            most_active_user = most_active_result.scalar_one_or_none()
            
            # Most downloaded asset
            most_downloaded_result = await self.db.execute(
                select(AssetStats).order_by(AssetStats.total_downloads.desc()).limit(1)
            )
            most_downloaded_asset = most_downloaded_result.scalar_one_or_none()
            
            return {
                "total_users": total_users,
                "total_downloads": total_downloads,
                "successful_downloads": successful_downloads,
                "failed_downloads": failed_downloads,
                "success_rate": round(success_rate, 2),
                "most_active_user": {
                    "username": most_active_user.username,
                    "downloads": most_active_user.total_downloads
                } if most_active_user else None,
                "most_downloaded_asset": {
                    "asset_id": most_downloaded_asset.asset_id,
                    "name": most_downloaded_asset.asset_name,
                    "downloads": most_downloaded_asset.total_downloads
                } if most_downloaded_asset else None
            }
            
        except Exception as e:
            logger.error("Error getting global stats", error=str(e))
            raise
    
    async def get_popular_assets(self, limit: int = 10) -> list[dict]:
        """Get most popular assets"""
        try:
            result = await self.db.execute(
                select(AssetStats)
                .order_by(AssetStats.total_downloads.desc())
                .limit(limit)
            )
            assets = result.scalars().all()
            
            return [
                {
                    "asset_id": asset.asset_id,
                    "asset_name": asset.asset_name,
                    "creator": asset.creator,
                    "total_downloads": asset.total_downloads,
                    "successful_downloads": asset.successful_downloads,
                    "failed_downloads": asset.failed_downloads,
                    "success_rate": round(
                        (asset.successful_downloads / asset.total_downloads) * 100 
                        if asset.total_downloads > 0 else 0, 2
                    ),
                    "unique_users": asset.unique_users,
                    "first_downloaded": asset.first_downloaded,
                    "last_downloaded": asset.last_downloaded
                }
                for asset in assets
            ]
            
        except Exception as e:
            logger.error("Error getting popular assets", error=str(e))
            raise
    
    async def get_daily_stats(self, days: int = 7) -> list[dict]:
        """Get daily statistics for the specified number of days"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            result = await self.db.execute(
                select(DailyStats)
                .where(DailyStats.date >= start_date)
                .order_by(DailyStats.date.desc())
            )
            daily_stats = result.scalars().all()
            
            return [
                {
                    "date": stats.date.strftime("%Y-%m-%d"),
                    "commands_used": stats.commands_used,
                    "downloads_attempted": stats.downloads_attempted,
                    "successful_downloads": stats.successful_downloads,
                    "failed_downloads": stats.failed_downloads,
                    "unique_users": stats.unique_users,
                    "success_rate": round(
                        (stats.successful_downloads / stats.downloads_attempted) * 100 
                        if stats.downloads_attempted > 0 else 0, 2
                    ),
                    "avg_response_time": stats.avg_response_time,
                    "total_requests": stats.total_requests
                }
                for stats in daily_stats
            ]
            
        except Exception as e:
            logger.error("Error getting daily stats", error=str(e))
            raise
