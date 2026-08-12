import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import os
import sys
from unittest.mock import Mock, AsyncMock

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def auth_test_data() -> Dict[str, Any]:
    """Test data for authentication system"""
    return {
        "valid_user": {
            "email": "test@example.com",
            "password": "Password123!",
            "name": "Test User",
            "role": "teacher"
        },
        "admin_user": {
            "email": "admin@example.com",
            "password": "Admin123!",
            "name": "Admin User",
            "role": "admin"
        },
        "student_user": {
            "email": "student@example.com", 
            "password": "Student123!",
            "name": "Student User",
            "role": "student"
        },
        "invalid_credentials": {
            "email": "invalid@example.com",
            "password": "wrongpassword"
        },
        "malformed_email": {
            "email": "invalid-email",
            "password": "Password123!"
        },
        "weak_password": {
            "email": "test@example.com",
            "password": "short"
        },
        "missing_fields": {
            "email": "test@example.com"
        }
    }

@pytest.fixture
def mock_jwt_tokens() -> Dict[str, str]:
    """Mock JWT tokens for testing"""
    return {
        "valid_admin_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsImV4cCI6MTk4ODgwODIwMCwiaWF0IjoxNjk4ODgwMjAwfQ.test_signature",
        "valid_teacher_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWFzdGVyQGV4YW1wbGUuY29tIiwiZXhwIjoxOTg4ODA4MjAwLCJpYXQiOTo2OTg4ODAyMDAwfQ.test_signature",
        "valid_student_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50QGV4YW1wbGUuY29tIiwiZXhwIjoxOTg4ODA4MjAwLCJpYXQiOTo2OTg4ODAyMDAwfQ.test_signature",
        "expired_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNjQ4ODgwODIwMCwiaWF0IjoxNjk4ODAyMDAwfQ.test_signature",
        "invalid_token": "invalid.token.signature",
        "no_token": ""
    }

@pytest.fixture
def test_headers(mock_jwt_tokens):
    """Test headers for API requests"""
    return {
        "valid_admin": {"Authorization": f"Bearer {mock_jwt_tokens['valid_admin_token']}"},
        "valid_teacher": {"Authorization": f"Bearer {mock_jwt_tokens['valid_teacher_token']}"},
        "valid_student": {"Authorization": f"Bearer {mock_jwt_tokens['valid_student_token']}"},
        "expired": {"Authorization": f"Bearer {mock_jwt_tokens['expired_token']}"},
        "invalid": {"Authorization": f"Bearer {mock_jwt_tokens['invalid_token']}"},
        "no_auth": {},
        "invalid_auth": {"Authorization": "Invalid Bearer Token"}
    }

