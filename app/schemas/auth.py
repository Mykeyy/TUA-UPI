from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re


class UserCreate(BaseModel):
    """Schema for user registration request"""
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50, 
        pattern="^[a-zA-Z0-9_-]+$",
        title="Username",
        description="Unique username for the account"
    )
    email: EmailStr = Field(
        ...,
        title="Email Address",
        description="Valid email address for the account"
    )
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=100,
        title="Password",
        description="Strong password with minimum 8 characters"
    )
    display_name: Optional[str] = Field(
        None,
        max_length=100,
        title="Display Name",
        description="Optional display name"
    )

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "john_doe",
                "email": "john.doe@example.com",
                "password": "SecurePassword123!",
                "display_name": "John Doe"
            }
        }
    }


class UserLogin(BaseModel):
    """Schema for user login request"""
    username: str = Field(
        ...,
        title="Username",
        description="Your account username"
    )
    password: str = Field(
        ...,
        title="Password", 
        description="Your account password"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "john_doe",
                "password": "SecurePassword123!"
            }
        }
    }


class EmailVerificationRequest(BaseModel):
    """Schema for email verification request"""
    email: EmailStr = Field(..., title="Email", description="Email to verify")


class EmailVerificationConfirm(BaseModel):
    """Schema for email verification confirmation"""
    token: str = Field(..., title="Token", description="Verification token from email")


class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr = Field(..., title="Email", description="Email to reset password for")


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str = Field(..., title="Token", description="Reset token from email")
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=100,
        title="New Password",
        description="New password"
    )

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v


class UserResponse(BaseModel):
    """Schema for user profile information"""
    id: int = Field(..., title="User ID", description="Unique user identifier")
    username: str = Field(..., title="Username", description="User's unique username")
    email: str = Field(..., title="Email", description="User's email address")
    display_name: Optional[str] = Field(None, title="Display Name", description="User's display name")
    is_active: bool = Field(..., title="Active Status", description="Whether the user account is active")
    is_admin: bool = Field(..., title="Admin Status", description="Whether the user has admin privileges")
    is_verified: bool = Field(..., title="Verified Status", description="Whether the user's email is verified")
    is_premium: bool = Field(..., title="Premium Status", description="Whether the user has premium features")
    
    # Usage tracking
    total_commands: int = Field(..., title="Total Commands", description="Total number of commands executed")
    total_downloads: int = Field(..., title="Total Downloads", description="Total number of downloads attempted")
    successful_downloads: int = Field(..., title="Successful Downloads", description="Number of successful downloads")
    failed_downloads: int = Field(..., title="Failed Downloads", description="Number of failed downloads")
    daily_downloads: int = Field(..., title="Daily Downloads", description="Downloads today")
    daily_limit: int = Field(..., title="Daily Limit", description="Daily download limit")
    
    # Timestamps
    created_at: datetime = Field(..., title="Created At", description="Account creation timestamp")
    last_seen: Optional[datetime] = Field(None, title="Last Seen", description="Last activity timestamp")
    last_login: Optional[datetime] = Field(None, title="Last Login", description="Last login timestamp")
    
    # API Key info
    has_api_key: bool = Field(..., title="Has API Key", description="Whether user has an active API key")
    api_key_created_at: Optional[datetime] = Field(None, title="API Key Created", description="API key creation timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "john.doe@example.com",
                "display_name": "John Doe",
                "is_active": True,
                "is_admin": False,
                "is_verified": True,
                "is_premium": False,
                "total_commands": 150,
                "total_downloads": 125,
                "successful_downloads": 120,
                "failed_downloads": 5,
                "daily_downloads": 25,
                "daily_limit": 1000,
                "created_at": "2024-01-15T10:30:00",
                "last_seen": "2024-07-13T14:22:30",
                "last_login": "2024-07-13T09:15:00",
                "has_api_key": True,
                "api_key_created_at": "2024-01-16T08:45:00"
            }
        }
    }


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    display_name: Optional[str] = Field(None, max_length=100, title="Display Name")
    bio: Optional[str] = Field(None, max_length=500, title="Bio")


