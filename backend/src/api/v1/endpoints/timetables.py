"""
Timetable Management API Endpoints

This module provides REST API endpoints for timetable management operations:
- CRUD operations for timetables
- Timetable generation and optimization
- Scheduling conflicts detection
- Resource allocation for timetables
- Timetable reporting and analytics

Author: Edu-Flow Team
"""

from datetime import datetime, time, date
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field, validator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.security import auth_service
from core.exceptions import ValidationError, NotFoundError, AuthenticationError, AuthorizationError
from infrastructure.repositories.timetable_repository import TimetableRepository

# Create router
router = APIRouter(prefix="/timetables", tags=["timetables"])

# Security
security = HTTPBearer()

# Repositories
timetable_repo = TimetableRepository()


# Pydantic models
class TimetableBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    academic_year: str = Field(..., min_length=4, max_length=10)
    semester: int = Field(..., ge=1, le=12)
    start_date: date = Field(..., description="Timetable start date")
    end_date: date = Field(..., description="Timetable end date")
    is_active: bool = Field(True)
    is_published: bool = Field(False)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TimetableCreate(TimetableBase):
    pass


class TimetableUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    academic_year: Optional[str] = Field(None, min_length=4, max_length=10)
    semester: Optional[int] = Field(None, ge=1, le=12)
    start_date: Optional[date] = Field(None)
    end_date: Optional[date] = Field(None)
    is_active: Optional[bool] = Field(None)
    is_published: Optional[bool] = Field(None)


class TimetableResponse(TimetableBase):
    id: str
    created_at: datetime
    updated_at: datetime
    created_by_id: str
    published_at: Optional[datetime]
    total_classes: int = 0
    total_resources: int = 0
    conflict_count: int = 0
    generation_status: str = "draft"
    schedule_version: str = "1.0"
    last_optimized: Optional[datetime]
    
    class Config:
        from_attributes = True


class TimetableEntryBase(BaseModel):
    timetable_id: str = Field(..., min_length=2)
    day_of_week: str = Field(..., description="Monday, Tuesday, etc.")
    start_time: time = Field(..., description="Start time (HH:MM)")
    end_time: time = Field(..., description="End time (HH:MM)")
    class_id: str = Field(..., min_length=2)
    subject_id: str = Field(..., min_length=2)
    teacher_id: str = Field(..., min_length=2)
    room_id: str = Field(..., min_length=2)
    building_id: str = Field(..., min_length=2)
    is_recurring: bool = Field(True, description="Whether the schedule recurs weekly")
    frequency: int = Field(1, ge=1, le=52, description="Frequency for non-recurring schedules")
    priority: int = Field(1, ge=1, le=5, description="Schedule priority")
    notes: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TimetableEntryCreate(TimetableEntryBase):
    pass


class TimetableEntryUpdate(BaseModel):
    timetable_id: Optional[str] = Field(None, min_length=2)
    day_of_week: Optional[str] = Field(None)
    start_time: Optional[time] = Field(None)
    end_time: Optional[time] = Field(None)
    class_id: Optional[str] = Field(None, min_length=2)
    subject_id: Optional[str] = Field(None, min_length=2)
    teacher_id: Optional[str] = Field(None, min_length=2)
    room_id: Optional[str] = Field(None, min_length=2)
    building_id: Optional[str] = Field(None, min_length=2)
    is_recurring: Optional[bool] = Field(None)
    frequency: Optional[int] = Field(None, ge=1, le=52)
    priority: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)


class TimetableEntryResponse(TimetableEntryBase):
    id: str
    created_at: datetime
    updated_at: datetime
    created_by_id: str
    duration_minutes: int = 0
    has_conflict: bool = False
    conflict_type: Optional[str] = None
    is_allocated: bool = False
    allocation_status: str = "pending"
    resource_utilization: float = 0.0
    
    class Config:
        from_attributes = True


