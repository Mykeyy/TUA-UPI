from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import uvicorn
import structlog

from app.config import settings
from app.database import create_tables
from app.routers import auth, audio, stats, health, docs
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Create database tables
    await create_tables()
    
    logger = structlog.get_logger()
    logger.info("Application startup complete", version=settings.API_VERSION)
    
    yield
    
    # Shutdown
    logger.info("Application shutdown complete")


def custom_openapi():
    """Generate custom OpenAPI schema with improved schema names"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="🎵 The Ultimate API",
        version=settings.API_VERSION,
        description=app.description,
        routes=app.routes,
        servers=app.servers,
        tags=app.openapi_tags,
    )
    
    # Customize schema names to be more user-friendly
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        schemas = openapi_schema["components"]["schemas"]
        
        # Create a mapping of old names to new names
        schema_renames = {
            "UserCreate": "User Registration Request",
            "UserLogin": "User Login Request", 
            "UserResponse": "User Profile",
            "UserStats": "User Statistics",
            "Token": "Authentication Token",
            "TokenData": "Token Payload",
            "APIKeyResponse": "API Key Response",
            "AssetInfo": "Audio Asset Information",
            "AudioDownloadRequest": "Single Audio Download Request",
            "AudioBatchRequest": "Batch Audio Download Request",
            "AudioDownloadResponse": "Audio Download Result",
            "AudioBatchResponse": "Batch Download Results",
            "AudioDownloadLog": "Download Log Entry",
            "AssetStatsResponse": "Asset Statistics",
            "GlobalStatsResponse": "Global API Statistics",
            "PopularAssetResponse": "Popular Asset",
            "UserRankingResponse": "User Ranking",
            "TimeSeriesData": "Time Series Data Point",
            "TimeSeriesResponse": "Time Series Statistics",
            "HealthStatus": "API Health Status"
        }
        
        # Apply the renames by creating new schema entries
        new_schemas = {}
        for old_name, schema in schemas.items():
            new_name = schema_renames.get(old_name, old_name)
            new_schemas[new_name] = schema
        
        openapi_schema["components"]["schemas"] = new_schemas
    
    # Add custom info
    openapi_schema["info"]["x-logo"] = {
        "url": "https://via.placeholder.com/120x120/3ac062/ffffff?text=TUA",
        "altText": "The Ultimate API Logo"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="🎵 The Ultimate API",
        description="""
        # The Ultimate Roblox Audio API
        
        **Enterprise-grade audio downloading service** for Roblox developers and content creators.
        
        ## Features
        
        - 🎵 **High-Quality Audio Downloads** - Download audio assets with metadata
        - 📦 **Batch Processing** - Download multiple assets in a single request
        - 👥 **User Management** - Secure authentication and user profiles
        - 📊 **Advanced Analytics** - Detailed statistics and usage tracking
        - 🛡️ **Rate Limiting** - Built-in protection against abuse
        - 🔒 **Secure Authentication** - JWT tokens and API key support
        - 📈 **Real-time Monitoring** - Health checks and performance metrics
        
        ## Getting Started
        
        1. Register for an account using the `/auth/register` endpoint
        2. Login to get your access token from `/auth/login`
        3. Start downloading audio using the `/audio/download` endpoint
        
        ## Rate Limits
        
        - **Free Users**: 50 requests per hour
        - **Premium Users**: 500 requests per hour
        - **Enterprise**: Custom limits available
        
        ## Support
        
        Need help? Check our documentation or contact support.
        """, 
        version=settings.API_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url=None,  # Disable default docs in favor of Stoplight Elements
        redoc_url=None,  # Disable redoc
        openapi_url="/docs/openapi.json",  # Custom OpenAPI URL
        contact={
            "name": "The Ultimate API Support",
            "url": "https://github.com/yourusername/ultimate-api",
            "email": "support@ultimate-api.com"
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        servers=[
            {
                "url": "https://api.ultimate-audio.com",
                "description": "Production server"
            },
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            }
        ],
        openapi_tags=[
            {
                "name": "Authentication",
                "description": "🔐 User authentication and account management operations",
            },
            {
                "name": "Audio",
                "description": "🎵 Audio downloading and asset management operations",
            },
            {
                "name": "Statistics", 
                "description": "📊 Analytics and usage statistics",
            },
            {
                "name": "Health",
                "description": "💚 API health monitoring and status checks",
            },
            {
                "name": "Documentation",
                "description": "📚 API documentation and specifications",
            }
        ]
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app"]
    )
    
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # Include routers
    app.include_router(docs.router, tags=["Documentation"])
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    app.include_router(audio.router, prefix="/audio", tags=["Audio"])
    app.include_router(stats.router, prefix="/stats", tags=["Statistics"])

    # Set custom OpenAPI schema generation
    app.openapi = custom_openapi

    return app


app = create_app()


@app.get("/")
async def root():
    """API root endpoint - redirects to documentation"""
    return {
        "message": "The Ultimate API - Roblox Audio Downloading Service",
        "version": settings.API_VERSION,
        "documentation": "/docs",
        "health_check": "/health",
        "openapi_spec": "/docs/openapi.json",
        "features": [
            "🎵 Audio Downloads",
            "📦 Batch Processing", 
            "👥 User Management",
            "📊 Advanced Analytics",
            "🛡️ Rate Limiting",
            "🔒 Secure Authentication"
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
