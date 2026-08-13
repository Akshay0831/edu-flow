"""
Department Management API Endpoints

This module provides REST API endpoints for department management operations:
- CRUD operations for departments
- Department hierarchy management
- Department statistics and metrics
- Department user management
- Department course management

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.security import auth_service
from src.core.exceptions import ValidationError, NotFoundError, AuthenticationError, AuthorizationError
from src.infrastructure.repositories.department_repository import DepartmentRepository

# Create router
router = APIRouter(prefix="/departments", tags=["departments"])

# Security
security = HTTPBearer()

# Repositories
department_repo = DepartmentRepository()


# Pydantic models
class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=10)
    description: Optional[str] = Field(None, max_length=500)
    head_of_department: Optional[str] = Field(None)
    contact_email: Optional[str] = Field(None)
    contact_phone: Optional[str] = Field(None)
    location: Optional[str] = Field(None, max_length=200)
    parent_department_id: Optional[str] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(DepartmentBase):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    code: Optional[str] = Field(None, min_length=2, max_length=10)


class DepartmentResponse(DepartmentBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    has_children: bool = False
    program_count: int = 0
    course_count: int = 0
    teacher_count: int = 0
    student_count: int = 0

    class Config:
        from_attributes = True


@router.get("/", response_model=List[DepartmentResponse])
async def get_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """
    Get all departments with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Search term for name or code
        is_active: Filter by active status
        
    Returns:
        List of departments
    """
    try:
        departments = await department_repo.get_all(
            skip=skip,
            limit=limit,
            search=search,
            is_active=is_active
        )
        
        # Add derived information
        for dept in departments:
            dept.has_children = await department_repo.has_children(dept.id)
            dept.program_count = await department_repo.get_program_count(dept.id)
            dept.course_count = await department_repo.get_course_count(dept.id)
            dept.teacher_count = await department_repo.get_teacher_count(dept.id)
            dept.student_count = await department_repo.get_student_count(dept.id)
        
        return departments
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch departments: {str(e)}"
        )


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(department_id: str):
    """
    Get a specific department by ID
    
    Args:
        department_id: Department ID
        
    Returns:
        Department details
    """
    try:
        department = await department_repo.get_by_id(department_id)
        if not department:
            raise NotFoundError(f"Department not found with ID: {department_id}")
        
        # Add derived information
        department.has_children = await department_repo.has_children(department_id)
        department.program_count = await department_repo.get_program_count(department_id)
        department.course_count = await department_repo.get_course_count(department_id)
        department.teacher_count = await department_repo.get_teacher_count(department_id)
        department.student_count = await department_repo.get_student_count(department_id)
        
        return department
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department not found with ID: {department_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch department: {str(e)}"
        )


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_data: DepartmentCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new department
    
    Args:
        department_data: Department data
        credentials: JWT token
        
    Returns:
        Created department
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'super_admin']:
            raise AuthorizationError("Insufficient permissions to create departments")
        
        # Create department
        department = await department_repo.create(
            name=department_data.name,
            code=department_data.code,
            description=department_data.description,
            head_of_department=department_data.head_of_department,
            contact_email=department_data.contact_email,
            contact_phone=department_data.contact_phone,
            location=department_data.location,
            parent_department_id=department_data.parent_department_id,
            metadata=department_data.metadata
        )
        
        return department
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create department: {str(e)}"
        )


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: str,
    department_data: DepartmentUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update a department
    
    Args:
        department_id: Department ID
        department_data: Updated department data
        credentials: JWT token
        
    Returns:
        Updated department
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'super_admin']:
            raise AuthorizationError("Insufficient permissions to update departments")
        
        # Check if department exists
        existing_dept = await department_repo.get_by_id(department_id)
        if not existing_dept:
            raise NotFoundError(f"Department not found with ID: {department_id}")
        
        # Update department
        department = await department_repo.update(
            department_id=department_id,
            **department_data.dict(exclude_unset=True)
        )
        
        return department
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department not found with ID: {department_id}"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update department: {str(e)}"
        )


@router.delete("/{department_id}")
async def delete_department(
    department_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a department
    
    Args:
        department_id: Department ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'super_admin']:
            raise AuthorizationError("Insufficient permissions to delete departments")
        
        # Check if department exists
        existing_dept = await department_repo.get_by_id(department_id)
        if not existing_dept:
            raise NotFoundError(f"Department not found with ID: {department_id}")
        
        # Check if department has children
        if await department_repo.has_children(department_id):
            raise ValidationError("Cannot delete department with child departments")
        
        # Check if department has programs
        if await department_repo.get_program_count(department_id) > 0:
            raise ValidationError("Cannot delete department with programs")
        
        # Delete department
        await department_repo.delete(department_id)
        
        return {"message": "Department deleted successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department not found with ID: {department_id}"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete department: {str(e)}"
        )


@router.post("/{department_id}/activate")
async def activate_department(
    department_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Activate a department
    
    Args:
        department_id: Department ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'super_admin']:
            raise AuthorizationError("Insufficient permissions to activate departments")
        
        await department_repo.update(department_id, is_active=True)
        
        return {"message": "Department activated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate department: {str(e)}"
        )


@router.post("/{department_id}/deactivate")
async def deactivate_department(
    department_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Deactivate a department
    
    Args:
        department_id: Department ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'super_admin']:
            raise AuthorizationError("Insufficient permissions to deactivate departments")
        
        await department_repo.update(department_id, is_active=False)
        
        return {"message": "Department deactivated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate department: {str(e)}"
        )


@router.get("/{department_id}/hierarchy")
async def get_department_hierarchy(
    department_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get department hierarchy
    
    Args:
        department_id: Department ID
        credentials: JWT token
        
    Returns:
        Department hierarchy data
    """
    try:
        hierarchy = await department_repo.get_hierarchy(department_id)
        return hierarchy
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch department hierarchy: {str(e)}"
        )


@router.get("/{department_id}/statistics")
async def get_department_statistics(
    department_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get department statistics
    
    Args:
        department_id: Department ID
        credentials: JWT token
        
    Returns:
        Department statistics
    """
    try:
        stats = await department_repo.get_statistics(department_id)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch department statistics: {str(e)}"
        )


@router.get("/{department_id}/programs")
async def get_department_programs(
    department_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get department programs
    
    Args:
        department_id: Department ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        credentials: JWT token
        
    Returns:
        List of department programs
    """
    try:
        programs = await department_repo.get_programs(department_id, skip, limit)
        return programs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch department programs: {str(e)}"
        )


@router.get("/{department_id}/courses")
async def get_department_courses(
    department_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get department courses
    
    Args:
        department_id: Department ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        credentials: JWT token
        
    Returns:
        List of department courses
    """
    try:
        courses = await department_repo.get_courses(department_id, skip, limit)
        return courses
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch department courses: {str(e)}"
        )


@router.get("/{department_id}/teachers")
async def get_department_teachers(
    department_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get department teachers
    
    Args:
        department_id: Department ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        credentials: JWT token
        
    Returns:
        List of department teachers
    """
    try:
        teachers = await department_repo.get_teachers(department_id, skip, limit)
        return teachers
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch department teachers: {str(e)}"
        )


@router.get("/{department_id}/students")
async def get_department_students(
    department_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get department students
    
    Args:
        department_id: Department ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        credentials: JWT token
        
    Returns:
        List of department students
    """
    try:
        students = await department_repo.get_students(department_id, skip, limit)
        return students
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch department students: {str(e)}"
        )