import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.security import AuthService
from src.core.exceptions import AuthenticationError, ValidationError, NotFoundError


class TestUserManagement:
    """Test suite for User Management System"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.authService = AuthService()
        self.test_secret_key = "test-secret-key"
        self.authService.secret_key = self.test_secret_key
        self.authService.algorithm = "HS256"
        
    def test_user_creation_validation(self):
        """Test user creation validation"""
        # Test invalid email
        with pytest.raises(ValidationError, match="Invalid email format"):
            self.authService.create_user(
                email="invalid-email",
                password="Password123!",
                name="Test User",
                role="student"
            )
        
        # Test weak password
        with pytest.raises(ValidationError, match="Password does not meet requirements"):
            self.authService.create_user(
                email="test@example.com",
                password="weak",
                name="Test User",
                role="student"
            )
        
        # Test invalid role
        with pytest.raises(ValidationError, match="Invalid role"):
            self.authService.create_user(
                email="test@example.com",
                password="Password123!",
                name="Test User",
                role="invalid_role"
            )
        
        # Test valid user creation
        user = self.authService.create_user(
            email="test@example.com",
            password="Password123!",
            name="Test User",
            role="student"
        )
        
        assert user["email"] == "test@example.com"
        assert user["name"] == "Test User"
        assert user["role"] == "student"
        assert "user_id" in user
        assert "created_at" in user
    
    def test_user_update_validation(self):
        """Test user update validation"""
        # Create a user first
        user = self.authService.create_user(
            email="test@example.com",
            password="Password123!",
            name="Test User",
            role="student"
        )
        
        user_id = user["user_id"]
        
        # Test invalid email update
        with pytest.raises(ValidationError, match="Invalid email format"):
            self.authService.update_user(
                user_id=user_id,
                email="invalid-email",
                name="Updated Name"
            )
        
        # Test valid user update
        updated_user = self.authService.update_user(
            user_id=user_id,
            email="updated@example.com",
            name="Updated User",
            bio="This is a test bio"
        )
        
        assert updated_user["email"] == "updated@example.com"
        assert updated_user["name"] == "Updated User"
        assert updated_user["bio"] == "This is a test bio"
    
    def test_user_deactivation(self):
        """Test user deactivation"""
        # Create a user first
        user = self.authService.create_user(
            email="test@example.com",
            password="Password123!",
            name="Test User",
            role="student"
        )
        
        user_id = user["user_id"]
        
        # Deactivate user
        deactivated_user = self.authService.deactivate_user(user_id)
        
        assert deactivated_user["is_active"] == False
        assert deactivated_user["deactivated_at"] is not None
        
        # Try to login with deactivated user
        with pytest.raises(AuthenticationError, match="Account is disabled"):
            self.authService.authenticate_user(
                email="test@example.com",
                password="Password123!"
            )
    
    def test_user_role_change(self):
        """Test user role change"""
        # Create a user first
        user = self.authService.create_user(
            email="test@example.com",
            password="Password123!",
            name="Test User",
            role="student"
        )
        
        user_id = user["user_id"]
        
        # Change role
        updated_user = self.authService.change_user_role(
            user_id=user_id,
            new_role="teacher"
        )
        
        assert updated_user["role"] == "teacher"
        
        # Verify new role works for authentication
        auth_result = self.authService.authenticate_user(
            email="test@example.com",
            password="Password123!"
        )
        assert auth_result["role"] == "teacher"
    
    def test_user_password_change(self):
        """Test user password change"""
        # Create a user first
        user = self.authService.create_user(
            email="test@example.com",
            password="Password123!",
            name="Test User",
            role="student"
        )
        
        user_id = user["user_id"]
        old_password_hash = user["password_hash"]
        
        # Change password
        self.authService.change_user_password(
            user_id=user_id,
            new_password="NewPassword123!"
        )
        
        # Verify old password doesn't work
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            self.authService.authenticate_user(
                email="test@example.com",
                password="Password123!"
            )
        
        # Verify new password works
        auth_result = self.authService.authenticate_user(
            email="test@example.com",
            password="NewPassword123!"
        )
        assert auth_result["user_id"] == user_id
    
    def test_user_profile_update(self):
        """Test user profile update"""
        # Create a user first
        user = self.authService.create_user(
            email="test@example.com",
            password="Password123!",
            name="Test User",
            role="student"
        )
        
        user_id = user["user_id"]
        
        # Update profile
        profile_data = {
            "name": "Updated Name",
            "phone": "+1234567890",
            "department": "Computer Science",
            "bio": "This is a test bio",
            "preferences": {
                "language": "en",
                "theme": "dark",
                "notifications": True
            }
        }
        
        updated_user = self.authService.update_user_profile(
            user_id=user_id,
            **profile_data
        )
        
        assert updated_user["name"] == "Updated Name"
        assert updated_user["phone"] == "+1234567890"
        assert updated_user["department"] == "Computer Science"
        assert updated_user["bio"] == "This is a test bio"
        assert updated_user["preferences"] == profile_data["preferences"]
    
    def test_user_search_and_filter(self):
        """Test user search and filtering"""
        # Create multiple users
        users = []
        for i in range(5):
            user = self.authService.create_user(
                email=f"user{i}@example.com",
                password="Password123!",
                name=f"User {i}",
                role="student" if i < 3 else "teacher"
            )
            users.append(user)
        
        # Search by name
        search_results = self.authService.search_users(
            query="User 1",
            role="student"
        )
        assert len(search_results) == 1
        assert search_results[0]["name"] == "User 1"
        
        # Filter by role
        teacher_results = self.authService.search_users(
            query="",
            role="teacher"
        )
        assert len(teacher_results) == 2
        
        # Filter by department (assuming some users have departments)
        department_results = self.authService.search_users(
            query="",
            department="Computer Science"
        )
        # This will depend on which users were assigned the department
        
        # Pagination
        paginated_results = self.authService.search_users(
            query="User",
            role="student",
            page=1,
            page_size=2
        )
        assert len(paginated_results) <= 2
    
    def test_user_activity_logging(self):
        """Test user activity logging"""
        # Create a user first
        user = self.authService.create_user(
            email="test@example.com",
            password="Password123!",
            name="Test User",
            role="student"
        )
        
        user_id = user["user_id"]
        
        # Simulate user activities
        activities = [
            {"action": "login", "timestamp": datetime.now(), "ip": "127.0.0.1"},
            {"action": "view_profile", "timestamp": datetime.now(), "ip": "127.0.0.1"},
            {"action": "update_settings", "timestamp": datetime.now(), "ip": "127.0.0.1"}
        ]
        
        for activity in activities:
            self.authService.log_user_activity(
                user_id=user_id,
                action=activity["action"],
                ip=activity["ip"]
            )
        
        # Get user activities
        user_activities = selfAuthService.get_user_activities(user_id)
        assert len(user_activities) >= len(activities)
        
        # Filter activities by action
        login_activities = self.authService.get_user_activities(
            user_id=user_id,
            action="login"
        )
        assert all(activity["action"] == "login" for activity in login_activities)
    
    def test_user_bulk_operations(self):
        """Test bulk user operations"""
        # Create multiple users
        users = []
        for i in range(3):
            user = self.authService.create_user(
                email=f"bulk_user{i}@example.com",
                password="Password123!",
                name=f"Bulk User {i}",
                role="student"
            )
            users.append(user)
        
        user_ids = [user["user_id"] for user in users]
        
        # Bulk deactivate
        deactivated_users = self.authService.bulk_deactivate_users(user_ids)
        assert len(deactivated_users) == len(user_ids)
        assert all(user["is_active"] == False for user in deactivated_users)
        
        # Bulk reactivate
        reactivated_users = self.authService.bulk_reactivate_users(user_ids)
        assert len(reactivated_users) == len(user_ids)
        assert all(user["is_active"] == True for user in reactivated_users)
    
    def test_user_permission_validation(self):
        """Test user permission validation"""
        # Create users with different roles
        student = self.authService.create_user(
            email="student@example.com",
            password="Password123!",
            name="Student User",
            role="student"
        )
        
        teacher = self.authService.create_user(
            email="teacher@example.com",
            password="Password123!",
            name="Teacher User",
            role="teacher"
        )
        
        admin = self.authService.create_user(
            email="admin@example.com",
            password="Password123!",
            name="Admin User",
            role="admin"
        )
        
        # Test permission checks
        # Students can view their own profile
        assert self.authService.check_permission(
            user_id=student["user_id"],
            action="view_profile",
            target_user_id=student["user_id"]
        ) == True
        
        # Students cannot view other students' profiles
        assert self.authService.check_permission(
            user_id=student["user_id"],
            action="view_profile",
            target_user_id=teacher["user_id"]
        ) == False
        
        # Teachers can view student profiles
        assert self.authService.check_permission(
            user_id=teacher["user_id"],
            action="view_profile",
            target_user_id=student["user_id"]
        ) == True
        
        # Admins can view all profiles
        assert self.authService.check_permission(
            user_id=admin["user_id"],
            action="view_profile",
            target_user_id=student["user_id"]
        ) == True
        
        assert self.authService.check_permission(
            user_id=admin["user_id"],
            action="view_profile",
            target_user_id=teacher["user_id"]
        ) == True
    
    def test_user_audit_trail(self):
        """Test user audit trail"""
        # Create a user first
        user = self.authService.create_user(
            email="test@example.com",
            password="Password123!",
            name="Test User",
            role="student"
        )
        
        user_id = user["user_id"]
        
        # Perform various operations
        self.authService.update_user(
            user_id=user_id,
            name="Updated Name"
        )
        
        selfAuthService.change_user_role(
            user_id=user_id,
            new_role="teacher"
        )
        
        self.authService.change_user_password(
            user_id=user_id,
            new_password="NewPassword123!"
        )
        
        # Get audit trail
        audit_trail = self.authService.get_user_audit_trail(user_id)
        
        # Verify audit entries exist
        assert len(audit_trail) >= 3
        
        # Verify specific entries
        entry_types = [entry["action"] for entry in audit_trail]
        assert "update" in entry_types
        assert "role_change" in entry_types
        assert "password_change" in entry_types
        
        # Verify timestamps
        for entry in audit_trail:
            assert "timestamp" in entry
            assert "user_id" in entry
            assert "action" in entry