#!/usr/bin/env python3
"""
Test script to verify database setup and connectivity

This script tests:
- MongoDB connectivity
- PostgreSQL connectivity
- Redis connectivity
- Database initialization
- Health checks

Author: Edu-Flow Team
"""

import asyncio
import pytest
import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

@pytest.mark.asyncio
async def test_mongodb():
    """Test MongoDB connection"""
    try:
        from src.services.database_service import database_service
        
        print("Testing MongoDB connection...")
        db = await database_service.connect()
        
        # Test basic operations
        test_data = {"test": True, "message": "MongoDB connection test"}
        result = await database_service.insert_one("test_collection", test_data)
        print(f"✅ MongoDB connected successfully. Document inserted: {result}")
        
        # Clean up
        await database_service.delete_one("test_collection", {"test": True})
        print("✅ Test document cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        return False

@pytest.mark.asyncio
async def test_postgresql():
    """Test PostgreSQL connection"""
    try:
        from src.database.postgresql import initialize_postgres
        
        print("Testing PostgreSQL connection...")
        if await initialize_postgres():
            print("✅ PostgreSQL connected successfully")
            return True
        else:
            print("❌ PostgreSQL connection failed")
            return False
            
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {str(e)}")
        return False

@pytest.mark.asyncio
async def test_redis():
    """Test Redis connection"""
    try:
        from src.database.redis import redis_cache
        
        print("Testing Redis connection...")
        await redis_cache.initialize()
        
        # Test basic operations
        test_key = "test_key"
        test_value = {"test": True, "message": "Redis connection test"}
        
        await redis_cache.set(test_key, test_value, ttl=300)
        retrieved_value = await redis_cache.get(test_key)
        
        if retrieved_value == test_value:
            print("✅ Redis connected successfully")
        else:
            print("❌ Redis connection failed - data mismatch")
            return False
        
        # Clean up
        await redis_cache.delete(test_key)
        print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        return False

@pytest.mark.asyncio
async def test_health_check():
    """Test database health check"""
    try:
        from src.services.database_service import database_service
        
        print("Testing database health check...")
        health = await database_service.health_check()
        
        if health["status"] == "healthy":
            print("✅ Database health check passed")
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
    print("🚀 Starting database setup tests...")
    print("=" * 50)
    
    results = {}
    
    # Test MongoDB
    print("\n📊 Testing MongoDB...")
    results["mongodb"] = await test_mongodb()
    
    # Test PostgreSQL
    print("\n📊 Testing PostgreSQL...")
    results["postgresql"] = await test_postgresql()
    
    # Test Redis
    print("\n📊 Testing Redis...")
    results["redis"] = await test_redis()
    
    # Test health check
    print("\n📊 Testing Health Check...")
    results["health_check"] = await test_health_check()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:15}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All database tests passed! Database setup is ready.")
    else:
        print("⚠️  Some tests failed. Please check the database setup.")
    print("=" * 50)
    
    return all_passed

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_all_tests())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)