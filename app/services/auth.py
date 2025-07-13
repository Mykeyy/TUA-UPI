from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional
import secrets
import structlog
import hashlib

from app.models.user import User
from app.schemas.auth import (
    UserCreate, Token, APIKeyResponse, UserResponse, 
    APIKeyCreate, APIKeyInfo, ClientCredentials, ClientCredentialsResponse,
    EmailVerificationRequest, EmailVerificationConfirm,
    PasswordResetRequest, PasswordResetConfirm, UserProfileUpdate
)
from app.config import settings

logger = structlog.get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Enhanced authentication service with email verification and comprehensive features"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # Import here to avoid circular imports
        try:
            from app.services.email import EmailService
            self.email_service = EmailService()
        except ImportError:
            logger.warning("Email service not available")
            self.email_service = None
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    async def _reset_daily_downloads_if_needed(self, user: User):
        """Reset daily downloads if it's a new day"""
        now = datetime.utcnow()
        if user.last_daily_reset is None or user.last_daily_reset.date() < now.date():
            await self.db.execute(
                update(User)
                .where(User.id == user.id)
                .values(daily_downloads=0, last_daily_reset=now)
            )
            await self.db.commit()
            # Refresh the user object to get updated values
            await self.db.refresh(user)
    
    def _user_to_response(self, user: User) -> UserResponse:
        """Convert User model to UserResponse schema"""
        # Create a dictionary with all user attributes plus calculated fields
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_verified": user.is_verified,
            "is_premium": user.is_premium,
            "total_commands": user.total_commands,
            "total_downloads": user.total_downloads,
            "successful_downloads": user.successful_downloads,
            "failed_downloads": user.failed_downloads,
            "daily_downloads": user.daily_downloads,
            "daily_limit": user.daily_limit,
            "created_at": user.created_at,
            "last_seen": user.last_seen,
            "last_login": user.last_login,
            "has_api_key": bool(user.api_key),
            "api_key_created_at": user.api_key_created_at,
        }
        return UserResponse(**user_dict)
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with email verification"""
        # Check if user already exists
        result = await self.db.execute(
            select(User).where(
                (User.username == user_data.username) | 
                (User.email == user_data.email)
            )
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            # Check which field conflicts
            existing_username = await self.db.execute(
                select(User).where(User.username == user_data.username)
            )
            if existing_username.scalar_one_or_none():
                raise ValueError("Username already exists")
            else:
                raise ValueError("Email already exists")
        
        # Create new user
        hashed_password = self.get_password_hash(user_data.password)
        
        # Check if this is the admin user
        is_admin = user_data.email == settings.ADMIN_EMAIL
        is_verified = is_admin  # Admin is pre-verified
        
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            display_name=user_data.display_name,
            is_admin=is_admin,
            is_verified=is_verified,
            daily_limit=settings.PREMIUM_TIER_DAILY_LIMIT if is_admin else settings.FREE_TIER_DAILY_LIMIT,
            is_premium=is_admin,
            last_daily_reset=datetime.utcnow()
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        # Send verification email (unless it's admin)
        if not is_admin and self.email_service:
            try:
                token = self.email_service.generate_verification_token(user_data.email)
                await self.db.execute(
                    update(User)
                    .where(User.id == user.id)
                    .values(
                        email_verification_token=token,
                        email_verification_sent_at=datetime.utcnow()
                    )
                )
                await self.db.commit()
                
                await self.email_service.send_verification_email(
                    user_data.email, 
                    user_data.username, 
                    token
                )
            except Exception as e:
                logger.error("Failed to send verification email", user_id=user.id, error=str(e))
                # Don't fail user creation if email fails
        
        logger.info("User created", user_id=user.id, username=user_data.username, is_admin=is_admin)
        return user
    
    async def authenticate_user(self, username: str, password: str) -> Token:
        """Authenticate user and return token with user info"""
        # Check if user exists by username or email
        result = await self.db.execute(
            select(User).where(
                (User.username == username) | (User.email == username)
            )
        )
        user = result.scalar_one_or_none()
        
        if not user or not self.verify_password(password, user.hashed_password):  # type: ignore
            raise ValueError("Incorrect username or password")
        
        if not user.is_active:  # type: ignore
            raise ValueError("Account is disabled")
        
        # Update last login and last seen using update query
        now = datetime.utcnow()
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_login=now, last_seen=now)
        )
        
        # Reset daily downloads if needed
        await self._reset_daily_downloads_if_needed(user)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # Convert user to response schema
        user_response = self._user_to_response(user)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
            user=user_response
        )
    
    async def generate_api_key(self, user_id: int, name: Optional[str] = None) -> APIKeyResponse:
        """Generate a new API key for user"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        # Generate secure API key
        api_key = f"rapi_{secrets.token_urlsafe(32)}"
        now = datetime.utcnow()
        
        # Use update query to modify the user
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                api_key=api_key,
                api_key_created_at=now,
                api_key_name=name
            )
        )
        await self.db.commit()
        
        return APIKeyResponse(
            api_key=api_key,
            name=name,
            created_at=now,
            message="API key generated successfully"
        )
    
    async def get_api_key_info(self, user_id: int) -> APIKeyInfo:
        """Get API key information without exposing the full key"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.api_key:  # type: ignore
            raise ValueError("No API key found")
        
        return APIKeyInfo(
            name=user.api_key_name,  # type: ignore
            created_at=user.api_key_created_at,  # type: ignore
            last_used=user.api_key_last_used,  # type: ignore
            key_preview=user.api_key[:8] + "..."  # type: ignore
        )
    
    async def revoke_api_key(self, user_id: int):
        """Revoke user's API key"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        # Use update query to clear API key fields
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                api_key=None,
                api_key_created_at=None,
                api_key_name=None,
                api_key_last_used=None
            )
        )
        await self.db.commit()
    
    async def generate_client_credentials(self, user_id: int, client_name: str) -> ClientCredentialsResponse:
        """Generate Discord bot client credentials"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        # Generate client ID and secret
        client_id = f"client_{secrets.token_urlsafe(16)}"
        client_secret = f"secret_{secrets.token_urlsafe(24)}"
        
        # Hash the client secret for storage
        hashed_secret = self.get_password_hash(client_secret)
        
        # Use update query to set client credentials
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                client_id=client_id,
                client_secret=hashed_secret,
                client_name=client_name
            )
        )
        await self.db.commit()
        
        return ClientCredentialsResponse(
            client_id=client_id,
            client_secret=client_secret,
            client_name=client_name
        )
    
    async def send_verification_email(self, email: str):
        """Send email verification email"""
        if not self.email_service:
            raise ValueError("Email service not available")
            
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        if user.is_verified:  # type: ignore
            raise ValueError("Email already verified")
        
        # Generate new token
        token = self.email_service.generate_verification_token(email)
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                email_verification_token=token,
                email_verification_sent_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        
        await self.email_service.send_verification_email(
            email, 
            user.username,  # type: ignore
            token
        )
    
    async def verify_email(self, token: str):
        """Verify email address using token"""
        if not self.email_service:
            raise ValueError("Email service not available")
            
        try:
            email = self.email_service.verify_verification_token(token)
        except ValueError:
            raise ValueError("Invalid or expired verification token")
        
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        if user.is_verified:  # type: ignore
            raise ValueError("Email already verified")
        
        # Use update query to verify email
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                is_verified=True,
                email_verification_token=None,
                email_verification_sent_at=None
            )
        )
        await self.db.commit()
        
        # Send welcome email
        try:
            await self.email_service.send_welcome_email(email, user.username)  # type: ignore
        except Exception as e:
            logger.error("Failed to send welcome email", user_id=user.id, error=str(e))
    
    async def request_password_reset(self, email: str):
        """Request password reset"""
        if not self.email_service:
            raise ValueError("Email service not available")
            
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Don't reveal if email exists
            return
        
        # Generate reset token
        token = self.email_service.generate_password_reset_token(email)
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                password_reset_token=token,
                password_reset_sent_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        
        await self.email_service.send_password_reset_email(
            email, 
            user.username,  # type: ignore
            token
        )
    
    async def reset_password(self, token: str, new_password: str):
        """Reset password using token"""
        if not self.email_service:
            raise ValueError("Email service not available")
            
        try:
            email = self.email_service.verify_password_reset_token(token)
        except ValueError:
            raise ValueError("Invalid or expired reset token")
        
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        # Update password using update query
        hashed_password = self.get_password_hash(new_password)
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                hashed_password=hashed_password,
                password_reset_token=None,
                password_reset_sent_at=None
            )
        )
        await self.db.commit()
    
    async def update_user_profile(self, user_id: int, profile_data: UserProfileUpdate) -> UserResponse:
        """Update user profile"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        # Build update values dict
        update_values = {}
        if profile_data.display_name is not None:
            update_values["display_name"] = profile_data.display_name
        if profile_data.bio is not None:
            update_values["bio"] = profile_data.bio
        
        if update_values:
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(**update_values)
            )
            await self.db.commit()
            await self.db.refresh(user)
        
        return self._user_to_response(user)
    
    async def create_admin_user_if_not_exists(self):
        """Create admin user if it doesn't exist"""
        result = await self.db.execute(
            select(User).where(User.email == settings.ADMIN_EMAIL)
        )
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            admin_data = UserCreate(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                password=settings.ADMIN_PASSWORD,
                display_name="Admin User"
            )
            
            admin_user = await self.create_user(admin_data)
            logger.info("Admin user created", user_id=admin_user.id)
        
        return admin_user
