"""
Attendance Management API Endpoints

This module provides REST API endpoints for attendance management operations:
- CRUD operations for attendance records
- Attendance tracking and monitoring
- Bulk attendance upload
- Attendance analytics and reporting
- Attendance policy enforcement

Author: Edu-Flow Team
"""

from datetime import datetime, date, time
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, File, UploadFile
from pydantic import BaseModel, Field, validator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.security import auth_service
from core.exceptions import ValidationError, NotFoundError, AuthenticationError, AuthorizationError
from infrastructure.repositories.attendance_repository import AttendanceRepository

# Create router
router = APIRouter(prefix="/attendance", tags=["attendance"])

# Security
security = HTTPBearer()

# Repositories
attendance_repo = AttendanceRepository()


# Pydantic models
class AttendanceBase(BaseModel):
    student_id: str = Field(..., min_length=2)
    class_id: str = Field(..., min_length=2)
    attendance_date: date = Field(..., description="Attendance date (YYYY-MM-DD)")
    attendance_type: str = Field(..., description="present, absent, late, excused")
    check_in_time: Optional[time] = Field(None, description="Check-in time")
    check_out_time: Optional[time] = Field(None, description="Check-out time")
    duration_minutes: Optional[int] = Field(None, description="Attendance duration in minutes")
    is_late: bool = Field(False, description="Whether student was late")
    late_minutes: Optional[int] = Field(None, description="Minutes late")
    excused_by: Optional[str] = Field(None, description="Who excused the absence")
    excused_reason: Optional[str] = Field(None, description="Reason for excuse")
    notes: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    attendance_type: Optional[str] = Field(None)
    check_in_time: Optional[time] = Field(None)
    check_out_time: Optional[time] = Field(None)
    duration_minutes: Optional[int] = Field(None)
    is_late: Optional[bool] = Field(None)
    late_minutes: Optional[int] = Field(None)
    excused_by: Optional[str] = Field(None)
    excused_reason: Optional[str] = Field(None)
    notes: Optional[str] = Field(None)


class AttendanceResponse(AttendanceBase):
    id: str
    created_at: datetime
    updated_at: datetime
    recorded_by_id: str
    status: str
    semester: int = 0
    academic_year: str = ""
    subject_code: str = ""
    student_name: str = ""
    class_name: str
    attendance_percentage: float = 0.0
    consecutive_absences: int = 0
    
    class Config:
        from_attributes = True


class AttendanceRecord(BaseModel):
    student_id: str = Field(..., min_length=2)
    attendance_type: str = Field(..., description="present, absent, late, excused")
    check_in_time: Optional[time] = Field(None)
    check_out_time: Optional[time] = Field(None)
    duration_minutes: Optional[int] = Field(None)
    late_minutes: Optional[int] = Field(None)
    excused_by: Optional[str] = Field(None)
    excused_reason: Optional[str] = Field(None)
    notes: Optional[str] = Field(None)


class AttendanceBulkUpload(BaseModel):
    class_id: str = Field(..., min_length=2)
    attendance_date: date = Field(..., description="Attendance date (YYYY-MM-DD)")
    records: List[AttendanceRecord] = Field(..., description="List of attendance records")
    recorded_by_id: str = Field(..., min_length=2)
    batch_reason: Optional[str] = Field(None, description="Reason for bulk update")


class AttendanceStats(BaseModel):
    student_id: str
    student_name: str
    total_classes: int
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    attendance_percentage: float
    consecutive_absences: int
    average_duration: float
    last_attendance_date: Optional[date]
    attendance_trend: List[Dict[str, Any]]


class ClassAttendanceStats(BaseModel):
    class_id: str
    class_name: str
    total_students: int
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    attendance_percentage: float
    attendance_by_day: List[Dict[str, Any]]
    attendance_by_student: List[AttendanceStats]


class AttendancePolicy(BaseModel):
    policy_name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    max_absences: int = Field(..., ge=0, description="Maximum allowed absences")
    max_late: int = Field(..., ge=0, description="Maximum allowed late arrivals")
    excused_absences_count: int = Field(..., ge=0, description="Excused absences allowed")
    consecutive_absences_limit: int = Field(..., ge=0, description="Consecutive absences limit")
    academic_year: str = Field(..., description="Academic year")
    semester: int = Field(..., ge=1, le=12)
    is_active: bool = Field(True)
    enforcement_level: str = Field(..., description="warning, strict, automatic")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AttendancePolicyCreate(AttendancePolicy):
    pass


class AttendancePolicyUpdate(BaseModel):
    policy_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    max_absences: Optional[int] = Field(None, ge=0)
    max_late: Optional[int] = Field(None, ge=0)
    excused_absences_count: Optional[int] = Field(None, ge=0)
    consecutive_absences_limit: Optional[int] = Field(None, ge=0)
    academic_year: Optional[str] = Field(None)
    semester: Optional[int] = Field(None, ge=1, le=12)
    is_active: Optional[bool] = Field(None)
    enforcement_level: Optional[str] = Field(None)


