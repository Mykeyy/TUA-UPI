#!/usr/bin/env python3
"""
Simple startup script for the Roblox Audio API
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """Check if environment is properly set up"""
    if not Path(".env").exists():
        print("⚠️  .env file not found. Copying from .env.example...")
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ .env file created. Please edit it with your configuration.")
        else:
            print("❌ .env.example not found. Please create a .env file manually.")
            return False
    
    # Check if temp directory exists
    temp_dir = Path("temp")
    if not temp_dir.exists():
        print("📁 Creating temp directory...")
        temp_dir.mkdir(exist_ok=True)
        print("✅ Temp directory created.")
    
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Roblox Audio API...")
    
    if not check_environment():
        sys.exit(1)
    
    print("🔧 Environment check complete.")
    print("🌐 Starting server on http://localhost:8000")
    print("📚 API docs available at http://localhost:8000/docs")
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
            "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
