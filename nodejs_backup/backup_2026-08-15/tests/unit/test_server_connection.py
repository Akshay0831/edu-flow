
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
"""
Test server database connection
"""

import asyncio
import sys
import os
sys.path.append('.')

async def test_server_connection():
    try:
        from src.services.database_service import database_service
        
        print("🔍 Testing server database connection...")
        
        # Check if database is connected
        print("1. Checking if database is connected...")
        if database_service.db is None:
            print("   Database is not connected, trying to connect...")
            # Try to connect
            await database_service.connect()
            print("   Connected successfully!")
        else:
            print("   Database is already connected!")
        
        # Now test the operations
        print("2. Testing database operations...")
        departments = await database_service.find_many("departments", {})
        print(f"   Found {len(departments)} departments")
        
        # Test health check
        print("3. Testing health check...")
        health = await database_service.health_check()
        print(f"   Health check result: {health}")
        
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_server_connection())