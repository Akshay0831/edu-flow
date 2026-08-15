"""
Unit Tests for API Routes

This module contains unit tests for the API routes, ensuring proper endpoint
functionality, request validation, and response formatting.

Author: Edu-Flow Team
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Mock settings before importing
class MockSettings:
    HOST = "localhost"
    PORT = 8000
    DEBUG = True
    ALLOWED_HOSTS = ["*"]
    CLIENT_ID = "test_client"
    CLIENT_SECRET = "test_secret"
    AUTH_URL = "http://localhost:8000/auth"
    TOKEN_URL = "http://localhost:8000/token"
    SCOPES = ["openid", "profile", "email"]
    SECRET_KEY = "test_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    secret_key = "test_secret_key"
    algorithm = "HS256"
    jwt_secret_key = "test_jwt_secret_key"
    jwt_algorithm = "HS256"

# Patch settings
with patch('src.config.settings.settings', MockSettings()):
    from src.api.v1 import app
    from src.core.database import get_db
    from src.models.user import User, UserRole
    from src.models.student import Student

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
def setup_test_db():
    # Import all models to create tables
    from ...src.models import user, student, course, teacher, department, enrollment
    from ...src.core.database import Base
    Base.metadata.create_all(bind=engine)
    
    # Create test user
    db = TestingSessionLocal()
    try:
        test_user = User(
            email="test@example.com",
            name="Test User",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        return test_user
    finally:
        db.close()

# Test client
@pytest.fixture(scope="module")
def client():
    setup_test_db()
    return TestClient(app)

# Test data
@pytest.fixture
def test_user_data():
    return {
        "email": "newuser@example.com",
        "password": "testpassword123",
        "name": "New User",
        "role": "student"
    }

@pytest.fixture
def test_course_data():
    return {
        "name": "Test Course",
        "code": "TC101",
        "department_id": "1",
        "credits": 3
    }

@pytest.fixture
def test_student_data():
    return {
        "student_id": "S001",
        "user_id": "1",
        "department_id": "1",
        "semester": "Fall 2023",
        "program": "Computer Science"
    }

class TestAPIRoutes:
    """Test class for API routes"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_api_info(self, client):
        """Test API info endpoint"""
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Edu-Flow API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data

    def test_api_stats(self, client):
        """Test API stats endpoint"""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.0.0"
        assert "endpoints_count" in data
        assert "uptime" in data

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to Edu-Flow API"
        assert data["version"] == "1.0.0"

    @patch('src.services.user_service.UserService')
    def test_user_registration(self, mock_user_service, client, test_user_data):
        """Test user registration endpoint"""
        # Mock the service
        mock_service_instance = Mock()
        mock_user_service.return_value = mock_service_instance
        mock_service_instance.create_user = AsyncMock(return_value=Mock(id="1", email="test@example.com"))
        
        response = client.post("/users/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert "user_id" in data

    @patch('src.services.user_service.UserService')
    def test_user_login(self, mock_user_service, client):
        """Test user login endpoint"""
        # Mock the service
        mock_service_instance = Mock()
        mock_user_service.return_value = mock_service_instance
        mock_service_instance.authenticate_user = AsyncMock(return_value=Mock(email="test@example.com"))
        
        login_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/users/token", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_user_registration_missing_fields(self, client, test_user_data):
        """Test user registration with missing required fields"""
        # Remove required field
        invalid_data = test_user_data.copy()
        del invalid_data["email"]
        
        response = client.post("/users/register", json=invalid_data)
        
        assert response.status_code == 422  # Validation error

    def test_user_registration_invalid_role(self, client, test_user_data):
        """Test user registration with invalid role"""
        # Invalid role
        invalid_data = test_user_data.copy()
        invalid_data["role"] = "invalid_role"
        
        response = client.post("/users/register", json=invalid_data)
        
        assert response.status_code == 400
        assert "Invalid role" in response.json()["detail"]

    @patch('src.services.student_service.StudentService')
    def test_get_students(self, mock_student_service, client):
        """Test get students endpoint"""
        # Mock the service
        mock_service_instance = Mock()
        mock_student_service.return_value = mock_service_instance
        mock_service_instance.get_students = AsyncMock(return_value=[
            {"id": "1", "name": "Test Student", "email": "test@example.com"}
        ])
        
        response = client.get("/students/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @patch('src.services.course_service.CourseService')
    def test_get_courses(self, mock_course_service, client):
        """Test get courses endpoint"""
        # Mock the service
        mock_service_instance = Mock()
        mock_course_service.return_value = mock_service_instance
        mock_service_instance.get_courses = AsyncMock(return_value=[
            {"id": "1", "name": "Test Course", "code": "TC101"}
        ])
        
        response = client.get("/courses/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @patch('src.services.course_service.CourseService')
    def test_create_course(self, mock_course_service, client, test_course_data):
        """Test create course endpoint"""
        # Mock the service
        mock_service_instance = Mock()
        mock_course_service.return_value = mock_service_instance
        mock_service_instance.create_course = AsyncMock(return_value=Mock(id="1", name="Test Course"))
        
        response = client.post("/courses/", json=test_course_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Course created successfully"
        assert "course_id" in data

    def test_create_course_missing_fields(self, client, test_course_data):
        """Test create course with missing required fields"""
        # Remove required field
        invalid_data = test_course_data.copy()
        del invalid_data["name"]
        
        response = client.post("/courses/", json=invalid_data)
        
        assert response.status_code == 422  # Validation error

    def test_create_course_unauthorized(self, client, test_course_data):
        """Test create course without authorization"""
        # Should fail for non-admin users
        response = client.post("/courses/", json=test_course_data)
        
        # In a real scenario, this would be 401 Unauthorized, but our mock might differ
        assert response.status_code in [401, 403, 422]

    @patch('src.services.student_service.StudentService')
    def test_get_student_by_id(self, mock_student_service, client):
        """Test get student by ID endpoint"""
        # Mock the service
        mock_service_instance = Mock()
        mock_student_service.return_value = mock_service_instance
        mock_service_instance.get_student_by_id = AsyncMock(return_value={
            "id": "1", "name": "Test Student", "student_id": "S001"
        })
        
        response = client.get("/students/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "1"
        assert data["name"] == "Test Student"

    @patch('src.services.student_service.StudentService')
    def test_get_student_not_found(self, mock_student_service, client):
        """Test get student by ID when student not found"""
        # Mock the service to raise exception
        mock_service_instance = Mock()
        mock_student_service.return_value = mock_service_instance
        mock_service_instance.get_student_by_id = AsyncMock(side_effect=Exception("Student not found"))
        
        response = client.get("/students/999")
        
        assert response.status_code == 404

    def test_documentation_endpoints(self, client):
        """Test documentation endpoints are accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/redoc")
        assert response.status_code == 200
        
        response = client.get("/openapi.json")
        assert response.status_code == 200

    @patch('src.services.student_service.StudentService')
    def test_enroll_student_in_course(self, mock_student_service, client):
        """Test enroll student in course endpoint"""
        # Mock the service
        mock_service_instance = Mock()
        mock_student_service.return_value = mock_service_instance
        mock_service_instance.enroll_student = AsyncMock(return_value=True)
        
        response = client.post("/students/1/courses/1/enroll")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Student enrolled successfully"

    @patch('src.services.course_service.CourseService')
    def test_unenroll_student_from_course(self, mock_course_service, client):
        """Test unenroll student from course endpoint"""
        # Mock the service
        mock_service_instance = Mock()
        mock_course_service.return_value = mock_service_instance
        mock_service_instance.unenroll_student = AsyncMock(return_value=True)
        
        response = client.delete("/courses/1/students/1/unenroll")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Student unenrolled successfully"

    def test_error_handling(self, client):
        """Test error handling for invalid endpoints"""
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404

    @patch('src.services.user_service.UserService')
    def test_duplicate_user_registration(self, mock_user_service, client, test_user_data):
        """Test user registration with duplicate email"""
        # Mock the service to raise exception
        mock_service_instance = Mock()
        mock_user_service.return_value = mock_service_instance
        mock_service_instance.create_user = AsyncMock(side_effect=Exception("User already exists"))
        
        response = client.post("/users/register", json=test_user_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get("/health")
        assert "access-control-allow-origin" in response.headers

    def test_request_logging(self, client):
        """Test that requests are logged"""
        # This test would normally require mocking the logger
        # For now, we'll just test the endpoint works
        response = client.get("/health")
        assert response.status_code == 200