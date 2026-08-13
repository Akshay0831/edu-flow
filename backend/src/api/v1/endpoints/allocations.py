"""
Teacher Allocation Management API Endpoints

This module provides REST API endpoints for teacher allocation management operations:
- CRUD operations for teacher allocations
- Allocation scheduling and optimization
- Resource allocation management
- Workload tracking
- Conflict detection and resolution

Author: Edu-Flow Team
"""

from datetime import datetime, time
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field, validator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.security import auth_service
from src.core.exceptions import ValidationError, NotFoundError, AuthenticationError, AuthorizationError
from src.infrastructure.repositories.allocation_repository import AllocationRepository

# Create router
router = APIRouter(prefix="/allocations", tags=["allocations"])

# Security
security = HTTPBearer()

# Repositories
allocation_repo = AllocationRepository()


# Pydantic models
class AllocationBase(BaseModel):
    teacher_id: str = Field(..., min_length=2)
    class_id: str = Field(..., min_length=2)
    subject_id: str = Field(..., min_length=2)
    academic_year: str = Field(..., min_length=4, max_length=10)
    semester: int = Field(..., ge=1, le=12)
    allocation_type: str = Field(..., description="primary, secondary, substitute")
    workload_hours: float = Field(..., ge=0, le=40)
    start_date: datetime = Field(..., description="Allocation start date")
    end_date: Optional[datetime] = Field(None, description="Allocation end date")
    priority: int = Field(1, ge=1, le=5, description="Allocation priority")
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AllocationCreate(AllocationBase):
    pass


class AllocationUpdate(BaseModel):
    teacher_id: Optional[str] = Field(None, min_length=2)
    class_id: Optional[str] = Field(None, min_length=2)
    subject_id: Optional[str] = Field(None, min_length=2)
    academic_year: Optional[str] = Field(None, min_length=4, max_length=10)
    semester: Optional[int] = Field(None, ge=1, le=12)
    allocation_type: Optional[str] = Field(None)
    workload_hours: Optional[float] = Field(None, ge=0, le=40)
    start_date: Optional[datetime] = Field(None)
    end_date: Optional[datetime] = Field(None)
    priority: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, description="active, completed, cancelled")


class AllocationResponse(AllocationBase):
    id: str
    created_at: datetime
    updated_at: datetime
    status: str
    assigned_by_id: str
    assigned_at: datetime
    has_conflicts: bool = False
    conflict_details: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ConflictCheck(BaseModel):
    has_conflicts: bool
    conflicts: List[Dict[str, Any]]
    recommendations: List[str]


@router.get("/", response_model=List[AllocationResponse])
async def get_allocations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    teacher_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    allocation_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    has_conflicts: Optional[bool] = Query(None)
):
    """
    Get all allocations with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        teacher_id: Filter by teacher ID
        class_id: Filter by class ID
        subject_id: Filter by subject ID
        academic_year: Filter by academic year
        semester: Filter by semester
        allocation_type: Filter by allocation type
        status: Filter by status
        has_conflicts: Filter by conflict status
        
    Returns:
        List of allocations
    """
    try:
        allocations = await allocation_repo.get_all(
            skip=skip,
            limit=limit,
            teacher_id=teacher_id,
            class_id=class_id,
            subject_id=subject_id,
            academic_year=academic_year,
            semester=semester,
            allocation_type=allocation_type,
            status=status,
            has_conflicts=has_conflicts
        )
        
        # Add conflict information
        for allocation in allocations:
            conflict_check = await allocation_repo.check_allocation_conflicts(allocation.id)
            allocation.has_conflicts = conflict_check['has_conflicts']
            allocation.conflict_details = conflict_check['conflicts']
        
        return allocations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch allocations: {str(e)}"
        )


@router.get("/{allocation_id}", response_model=AllocationResponse)
async def get_allocation(allocation_id: str):
    """
    Get a specific allocation by ID
    
    Args:
        allocation_id: Allocation ID
        
    Returns:
        Allocation details
    """
    try:
        allocation = await allocation_repo.get_by_id(allocation_id)
        if not allocation:
            raise NotFoundError(f"Allocation not found with ID: {allocation_id}")
        
        # Add conflict information
        conflict_check = await allocation_repo.check_allocation_conflicts(allocation_id)
        allocation.has_conflicts = conflict_check['has_conflicts']
        allocation.conflict_details = conflict_check['conflicts']
        
        return allocation
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation not found with ID: {allocation_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch allocation: {str(e)}"
        )


