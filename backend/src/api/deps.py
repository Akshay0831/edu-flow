"""
API Dependencies for Edu-Flow Backend

This module provides dependency injection for API endpoints:
- Database session management
- Authentication and authorization
- Service container access
- Common validation utilities

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.http import HTTPBase
import jwt
from datetime import datetime, timedelta
import logging

from core.security import SecurityConfig
from core.database_abstraction import DatabaseManager, DatabaseConfig
from core.service_container import get_service_container
from core.exceptions import AuthenticationError, NotFoundError

logger = logging.getLogger(__name__)

# Security schemes
security = HTTPBearer(auto_error=True)


def get_db() -> Session:
    """
    Get database session for API operations.
    
    Returns:
        Database session instance
    """
    try:
        from core.database_abstraction import DatabaseManager
        db_manager = DatabaseManager()
        db_session = db_manager.get_session()
        yield db_session
        db_session.close()
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: JWT token credentials
        
    Returns:
        Decoded user information
    """
    try:
        # Decode JWT token
        token = credentials.credentials
        payload = jwt.decode(
            token,
            SecurityConfig.JWT_SECRET,
            algorithms=[SecurityConfig.JWT_ALGORITHM]
        )
        
        # Extract user information
        user_id = payload.get("user_id")
        role = payload.get("role")
        
        if not user_id or not role:
            raise AuthenticationError("Invalid token payload")
        
        return {
            "user_id": user_id,
            "role": role,
            "email": payload.get("email"),
            "full_name": payload.get("full_name"),
            "token": token,
            "exp": payload.get("exp"),
            "iat": payload.get("iat")
        }
    
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.JWTError:
        raise AuthenticationError("Invalid token")
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


def get_service_container() -> Dict[str, Any]:
    """
    Get service container for dependency injection.
    
    Returns:
        Service container instance
    """
    try:
        from core.service_container import get_service_container
        container = get_service_container()
        return container
    except Exception as e:
        logger.error(f"Service container error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service container unavailable"
        )


def validate_user_role(required_role: str):
    """
    Role-based access control decorator.
    
    Args:
        required_role: Required role (admin, teacher, student)
        
    Returns:
        Dependency function for role validation
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role")
        
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}"
            )
        
        return current_user
    
    return role_checker


def validate_student_role(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Validate user has student role."""
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Student role required"
        )
    return current_user


def validate_teacher_role(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Validate user has teacher role."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Teacher role required"
        )
    return current_user


def validate_admin_role(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Validate user has admin role."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required"
        )
    return current_user


def validate_optional_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict[str, Any]]:
    """
    Optional authentication - returns user if authenticated, None otherwise.
    
    Args:
        credentials: Optional JWT token credentials
        
    Returns:
        Decoded user information or None
    """
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None


# Common validation functions
def validate_resource_id(resource_id: str) -> str:
    """
    Validate resource ID format.
    
    Args:
        resource_id: Resource ID to validate
        
    Returns:
        Validated resource ID
    """
    if not resource_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resource ID is required"
        )
    
    if not isinstance(resource_id, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resource ID must be a string"
        )
    
    if len(resource_id.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resource ID cannot be empty"
        )
    
    return resource_id.strip()


def validate_pagination_params(page: int = 1, limit: int = 100) -> Dict[str, int]:
    """
    Validate pagination parameters.
    
    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 100)
        
    Returns:
        Validated pagination parameters
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be positive"
        )
    
    if limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be positive"
        )
    
    if limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit cannot exceed 1000"
        )
    
    return {"page": page, "limit": limit}


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=SecurityConfig.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        SecurityConfig.JWT_SECRET,
        algorithm=SecurityConfig.JWT_ALGORITHM
    )
    
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        import bcrypt
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def get_hashed_password(password: str) -> str:
    """
    Hash password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    import bcrypt
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')