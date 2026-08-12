"""
User API endpoints for user management.

This module provides:
- User CRUD operations
- Authentication endpoints
- Authorization checks
- Validation and error handling
- Caching optimization
- Health checks
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from src.core.exceptions import ValidationError, NotFoundError, ConflictError, AuthenticationError
from src.core.security import auth_service, verify_token
from src.core.response_handler import ResponseFormatter
from src.services.base_service import UserService, get_user_service, ServiceFactory

router = APIRouter()
security = HTTPBearer()

logger = logging.getLogger(__name__)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user."""
    try:
        token = credentials.credentials
        user = await verify_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/", response_model=Dict[str, Any])
async def create_user(
    user_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Create a new user."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create users"
            )
        
        # Validate user data
        if not user_data.get('email'):
            raise ValidationError("Email is required", "email")
        
        if not user_data.get('name'):
            raise ValidationError("Name is required", "name")
        
        if not user_data.get('role'):
            raise ValidationError("Role is required", "role")
        
        # Check if user already exists
        existing_user = await user_service.get_user_by_email(user_data['email'])
        if existing_user:
            raise ConflictError("User with this email already exists", "email")
        
        # Create user
        user_id = await user_service.create_user(user_data)
        
        # Get created user
        created_user = await user_service.get_user_by_id(user_id)
        
        logger.info(f"User created: {user_id}")
        return ResponseFormatter.success(
            data=created_user,
            message="User created successfully",
            status_code=status.HTTP_201_CREATED
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ConflictError as e:
        logger.warning(f"Conflict error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get current user profile."""
    try:
        return ResponseFormatter.success(
            data=current_user,
            message="User profile retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID."""
    try:
        # Check permissions
        if current_user.get('id') != user_id and current_user.get('role') not in ['admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found", "user_id")
        
        return ResponseFormatter.success(
            data=user,
            message="User retrieved successfully"
        )
        
    except NotFoundError as e:
        logger.warning(f"User not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/{user_id}", response_model=Dict[str, Any])
async def update_user(
    user_id: str,
    update_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update user information."""
    try:
        # Check permissions
        if current_user.get('id') != user_id and current_user.get('role') not in ['admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Validate update data
        if not update_data:
            raise ValidationError("Update data is required", "update_data")
        
        # Update user
        result = await user_service.update_user(user_id, update_data)
        
        if result == 0:
            raise NotFoundError("User not found", "user_id")
        
        # Get updated user
        updated_user = await user_service.get_user_by_id(user_id)
        
        logger.info(f"User updated: {user_id}")
        return ResponseFormatter.success(
            data=updated_user,
            message="User updated successfully"
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        logger.warning(f"User not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/", response_model=Dict[str, Any])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    role: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get users with pagination and filtering."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Build filter
        filter_dict = {}
        if role:
            filter_dict['role'] = role
        
        # Get users
        users = await user_service.find_many(
            "users",
            filter_dict,
            limit=limit,
            skip=skip
        )
        
        # Get total count
        total = await user_service._database.count("users", filter_dict)
        
        return ResponseFormatter.success(
            data={
                "users": users,
                "pagination": {
                    "total": total,
                    "skip": skip,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit
                }
            },
            message="Users retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/{user_id}", response_model=Dict[str, Any])
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Delete a user."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can delete users"
            )
        
        if current_user.get('id') == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Get user first
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found", "user_id")
        
        # Delete user
        result = await user_service.delete_one("users", {"id": user_id})
        
        if result == 0:
            raise NotFoundError("User not found", "user_id")
        
        logger.info(f"User deleted: {user_id}")
        return ResponseFormatter.success(
            message="User deleted successfully"
        )
        
    except NotFoundError as e:
        logger.warning(f"User not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{user_id}/health", response_model=Dict[str, Any])
async def user_service_health(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """Health check for user service."""
    try:
        health_status = await user_service.health_check()
        return ResponseFormatter.success(
            data=health_status,
            message="User service health check completed"
        )
    except Exception as e:
        logger.error(f"Error checking user service health: {str(e)}")
        return ResponseFormatter.error(
            message="User service health check failed",
            error_code="SERVICE_HEALTH_ERROR",
            details={"error": str(e)}
        )