class APIKeyCreate(BaseModel):
    """Schema for API key creation request"""
    name: Optional[str] = Field(None, max_length=100, title="API Key Name", description="Optional name for the API key")


class APIKeyResponse(BaseModel):
    """Schema for API key generation response"""
    api_key: str = Field(..., title="API Key", description="Generated API key for authentication")
    name: Optional[str] = Field(None, title="API Key Name", description="Name of the API key")
    created_at: datetime = Field(..., title="Created At", description="API key creation timestamp")
    message: str = Field(..., title="Message", description="Success message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "api_key": "rapi_1234567890abcdef",
                "name": "My Discord Bot",
                "created_at": "2024-07-13T14:22:30",
                "message": "API key generated successfully"
            }
        }
    }


class APIKeyInfo(BaseModel):
    """Schema for API key information (without revealing the key)"""
    name: Optional[str] = Field(None, title="API Key Name")
    created_at: datetime = Field(..., title="Created At")
    last_used: Optional[datetime] = Field(None, title="Last Used")
    key_preview: str = Field(..., title="Key Preview", description="First 8 characters of the key")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "My Discord Bot",
                "created_at": "2024-07-13T14:22:30",
                "last_used": "2024-07-13T16:45:00",
                "key_preview": "rapi_123"
            }
        }
    }


class ClientCredentials(BaseModel):
    """Schema for Discord bot client credentials"""
    client_name: str = Field(..., max_length=100, title="Client Name", description="Name of your Discord bot/app")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "client_name": "My Audio Bot"
            }
        }
    }


class ClientCredentialsResponse(BaseModel):
    """Schema for client credentials response"""
    client_id: str = Field(..., title="Client ID", description="Generated client ID")
    client_secret: str = Field(..., title="Client Secret", description="Generated client secret")
    client_name: str = Field(..., title="Client Name", description="Name of the client")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "client_id": "client_123456789",
                "client_secret": "secret_abcdefghijklmnop",
                "client_name": "My Audio Bot"
            }
        }
    }


class UserStats(BaseModel):
    """Schema for user statistics overview"""
    total_commands: int = Field(..., title="Total Commands", description="Total number of commands executed")
    total_downloads: int = Field(..., title="Total Downloads", description="Total number of downloads attempted")
    successful_downloads: int = Field(..., title="Successful Downloads", description="Number of successful downloads")
    failed_downloads: int = Field(..., title="Failed Downloads", description="Number of failed downloads")
    success_rate: float = Field(..., title="Success Rate", description="Download success rate as percentage")
    daily_downloads: int = Field(..., title="Daily Downloads", description="Downloads today")
    daily_limit: int = Field(..., title="Daily Limit", description="Daily download limit")
    remaining_today: int = Field(..., title="Remaining Today", description="Remaining downloads today")
    first_seen: datetime = Field(..., title="First Seen", description="First activity timestamp")
    last_seen: Optional[datetime] = Field(None, title="Last Seen", description="Last activity timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_commands": 150,
                "total_downloads": 125,
                "successful_downloads": 120,
                "failed_downloads": 5,
                "success_rate": 96.0,
                "daily_downloads": 25,
                "daily_limit": 1000,
                "remaining_today": 975,
                "first_seen": "2024-01-15T10:30:00",
                "last_seen": "2024-07-13T14:22:30"
            }
        }
    }


class Token(BaseModel):
    """Schema for authentication token response"""
    access_token: str = Field(..., title="Access Token", description="JWT access token for authentication")
    token_type: str = Field(default="bearer", title="Token Type", description="Type of the authentication token")
    expires_in: int = Field(..., title="Expires In", description="Token expiration time in seconds")
    user: UserResponse = Field(..., title="User", description="User information")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": 1,
                    "username": "john_doe",
                    "email": "john.doe@example.com",
                    "is_verified": True
                }
            }
        }
    }


class TokenData(BaseModel):
    """Schema for token payload data"""
    username: Optional[str] = Field(None, title="Username", description="Username from token payload")


class EmailResponse(BaseModel):
    """Schema for email operation responses"""
    message: str = Field(..., title="Message", description="Response message")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Verification email sent successfully"
            }
        }
    }
