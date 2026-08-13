"""
Timetable Entry Management API Endpoints

This module provides REST API endpoints for timetable entry management operations:
- CRUD operations for timetable entries
- Individual entry scheduling and management
- Entry conflict detection and resolution
- Resource allocation for individual entries
- Entry reporting and analytics

Author: Edu-Flow Team
"""

from datetime import datetime, time, date
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field, validator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.security import auth_service
from src.core.exceptions import ValidationError, NotFoundError, AuthenticationError, AuthorizationError
from src.infrastructure.repositories.timetable_entry_repository import TimetableEntryRepository

# Create router
router = APIRouter(prefix="/timetable-entries", tags=["timetable-entries"])

# Security
security = HTTPBearer()

# Repositories
timetable_entry_repo = TimetableEntryRepository()


# Pydantic models
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
    allocated_resources: Dict[str, Any] = Field(default_factory=dict)
    scheduled_dates: List[date] = Field(default_factory=list)
    next_occurrence: Optional[date] = None
    occurrence_count: int = 0
    cancellation_count: int = 0
    
    class Config:
        from_attributes = True


class TimetableEntryOccurrence(BaseModel):
    id: str
    timetable_entry_id: str
    occurrence_date: date
    start_time: time
    end_time: time
    status: str = Field(..., description="scheduled, cancelled, completed")
    is_attended: bool = False
    attendance_count: int = 0
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TimetableEntryConflict(BaseModel):
    id: str
    conflict_type: str = Field(..., description="teacher_conflict, room_conflict, class_conflict")
    conflict_level: str = Field(..., description="low, medium, high")
    conflicting_entries: List[Dict[str, Any]] = Field(..., description="List of conflicting entries")
    suggested_resolutions: List[str] = Field(..., description="Suggested resolutions")
    impact_assessment: Dict[str, Any] = Field(..., description="Impact assessment")
    resolution_priority: int = Field(..., ge=1, le=5)
    can_be_automatically_resolved: bool = False


class ResourceAllocationRequest(BaseModel):
    timetable_entry_id: str = Field(..., min_length=2)
    allocation_date: date = Field(..., description="Allocation date")
    allocated_resources: Dict[str, Any] = Field(..., description="Allocated resources")
    allocation_reason: Optional[str] = Field(None, description="Reason for allocation")
    priority: int = Field(1, ge=1, le=5, description="Allocation priority")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ResourceAllocationResponse(BaseModel):
    allocation_id: str
    timetable_entry_id: str
    allocation_date: date
    allocated_resources: Dict[str, Any]
    allocation_status: str = "pending"
    is_confirmed: bool = False
    confirmation_date: Optional[datetime] = None
    allocation_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


