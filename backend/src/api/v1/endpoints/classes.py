"""
Class Management API Endpoints

This module provides REST API endpoints for class management operations:
- CRUD operations for classes
- Class scheduling and timetabling
- Class enrollment management
- Class attendance tracking
- Class performance metrics

Author: Edu-Flow Team
"""

from datetime import datetime, time
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field, validator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.security import auth_service
from core.exceptions import ValidationError, NotFoundError, AuthenticationError, AuthorizationError
from infrastructure.repositories.class_repository import ClassRepository

# Create router
router = APIRouter(prefix="/classes", tags=["classes"])

# Security
security = HTTPBearer()

# Repositories
class_repo = ClassRepository()


# Pydantic models
class ClassBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=20)
    department_id: str = Field(..., min_length=2)
    program_id: str = Field(..., min_length=2)
    subject_id: str = Field(..., min_length=2)
    academic_year: str = Field(..., min_length=4, max_length=10)
    semester: int = Field(..., ge=1, le=12)
    section: str = Field(..., min_length=1, max_length=10)
    max_capacity: int = Field(..., ge=1, le=1000)
    current_enrollment: int = Field(0, ge=0, le=1000)
    classroom: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ClassCreate(ClassBase):
    allocated_teacher_id: Optional[str] = Field(None)
    schedule_days: List[str] = Field(default_factory=list)
    schedule_times: List[str] = Field(default_factory=list)
    schedule_duration: Optional[int] = Field(None)  # in minutes


class ClassUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    code: Optional[str] = Field(None, min_length=2, max_length=20)
    department_id: Optional[str] = Field(None, min_length=2)
    program_id: Optional[str] = Field(None, min_length=2)
    subject_id: Optional[str] = Field(None, min_length=2)
    academic_year: Optional[str] = Field(None, min_length=4, max_length=10)
    semester: Optional[int] = Field(None, ge=1, le=12)
    section: Optional[str] = Field(None, min_length=1, max_length=10)
    max_capacity: Optional[int] = Field(None, ge=1, le=1000)
    current_enrollment: Optional[int] = Field(None, ge=0, le=1000)
    classroom: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    allocated_teacher_id: Optional[str] = Field(None)
    schedule_days: Optional[List[str]] = Field(None)
    schedule_times: Optional[List[str]] = Field(None)
    schedule_duration: Optional[int] = Field(None)
    is_active: Optional[bool] = Field(None)


class ClassResponse(ClassBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    allocated_teacher_id: Optional[str]
    attendance_count: int = 0
    average_grade: float = 0.0
    students_enrolled: int = 0
    is_full: bool = False
    
    class Config:
        from_attributes = True


class ScheduleAssignment(BaseModel):
    day_of_week: str = Field(..., description="Day of week (Monday, Tuesday, etc.)")
    start_time: str = Field(..., description="Start time (HH:MM)")
    end_time: str = Field(..., description="End time (HH:MM)")
    classroom: Optional[str] = Field(None)
    is_recurring: bool = Field(True, description="Whether schedule recurs weekly")


@router.get("/", response_model=List[ClassResponse])
async def get_classes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    program_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    allocated_teacher_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """
    Get all classes with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Search term for name or code
        department_id: Filter by department ID
        program_id: Filter by program ID
        subject_id: Filter by subject ID
        academic_year: Filter by academic year
        semester: Filter by semester
        allocated_teacher_id: Filter by allocated teacher ID
        is_active: Filter by active status
        
    Returns:
        List of classes
    """
    try:
        classes = await class_repo.get_all(
            skip=skip,
            limit=limit,
            search=search,
            department_id=department_id,
            program_id=program_id,
            subject_id=subject_id,
            academic_year=academic_year,
            semester=semester,
            allocated_teacher_id=allocated_teacher_id,
            is_active=is_active
        )
        
        # Add derived information
        for cls in classes:
            cls.attendance_count = await class_repo.get_attendance_count(cls.id)
            cls.average_grade = await class_repo.get_average_grade(cls.id)
            cls.students_enrolled = await class_repo.get_student_count(cls.id)
            cls.is_full = cls.current_enrollment >= cls.max_capacity
        
        return classes
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch classes: {str(e)}"
        )


