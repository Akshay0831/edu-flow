"""Authentication service for FastAPI."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, field_validator
from fastapi import HTTPException, status
from src.core.exceptions import ValidationError, NotFoundError, AuthenticationError


class AuthService:
    """Authentication service."""
    
    def __init__(self, secret_key: str = "your-secret-key", algorithm: str = "HS256"):
        """Initialize auth service."""
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password."""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception:
            # Fallback to simple hash if bcrypt fails
            import hashlib
            return hashlib.sha256((plain_password + "salt").encode()).hexdigest() == hashed_password
    
    def get_password_hash(self, password: str) -> str:
        """Get password hash."""
        try:
            return self.pwd_context.hash(password)
        except Exception:
            # Fallback to simple hash if bcrypt fails
            import hashlib
            return hashlib.sha256((password + "salt").encode()).hexdigest()
    
    def create_access_token(self, data: dict, expires_delta: Optional[datetime] = None) -> str:
        """Create access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_token(self, token: str) -> dict:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise AuthenticationError("Invalid token")
    
    def create_user(self, email: str, password: str, name: str, role: str = "student") -> dict:
        """Create a new user."""
        # Validate email
        if not EmailStr.validate(email):
            raise ValidationError("Invalid email format")
        
        # Validate password strength
        self._validate_password(password)
        
        # Validate role
        valid_roles = ['student', 'teacher', 'admin', 'staff']
        if role not in valid_roles:
            raise ValidationError(f'Invalid role. Must be one of: {valid_roles}')
        
        # Check if user already exists
        if self.get_user_by_email(email):
            raise ValidationError("User with this email already exists")
        
        # Create user
        from uuid import uuid4
        user_id = str(uuid4())
        user = {
            "user_id": user_id,
            "email": email,
            "password_hash": self.get_password_hash(password),
            "name": name,
            "role": role,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Mock database storage
        self._store_user(user)
        
        return user
    
    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email."""
        # Mock database lookup
        if email == "admin@example.com":
            return {
                "user_id": "admin-id",
                "email": "admin@example.com",
                "password_hash": self.get_password_hash("admin123"),
                "name": "Admin User",
                "role": "admin",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID."""
        # Mock database lookup
        if user_id == "admin-id":
            return {
                "user_id": "admin-id",
                "email": "admin@example.com",
                "password_hash": self.get_password_hash("admin123"),
                "name": "Admin User",
                "role": "admin",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        return None
    
    def update_user(self, user_id: str, **kwargs) -> dict:
        """Update user."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Validate email if provided
        if 'email' in kwargs and kwargs['email']:
            if not EmailStr.validate(kwargs['email']):
                raise ValidationError("Invalid email format")
            
            # Check if email already exists
            existing_user = self.get_user_by_email(kwargs['email'])
            if existing_user and existing_user['user_id'] != user_id:
                raise ValidationError("User with this email already exists")
        
        # Update user
        for key, value in kwargs.items():
            if key in ['email', 'name', 'role', 'department', 'bio', 'phone', 'preferences']:
                user[key] = value
        
        user['updated_at'] = datetime.utcnow()
        return user
    
    def deactivate_user(self, user_id: str) -> dict:
        """Deactivate user."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        user['is_active'] = False
        user['updated_at'] = datetime.utcnow()
        return user
    
    def change_user_role(self, user_id: str, new_role: str) -> dict:
        """Change user role."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Validate role
        valid_roles = ['student', 'teacher', 'admin', 'staff']
        if new_role not in valid_roles:
            raise ValidationError(f'Invalid role. Must be one of: {valid_roles}')
        
        user['role'] = new_role
        user['updated_at'] = datetime.utcnow()
        return user
    
    def update_user_profile(self, user_id: str, **kwargs) -> dict:
        """Update user profile."""
        return self.update_user(user_id, **kwargs)
    
    def change_user_password(self, user_id: str, old_password: str, new_password: str) -> dict:
        """Change user password."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Verify old password
        if not self.verify_password(old_password, user['password_hash']):
            raise ValidationError("Invalid old password")
        
        # Validate new password
        self._validate_password(new_password)
        
        # Update password
        user['password_hash'] = self.get_password_hash(new_password)
        user['updated_at'] = datetime.utcnow()
        return user
    
    def search_users(self, query: str, role: Optional[str] = None) -> List[dict]:
        """Search users."""
        # Mock search results
        users = []
        if query.lower() in "admin user".lower() and (not role or role == "admin"):
            users.append({
                "user_id": "admin-id",
                "email": "admin@example.com",
                "name": "Admin User",
                "role": "admin",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
        return users
    
    def log_user_activity(self, user_id: str, action: str, ip: str = None) -> dict:
        """Log user activity."""
        from uuid import uuid4
        return {
            "activity_id": str(uuid4()),
            "user_id": user_id,
            "action": action,
            "ip": ip or "127.0.0.1",
            "timestamp": datetime.utcnow(),
            "status": "logged"
        }
    
    def bulk_deactivate_users(self, user_ids: List[str]) -> List[dict]:
        """Bulk deactivate users."""
        deactivated_users = []
        for user_id in user_ids:
            try:
                deactivated_user = self.deactivate_user(user_id)
                deactivated_users.append(deactivated_user)
            except NotFoundError:
                continue
        return deactivated_users
    
    def check_permission(self, user_id: str, action: str, target_user_id: str = None) -> bool:
        """Check user permission."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Simple permission logic
        if action == "view_profile":
            return True  # Users can view their own profile
        elif action == "manage_users" and user["role"] == "admin":
            return True
        elif action == "manage_students" and user["role"] in ["admin", "teacher"]:
            return True
        
        return False
    
    def get_user_audit_trail(self, user_id: str) -> List[dict]:
        """Get user audit trail."""
        return [
            {
                "activity_id": "activity-1",
                "user_id": user_id,
                "action": "login",
                "ip": "127.0.0.1",
                "timestamp": datetime.utcnow(),
                "status": "completed"
            },
            {
                "activity_id": "activity-2",
                "user_id": user_id,
                "action": "update_profile",
                "ip": "127.0.0.1",
                "timestamp": datetime.utcnow(),
                "status": "completed"
            }
        ]
    
    def authenticate_user(self, username: str, password: str) -> dict:
        """Authenticate user."""
        user = self.get_user_by_email(username)
        if not user or not self.verify_password(password, user['password_hash']):
            raise AuthenticationError("Invalid credentials")
        
        if not user['is_active']:
            raise AuthenticationError("User account is deactivated")
        
        return user
    
    def refresh_token(self, token: str) -> str:
        """Refresh token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if not user_id:
                raise JWTError("Invalid token")
            
            # Create new token
            new_token = self.create_access_token(data={"sub": user_id})
            return new_token
        except JWTError:
            raise AuthenticationError("Invalid token")
    
    def _validate_password(self, password: str):
        """Validate password strength."""
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in password):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in password):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in password):
            raise ValidationError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
            raise ValidationError('Password must contain at least one special character')
    
    def _store_user(self, user: dict):
        """Mock user storage."""
        pass
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """Get user permissions."""
        user = self.get_user_by_id(user_id)
        if not user:
            return []
        
        permissions = {
            "student": ["view_profile", "view_courses", "enroll_in_courses", "view_grades"],
            "teacher": ["view_profile", "view_courses", "create_courses", "manage_students", "view_grades"],
            "admin": ["view_profile", "view_courses", "create_courses", "manage_users", "manage_students", "manage_grades"],
            "staff": ["view_profile", "view_courses", "manage_courses"]
        }
        
        return permissions.get(user["role"], [])