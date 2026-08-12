"""
Teacher API endpoints for teacher management.

This module provides:
- Teacher CRUD operations
- Class assignment endpoints
- Subject management
- Performance analytics
- Health checks
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from src.core.exceptions import ValidationError, NotFoundError, AuthenticationError
from src.core.security import AuthService
from src.core.response_handler import ResponseFormatter


router = APIRouter()
security = HTTPBearer()

logger = logging.getLogger(__name__)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user."""
    try:
        token = credentials.credentials
        auth_service = AuthService()
        token_data = auth_service.verify_token(token)
        return token_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

@router.post("/", response_model=Dict[str, Any])
async def create_teacher(
    teacher_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new teacher."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create teachers"
            )
        
        # Validate teacher data
        if not teacher_data.get('user_id'):
            raise ValidationError("User ID is required", "user_id")
        
        if not teacher_data.get('employee_id'):
            raise ValidationError("Employee ID is required", "employee_id")
        
        if not teacher_data.get('department_id'):
            raise ValidationError("Department ID is required", "department_id")
        
        # Check if teacher already exists
        existing_teacher = await teacher_service.get_teacher_by_id(teacher_data['user_id'])
        if existing_teacher:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Teacher with this user ID already exists"
            )
        
        # Create teacher
        teacher_id = await teacher_service.create_teacher(teacher_data)
        
        # Get created teacher
        created_teacher = await teacher_service.get_teacher_by_id(teacher_id)
        
        logger.info(f"Teacher created: {teacher_id}")
        return ResponseFormatter.success(
            data=created_teacher,
            message="Teacher created successfully",
            status_code=status.HTTP_201_CREATED
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error creating teacher: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating teacher: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/me", response_model=Dict[str, Any])
async def get_current_teacher_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current teacher profile."""
    try:
        # Check if user is a teacher
        # TODO: Implement teacher service lookup
        if current_user.get('role') != 'teacher':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Teacher role required"
            )
        
        # Return basic profile info for now
        return {
            "id": current_user['id'],
            "name": current_user.get('name'),
            "email": current_user.get('email'),
            "role": current_user.get('role')
        }
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher profile not found"
            )
        
        return ResponseFormatter.success(
            data=teacher,
            message="Teacher profile retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting teacher profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{teacher_id}", response_model=Dict[str, Any])
async def get_teacher(
    teacher_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    teacher_service: TeacherService = Depends(get_teacher_service)
):
    """Get teacher by ID."""
    try:
        # Check permissions
        if current_user.get('id') != teacher_id and current_user.get('role') not in ['admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        teacher = await teacher_service.get_teacher_by_id(teacher_id)
        if not teacher:
            raise NotFoundError("Teacher not found", "teacher_id")
        
        return ResponseFormatter.success(
            data=teacher,
            message="Teacher retrieved successfully"
        )
        
    except NotFoundError as e:
        logger.warning(f"Teacher not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting teacher: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/{teacher_id}", response_model=Dict[str, Any])
async def update_teacher(
    teacher_id: str,
    update_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    teacher_service: TeacherService = Depends(get_teacher_service)
):
    """Update teacher information."""
    try:
        # Check permissions
        if current_user.get('id') != teacher_id and current_user.get('role') not in ['admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Validate update data
        if not update_data:
            raise ValidationError("Update data is required", "update_data")
        
        # Update teacher
        result = await teacher_service.update_teacher(teacher_id, update_data)
        
        if result == 0:
            raise NotFoundError("Teacher not found", "teacher_id")
        
        # Get updated teacher
        updated_teacher = await teacher_service.get_teacher_by_id(teacher_id)
        
        logger.info(f"Teacher updated: {teacher_id}")
        return ResponseFormatter.success(
            data=updated_teacher,
            message="Teacher updated successfully"
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error updating teacher: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        logger.warning(f"Teacher not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating teacher: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/", response_model=Dict[str, Any])
async def get_teachers(
    department_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    teacher_service: TeacherService = Depends(get_teacher_service)
):
    """Get teachers with pagination and filtering."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Build filter
        filter_dict = {}
        if department_id:
            filter_dict["department_id"] = department_id
        
        # Get teachers
        teachers = await teacher_service.find_many(
            "teachers",
            filter_dict,
            limit=limit,
            skip=skip
        )
        
        # Get total count
        total = await teacher_service._database.count("teachers", filter_dict)
        
        return ResponseFormatter.success(
            data={
                "teachers": teachers,
                "pagination": {
                    "total": total,
                    "skip": skip,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit
                }
            },
            message="Teachers retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting teachers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{teacher_id}/classes", response_model=Dict[str, Any])
async def get_teacher_classes(
    teacher_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    teacher_service: TeacherService = Depends(get_teacher_service)
):
    """Get classes assigned to a teacher."""
    try:
        # Check permissions
        if current_user.get('id') != teacher_id and current_user.get('role') not in ['admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # This would typically be implemented with a join or separate service
        # For now, we'll return a placeholder response
        classes_assigned = []  # Placeholder - implement actual class assignment logic
        
        return ResponseFormatter.success(
            data={
                "teacher_id": teacher_id,
                "classes": classes_assigned,
                "count": len(classes_assigned)
            },
            message="Teacher classes retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting teacher classes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{teacher_id}/health", response_model=Dict[str, Any])
async def teacher_service_health(
    teacher_id: str,
    teacher_service: TeacherService = Depends(get_teacher_service)
):
    """Health check for teacher service."""
    try:
        health_status = await teacher_service.health_check()
        return ResponseFormatter.success(
            data=health_status,
            message="Teacher service health check completed"
        )
    except Exception as e:
        logger.error(f"Error checking teacher service health: {str(e)}")
        return ResponseFormatter.error(
            message="Teacher service health check failed",
            error_code="SERVICE_HEALTH_ERROR",
            details={"error": str(e)}
        )