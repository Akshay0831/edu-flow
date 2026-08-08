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
        # Create mock user service
        self.mock_user_service = Mock()
        
        # Create auth service first
        self.authService = AuthService()
        self.test_secret_key = "test-secret-key"
        self.authService.secret_key = self.test_secret_key
        self.authService.algorithm = "HS256"
        # Track created emails for mock
        self.created_emails = set()
        
        # Mock get_user_by_email to return NotFoundError for non-existent users
        # but return the user for authentication
        # Mock get_user_by_email to return NotFoundError for non-existent users
        # but return the user for authentication
        def mock_get_user_by_email(email):
            if email == "admin@example.com":
                return {
                    "user_id": "admin-id",
                    "email": "admin@example.com",
                    "password_hash": "hashed_password",
                    "name": "Admin User",
                    "role": "admin",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            elif email in self.created_emails:
                # Return user data for created emails
                if email == "student@example.com":
                    return {
                        "user_id": "student-id",
                        "email": "student@example.com",
                        "password_hash": "hashed_password",
                        "name": "Student User",
                        "role": "student",
                        "is_active": True,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
                elif email == "teacher@example.com":
                    return {
                        "user_id": "teacher-id",
                        "email": "teacher@example.com",
                        "password_hash": "hashed_password",
                        "name": "Teacher User",
                        "role": "teacher",
                        "is_active": True,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
                elif email == "admin2@example.com":
                    return {
                        "user_id": "admin2-id",
                        "email": "admin2@example.com",
                        "password_hash": "hashed_password",
                        "name": "Admin User",
                        "role": "admin",
                        "is_active": True,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
                elif email == "test@example.com":
                    return {
                        "user_id": "test-user-id",
                        "email": "test@example.com",
                        "password_hash": self.authService.get_password_hash("Password123!"),
                        "name": "Test User",
                        "role": "student",
                        "is_active": True,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
            else:
                raise NotFoundError("User not found")
        
        def mock_get_user(user_id):
            user_map = {
                "student-id": {
                    "user_id": "student-id",
                    "email": "student@example.com",
                    "name": "Student User",
                    "role": "student",
                    "password_hash": "hashed_password",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                "teacher-id": {
                    "user_id": "teacher-id",
                    "email": "teacher@example.com",
                    "name": "Teacher User",
                    "role": "teacher",
                    "password_hash": "hashed_password",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                "admin-id": {
                    "user_id": "admin-id",
                    "email": "admin@example.com",
                    "name": "Admin User",
                    "role": "admin",
                    "password_hash": "hashed_password",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                "admin2-id": {
                    "user_id": "admin2-id",
                    "email": "admin2@example.com",
                    "name": "Admin User",
                    "role": "admin",
                    "password_hash": "hashed_password",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                "test-user-id": {
                    "user_id": "test-user-id",
                    "email": "test@example.com",
                    "name": "Test User",
                    "role": "student",
                    "password_hash": self.authService.get_password_hash("Password123!"),
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            }
            return user_map.get(user_id, None)
        
        self.mock_user_service.get_user_by_email.side_effect = mock_get_user_by_email
        self.mock_user_service.get_user.side_effect = mock_get_user
        
        self.mock_user_service.get_user_by_email.side_effect = mock_get_user_by_email
        def mock_create_user(email, password, name, role):
            # Generate unique user_id based on email
            email_to_id = {
                "student@example.com": "student-id",
                "teacher@example.com": "teacher-id", 
                "admin2@example.com": "admin2-id",
                "test@example.com": "test-user-id"
            }
            user_id = email_to_id.get(email, f"user-{hash(email) % 10000}")
            
            # Add to created emails for mock_get_user_by_email to work
            self.created_emails.add(email)
            
            # Create user data for get_user mock
            user_data = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "role": role,
                "password_hash": "hashed_password",
                "is_active": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # Add to created users dict for get_user mock
            if not hasattr(self, 'created_users_dict'):
                self.created_users_dict = {}
            self.created_users_dict[user_id] = user_data
            
            # Return user creation result
            return {
                "user_id": user_id,
                "created_at": datetime.now()
            }
        
        self.mock_user_service.create_user.side_effect = mock_create_user
        def mock_get_user(user_id):
            user_map = {
                "student-id": {
                    "user_id": "student-id",
                    "email": "student@example.com",
                    "name": "Student User",
                    "role": "student",
                    "password_hash": "hashed_password",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                "teacher-id": {
                    "user_id": "teacher-id",
                    "email": "teacher@example.com",
                    "name": "Teacher User",
                    "role": "teacher",
                    "password_hash": "hashed_password",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                "admin-id": {
                    "user_id": "admin-id",
                    "email": "admin@example.com",
                    "name": "Admin User",
                    "role": "admin",
                    "password_hash": "hashed_password",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                "admin2-id": {
                    "user_id": "admin2-id",
                    "email": "admin2@example.com",
                    "name": "Admin User",
                    "role": "admin",
                    "password_hash": "hashed_password",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                "test-user-id": {
                    "user_id": "test-user-id",
                    "email": "test@example.com",
                    "name": "Test User",
                    "role": "student",
                    "password_hash": self.authService.get_password_hash("Password123!"),
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            }
            return user_map.get(user_id, None)
        
        self.mock_user_service.get_user.side_effect = mock_get_user
        
        self.authService.user_service = self.mock_user_service
        
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
        with pytest.raises(ValidationError, match="Password does not meet strength requirements"):
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
        
        # Update mock to return the created user for authentication
        def mock_get_user_by_email_after_creation(email):
            if email == "test@example.com":
                deactivated_user = {
                    "user_id": "test-user-id",
                    "email": "test@example.com",
                    "password_hash": self.authService.get_password_hash("Password123!"),
                    "name": "Test User",
                    "role": "student",
                    "is_active": False,  # deactivated
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "deactivated_at": datetime.now()
                }
                return deactivated_user
            elif email == "admin@example.com":
                return {
                    "user_id": "admin-id",
                    "email": "admin@example.com",
                    "password_hash": "hashed_password",
                    "name": "Admin User",
                    "role": "admin",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            else:
                raise NotFoundError("User not found")
        
        # Update the mock to use the new behavior
        self.mock_user_service.get_user_by_email.side_effect = mock_get_user_by_email_after_creation
        
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
        
        # Update mock to return the updated user for authentication
        def mock_get_user_by_email_after_role_change(email):
            if email == "test@example.com":
                return {
                    "user_id": "test-user-id",
                    "email": "test@example.com",
                    "password_hash": self.authService.get_password_hash("Password123!"),
                    "name": "Test User",
                    "role": "teacher",  # updated role
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            elif email == "admin@example.com":
                return {
                    "user_id": "admin-id",
                    "email": "admin@example.com",
                    "password_hash": "hashed_password",
                    "name": "Admin User",
                    "role": "admin",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            else:
                raise NotFoundError("User not found")
        
        # Update the mock to use the new behavior
        self.mock_user_service.get_user_by_email.side_effect = mock_get_user_by_email_after_role_change
        
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
        
        # Update mock to return the updated user with new password for authentication
        def mock_get_user_by_email_after_password_change(email):
            if email == "test@example.com":
                return {
                    "user_id": "test-user-id",
                    "email": "test@example.com",
                    "password_hash": self.authService.get_password_hash("NewPassword123!"),  # new password
                    "name": "Test User",
                    "role": "student",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            elif email == "admin@example.com":
                return {
                    "user_id": "admin-id",
                    "email": "admin@example.com",
                    "password_hash": "hashed_password",
                    "name": "Admin User",
                    "role": "admin",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            else:
                raise NotFoundError("User not found")
        
        # Update the mock to use the new behavior
        self.mock_user_service.get_user_by_email.side_effect = mock_get_user_by_email_after_password_change
        
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
        
        # Log user activities
        activities = []
        for action in ["login", "view_profile", "update_settings"]:
            activity = self.authService.log_user_activity(
                user_id=user_id,
                action=action,
                ip="127.0.0.1"
            )
            activities.append(activity)
        
        # Verify activities were logged correctly
        assert len(activities) == 3
        for activity in activities:
            assert activity["user_id"] == user_id
            assert activity["ip"] == "127.0.0.1"
            assert activity["action"] in ["login", "view_profile", "update_settings"]
    
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
            email="admin2@example.com",
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
        
        self.authService.change_user_role(
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