@router.get("/", response_model=List[AttendanceResponse])
async def get_attendance_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    student_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    attendance_date: Optional[date] = Query(None),
    attendance_type: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    is_late: Optional[bool] = Query(None),
    recorded_by: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    Get attendance records with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        student_id: Filter by student ID
        class_id: Filter by class ID
        attendance_date: Filter by attendance date
        attendance_type: Filter by attendance type
        academic_year: Filter by academic year
        semester: Filter by semester
        is_late: Filter by late status
        recorded_by: Filter by recorder ID
        search: Search term in student name or class name
        
    Returns:
        List of attendance records
    """
    try:
        attendance_records = await attendance_repo.get_all(
            skip=skip,
            limit=limit,
            student_id=student_id,
            class_id=class_id,
            attendance_date=attendance_date,
            attendance_type=attendance_type,
            academic_year=academic_year,
            semester=semester,
            is_late=is_late,
            recorded_by=recorded_by,
            search=search
        )
        
        # Add derived information
        for record in attendance_records:
            record.attendance_percentage = await attendance_repo.get_attendance_percentage(
                record.student_id, record.class_id
            )
            record.consecutive_absences = await attendance_repo.get_consecutive_absences(
                record.student_id, record.class_id
            )
            record.semester = await attendance_repo.get_semester(record.class_id)
            record.academic_year = await attendance_repo.get_academic_year(record.class_id)
            record.subject_code = await attendance_repo.get_subject_code(record.class_id)
            record.student_name = await attendance_repo.get_student_name(record.student_id)
            record.class_name = await attendance_repo.get_class_name(record.class_id)
        
        return attendance_records
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch attendance records: {str(e)}"
        )


@router.get("/{attendance_id}", response_model=AttendanceResponse)
async def get_attendance_record(attendance_id: str):
    """
    Get a specific attendance record by ID
    
    Args:
        attendance_id: Attendance record ID
        
    Returns:
        Attendance record details
    """
    try:
        record = await attendance_repo.get_by_id(attendance_id)
        if not record:
            raise NotFoundError(f"Attendance record not found with ID: {attendance_id}")
        
        # Add derived information
        record.attendance_percentage = await attendance_repo.get_attendance_percentage(
            record.student_id, record.class_id
        )
        record.consecutive_absences = await attendance_repo.get_consecutive_absences(
            record.student_id, record.class_id
        )
        record.semester = await attendance_repo.get_semester(record.class_id)
        record.academic_year = await attendance_repo.get_academic_year(record.class_id)
        record.subject_code = await attendance_repo.get_subject_code(record.class_id)
        record.student_name = await attendance_repo.get_student_name(record.student_id)
        record.class_name = await attendance_repo.get_class_name(record.class_id)
        
        return record
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record not found with ID: {attendance_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch attendance record: {str(e)}"
        )


@router.post("/", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def create_attendance_record(
    attendance_data: AttendanceCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new attendance record
    
    Args:
        attendance_data: Attendance data
        credentials: JWT token
        
    Returns:
        Created attendance record
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to create attendance records")
        
        # Validate attendance type
        valid_types = ['present', 'absent', 'late', 'excused']
        if attendance_data.attendance_type not in valid_types:
            raise ValidationError(f"Invalid attendance type. Must be one of: {valid_types}")
        
        # Validate student
        student_exists = await attendance_repo.validate_student(attendance_data.student_id)
        if not student_exists:
            raise ValidationError("Student not found")
        
        # Validate class
        class_exists = await attendance_repo.validate_class(attendance_data.class_id)
        if not class_exists:
            raise ValidationError("Class not found")
        
        # Validate class enrollment
        is_enrolled = await attendance_repo.is_student_enrolled(
            attendance_data.student_id, attendance_data.class_id
        )
        if not is_enrolled:
            raise ValidationError("Student is not enrolled in this class")
        
        # Validate times
        if attendance_data.check_in_time and attendance_data.check_out_time:
            if attendance_data.check_out_time <= attendance_data.check_in_time:
                raise ValidationError("Check-out time must be after check-in time")
        
        # Calculate duration
        if attendance_data.check_in_time and attendance_data.check_out_time:
            duration = (datetime.combine(date.min, attendance_data.check_out_time) - 
                       datetime.combine(date.min, attendance_data.check_in_time)).total_seconds() / 60
            attendance_data.duration_minutes = int(duration)
        
        # Calculate late status
        if attendance_data.check_in_time:
            scheduled_start = await attendance_repo.get_scheduled_class_time(
                attendance_data.class_id, attendance_data.attendance_date
            )
            if scheduled_start and attendance_data.check_in_time > scheduled_start:
                attendance_data.is_late = True
                minutes_late = (datetime.combine(date.min, attendance_data.check_in_time) - 
                              datetime.combine(date.min, scheduled_start)).total_seconds() / 60
                attendance_data.late_minutes = int(minutes_late)
        
        # Create attendance record
        record = await attendance_repo.create(
            student_id=attendance_data.student_id,
            class_id=attendance_data.class_id,
            attendance_date=attendance_data.attendance_date,
            attendance_type=attendance_data.attendance_type,
            check_in_time=attendance_data.check_in_time,
            check_out_time=attendance_data.check_out_time,
            duration_minutes=attendance_data.duration_minutes,
            is_late=attendance_data.is_late,
            late_minutes=attendance_data.late_minutes,
            excused_by=attendance_data.excused_by,
            excused_reason=attendance_data.excused_reason,
            notes=attendance_data.notes,
            metadata=attendance_data.metadata,
            recorded_by_id=auth.get('user_id') or auth.get('id')
        )
        
        return record
        
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
            detail=f"Failed to create attendance record: {str(e)}"
        )


@router.put("/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance_record(
    attendance_id: str,
    attendance_data: AttendanceUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update an attendance record
    
    Args:
        attendance_id: Attendance record ID
        attendance_data: Updated attendance data
        credentials: JWT token
        
    Returns:
        Updated attendance record
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to update attendance records")
        
        # Check if record exists
        existing_record = await attendance_repo.get_by_id(attendance_id)
        if not existing_record:
            raise NotFoundError(f"Attendance record not found with ID: {attendance_id}")
        
        # Validate attendance type if updated
        if attendance_data.attendance_type:
            valid_types = ['present', 'absent', 'late', 'excused']
            if attendance_data.attendance_type not in valid_types:
                raise ValidationError(f"Invalid attendance type. Must be one of: {valid_types}")
        
        # Validate times if updated
        if attendance_data.check_in_time and attendance_data.check_out_time:
            if attendance_data.check_out_time <= attendance_data.check_in_time:
                raise ValidationError("Check-out time must be after check-in time")
        
        # Calculate duration if times updated
        if attendance_data.check_in_time and attendance_data.check_out_time:
            duration = (datetime.combine(date.min, attendance_data.check_out_time) - 
                       datetime.combine(date.min, attendance_data.check_in_time)).total_seconds() / 60
            attendance_data.duration_minutes = int(duration)
        
        # Calculate late status if times updated
        if attendance_data.check_in_time:
            scheduled_start = await attendance_repo.get_scheduled_class_time(
                existing_record.class_id, existing_record.attendance_date
            )
            if scheduled_start and attendance_data.check_in_time > scheduled_start:
                attendance_data.is_late = True
                minutes_late = (datetime.combine(date.min, attendance_data.check_in_time) - 
                              datetime.combine(date.min, scheduled_start)).total_seconds() / 60
                attendance_data.late_minutes = int(minutes_late)
        
        # Update attendance record
        record = await attendance_repo.update(
            attendance_id=attendance_id,
            **attendance_data.dict(exclude_unset=True)
        )
        
        return record
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record not found with ID: {attendance_id}"
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
            detail=f"Failed to update attendance record: {str(e)}"
        )


@router.delete("/{attendance_id}")
async def delete_attendance_record(
    attendance_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete an attendance record
    
    Args:
        attendance_id: Attendance record ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to delete attendance records")
        
        # Check if record exists
        existing_record = await attendance_repo.get_by_id(attendance_id)
        if not existing_record:
            raise NotFoundError(f"Attendance record not found with ID: {attendance_id}")
        
        # Delete attendance record
        await attendance_repo.delete(attendance_id)
        
        return {"message": "Attendance record deleted successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record not found with ID: {attendance_id}"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete attendance record: {str(e)}"
        )


@router.post("/bulk-upload")
async def bulk_upload_attendance(
    upload_data: AttendanceBulkUpload,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Bulk upload attendance records
    
    Args:
        upload_data: Attendance upload data
        credentials: JWT token
        
    Returns:
        Upload result
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to bulk upload attendance")
        
        # Validate class
        class_exists = await attendance_repo.validate_class(upload_data.class_id)
        if not class_exists:
            raise ValidationError("Class not found")
        
        # Validate all students
        for record in upload_data.records:
            student_exists = await attendance_repo.validate_student(record.student_id)
            if not student_exists:
                raise ValidationError(f"Student not found: {record.student_id}")
            
            # Validate enrollment
            is_enrolled = await attendance_repo.is_student_enrolled(
                record.student_id, upload_data.class_id
            )
            if not is_enrolled:
                raise ValidationError(f"Student {record.student_id} is not enrolled in this class")
        
        # Validate attendance types
        valid_types = ['present', 'absent', 'late', 'excused']
        for record in upload_data.records:
            if record.attendance_type not in valid_types:
                raise ValidationError(f"Invalid attendance type for student {record.student_id}")
        
        # Bulk upload attendance
        result = await attendance_repo.bulk_upload(
            class_id=upload_data.class_id,
            attendance_date=upload_data.attendance_date,
            records=upload_data.records,
            recorded_by_id=upload_data.recorded_by_id,
            batch_reason=upload_data.batch_reason
        )
        
        return result
        
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
            detail=f"Failed to bulk upload attendance: {str(e)}"
        )


@router.post("/file-upload")
async def upload_attendance_file(
    file: UploadFile = File(...),
    class_id: str = Query(..., min_length=2),
    attendance_date: date = Query(..., description="Attendance date (YYYY-MM-DD)"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Upload attendance file (CSV/Excel)
    
    Args:
        file: Upload file
        class_id: Class ID
        attendance_date: Attendance date
        credentials: JWT token
        
    Returns:
        Upload result
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to upload attendance files")
        
        # Validate file type
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise ValidationError("Only CSV and Excel files are supported")
        
        # Process file
        result = await attendance_repo.process_attendance_file(
            file=file,
            class_id=class_id,
            attendance_date=attendance_date,
            recorded_by_id=auth.get('user_id') or auth.get('id')
        )
        
        return result
        
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
            detail=f"Failed to process attendance file: {str(e)}"
        )


@router.get("/stats/class/{class_id}")
async def get_class_attendance_stats(
    class_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get attendance statistics for a class
    
    Args:
        class_id: Class ID
        start_date: Start date filter
        end_date: End date filter
        credentials: JWT token
        
    Returns:
        Class attendance statistics
    """
    try:
        stats = await attendance_repo.get_class_attendance_stats(
            class_id=class_id,
            start_date=start_date,
            end_date=end_date
        )
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch class attendance stats: {str(e)}"
        )


