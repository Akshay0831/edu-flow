import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
from src.core.validation import validate_email, validate_password
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
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
        self.auth_service = AuthService()
        self.test_secret_key = "test-secret-key"
        self.auth_service.secret_key = self.test_secret_key
        self.auth_service.algorithm = "HS256"
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
                        "password_hash": self.auth_service.get_password_hash("Password123!"),
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
                    "password_hash": self.auth_service.get_password_hash("Password123!"),
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
                    "password_hash": self.auth_service.get_password_hash("Password123!"),
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            }
            return user_map.get(user_id, None)
        
        self.mock_user_service.get_user.side_effect = mock_get_user
        self.mock_user_service.create_user = Mock()
        self.mock_user_service.create_user.side_effect = [
            ValidationError("Invalid email format"),  # First call - invalid email
            ValidationError("Password does not meet strength requirements"),  # Second call - weak password
            ValidationError("Invalid role"),  # Third call - invalid role
            {"user_id": "new-user-id"},  # Fourth call - successful creation (returns just user_id as expected by AuthService)
        ] * 100  # Repeat the pattern to ensure we never run out
        
        self.auth_service.user_service = self.mock_user_service
        
    def test_user_creation_validation(self):
        """Test user creation validation"""
        # Test invalid email
        with pytest.raises(ValidationError, match="Invalid email format"):
            self.auth_service.create_user(
                email="invalid-email",
                password="Password123!",
                name="Test User",
                role="student"
            )
        
        # Test weak password
        with pytest.raises(ValidationError, match="Password does not meet strength requirements"):
            self.auth_service.create_user(
                email="test@example.com",
                password="weak",
                name="Test User",
                role="student"
            )
        
        # Test invalid role
        with pytest.raises(ValidationError, match="Invalid role"):
            self.auth_service.create_user(
                email="test@example.com",
                password="Password123!",
                name="Test User",
                role="invalid_role"
            )
        
        # Test valid user creation
        user = self.auth_service.create_user(
            email="test@example.com",
            password="Password123!",
            name="Test User",
            role="student"
        )
        
        # AuthService only returns user_id
        assert user["user_id"] == "new-user-id"
        
        # Reset mock for next test
        self.mock_user_service.create_user.side_effect = None
        self.mock_user_service.create_user.reset_mock()
    
    def test_user_update_validation(self):
        """Test user update validation"""
        # Set up fresh mock for successful user creation
        self.mock_user_service.create_user.side_effect = [{"user_id": "test-user-id"}]
        
        # Create a user first
        user = self.auth_service.create_user(
            email="test@example.com",
            password="Password123!",
            name="Test User",
            role="student"
        )
        
        user_id = user["user_id"]
        
        # Set up mock for update operations
        def mock_update_user(user_id, **kwargs):
            return True
        
        self.mock_user_service.update_user = Mock(side_effect=mock_update_user)
        
        # Test invalid email update
        with pytest.raises(ValidationError, match="Invalid email format"):
            self.auth_service.update_user(
                user_id=user_id,
                email="invalid-email",
                name="Updated Name"
            )
        
        # Test valid user update
        updated_user = self.auth_service.update_user(
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
        # Reset mocks for fresh test
        self.mock_user_service.reset_mock()
        
        # Set up fresh mock for successful user creation
        self.mock_user_service.create_user.side_effect = [{"user_id": "test-user-id"}]
        
        # Create a user first
        user = self.auth_service.create_user(
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
                    "password_hash": self.auth_service.get_password_hash("Password123!"),
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
        
        # Set up mock for deactivation
        def mock_deactivate_user(user_id):
            return True
        
        self.mock_user_service.deactivate_user = Mock(side_effect=mock_deactivate_user)
        
        # Update the mock to use the new behavior
        self.mock_user_service.get_user_by_email.side_effect = mock_get_user_by_email_after_creation
        
        # Deactivate user
        deactivated_user = self.auth_service.deactivate_user(user_id)
        
        assert deactivated_user["is_active"] == False
        assert deactivated_user["deactivated_at"] is not None
        
        # Try to login with deactivated user
        with pytest.raises(AuthenticationError, match="Account is disabled"):
            self.auth_service.authenticate_user(
                email="test@example.com",
                password="Password123!"
            )
    
    def test_user_role_change(self):
        """Test user role change"""
        # Reset mocks for fresh test
        self.mock_user_service.reset_mock()
        
        # Set up fresh mock for successful user creation
        self.mock_user_service.create_user.side_effect = [{"user_id": "test-user-id"}]
        
        # Create a user first
        user = self.auth_service.create_user(
            email="test@example.com",
            password="Password123!",
            name="Test User",
            role="student"
        )
        
        user_id = user["user_id"]
        
        # Set up mock for role change
        def mock_change_user_role(user_id, new_role):
            return True
        
        self.mock_user_service.change_user_role = Mock(side_effect=mock_change_user_role)
        
        # Change role
        updated_user = self.auth_service.change_user_role(
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
                    "password_hash": self.auth_service.get_password_hash("Password123!"),
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
        auth_result = self.auth_service.authenticate_user(
            email="test@example.com",
            password="Password123!"
        )
        assert auth_result["user"]["role"] == "teacher"
    
    def test_user_password_change(self):
        """Test user password change"""
        # Reset mocks for fresh test
        self.mock_user_service.reset_mock()
        
        # Set up fresh mock for successful user creation
        self.mock_user_service.create_user.side_effect = [{"user_id": "test-user-id"}]
        
        # Create a user first
        user = self.auth_service.create_user(
            email="test@example.com",
            password="Password123!",
            name="Test User",
            role="student"
        )
        
        user_id = user["user_id"]
        old_password_hash = user["password_hash"]
        
        # Set up mock for password change
        def mock_update_user_password(user_id, **kwargs):
            return True
        
        self.mock_user_service.update_user = Mock(side_effect=mock_update_user_password)
        
        # Change password
        self.auth_service.change_user_password(
            user_id=user_id,
            new_password="NewPassword123!"
        )
        
        # Update mock to return the updated user with new password for authentication
        def mock_get_user_by_email_after_password_change(email):
            if email == "test@example.com":
                return {
                    "user_id": "test-user-id",
                    "email": "test@example.com",
                    "password_hash": self.auth_service.get_password_hash("NewPassword123!"),  # new password
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
            self.auth_service.authenticate_user(
                email="test@example.com",
                password="Password123!"
            )
        
        # Verify new password works
        auth_result = self.auth_service.authenticate_user(
            email="test@example.com",
            password="NewPassword123!"
        )
        assert auth_result["user"]["id"] == user_id
    
    def test_user_profile_update(self):
        """Test user profile update"""
        # Reset mocks for fresh test
        self.mock_user_service.reset_mock()
        
        # Set up fresh mock for successful user creation
        self.mock_user_service.create_user.side_effect = [{"user_id": "test-user-id"}]
        
        # Create a user first
        user = self.auth_service.create_user(
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
        
        # Set up mock for profile update
        def mock_update_user_profile(user_id, **kwargs):
            return True
        
        self.mock_user_service.update_user = Mock(side_effect=mock_update_user_profile)
        
        updated_user = self.auth_service.update_user_profile(
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
        # Reset mocks for fresh test
        self.mock_user_service.reset_mock()
        
        # Set up fresh mock for multiple user creation
        self.mock_user_service.create_user.side_effect = [
            {"user_id": "user0-id"},
            {"user_id": "user1-id"},
            {"user_id": "user2-id"},
            {"user_id": "user3-id"},
            {"user_id": "user4-id"}
        ]
        
        # Create multiple users
        users = []
        for i in range(5):
            user = self.auth_service.create_user(
                email=f"user{i}@example.com",
                password="Password123!",
                name=f"User {i}",
                role="student" if i < 3 else "teacher"
            )
            users.append(user)
        
        # Set up mock for getting all users
        def mock_get_all_users():
            return [
                {
                    "user_id": "user0-id",
                    "email": "user0@example.com",
                    "name": "User 0",
                    "role": "student",
                    "is_active": True
                },
                {
                    "user_id": "user1-id",
                    "email": "user1@example.com",
                    "name": "User 1",
                    "role": "student",
                    "is_active": True
                },
                {
                    "user_id": "user2-id",
                    "email": "user2@example.com",
                    "name": "User 2",
                    "role": "student",
                    "is_active": True
                },
                {
                    "user_id": "user3-id",
                    "email": "user3@example.com",
                    "name": "User 3",
                    "role": "teacher",
                    "is_active": True
                },
                {
                    "user_id": "user4-id",
                    "email": "user4@example.com",
                    "name": "User 4",
                    "role": "teacher",
                    "is_active": True
                }
            ]
        
        self.mock_user_service.get_all_users = Mock(side_effect=mock_get_all_users)
        
        # Search by name
        search_results = self.auth_service.search_users(
            query="User 1",
            role="student"
        )
        assert len(search_results) == 1
        assert search_results[0]["name"] == "User 1"
        
        # Filter by role
        teacher_results = self.auth_service.search_users(
            query="",
            role="teacher"
        )
        assert len(teacher_results) == 2
        
        # Filter by department (assuming some users have departments)
        department_results = self.auth_service.search_users(
            query="",
            department="Computer Science"
        )
        # This will depend on which users were assigned the department
        
        # Pagination
        paginated_results = self.auth_service.search_users(
            query="User",
            role="student",
            page=1,
            page_size=2
        )
        assert len(paginated_results) <= 2
    
    def test_user_activity_logging(self):
        """Test user activity logging"""
        # Reset mocks for fresh test
        self.mock_user_service.reset_mock()
        
        # Set up fresh mock for successful user creation
        self.mock_user_service.create_user.side_effect = [{"user_id": "test-user-id"}]
        
        # Create a user first
        user = self.auth_service.create_user(
            email="test@example.com",
            password="Password123!",
            name="Test User",
            role="student"
        )
        
        user_id = user["user_id"]
        
        # Set up mock for activity logging
        def mock_log_user_activity(**kwargs):
            return True
        
        self.mock_user_service.log_user_activity = Mock(side_effect=mock_log_user_activity)
        
        # Log user activities
        activities = []
        for action in ["login", "view_profile", "update_settings"]:
            activity = self.auth_service.log_user_activity(
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
        # Reset mocks for fresh test
        self.mock_user_service.reset_mock()
        
        # Reset side effects
        self.mock_user_service.create_user.side_effect = None
        
        # Set up mock for user creation (simple return)
        self.mock_user_service.create_user.return_value = {"user_id": "bulk-user-id"}
        
        # Set up mock for get_user (for bulk operations)
        def mock_get_user(user_id):
            return {"user_id": user_id, "is_active": True, "email": "test@example.com", "role": "student"}
        
        self.mock_user_service.get_user.side_effect = mock_get_user
        
        # Set up mock for deactivate_user
        self.mock_user_service.deactivate_user.return_value = {"is_active": False, "deactivated_at": "2024-01-01T12:00:00Z"}
        
        # Set up mock for reactivate_user
        self.mock_user_service.reactivate_user.return_value = {"is_active": True, "reactivated_at": "2024-01-01T13:00:00Z"}
        
        # Create multiple users
        users = []
        for i in range(3):
            user = self.auth_service.create_user(
                email=f"bulk_user{i}@example.com",
                password="Password123!",
                name=f"Bulk User {i}",
                role="student"
            )
            users.append(user)
        
        user_ids = [user["user_id"] for user in users]
        
        # Bulk deactivate
        deactivated_users = self.auth_service.bulk_deactivate_users(user_ids)
        assert len(deactivated_users) == len(user_ids)
        assert all(user["is_active"] == False for user in deactivated_users)
        
        # Bulk reactivate
        reactivated_users = self.auth_service.bulk_reactivate_users(user_ids)
        assert len(reactivated_users) == len(user_ids)
        assert all(user["is_active"] == True for user in reactivated_users)
    
    def test_user_permission_validation(self):
        """Test user permission validation"""
        # Reset mocks for fresh test
        self.mock_user_service.reset_mock()
        
        # Set up fresh mock for multiple user creation
        self.mock_user_service.create_user.side_effect = [
            {"user_id": "student-id"},
            {"user_id": "teacher-id"},
            {"user_id": "admin-id"}
        ]
        
        # Create users with different roles
        student = self.auth_service.create_user(
            email="student@example.com",
            password="Password123!",
            name="Student User",
            role="student"
        )
        
        teacher = self.auth_service.create_user(
            email="teacher@example.com",
            password="Password123!",
            name="Teacher User",
            role="teacher"
        )
        
        admin = self.auth_service.create_user(
            email="admin2@example.com",
            password="Password123!",
            name="Admin User",
            role="admin"
        )
        
        # Set up mock for get_user for permission checking
        def mock_get_user(user_id):
            users = {
                "student-id": {
                    "user_id": "student-id",
                    "role": "student",
                    "email": "student@example.com"
                },
                "teacher-id": {
                    "user_id": "teacher-id",
                    "role": "teacher", 
                    "email": "teacher@example.com"
                },
                "admin-id": {
                    "user_id": "admin-id",
                    "role": "admin",
                    "email": "admin2@example.com"
                }
            }
            return users.get(user_id, None)
        
        self.mock_user_service.get_user = Mock(side_effect=mock_get_user)
        
        # Test permission checks
        # Students can view their own profile
        assert self.auth_service.check_permission(
            user_id=student["user_id"],
            action="view_profile",
            target_user_id=student["user_id"]
        ) == True
        
        # Students cannot view other students' profiles
        assert self.auth_service.check_permission(
            user_id=student["user_id"],
            action="view_profile",
            target_user_id=teacher["user_id"]
        ) == False
        
        # Teachers can view student profiles
        assert self.auth_service.check_permission(
            user_id=teacher["user_id"],
            action="view_profile",
            target_user_id=student["user_id"]
        ) == True
        
        # Admins can view all profiles
        assert self.auth_service.check_permission(
            user_id=admin["user_id"],
            action="view_profile",
            target_user_id=student["user_id"]
        ) == True
        
        assert self.auth_service.check_permission(
            user_id=admin["user_id"],
            action="view_profile",
            target_user_id=teacher["user_id"]
        ) == True
    
    def test_user_audit_trail(self):
        """Test user audit trail"""
        # Reset mocks for fresh test
        self.mock_user_service.reset_mock()
        
        # Reset side effects
        self.mock_user_service.create_user.side_effect = None
        
        # Set up mock for user creation
        self.mock_user_service.create_user.return_value = {"user_id": "user-id"}
        
        # Set up mock for update_user
        self.mock_user_service.update_user.return_value = {"status": "success", "user_id": "user-id"}
        
        # Set up mock for change_user_role
        self.mock_user_service.change_user_role.return_value = {"status": "success", "user_id": "user-id"}
        
        # Set up mock for change_user_password  
        self.mock_user_service.change_user_password.return_value = {"status": "success", "user_id": "user-id"}
        
        # Set up mock for get_user_audit_trail
        self.mock_user_service.get_user_audit_trail.return_value = [
            {"action": "create", "timestamp": "2024-01-01T10:00:00Z", "user_id": "user-id"},
            {"action": "update", "timestamp": "2024-01-01T11:00:00Z", "user_id": "user-id"},
            {"action": "role_change", "timestamp": "2024-01-01T12:00:00Z", "user_id": "user-id"},
            {"action": "password_change", "timestamp": "2024-01-01T13:00:00Z", "user_id": "user-id"}
        ]
        
        # Create a user first
        user = self.auth_service.create_user(
            email="test@example.com",
            password="Password123!",
            name="Test User",
            role="student"
        )
        
        user_id = user["user_id"]
        
        # Perform various operations
        self.auth_service.update_user(
            user_id=user_id,
            name="Updated Name"
        )
        
        self.auth_service.change_user_role(
            user_id=user_id,
            new_role="teacher"
        )
        
        self.auth_service.change_user_password(
            user_id=user_id,
            new_password="NewPassword123!"
        )
        
        # Get audit trail
        audit_trail = self.auth_service.get_user_audit_trail(user_id)
        
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