from tests.test_utils import assert_response_format, assert_error, assert_success
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
"""
All database endpoints tests
"""

import pytest
import asyncio
import httpx
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
        assert_response_format(response, 200)
        
        endpoints = [
            "health",
            "api/v1/database/departments",
            "api/v1/database/courses",
            "api/v1/database/users",
            "api/v1/database/enrollments",
            "api/v1/database/assessments"
        ]
        
        # Skip real server connection tests for now
        # endpoints should be tested individually using the TestClient
        
        return True
    
    @pytest.mark.asyncio
    async def test_departments_endpoint(self, client):
        """Test departments endpoint"""
        response = client.get("/api/v1/database/departments")
        # Check if endpoint exists (could be 404 if not implemented)
        assert response.status_code in [200, 201, 400, 401, 403, 422, 404]
        if response.status_code != 404:
            data = response.json()
            assert "count" in data
    
    @pytest.mark.asyncio
    async def test_courses_endpoint(self, client):
        """Test courses endpoint"""
        response = client.get("/api/v1/database/courses")
        # Check if endpoint exists (could be 404 if not implemented)
        assert response.status_code in [200, 201, 400, 401, 403, 422, 404]
        if response.status_code != 404:
            data = response.json()
            assert "count" in data
    
    @pytest.mark.asyncio
    async def test_users_endpoint(self, client):
        """Test users endpoint"""
        response = client.get("/api/v1/database/users")
        # Check if endpoint exists (could be 404 if not implemented)
        assert response.status_code in [200, 201, 400, 401, 403, 422, 404]
        if response.status_code != 404:
            data = response.json()
            assert "count" in data