"""
Complete API Integration Test Suite

This test suite validates all API endpoints and their interactions
with the database services.
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the application
from src.api.v1 import app
from src.core.dependencies import get_db
from src.core.security import SecurityConfig
from src.models.course import Course
from src.models.student import StudentBase as Student
from src.models.user import User
from src.services.user_service import UserService
from src.services.student_service import StudentService
from src.services.course_service import CourseService


class TestAPIComplete:
    """Complete API test suite"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def test_user_data(self):
        """Test user data"""
        return {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test User",
            "role": "student"
        }
    
    @pytest.fixture
    def test_course_data(self):
        """Test course data"""
        return {
            "name": "Test Course",
            "code": "TC101",
            "credits": 3,
            "semester": "Fall 2023"
        }
    
    @pytest.fixture
    def auth_headers(self, client):
        """Create authentication headers"""
        # Register user first
        user_data = {
            "email": "auth@example.com",
            "password": "authpass123",
            "name": "Auth User",
            "role": "student"
        }
        
        response = client.post("/users/register", json=user_data)
        assert response.status_code == 200
        
        # Get access token
        response = client.post("/users/token", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        assert response.status_code == 200
        
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def admin_auth_headers(self, client):
        """Create admin authentication headers"""
        # Register admin user
        admin_data = {
            "email": "admin@example.com",
            "password": "adminpass123",
            "name": "Admin User",
            "role": "admin"
        }
        
        response = client.post("/users/register", json=admin_data)
        assert response.status_code == 200
        
        # Get access token
        response = client.post("/users/token", data={
            "username": admin_data["email"],
            "password": admin_data["password"]
        })
        assert response.status_code == 200
        
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    # ====================== System Endpoints ======================
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_api_info(self, client):
        """Test API info endpoint"""
        response = client.get("/api/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data
    
    def test_api_stats(self, client):
        """Test API stats endpoint"""
        response = client.get("/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "endpoints_count" in data
        assert "version" in data
    
    # ====================== Authentication Endpoints ======================
    
    def test_register_user(self, client, test_user_data):
        """Test user registration"""
        response = client.post("/users/register", json=test_user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "user_id" in data
        
        # Verify user exists
        response = client.get("/users/")
        assert response.status_code == 200
        users = response.json()
        assert len(users) > 0
    
    def test_login_for_access_token(self, client, test_user_data):
        """Test login and token generation"""
        # Register user first
        client.post("/users/register", json=test_user_data)
        
        # Login
        response = client.post("/users/token", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_get_current_user(self, client, auth_headers):
        """Test get current user endpoint"""
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "email" in data
        assert "name" in data
        assert "role" in data
    
    def test_get_users(self, client, test_user_data, auth_headers):
        """Test get users endpoint"""
        # Register a test user
        client.post("/users/register", json=test_user_data)
        
        response = client.get("/users/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_users_with_pagination(self, client, test_user_data, auth_headers):
        """Test users endpoint with pagination"""
        # Register multiple test users
        for i in range(5):
            user_data = test_user_data.copy()
            user_data["email"] = f"user{i}@example.com"
            user_data["name"] = f"User {i}"
            client.post("/users/register", json=user_data)
        
        # Test with limit
        response = client.get("/users/?limit=2", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) <= 2
    
    def test_get_users_with_role_filter(self, client, test_user_data, auth_headers):
        """Test users endpoint with role filter"""
        # Register test user with different roles
        client.post("/users/register", test_user_data)  # student
        admin_data = test_user_data.copy()
        admin_data["email"] = "admin@example.com"
        admin_data["role"] = "admin"
        client.post("/users/register", admin_data)  # admin
        
        # Filter by role
        response = client.get("/users/?role=student", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert all(user["role"] == "student" for user in data)
    
    def test_get_users_with_search(self, client, test_user_data, auth_headers):
        """Test users endpoint with search"""
        # Register test users
        client.post("/users/register", test_user_data)  # Test User
        
        # Search
        response = client.get("/users/?search=Test", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0
    
    def test_update_user(self, client, auth_headers):
        """Test update user endpoint"""
        response = client.get("/users/me", headers=auth_headers)
        user_id = response.json()["id"]
        
        update_data = {"name": "Updated Name", "email": "updated@example.com"}
        response = client.put(f"/users/{user_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        
        # Verify update
        response = client.get("/users/me", headers=auth_headers)
        assert response.json()["name"] == "Updated Name"
    
    def test_activate_user(self, client, admin_auth_headers):
        """Test activate user endpoint"""
        # Get all users
        response = client.get("/users/", headers=admin_auth_headers)
        user_id = response.json()[0]["id"]
        
        response = client.post(f"/users/{user_id}/activate", headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
    
    def test_deactivate_user(self, client, admin_auth_headers):
        """Test deactivate user endpoint"""
        # Get all users
        response = client.get("/users/", headers=admin_auth_headers)
        user_id = response.json()[0]["id"]
        
        response = client.post(f"/users/{user_id}/deactivate", headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
    
    # ====================== Student Management Endpoints ======================
    
    def test_get_students(self, client, auth_headers):
        """Test get students endpoint"""
        response = client.get("/students/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_students_with_department_filter(self, client, auth_headers):
        """Test students endpoint with department filter"""
        response = client.get("/students/?department_id=test-dept", headers=auth_headers)
        assert response.status_code == 200
    
    def test_get_students_with_course_filter(self, client, auth_headers):
        """Test students endpoint with course filter"""
        response = client.get("/students/?course_id=test-course", headers=auth_headers)
        assert response.status_code == 200
    
    def test_get_student_by_id(self, client, auth_headers):
        """Test get student by ID endpoint"""
        response = client.get("/students/test-student-id", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "student_id" in data
        assert "user" in data
    
    def test_enroll_student_in_course(self, client, auth_headers):
        """Test enroll student in course endpoint"""
        response = client.post("/students/test-student-id/courses/test-course-id/enroll", 
                             headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
    
    def test_unenroll_student_from_course(self, client, auth_headers):
        """Test unenroll student from course endpoint"""
        response = client.delete("/students/test-student-id/courses/test-course-id/unenroll",
                               headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
    
    def test_get_student_courses(self, client, auth_headers):
        """Test get student courses endpoint"""
        response = client.get("/students/test-student-id/courses", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_student_marks(self, client, auth_headers):
        """Test get student marks endpoint"""
        response = client.get("/students/test-student-id/marks", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_student_marks_with_course_filter(self, client, auth_headers):
        """Test get student marks with course filter"""
        response = client.get("/students/test-student-id/marks?course_id=test-course", 
                             headers=auth_headers)
        assert response.status_code == 200
    
    def test_get_student_performance(self, client, auth_headers):
        """Test get student performance endpoint"""
        response = client.get("/students/test-student-id/performance", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_student_attendance(self, client, auth_headers):
        """Test get student attendance endpoint"""
        response = client.get("/students/test-student-id/attendance", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    # ====================== Course Management Endpoints ======================
    
    def test_get_courses(self, client, auth_headers):
        """Test get courses endpoint"""
        response = client.get("/courses/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_courses_with_department_filter(self, client, auth_headers):
        """Test courses endpoint with department filter"""
        response = client.get("/courses/?department_id=test-dept", headers=auth_headers)
        assert response.status_code == 200
    
    def test_get_courses_with_semester_filter(self, client, auth_headers):
        """Test courses endpoint with semester filter"""
        response = client.get("/courses/?semester=Fall+2023", headers=auth_headers)
        assert response.status_code == 200
    
    def test_create_course(self, client, admin_auth_headers, test_course_data):
        """Test create course endpoint"""
        response = client.post("/courses/", json=test_course_data, headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
    
    def test_update_course(self, client, admin_auth_headers, test_course_data):
        """Test update course endpoint"""
        # Create course first
        response = client.post("/courses/", json=test_course_data, headers=admin_auth_headers)
        assert response.status_code == 200
        
        # Update course
        update_data = {"name": "Updated Course Name"}
        response = client.put("/courses/test-course-id", json=update_data, headers=admin_auth_headers)
        assert response.status_code == 200
    
    def test_get_course_students(self, client, auth_headers):
        """Test get course students endpoint"""
        response = client.get("/courses/test-course-id/students", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_course_performance(self, client, auth_headers):
        """Test get course performance endpoint"""
        response = client.get("/courses/test-course-id/performance", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_course_schedule(self, client, auth_headers):
        """Test get course schedule endpoint"""
        response = client.get("/courses/test-course-id/schedule", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_course_assignments(self, client, auth_headers):
        """Test get course assignments endpoint"""
        response = client.get("/courses/test-course-id/assignments", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_course_attendance(self, client, auth_headers):
        """Test get course attendance endpoint"""
        response = client.get("/courses/test-course-id/attendance", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    # ====================== Error Handling ======================
    
    def test_invalid_token(self, client):
        """Test with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 401
    
    def test_no_token(self, client):
        """Test without token"""
        response = client.get("/users/me")
        assert response.status_code == 401
    
    def test_insufficient_permissions(self, client, auth_headers):
        """Test with insufficient permissions"""
        response = client.get("/users/100000/not-found-user", headers=auth_headers)
        assert response.status_code == 404
    
    def test_invalid_request_data(self, client):
        """Test with invalid request data"""
        response = client.post("/users/register", {})
        assert response.status_code == 422
    
    # ====================== Performance Tests ======================
    
    def test_multiple_requests_performance(self, client):
        """Test performance with multiple requests"""
        import time
        
        start_time = time.time()
        
        # Make multiple requests
        for i in range(10):
            response = client.get("/health")
            assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete in reasonable time (less than 5 seconds)
        assert total_time < 5
    
    def test_concurrent_requests(self, client):
        """Test concurrent requests"""
        import concurrent.futures
        import time
        
        def make_request():
            return client.get("/health")
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # All requests should be successful
        for result in results:
            assert result.status_code == 200
    
    # ====================== Integration Tests ======================
    
    def test_user_student_lifecycle(self, client, test_user_data, auth_headers):
        """Test complete user to student lifecycle"""
        # Step 1: Register user
        response = client.post("/users/register", json=test_user_data)
        assert response.status_code == 200
        
        # Step 2: Login
        response = client.post("/users/token", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Step 3: Get user profile
        response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        user_id = response.json()["id"]
        
        # Step 4: Update user
        update_data = {"name": "Updated User Name"}
        response = client.put(f"/users/{user_id}", json=update_data, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        
        # Step 5: Get updated user
        response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["name"] == "Updated User Name"
    
    def test_course_enrollment_lifecycle(self, client, auth_headers, admin_auth_headers):
        """Test complete course enrollment lifecycle"""
        # Step 1: Create course
        course_data = {
            "name": "Test Course",
            "code": "TC101",
            "credits": 3,
            "semester": "Fall 2023"
        }
        response = client.post("/courses/", json=course_data, headers=admin_auth_headers)
        assert response.status_code == 200
        
        # Step 2: Get course
        response = client.get("/courses/", headers=auth_headers)
        course_id = response.json()[0]["id"]
        
        # Step 3: Enroll student
        response = client.post(f"/students/test-student-id/courses/{course_id}/enroll", 
                             headers=auth_headers)
        assert response.status_code == 200
        
        # Step 4: Get student courses
        response = client.get("/students/test-student-id/courses", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) > 0
        
        # Step 5: Unenroll student
        response = client.delete(f"/students/test-student-id/courses/{course_id}/unenroll",
                               headers=auth_headers)
        assert response.status_code == 200
        
        # Step 6: Verify unenrollment
        response = client.get("/students/test-student-id/courses", headers=auth_headers)
        assert response.status_code == 200
    
    def test_admin_operations(self, client, admin_auth_headers):
        """Test admin operations"""
        # Step 1: Register multiple users
        for i in range(3):
            user_data = {
                "email": f"adminuser{i}@example.com",
                "password": "pass123",
                "name": f"Admin User {i}",
                "role": "student"
            }
            response = client.post("/users/register", json=user_data)
            assert response.status_code == 200
        
        # Step 2: Get all users
        response = client.get("/users/", headers=admin_auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 3
        
        # Step 3: Activate/deactivate users
        users = response.json()
        for user in users[:2]:
            response = client.post(f"/users/{user['id']}/deactivate", headers=admin_auth_headers)
            assert response.status_code == 200
            
            response = client.post(f"/users/{user['id']}/activate", headers=admin_auth_headers)
            assert response.status_code == 200
        
        # Step 4: Create multiple courses
        for i in range(3):
            course_data = {
                "name": f"Admin Course {i}",
                "code": f"AC{i:03d}",
                "credits": 3,
                "semester": "Fall 2023"
            }
            response = client.post("/courses/", json=course_data, headers=admin_auth_headers)
            assert response.status_code == 200
        
        # Step 5: Get all courses
        response = client.get("/courses/", headers=admin_auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 3

    @pytest.mark.parametrize("endpoint,method", [
        ("/users/", "GET"),
        ("/users/me", "GET"),
        ("/students/", "GET"),
        ("/courses/", "GET"),
        ("/health", "GET"),
    ])
    def test_endpoint_security(self, client, endpoint, method):
        """Test that endpoints require authentication"""
        if method == "GET":
            response = client.get(endpoint)
        else:
            response = client.post(endpoint)
        
        assert response.status_code == 401

    # ====================== Cleanup ======================
    
    @pytest.fixture(autouse=True)
    def cleanup(self, client, admin_auth_headers):
        """Cleanup test data"""
        try:
            # Clean up users
            response = client.get("/users/", headers=admin_auth_headers)
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    if user["email"].startswith(("test", "auth", "admin")):
                        response = client.post(f"/users/{user['id']}/deactivate", 
                                             headers=admin_auth_headers)
            
            # Clean up courses
            response = client.get("/courses/", headers=admin_auth_headers)
            if response.status_code == 200:
                courses = response.json()
                for course in courses:
                    if course["name"].startswith(("Test", "Admin", "Course")):
                        response = client.delete(f"/courses/{course['id']}", 
                                               headers=admin_auth_headers)
        except Exception as e:
            print(f"Cleanup error: {e}")