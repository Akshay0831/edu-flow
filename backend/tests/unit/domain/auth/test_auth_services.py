"""
Unit tests for authentication domain services

This module contains unit tests for:
- AuthService: Authentication service tests
- PasswordService: Password management service tests

Author: Edu-Flow Team
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock, patch

from src.core.security import AuthService
from src.domain.auth.entities import User, UserRole, Token
from src.domain.auth.services import PasswordService
from src.infrastructure.exceptions import AuthenticationError, ValidationError


class TestAuthService:
    """Test cases for AuthService"""
    
    @pytest.fixture
    def auth_service(self):
        """Create authentication service fixture"""
        return AuthService()
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user fixture"""
        return User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            password_hash="hashed-password",
            role=UserRole.STUDENT,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
    
    def test_create_access_token(self, auth_service, mock_user):
        """Test creating access token"""
        user_data = {
            "sub": mock_user.id,
            "email": mock_user.email,
            "role": mock_user.role.value,
            "user_id": mock_user.id
        }
        token = auth_service.create_access_token(user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        from jose import jwt
        decoded = jwt.decode(token, auth_service.secret_key, algorithms=[auth_service.algorithm])
        assert decoded["sub"] == mock_user.id
        assert decoded["email"] == mock_user.email
        assert decoded["role"] == mock_user.role.value
        assert "exp" in decoded
    
    def test_create_refresh_token(self, auth_service, mock_user):
        """Test creating refresh token"""
        from jose import jwt
        
        user_data = {
            "sub": mock_user.id,
            "email": mock_user.email,
            "role": mock_user.role.value,
            "user_id": mock_user.id
        }
        token = auth_service.create_refresh_token(user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        decoded = jwt.decode(token, auth_service.secret_key, algorithms=[auth_service.algorithm])
        assert decoded["sub"] == mock_user.id
        assert decoded["email"] == mock_user.email
        assert decoded["role"] == mock_user.role.value
        assert decoded["type"] == "refresh"
        assert "exp" in decoded
    
    def test_create_token_pair(self, auth_service, mock_user):
        """Test creating token pair"""
        from jose import jwt
        
        user_data = {
            "sub": mock_user.id,
            "email": mock_user.email,
            "role": mock_user.role.value,
            "user_id": mock_user.id
        }
        token_pair = auth_service.create_token_pair(user_data)
        
        assert isinstance(token_pair, dict)
        assert token_pair["access_token"]
        assert token_pair["refresh_token"]
        
        # Verify both tokens can be decoded
        decoded_access = jwt.decode(token_pair["access_token"], auth_service.secret_key, algorithms=[auth_service.algorithm])
        assert decoded_access["sub"] == mock_user.id
        assert decoded_access["email"] == mock_user.email
        assert decoded_access["role"] == mock_user.role.value
        assert "exp" in decoded_access
        
        decoded_refresh = jwt.decode(token_pair["refresh_token"], auth_service.secret_key, algorithms=[auth_service.algorithm])
        assert decoded_refresh["sub"] == mock_user.id
        assert decoded_refresh["email"] == mock_user.email
        assert decoded_refresh["role"] == mock_user.role.value
        assert decoded_refresh["type"] == "refresh"
        assert "exp" in decoded_refresh
    
    def test_verify_token_valid(self, auth_service, mock_user):
        """Test verifying valid token"""
        from jose import jwt
        
        user_data = {
            "sub": mock_user.id,
            "email": mock_user.email,
            "role": mock_user.role.value,
            "user_id": mock_user.id
        }
        token = auth_service.create_access_token(user_data)
        verified_user = auth_service.verify_token(token)
        
        assert verified_user.sub == mock_user.id
        assert verified_user.email == mock_user.email
        assert verified_user.role == mock_user.role.value
    
    def test_verify_token_invalid(self, auth_service):
        """Test verifying invalid token"""
        with pytest.raises(AuthenticationError):
            auth_service.verify_token("invalid-token")
    
    def test_verify_token_wrong_type(self, auth_service, mock_user):
        """Test verifying token with wrong type"""
        from jose import jwt
        
        user_data = {
            "sub": mock_user.id,
            "email": mock_user.email,
            "role": mock_user.role.value,
            "user_id": mock_user.id
        }
        # Create refresh token and try to verify as access token
        refresh_token = auth_service.create_refresh_token(user_data)
        
        with pytest.raises(AuthenticationError):
            auth_service.verify_token(refresh_token, expected_type="access")
    
    def test_refresh_access_token(self, auth_service, mock_user):
        """Test refreshing access token"""
        from jose import jwt
        
        user_data = {
            "sub": mock_user.id,
            "email": mock_user.email,
            "role": mock_user.role.value,
            "user_id": mock_user.id
        }
        refresh_token = auth_service.create_refresh_token(user_data)
        new_token_pair = auth_service.refresh_access_token(refresh_token)
        
        assert isinstance(new_token_pair, dict)
        assert new_token_pair["access_token"] != refresh_token
        assert new_token_pair["refresh_token"] == refresh_token
        assert new_token_pair["token_type"] == "bearer"
        
        # Verify new access token is valid
        decoded_new = jwt.decode(new_token_pair["access_token"], auth_service.secret_key, algorithms=[auth_service.algorithm])
        assert decoded_new["sub"] == mock_user.id
        assert decoded_new["email"] == mock_user.email
        assert decoded_new["role"] == mock_user.role.value
    
    def test_refresh_access_token_invalid(self, auth_service):
        """Test refreshing with invalid refresh token"""
        with pytest.raises(AuthenticationError):
            auth_service.refresh_access_token("invalid-refresh-token")
    
    def test_refresh_access_token_wrong_type(self, auth_service, mock_user):
        """Test refreshing with wrong token type"""
        from jose import jwt
        
        user_data = {
            "sub": mock_user.id,
            "email": mock_user.email,
            "role": mock_user.role.value,
            "user_id": mock_user.id
        }
        # Create access token and try to use as refresh token
        access_token = auth_service.create_access_token(user_data)
        
        with pytest.raises(AuthenticationError):
            auth_service.refresh_access_token(access_token)


class TestPasswordService:
    """Test cases for PasswordService"""
    
    @pytest.fixture
    def password_service(self):
        """Create password service fixture"""
        return PasswordService()
    
    def test_hash_password(self, password_service):
        """Test password hashing"""
        password = "test-password-123"
        hashed = password_service.hash_password(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password
    
    def test_verify_password_correct(self, password_service):
        """Test verifying correct password"""
        password = "test-password-123"
        hashed = password_service.hash_password(password)
        
        assert password_service.verify_password(password, hashed)
    
    def test_verify_password_incorrect(self, password_service):
        """Test verifying incorrect password"""
        password = "test-password-123"
        wrong_password = "wrong-password-456"
        hashed = password_service.hash_password(password)
        
        assert not password_service.verify_password(wrong_password, hashed)
    
    def test_validate_password_strength_valid(self, password_service):
        """Test validating strong password"""
        password = "StrongPassword123"
        result = password_service.validate_password_strength(password)
        
        assert result["is_valid"]
        assert len(result["errors"]) == 0
    
    def test_validate_password_strength_too_short(self, password_service):
        """Test validating password that's too short"""
        password = "Short1"
        result = password_service.validate_password_strength(password)
        
        assert not result["is_valid"]
        assert len(result["errors"]) > 0
        assert any("at least 8 characters" in error for error in result["errors"])
    
    def test_validate_password_strength_no_uppercase(self, password_service):
        """Test validating password without uppercase"""
        password = "lowercase123"
        result = password_service.validate_password_strength(password)
        
        assert result["is_valid"]  # Still valid but with warnings
        assert len(result["warnings"]) > 0
        assert any("uppercase letter" in warning for warning in result["warnings"])
    
    def test_validate_password_strength_no_lowercase(self, password_service):
        """Test validating password without lowercase"""
        password = "UPPERCASE123"
        result = password_service.validate_password_strength(password)
        
        assert result["is_valid"]  # Still valid but with warnings
        assert len(result["warnings"]) > 0
        assert any("lowercase letter" in warning for warning in result["warnings"])
    
    def test_validate_password_strength_no_digit(self, password_service):
        """Test validating password without digit"""
        password = "NoDigitHere"
        result = password_service.validate_password_strength(password)
        
        assert result["is_valid"]  # Still valid but with warnings
        assert len(result["warnings"]) > 0
        assert any("digit" in warning for warning in result["warnings"])
    
    def test_validate_password_strength_long_password(self, password_service):
        """Test validating very long password"""
        password = "a" * 100  # 100 character password
        result = password_service.validate_password_strength(password)
        
        assert result["is_valid"]  # Still valid but with warnings
        assert len(result["warnings"]) > 0
        assert any("72 characters" in warning for warning in result["warnings"])
    
    @patch('passlib.context.CryptContext.hash')
    def test_password_hashing_fallback(self, mock_hash, password_service):
        """Test password hashing fallback mechanism"""
        # Track calls to simulate the fallback behavior
        call_count = 0
        
        def mock_hash_side_effect(password):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call fails with "72 bytes"
                raise Exception("72 bytes")
            else:
                # Second call succeeds (with truncated password)
                return f"hashed_{password}"
        
        mock_hash.side_effect = mock_hash_side_effect
        
        password = "test-password-123"
        hashed = password_service.hash_password(password)
        
        assert isinstance(hashed, str)
        assert call_count == 2  # Should have been called twice (original + fallback)
        mock_hash.assert_called()  # Should have been called


class TestUserEntity:
    """Test cases for User entity"""
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user fixture"""
        return User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            password_hash="hashed-password",
            role=UserRole.STUDENT,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
    
    def test_user_creation(self, mock_user):
        """Test user creation"""
        assert mock_user.id == "user-123"
        assert mock_user.email == "test@example.com"
        assert mock_user.name == "Test User"
        assert mock_user.role == UserRole.STUDENT
        assert mock_user.is_active == True
        assert mock_user.created_at is not None
    
    def test_user_update_profile(self, mock_user):
        """Test user profile update"""
        mock_user.update_profile(name="Updated Name", phone="123-456-7890")
        
        assert mock_user.name == "Updated Name"
        assert mock_user.phone == "123-456-7890"
        assert mock_user.updated_at > mock_user.created_at
    
    def test_user_change_password(self, mock_user):
        """Test password change"""
        new_password_hash = "new-hashed-password"
        mock_user.change_password(new_password_hash)
        
        assert mock_user.password_hash == new_password_hash
        assert mock_user.updated_at > mock_user.created_at
    
    def test_user_deactivate(self, mock_user):
        """Test user deactivation"""
        mock_user.deactivate()
        
        assert mock_user.is_active == False
        assert mock_user.updated_at > mock_user.created_at
    
    def test_user_activate(self, mock_user):
        """Test user activation"""
        mock_user.is_active = False
        mock_user.activate()
        
        assert mock_user.is_active == True
        assert mock_user.updated_at > mock_user.created_at
    
    def test_user_update_last_login(self, mock_user):
        """Test updating last login"""
        mock_user.update_last_login()
        
        assert mock_user.last_login is not None
        assert mock_user.updated_at > mock_user.created_at
    
    def test_user_has_permission(self, mock_user):
        """Test permission checking"""
        # Student can access student resources
        assert mock_user.has_permission(UserRole.STUDENT)
        
        # Student cannot access admin resources
        assert not mock_user.has_permission(UserRole.ADMIN)
        
        # Teacher can access student and teacher resources
        teacher_user = User(
            id="teacher-123",
            email="teacher@example.com",
            name="Teacher User",
            password_hash="hashed-password",
            role=UserRole.TEACHER,
            is_active=True,
            created_at=datetime.now()
        )
        assert teacher_user.has_permission(UserRole.STUDENT)
        assert teacher_user.has_permission(UserRole.TEACHER)
        assert not teacher_user.has_permission(UserRole.ADMIN)
    
    def test_user_email_validation(self):
        """Test email validation"""
        # Valid email
        user = User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            password_hash="hashed-password",
            role=UserRole.STUDENT,
            is_active=True,
            created_at=datetime.now()
        )
        assert user.email == "test@example.com"
        
        # Invalid email
        with pytest.raises(ValueError):
            User(
                id="user-456",
                email="invalid-email",
                name="Test User 2",
                password_hash="hashed-password",
                role=UserRole.STUDENT,
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
    
    def test_user_name_validation(self):
        """Test name validation"""
        # Valid name
        user = User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            password_hash="hashed-password",
            role=UserRole.STUDENT,
            is_active=True,
            created_at=datetime.now()
        )
        assert user.name == "Test User"
        
        # Empty name
        with pytest.raises(ValueError):
            User(
                id="user-456",
                email="test2@example.com",
                name="",
                password_hash="hashed-password",
                role=UserRole.STUDENT,
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )