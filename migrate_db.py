#!/usr/bin/env python3
"""
Database migration script for The Ultimate API authentication system.
This script will:
1. Create the updated user table with new columns
2. Create the admin user with encrypted credentials
3. Set up the database for the authentication system
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_factory, engine
from app.models.user import User
from app.services.auth import AuthService
from app.schemas.auth import UserCreate
from app.config import settings

async def create_admin_user():
    """Create the admin user with the specified credentials."""
    async with async_session_factory() as db:
        auth_service = AuthService(db)
        
        # Check if admin user already exists
        result = await db.execute(
            select(User).where(User.email == "mykey@apiadmin.dev")
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("✅ Admin user already exists")
            print(f"   Email: {existing_admin.email}")
            print(f"   Username: {existing_admin.username}")
            print(f"   Client ID: {existing_admin.client_id}")
            print(f"   Client Secret: {existing_admin.client_secret}")
            return existing_admin
        
        # Create admin user
        admin_data = UserCreate(
            username="admin",
            email="mykey@apiadmin.dev",
            password="1283Ya123c",  # Made the first letter uppercase to meet validation
            display_name="API Administrator"
        )
        
        try:
            admin_user = await auth_service.create_user(admin_data)
            print("✅ Admin user created successfully")
            print(f"   Email: {admin_user.email}")
            print(f"   Username: {admin_user.username}")
            print(f"   Client ID: {admin_user.client_id}")
            print(f"   Client Secret: {admin_user.client_secret}")
            return admin_user
        except Exception as e:
            print(f"❌ Failed to create admin user: {e}")
            raise

async def migrate_database():
    """Run database migrations."""
    print("🔧 Starting database migration...")
    
    try:
        # Import models to ensure they're registered
        from app.models import user, audio_log
        from app.models.user import Base
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database tables created/updated successfully")
        
        # Create admin user
        await create_admin_user()
        
        print("🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

async def check_database_status():
    """Check the current database status."""
    print("📊 Checking database status...")
    
    try:
        async with async_session_factory() as db:
            # Check if user table exists and has the new columns
            result = await db.execute(text("""
                SELECT COUNT(*) as user_count 
                FROM sqlite_master 
                WHERE type='table' AND name='users'
            """))
            
            table_exists = (result.scalar() or 0) > 0
            
            if table_exists:
                # Check user count
                result = await db.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                
                # Check admin user
                result = await db.execute(text("""
                    SELECT username, email, is_admin, is_verified 
                    FROM users 
                    WHERE email = 'mykey@apiadmin.dev'
                """))
                admin_user = result.fetchone()
                
                print(f"📈 Database Status:")
                print(f"   Users table: {'✅ Exists' if table_exists else '❌ Missing'}")
                print(f"   Total users: {user_count}")
                print(f"   Admin user: {'✅ Exists' if admin_user else '❌ Missing'}")
                
                if admin_user:
                    print(f"   Admin details: {admin_user.username} ({admin_user.email})")
                    print(f"   Admin verified: {'✅' if admin_user.is_verified else '❌'}")
                    print(f"   Admin privileges: {'✅' if admin_user.is_admin else '❌'}")
            else:
                print("❌ Users table does not exist")
                
    except Exception as e:
        print(f"❌ Failed to check database status: {e}")

def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration for The Ultimate API")
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Check database status instead of running migration"
    )
    
    args = parser.parse_args()
    
    if args.check:
        print("🔍 Database Status Check")
        print("=" * 50)
        asyncio.run(check_database_status())
    else:
        print("🚀 The Ultimate API - Database Migration")
        print("=" * 50)
        asyncio.run(migrate_database())

if __name__ == "__main__":
    main()
