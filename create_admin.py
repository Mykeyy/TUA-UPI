#!/usr/bin/env python3
"""
Quick script to recreate the admin user after database reset
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session, create_tables
from app.services.auth import AuthService
from app.schemas.auth import UserCreate
from app.config import settings

async def create_admin_user():
    """Create the admin user"""
    print("🔧 Creating admin user...")
    
    # Ensure tables exist
    await create_tables()
    
    # Get database session
    async for db in get_async_session():
        try:
            auth_service = AuthService(db)
            
            # Create admin user with the configured credentials
            admin_data = UserCreate(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                password=settings.ADMIN_PASSWORD,
                display_name="Administrator"
            )
            
            print(f"📧 Admin Email: {settings.ADMIN_EMAIL}")
            print(f"👤 Admin Username: {settings.ADMIN_USERNAME}")
            print(f"🔑 Admin Password: {settings.ADMIN_PASSWORD}")
            
            # Create the user
            user = await auth_service.create_user(admin_data)
            
            print(f"✅ Admin user created successfully!")
            print(f"   User ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Is Admin: {user.is_admin}")
            print(f"   Is Verified: {user.is_verified}")
            
            return True
            
        except ValueError as e:
            if "already exists" in str(e):
                print(f"✅ Admin user already exists: {e}")
                return True
            else:
                print(f"❌ Error creating admin user: {e}")
                return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
        finally:
            break  # Exit the generator

if __name__ == "__main__":
    print("============================================================")
    print("🔧 ADMIN USER CREATOR")
    print("============================================================")
    
    try:
        success = asyncio.run(create_admin_user())
        if success:
            print("\n🎉 Admin user is ready!")
            print("💡 You can now log in to the dashboard with:")
            print(f"   📧 Email: {settings.ADMIN_EMAIL}")
            print(f"   👤 Username: {settings.ADMIN_USERNAME}")
            print(f"   🔑 Password: {settings.ADMIN_PASSWORD}")
            print("\n🌐 Dashboard: http://localhost:8000/docs/auth/dashboard.html")
        else:
            print("\n❌ Failed to create admin user")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        sys.exit(1)
    
    print("============================================================")
