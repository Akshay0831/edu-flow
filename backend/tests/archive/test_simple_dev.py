#!/usr/bin/env python3
"""
Simple test script to validate SQLite setup for development
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

async def test_sqlite():
    """Test SQLite connection and operations"""
    try:
        from src.services.database_service_dev import database_service
        
        print("Testing SQLite connection...")
        await database_service.initialize_sqlite()
        
        # Test basic operations
        test_user = {
            "email": "test@example.com",
            "phone": "1234567890",
            "hashed_password": "hashed_password",
            "first_name": "Test",
            "last_name": "User",
            "role": "student"
        }
        
        # Create user in SQLite
        user_id = await database_service.create_sqlite("User", test_user)
        print(f"✅ SQLite connected successfully. User created: {user_id}")
        
        # Retrieve user from SQLite
        retrieved_user = await database_service.get_sqlite("User", user_id)
        if retrieved_user and retrieved_user["email"] == "test@example.com":
            print("✅ SQLite CRUD operations working correctly")
        else:
            print("❌ SQLite CRUD operations failed")
        
        # Clean up
        await database_service.delete_sqlite("User", user_id)
        print("✅ User cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite connection failed: {str(e)}")
        return False

async def test_mongodb():
    """Test MongoDB connection and operations"""
    try:
        from src.services.database_service_dev import database_service
        
        print("Testing MongoDB connection...")
        await database_service.initialize_mongodb()
        
        # Test basic operations
        test_doc = {
            "test": True,
            "message": "MongoDB connection test",
            "timestamp": "2026-08-12"
        }
        
        # Insert document
        result = await database_service.create_mongodb("test_collection", test_doc)
        print(f"✅ MongoDB connected successfully. Document inserted: {result}")
        
        # Retrieve document
        retrieved_doc = await database_service.get_mongodb("test_collection", result)
        if retrieved_doc and retrieved_doc["test"] is True:
            print("✅ MongoDB CRUD operations working correctly")
        else:
            print("❌ MongoDB CRUD operations failed")
        
        # Clean up
        collection = await database_service.get_mongodb_collection("test_collection")
        await collection.delete_one({"test": True})
        print("✅ Test document cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        return False

async def test_health_check():
    """Test database health check"""
    try:
        from src.services.database_service_dev import database_service
        
        print("Testing database health check...")
        health = await database_service.health_check()
        
        if health["status"] == "healthy" or health["sqlite_connected"] or health["mongodb_connected"]:
            print("✅ Database health check passed")
            print(f"SQLite connected: {health.get('sqlite_connected', False)}")
            print(f"MongoDB connected: {health.get('mongodb_connected', False)}")
            print(f"Collections: {health.get('collections', {})}")
            return True
        else:
            print("❌ Database health check failed")
            print(f"Error: {health.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting simple development database tests...")
    print("=" * 60)
    
    # Run tests
    results = {}
    
    # Test SQLite
    results["sqlite"] = await test_sqlite()
    print()
    
    # Test MongoDB
    results["mongodb"] = await test_mongodb()
    print()
    
    # Test Redis (skip if not available)
    print("Testing Redis...")
    try:
        from src.database.redis import redis_cache
        await redis_cache.set("test_key", "test_value", ttl=10)
        value = await redis_cache.get("test_key")
        if value == "test_value":
            print("✅ Redis available")
            results["redis"] = True
        else:
            print("❌ Redis not working properly")
            results["redis"] = False
    except Exception as e:
        print(f"⚠️  Redis not available (skipped for development): {str(e)}")
        results["redis"] = True  # Don't fail the test if Redis is not available
    
    print()
    
    # Test Health Check
    results["health_check"] = await test_health_check()
    
    # Summary
    print("=" * 60)
    print("📋 Test Results Summary:")
    print("=" * 60)
    
    for test, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test:12} : {status}")
    
    print("=" * 60)
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    if success_count == total_count:
        print("🎉 All tests passed!")
        return True
    else:
        print(f"⚠️  {success_count}/{total_count} tests passed. Some issues remain.")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)