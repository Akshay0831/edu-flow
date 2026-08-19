"""
Domain entities for authentication

This module contains the core domain entities for authentication:
- User: User entity with business logic
- Role: User role enumeration
- Token: Token entity for authentication

Author: Edu-Flow Team
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    STAFF = "staff"


class Token(BaseModel):
    """Domain entity for authentication tokens"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_at: datetime = Field(..., description="Token expiration time")
    user_id: str = Field(..., description="Associated user ID")
    email: str = Field(..., description="Associated user email")
    role: UserRole = Field(..., description="User role")
    
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.now(timezone.utc) >= self.expires_at
    
    def can_be_refreshed(self) -> bool:
        """Check if token can be refreshed"""
        return not self.is_expired()


class User(BaseModel):
    """Domain entity for users"""
    id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address", pattern=r'^[^@]+@[^@]+\.[^@]+$')
    name: str = Field(..., description="User full name", min_length=1, max_length=100)
    password_hash: str = Field(..., description="Hashed password")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(True, description="Account status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    department_id: Optional[str] = Field(None, description="Department assignment")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Address")
    emergency_contact: Optional[Dict[str, str]] = Field(None, description="Emergency contact information")
    medical_info: Optional[str] = Field(None, description="Medical information")
    family_info: Optional[Dict[str, Any]] = Field(None, description="Family information")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    
    def update_profile(self, **kwargs) -> None:
        """Update user profile"""
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ['id', 'email', 'password_hash', 'created_at']:
                setattr(self, key, value)
        # Ensure updated_at is timezone-aware to match created_at
        self.updated_at = datetime.now(timezone.utc)
    
    def change_password(self, new_password_hash: str) -> None:
        """Change user password"""
        self.password_hash = new_password_hash
        self.updated_at = datetime.now(timezone.utc)
    
    def deactivate(self) -> None:
        """Deactivate user account"""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
    
    def activate(self) -> None:
        """Activate user account"""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)
    
    def update_last_login(self) -> None:
        """Update last login timestamp"""
        self.last_login = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format"""
        if not v or '@' not in v:
            raise ValueError("Invalid email format")
        return v.lower()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name is not empty"""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
    
    def has_permission(self, required_role: UserRole) -> bool:
        """Check if user has required permission"""
        role_hierarchy = {
            UserRole.ADMIN: 4,
            UserRole.STAFF: 3,
            UserRole.TEACHER: 2,
            UserRole.STUDENT: 1
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)