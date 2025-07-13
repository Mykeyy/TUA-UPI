from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import time
import structlog

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(list)
        self.downloads = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries (older than 1 hour)
        self._cleanup_old_entries(current_time)
        
        # Check rate limits
        if self._is_rate_limited(client_ip, request.url.path, current_time):
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                path=request.url.path
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Record this request
        self._record_request(client_ip, request.url.path, current_time)
        
        response = await call_next(request)
        return response
    
    def _cleanup_old_entries(self, current_time: float):
        """Remove entries older than 1 hour"""
        cutoff_time = current_time - 3600  # 1 hour ago
        
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                timestamp for timestamp in self.requests[ip] 
                if timestamp > cutoff_time
            ]
            if not self.requests[ip]:
                del self.requests[ip]
        
        for ip in list(self.downloads.keys()):
            self.downloads[ip] = [
                timestamp for timestamp in self.downloads[ip] 
                if timestamp > cutoff_time
            ]
            if not self.downloads[ip]:
                del self.downloads[ip]
    
    def _is_rate_limited(self, client_ip: str, path: str, current_time: float) -> bool:
        """Check if client is rate limited"""
        # General request rate limit (60 per minute)
        recent_requests = [
            timestamp for timestamp in self.requests[client_ip]
            if timestamp > current_time - 60  # Last minute
        ]
        
        if len(recent_requests) >= 60:
            return True
        
        # Download-specific rate limit (100 per hour)
        if "/audio/download" in path or "/audio/batch" in path:
            recent_downloads = [
                timestamp for timestamp in self.downloads[client_ip]
                if timestamp > current_time - 3600  # Last hour
            ]
            
            if len(recent_downloads) >= 100:
                return True
        
        return False
    
    def _record_request(self, client_ip: str, path: str, current_time: float):
        """Record a request"""
        self.requests[client_ip].append(current_time)
        
        # Also record as download if it's a download endpoint
        if "/audio/download" in path or "/audio/batch" in path:
            self.downloads[client_ip].append(current_time)
