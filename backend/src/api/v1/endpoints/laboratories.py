"""
Laboratory Management API Endpoints

This module provides REST API endpoints for laboratory management operations:
- CRUD operations for laboratories
- Laboratory scheduling and allocation
- Equipment and resource management
- Laboratory capacity and utilization
- Laboratory reporting and analytics

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
from src.infrastructure.repositories.laboratory_repository import LaboratoryRepository

# Create router
router = APIRouter(prefix="/laboratories", tags=["laboratories"])

# Security
security = HTTPBearer()

# Repositories
laboratory_repo = LaboratoryRepository()


# Pydantic models
class LaboratoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., min_length=1, max_length=10, description="Laboratory code")
    building_id: str = Field(..., min_length=2, description="Building ID")
    floor: int = Field(..., ge=1, le=20, description="Floor number")
    capacity: int = Field(..., ge=1, le=500, description="Laboratory capacity")
    equipment: Dict[str, Any] = Field(..., description="Equipment information")
    amenities: List[str] = Field(..., description="List of amenities")
    safety_features: List[str] = Field(..., description="Safety features available")
    maintenance_schedule: Optional[Dict[str, Any]] = Field(None, description="Maintenance schedule")
    operating_hours: Dict[str, Any] = Field(..., description="Operating hours")
    usage_policy: str = Field(..., max_length=1000, description="Usage policy")
    is_active: bool = Field(True)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class LaboratoryCreate(LaboratoryBase):
    pass


class LaboratoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=10)
    building_id: Optional[str] = Field(None, min_length=2)
    floor: Optional[int] = Field(None, ge=1, le=20)
    capacity: Optional[int] = Field(None, ge=1, le=500)
    equipment: Optional[Dict[str, Any]] = Field(None)
    amenities: Optional[List[str]] = Field(None)
    safety_features: Optional[List[str]] = Field(None)
    maintenance_schedule: Optional[Dict[str, Any]] = Field(None)
    operating_hours: Optional[Dict[str, Any]] = Field(None)
    usage_policy: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = Field(None)


class LaboratoryResponse(LaboratoryBase):
    id: str
    created_at: datetime
    updated_at: datetime
    lab_type: str = ""
    specialty: str = ""
    current_utilization: float = 0.0
    total_bookings: int = 0
    active_bookings: int = 0
    next_maintenance: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    equipment_count: int = 0
    is_compliant: bool = True
    compliance_score: float = 100.0
    
    class Config:
        from_attributes = True


class LaboratoryBooking(BaseModel):
    laboratory_id: str = Field(..., min_length=2)
    class_id: str = Field(..., min_length=2)
    subject_id: str = Field(..., min_length=2)
    teacher_id: str = Field(..., min_length=2)
    start_time: datetime = Field(..., description="Booking start time")
    end_time: datetime = Field(..., description="Booking end time")
    booking_type: str = Field(..., description="regular, special, maintenance")
    purpose: str = Field(..., max_length=500, description="Purpose of booking")
    equipment_required: Optional[List[str]] = Field(None, description="Required equipment")
    participants_count: int = Field(..., ge=1, le=500, description="Number of participants")
    safety_requirements: Optional[List[str]] = Field(None, description="Safety requirements")
    priority: int = Field(1, ge=1, le=5, description="Booking priority")
    booking_notes: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class LaboratoryBookingResponse(LaboratoryBooking):
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
    cancellation_policy: str = ""
    
    class Config:
        from_attributes = True


class LaboratoryEquipment(BaseModel):
    equipment_id: str = Field(..., min_length=2)
    equipment_name: str = Field(..., max_length=100)
    equipment_type: str = Field(..., description="Equipment category")
    quantity: int = Field(..., ge=1)
    condition: str = Field(..., description="new, good, fair, poor, broken")
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    specifications: Dict[str, Any] = Field(..., description="Equipment specifications")
    safety_requirements: List[str] = Field(..., description="Safety requirements")
    is_available: bool = True
    booking_rules: Dict[str, Any] = Field(..., description="Booking rules")
    maintenance_history: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class LaboratoryMaintenance(BaseModel):
    laboratory_id: str = Field(..., min_length=2)
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


class LaboratoryStats(BaseModel):
    laboratory_id: str
    laboratory_name: str
    total_bookings: int
    active_bookings: int
    average_utilization: float
    peak_utilization_hours: Dict[str, float]
    equipment_utilization: Dict[str, float]
    maintenance_frequency: float
    compliance_score: float
    safety_incidents_count: int
    reschedule_rate: float
    cancellation_rate: float
    popular_equipment: List[str]


@router.get("/", response_model=List[LaboratoryResponse])
async def get_laboratories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    building_id: Optional[str] = Query(None),
    lab_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    Get all laboratories with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        building_id: Filter by building ID
        lab_type: Filter by laboratory type
        is_active: Filter by active status
        search: Search term in name or code
        
    Returns:
        List of laboratories
    """
    try:
        laboratories = await laboratory_repo.get_all(
            skip=skip,
            limit=limit,
            building_id=building_id,
            lab_type=lab_type,
            is_active=is_active,
            search=search
        )
        
        # Add derived information
        for lab in laboratories:
            lab.current_utilization = await laboratory_repo.get_current_utilization(lab.id)
            lab.total_bookings = await laboratory_repo.get_total_bookings(lab.id)
            lab.active_bookings = await laboratory_repo.get_active_bookings(lab.id)
            lab.next_maintenance = await laboratory_repo.get_next_maintenance(lab.id)
            lab.last_maintenance = await laboratory_repo.get_last_maintenance(lab.id)
            lab.equipment_count = len(lab.equipment) if lab.equipment else 0
            lab.is_compliant, lab.compliance_score = await laboratory_repo.check_compliance(lab.id)
        
        return laboratories
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch laboratories: {str(e)}"
        )