@router.get("/stats/student/{student_id}")
async def get_student_attendance_stats(
    student_id: str,
    class_id: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get attendance statistics for a student
    
    Args:
        student_id: Student ID
        class_id: Filter by class ID
        academic_year: Filter by academic year
        semester: Filter by semester
        credentials: JWT token
        
    Returns:
        Student attendance statistics
    """
    try:
        stats = await attendance_repo.get_student_attendance_stats(
            student_id=student_id,
            class_id=class_id,
            academic_year=academic_year,
            semester=semester
        )
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch student attendance stats: {str(e)}"
        )


@router.get("/policies", response_model=List[AttendancePolicy])
async def get_attendance_policies(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get attendance policies
    
    Args:
        academic_year: Filter by academic year
        semester: Filter by semester
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of attendance policies
    """
    try:
        policies = await attendance_repo.get_attendance_policies(
            academic_year=academic_year,
            semester=semester,
            skip=skip,
            limit=limit
        )
        return policies
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch attendance policies: {str(e)}"
        )


@router.post("/policies", response_model=AttendancePolicy, status_code=status.HTTP_201_CREATED)
async def create_attendance_policy(
    policy: AttendancePolicyCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create attendance policy
    
    Args:
        policy: Policy data
        credentials: JWT token
        
    Returns:
        Created policy
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin']:
            raise AuthorizationError("Insufficient permissions to create attendance policies")
        
        # Create policy
        policy_obj = await attendance_repo.create_attendance_policy(
            policy_name=policy.policy_name,
            description=policy.description,
            max_absences=policy.max_absences,
            max_late=policy.max_late,
            excused_absences_count=policy.excused_absences_count,
            consecutive_absences_limit=policy.consecutive_absences_limit,
            academic_year=policy.academic_year,
            semester=policy.semester,
            is_active=policy.is_active,
            enforcement_level=policy.enforcement_level,
            metadata=policy.metadata,
            created_by_id=auth.get('user_id') or auth.get('id')
        )
        
        return policy_obj
        
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create attendance policy: {str(e)}"
        )


@router.get("/violations/policy/{policy_id}")
async def get_attendance_violations(
    policy_id: str,
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get attendance violations based on policy
    
    Args:
        policy_id: Policy ID
        academic_year: Filter by academic year
        semester: Filter by semester
        skip: Number of records to skip
        limit: Maximum number of records to return
        credentials: JWT token
        
    Returns:
        List of attendance violations
    """
    try:
        violations = await attendance_repo.get_attendance_violations(
            policy_id=policy_id,
            academic_year=academic_year,
            semester=semester,
            skip=skip,
            limit=limit
        )
        return violations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch attendance violations: {str(e)}"
        )