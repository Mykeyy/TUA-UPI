from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import structlog

from app.database import get_async_session
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token, APIKeyResponse
from app.services.auth import AuthService
from app.dependencies import get_current_user

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """Register a new user"""
    try:
        auth_service = AuthService(db)
        user = await auth_service.create_user(user_data)
        logger.info("User registered successfully", user_id=user.id, username=user.username)
        return user
    except ValueError as e:
        logger.warning("User registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Unexpected error during registration", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_async_session)
):
    """Login user and return access token"""
    try:
        auth_service = AuthService(db)
        token = await auth_service.authenticate_user(
            user_credentials.username,
            user_credentials.password
        )
        logger.info("User logged in successfully", username=user_credentials.username)
        return token
    except ValueError as e:
        logger.warning("Login failed", username=user_credentials.username, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error("Unexpected error during login", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.post("/api-key", response_model=APIKeyResponse)
async def generate_api_key(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Generate a new API key for the current user"""
    try:
        auth_service = AuthService(db)
        api_key_data = await auth_service.generate_api_key(current_user.id)
        logger.info("API key generated", user_id=current_user.id)
        return api_key_data
    except Exception as e:
        logger.error("Error generating API key", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate API key"
        )


@router.delete("/api-key")
async def revoke_api_key(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Revoke the current user's API key"""
    try:
        auth_service = AuthService(db)
        await auth_service.revoke_api_key(current_user.id)
        logger.info("API key revoked", user_id=current_user.id)
        return {"message": "API key revoked successfully"}
    except Exception as e:
        logger.error("Error revoking API key", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )
