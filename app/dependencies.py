from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from jose import JWTError, jwt
from datetime import datetime
import structlog

from app.database import get_async_session
from app.models.user import User
from app.schemas.auth import UserResponse, TokenData
from app.config import settings

logger = structlog.get_logger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session)
) -> UserResponse:
    """Get current authenticated user"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub") or ""
        if not username:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # Get user from database with API keys relationship
    result = await db.execute(
        select(User)
        .options(selectinload(User.api_keys))
        .where(User.username == token_data.username)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    # Update last seen
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_seen=datetime.utcnow())
    )
    await db.commit()
    
    # Use AuthService to properly convert User to UserResponse
    from app.services.auth import AuthService
    auth_service = AuthService(db)
    return auth_service._user_to_response(user)


async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """Get current active user (redundant check but kept for clarity)"""
    return current_user


async def get_admin_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """Get current user and verify admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def rate_limit_check():
    """Rate limiting dependency (placeholder)"""
    # This would be implemented with Redis or similar
    # For now, it's a placeholder
    pass


async def api_key_auth(
    api_key: str,
    db: AsyncSession = Depends(get_async_session)
) -> UserResponse:
    """Authenticate using API key"""
    
    result = await db.execute(
        select(User).where(User.api_key == api_key, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Update last seen
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_seen=datetime.utcnow())
    )
    await db.commit()
    
    # Use AuthService to properly convert User to UserResponse
    from app.services.auth import AuthService
    auth_service = AuthService(db)
    return auth_service._user_to_response(user)