@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(class_id: str):
    """
    Get a specific class by ID
    
    Args:
        class_id: Class ID
        
    Returns:
        Class details
    """
    try:
        class_obj = await class_repo.get_by_id(class_id)
        if not class_obj:
            raise NotFoundError(f"Class not found with ID: {class_id}")
        
        # Add derived information
        class_obj.attendance_count = await class_repo.get_attendance_count(class_id)
        class_obj.average_grade = await class_repo.get_average_grade(class_id)
        class_obj.students_enrolled = await class_repo.get_student_count(class_id)
        class_obj.is_full = class_obj.current_enrollment >= class_obj.max_capacity
        
        return class_obj
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class not found with ID: {class_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch class: {str(e)}"
        )


@router.post("/", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: ClassCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new class
    
    Args:
        class_data: Class data
        credentials: JWT token
        
    Returns:
        Created class
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to create classes")
        
        # Validate capacity
        if class_data.max_capacity < 1:
            raise ValidationError("Maximum capacity must be at least 1")
        
        if class_data.current_enrollment > class_data.max_capacity:
            raise ValidationError("Current enrollment cannot exceed maximum capacity")
        
        # Validate teacher if allocated
        if class_data.allocated_teacher_id:
            teacher_exists = await class_repo.validate_teacher(class_data.allocated_teacher_id)
            if not teacher_exists:
                raise ValidationError("Allocated teacher not found")
        
        # Validate schedule
        if class_data.schedule_days and class_data.schedule_times:
            if len(class_data.schedule_days) != len(class_data.schedule_times):
                raise ValidationError("Schedule days and times must have the same length")
        
        # Create class
        class_obj = await class_repo.create(
            name=class_data.name,
            code=class_data.code,
            department_id=class_data.department_id,
            program_id=class_data.program_id,
            subject_id=class_data.subject_id,
            academic_year=class_data.academic_year,
            semester=class_data.semester,
            section=class_data.section,
            max_capacity=class_data.max_capacity,
            current_enrollment=class_data.current_enrollment,
            classroom=class_data.classroom,
            description=class_data.description,
            allocated_teacher_id=class_data.allocated_teacher_id,
            schedule_days=class_data.schedule_days,
            schedule_times=class_data.schedule_times,
            schedule_duration=class_data.schedule_duration,
            metadata=class_data.metadata
        )
        
        return class_obj
        
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
            detail=f"Failed to create class: {str(e)}"
        )


@router.put("/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: str,
    class_data: ClassUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update a class
    
    Args:
        class_id: Class ID
        class_data: Updated class data
        credentials: JWT token
        
    Returns:
        Updated class
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to update classes")
        
        # Check if class exists
        existing_class = await class_repo.get_by_id(class_id)
        if not existing_class:
            raise NotFoundError(f"Class not found with ID: {class_id}")
        
        # Validate capacity if updated
        if class_data.max_capacity is not None:
            if class_data.max_capacity < 1:
                raise ValidationError("Maximum capacity must be at least 1")
            
            if class_data.current_enrollment is not None:
                if class_data.current_enrollment > class_data.max_capacity:
                    raise ValidationError("Current enrollment cannot exceed maximum capacity")
        
        # Validate teacher if updated
        if class_data.allocated_teacher_id:
            teacher_exists = await class_repo.validate_teacher(class_data.allocated_teacher_id)
            if not teacher_exists:
                raise ValidationError("Allocated teacher not found")
        
        # Update class
        class_obj = await class_repo.update(
            class_id=class_id,
            **class_data.dict(exclude_unset=True)
        )
        
        return class_obj
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class not found with ID: {class_id}"
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
            detail=f"Failed to update class: {str(e)}"
        )


