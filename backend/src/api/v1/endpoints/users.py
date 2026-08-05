"""
User Management API Endpoints

This module provides REST API endpoints for user management operations:
- CRUD operations for users
- User authentication and authorization
- User profile management
- User search and filtering
- User activity logging
- User audit trail
- User permission management

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, validator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.security import AuthService
from src.core.exceptions import ValidationError, NotFoundError, AuthenticationError
from src.services.user_service import UserService

# Create router
router = APIRouter(prefix="/users", tags=["users"])

# Security
security = HTTPBearer()

# Services
user_service = UserService()
auth_service = AuthService()


# Pydantic models
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str
    department: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['student', 'teacher', 'admin', 'staff']
        if v not in valid_roles:
            raise ValueError(f'Invalid role. Must be one of: {valid_roles}')
        return v


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserProfileUpdate(UserUpdate):
    pass


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    department: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None


class UserSearchRequest(BaseModel):
    query: Optional[str] = ""
    role: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    page: int = 1
    page_size: int = 10


class UserBulkActionRequest(BaseModel):
    user_ids: List[str]
    action: str
    params: Optional[Dict[str, Any]] = None


class UserActivity(BaseModel):
    activity_id: str
    user_id: str
    action: str
    ip: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime


class AuditTrail(BaseModel):
    audit_id: str
    user_id: str
    action: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    performed_by: str


class UserStatistics(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    role_distribution: Dict[str, int]


# Dependency to get current user from token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from JWT token"""
    try:
        token = credentials.credentials
        user_data = auth_service.decode_token(token)
        return user_data
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# API Endpoints
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user
    
    - **email**: Valid email address
    - **password**: Must meet password requirements
    - **name**: User display name
    - **role**: User role (student, teacher, admin, staff)
    """
    try:
        user = user_service.create_user(
            email=user_data.email,
            password=user_data.password,
            name=user_data.name,
            role=user_data.role,
            department=user_data.department,
            bio=user_data.bio,
            phone=user_data.phone,
            preferences=user_data.preferences
        )
        return UserResponse(**user)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current user information
    
    Returns the profile of the authenticated user
    """
    try:
        user = user_service.get_user(current_user["user_id"])
        return UserResponse(**user)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get user by ID
    
    - **user_id**: Unique user identifier
    """
    try:
        user = user_service.get_user(user_id)
        
        # Check permissions
        if not user_service.check_permission(current_user["user_id"], "view_profile", user_id):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        return UserResponse(**user)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Update user information
    
    - **user_id**: Unique user identifier
    - **user_data**: Updated user information
    """
    try:
        # Check permissions
        if not user_service.check_permission(current_user["user_id"], "update_profile", user_id):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        user = user_service.update_user(
            user_id=user_id,
            **user_data.dict(exclude_unset=True)
        )
        return UserResponse(**user)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}/profile", response_model=UserResponse)
async def update_user_profile(user_id: str, profile_data: UserProfileUpdate, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Update user profile
    
    - **user_id**: Unique user identifier
    - **profile_data**: Updated profile information
    """
    return await update_user(user_id, profile_data, current_user)


@router.put("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Deactivate a user
    
    - **user_id**: Unique user identifier
    """
    try:
        # Check permissions
        if not user_service.check_permission(current_user["user_id"], "manage_users", user_id):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        user = user_service.deactivate_user(user_id)
        return UserResponse(**user)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}/reactivate", response_model=UserResponse)
async def reactivate_user(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Reactivate a deactivated user
    
    - **user_id**: Unique user identifier
    """
    try:
        # Check permissions
        if not user_service.check_permission(current_user["user_id"], "manage_users", user_id):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        user = user_service.reactivate_user(user_id)
        return UserResponse(**user)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}/role", response_model=UserResponse)
async def change_user_role(user_id: str, role: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Change user role
    
    - **user_id**: Unique user identifier
    - **role**: New user role (student, teacher, admin, staff)
    """
    try:
        # Check permissions
        if not user_service.check_permission(current_user["user_id"], "manage_users", user_id):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        user = user_service.change_user_role(user_id, role)
        return UserResponse(**user)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}/password", response_model=dict)
async def change_user_password(user_id: str, new_password: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Change user password
    
    - **user_id**: Unique user identifier
    - **new_password**: New password (must meet requirements)
    """
    try:
        # Check permissions
        if not user_service.check_permission(current_user["user_id"], "manage_users", user_id):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        user_service.change_user_password(user_id, new_password)
        return {"message": "Password changed successfully"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}", response_model=dict)
async def delete_user(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Delete a user (soft delete)
    
    - **user_id**: Unique user identifier
    """
    try:
        # Check permissions
        if not user_service.check_permission(current_user["user_id"], "manage_users", user_id):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        user = user_service.delete_user(user_id)
        return {"message": "User deleted successfully"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=List[UserResponse])
async def search_users(search_request: UserSearchRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Search users with filtering and pagination
    
    - **query**: Search query for name/email
    - **role**: Filter by role
    - **department**: Filter by department
    - **is_active**: Filter by active status
    - **page**: Page number
    - **page_size**: Number of items per page
    """
    try:
        users = user_service.search_users(
            query=search_request.query,
            role=search_request.role,
            department=search_request.department,
            is_active=search_request.is_active,
            page=search_request.page,
            page_size=search_request.page_size
        )
        
        # Convert to response format
        return [UserResponse(**user) for user in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=UserStatistics)
async def get_user_statistics(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get user statistics
    
    Returns user statistics including total users, active users, and role distribution
    """
    try:
        statistics = user_service.get_user_statistics()
        return UserStatistics(**statistics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-action", response_model=dict)
async def bulk_user_action(action_request: UserBulkActionRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Perform bulk actions on users
    
    - **user_ids**: List of user IDs to act on
    - **action**: Action to perform (deactivate, reactivate, change_role)
    - **params**: Additional parameters for the action
    """
    try:
        # Check permissions
        if not user_service.check_permission(current_user["user_id"], "manage_users"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        if action_request.action == "deactivate":
            users = user_service.bulk_deactivate_users(action_request.user_ids)
        elif action_request.action == "reactivate":
            users = user_service.bulk_reactivate_users(action_request.user_ids)
        elif action_request.action == "change_role":
            new_role = action_request.params.get("role")
            if not new_role:
                raise HTTPException(status_code=400, detail="Role parameter is required for change_role action")
            users = user_service.bulk_change_user_role(action_request.user_ids, new_role)
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        return {
            "message": f"Bulk {action_request.action} completed successfully",
            "users_affected": len(users)
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/activities", response_model=List[UserActivity])
async def get_user_activities(user_id: str, action: Optional[str] = None, 
                           limit: int = 50, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get user activities
    
    - **user_id**: Unique user identifier
    - **action**: Filter by action type
    - **limit**: Maximum number of activities to return
    """
    try:
        # Check permissions
        if not user_service.check_permission(current_user["user_id"], "view_profile", user_id):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        activities = user_service.get_user_activities(
            user_id=user_id,
            action=action,
            limit=limit
        )
        
        return [UserActivity(**activity) for activity in activities]
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/audit-trail", response_model=List[AuditTrail])
async def get_user_audit_trail(user_id: str, limit: int = 100, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get user audit trail
    
    - **user_id**: Unique user identifier
    - **limit**: Maximum number of audit entries to return
    """
    try:
        # Check permissions
        if not user_service.check_permission(current_user["user_id"], "manage_users", user_id):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        audit_trail = user_service.get_user_audit_trail(user_id=user_id, limit=limit)
        
        return [AuditTrail(**entry) for entry in audit_trail]
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))