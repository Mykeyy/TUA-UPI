<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Roblox Audio API - Copilot Instructions

This is a FastAPI-based REST API project for downloading Roblox audio files. The project is structured to be scalable, maintainable, and follows modern Python development practices.

## Project Context

This API is based on existing Discord bot functionality for downloading Roblox audio files. The core features include:
- Audio file downloading from Roblox
- User authentication and management
- Usage statistics and logging
- Rate limiting and abuse prevention
- Batch operations for multiple downloads

## Code Style and Standards

- Use **async/await** patterns throughout the application
- Follow **FastAPI best practices** for route handlers and dependency injection
- Use **Pydantic models** for request/response validation
- Implement **proper error handling** with custom HTTP exceptions
- Use **SQLAlchemy 2.0** style with async sessions
- Follow **type hints** for all function parameters and return values
- Use **structlog** for structured logging

## Architecture Patterns

- **Repository Pattern**: Separate data access logic in repository classes
- **Service Layer**: Business logic should be in service classes
- **Dependency Injection**: Use FastAPI's dependency system
- **Schema Validation**: All API inputs/outputs should use Pydantic schemas
- **Error Handling**: Create custom exception classes for different error types

## Key Components

1. **Audio Downloader Service**: Port the existing bot's audio downloading logic
2. **User Management**: Authentication, registration, and user tracking
3. **Statistics Service**: Track downloads, usage patterns, and generate reports
4. **Rate Limiting**: Implement proper rate limiting to prevent abuse
5. **File Management**: Handle temporary file storage and cleanup

## Security Considerations

- Always validate and sanitize user inputs
- Implement proper JWT token handling
- Use rate limiting for all endpoints
- Sanitize file names and paths
- Implement CORS properly for web clients

## Performance Guidelines

- Use async operations for all I/O operations
- Implement caching where appropriate (Redis)
- Use database connection pooling
- Stream large file downloads
- Implement proper pagination for list endpoints

## Testing Approach

- Write unit tests for services and utilities
- Create integration tests for API endpoints
- Use pytest with async support
- Mock external API calls (Roblox APIs)
- Test rate limiting and error scenarios