@router.get("/{laboratory_id}", response_model=LaboratoryResponse)
async def get_laboratory(laboratory_id: str):
    """
    Get a specific laboratory by ID
    
    Args:
        laboratory_id: Laboratory ID
        
    Returns:
        Laboratory details
    """
    try:
        laboratory = await laboratory_repo.get_by_id(laboratory_id)
        if not laboratory:
            raise NotFoundError(f"Laboratory not found with ID: {laboratory_id}")
        
        # Add derived information
        laboratory.current_utilization = await laboratory_repo.get_current_utilization(laboratory_id)
        laboratory.total_bookings = await laboratory_repo.get_total_bookings(laboratory_id)
        laboratory.active_bookings = await laboratory_repo.get_active_bookings(laboratory_id)
        laboratory.next_maintenance = await laboratory_repo.get_next_maintenance(laboratory_id)
        laboratory.last_maintenance = await laboratory_repo.get_last_maintenance(laboratory_id)
        laboratory.equipment_count = len(laboratory.equipment) if laboratory.equipment else 0
        laboratory.is_compliant, laboratory.compliance_score = await laboratory_repo.check_compliance(laboratory_id)
        
        return laboratory
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Laboratory not found with ID: {laboratory_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch laboratory: {str(e)}"
        )


@router.post("/", response_model=LaboratoryResponse, status_code=status.HTTP_201_CREATED)
async def create_laboratory(
    laboratory_data: LaboratoryCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new laboratory
    
    Args:
        laboratory_data: Laboratory data
        credentials: JWT token
        
    Returns:
        Created laboratory
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to create laboratories")
        
        # Validate laboratory code uniqueness
        code_exists = await laboratory_repo.validate_code(laboratory_data.code)
        if code_exists:
            raise ValidationError("Laboratory code already exists")
        
        # Validate building
        building_exists = await laboratory_repo.validate_building(laboratory_data.building_id)
        if not building_exists:
            raise ValidationError("Building not found")
        
        # Validate equipment data
        if not laboratory_data.equipment:
            raise ValidationError("Equipment information is required")
        
        # Validate operating hours
        if not laboratory_repo.validate_operating_hours(laboratory_data.operating_hours):
            raise ValidationError("Invalid operating hours format")
        
        # Create laboratory
        laboratory = await laboratory_repo.create(
            name=laboratory_data.name,
            code=laboratory_data.code,
            building_id=laboratory_data.building_id,
            floor=laboratory_data.floor,
            capacity=laboratory_data.capacity,
            equipment=laboratory_data.equipment,
            amenities=laboratory_data.amenities,
            safety_features=laboratory_data.safety_features,
            maintenance_schedule=laboratory_data.maintenance_schedule,
            operating_hours=laboratory_data.operating_hours,
            usage_policy=laboratory_data.usage_policy,
            is_active=laboratory_data.is_active,
            metadata=laboratory_data.metadata,
            created_by_id=auth.get('user_id') or auth.get('id')
        )
        
        return laboratory
        
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
            detail=f"Failed to create laboratory: {str(e)}"
        )