@router.delete("/{class_id}")
async def delete_class(
    class_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a class
    
    Args:
        class_id: Class ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to delete classes")
        
        # Check if class exists
        existing_class = await class_repo.get_by_id(class_id)
        if not existing_class:
            raise NotFoundError(f"Class not found with ID: {class_id}")
        
        # Check if class has enrollments
        if existing_class.current_enrollment > 0:
            raise ValidationError("Cannot delete class with active enrollments")
        
        # Delete class
        await class_repo.delete(class_id)
        
        return {"message": "Class deleted successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class not found with ID: {class_id}"
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
            detail=f"Failed to delete class: {str(e)}"
        )


@router.post("/{class_id}/activate")
async def activate_class(
    class_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Activate a class
    
    Args:
        class_id: Class ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to activate classes")
        
        await class_repo.update(class_id, is_active=True)
        
        return {"message": "Class activated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate class: {str(e)}"
        )


@router.post("/{class_id}/deactivate")
async def deactivate_class(
    class_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Deactivate a class
    
    Args:
        class_id: Class ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to deactivate classes")
        
        await class_repo.update(class_id, is_active=False)
        
        return {"message": "Class deactivated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate class: {str(e)}"
        )


@router.post("/{class_id}/assign-teacher")
async def assign_teacher_to_class(
    class_id: str,
    teacher_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Assign a teacher to a class
    
    Args:
        class_id: Class ID
        teacher_id: Teacher ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to assign teachers")
        
        # Validate teacher exists
        teacher_exists = await class_repo.validate_teacher(teacher_id)
        if not teacher_exists:
            raise ValidationError("Teacher not found")
        
        # Assign teacher
        await class_repo.assign_teacher(class_id, teacher_id)
        
        return {"message": "Teacher assigned successfully"}
        
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
            detail=f"Failed to assign teacher: {str(e)}"
        )


@router.post("/{class_id}/remove-teacher")
async def remove_teacher_from_class(
    class_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Remove teacher from a class
    
    Args:
        class_id: Class ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to remove teachers")
        
        # Remove teacher
        await class_repo.remove_teacher(class_id)
        
        return {"message": "Teacher removed successfully"}
        
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove teacher: {str(e)}"
        )


@router.post("/{class_id}/assign-schedule")
async def assign_schedule_to_class(
    class_id: str,
    schedule: ScheduleAssignment,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Assign schedule to a class
    
    Args:
        class_id: Class ID
        schedule: Schedule assignment data
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to assign schedules")
        
        # Validate schedule times
        try:
            start_time = time.fromisoformat(schedule.start_time)
            end_time = time.fromisoformat(schedule.end_time)
            
            if start_time >= end_time:
                raise ValidationError("Start time must be before end time")
        except ValueError:
            raise ValidationError("Invalid time format. Use HH:MM format")
        
        # Assign schedule
        await class_repo.assign_schedule(
            class_id=class_id,
            day_of_week=schedule.day_of_week,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            classroom=schedule.classroom,
            is_recurring=schedule.is_recurring
        )
        
        return {"message": "Schedule assigned successfully"}
        
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
            detail=f"Failed to assign schedule: {str(e)}"
        )


@router.get("/{class_id}/students")
async def get_class_students(
    class_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get students in a class
    
    Args:
        class_id: Class ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        credentials: JWT token
        
    Returns:
        List of students in the class
    """
    try:
        students = await class_repo.get_students(class_id, skip, limit)
        return students
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch class students: {str(e)}"
        )


@router.get("/{class_id}/attendance")
async def get_class_attendance(
    class_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get class attendance statistics
    
    Args:
        class_id: Class ID
        start_date: Start date filter (YYYY-MM-DD)
        end_date: End date filter (YYYY-MM-DD)
        credentials: JWT token
        
    Returns:
        Class attendance statistics
    """
    try:
        attendance_stats = await class_repo.get_attendance_stats(class_id, start_date, end_date)
        return attendance_stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch class attendance: {str(e)}"
        )


@router.get("/{class_id}/performance")
async def get_class_performance(
    class_id: str,
    subject_id: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get class performance metrics
    
    Args:
        class_id: Class ID
        subject_id: Filter by subject ID
        semester: Filter by semester
        credentials: JWT token
        
    Returns:
        Class performance metrics
    """
    try:
        performance = await class_repo.get_performance_metrics(class_id, subject_id, semester)
        return performance
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch class performance: {str(e)}"
        )