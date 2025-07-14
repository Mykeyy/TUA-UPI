from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import httpx
import aiofiles
import os
import tempfile
import structlog

from app.models.user import User
from app.models.audio_log import AudioDownloadLog, AssetStats
from app.schemas.audio import (
    AssetInfo, AudioDownloadResponse, AudioBatchResponse
)
from app.config import settings

logger = structlog.get_logger(__name__)


class AudioService:
    """Service for handling audio operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_asset_info(self, asset_id: int) -> AssetInfo:
        """Get information about an audio asset"""
        try:
            # Check if Roblox cookie is configured
            if not settings.ROBLOX_COOKIE:
                logger.warning("Roblox cookie not configured - using fallback mode", asset_id=asset_id)
                return AssetInfo(
                    asset_id=asset_id,
                    name=f"Audio Asset {asset_id}",
                    creator="Unknown (No Auth)",
                    description="Limited info - Roblox authentication not configured",
                    created=None,
                    updated=None
                )
            
            async with httpx.AsyncClient() as client:
                # Use Roblox API to get asset info
                url = f"https://assetdelivery.roblox.com/v1/asset/?id={asset_id}"
                headers = {
                    "Cookie": f".ROBLOSECURITY={settings.ROBLOX_COOKIE}",
                    "User-Agent": "Roblox/WinInet"
                }
                
                response = await client.get(url, headers=headers)
                
                # Handle 403 Forbidden specifically
                if response.status_code == 403:
                    logger.error("Roblox authentication failed - cookie may be invalid or expired", 
                               asset_id=asset_id, status_code=response.status_code)
                    # Return fallback info instead of failing
                    return AssetInfo(
                        asset_id=asset_id,
                        name=f"Audio Asset {asset_id}",
                        creator="Unknown (Auth Failed)",
                        description="Cookie expired or invalid - please update ROBLOX_COOKIE in .env",
                        created=None,
                        updated=None
                    )
                
                response.raise_for_status()
                
                # Try to get more detailed info from catalog API
                catalog_url = f"https://catalog.roblox.com/v1/catalog/items/details"
                catalog_payload = {"items": [{"itemType": "Asset", "id": asset_id}]}
                
                catalog_response = await client.post(catalog_url, json=catalog_payload)
                
                if catalog_response.status_code == 200:
                    catalog_data = catalog_response.json()
                    if catalog_data.get("data"):
                        item = catalog_data["data"][0]
                        return AssetInfo(
                            asset_id=asset_id,
                            name=item.get("name", f"Audio {asset_id}"),
                            creator=item.get("creatorName", "Unknown"),
                            description=item.get("description"),
                            created=item.get("created"),
                            updated=item.get("updated")
                        )
                
                # Fallback to basic info
                return AssetInfo(
                    asset_id=asset_id,
                    name=f"Audio {asset_id}",
                    creator="Unknown",
                    description="Information unavailable",
                    created=None,
                    updated=None
                )
                
        except Exception as e:
            logger.error("Error getting asset info", asset_id=asset_id, error=str(e))
            raise ValueError(f"Could not retrieve information for asset {asset_id}")
    
    async def download_audio(self, user_id: int, asset_id: int, place_id: str) -> AudioDownloadResponse:
        """Download a single audio file"""
        try:
            # Get asset info first
            asset_info = await self.get_asset_info(asset_id)
            
            # Get audio URL
            audio_url = await self._get_audio_url(asset_id, place_id)
            if not audio_url:
                await self._log_download(user_id, asset_id, asset_info.name, asset_info.creator, False, "Could not get audio URL")
                return AudioDownloadResponse(
                    success=False,
                    asset_id=asset_id,
                    asset_name=asset_info.name,
                    creator=asset_info.creator,
                    file_size=None,
                    download_url=None,
                    error_message="Could not get audio URL"
                )
            
            # Download the file
            file_size, download_url = await self._download_file(audio_url, asset_info.name)
            
            # Log successful download
            await self._log_download(user_id, asset_id, asset_info.name, asset_info.creator, True, None, file_size)
            
            return AudioDownloadResponse(
                success=True,
                asset_id=asset_id,
                asset_name=asset_info.name,
                creator=asset_info.creator,
                file_size=file_size,
                download_url=download_url,
                error_message=None
            )
            
        except Exception as e:
            logger.error("Error downloading audio", asset_id=asset_id, error=str(e))
            # Log failed download
            await self._log_download(user_id, asset_id, f"Asset {asset_id}", "Unknown", False, str(e))
            return AudioDownloadResponse(
                success=False,
                asset_id=asset_id,
                asset_name=f"Asset {asset_id}",
                creator="Unknown",
                file_size=None,
                download_url=None,
                error_message=str(e)
            )
    
    async def download_audio_batch(self, user_id: int, asset_ids: list[int], place_id: str) -> AudioBatchResponse:
        """Download multiple audio files"""
        downloads = []
        successful = 0
        failed = 0
        
        for asset_id in asset_ids:
            result = await self.download_audio(user_id, asset_id, place_id)
            downloads.append(result)
            
            if result.success:
                successful += 1
            else:
                failed += 1
        
        return AudioBatchResponse(
            total_requested=len(asset_ids),
            successful_downloads=successful,
            failed_downloads=failed,
            downloads=downloads
        )
    
    async def _get_audio_url(self, asset_id: int, place_id: str) -> str | None:
        """Get the actual audio file URL"""
        try:
            async with httpx.AsyncClient() as client:
                # This is a simplified version - you'll need to implement the actual Roblox audio location logic
                url = f"https://assetdelivery.roblox.com/v1/asset/?id={asset_id}"
                headers = {
                    "Cookie": f".ROBLOSECURITY={settings.ROBLOX_COOKIE}",
                    "User-Agent": "Roblox/WinInet"
                }
                
                response = await client.get(url, headers=headers, follow_redirects=True)
                if response.status_code == 200:
                    return str(response.url)
                
                return None
        except Exception as e:
            logger.error("Error getting audio URL", asset_id=asset_id, error=str(e))
            return None
    
    async def _download_file(self, url: str, filename: str) -> tuple[int, str]:
        """Download file and return size and local path"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Create temp file
                temp_dir = settings.TEMP_DIR
                os.makedirs(temp_dir, exist_ok=True)
                
                safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
                temp_path = os.path.join(temp_dir, f"{safe_filename}.ogg")
                
                async with aiofiles.open(temp_path, 'wb') as f:
                    await f.write(response.content)
                
                file_size = len(response.content)
                return file_size, temp_path
                
        except Exception as e:
            logger.error("Error downloading file", url=url, error=str(e))
            raise
    
    async def _log_download(self, user_id: int, asset_id: int, asset_name: str, creator: str, 
                          success: bool, error_message: str | None = None, file_size: int | None = None):
        """Log download attempt to database"""
        try:
            # Create download log
            download_log = AudioDownloadLog(
                user_id=user_id,
                asset_id=asset_id,
                asset_name=asset_name,
                creator=creator,
                success=success,
                file_size=file_size,
                error_message=error_message
            )
            self.db.add(download_log)
            
            # Update user stats
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                # Handle None values safely
                user.total_downloads = (user.total_downloads or 0) + 1  # type: ignore
                if success:
                    user.successful_downloads = (user.successful_downloads or 0) + 1  # type: ignore
                else:
                    user.failed_downloads = (user.failed_downloads or 0) + 1  # type: ignore
            
            # Update or create asset stats
            result = await self.db.execute(select(AssetStats).where(AssetStats.asset_id == asset_id))
            asset_stats = result.scalar_one_or_none()
            
            if not asset_stats:
                asset_stats = AssetStats(
                    asset_id=asset_id,
                    asset_name=asset_name,
                    creator=creator
                )
                self.db.add(asset_stats)
            
            # Handle None values safely for asset stats too
            asset_stats.total_downloads = (asset_stats.total_downloads or 0) + 1  # type: ignore
            asset_stats.last_downloaded = datetime.utcnow()  # type: ignore
            if success:
                asset_stats.successful_downloads = (asset_stats.successful_downloads or 0) + 1  # type: ignore
            else:
                asset_stats.failed_downloads = (asset_stats.failed_downloads or 0) + 1  # type: ignore
            
            await self.db.commit()
            
        except Exception as e:
            logger.error("Error logging download", error=str(e))
            await self.db.rollback()
