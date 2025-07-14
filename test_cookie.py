#!/usr/bin/env python3
"""
Test script to validate Roblox cookie
"""
import asyncio
import httpx
from app.config import settings

async def test_roblox_cookie():
    """Test if the Roblox cookie is valid and working"""
    print("🔍 Testing Roblox Cookie...")
    print("=" * 50)
    
    if not settings.ROBLOX_COOKIE:
        print("❌ No Roblox cookie found in .env file")
        return False
    
    print(f"📝 Cookie found (length: {len(settings.ROBLOX_COOKIE)} characters)")
    print(f"🎯 Cookie preview: {settings.ROBLOX_COOKIE[:50]}...")
    print()
    
    # Test 1: Basic authentication check
    print("🧪 Test 1: Basic Authentication Check")
    try:
        async with httpx.AsyncClient() as client:
            # Test with a simple API endpoint that requires authentication
            url = "https://users.roblox.com/v1/users/authenticated"
            headers = {
                "Cookie": f".ROBLOSECURITY={settings.ROBLOX_COOKIE}",
                "User-Agent": "Roblox/WinInet"
            }
            
            response = await client.get(url, headers=headers)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"   ✅ Authentication successful!")
                print(f"   👤 User ID: {user_data.get('id', 'Unknown')}")
                print(f"   📛 Username: {user_data.get('name', 'Unknown')}")
                print(f"   📧 Display Name: {user_data.get('displayName', 'Unknown')}")
            elif response.status_code == 401:
                print("   ❌ Authentication failed - Cookie is invalid or expired")
                return False
            elif response.status_code == 403:
                print("   ❌ Access forbidden - Cookie might be restricted")
                return False
            else:
                print(f"   ⚠️  Unexpected response: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error during authentication test: {e}")
        return False
    
    print()
    
    # Test 2: Asset delivery test
    print("🧪 Test 2: Asset Delivery Test")
    try:
        async with httpx.AsyncClient() as client:
            # Test with a known public audio asset
            test_asset_id = 142376088  # A public Roblox audio asset
            url = f"https://assetdelivery.roblox.com/v1/asset/?id={test_asset_id}"
            headers = {
                "Cookie": f".ROBLOSECURITY={settings.ROBLOX_COOKIE}",
                "User-Agent": "Roblox/WinInet"
            }
            
            response = await client.get(url, headers=headers)
            print(f"   Status Code: {response.status_code}")
            print(f"   Content Type: {response.headers.get('content-type', 'Unknown')}")
            
            if response.status_code == 200:
                print("   ✅ Asset delivery working!")
                print(f"   📁 Content Length: {len(response.content)} bytes")
                if response.url != url:
                    print(f"   🔗 Redirected to: {response.url}")
            elif response.status_code == 403:
                print("   ❌ Asset delivery blocked - Cookie authentication failed")
                return False
            elif response.status_code == 404:
                print("   ⚠️  Asset not found (this might be expected)")
            else:
                print(f"   ⚠️  Unexpected response: {response.status_code}")
                
    except Exception as e:
        print(f"   ❌ Error during asset delivery test: {e}")
        return False
    
    print()
    
    # Test 3: Catalog API test
    print("🧪 Test 3: Catalog API Test")
    try:
        async with httpx.AsyncClient() as client:
            catalog_url = "https://catalog.roblox.com/v1/catalog/items/details"
            catalog_payload = {"items": [{"itemType": "Asset", "id": 142376088}]}
            
            response = await client.post(catalog_url, json=catalog_payload)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                catalog_data = response.json()
                if catalog_data.get("data"):
                    item = catalog_data["data"][0]
                    print("   ✅ Catalog API working!")
                    print(f"   📛 Asset Name: {item.get('name', 'Unknown')}")
                    print(f"   👤 Creator: {item.get('creatorName', 'Unknown')}")
                else:
                    print("   ⚠️  No catalog data returned")
            else:
                print(f"   ⚠️  Catalog API response: {response.status_code}")
                
    except Exception as e:
        print(f"   ❌ Error during catalog API test: {e}")
    
    print()
    print("🎉 Cookie validation complete!")
    return True

if __name__ == "__main__":
    print("🍪 ROBLOX COOKIE VALIDATION TOOL")
    print("=" * 50)
    
    try:
        result = asyncio.run(test_roblox_cookie())
        if result:
            print("\n✅ Overall Result: Cookie appears to be working!")
        else:
            print("\n❌ Overall Result: Cookie validation failed!")
            print("\n💡 Solutions:")
            print("   1. Get a fresh cookie from your browser:")
            print("      - Go to roblox.com and log in")
            print("      - Press F12 → Application → Cookies → .ROBLOSECURITY")
            print("      - Copy the full cookie value to your .env file")
            print("   2. Check if your Roblox account has any restrictions")
            print("   3. Make sure you're logged in to the correct account")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
