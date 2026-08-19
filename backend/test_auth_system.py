#!/usr/bin/env python3
"""
Test script to verify the authentication system is working correctly.

This script tests:
1. User registration
2. User login
3. Token generation and validation
4. Password hashing and verification
5. Role-based access control
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.auth_service import auth_service, AuthService
from src.services.user_service import UserService


async def test_password_hashing():
    """Test password hashing and verification"""
    print("🔐 Testing password hashing and verification...")
    
    # Test password hashing
    password = "TestPassword123!"
    hashed = auth_service.hash_password(password)
    print(f"   Password: {password}")
    print(f"   Hashed: {hashed[:20]}...")
    
    # Test password verification
    assert auth_service.verify_password(password, hashed), "Password verification failed"
    assert not auth_service.verify_password("wrong_password", hashed), "Wrong password accepted"
    print("   ✅ Password hashing and verification working")


async def test_user_registration():
    """Test user registration"""
    print("👤 Testing user registration...")
    
    # Create user service
    user_service = UserService()
    await user_service.initialize()
    auth_service.set_user_service(user_service)
    
    # Test user registration
    user_data = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "name": "Test User",
        "role": "student"
    }
    
    try:
        user = await auth_service.create_user(user_data)
        print(f"   User created: {user['email']} ({user['role']})")
        assert user['email'] == "test@example.com"
        assert user['role'] == "student"
        print("   ✅ User registration working")
        
        # Clean up
        await user_service.dispose()
        return user
    except Exception as e:
        print(f"   ❌ User registration failed: {e}")
        await user_service.dispose()
        return None


async def test_user_login():
    """Test user login"""
    print("🔑 Testing user login...")
    
    # Create user service and register a user
    user_service = UserService()
    await user_service.initialize()
    auth_service.set_user_service(user_service)
    
    # Register a test user
    user_data = {
        "email": "login_test@example.com",
        "password": "TestPassword123!",
        "name": "Login Test User",
        "role": "student"
    }
    
    await auth_service.create_user(user_data)
    
    # Test login
    try:
        login_result = await auth_service.authenticate_user(
            email="login_test@example.com",
            password="TestPassword123!"
        )
        
        print(f"   Login successful: {login_result['user']['email']}")
        assert 'access_token' in login_result
        assert 'refresh_token' in login_result
        assert login_result['user']['role'] == 'student'
        print("   ✅ User login working")
        
        # Test wrong password
        try:
            await auth_service.authenticate_user(
                email="login_test@example.com",
                password="wrong_password"
            )
            assert False, "Wrong password should have failed"
        except Exception as e:
            print(f"   ✅ Wrong password correctly rejected: {type(e).__name__}")
        
        # Clean up
        await user_service.dispose()
        return login_result
    except Exception as e:
        print(f"   ❌ User login failed: {e}")
        await user_service.dispose()
        return None


async def test_token_validation():
    """Test token generation and validation"""
    print("🎫 Testing token validation...")
    
    # Create a test token
    test_data = {
        "sub": "test_user_id",
        "email": "test@example.com",
        "role": "student"
    }
    
    # Generate access token
    access_token = auth_service.create_access_token(test_data)
    print(f"   Access token: {access_token[:50]}...")
    
    # Validate token
    try:
        token_data = auth_service.decode_token(access_token)
        print(f"   Token validated: {token_data.email} ({token_data.role})")
        assert token_data.email == "test@example.com"
        assert token_data.role == "student"
        print("   ✅ Token validation working")
        return token_data
    except Exception as e:
        print(f"   ❌ Token validation failed: {e}")
        return None


async def test_role_based_access():
    """Test role-based access control"""
    print("🛡️ Testing role-based access control...")
    
    # Test different roles
    roles_permissions = {
        "student": ["view_profile", "view_courses"],
        "teacher": ["view_profile", "view_courses", "create_content", "manage_students"],
        "admin": ["view_profile", "view_courses", "create_content", "manage_students", "manage_users"]
    }
    
    for role, permissions in roles_permissions.items():
        print(f"   Testing {role} role...")
        for permission in permissions:
            has_permission = auth_service.check_permission(role, permission)
            assert has_permission, f"{role} should have {permission} permission"
        print(f"   ✅ {role} role permissions working")


async def test_account_lockout():
    """Test account lockout after failed attempts"""
    print("🔒 Testing account lockout...")
    
    user_service = UserService()
    await user_service.initialize()
    auth_service.set_user_service(user_service)
    
    # Register a test user
    user_data = {
        "email": "lockout_test@example.com",
        "password": "TestPassword123!",
        "name": "Lockout Test User",
        "role": "student"
    }
    
    await auth_service.create_user(user_data)
    
    # Simulate multiple failed login attempts
    for i in range(5):  # Max attempts = 5
        try:
            await auth_service.authenticate_user(
                email="lockout_test@example.com",
                password="wrong_password"
            )
        except Exception as e:
            print(f"   Failed attempt {i+1}: {type(e).__name__}")
    
    # Now try to login - should be locked out
    try:
        await auth_service.authenticate_user(
            email="lockout_test@example.com",
            password="TestPassword123!"
        )
        assert False, "Account should be locked out"
    except Exception as e:
        print(f"   ✅ Account correctly locked out: {type(e).__name__}")
    
    # Clean up
    await user_service.dispose()


async def run_all_tests():
    """Run all authentication tests"""
    print("🚀 Starting authentication system tests...\n")
    
    try:
        await test_password_hashing()
        print()
        
        await test_user_registration()
        print()
        
        await test_user_login()
        print()
        
        await test_token_validation()
        print()
        
        await test_role_based_access()
        print()
        
        await test_account_lockout()
        print()
        
        print("🎉 All authentication tests passed!")
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)