@router.put("/{laboratory_id}", response_model=LaboratoryResponse)
async def update_laboratory(
    laboratory_id: str,
    laboratory_data: LaboratoryUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update a laboratory
    
    Args:
        laboratory_id: Laboratory ID
        laboratory_data: Updated laboratory data
        credentials: JWT token
        
    Returns:
        Updated laboratory
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to update laboratories")
        
        # Check if laboratory exists
        existing_laboratory = await laboratory_repo.get_by_id(laboratory_id)
        if not existing_laboratory:
            raise NotFoundError(f"Laboratory not found with ID: {laboratory_id}")
        
        # Validate laboratory code if updated and changed
        if laboratory_data.code and laboratory_data.code != existing_laboratory.code:
            code_exists = await laboratory_repo.validate_code(laboratory_data.code)
            if code_exists:
                raise ValidationError("Laboratory code already exists")
        
        # Validate building if updated
        if laboratory_data.building_id:
            building_exists = await laboratory_repo.validate_building(laboratory_data.building_id)
            if not building_exists:
                raise ValidationError("Building not found")
        
        # Validate operating hours if updated
        if laboratory_data.operating_hours:
            if not laboratory_repo.validate_operating_hours(laboratory_data.operating_hours):
                raise ValidationError("Invalid operating hours format")
        
        # Update laboratory
        laboratory = await laboratory_repo.update(
            laboratory_id=laboratory_id,
            **laboratory_data.dict(exclude_unset=True)
        )
        
        return laboratory
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Laboratory not found with ID: {laboratory_id}"
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
            detail=f"Failed to update laboratory: {str(e)}"
        )


