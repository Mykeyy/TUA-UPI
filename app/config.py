from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    API_TITLE: str = "Roblox Audio API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "A REST API for downloading Roblox audio files"
    
    # Database
    DATABASE_URL: str = "sqlite:///./audio_api.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Roblox
    ROBLOX_COOKIE: str = ""
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_DOWNLOADS_PER_HOUR: int = 100
    RATE_LIMIT_BATCH_SIZE: int = 10
    
    # File Storage
    TEMP_DIR: str = "./temp"
    MAX_FILE_SIZE_MB: int = 50
    CLEANUP_INTERVAL_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Email Settings
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@ultimate-api.com"
    MAIL_FROM_NAME: str = "The Ultimate API"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    
    # Admin Settings (Pre-configured admin user)
    ADMIN_EMAIL: str = "mykey@apiadmin.dev"
    ADMIN_PASSWORD: str = "1283ya123c"
    ADMIN_USERNAME: str = "admin_mykey"
    
    # Email Verification
    EMAIL_VERIFICATION_SECRET: str = "email-verification-secret-change-in-production"
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    
    # API Rate Limits
    FREE_TIER_DAILY_LIMIT: int = 1000
    PREMIUM_TIER_DAILY_LIMIT: int = 10000
    
    # Frontend URL for email links
    FRONTEND_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def configure_logging():
    """Configure logging to reduce verbosity"""
    import logging
    
    # Suppress noisy loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.ERROR)
    logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
    
    # Set root logger to WARNING to reduce noise
    logging.getLogger().setLevel(logging.WARNING)
