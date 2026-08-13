"""
Room Management API Endpoints

This module provides REST API endpoints for room management operations:
- CRUD operations for rooms
- Room scheduling and allocation
- Room capacity and utilization
- Room features and amenities
- Room reporting and analytics

Author: Edu-Flow Team
"""

from datetime import datetime, time
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, File, UploadFile
from pydantic import BaseModel, Field, validator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.security import auth_service
from src.core.exceptions import ValidationError, NotFoundError, AuthenticationError, AuthorizationError
from src.infrastructure.repositories.room_repository import RoomRepository

# Create router
router = APIRouter(prefix="/rooms", tags=["rooms"])

# Security
security = HTTPBearer()

# Repositories
room_repo = RoomRepository()


# Pydantic models
class RoomBase(BaseModel):
    name: str = Field(..., max_length=100)
    room_code: str = Field(..., min_length=1, max_length=10, description="Room code")
    building_id: str = Field(..., min_length=2, description="Building ID")
    floor: int = Field(..., ge=1, le=20, description="Floor number")
    room_type: str = Field(..., description="lecture, lab, seminar, office, meeting, storage")
    capacity: int = Field(..., ge=1, le=500, description="Room capacity")
    amenities: List[str] = Field(..., description="List of amenities")
    equipment: Dict[str, Any] = Field(..., description="Equipment information")
    features: List[str] = Field(..., description="Room features")
    availability: Dict[str, Any] = Field(..., description="Availability schedule")
    usage_policy: str = Field(..., max_length=1000, description="Usage policy")
    is_active: bool = Field(True)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    room_code: Optional[str] = Field(None, min_length=1, max_length=10)
    building_id: Optional[str] = Field(None, min_length=2)
    floor: Optional[int] = Field(None, ge=1, le=20)
    room_type: Optional[str] = Field(None)
    capacity: Optional[int] = Field(None, ge=1, le=500)
    amenities: Optional[List[str]] = Field(None)
    equipment: Optional[Dict[str, Any]] = Field(None)
    features: Optional[List[str]] = Field(None)
    availability: Optional[Dict[str, Any]] = Field(None)
    usage_policy: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = Field(None)


class RoomResponse(RoomBase):
    id: str
    created_at: datetime
    updated_at: datetime
    total_bookings: int = 0
    active_bookings: int = 0
    current_utilization: float = 0.0
    peak_utilization_hours: Dict[str, float] = Field(default_factory=dict)
    maintenance_schedule: Optional[Dict[str, Any]] = None
    next_maintenance: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    equipment_count: int = 0
    is_compliant: bool = True
    compliance_score: float = 100.0
    booking_rules: Dict[str, Any] = Field(default_factory=dict)
    waiting_list_count: int = 0
    
    class Config:
        from_attributes = True


class RoomBooking(BaseModel):
    room_id: str = Field(..., min_length=2)
    class_id: str = Field(..., min_length=2)
    subject_id: str = Field(..., min_length=2)
    teacher_id: str = Field(..., min_length=2)
    start_time: datetime = Field(..., description="Booking start time")
    end_time: datetime = Field(..., description="Booking end time")
    booking_type: str = Field(..., description="regular, special, exam, event")
    purpose: str = Field(..., max_length=500, description="Purpose of booking")
    equipment_required: Optional[List[str]] = Field(None, description="Required equipment")
    participants_count: int = Field(..., ge=1, le=500, description="Number of participants")
    priority: int = Field(1, ge=1, le=5, description="Booking priority")
    booking_notes: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RoomBookingResponse(RoomBooking):
    id: str
    created_at: datetime
    updated_at: datetime
    booking_status: str = "pending"
    is_confirmed: bool = False
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    rescheduled_count: int = 0
    equipment_available: bool = True
    capacity_available: bool = True
    can_be_rescheduled: bool = True
    waiting_list_position: int = 0
    
    class Config:
        from_attributes = True


class RoomMaintenance(BaseModel):
    room_id: str = Field(..., min_length=2)
    maintenance_type: str = Field(..., description="preventive, corrective, emergency")
    description: str = Field(..., max_length=500)
    scheduled_date: datetime = Field(..., description="Maintenance date")
    estimated_duration: int = Field(..., ge=1, description="Duration in hours")
    maintenance_team: List[str] = Field(..., description="Maintenance team members")
    equipment_involved: List[str] = Field(..., description="Equipment involved")
    cost_estimate: float = Field(..., ge=0)
    actual_cost: Optional[float] = None
    status: str = Field(..., description="scheduled, in_progress, completed, cancelled")
    completion_date: Optional[datetime] = None
    maintenance_notes: Optional[str] = Field(None, max_length=1000)
    safety_measures: List[str] = Field(..., description="Safety measures taken")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RoomStats(BaseModel):
    room_id: str
    room_name: str
    total_bookings: int
    active_bookings: int
    average_utilization: float
    peak_utilization_hours: Dict[str, float]
    equipment_utilization: Dict[str, float]
    maintenance_frequency: float
    compliance_score: float
    booking_cancellation_rate: float
    booking_reschedule_rate: float
    popular_equipment: List[str]
    waiting_list_stats: Dict[str, int]


