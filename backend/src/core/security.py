"""
Security module for Edu-Flow Backend

This module provides authentication, authorization, and security utilities:
- JWT token generation and verification
- Password hashing and validation
- Session management
- Security middleware
- Multi-provider authentication support (Firebase, JWT, Custom Auth)

Author: Edu-Flow Team
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Union
import hashlib
import re
from abc import ABC, abstractmethod
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from core.validation import validate_email
from core.exceptions import ValidationError as CustomValidationError
from .auth_gateway import AuthProvider, auth_gateway

try:
    import bcrypt
except ImportError:
    bcrypt = None

from .exceptions import AuthenticationError, AuthorizationError, ValidationError, NotFoundError
from .config.settings import settings

# Mock imports for models if not available
try:
    from models.user import User
    from models.student import Student
except ImportError:
    User = None
    Student = None

# Password context for hashing with fallback
pwd_context = CryptContext(schemes=["sha256_crypt", "bcrypt"], deprecated="auto")

# Security configuration
class SecurityConfig:
    """Security configuration for the API"""
    
    # OAuth2 configuration
    OAUTH2_CONFIG = {
        "clientId": "default-client-id",
        "clientSecret": "default-client-secret",
        "authUrl": "http://localhost:8000/auth",
        "tokenUrl": "http://localhost:8000/token",
        "scopes": ["openid", "profile", "email"]
    }
    
    # JWT configuration
    SECRET_KEY = settings.security.secret_key
    ALGORITHM = settings.security.algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.security.access_token_expire_minutes or 30
    REFRESH_TOKEN_EXPIRE_DAYS = settings.security.refresh_token_expire_days or 7

# Token data model
class TokenData(BaseModel):
    sub: str
    email: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None
    type: Optional[str] = None
    provider: Optional[str] = None

class AuthService:
    """Enhanced authentication service using the authentication gateway"""
    
    def __init__(self, user_service=None):
        self.pwd_context = pwd_context
        self.user_service = user_service
        self.auth_gateway = auth_gateway
        self.secret_key = settings.security.secret_key
        self.algorithm = settings.security.algorithm
        self.access_token_expire_minutes = settings.security.access_token_expire_minutes
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access", "provider": AuthProvider.JWT})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        # Refresh tokens typically last much longer
        expire = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days
        
        to_encode.update({"exp": expire, "type": "refresh", "provider": AuthProvider.JWT})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    async def authenticate_user(self, credentials: Dict[str, Any], provider: str = None) -> Dict[str, Any]:
        """Authenticate user with specified provider"""
        return await self.auth_gateway.authenticate(credentials, provider)
    
    async def verify_token(self, token: str, provider: str = None) -> Dict[str, Any]:
        """Verify token using specified provider"""
        return await self.auth_gateway.verify_token(token, provider)
    
    async def authenticate_with_fallback(self, credentials: Dict[str, Any], preferred_provider: str = None) -> Dict[str, Any]:
        """Authenticate with fallback mechanism"""
        try:
            # Try preferred provider first
            if preferred_provider:
                return await self.auth_gateway.authenticate(credentials, preferred_provider)
        except Exception:
            pass  # Fall through to default provider
        
        # Fall back to default provider
        return await self.auth_gateway.authenticate(credentials)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token"""
        try:
            # Decode the refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify it's a refresh token
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid refresh token")
            
            # Create new token data from refresh token payload
            user_data = {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role"),
                "user_id": payload.get("sub")
            }
            
            # Create new access token
            new_access_token = self.create_access_token(user_data)
            
            return {
                "access_token": new_access_token,
                "refresh_token": refresh_token,  # Return original refresh token
                "token_type": "bearer"
            }
        except JWTError:
            raise AuthenticationError("Invalid refresh token")
    
    def verify_token(self, token: str, expected_type: str = None) -> TokenData:
        """Verify JWT token and return decoded data"""
        if not token:
            raise AuthenticationError("Could not validate credentials")
            
        credentials_exception = AuthenticationError("Could not validate credentials")
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("email")
            user_id: str = payload.get("sub")
            role: str = payload.get("role")
            exp: int = payload.get("exp")
            token_type: str = payload.get("type")
            
            if user_id is None:
                raise credentials_exception
            
            # Validate token type if expected
            if expected_type and token_type != expected_type:
                if expected_type == "access" and token_type == "refresh":
                    raise AuthenticationError("Invalid token type - expected access token")
                elif expected_type == "refresh" and token_type == "access":
                    raise AuthenticationError("Invalid token type - expected refresh token")
                else:
                    raise AuthenticationError(f"Invalid token type - expected {expected_type}")
                
            token_data = TokenData(
                sub=user_id,
                email=email,
                role=role,
                exp=datetime.fromtimestamp(exp) if exp else None,
                type=token_type
            )
        except JWTError:
            raise credentials_exception
            
        return token_data
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        if not hashed_password or not hashed_password.strip():
            return False
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        if not password:
            # Generate hash for empty string instead of None
            password = ""
        
        try:
            # Try bcrypt first
            return self.pwd_context.hash(password)
        except Exception as e:
            # Fallback to SHA-256 if bcrypt fails and is available
            if bcrypt:
                if "72 bytes" in str(e):
                    # Truncate password for bcrypt compatibility
                    truncated_password = password[:72]
                    return self.pwd_context.hash(truncated_password)
                else:
                    # Try bcrypt with different settings
                    return self.pwd_context.hash(password)
            else:
                # If bcrypt is not available, use SHA-256
                return hashlib.sha256(password.encode()).hexdigest()
    
    async def authenticate_user(self, email: str, password: str, user_service=None) -> Dict[str, Any]:
        """Authenticate user with email and password"""
        # Use provided user_service or fall back to attached user_service
        if user_service is None:
            user_service = self.user_service
            if user_service is None:
                raise AuthenticationError("User service not available")
        
        user = await user_service.get_user_by_email(email)
        if not user:
            raise AuthenticationError("Invalid credentials")
        
        # Check if account is deactivated
        if not user.get("is_active", True):
            raise AuthenticationError("Account is disabled")
        
        if not self.verify_password(password, user["password_hash"]):
            raise AuthenticationError("Invalid credentials")
        
        # Create access token
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": user["user_id"], "email": user["email"], "role": user.get("role", "student")},
            expires_delta=access_token_expires
        )
        
        # Create refresh token
        refresh_token = self.create_refresh_token(
            data={"sub": user["user_id"], "email": user["email"], "role": user.get("role", "student")}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user["user_id"],
                "email": user["email"],
                "role": user.get("role", "student"),
                "name": user.get("name", "")
            }
        }
    
    async def login_user(self, login_data: Dict[str, str]) -> Dict[str, Any]:
        """Login user and return tokens"""
        return await self.authenticate_user(
            email=login_data["email"],
            password=login_data["password"],
            user_service=self.user_service
        )
    
    async def create_user(self, user_data: Dict[str, Any], provider: str = None, user_service=None) -> Dict[str, Any]:
        """Create a new user"""
        try:
            print(f"DEBUG: create_user called with user_data={user_data}, provider={provider}, user_service={user_service}")
            email = user_data.get("email")
            password = user_data.get("password")
            name = user_data.get("name")
            role = user_data.get("role", "student")
            
            # Use provided user_service or the one in auth_service
            if user_service is None:
                user_service = self.user_service
                print(f"DEBUG: Using self.user_service={user_service} (type: {type(user_service)})")
                if user_service is None:
                    raise AuthenticationError("User service not available")
            
            # Create user using the service method (user service will handle password hashing)
            user_result = await user_service.create_user(
                {
                    "email": email,
                    "password": password,
                    "name": name,
                    "role": role,
                }
            )
            
            # Extract the actual user_id from the result
            user_id = user_result.get("user_id", str(user_result.get("id", "default_user_id")))
            
            return {
                "user_id": str(user_id),
                "email": email,
                "name": name,
                "role": role
            }
        except CustomValidationError as e:
            raise e  # Re-raise ValidationError to be caught by API endpoint
    
    def update_user(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Update user information"""
        try:
            # Use provided user_service or the one in auth_service
            if self.user_service is None:
                raise AuthenticationError("User service not available")
            
            # Validate email if provided
            if "email" in kwargs:
                validate_email(kwargs["email"])
            
            # Validate name if provided
            if "name" in kwargs and not kwargs["name"].strip():
                raise CustomValidationError("Name cannot be empty")
            
            # Update user using the service method
            updated_result = self.user_service.update_user(user_id, **kwargs)
            
            # Convert boolean result to consistent format with updated data
            if updated_result is True:
                # Return a consistent format with the updated values
                result_data = {"success": True}
                for key, value in kwargs.items():
                    result_data[key] = value
                return result_data
            
            return updated_result
        except CustomValidationError as e:
            raise e  # Re-raise ValidationError to be caught by API endpoint
    
    def deactivate_user(self, user_id: str) -> Dict[str, Any]:
        """Deactivate a user account"""
        try:
            # Use provided user_service or the one in auth_service
            if self.user_service is None:
                raise AuthenticationError("User service not available")
            
            # Deactivate user using the service method
            deactivated_result = self.user_service.deactivate_user(user_id)
            
            # Handle boolean return by creating response data
            if deactivated_result is True:
                return {
                    "is_active": False,
                    "deactivated_at": datetime.now()
                }
            
            return deactivated_result
        except CustomValidationError as e:
            raise e  # Re-raise ValidationError to be caught by API endpoint
    
    def bulk_deactivate_users(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """Bulk deactivate multiple user accounts"""
        try:
            # Use provided user_service or the one in auth_service
            if self.user_service is None:
                raise AuthenticationError("User service not available")
            
            # Validate all user IDs
            valid_user_ids = []
            for user_id in user_ids:
                try:
                    # Check if user exists
                    user = self.user_service.get_user(user_id)
                    if user:
                        valid_user_ids.append(user_id)
                    else:
                        # Skip non-existent users but continue with others
                        continue
                except:
                    # Skip users that can't be retrieved but continue with others
                    continue
            
            # Deactivate all valid users
            deactivated_users = []
            for user_id in valid_user_ids:
                try:
                    result = self.deactivate_user(user_id)
                    deactivated_users.append(result)
                except Exception:
                    # Skip users that can't be deactivated but continue with others
                    continue
            
            return deactivated_users
        except CustomValidationError as e:
            raise e  # Re-raise ValidationError to be caught by API endpoint
    
    def bulk_reactivate_users(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """Bulk reactivate multiple user accounts"""
        try:
            # Use provided user_service or the one in auth_service
            if self.user_service is None:
                raise AuthenticationError("User service not available")
            
            # Validate all user IDs
            valid_user_ids = []
            for user_id in user_ids:
                try:
                    # Check if user exists
                    user = self.user_service.get_user(user_id)
                    if user:
                        valid_user_ids.append(user_id)
                    else:
                        # Skip non-existent users but continue with others
                        continue
                except:
                    # Skip users that can't be retrieved but continue with others
                    continue
            
            # Reactivate all valid users (assuming service has reactivate method)
            reactivated_users = []
            for user_id in valid_user_ids:
                try:
                    # For now, we'll assume there's a reactivate_user method
                    # or we'll simulate it by updating the user record
                    result = self.user_service.reactivate_user(user_id)
                    reactivated_users.append(result)
                except Exception:
                    # Skip users that can't be reactivated but continue with others
                    continue
            
            return reactivated_users
        except CustomValidationError as e:
            raise e  # Re-raise ValidationError to be caught by API endpoint
    
    def change_user_role(self, user_id: str, new_role: str) -> Dict[str, Any]:
        """Change user role"""
        try:
            # Use provided user_service or the one in auth_service
            if self.user_service is None:
                raise AuthenticationError("User service not available")
            
            # Validate role
            valid_roles = ["student", "teacher", "admin"]
            if new_role not in valid_roles:
                raise CustomValidationError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
            
            # Change user role using the service method
            updated_result = self.user_service.change_user_role(user_id, new_role)
            
            # Handle boolean return by creating response data
            if updated_result is True:
                return {
                    "role": new_role
                }
            
            return updated_result
        except CustomValidationError as e:
            raise e  # Re-raise ValidationError to be caught by API endpoint
    
    def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if it's a refresh token
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid refresh token")
            
            # Create new access token with current timestamp to ensure uniqueness
            from datetime import datetime
            access_token = self.create_access_token(
                data={
                    "sub": payload.get("sub"), 
                    "email": payload.get("email"), 
                    "role": payload.get("role"),
                    "iat": int(datetime.utcnow().timestamp())  # Include issued at timestamp
                }
            )
            
            # Create new refresh token with current timestamp to ensure uniqueness
            from datetime import datetime
            new_refresh_token = self.create_refresh_token(
                data={
                    "sub": payload.get("sub"), 
                    "email": payload.get("email"), 
                    "role": payload.get("role"),
                    "iat": int(datetime.utcnow().timestamp())  # Include issued at timestamp
                }
            )
            
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,  # Generate new refresh token
                "token_type": "bearer",
                "expires_in": 30 * 60  # 30 minutes in seconds
            }
        except JWTError:
            raise AuthenticationError("Invalid refresh token")
    
    def logout_user(self, token: str) -> bool:
        """
        Logout user (JWT is stateless, so this is mostly for future session management)
        
        - **token**: User access token
        
        Returns success status
        """
        # JWT is stateless, so we can't invalidate tokens directly
        # This method can be enhanced later with token blacklisting
        return True
    
    def change_user_password(self, user_id: str, new_password: str) -> bool:
        """Change user password without requiring current password"""
        try:
            # Use provided user_service or the one in auth_service
            if self.user_service is None:
                raise AuthenticationError("User service not available")
            
            # Validate new password strength
            if not self.validate_password_strength(new_password):
                raise CustomValidationError("Password does not meet strength requirements")
            
            # Hash new password
            hashed_password = self.get_password_hash(new_password)
            
            # Update user password using the service method
            result = self.user_service.update_user(user_id, password_hash=hashed_password)
            
            return result is True or result
        except CustomValidationError as e:
            raise e  # Re-raise ValidationError to be caught by API endpoint
    
    def update_user_profile(self, user_id: str, **profile_data) -> Dict[str, Any]:
        """Update user profile information"""
        try:
            # Use provided user_service or the one in auth_service
            if self.user_service is None:
                raise AuthenticationError("User service not available")
            
            # Validate profile data
            if "name" in profile_data and not profile_data["name"].strip():
                raise CustomValidationError("Name cannot be empty")
            
            # Extract password if present (should be handled separately)
            password_hash = None
            if "password" in profile_data:
                password_hash = self.get_password_hash(profile_data.pop("password"))
            
            # Update user using the service method
            if password_hash:
                result = self.user_service.update_user(user_id, password_hash=password_hash, **profile_data)
            else:
                result = self.user_service.update_user(user_id, **profile_data)
            
            # Handle boolean return by creating response data
            if result is True:
                response_data = {"success": True}
                response_data.update(profile_data)
                return response_data
            
            return result
        except CustomValidationError as e:
            raise e  # Re-raise ValidationError to be caught by API endpoint
    
    def search_users(self, query: str = None, role: str = None, department: str = None, is_active: bool = None, page: int = None, page_size: int = None) -> List[Dict[str, Any]]:
        """Search and filter users"""
        try:
            # Use provided user_service or the one in auth_service
            if self.user_service is None:
                raise AuthenticationError("User service not available")
            
            # Get all users first
            all_users = []
            # Assuming there's a method to get all users, if not, we'll need to mock or create one
            if hasattr(self.user_service, 'get_all_users'):
                all_users = self.user_service.get_all_users()
            else:
                # Fallback: get users one by one or handle differently
                # For now, return empty list or handle appropriately
                return []
            
            # Filter users based on criteria
            filtered_users = []
            for user in all_users:
                # Check query filter (search in name or email)
                if query:
                    query_lower = query.lower()
                    name_match = user.get("name", "").lower().find(query_lower) != -1
                    email_match = user.get("email", "").lower().find(query_lower) != -1
                    if not (name_match or email_match):
                        continue
                
                # Check role filter
                if role and user.get("role") != role:
                    continue
                
                # Check department filter
                if department and user.get("department") != department:
                    continue
                
                # Check active status filter
                if is_active is not None and user.get("is_active") != is_active:
                    continue
                
                filtered_users.append(user)
            
            # Apply pagination if provided
            if page is not None and page_size is not None:
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                filtered_users = filtered_users[start_idx:end_idx]
            
            return filtered_users
        except CustomValidationError as e:
            raise e  # Re-raise ValidationError to be caught by API endpoint
    
    def log_user_activity(self, user_id: str, action: str, ip: str = None, user_agent: str = None) -> Dict[str, Any]:
        """Log user activity for auditing purposes"""
        try:
            # Use provided user_service or the one in auth_service
            if self.user_service is None:
                raise AuthenticationError("User service not available")
            
            # Validate action
            valid_actions = ["login", "logout", "create", "update", "delete", "view", "download", "upload", "view_profile", "update_settings"]
            if action not in valid_actions:
                raise CustomValidationError(f"Invalid action. Must be one of: {', '.join(valid_actions)}")
            
            # Log activity using the service method
            activity_data = {
                "user_id": user_id,
                "action": action,
                "ip": ip or "unknown",
                "user_agent": user_agent or "unknown",
                "timestamp": datetime.now()
            }
            
            result = self.user_service.log_user_activity(**activity_data)
            
            # Handle boolean return by creating response data
            if result is True:
                return {
                    "success": True,
                    "activity_id": f"activity_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "user_id": user_id,
                    "action": action,
                    "ip": ip or "unknown"
                }
            
            return result
        except CustomValidationError as e:
            raise e  # Re-raise ValidationError to be caught by API endpoint
    
    def get_user_audit_trail(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user audit trail"""
        try:
            # Use provided user_service or the one in auth_service
            if self.user_service is None:
                raise AuthenticationError("User service not available")
            
            # Get audit trail from service
            audit_trail = self.user_service.get_user_audit_trail(user_id)
            return audit_trail
        except CustomValidationError as e:
            raise e  # Re-raise ValidationError to be caught by API endpoint
    
    def check_permission(self, user_id: str, action: str, target_user_id: str = None, resource: str = None) -> bool:
        """Check if user has permission to perform an action"""
        try:
            # Use provided user_service or the one in auth_service
            if self.user_service is None:
                raise AuthenticationError("User service not available")
            
            # Get the user
            user = self.user_service.get_user(user_id)
            if not user:
                raise AuthenticationError("User not found")
            
            # Admins have all permissions
            if user.get("role") == "admin":
                return True
            
            # Role-based permissions
            role = user.get("role", "student")
            
            # Define permissions by role
            permissions = {
                "student": {
                    "view_profile": True,  # Can view their own profile
                    "update_profile": True,  # Can update their own profile
                    "view_courses": True,
                    "submit_assignments": True,
                    "view_grades": True
                },
                "teacher": {
                    "view_profile": True,
                    "update_profile": True,
                    "view_courses": True,
                    "create_courses": True,
                    "manage_students": True,
                    "grade_assignments": True
                }
            }
            
            # Check if action is allowed for the role
            action_permissions = permissions.get(role, {})
            has_permission = action_permissions.get(action, False)
            
            # Additional permission checks for specific actions
            if action in ["view_profile", "update_profile"] and target_user_id:
                # Users can view/update their own profile
                has_permission = has_permission and (user_id == target_user_id)
                # Teachers can view other profiles
                if role == "teacher" and action == "view_profile":
                    has_permission = True
            
            return has_permission
        except CustomValidationError as e:
            raise e  # Re-raise ValidationError to be caught by API endpoint
    
    def change_password(self, user_id: str, current_password: str, new_password: str, user_service) -> bool:
        """Change user password"""
        user = user_service.get_user(user_id)
        if not user:
            raise NotFoundError("User not found")
            
        if not self.verify_password(current_password, user["password"]):
            raise ValidationError("Current password is incorrect")
            
        # Hash new password and update
        hashed_password = self.get_password_hash(new_password)
        user_service.update_user(user_id, password_hash=hashed_password)
        
        return True
    
    def initiate_password_reset(self, email: str, user_service) -> Dict[str, str]:
        """Initiate password reset flow"""
        if user_service is None:
            raise AuthenticationError("User service not available")
            
        try:
            user = user_service.get_user_by_email(email)
            if not user:
                # Don't reveal if email exists or not
                raise ValidationError("If the email exists, a reset link will be sent")
        except NotFoundError:
            # Don't reveal if email exists or not
            raise ValidationError("If the email exists, a reset link will be sent")
        
        # Create reset token with shorter expiration
        reset_token = self.create_access_token(
            data={"sub": user["user_id"], "email": user["email"], "type": "reset"},
            expires_delta=timedelta(hours=1)
        )
        
        # In a real implementation, you would send an email with the reset token
        # For now, just return the token (in production, don't do this!)
        return {
            "message": "Password reset initiated",
            "reset_token": reset_token
        }
    
    def confirm_password_reset(self, reset_token: str, new_password: str, confirm_password: str, user_service) -> bool:
        """Confirm password reset"""
        if new_password != confirm_password:
            raise ValidationError("Passwords do not match")
        
        # Verify reset token
        token_data = self.verify_token(reset_token)
        if token_data.type != "reset":
            raise AuthenticationError("Invalid reset token")
        
        # Update password
        user_service.change_user_password(token_data.sub, new_password)
        
        return True
    
    def validate_password_strength(self, password: str) -> bool:
        """Validate password strength based on requirements"""
        if not password or len(password.strip()) < settings.password_min_length:
            return False
        
        # Check for whitespace
        if any(c.isspace() for c in password):
            return False
        
        has_uppercase = any(c.isupper() for c in password)
        has_lowercase = any(c.islower() for c in password)
        has_number = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        # Only check requirements that are enabled
        checks = []
        if settings.password_require_uppercase:
            checks.append(has_uppercase)
        if settings.password_require_lowercase:
            checks.append(has_lowercase)
        if settings.password_require_number:
            checks.append(has_number)
        if settings.password_require_special:
            checks.append(has_special)
        
        return all(checks)
    
    def validate_password(self, password: str) -> bool:
        """Validate password meets basic requirements"""
        if not password or len(password) < 8:
            return False
        
        # Check for at least one uppercase, one lowercase, one digit, and one special character
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*(),.?":{}|<>' for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def create_session_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create session data from user data"""
        return {
            "user_id": user_data.get("user_id"),
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "role": user_data.get("role"),
            "session_start": datetime.now(timezone.utc).isoformat()
        }
    
    def validate_session_data(self, session_data: Dict[str, Any]) -> bool:
        """Validate session data"""
        required_fields = ["user_id", "email"]
        return all(field in session_data for field in required_fields)
    
    def sanitize_input(self, input_str: str) -> str:
        """Sanitize input to prevent injection attacks"""
        # Use the enhanced validation version
        from core.validation import sanitize_input as validation_sanitize
        return validation_sanitize(input_str)

# Global auth service instance
auth_service = AuthService()