@router.post("/", response_model=AllocationResponse, status_code=status.HTTP_201_CREATED)
async def create_allocation(
    allocation_data: AllocationCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new teacher allocation
    
    Args:
        allocation_data: Allocation data
        credentials: JWT token
        
    Returns:
        Created allocation
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to create allocations")
        
        # Validate dates
        if allocation_data.end_date and allocation_data.end_date < allocation_data.start_date:
            raise ValidationError("End date must be after start date")
        
        # Check for existing allocations
        existing_allocations = await allocation_repo.check_existing_allocations(
            allocation_data.teacher_id,
            allocation_data.class_id,
            allocation_data.academic_year,
            allocation_data.semester
        )
        
        if existing_allocations:
            raise ValidationError("Teacher already allocated to this class for the given semester")
        
        # Check workload constraints
        workload_check = await allocation_repo.check_workload_constraints(
            allocation_data.teacher_id,
            allocation_data.workload_hours
        )
        
        if not workload_check['is_valid']:
            raise ValidationError(f"Workload constraint violated: {workload_check['reason']}")
        
        # Create allocation
        allocation = await allocation_repo.create(
            teacher_id=allocation_data.teacher_id,
            class_id=allocation_data.class_id,
            subject_id=allocation_data.subject_id,
            academic_year=allocation_data.academic_year,
            semester=allocation_data.semester,
            allocation_type=allocation_data.allocation_type,
            workload_hours=allocation_data.workload_hours,
            start_date=allocation_data.start_date,
            end_date=allocation_data.end_date,
            priority=allocation_data.priority,
            notes=allocation_data.notes,
            metadata=allocation_data.metadata
        )
        
        # Assign allocation
        assigned_by_id = auth.get('user_id') or auth.get('id')
        await allocation_repo.assign_allocation(allocation.id, assigned_by_id)
        
        return allocation
        
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
            detail=f"Failed to create allocation: {str(e)}"
        )


@router.put("/{allocation_id}", response_model=AllocationResponse)
async def update_allocation(
    allocation_id: str,
    allocation_data: AllocationUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update an allocation
    
    Args:
        allocation_id: Allocation ID
        allocation_data: Updated allocation data
        credentials: JWT token
        
    Returns:
        Updated allocation
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to update allocations")
        
        # Check if allocation exists
        existing_allocation = await allocation_repo.get_by_id(allocation_id)
        if not existing_allocation:
            raise NotFoundError(f"Allocation not found with ID: {allocation_id}")
        
        # Validate dates
        if allocation_data.start_date and allocation_data.end_date:
            if allocation_data.end_date < allocation_data.start_date:
                raise ValidationError("End date must be after start date")
        
        # Check for conflicts if updating dates
        if allocation_data.start_date or allocation_data.end_date:
            conflict_check = await allocation_repo.check_allocation_conflicts(allocation_id)
            if conflict_check['has_conflicts']:
                raise ValidationError(f"Cannot update allocation due to conflicts: {conflict_check['conflicts']}")
        
        # Check workload constraints if updating hours
        if allocation_data.workload_hours is not None:
            workload_check = await allocation_repo.check_workload_constraints(
                allocation_data.teacher_id or existing_allocation.teacher_id,
                allocation_data.workload_hours
            )
            
            if not workload_check['is_valid']:
                raise ValidationError(f"Workload constraint violated: {workload_check['reason']}")
        
        # Update allocation
        allocation = await allocation_repo.update(
            allocation_id=allocation_id,
            **allocation_data.dict(exclude_unset=True)
        )
        
        return allocation
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation not found with ID: {allocation_id}"
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
            detail=f"Failed to update allocation: {str(e)}"
        )