@router.get("/", response_model=List[RoomResponse])
async def get_rooms(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    building_id: Optional[str] = Query(None),
    room_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    Get all rooms with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        building_id: Filter by building ID
        room_type: Filter by room type
        is_active: Filter by active status
        search: Search term in name or room code
        
    Returns:
        List of rooms
    """
    try:
        rooms = await room_repo.get_all(
            skip=skip,
            limit=limit,
            building_id=building_id,
            room_type=room_type,
            is_active=is_active,
            search=search
        )
        
        # Add derived information
        for room in rooms:
            room.current_utilization = await room_repo.get_current_utilization(room.id)
            room.total_bookings = await room_repo.get_total_bookings(room.id)
            room.active_bookings = await room_repo.get_active_bookings(room.id)
            room.peak_utilization_hours = await room_repo.get_peak_utilization_hours(room.id)
            room.next_maintenance = await room_repo.get_next_maintenance(room.id)
            room.last_maintenance = await room_repo.get_last_maintenance(room.id)
            room.equipment_count = len(room.equipment) if room.equipment else 0
            room.is_compliant, room.compliance_score = await room_repo.check_compliance(room.id)
            room.waiting_list_count = await room_repo.get_waiting_list_count(room.id)
        
        return rooms
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch rooms: {str(e)}"
        )


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: str):
    """
    Get a specific room by ID
    
    Args:
        room_id: Room ID
        
    Returns:
        Room details
    """
    try:
        room = await room_repo.get_by_id(room_id)
        if not room:
            raise NotFoundError(f"Room not found with ID: {room_id}")
        
        # Add derived information
        room.current_utilization = await room_repo.get_current_utilization(room_id)
        room.total_bookings = await room_repo.get_total_bookings(room_id)
        room.active_bookings = await room_repo.get_active_bookings(room_id)
        room.peak_utilization_hours = await room_repo.get_peak_utilization_hours(room_id)
        room.next_maintenance = await room_repo.get_next_maintenance(room_id)
        room.last_maintenance = await room_repo.get_last_maintenance(room_id)
        room.equipment_count = len(room.equipment) if room.equipment else 0
        room.is_compliant, room.compliance_score = await room_repo.check_compliance(room_id)
        room.waiting_list_count = await room_repo.get_waiting_list_count(room_id)
        
        return room
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room not found with ID: {room_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch room: {str(e)}"
        )


@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new room
    
    Args:
        room_data: Room data
        credentials: JWT token
        
    Returns:
        Created room
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to create rooms")
        
        # Validate room code uniqueness
        code_exists = await room_repo.validate_code(room_data.room_code)
        if code_exists:
            raise ValidationError("Room code already exists")
        
        # Validate building
        building_exists = await room_repo.validate_building(room_data.building_id)
        if not building_exists:
            raise ValidationError("Building not found")
        
        # Validate room type
        valid_types = ['lecture', 'lab', 'seminar', 'office', 'meeting', 'storage']
        if room_data.room_type not in valid_types:
            raise ValidationError(f"Invalid room type. Must be one of: {valid_types}")
        
        # Validate equipment data
        if not room_data.equipment:
            raise ValidationError("Equipment information is required")
        
        # Create room
        room = await room_repo.create(
            name=room_data.name,
            room_code=room_data.room_code,
            building_id=room_data.building_id,
            floor=room_data.floor,
            room_type=room_data.room_type,
            capacity=room_data.capacity,
            amenities=room_data.amenities,
            equipment=room_data.equipment,
            features=room_data.features,
            availability=room_data.availability,
            usage_policy=room_data.usage_policy,
            is_active=room_data.is_active,
            metadata=room_data.metadata,
            created_by_id=auth.get('user_id') or auth.get('id')
        )
        
        return room
        
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
            detail=f"Failed to create room: {str(e)}"
        )


@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: str,
    room_data: RoomUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update a room
    
    Args:
        room_id: Room ID
        room_data: Updated room data
        credentials: JWT token
        
    Returns:
        Updated room
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to update rooms")
        
        # Check if room exists
        existing_room = await room_repo.get_by_id(room_id)
        if not existing_room:
            raise NotFoundError(f"Room not found with ID: {room_id}")
        
        # Validate room code if updated and changed
        if room_data.room_code and room_data.room_code != existing_room.room_code:
            code_exists = await room_repo.validate_code(room_data.room_code)
            if code_exists:
                raise ValidationError("Room code already exists")
        
        # Validate building if updated
        if room_data.building_id:
            building_exists = await room_repo.validate_building(room_data.building_id)
            if not building_exists:
                raise ValidationError("Building not found")
        
        # Validate room type if updated
        if room_data.room_type:
            valid_types = ['lecture', 'lab', 'seminar', 'office', 'meeting', 'storage']
            if room_data.room_type not in valid_types:
                raise ValidationError(f"Invalid room type. Must be one of: {valid_types}")
        
        # Update room
        room = await room_repo.update(
            room_id=room_id,
            **room_data.dict(exclude_unset=True)
        )
        
        return room
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room not found with ID: {room_id}"
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
            detail=f"Failed to update room: {str(e)}"
        )


@router.delete("/{room_id}")
async def delete_room(
    room_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a room
    
    Args:
        room_id: Room ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to delete rooms")
        
        # Check if room exists
        existing_room = await room_repo.get_by_id(room_id)
        if not existing_room:
            raise NotFoundError(f"Room not found with ID: {room_id}")
        
        # Check if room has active bookings
        has_active_bookings = await room_repo.has_active_bookings(room_id)
        if has_active_bookings:
            raise ValidationError("Cannot delete room with active bookings")
        
        # Delete room
        await room_repo.delete(room_id)
        
        return {"message": "Room deleted successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room not found with ID: {room_id}"
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
            detail=f"Failed to delete room: {str(e)}"
        )


@router.post("/{room_id}/book", response_model=RoomBookingResponse, status_code=status.HTTP_201_CREATED)
async def book_room(
    room_id: str,
    booking_data: RoomBooking,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Book a room
    
    Args:
        room_id: Room ID
        booking_data: Booking data
        credentials: JWT token
        
    Returns:
        Created booking
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to book rooms")
        
        # Check if room exists
        room_exists = await room_repo.validate_room(room_id)
        if not room_exists:
            raise NotFoundError(f"Room not found with ID: {room_id}")
        
        # Validate time range
        if booking_data.end_time <= booking_data.start_time:
            raise ValidationError("End time must be after start time")
        
        # Validate class and teacher
        class_exists = await room_repo.validate_class(booking_data.class_id)
        if not class_exists:
            raise ValidationError("Class not found")
        
        teacher_exists = await room_repo.validate_teacher(booking_data.teacher_id)
        if not teacher_exists:
            raise ValidationError("Teacher not found")
        
        # Validate subject
        subject_exists = await room_repo.validate_subject(booking_data.subject_id)
        if not subject_exists:
            raise ValidationError("Subject not found")
        
        # Validate equipment availability
        equipment_available = await room_repo.check_equipment_availability(
            room_id, booking_data.equipment_required or []
        )
        if not equipment_available:
            raise ValidationError("Required equipment not available")
        
        # Check for booking conflicts
        conflict_check = await room_repo.check_booking_conflicts(
            room_id, booking_data.start_time, booking_data.end_time
        )
        
        if conflict_check['has_conflict']:
            raise ValidationError(f"Booking conflict detected: {conflict_check['conflict_details']}")
        
        # Check capacity
        capacity_available = await room_repo.check_capacity_availability(
            room_id, booking_data.participants_count
        )
        
        if not capacity_available:
            # Check waiting list
            waiting_list_position = await room_repo.add_to_waiting_list(
                room_id, booking_data.participants_count, 
                booking_data.start_time, booking_data.end_time,
                auth.get('user_id') or auth.get('id')
            )
            
            return {
                "message": "Room at capacity. Added to waiting list",
                "waiting_list_position": waiting_list_position
            }
        
        # Create booking
        booking = await room_repo.create_booking(
            room_id=room_id,
            class_id=booking_data.class_id,
            subject_id=booking_data.subject_id,
            teacher_id=booking_data.teacher_id,
            start_time=booking_data.start_time,
            end_time=booking_data.end_time,
            booking_type=booking_data.booking_type,
            purpose=booking_data.purpose,
            equipment_required=booking_data.equipment_required,
            participants_count=booking_data.participants_count,
            priority=booking_data.priority,
            booking_notes=booking_data.booking_notes,
            metadata=booking_data.metadata,
            created_by_id=auth.get('user_id') or auth.get('id')
        )
        
        return booking
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room not found with ID: {room_id}"
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
            detail=f"Failed to book room: {str(e)}"
        )


@router.get("/{room_id}/bookings")
async def get_room_bookings(
    room_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    booking_status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    booking_type: Optional[str] = Query(None),
    teacher_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    Get room bookings with optional filtering
    
    Args:
        room_id: Room ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        booking_status: Filter by booking status
        start_date: Start date filter
        end_date: End date filter
        booking_type: Filter by booking type
        teacher_id: Filter by teacher ID
        class_id: Filter by class ID
        search: Search term in purpose or booking notes
        
    Returns:
        List of room bookings
    """
    try:
        bookings = await room_repo.get_room_bookings(
            room_id=room_id,
            skip=skip,
            limit=limit,
            booking_status=booking_status,
            start_date=start_date,
            end_date=end_date,
            booking_type=booking_type,
            teacher_id=teacher_id,
            class_id=class_id,
            search=search
        )
        return bookings
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch room bookings: {str(e)}"
        )


