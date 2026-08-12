from tests.test_utils import assert_response_format, assert_error, assert_success
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
"""
All database endpoints tests
"""

import pytest
import asyncio
import sys
import os
sys.path.append('.')
from fastapi.testclient import TestClient
from src.main import app


class TestDatabaseEndpoints:
    """Test suite for all database endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_database_health_endpoint(self, client):
        """Test database health endpoint"""
        response = client.get("/health")
        TestValidationSystem.assert_http_error(response, expected_status)
        
        endpoints = [
            "health",
            "api/v1/database/departments",
            "api/v1/database/courses",
            "api/v1/database/users",
            "api/v1/database/enrollments",
            "api/v1/database/assessments"
        ]
        
        async with httpx.AsyncClient() as client:
            for endpoint in endpoints:
                print(f"\n2. Testing {endpoint}...")
                try:
                    response = await client.get(f"http://localhost:8000/{endpoint}", timeout=10.0)
                    print(f"   Status Code: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'count' in data:
                            print(f"   ✅ Success! Found {data.get('count', 0)} items")
                        else:
                            print(f"   ✅ Success! Response: {data}")
                    else:
                        print(f"   ❌ Error: {response.text}")
                        
                except Exception as e:
                    print(f"   ❌ HTTP Error: {e}")
                    
        # Test specific endpoints
        await self.test_departments_endpoint(client)
        await self.test_courses_endpoint(client)
        await self.test_users_endpoint(client)
        
        return True
    
    @pytest.mark.asyncio
    async def test_departments_endpoint(self, client):
        """Test departments endpoint"""
        response = client.get("/api/v1/database/departments")
        TestValidationSystem.assert_http_error(response, expected_status)
        data = response.json()
        assert "count" in data
    
    @pytest.mark.asyncio
    async def test_courses_endpoint(self, client):
        """Test courses endpoint"""
        response = client.get("/api/v1/database/courses")
        TestValidationSystem.assert_http_error(response, expected_status)
        data = response.json()
        assert "count" in data
    
    @pytest.mark.asyncio
    async def test_users_endpoint(self, client):
        """Test users endpoint"""
        response = client.get("/api/v1/database/users")
        TestValidationSystem.assert_http_error(response, expected_status)
        data = response.json()
        assert "count" in data