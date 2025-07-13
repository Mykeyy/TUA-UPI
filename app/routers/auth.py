from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional
import structlog

from app.database import get_async_session
from app.schemas.auth import (
    UserCreate, UserLogin, UserResponse, Token, APIKeyResponse, APIKeyCreate, APIKeyInfo,
    ClientCredentials, ClientCredentialsResponse, EmailVerificationRequest, 
    EmailVerificationConfirm, PasswordResetRequest, PasswordResetConfirm,
    UserProfileUpdate, EmailResponse
)
from app.services.auth import AuthService
from app.dependencies import get_current_user, get_admin_user

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """Register a new user with email verification"""
    try:
        auth_service = AuthService(db)
        user = await auth_service.create_user(user_data)
        logger.info("User registered successfully", user_id=user.id, username=user.username)
        # Use AuthService to properly convert User to UserResponse
        return auth_service._user_to_response(user)
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
    """Login user and return access token with user info"""
    try:
        auth_service = AuthService(db)
        token = await auth_service.authenticate_user(
            user_credentials.username_or_email,
            user_credentials.password
        )
        logger.info("User logged in successfully", username_or_email=user_credentials.username_or_email)
        return token
    except ValueError as e:
        logger.warning("Login failed", username_or_email=user_credentials.username_or_email, error=str(e))
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


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update user profile"""
    try:
        auth_service = AuthService(db)
        updated_user = await auth_service.update_user_profile(current_user.id, profile_data)
        logger.info("Profile updated", user_id=current_user.id)
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error updating profile", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/api-key", response_model=APIKeyResponse)
async def generate_api_key(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    request: Optional[APIKeyCreate] = Body(None)
):
    """Generate a new API key for the current user"""
    try:
        auth_service = AuthService(db)
        name = request.name if request else None
        api_key_response = await auth_service.generate_api_key(current_user.id, name)
        logger.info("API key generated", user_id=current_user.id)
        return api_key_response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error generating API key", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate API key"
        )


@router.get("/api-key", response_model=APIKeyInfo)
async def get_api_key_info(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get API key information (without exposing the full key)"""
    try:
        auth_service = AuthService(db)
        api_key_info = await auth_service.get_api_key_info(current_user.id)
        return api_key_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error getting API key info", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get API key information"
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


@router.post("/client-credentials", response_model=ClientCredentialsResponse)
async def generate_client_credentials(
    credentials: ClientCredentials,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Generate Discord bot client credentials"""
    try:
        auth_service = AuthService(db)
        client_creds = await auth_service.generate_client_credentials(
            current_user.id, 
            credentials.client_name
        )
        logger.info("Client credentials generated", user_id=current_user.id, client_name=credentials.client_name)
        return client_creds
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error generating client credentials", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate client credentials"
        )


@router.post("/send-verification-email", response_model=EmailResponse)
async def send_verification_email(
    request: EmailVerificationRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Send email verification email"""
    try:
        auth_service = AuthService(db)
        await auth_service.send_verification_email(request.email)
        return EmailResponse(message="Verification email sent successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error sending verification email", email=request.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )


@router.post("/verify-email", response_model=EmailResponse)
async def verify_email(
    request: EmailVerificationConfirm,
    db: AsyncSession = Depends(get_async_session)
):
    """Verify email address using token"""
    try:
        auth_service = AuthService(db)
        await auth_service.verify_email(request.token)
        return EmailResponse(message="Email verified successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error verifying email", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email"
        )


@router.post("/request-password-reset", response_model=EmailResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Request password reset email"""
    try:
        auth_service = AuthService(db)
        await auth_service.request_password_reset(request.email)
        return EmailResponse(message="Password reset email sent successfully")
    except Exception as e:
        logger.error("Error requesting password reset", email=request.email, error=str(e))
        # Always return success to prevent email enumeration
        return EmailResponse(message="If the email exists, a password reset link has been sent")


@router.post("/reset-password", response_model=EmailResponse)
async def reset_password(
    request: PasswordResetConfirm,
    db: AsyncSession = Depends(get_async_session)
):
    """Reset password using token"""
    try:
        auth_service = AuthService(db)
        await auth_service.reset_password(request.token, request.new_password)
        return EmailResponse(message="Password reset successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error resetting password", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.post("/admin/create-admin-user", response_model=UserResponse)
async def create_admin_user(
    db: AsyncSession = Depends(get_async_session)
):
    """Create admin user (public endpoint for initial setup)"""
    try:
        auth_service = AuthService(db)
        admin_user = await auth_service.create_admin_user_if_not_exists()
        return auth_service._user_to_response(admin_user)
    except Exception as e:
        logger.error("Error creating admin user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create admin user"
        )
