"""
Documentation router for serving Stoplight Elements documentation
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path

router = APIRouter()

# Get the docs directory path - go up two levels from app/routers to project root
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"

@router.get("/docs", response_class=HTMLResponse)
async def get_documentation():
    """
    Serve the Stoplight Elements documentation
    """
    docs_file = DOCS_DIR / "index.html"
    print(f"Looking for docs file at: {docs_file}")
    print(f"File exists: {docs_file.exists()}")
    print(f"DOCS_DIR: {DOCS_DIR}")
    print(f"DOCS_DIR exists: {DOCS_DIR.exists()}")
    
    if docs_file.exists():
        return FileResponse(docs_file, media_type="text/html")
    else:
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Documentation Not Found</title></head>
                <body>
                    <h1>Documentation Not Found</h1>
                    <p>The documentation files are not available.</p>
                    <p>Looking for: {docs_file}</p>
                    <p>DOCS_DIR: {DOCS_DIR}</p>
                    <p>DOCS_DIR exists: {DOCS_DIR.exists()}</p>
                </body>
            </html>
            """,
            status_code=404
        )

@router.get("/docs/openapi.yaml")
async def get_openapi_spec():
    """
    Serve the OpenAPI specification YAML file
    """
    openapi_file = DOCS_DIR / "openapi.yaml"
    if openapi_file.exists():
        return FileResponse(openapi_file, media_type="application/x-yaml")
    else:
        return {"error": "OpenAPI specification not found"}

@router.get("/docs/openapi.json")
async def get_openapi_json():
    """
    Serve the OpenAPI specification as JSON
    """
    from app.main import app
    return app.openapi()

@router.get("/docs/tos.html", response_class=HTMLResponse)
async def get_terms_of_service():
    """
    Serve the Terms of Service page
    """
    tos_file = DOCS_DIR / "tos.html"
    if tos_file.exists():
        return FileResponse(tos_file, media_type="text/html")
    else:
        return HTMLResponse(
            content="""
            <html>
                <head><title>Terms of Service Not Found</title></head>
                <body>
                    <h1>Terms of Service Not Found</h1>
                    <p>The Terms of Service file is not available.</p>
                </body>
            </html>
            """,
            status_code=404
        )

@router.get("/docs/bot", response_class=HTMLResponse)
async def get_discord_bot():
    """
    Serve the Discord bot page
    """
    bot_file = DOCS_DIR / "bot.html"
    if bot_file.exists():
        return FileResponse(bot_file, media_type="text/html")
    else:
        return HTMLResponse(
            content="""
            <html>
                <head><title>Discord Bot Not Found</title></head>
                <body>
                    <h1>Discord Bot Page Not Found</h1>
                    <p>The Discord bot page is not available.</p>
                </body>
            </html>
            """,
            status_code=404
        )

@router.get("/docs/auth/login", response_class=HTMLResponse)
async def get_login_page():
    """
    Serve the login page
    """
    login_file = DOCS_DIR / "auth" / "login.html"
    if login_file.exists():
        return FileResponse(login_file, media_type="text/html")
    else:
        return HTMLResponse(
            content="""
            <html>
                <head><title>Login Not Found</title></head>
                <body>
                    <h1>Login Page Not Found</h1>
                    <p>The login page is not available.</p>
                </body>
            </html>
            """,
            status_code=404
        )

@router.get("/docs/auth/signup", response_class=HTMLResponse)
async def get_signup_page():
    """
    Serve the signup page
    """
    signup_file = DOCS_DIR / "auth" / "signup.html"
    if signup_file.exists():
        return FileResponse(signup_file, media_type="text/html")
    else:
        return HTMLResponse(
            content="""
            <html>
                <head><title>Signup Not Found</title></head>
                <body>
                    <h1>Signup Page Not Found</h1>
                    <p>The signup page is not available.</p>
                </body>
            </html>
            """,
            status_code=404
        )

@router.get("/docs/auth/dashboard", response_class=HTMLResponse)
async def get_dashboard_page():
    """
    Serve the dashboard page
    """
    dashboard_file = DOCS_DIR / "auth" / "dashboard.html"
    if dashboard_file.exists():
        return FileResponse(dashboard_file, media_type="text/html")
    else:
        return HTMLResponse(
            content="""
            <html>
                <head><title>Dashboard Not Found</title></head>
                <body>
                    <h1>Dashboard Page Not Found</h1>
                    <p>The dashboard page is not available.</p>
                </body>
            </html>
            """,
            status_code=404
        )

@router.get("/docs/auth/forgot-password", response_class=HTMLResponse)
async def get_forgot_password_page():
    """
    Serve the forgot password page
    """
    forgot_file = DOCS_DIR / "auth" / "forgot-password.html"
    if forgot_file.exists():
        return FileResponse(forgot_file, media_type="text/html")
    else:
        return HTMLResponse(
            content="""
            <html>
                <head><title>Forgot Password Not Found</title></head>
                <body>
                    <h1>Forgot Password Page Not Found</h1>
                    <p>The forgot password page is not available.</p>
                </body>
            </html>
            """,
            status_code=404
        )
