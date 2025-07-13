from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "Roblox Audio API",
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    # Add database connectivity check here if needed
    return {
        "status": "ready",
        "database": "connected",
        "cache": "available"
    }
