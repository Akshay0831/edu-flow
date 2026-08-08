#!/usr/bin/env python3

"""
Comprehensive error analysis for authentication tests
"""

import json
from fastapi.testclient import TestClient
from src.main import app, auth_service
import sys
import os

def analyze_common_error_patterns():
    """Analyze common error patterns in auth tests"""
    client = TestClient(app)
    
    print("=== Analyzing Common Error Patterns ===")
    
    # Test 1: Check login endpoint response format
    print("\n1. Testing Login Endpoint Response Format:")
    # First register a user
    register_data = {
        "email": "test@example.com",
        "password": "Password123!",
        "name": "Test User",
        "role": "teacher"
    }
    
    register_response = client.post("/api/v1/auth/register", json=register_data)
    print(f"Registration: {register_response.status_code}")
    
    # Now login
    login_data = {
        "email": "test@example.com", 
        "password": "Password123!"
    }
    
    login_response = client.post("/api/v1/auth/login", json=login_data)
    print(f"Login Status: {login_response.status_code}")
    print(f"Login Response: {login_response.json()}")
    
    # Test 2: Check password strength validation
    print("\n2. Testing Password Strength Validation:")
    weak_password_data = {
        "email": "weak@example.com",
        "password": "weak",
        "name": "Weak User",
        "role": "student"
    }
    
    weak_response = client.post("/api/v1/auth/register", json=weak_password_data)
    print(f"Weak Password Status: {weak_response.status_code}")
    print(f"Weak Password Response: {weak_response.json()}")
    
    # Test 3: Check missing fields
    print("\n3. Testing Missing Registration Fields:")
    incomplete_data = {
        "email": "incomplete@example.com"
        # Missing required fields
    }
    
    incomplete_response = client.post("/api/v1/auth/register", json=incomplete_data)
    print(f"Incomplete Data Status: {incomplete_response.status_code}")
    print(f"Incomplete Data Response: {incomplete_response.json()}")
    
    # Test 4: Check CORS headers
    print("\n4. Testing CORS Headers:")
    # Use a different email for CORS test
    cors_data = {
        "email": "cors-test@example.com",
        "password": "Password123!",
        "name": "CORS Test User",
        "role": "teacher"
    }
    cors_response = client.post("/api/v1/auth/register", json=cors_data)
    print(f"POST Response Status: {cors_response.status_code}")
    print(f"Response Headers: {dict(cors_response.headers)}")
    
    # Check for CORS-specific headers
    cors_headers = dict(cors_response.headers)
    has_cors = any('access-control' in key.lower() for key in cors_headers.keys())
    print(f"Has CORS headers: {has_cors}")
    
    # Test 5: Check security headers
    print("\n5. Testing Security Headers:")
    security_response = client.get("/api/v1/users/me")
    print(f"Security Headers Status: {security_response.status_code}")
    print(f"Security Headers: {dict(security_response.headers)}")

if __name__ == "__main__":
    analyze_common_error_patterns()