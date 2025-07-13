# Roblox Audio API

A REST API for downloading Roblox audio files, built with FastAPI. This API provides endpoints for retrieving audio files, asset information, and user statistics.

## Features

- 🎵 **Audio Download**: Download Roblox audio files by asset ID
- 📊 **Asset Information**: Get detailed information about audio assets
- 👥 **User Management**: User registration, authentication, and usage tracking
- 📈 **Statistics**: Comprehensive download and usage statistics
- 🔒 **Rate Limiting**: Built-in rate limiting to prevent abuse
- 🚀 **High Performance**: Async/await architecture with FastAPI
- 📚 **Auto Documentation**: Interactive API docs with Swagger UI

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL (optional, SQLite used by default)
- Redis (optional, for caching and rate limiting)

### Installation

1. Clone the repository:
```bash
git clone <your-repo>
cd roblox-audio-api
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get access token
- `GET /auth/me` - Get current user information

### Audio Operations
- `GET /audio/info/{asset_id}` - Get audio asset information
- `POST /audio/download` - Download single audio file
- `POST /audio/batch` - Download multiple audio files

### Statistics
- `GET /stats/user` - Get user statistics
- `GET /stats/global` - Get global statistics
- `GET /stats/assets` - Get asset statistics

## Environment Variables

Create a `.env` file with the following variables:

```
# Application
DEBUG=True
SECRET_KEY=your-secret-key-here
API_TITLE=Roblox Audio API
API_VERSION=1.0.0

# Database
DATABASE_URL=sqlite:///./audio_api.db
# DATABASE_URL=postgresql://user:password@localhost/audio_api

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Roblox Configuration
ROBLOX_COOKIE=your-roblox-cookie-here

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_DOWNLOADS_PER_HOUR=100

# File Storage
TEMP_DIR=./temp
MAX_FILE_SIZE_MB=50
```

## Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings
├── database.py          # Database connection and setup
├── dependencies.py      # Dependency injection functions
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── routers/             # API route handlers
├── services/            # Business logic services
├── utils/               # Utility functions
└── middleware/          # Custom middleware
```

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black app/
isort app/
```

### Type Checking
```bash
mypy app/
```

## Docker

Build and run with Docker:

```bash
docker build -t roblox-audio-api .
docker run -p 8000:8000 roblox-audio-api
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