class TimetableConflict(BaseModel):
    id: str
    conflict_type: str = Field(..., description="teacher_conflict, room_conflict, class_conflict")
    conflict_level: str = Field(..., description="low, medium, high")
    affected_entries: List[Dict[str, Any]] = Field(..., description="List of conflicting entries")
    suggested_resolutions: List[str] = Field(..., description="Suggested resolutions")
    impact_assessment: Dict[str, Any] = Field(..., description="Impact assessment")
    resolution_priority: int = Field(..., ge=1, le=5)


class TimetableOptimizationRequest(BaseModel):
    timetable_id: str = Field(..., min_length=2)
    optimization_objective: str = Field(..., description="minimize_conflicts, balance_load, optimize_space")
    constraints: Dict[str, Any] = Field(..., description="Optimization constraints")
    priority_weights: Optional[Dict[str, float]] = Field(None, description="Priority weights")
    max_iterations: Optional[int] = Field(1000, ge=1, le=10000, description="Maximum optimization iterations")
    timeout_seconds: Optional[int] = Field(300, ge=1, le=3600, description="Optimization timeout in seconds")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TimetableStats(BaseModel):
    timetable_id: str
    timetable_name: str
    total_entries: int
    active_entries: int
    conflict_count: int
    teacher_utilization: Dict[str, float]
    room_utilization: Dict[str, float]
    class_schedule_distribution: Dict[str, int]
    time_slot_distribution: Dict[str, int]
    load_balance_index: float
    space_efficiency: float
    quality_score: float