@router.get("/", response_model=List[TimetableEntryResponse])
async def get_timetable_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    timetable_id: Optional[str] = Query(None),
    day_of_week: Optional[str] = Query(None),
    teacher_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    room_id: Optional[str] = Query(None),
    building_id: Optional[str] = Query(None),
    is_recurring: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(None),
    has_conflict: Optional[bool] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    Get timetable entries with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        timetable_id: Filter by timetable ID
        day_of_week: Filter by day of week
        teacher_id: Filter by teacher ID
        class_id: Filter by class ID
        room_id: Filter by room ID
        building_id: Filter by building ID
        is_recurring: Filter by recurring status
        is_active: Filter by active status
        has_conflict: Filter by conflict status
        search: Search term in notes or metadata
        
    Returns:
        List of timetable entries
    """
    try:
        entries = await timetable_entry_repo.get_all(
            skip=skip,
            limit=limit,
            timetable_id=timetable_id,
            day_of_week=day_of_week,
            teacher_id=teacher_id,
            class_id=class_id,
            room_id=room_id,
            building_id=building_id,
            is_recurring=is_recurring,
            is_active=is_active,
            has_conflict=has_conflict,
            search=search
        )
        
        # Add derived information
        for entry in entries:
            entry.duration_minutes = await timetable_entry_repo.get_entry_duration(entry.id)
            entry.has_conflict = await timetable_entry_repo.has_entry_conflict(entry.id)
            entry.resource_utilization = await timetable_entry_repo.get_resource_utilization(entry.id)
            entry.is_allocated = await timetable_entry_repo.is_entry_allocated(entry.id)
            entry.scheduled_dates = await timetable_entry_repo.get_scheduled_dates(entry.id)
            entry.next_occurrence = await timetable_entry_repo.get_next_occurrence(entry.id)
            entry.occurrence_count = await timetable_entry_repo.get_occurrence_count(entry.id)
            entry.cancellation_count = await timetable_entry_repo.get_cancellation_count(entry.id)
        
        return entries
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timetable entries: {str(e)}"
        )


@router.get("/{entry_id}", response_model=TimetableEntryResponse)
async def get_timetable_entry(entry_id: str):
    """
    Get a specific timetable entry by ID
    
    Args:
        entry_id: Timetable entry ID
        
    Returns:
        Timetable entry details
    """
    try:
        entry = await timetable_entry_repo.get_by_id(entry_id)
        if not entry:
            raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
        
        # Add derived information
        entry.duration_minutes = await timetable_entry_repo.get_entry_duration(entry.id)
        entry.has_conflict = await timetable_entry_repo.has_entry_conflict(entry.id)
        entry.resource_utilization = await timetable_entry_repo.get_resource_utilization(entry.id)
        entry.is_allocated = await timetable_entry_repo.is_entry_allocated(entry.id)
        entry.scheduled_dates = await timetable_entry_repo.get_scheduled_dates(entry.id)
        entry.next_occurrence = await timetable_entry_repo.get_next_occurrence(entry.id)
        entry.occurrence_count = await timetable_entry_repo.get_occurrence_count(entry.id)
        entry.cancellation_count = await timetable_entry_repo.get_cancellation_count(entry.id)
        
        return entry
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timetable entry not found with ID: {entry_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timetable entry: {str(e)}"
        )


@router.post("/", response_model=TimetableEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_timetable_entry(
    entry_data: TimetableEntryCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new timetable entry
    
    Args:
        entry_data: Timetable entry data
        credentials: JWT token
        
    Returns:
        Created timetable entry
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to create timetable entries")
        
        # Validate time range
        if entry_data.end_time <= entry_data.start_time:
            raise ValidationError("End time must be after start time")
        
        # Validate resources
        teacher_exists = await timetable_entry_repo.validate_teacher(entry_data.teacher_id)
        if not teacher_exists:
            raise ValidationError("Teacher not found")
        
        room_exists = await timetable_entry_repo.validate_room(entry_data.room_id)
        if not room_exists:
            raise ValidationError("Room not found")
        
        class_exists = await timetable_entry_repo.validate_class(entry_data.class_id)
        if not class_exists:
            raise ValidationError("Class not found")
        
        subject_exists = await timetable_entry_repo.validate_subject(entry_data.subject_id)
        if not subject_exists:
            raise ValidationError("Subject not found")
        
        # Validate frequency
        if entry_data.frequency < 1 or entry_data.frequency > 52:
            raise ValidationError("Frequency must be between 1 and 52")
        
        # Validate priority
        if entry_data.priority < 1 or entry_data.priority > 5:
            raise ValidationError("Priority must be between 1 and 5")
        
        # Check for conflicts
        conflict_check = await timetable_entry_repo.check_entry_conflicts(entry_data)
        
        if conflict_check['has_conflict']:
            raise ValidationError(f"Schedule conflict detected: {conflict_check['conflict_details']}")
        
        # Create timetable entry
        entry = await timetable_entry_repo.create(
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
        entry.duration_minutes = await timetable_entry_repo.get_entry_duration(entry.id)
        entry.has_conflict = await timetable_entry_repo.has_entry_conflict(entry.id)
        entry.resource_utilization = await timetable_entry_repo.get_resource_utilization(entry.id)
        entry.is_allocated = await timetable_entry_repo.is_entry_allocated(entry.id)
        entry.scheduled_dates = await timetable_entry_repo.get_scheduled_dates(entry.id)
        entry.next_occurrence = await timetable_entry_repo.get_next_occurrence(entry.id)
        entry.occurrence_count = await timetable_entry_repo.get_occurrence_count(entry.id)
        entry.cancellation_count = await timetable_entry_repo.get_cancellation_count(entry.id)
        
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
            detail=f"Failed to create timetable entry: {str(e)}"
        )


@router.put("/{entry_id}", response_model=TimetableEntryResponse)
async def update_timetable_entry(
    entry_id: str,
    entry_data: TimetableEntryUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update a timetable entry
    
    Args:
        entry_id: Timetable entry ID
        entry_data: Updated timetable entry data
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
        existing_entry = await timetable_entry_repo.get_by_id(entry_id)
        if not existing_entry:
            raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
        
        # Validate time range if updated
        if entry_data.start_time and entry_data.end_time:
            if entry_data.end_time <= entry_data.start_time:
                raise ValidationError("End time must be after start time")
        
        # Validate resources if updated
        if entry_data.teacher_id:
            teacher_exists = await timetable_entry_repo.validate_teacher(entry_data.teacher_id)
            if not teacher_exists:
                raise ValidationError("Teacher not found")
        
        if entry_data.room_id:
            room_exists = await timetable_entry_repo.validate_room(entry_data.room_id)
            if not room_exists:
                raise ValidationError("Room not found")
        
        if entry_data.class_id:
            class_exists = await timetable_entry_repo.validate_class(entry_data.class_id)
            if not class_exists:
                raise ValidationError("Class not found")
        
        if entry_data.subject_id:
            subject_exists = await timetable_entry_repo.validate_subject(entry_data.subject_id)
            if not subject_exists:
                raise ValidationError("Subject not found")
        
        # Validate frequency if updated
        if entry_data.frequency is not None:
            if entry_data.frequency < 1 or entry_data.frequency > 52:
                raise ValidationError("Frequency must be between 1 and 52")
        
        # Validate priority if updated
        if entry_data.priority is not None:
            if entry_data.priority < 1 or entry_data.priority > 5:
                raise ValidationError("Priority must be between 1 and 5")
        
        # Update timetable entry
        entry = await timetable_entry_repo.update(
            entry_id=entry_id,
            **entry_data.dict(exclude_unset=True)
        )
        
        # Add derived information
        entry.duration_minutes = await timetable_entry_repo.get_entry_duration(entry.id)
        entry.has_conflict = await timetable_entry_repo.has_entry_conflict(entry.id)
        entry.resource_utilization = await timetable_entry_repo.get_resource_utilization(entry.id)
        entry.is_allocated = await timetable_entry_repo.is_entry_allocated(entry.id)
        entry.scheduled_dates = await timetable_entry_repo.get_scheduled_dates(entry.id)
        entry.next_occurrence = await timetable_entry_repo.get_next_occurrence(entry.id)
        entry.occurrence_count = await timetable_entry_repo.get_occurrence_count(entry.id)
        entry.cancellation_count = await timetable_entry_repo.get_cancellation_count(entry.id)
        
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


@router.delete("/{entry_id}")
async def delete_timetable_entry(
    entry_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a timetable entry
    
    Args:
        entry_id: Timetable entry ID
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
        existing_entry = await timetable_entry_repo.get_by_id(entry_id)
        if not existing_entry:
            raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
        
        # Delete timetable entry
        await timetable_entry_repo.delete(entry_id)
        
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


@router.get("/{entry_id}/occurrences")
async def get_timetable_entry_occurrences(
    entry_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get timetable entry occurrences
    
    Args:
        entry_id: Timetable entry ID
        start_date: Start date filter
        end_date: End date filter
        status: Filter by status
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of timetable entry occurrences
    """
    try:
        occurrences = await timetable_entry_repo.get_occurrences(
            entry_id=entry_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
            skip=skip,
            limit=limit
        )
        return occurrences
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timetable entry occurrences: {str(e)}"
        )


