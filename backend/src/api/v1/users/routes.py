"""
User Routes - REST API Endpoints

This module provides comprehensive REST API endpoints for user management,
including authentication, CRUD operations, and user management features.

Author: Edu-Flow Team
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta
import json
from logging import getLogger

from ...models.user import User, UserRole
from ...services.user_service import UserService
from ...core.security import SecurityConfig
from ...core.dependencies import get_db, get_current_user, get_current_active_admin
from ...core.exceptions import UserNotFoundError, UserExistsError, AuthenticationError
from ...config.settings import settings

logger = getLogger(__name__)
security_config = SecurityConfig()

router = APIRouter(prefix="/users", tags=["users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")


@router.post("/token", response_model=Dict[str, str])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint to authenticate users and return JWT tokens
    
    Args:
        form_data: OAuth2 password form with username and password
        db: Database session
        
    Returns:
        Dictionary with access token token type
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        user_service = UserService(db)
        user = await user_service.authenticate_user(form_data.username, form_data.password)
        
        if not user:
            raise AuthenticationError("Invalid credentials")
            
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security_config.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        logger.info(f"User {user.email} logged in successfully")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except AuthenticationError:
        logger.warning(f"Failed login attempt for {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/register", response_model=Dict[str, str], status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Register a new user in the system
    
    Args:
        user_data: Dictionary containing user information (email, password, name, role)
        db: Database session
        
    Returns:
        Success message with user ID
        
    Raises:
        HTTPException: If user already exists or validation fails
    """
    try:
        user_service = UserService(db)
        
        # Validate required fields
        required_fields = ["email", "password", "name", "role"]
        for field in required_fields:
            if field not in user_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Validate role
        try:
            role = UserRole(user_data["role"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be one of: student, teacher, admin"
            )
        
        # Create user
        user = await user_service.create_user(
            email=user_data["email"],
            password=user_data["password"],
            name=user_data["name"],
            role=role,
            **{k: v for k, v in user_data.items() if k not in required_fields}
        )
        
        logger.info(f"New user registered: {user.email}")
        return {"message": "User registered successfully", "user_id": str(user.id)}
        
    except UserExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.get("/", response_model=List[Dict[str, Any]])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Get list of users (admin only)
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        role: Filter by user role
        search: Search term for user name or email
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        List of user dictionaries
    """
    user_service = UserService(db)
    users = await user_service.get_users(
        skip=skip,
        limit=limit,
        role=role,
        search=search
    )
    return users


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile information
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User profile information
    """
    user_service = UserService(db)
    user_info = await user_service.get_user_by_id(current_user.id)
    return user_info


@router.put("/me", response_model=Dict[str, Any])
async def update_current_user(
    user_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information
    
    Args:
        user_data: User data to update
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user information
    """
    user_service = UserService(db)
    updated_user = await user_service.update_user(current_user.id, user_data)
    return updated_user


@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID
    
    Args:
        user_id: User ID to retrieve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        return user
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.put("/{user_id}", response_model=Dict[str, Any])
async def update_user(
    user_id: str,
    user_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Update user information (admin only)
    
    Args:
        user_id: User ID to update
        user_data: User data to update
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        Updated user information
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user_service = UserService(db)
        updated_user = await user_service.update_user(user_id, user_data)
        return updated_user
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Delete user (admin only)
    
    Args:
        user_id: User ID to delete
        current_user: Current authenticated user (admin)
        db: Database session
        background_tasks: Background tasks for cleanup
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user_service = UserService(db)
        await user_service.delete_user(user_id, background_tasks)
        
        logger.info(f"User deleted: {user_id}")
        return None
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.post("/{user_id}/activate", response_model=Dict[str, str])
async def activate_user(
    user_id: str,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Activate user account (admin only)
    
    Args:
        user_id: User ID to activate
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user_service = UserService(db)
        await user_service.activate_user(user_id)
        
        logger.info(f"User activated: {user_id}")
        return {"message": "User activated successfully"}
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.post("/{user_id}/deactivate", response_model=Dict[str, str])
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Deactivate user account (admin only)
    
    Args:
        user_id: User ID to deactivate
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user_service = UserService(db)
        await user_service.deactivate_user(user_id)
        
        logger.info(f"User deactivated: {user_id}")
        return {"message": "User deactivated successfully"}
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.get("/{user_id}/activity", response_model=List[Dict[str, Any]])
async def get_user_activity(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user activity logs
    
    Args:
        user_id: User ID to get activity for
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of user activity logs
    """
    # Admin users can see any user's activity, regular users can only see their own
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's activity"
        )
    
    user_service = UserService(db)
    activity_logs = await user_service.get_user_activity(user_id)
    return activity_logs


@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_user_statistics(
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Get user statistics (admin only)
    
    Args:
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        User statistics dictionary
    """
    user_service = UserService(db)
    stats = await user_service.get_user_statistics()
    return stats