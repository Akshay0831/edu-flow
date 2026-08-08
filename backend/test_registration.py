#!/usr/bin/env python3

"""
Simple test script to verify registration endpoint works
"""

from fastapi.testclient import TestClient
from src.main import app

def test_registration():
    """Test the registration endpoint"""
    client = TestClient(app)
    
    # Test valid user registration
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "Password123!",
            "name": "Test User",
            "role": "teacher"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    assert response.json().get("message") == "User registered successfully"

if __name__ == "__main__":
    test_registration()