@router.get("/{entry_id}/conflicts")
async def get_timetable_entry_conflicts(
    entry_id: str,
    conflict_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get timetable entry conflicts
    
    Args:
        entry_id: Timetable entry ID
        conflict_type: Filter by conflict type
        severity: Filter by severity level
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of timetable entry conflicts
    """
    try:
        conflicts = await timetable_entry_repo.get_entry_conflicts(
            entry_id=entry_id,
            conflict_type=conflict_type,
            severity=severity,
            skip=skip,
            limit=limit
        )
        return conflicts
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timetable entry conflicts: {str(e)}"
        )


@router.post("/{entry_id}/allocate-resources")
async def allocate_resources(
    entry_id: str,
    allocation_request: ResourceAllocationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Allocate resources to a timetable entry
    
    Args:
        entry_id: Timetable entry ID
        allocation_request: Resource allocation request
        credentials: JWT token
        
    Returns:
        Resource allocation result
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to allocate resources")
        
        # Check if entry exists
        existing_entry = await timetable_entry_repo.get_by_id(entry_id)
        if not existing_entry:
            raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
        
        # Allocate resources
        allocation = await timetable_entry_repo.allocate_resources(
            entry_id=entry_id,
            allocation_date=allocation_request.allocation_date,
            allocated_resources=allocation_request.allocated_resources,
            allocation_reason=allocation_request.allocation_reason,
            priority=allocation_request.priority,
            metadata=allocation_request.metadata,
            allocated_by_id=auth.get('user_id') or auth.get('id')
        )
        
        return allocation
        
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
            detail=f"Failed to allocate resources: {str(e)}"
        )


@router.post("/{entry_id}/confirm-allocation/{allocation_id}")
async def confirm_resource_allocation(
    entry_id: str,
    allocation_id: str,
    confirmation_notes: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Confirm resource allocation
    
    Args:
        entry_id: Timetable entry ID
        allocation_id: Allocation ID
        confirmation_notes: Confirmation notes
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to confirm allocations")
        
        # Confirm allocation
        await timetable_entry_repo.confirm_allocation(
            entry_id=entry_id,
            allocation_id=allocation_id,
            confirmed_by_id=auth.get('user_id') or auth.get('id'),
            confirmation_notes=confirmation_notes
        )
        
        return {"message": "Resource allocation confirmed successfully"}
        
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm resource allocation: {str(e)}"
        )


@router.post("/{entry_id}/cancel-occurrence")
async def cancel_occurrence(
    entry_id: str,
    occurrence_date: date,
    cancellation_reason: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Cancel a specific occurrence of a timetable entry
    
    Args:
        entry_id: Timetable entry ID
        occurrence_date: Occurrence date to cancel
        cancellation_reason: Reason for cancellation
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to cancel occurrences")
        
        # Cancel occurrence
        await timetable_entry_repo.cancel_occurrence(
            entry_id=entry_id,
            occurrence_date=occurrence_date,
            cancelled_by_id=auth.get('user_id') or auth.get('id'),
            cancellation_reason=cancellation_reason
        )
        
        return {"message": "Occurrence cancelled successfully"}
        
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel occurrence: {str(e)}"
        )


@router.get("/{entry_id}/analytics")
async def get_timetable_entry_analytics(
    entry_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get timetable entry analytics
    
    Args:
        entry_id: Timetable entry ID
        start_date: Start date filter
        end_date: End date filter
        credentials: JWT token
        
    Returns:
        Timetable entry analytics
    """
    try:
        analytics = await timetable_entry_repo.get_entry_analytics(
            entry_id=entry_id,
            start_date=start_date,
            end_date=end_date
        )
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timetable entry analytics: {str(e)}"
        )


@router.get("/analytics/teacher/{teacher_id}")
async def get_teacher_schedule_analytics(
    teacher_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get teacher schedule analytics
    
    Args:
        teacher_id: Teacher ID
        start_date: Start date filter
        end_date: End date filter
        skip: Number of records to skip
        limit: Maximum number of records to return
        credentials: JWT token
        
    Returns:
        Teacher schedule analytics
    """
    try:
        analytics = await timetable_entry_repo.get_teacher_schedule_analytics(
            teacher_id=teacher_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch teacher schedule analytics: {str(e)}"
        )


@router.get("/analytics/room/{room_id}")
async def get_room_usage_analytics(
    room_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get room usage analytics
    
    Args:
        room_id: Room ID
        start_date: Start date filter
        end_date: End date filter
        skip: Number of records to skip
        limit: Maximum number of records to return
        credentials: JWT token
        
    Returns:
        Room usage analytics
    """
    try:
        analytics = await timetable_entry_repo.get_room_usage_analytics(
            room_id=room_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch room usage analytics: {str(e)}"
        )