@router.delete("/{allocation_id}")
async def delete_allocation(
    allocation_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete an allocation
    
    Args:
        allocation_id: Allocation ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to delete allocations")
        
        # Check if allocation exists
        existing_allocation = await allocation_repo.get_by_id(allocation_id)
        if not existing_allocation:
            raise NotFoundError(f"Allocation not found with ID: {allocation_id}")
        
        # Check if allocation is active
        if existing_allocation.status == 'active':
            raise ValidationError("Cannot delete active allocations. Cancel them first.")
        
        # Delete allocation
        await allocation_repo.delete(allocation_id)
        
        return {"message": "Allocation deleted successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation not found with ID: {allocation_id}"
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
            detail=f"Failed to delete allocation: {str(e)}"
        )


@router.post("/{allocation_id}/activate")
async def activate_allocation(
    allocation_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Activate an allocation
    
    Args:
        allocation_id: Allocation ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to activate allocations")
        
        await allocation_repo.update(allocation_id, status='active')
        
        return {"message": "Allocation activated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate allocation: {str(e)}"
        )


@router.post("/{allocation_id}/cancel")
async def cancel_allocation(
    allocation_id: str,
    reason: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Cancel an allocation
    
    Args:
        allocation_id: Allocation ID
        reason: Reason for cancellation
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to cancel allocations")
        
        await allocation_repo.cancel_allocation(allocation_id, reason)
        
        return {"message": "Allocation cancelled successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel allocation: {str(e)}"
        )


@router.get("/conflicts/check/{allocation_id}")
async def check_allocation_conflicts(
    allocation_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Check allocation conflicts
    
    Args:
        allocation_id: Allocation ID
        credentials: JWT token
        
    Returns:
        Conflict check result
    """
    try:
        conflict_check = await allocation_repo.check_allocation_conflicts(allocation_id)
        return conflict_check
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check allocation conflicts: {str(e)}"
        )


@router.get("/conflicts/resolve/{conflict_id}")
async def resolve_conflict(
    conflict_id: str,
    resolution_action: str = Field(..., description="reassign, reschedule, cancel"),
    resolution_details: Optional[Dict[str, Any]] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Resolve allocation conflict
    
    Args:
        conflict_id: Conflict ID
        resolution_action: Resolution action
        resolution_details: Resolution details
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to resolve conflicts")
        
        await allocation_repo.resolve_conflict(
            conflict_id=conflict_id,
            resolution_action=resolution_action,
            resolution_details=resolution_details,
            resolved_by_id=auth.get('user_id') or auth.get('id')
        )
        
        return {"message": "Conflict resolved successfully"}
        
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
            detail=f"Failed to resolve conflict: {str(e)}"
        )


@router.get("/workload/{teacher_id}")
async def get_teacher_workload(
    teacher_id: str,
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get teacher workload information
    
    Args:
        teacher_id: Teacher ID
        academic_year: Filter by academic year
        semester: Filter by semester
        credentials: JWT token
        
    Returns:
        Teacher workload information
    """
    try:
        workload = await allocation_repo.get_teacher_workload(
            teacher_id=teacher_id,
            academic_year=academic_year,
            semester=semester
        )
        return workload
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch teacher workload: {str(e)}"
        )


@router.get("/schedule/{teacher_id}")
async def get_teacher_schedule(
    teacher_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get teacher schedule
    
    Args:
        teacher_id: Teacher ID
        start_date: Start date filter (YYYY-MM-DD)
        end_date: End date filter (YYYY-MM-DD)
        credentials: JWT token
        
    Returns:
        Teacher schedule
    """
    try:
        schedule = await allocation_repo.get_teacher_schedule(
            teacher_id=teacher_id,
            start_date=start_date,
            end_date=end_date
        )
        return schedule
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch teacher schedule: {str(e)}"
        )


@router.get("/optimization/suggestions")
async def get_optimization_suggestions(
    teacher_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get allocation optimization suggestions
    
    Args:
        teacher_id: Filter by teacher ID
        class_id: Filter by class ID
        academic_year: Filter by academic year
        semester: Filter by semester
        credentials: JWT token
        
    Returns:
        Optimization suggestions
    """
    try:
        suggestions = await allocation_repo.get_optimization_suggestions(
            teacher_id=teacher_id,
            class_id=class_id,
            academic_year=academic_year,
            semester=semester
        )
        return suggestions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch optimization suggestions: {str(e)}"
        )


@router.post("/batch-assign")
async def batch_assign_allocations(
    assignments: List[Dict[str, Any]],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Batch assign allocations
    
    Args:
        assignments: List of assignment data
        credentials: JWT token
        
    Returns:
        Batch assignment result
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions for batch assignment")
        
        # Validate assignments
        for assignment in assignments:
            required_fields = ['teacher_id', 'class_id', 'subject_id', 'academic_year', 'semester']
            for field in required_fields:
                if field not in assignment:
                    raise ValidationError(f"Missing required field: {field}")
        
        # Batch assign allocations
        results = await allocation_repo.batch_assign(assignments, auth.get('user_id') or auth.get('id'))
        
        return results
        
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
            detail=f"Failed to batch assign allocations: {str(e)}"
        )