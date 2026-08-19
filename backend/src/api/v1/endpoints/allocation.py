"""
Class & Teacher Allocation API Endpoints

This module provides REST API endpoints for class and teacher allocation:
- CRUD operations for allocations
- Availability management and scheduling
- Optimization and auto-allocation
- Request management and approval
- Timetable optimization

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_user, get_service_container
from src.services.allocation_service import AllocationService
from core.response_handler import ResponseFormatter
from core.exceptions import ValidationError, NotFoundError
from models.allocation import AllocationStatus, ConstraintType
from src.services.base_service import ServiceContainer

router = APIRouter(prefix="/allocation", tags=["Class & Teacher Allocation"])

# region: Basic CRUD Endpoints
@router.post("/allocations", response_model=Dict[str, Any])
async def create_allocation(
    allocation_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """
    Create a new class allocation
    
    **Required:**
    - class_id: Class ID
    - teacher_id: Teacher ID
    - subject_id: Subject ID
    - academic_year: Academic year
    - semester: Semester
    
    **Optional:**
    - allocation_priority: Priority (1-5, default: 1)
    - load_percentage: Teacher load percentage (default: 100.0)
    - teaching_method: Lecture, Lab, Tutorial, Seminar (default: "lecture")
    - notes: Additional notes
    """
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        allocation = await allocation_service.create_allocation(
            class_id=allocation_data["class_id"],
            teacher_id=allocation_data["teacher_id"],
            subject_id=allocation_data["subject_id"],
            academic_year=allocation_data["academic_year"],
            semester=allocation_data["semester"],
            allocation_priority=allocation_data.get("allocation_priority", 1),
            load_percentage=allocation_data.get("load_percentage", 100.0),
            teaching_method=allocation_data.get("teaching_method", "lecture"),
            notes=allocation_data.get("notes")
        )
        
        return ResponseFormatter.success(
            data=allocation.__dict__,
            message="Class allocation created successfully",
            status_code=201
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating allocation: {str(e)}")

@router.get("/allocations/{allocation_id}", response_model=Dict[str, Any])
async def get_allocation(
    allocation_id: str = Path(..., description="Allocation ID"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get a specific class allocation"""
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        allocation = await allocation_service.get_allocation_by_id(allocation_id)
        
        if not allocation:
            raise NotFoundError(f"Class allocation not found: {allocation_id}")
        
        return ResponseFormatter.success(
            data=allocation.__dict__,
            message="Class allocation retrieved successfully"
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving allocation: {str(e)}")

@router.get("/allocations", response_model=Dict[str, Any])
async def get_allocations(
    class_id: Optional[str] = Query(None, description="Class ID filter"),
    teacher_id: Optional[str] = Query(None, description="Teacher ID filter"),
    academic_year: Optional[str] = Query(None, description="Academic year filter"),
    semester: Optional[str] = Query(None, description="Semester filter"),
    status: Optional[str] = Query(None, description="Allocation status filter"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get class allocations based on filters"""
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        allocations = await allocation_service.get_class_allocations(
            class_id=class_id,
            teacher_id=teacher_id,
            academic_year=academic_year,
            semester=semester,
            status=status
        )
        
        return ResponseFormatter.success(
            data=[alloc.__dict__ for alloc in allocations],
            message=f"Found {len(allocations)} class allocations"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving allocations: {str(e)}")

@router.put("/allocations/{allocation_id}", response_model=Dict[str, Any])
async def update_allocation(
    allocation_id: str = Path(..., description="Allocation ID"),
    updates: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Update a class allocation"""
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        allocation = await allocation_service.update_allocation(allocation_id, updates)
        
        return ResponseFormatter.success(
            data=allocation.__dict__,
            message="Class allocation updated successfully"
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating allocation: {str(e)}")

@router.delete("/allocations/{allocation_id}", response_model=Dict[str, Any])
async def delete_allocation(
    allocation_id: str = Path(..., description="Allocation ID"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Delete a class allocation"""
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        success = await allocation_service.delete_allocation(allocation_id)
        
        if success:
            return ResponseFormatter.success(
                data={"deleted": True, "allocation_id": allocation_id},
                message="Class allocation deleted successfully"
            )
        else:
            raise NotFoundError(f"Class allocation not found: {allocation_id}")
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting allocation: {str(e)}")

# region: Allocation Optimization
@router.post("/optimize", response_model=Dict[str, Any])
async def optimize_allocation(
    optimization_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Optimize class allocations based on constraints and preferences"""
    
    required_fields = ["academic_year", "semester", "allocation_requests"]
    for field in required_fields:
        if field not in optimization_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        result = await allocation_service.optimize_allocation(
            academic_year=optimization_data["academic_year"],
            semester=optimization_data["semester"],
            allocation_requests=optimization_data["allocation_requests"]
        )
        
        return ResponseFormatter.success(
            data=result,
            message="Allocations optimized successfully"
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing allocations: {str(e)}")

@router.post("/auto-allocate", response_model=Dict[str, Any])
async def auto_allocate_classes(
    auto_allocate_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Automatically allocate classes to available teachers"""
    
    required_fields = ["academic_year", "semester"]
    for field in required_fields:
        if field not in auto_allocate_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    force_allocation = auto_allocate_data.get("force_allocation", False)
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        result = await allocation_service.auto_allocate_classes(
            academic_year=auto_allocate_data["academic_year"],
            semester=auto_allocate_data["semester"],
            force_allocation=force_allocation
        )
        
        message = "Class allocation suggestions generated successfully"
        if force_allocation:
            message = "Classes auto-allocated successfully"
        
        return ResponseFormatter.success(
            data=result,
            message=message
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in auto-allocation: {str(e)}")

@router.get("/teacher/{teacher_id}/load", response_model=Dict[str, Any])
async def get_teacher_load(
    teacher_id: str = Path(..., description="Teacher ID"),
    academic_year: Optional[str] = Query(None, description="Academic year"),
    semester: Optional[str] = Query(None, description="Semester"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get teacher's current load information"""
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        # Get teacher's allocations
        allocations = await allocation_service.get_class_allocations(
            teacher_id=teacher_id,
            academic_year=academic_year,
            semester=semester
        )
        
        # Calculate load
        total_load = sum(alloc.load_percentage for alloc in allocations)
        
        load_breakdown = {}
        for alloc in allocations:
            load_breakdown[alloc.class_id] = {
                "subject": alloc.subject_id,
                "load_percentage": alloc.load_percentage,
                "teaching_method": alloc.teaching_method,
                "status": alloc.allocation_status
            }
        
        return ResponseFormatter.success(
            data={
                "teacher_id": teacher_id,
                "academic_year": academic_year,
                "semester": semester,
                "total_load_percentage": total_load,
                "allocations_count": len(allocations),
                "load_breakdown": load_breakdown,
                "capacity_status": self._get_capacity_status(total_load)
            },
            message="Teacher load information retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating teacher load: {str(e)}")

# region: Availability Management
@router.post("/availability/teacher", response_model=Dict[str, Any])
async def create_teacher_availability(
    availability_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Create teacher availability"""
    
    required_fields = ["teacher_id", "day_of_week", "start_time", "end_time", "academic_year", "semester"]
    for field in required_fields:
        if field not in availability_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        availability = await allocation_service.create_teacher_availability(
            teacher_id=availability_data["teacher_id"],
            day_of_week=availability_data["day_of_week"],
            start_time=availability_data["start_time"],
            end_time=availability_data["end_time"],
            academic_year=availability_data["academic_year"],
            semester=availability_data["semester"],
            preference_level=availability_data.get("preference_level", 1),
            notes=availability_data.get("notes")
        )
        
        return ResponseFormatter.success(
            data=availability.__dict__,
            message="Teacher availability created successfully",
            status_code=201
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating availability: {str(e)}")

@router.get("/availability/teacher/{teacher_id}", response_model=Dict[str, Any])
async def get_teacher_availability(
    teacher_id: str = Path(..., description="Teacher ID"),
    academic_year: Optional[str] = Query(None, description="Academic year"),
    semester: Optional[str] = Query(None, description="Semester"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get teacher's availability"""
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        # Placeholder implementation - would need to get availability data
        return ResponseFormatter.success(
            data={
                "teacher_id": teacher_id,
                "academic_year": academic_year,
                "semester": semester,
                "availability": []
            },
            message="Teacher availability retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving availability: {str(e)}")

@router.post("/availability/check", response_model=Dict[str, Any])
async def check_teacher_availability(
    availability_check: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Check teacher availability for specific time slot"""
    
    required_fields = ["teacher_id", "day_of_week", "start_time", "end_time", "academic_year", "semester"]
    for field in required_fields:
        if field not in availability_check:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        result = await allocation_service.check_teacher_availability(
            teacher_id=availability_check["teacher_id"],
            day_of_week=availability_check["day_of_week"],
            start_time=availability_check["start_time"],
            end_time=availability_check["end_time"],
            academic_year=availability_check["academic_year"],
            semester=availability_check["semester"]
        )
        
        return ResponseFormatter.success(
            data=result,
            message="Availability check completed"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking availability: {str(e)}")

# region: Request Management
@router.post("/requests", response_model=Dict[str, Any])
async def create_allocation_request(
    request_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Create allocation request"""
    
    required_fields = ["class_id", "subject_id", "academic_year", "semester"]
    for field in required_fields:
        if field not in request_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        request = await allocation_service.create_allocation_request(
            class_id=request_data["class_id"],
            subject_id=request_data["subject_id"],
            academic_year=request_data["academic_year"],
            semester=request_data["semester"],
            request_reason=request_data.get("request_reason"),
            special_requirements=request_data.get("special_requirements"),
            requested_teacher_id=request_data.get("requested_teacher_id"),
            requested_by=current_user.get("user_id") or "system"
        )
        
        return ResponseFormatter.success(
            data=request.__dict__,
            message="Allocation request created successfully",
            status_code=201
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating request: {str(e)}")

@router.put("/requests/{request_id}/approve", response_model=Dict[str, Any])
async def approve_allocation_request(
    request_id: str = Path(..., description="Request ID"),
    approval_data: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Approve allocation request"""
    
    required_fields = ["approved_teacher_id"]
    for field in required_fields:
        if field not in approval_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        allocation = await allocation_service.approve_allocation_request(
            request_id=request_id,
            approved_teacher_id=approval_data["approved_teacher_id"],
            notes=approval_data.get("notes")
        )
        
        return ResponseFormatter.success(
            data=allocation.__dict__,
            message="Allocation request approved successfully"
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving request: {str(e)}")

@router.get("/requests", response_model=Dict[str, Any])
async def get_allocation_requests(
    status: Optional[str] = Query(None, description="Request status filter"),
    academic_year: Optional[str] = Query(None, description="Academic year filter"),
    semester: Optional[str] = Query(None, description="Semester filter"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get allocation requests"""
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        # Placeholder implementation
        return ResponseFormatter.success(
            data={},
            message="Allocation requests retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving requests: {str(e)}")

# region: Timetable Management
@router.post("/timetable/optimize", response_model=Dict[str, Any])
async def optimize_timetable(
    timetable_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Optimize timetable for given academic year and semester"""
    
    required_fields = ["academic_year", "semester"]
    for field in required_fields:
        if field not in timetable_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        result = await allocation_service.optimize_timetable(
            academic_year=timetable_data["academic_year"],
            semester=timetable_data["semester"],
            constraints=timetable_data.get("constraints", [])
        )
        
        return ResponseFormatter.success(
            data=result,
            message="Timetable optimized successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing timetable: {str(e)}")

@router.get("/timetable/{academic_year}/{semester}", response_model=Dict[str, Any])
async def get_timetable(
    academic_year: str = Path(..., description="Academic year"),
    semester: str = Path(..., description="Semester"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get timetable for given academic year and semester"""
    
    allocation_service = service_container.get_allocation_service()
    
    try:
        # Placeholder implementation
        return ResponseFormatter.success(
            data={
                "academic_year": academic_year,
                "semester": semester,
                "timetable": []
            },
            message="Timetable retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving timetable: {str(e)}")

# region: Helper Methods
def _get_capacity_status(total_load: float) -> str:
    """Get capacity status based on load percentage"""
    if total_load < 80:
        return "under_capacity"
    elif total_load <= 100:
        return "optimal_capacity"
    elif total_load <= 120:
        return "over_capacity"
    else:
        return "overloaded"