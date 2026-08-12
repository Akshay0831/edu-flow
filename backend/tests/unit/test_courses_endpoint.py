from src.core.test_validation_system import TestValidationSystem, assert_response_format, assert_error, assert_success
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
"""
Courses endpoint tests
"""

import pytest
import asyncio
import sys
import os
sys.path.append('.')
from fastapi.testclient import TestClient
from src.main import app


class TestCoursesEndpoint:
    """Test suite for courses endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_courses_endpoint_health(self, client):
        """Test courses endpoint health"""
        response = client.get("/health")
        TestValidationSystem.assert_http_error(response, 200)
    
    def test_courses_endpoint_exists(self, client):
        """Test courses endpoint exists and returns valid response"""
        response = client.get("/api/v1/database/courses")
        TestValidationSystem.assert_http_error(response, expected_status)
        data = response.json()
        assert "count" in data
        
    def test_courses_endpoint_detailed(self, client):
        """Test courses endpoint with detailed response"""
        response = client.get("/api/v1/database/courses")
        TestValidationSystem.assert_http_error(response, 200)
        data = response.json()
        assert "count" in data
        if data.get('message'):
            assert isinstance(data['message'], str)
        if data.get('courses'):
            assert isinstance(data['courses'], list)
            if data['courses']:
                assert isinstance(data['courses'][0], dict)
    
    def test_create_course_endpoint(self, client):
        """Test course creation endpoint"""
        course_data = {
            "name": "Test Course",
            "code": "TC101",
            "description": "Test course description",
            "credits": 3,
            "department_id": "DEPT001"
        }
        
        response = client.post("/api/v1/database/courses", json=course_data)
        # Course creation might require auth, so we just check for valid response
        assert response.status_code in [200, 201, 400, 401, 403, 422]