#!/usr/bin/env python3
"""
Simple startup script for the Roblox Audio API
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

def print_banner():
    """Print a nice banner"""
    print("=" * 60)
    print("🎵 ROBLOX AUDIO API SERVER")
    print("=" * 60)
    print()

def check_environment():
    """Check if environment is properly set up"""
    print("🔧 Checking environment...")
    
    if not Path(".env").exists():
        print("   ⚠️  .env file not found. Copying from .env.example...")
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("   ✅ .env file created. Please edit it with your configuration.")
        else:
            print("   ❌ .env.example not found. Please create a .env file manually.")
            return False
    else:
        print("   ✅ .env file found")
    
    # Check if temp directory exists
    temp_dir = Path("temp")
    if not temp_dir.exists():
        print("   📁 Creating temp directory...")
        temp_dir.mkdir(exist_ok=True)
        print("   ✅ Temp directory created")
    else:
        print("   ✅ Temp directory exists")
    
    # Check if virtual environment exists
    venv_python = Path(".venv/Scripts/python.exe")
    if venv_python.exists():
        print("   ✅ Virtual environment found")
    else:
        print("   ⚠️  Virtual environment not found, using system Python")
    
    print("   ✅ Environment check complete")
    print()
    return True

def main():
    """Main startup function"""
    # Configure logging to suppress verbose output
    import logging_config  # This applies our custom logging configuration
    
    print_banner()
    
    if not check_environment():
        print("❌ Environment check failed. Exiting.")
        sys.exit(1)
    
    print("🌐 Starting FastAPI server...")
    print("   📡 Host: http://localhost:8000")
    print("   📚 API Documentation: http://localhost:8000/docs")
    print("   🔐 Admin Dashboard: http://localhost:8000/auth/dashboard")
    print()
    print("💡 Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    # Start the server
    try:
        # Use the virtual environment's Python
        venv_python = Path(".venv/Scripts/python.exe")
        if venv_python.exists():
            python_cmd = str(venv_python)
        else:
            python_cmd = "python"
            
        subprocess.run([
            python_cmd, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--log-level", "warning"
        ], check=True)
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("👋 Server stopped gracefully. Goodbye!")
        print("=" * 60)
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 60)
        print(f"❌ Server failed to start: {e}")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