@router.delete("/{laboratory_id}")
async def delete_laboratory(
    laboratory_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a laboratory
    
    Args:
        laboratory_id: Laboratory ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to delete laboratories")
        
        # Check if laboratory exists
        existing_laboratory = await laboratory_repo.get_by_id(laboratory_id)
        if not existing_laboratory:
            raise NotFoundError(f"Laboratory not found with ID: {laboratory_id}")
        
        # Check if laboratory has active bookings
        has_active_bookings = await laboratory_repo.has_active_bookings(laboratory_id)
        if has_active_bookings:
            raise ValidationError("Cannot delete laboratory with active bookings")
        
        # Delete laboratory
        await laboratory_repo.delete(laboratory_id)
        
        return {"message": "Laboratory deleted successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Laboratory not found with ID: {laboratory_id}"
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
            detail=f"Failed to delete laboratory: {str(e)}"
        )


@router.post("/{laboratory_id}/book", response_model=LaboratoryBookingResponse, status_code=status.HTTP_201_CREATED)
async def book_laboratory(
    laboratory_id: str,
    booking_data: LaboratoryBooking,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Book a laboratory
    
    Args:
        laboratory_id: Laboratory ID
        booking_data: Booking data
        credentials: JWT token
        
    Returns:
        Created booking
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to book laboratories")
        
        # Check if laboratory exists
        laboratory_exists = await laboratory_repo.validate_laboratory(laboratory_id)
        if not laboratory_exists:
            raise NotFoundError(f"Laboratory not found with ID: {laboratory_id}")
        
        # Validate time range
        if booking_data.end_time <= booking_data.start_time:
            raise ValidationError("End time must be after start time")
        
        # Validate class and teacher
        class_exists = await laboratory_repo.validate_class(booking_data.class_id)
        if not class_exists:
            raise ValidationError("Class not found")
        
        teacher_exists = await laboratory_repo.validate_teacher(booking_data.teacher_id)
        if not teacher_exists:
            raise ValidationError("Teacher not found")
        
        # Validate subject
        subject_exists = await laboratory_repo.validate_subject(booking_data.subject_id)
        if not subject_exists:
            raise ValidationError("Subject not found")
        
        # Validate equipment availability
        equipment_available = await laboratory_repo.check_equipment_availability(
            laboratory_id, booking_data.equipment_required or []
        )
        if not equipment_available:
            raise ValidationError("Required equipment not available")
        
        # Check for booking conflicts
        conflict_check = await laboratory_repo.check_booking_conflicts(
            laboratory_id, booking_data.start_time, booking_data.end_time
        )
        
        if conflict_check['has_conflict']:
            raise ValidationError(f"Booking conflict detected: {conflict_check['conflict_details']}")
        
        # Check capacity
        capacity_available = await laboratory_repo.check_capacity_availability(
            laboratory_id, booking_data.participants_count
        )
        
        if not capacity_available:
            raise ValidationError("Laboratory capacity exceeded")
        
        # Create booking
        booking = await laboratory_repo.create_booking(
            laboratory_id=laboratory_id,
            class_id=booking_data.class_id,
            subject_id=booking_data.subject_id,
            teacher_id=booking_data.teacher_id,
            start_time=booking_data.start_time,
            end_time=booking_data.end_time,
            booking_type=booking_data.booking_type,
            purpose=booking_data.purpose,
            equipment_required=booking_data.equipment_required,
            participants_count=booking_data.participants_count,
            safety_requirements=booking_data.safety_requirements,
            priority=booking_data.priority,
            booking_notes=booking_data.booking_notes,
            metadata=booking_data.metadata,
            created_by_id=auth.get('user_id') or auth.get('id')
        )
        
        return booking
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Laboratory not found with ID: {laboratory_id}"
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
            detail=f"Failed to book laboratory: {str(e)}"
        )


@router.get("/{laboratory_id}/bookings")
async def get_laboratory_bookings(
    laboratory_id: str,
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
    Get laboratory bookings with optional filtering
    
    Args:
        laboratory_id: Laboratory ID
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
        List of laboratory bookings
    """
    try:
        bookings = await laboratory_repo.get_laboratory_bookings(
            laboratory_id=laboratory_id,
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
            detail=f"Failed to fetch laboratory bookings: {str(e)}"
        )


@router.post("/{laboratory_id}/equipment", status_code=status.HTTP_201_CREATED)
async def add_equipment(
    laboratory_id: str,
    equipment: LaboratoryEquipment,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Add equipment to a laboratory
    
    Args:
        laboratory_id: Laboratory ID
        equipment: Equipment data
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to manage equipment")
        
        # Validate laboratory
        laboratory_exists = await laboratory_repo.validate_laboratory(laboratory_id)
        if not laboratory_exists:
            raise NotFoundError(f"Laboratory not found with ID: {laboratory_id}")
        
        # Validate equipment data
        if not equipment.equipment_name:
            raise ValidationError("Equipment name is required")
        
        if equipment.quantity < 1:
            raise ValidationError("Quantity must be at least 1")
        
        # Add equipment
        await laboratory_repo.add_equipment(
            laboratory_id=laboratory_id,
            equipment_data=equipment.dict()
        )
        
        return {"message": "Equipment added successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Laboratory not found with ID: {laboratory_id}"
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
            detail=f"Failed to add equipment: {str(e)}"
        )


@router.post("/{laboratory_id}/maintenance", response_model=LaboratoryMaintenance, status_code=status.HTTP_201_CREATED)
async def schedule_maintenance(
    laboratory_id: str,
    maintenance_data: LaboratoryMaintenance,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Schedule maintenance for a laboratory
    
    Args:
        laboratory_id: Laboratory ID
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
        
        # Validate laboratory
        laboratory_exists = await laboratory_repo.validate_laboratory(laboratory_id)
        if not laboratory_exists:
            raise NotFoundError(f"Laboratory not found with ID: {laboratory_id}")
        
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
        maintenance = await laboratory_repo.schedule_maintenance(
            laboratory_id=laboratory_id,
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
            detail=f"Laboratory not found with ID: {laboratory_id}"
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


@router.get("/{laboratory_id}/stats", response_model=LaboratoryStats)
async def get_laboratory_stats(
    laboratory_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """
    Get laboratory statistics
    
    Args:
        laboratory_id: Laboratory ID
        start_date: Start date filter
        end_date: End date filter
        
    Returns:
        Laboratory statistics
    """
    try:
        stats = await laboratory_repo.get_laboratory_stats(
            laboratory_id=laboratory_id,
            start_date=start_date,
            end_date=end_date
        )
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch laboratory stats: {str(e)}"
        )


@router.get("/{laboratory_id}/availability")
async def get_laboratory_availability(
    laboratory_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    time_slot: Optional[str] = Query(None, description="HH:MM-HH:MM format")
):
    """
    Get laboratory availability
    
    Args:
        laboratory_id: Laboratory ID
        start_date: Start date filter
        end_date: End date filter
        time_slot: Specific time slot to check
        
    Returns:
        Laboratory availability information
    """
    try:
        availability = await laboratory_repo.get_laboratory_availability(
            laboratory_id=laboratory_id,
            start_date=start_date,
            end_date=end_date,
            time_slot=time_slot
        )
        return availability
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch laboratory availability: {str(e)}"
        )