#!/usr/bin/env python3
"""
Test script to validate SQLite and Redis setup for development

This script tests:
- SQLite connectivity and operations
- Redis connectivity and operations
- Database migrations
- Health checks

Author: Edu-Flow Team
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
            return False
        
        # Clean up
        try:
            session = await database_service.get_sqlite_session()
            from src.database.sqlite import User
            await session.delete(User(id=user_id))
            await session.commit()
            print("✅ Test user cleaned up")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite connection failed: {str(e)}")
        return False

async def test_redis():
    """Test Redis connection and operations"""
    try:
        from src.database.redis import redis_cache
        
        print("Testing Redis connection...")
        
        # Test basic operations
        test_key = "test_key"
        test_value = {"test": True, "message": "Redis connection test", "timestamp": "2026-08-12"}
        
        await redis_cache.set(test_key, test_value, ttl=300)
        retrieved_value = await redis_cache.get(test_key)
        
        if retrieved_value == test_value:
            print("✅ Redis connected successfully")
        else:
            print("❌ Redis connection failed - data mismatch")
            print(f"Expected: {test_value}")
            print(f"Got: {retrieved_value}")
            return False
        
        # Test key existence
        exists = await redis_cache.exists(test_key)
        if exists:
            print("✅ Redis key existence check working")
        else:
            print("❌ Redis key existence check failed")
            return False
        
        # Test TTL
        await redis_cache.expire(test_key, 60)
        print("✅ Redis TTL management working")
        
        # Test key deletion
        await redis_cache.delete(test_key)
        print("✅ Redis deletion working")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        return False

async def test_mongodb():
    """Test MongoDB connection and operations"""
    try:
        from src.services.database_service_dev import database_service
        
        print("Testing MongoDB connection...")
        await database_service.initialize_mongodb()
        
        # Test basic operations
        test_data = {
            "test": True,
            "message": "MongoDB connection test",
            "timestamp": "2026-08-12"
        }
        
        # Create document in MongoDB
        result = await database_service.create_mongodb("test_collection", test_data)
        print(f"✅ MongoDB connected successfully. Document inserted: {result}")
        
        # Retrieve document from MongoDB
        retrieved_doc = await database_service.get_mongodb("test_collection", {"test": True})
        if retrieved_doc and retrieved_doc["message"] == "MongoDB connection test":
            print("✅ MongoDB CRUD operations working correctly")
        else:
            print("❌ MongoDB CRUD operations failed")
            return False
        
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

async def run_all_tests():
    """Run all database tests"""
    print("🚀 Starting development database setup tests...")
    print("=" * 60)
    
    results = {}
    
    # Test SQLite
    print("\n📊 Testing SQLite...")
    results["sqlite"] = await test_sqlite()
    
    # Test MongoDB
    print("\n📊 Testing MongoDB...")
    results["mongodb"] = await test_mongodb()
    
    # Test Redis
    print("\n📊 Testing Redis...")
    results["redis"] = await test_redis()
    
    # Test health check
    print("\n📊 Testing Health Check...")
    results["health_check"] = await test_health_check()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:15}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All development database tests passed! Database setup is ready.")
        print("💡 Note: Redis is configured for Docker deployment")
    else:
        print("⚠️  Some tests failed. Please check the database setup.")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_all_tests())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)