@router.get("/", response_model=List[TimetableResponse])
async def get_timetables(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_published: Optional[bool] = Query(None),
    generation_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    Get all timetables with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        academic_year: Filter by academic year
        semester: Filter by semester
        is_active: Filter by active status
        is_published: Filter by published status
        generation_status: Filter by generation status
        search: Search term in name or description
        
    Returns:
        List of timetables
    """
    try:
        timetables = await timetable_repo.get_all(
            skip=skip,
            limit=limit,
            academic_year=academic_year,
            semester=semester,
            is_active=is_active,
            is_published=is_published,
            generation_status=generation_status,
            search=search
        )
        
        # Add derived information
        for timetable in timetables:
            timetable.total_classes = await timetable_repo.get_total_classes(timetable.id)
            timetable.total_resources = await timetable_repo.get_total_resources(timetable.id)
            timetable.conflict_count = await timetable_repo.get_conflict_count(timetable.id)
            timetable.last_optimized = await timetable_repo.get_last_optimized(timetable.id)
        
        return timetables
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timetables: {str(e)}"
        )


@router.get("/{timetable_id}", response_model=TimetableResponse)
async def get_timetable(timetable_id: str):
    """
    Get a specific timetable by ID
    
    Args:
        timetable_id: Timetable ID
        
    Returns:
        Timetable details
    """
    try:
        timetable = await timetable_repo.get_by_id(timetable_id)
        if not timetable:
            raise NotFoundError(f"Timetable not found with ID: {timetable_id}")
        
        # Add derived information
        timetable.total_classes = await timetable_repo.get_total_classes(timetable_id)
        timetable.total_resources = await timetable_repo.get_total_resources(timetable_id)
        timetable.conflict_count = await timetable_repo.get_conflict_count(timetable_id)
        timetable.last_optimized = await timetable_repo.get_last_optimized(timetable_id)
        
        return timetable
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timetable not found with ID: {timetable_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timetable: {str(e)}"
        )


@router.post("/", response_model=TimetableResponse, status_code=status.HTTP_201_CREATED)
async def create_timetable(
    timetable_data: TimetableCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new timetable
    
    Args:
        timetable_data: Timetable data
        credentials: JWT token
        
    Returns:
        Created timetable
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to create timetables")
        
        # Validate dates
        if timetable_data.end_date <= timetable_data.start_date:
            raise ValidationError("End date must be after start date")
        
        # Validate academic year format
        if not timetable_data.academic_year.replace('-', '').isdigit() or len(timetable_data.academic_year) != 9:
            raise ValidationError("Academic year must be in format YYYY-YYYY")
        
        # Create timetable
        timetable = await timetable_repo.create(
            name=timetable_data.name,
            description=timetable_data.description,
            academic_year=timetable_data.academic_year,
            semester=timetable_data.semester,
            start_date=timetable_data.start_date,
            end_date=timetable_data.end_date,
            is_active=timetable_data.is_active,
            is_published=timetable_data.is_published,
            metadata=timetable_data.metadata,
            created_by_id=auth.get('user_id') or auth.get('id')
        )
        
        return timetable
        
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
            detail=f"Failed to create timetable: {str(e)}"
        )


@router.put("/{timetable_id}", response_model=TimetableResponse)
async def update_timetable(
    timetable_id: str,
    timetable_data: TimetableUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update a timetable
    
    Args:
        timetable_id: Timetable ID
        timetable_data: Updated timetable data
        credentials: JWT token
        
    Returns:
        Updated timetable
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to update timetables")
        
        # Check if timetable exists
        existing_timetable = await timetable_repo.get_by_id(timetable_id)
        if not existing_timetable:
            raise NotFoundError(f"Timetable not found with ID: {timetable_id}")
        
        # Validate dates if updated
        if timetable_data.start_date and timetable_data.end_date:
            if timetable_data.end_date <= timetable_data.start_date:
                raise ValidationError("End date must be after start date")
        
        # Update timetable
        timetable = await timetable_repo.update(
            timetable_id=timetable_id,
            **timetable_data.dict(exclude_unset=True)
        )
        
        return timetable
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timetable not found with ID: {timetable_id}"
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
            detail=f"Failed to update timetable: {str(e)}"
        )


@router.delete("/{timetable_id}")
async def delete_timetable(
    timetable_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a timetable
    
    Args:
        timetable_id: Timetable ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to delete timetables")
        
        # Check if timetable exists
        existing_timetable = await timetable_repo.get_by_id(timetable_id)
        if not existing_timetable:
            raise NotFoundError(f"Timetable not found with ID: {timetable_id}")
        
        # Check if timetable has entries
        has_entries = await timetable_repo.has_entries(timetable_id)
        if has_entries:
            raise ValidationError("Cannot delete timetable with existing entries")
        
        # Delete timetable
        await timetable_repo.delete(timetable_id)
        
        return {"message": "Timetable deleted successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timetable not found with ID: {timetable_id}"
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
            detail=f"Failed to delete timetable: {str(e)}"
        )


@router.post("/{timetable_id}/publish")
async def publish_timetable(
    timetable_id: str,
    publish_date: Optional[datetime] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Publish a timetable
    
    Args:
        timetable_id: Timetable ID
        publish_date: Publish date (optional)
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to publish timetables")
        
        # Check for conflicts before publishing
        conflicts = await timetable_repo.get_timetable_conflicts(timetable_id)
        if conflicts:
            raise ValidationError(f"Cannot publish timetable with {len(conflicts)} unresolved conflicts")
        
        # Publish timetable
        await timetable_repo.publish_timetable(timetable_id, publish_date)
        
        return {"message": "Timetable published successfully"}
        
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
            detail=f"Failed to publish timetable: {str(e)}"
        )


@router.get("/{timetable_id}/entries")
async def get_timetable_entries(
    timetable_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    day_of_week: Optional[str] = Query(None),
    teacher_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    room_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    has_conflict: Optional[bool] = Query(None)
):
    """
    Get timetable entries with optional filtering
    
    Args:
        timetable_id: Timetable ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        day_of_week: Filter by day of week
        teacher_id: Filter by teacher ID
        class_id: Filter by class ID
        room_id: Filter by room ID
        is_active: Filter by active status
        has_conflict: Filter by conflict status
        
    Returns:
        List of timetable entries
    """
    try:
        entries = await timetable_repo.get_timetable_entries(
            timetable_id=timetable_id,
            skip=skip,
            limit=limit,
            day_of_week=day_of_week,
            teacher_id=teacher_id,
            class_id=class_id,
            room_id=room_id,
            is_active=is_active,
            has_conflict=has_conflict
        )
        
        # Add derived information
        for entry in entries:
            entry.duration_minutes = await timetable_repo.get_entry_duration(entry.id)
            entry.has_conflict = await timetable_repo.has_entry_conflict(entry.id)
            entry.resource_utilization = await timetable_repo.get_resource_utilization(entry.id)
            entry.is_allocated = await timetable_repo.is_entry_allocated(entry.id)
        
        return entries
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timetable entries: {str(e)}"
        )


@router.post("/{timetable_id}/entries", response_model=TimetableEntryResponse, status_code=status.HTTP_201_CREATED)
async def add_timetable_entry(
    timetable_id: str,
    entry_data: TimetableEntryCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Add an entry to a timetable
    
    Args:
        timetable_id: Timetable ID
        entry_data: Entry data
        credentials: JWT token
        
    Returns:
        Created timetable entry
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to add timetable entries")
        
        # Validate time range
        if entry_data.end_time <= entry_data.start_time:
            raise ValidationError("End time must be after start time")
        
        # Validate resources
        teacher_exists = await timetable_repo.validate_teacher(entry_data.teacher_id)
        if not teacher_exists:
            raise ValidationError("Teacher not found")
        
        room_exists = await timetable_repo.validate_room(entry_data.room_id)
        if not room_exists:
            raise ValidationError("Room not found")
        
        class_exists = await timetable_repo.validate_class(entry_data.class_id)
        if not class_exists:
            raise ValidationError("Class not found")
        
        subject_exists = await timetable_repo.validate_subject(entry_data.subject_id)
        if not subject_exists:
            raise ValidationError("Subject not found")
        
        # Check for conflicts
        conflict_check = await timetable_repo.check_entry_conflicts(
            timetable_id, entry_data
        )
        
        if conflict_check['has_conflict']:
            raise ValidationError(f"Schedule conflict detected: {conflict_check['conflict_details']}")
        
        # Create entry
        entry = await timetable_repo.create_entry(
            timetable_id=entry_data.timetable_id,
            day_of_week=entry_data.day_of_week,
            start_time=entry_data.start_time,
            end_time=entry_data.end_time,
            class_id=entry_data.class_id,
            subject_id=entry_data.subject_id,
            teacher_id=entry_data.teacher_id,
            room_id=entry_data.room_id,
            building_id=entry_data.building_id,
            is_recurring=entry_data.is_recurring,
            frequency=entry_data.frequency,
            priority=entry_data.priority,
            notes=entry_data.notes,
            metadata=entry_data.metadata,
            created_by_id=auth.get('user_id') or auth.get('id')
        )
        
        # Add derived information
        entry.duration_minutes = await timetable_repo.get_entry_duration(entry.id)
        entry.has_conflict = await timetable_repo.has_entry_conflict(entry.id)
        entry.resource_utilization = await timetable_repo.get_resource_utilization(entry.id)
        entry.is_allocated = await timetable_repo.is_entry_allocated(entry.id)
        
        return entry
        
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
            detail=f"Failed to add timetable entry: {str(e)}"
        )


@router.put("/{timetable_id}/entries/{entry_id}", response_model=TimetableEntryResponse)
async def update_timetable_entry(
    timetable_id: str,
    entry_id: str,
    entry_data: TimetableEntryUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update a timetable entry
    
    Args:
        timetable_id: Timetable ID
        entry_id: Entry ID
        entry_data: Updated entry data
        credentials: JWT token
        
    Returns:
        Updated timetable entry
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to update timetable entries")
        
        # Check if entry exists
        existing_entry = await timetable_repo.get_entry_by_id(entry_id)
        if not existing_entry:
            raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
        
        # Validate time range if updated
        if entry_data.start_time and entry_data.end_time:
            if entry_data.end_time <= entry_data.start_time:
                raise ValidationError("End time must be after start time")
        
        # Validate resources if updated
        if entry_data.teacher_id:
            teacher_exists = await timetable_repo.validate_teacher(entry_data.teacher_id)
            if not teacher_exists:
                raise ValidationError("Teacher not found")
        
        if entry_data.room_id:
            room_exists = await timetable_repo.validate_room(entry_data.room_id)
            if not room_exists:
                raise ValidationError("Room not found")
        
        if entry_data.class_id:
            class_exists = await timetable_repo.validate_class(entry_data.class_id)
            if not class_exists:
                raise ValidationError("Class not found")
        
        if entry_data.subject_id:
            subject_exists = await timetable_repo.validate_subject(entry_data.subject_id)
            if not subject_exists:
                raise ValidationError("Subject not found")
        
        # Update entry
        entry = await timetable_repo.update_entry(
            timetable_id=timetable_id,
            entry_id=entry_id,
            **entry_data.dict(exclude_unset=True)
        )
        
        # Add derived information
        entry.duration_minutes = await timetable_repo.get_entry_duration(entry.id)
        entry.has_conflict = await timetable_repo.has_entry_conflict(entry.id)
        entry.resource_utilization = await timetable_repo.get_resource_utilization(entry.id)
        entry.is_allocated = await timetable_repo.is_entry_allocated(entry.id)
        
        return entry
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timetable entry not found with ID: {entry_id}"
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
            detail=f"Failed to update timetable entry: {str(e)}"
        )


@router.delete("/{timetable_id}/entries/{entry_id}")
async def delete_timetable_entry(
    timetable_id: str,
    entry_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a timetable entry
    
    Args:
        timetable_id: Timetable ID
        entry_id: Entry ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to delete timetable entries")
        
        # Check if entry exists
        existing_entry = await timetable_repo.get_entry_by_id(entry_id)
        if not existing_entry:
            raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
        
        # Delete entry
        await timetable_repo.delete_entry(entry_id)
        
        return {"message": "Timetable entry deleted successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timetable entry not found with ID: {entry_id}"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete timetable entry: {str(e)}"
        )


@router.post("/{timetable_id}/optimize")
async def optimize_timetable(
    timetable_id: str,
    optimization_request: TimetableOptimizationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Optimize a timetable
    
    Args:
        timetable_id: Timetable ID
        optimization_request: Optimization request
        credentials: JWT token
        
    Returns:
        Optimization result
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to optimize timetables")
        
        # Check if timetable exists
        existing_timetable = await timetable_repo.get_by_id(timetable_id)
        if not existing_timetable:
            raise NotFoundError(f"Timetable not found with ID: {timetable_id}")
        
        # Optimize timetable
        result = await timetable_repo.optimize_timetable(
            timetable_id=timetable_id,
            optimization_objective=optimization_request.optimization_objective,
            constraints=optimization_request.constraints,
            priority_weights=optimization_request.priority_weights,
            max_iterations=optimization_request.max_iterations,
            timeout_seconds=optimization_request.timeout_seconds,
            metadata=optimization_request.metadata
        )
        
        return result
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timetable not found with ID: {timetable_id}"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize timetable: {str(e)}"
        )


@router.get("/{timetable_id}/conflicts")
async def get_timetable_conflicts(
    timetable_id: str,
    conflict_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get timetable conflicts
    
    Args:
        timetable_id: Timetable ID
        conflict_type: Filter by conflict type
        severity: Filter by severity level
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of timetable conflicts
    """
    try:
        conflicts = await timetable_repo.get_timetable_conflicts(
            timetable_id=timetable_id,
            conflict_type=conflict_type,
            severity=severity,
            skip=skip,
            limit=limit
        )
        return conflicts
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timetable conflicts: {str(e)}"
        )


@router.get("/{timetable_id}/stats", response_model=TimetableStats)
async def get_timetable_stats(
    timetable_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """
    Get timetable statistics
    
    Args:
        timetable_id: Timetable ID
        start_date: Start date filter
        end_date: End date filter
        
    Returns:
        Timetable statistics
    """
    try:
        stats = await timetable_repo.get_timetable_stats(
            timetable_id=timetable_id,
            start_date=start_date,
            end_date=end_date
        )
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timetable stats: {str(e)}"
        )