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
from app.models.api_key import APIKey
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
        # Check if user has any active API keys - handle lazy loading safely
        has_api_key = False
        latest_api_key = None
        
        try:
            # Safely access api_keys relationship
            if hasattr(user, 'api_keys') and user.api_keys is not None:
                active_keys = [key for key in user.api_keys if key.is_active]  # type: ignore
                if active_keys:
                    has_api_key = True
                    latest_api_key = max(active_keys, key=lambda k: k.created_at)  # type: ignore
        except Exception:
            # If there's any issue accessing the relationship, default to False
            has_api_key = False
            latest_api_key = None
        
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
            "has_api_key": has_api_key,
            "api_key_created_at": latest_api_key.created_at if latest_api_key else None,  # type: ignore
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
            select(User).options(selectinload(User.api_keys)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        # Check API key limits
        active_keys = [key for key in user.api_keys if key.is_active]
        max_keys = 10 if user.is_admin else 3  # type: ignore
        
        if len(active_keys) >= max_keys:
            user_type = "admin" if user.is_admin else "user"  # type: ignore
            raise ValueError(f"Maximum API key limit reached. {user_type.title()} accounts can have up to {max_keys} active API keys.")
        
        # Generate secure API key
        api_key = f"rapi_{secrets.token_urlsafe(32)}"
        now = datetime.utcnow()
        
        # Create new API key record
        new_api_key = APIKey(
            user_id=user_id,
            key_hash=hashlib.sha256(api_key.encode()).hexdigest(),
            key_preview=api_key[:8] + "...",
            name=name or f"API Key {now.strftime('%Y-%m-%d %H:%M')}",
            created_at=now,
            is_active=True
        )
        
        self.db.add(new_api_key)
        await self.db.commit()
        await self.db.refresh(new_api_key)
        
        return APIKeyResponse(
            api_key=api_key,
            name=name or f"API Key {now.strftime('%Y-%m-%d %H:%M')}",
            created_at=now,
            message="API key generated successfully"
        )
    
    async def get_api_key_info(self, user_id: int) -> Optional[APIKeyInfo]:
        """Get API key information without exposing the full key"""
        result = await self.db.execute(
            select(User).options(selectinload(User.api_keys)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.api_keys:
            return None
        
        # Get the most recently created active API key
        active_keys = [key for key in user.api_keys if key.is_active]
        if not active_keys:
            return None
        
        latest_key = max(active_keys, key=lambda k: k.created_at)
        
        return APIKeyInfo(
            id=latest_key.id,  # type: ignore
            name=latest_key.name,  # type: ignore
            created_at=latest_key.created_at,  # type: ignore
            last_used=latest_key.last_used,  # type: ignore
            key_preview=latest_key.key_preview,  # type: ignore
            usage_count=latest_key.usage_count  # type: ignore
        )
    
    async def revoke_api_key(self, user_id: int, key_id: Optional[int] = None):
        """Revoke user's API key(s)"""
        if key_id:
            # Revoke specific API key
            await self.db.execute(
                update(APIKey)
                .where(APIKey.user_id == user_id, APIKey.id == key_id)
                .values(is_active=False, revoked_at=datetime.utcnow())
            )
        else:
            # Revoke all API keys for user
            await self.db.execute(
                update(APIKey)
                .where(APIKey.user_id == user_id)
                .values(is_active=False, revoked_at=datetime.utcnow())
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
            print(f"   ✅ Created admin user: {admin_user.username}")
        else:
            print(f"   ✅ Admin user exists: {admin_user.username}")
        
        return admin_user
    
    async def list_api_keys(self, user_id: int) -> list[APIKeyInfo]:
        """List all active API keys for a user"""
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.user_id == user_id, APIKey.is_active == True)
            .order_by(APIKey.created_at.desc())
        )
        api_keys = result.scalars().all()
        
        return [
            APIKeyInfo(
                id=key.id,  # type: ignore
                name=key.name,  # type: ignore
                created_at=key.created_at,  # type: ignore
                last_used=key.last_used,  # type: ignore
                key_preview=key.key_preview,  # type: ignore
                usage_count=key.usage_count  # type: ignore
            )
            for key in api_keys
        ]
    
    async def validate_api_key(self, api_key: str) -> Optional[User]:
        """Validate an API key and return the associated user"""
        # Hash the provided key to compare with stored hash
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        result = await self.db.execute(
            select(APIKey)
            .options(selectinload(APIKey.user))
            .where(APIKey.key_hash == key_hash, APIKey.is_active == True)
        )
        api_key_record = result.scalar_one_or_none()
        
        if not api_key_record or not api_key_record.user:
            return None
        
        # Update last used timestamp and usage count
        await self.db.execute(
            update(APIKey)
            .where(APIKey.id == api_key_record.id)
            .values(
                last_used=datetime.utcnow(),
                usage_count=APIKey.usage_count + 1
            )
        )
        await self.db.commit()
        
        return api_key_record.user