@router.get("/{room_id}/waiting-list")
async def get_room_waiting_list(
    room_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get room waiting list
    
    Args:
        room_id: Room ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        Room waiting list
    """
    try:
        waiting_list = await room_repo.get_waiting_list(
            room_id=room_id,
            skip=skip,
            limit=limit
        )
        return waiting_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch room waiting list: {str(e)}"
        )


@router.post("/{room_id}/maintain", response_model=RoomMaintenance, status_code=status.HTTP_201_CREATED)
async def schedule_maintenance(
    room_id: str,
    maintenance_data: RoomMaintenance,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Schedule maintenance for a room
    
    Args:
        room_id: Room ID
        maintenance_data: Maintenance data
        credentials: JWT token
        
    Returns:
        Created maintenance record
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to schedule maintenance")
        
        # Validate room
        room_exists = await room_repo.validate_room(room_id)
        if not room_exists:
            raise NotFoundError(f"Room not found with ID: {room_id}")
        
        # Validate maintenance data
        valid_types = ['preventive', 'corrective', 'emergency']
        if maintenance_data.maintenance_type not in valid_types:
            raise ValidationError(f"Invalid maintenance type. Must be one of: {valid_types}")
        
        if maintenance_data.estimated_duration < 1:
            raise ValidationError("Estimated duration must be at least 1 hour")
        
        if maintenance_data.cost_estimate < 0:
            raise ValidationError("Cost estimate must be non-negative")
        
        # Validate maintenance date
        if maintenance_data.scheduled_date < datetime.now():
            raise ValidationError("Maintenance date must be in the future")
        
        # Schedule maintenance
        maintenance = await room_repo.schedule_maintenance(
            room_id=room_id,
            maintenance_type=maintenance_data.maintenance_type,
            description=maintenance_data.description,
            scheduled_date=maintenance_data.scheduled_date,
            estimated_duration=maintenance_data.estimated_duration,
            maintenance_team=maintenance_data.maintenance_team,
            equipment_involved=maintenance_data.equipment_involved,
            cost_estimate=maintenance_data.cost_estimate,
            safety_measures=maintenance_data.safety_measures,
            metadata=maintenance_data.metadata,
            scheduled_by_id=auth.get('user_id') or auth.get('id')
        )
        
        return maintenance
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room not found with ID: {room_id}"
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
            detail=f"Failed to schedule maintenance: {str(e)}"
        )


@router.get("/{room_id}/stats", response_model=RoomStats)
async def get_room_stats(
    room_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """
    Get room statistics
    
    Args:
        room_id: Room ID
        start_date: Start date filter
        end_date: End date filter
        
    Returns:
        Room statistics
    """
    try:
        stats = await room_repo.get_room_stats(
            room_id=room_id,
            start_date=start_date,
            end_date=end_date
        )
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch room stats: {str(e)}"
        )


@router.get("/{room_id}/availability")
async def get_room_availability(
    room_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    time_slot: Optional[str] = Query(None, description="HH:MM-HH:MM format")
):
    """
    Get room availability
    
    Args:
        room_id: Room ID
        start_date: Start date filter
        end_date: End date filter
        time_slot: Specific time slot to check
        
    Returns:
        Room availability information
    """
    try:
        availability = await room_repo.get_room_availability(
            room_id=room_id,
            start_date=start_date,
            end_date=end_date,
            time_slot=time_slot
        )
        return availability
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch room availability: {str(e)}"
        )