@pytest.fixture
def mock_database_operations():
    """Mock database operations for testing"""
    return {
        "find_user_by_email": lambda email: {
            "email": email,
            "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPkU2Cslq",  # password123
            "name": "Test User",
            "role": "teacher",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }.get(email) if email in ["test@example.com", "admin@example.com", "student@example.com"] else None,
        
        "create_user": lambda user_data: {
            "id": "user123",
            "email": user_data["email"],
            "password_hash": user_data["password"],
            "name": user_data["name"],
            "role": user_data["role"],
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        
        "update_user": lambda user_id, user_data: True,
        
        "delete_user": lambda user_id: True,
        
        "find_user_by_id": lambda user_id: {
            "id": user_id,
            "email": "test@example.com",
            "name": "Test User",
            "role": "teacher",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        } if user_id == "user123" else None,
        
        "get_all_users": lambda: [
            {
                "id": "user123",
                "email": "test@example.com",
                "name": "Test User",
                "role": "teacher",
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
    }

@pytest.fixture
def mock_password_operations():
    """Mock password operations for testing"""
    return {
        "hash_password": lambda password: "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPkU2Cslq",  # password123
        
        "verify_password": lambda plain_password, hashed_password: plain_password == "password123" and hashed_password == "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPkU2Cslq",
        
        "is_strong_password": lambda password: len(password) >= 8 and any(c.isdigit() for c in password) and any(c.isalpha() for c in password),
        
        "is_valid_email": lambda email: "@" in email and "." in email.split("@")[-1]
    }

@pytest.fixture
def mock_user_repository():
    """Mock user repository for testing"""
    from unittest.mock import Mock, AsyncMock
    
    mock_repo = Mock()
    mock_repo.get_by_email = Mock(return_value=None)  # Return None by default, can be overridden in tests
    mock_repo.create = AsyncMock()
    mock_repo.update = AsyncMock()
    mock_repo.get_by_id = Mock(return_value=None)  # Return None by default, can be overridden in tests
    mock_repo.get_all = Mock(return_value=[])
    mock_repo.delete = Mock(return_value=True)
    
    return mock_repo

@pytest.fixture
def mock_student_repository():
    """Mock student repository for testing"""
    
    mock_repo = Mock()
    mock_repo.create = AsyncMock()
    mock_repo.update = AsyncMock()
    mock_repo.get_by_id = AsyncMock()
    mock_repo.get_by_email = AsyncMock()
    mock_repo.get_by_student_id = AsyncMock()
    mock_repo.get_all = Mock(return_value=[])
    mock_repo.delete = Mock(return_value=True)
    
    return mock_repo

@pytest.fixture
def mock_teacher_repository():
    """Mock teacher repository for testing"""
    
    mock_repo = Mock()
    mock_repo.create = AsyncMock(return_value={"id": "teacher-123", "name": "Jane Smith", "email": "jane@example.com"})
    mock_repo.get_by_id = Mock(return_value={"id": "teacher-123", "name": "Jane Smith", "email": "jane@example.com"})
    mock_repo.get_by_email = Mock(return_value={"id": "teacher-123", "name": "Jane Smith", "email": "jane@example.com"})
    mock_repo.get_all = Mock(return_value=[{"id": "teacher-123", "name": "Jane Smith", "email": "jane@example.com"}])
    mock_repo.update = Mock(return_value=True)
    mock_repo.delete = Mock(return_value=True)
    
    return mock_repo

@pytest.fixture
def mock_department_repository():
    """Mock department repository for testing"""
    
    mock_repo = Mock()
    mock_repo.create = AsyncMock(return_value={"id": "dept-123", "name": "Computer Science", "code": "CS"})
    mock_repo.get_by_id = Mock(return_value={"id": "dept-123", "name": "Computer Science", "code": "CS"})
    mock_repo.get_by_code = Mock(return_value={"id": "dept-123", "name": "Computer Science", "code": "CS"})
    mock_repo.get_all = Mock(return_value=[{"id": "dept-123", "name": "Computer Science", "code": "CS"}])
    mock_repo.update = Mock(return_value=True)
    mock_repo.delete = Mock(return_value=True)
    
    return mock_repo

@pytest.fixture
def mock_enrollment_repository():
    """Mock enrollment repository for testing"""
    
    mock_repo = Mock()
    mock_repo.create = AsyncMock()
    mock_repo.update = AsyncMock()
    mock_repo.get_by_student_id = AsyncMock()
    mock_repo.get_by_id = AsyncMock()
    mock_repo.get_all = Mock(return_value=[])
    mock_repo.delete = Mock(return_value=True)
    
    return mock_repo

@pytest.fixture
def mock_course_repository():
    """Mock course repository for testing"""
    
    mock_repo = Mock()
    mock_repo.get_by_id = AsyncMock()
    mock_repo.create = AsyncMock()
    mock_repo.update = AsyncMock()
    mock_repo.get_all = Mock(return_value=[])
    mock_repo.delete = Mock(return_value=True)
    
    return mock_repo

@pytest.fixture
def sample_course():
    """Sample course data for testing"""
    # Create a mock object that has the attributes expected by the enrollment service
    from unittest.mock import Mock
    
    course = Mock()
    course.id = "course-123"
    course.name = "Mathematics"
    course.code = "MATH101"
    course.description = "Basic mathematics course"
    course.capacity = 30
    course.enrolled_students = 25
    course.credits = 3
    course.department_id = "dept-123"
    
    return course

@pytest.fixture
def sample_student():
    """Sample student data for testing"""
    return {
        "id": "student-123",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "student_id": "STU001",
        "grade_level": 10,
        "phone": "123-456-7890",
        "address": "123 Main St"
    }

@pytest.fixture
def sample_teacher():
    """Sample teacher data for testing"""
    return {
        "id": "teacher-123",
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "employee_id": "EMP001",
        "department_id": "dept-123"
    }

@pytest.fixture
def sample_student_data():
    """Sample student data for testing"""
    return {
        "student_id": "STU001",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "grade_level": 10,
        "enrollment_date": "2023-09-01",
        "phone": "123-456-7890",
        "address": "123 Main St"
    }

@pytest.fixture
def sample_academic_record():
    """Sample academic record data for testing"""
    return {
        "student_id": "student-123",
        "course_id": "course-123",
        "grade": 85.0,
        "credits": 3.0,
        "semester": "Fall",
        "academic_year": "2023-2024",
        "grade_letter": "B",
        "instructor_id": "teacher-123"
    }

@pytest.fixture
def sample_department():
    """Sample department data for testing"""
    return {
        "id": "dept-123",
        "name": "Computer Science",
        "code": "CS",
        "description": "Computer Science Department"
    }

@pytest.fixture
def mock_academic_record_repository():
    """Mock academic record repository"""
    
    mock_repo = Mock()
    mock_repo.create = AsyncMock()
    mock_repo.update = AsyncMock()
    mock_repo.get_by_student_id = AsyncMock()
    mock_repo.get_by_id = AsyncMock()
    mock_repo.get_all = Mock(return_value=[])
    return mock_repo