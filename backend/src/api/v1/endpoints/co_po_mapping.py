"""
CO-PO Mapping API Endpoints

This module provides REST API endpoints for CO-PO mapping functionality:
- CRUD operations for CO-PO mappings
- Attainment calculation and reporting
- Batch analysis and report generation
- Configuration management
- Export functionality

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_current_user, get_service_container
from src.services.co_po_mapping_service import COPOMappingService
from src.core.response_handler import ResponseFormatter
from src.core.exceptions import ValidationError, NotFoundError
from src.models.co_po_mapping import COPOMapping, AttainmentLevel, AttainmentGrade
from src.services.base_service import ServiceContainer

router = APIRouter(prefix="/co-po-mapping", tags=["CO-PO Mapping"])

# region: Basic CRUD Endpoints
@router.post("/mappings", response_model=Dict[str, Any])
async def create_mapping(
    mapping_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """
    Create a new CO-PO mapping
    
    **Required:**
    - course_id: Course ID
    - program_outcome_id: Program Outcome ID  
    - course_outcome_id: Course Outcome ID
    
    **Optional:**
    - weight: Mapping weight (default: 1.0)
    - mapping_type: Type of mapping (default: "direct")
    - attainment_thresholds: Custom attainment thresholds
    - mapping_description: Description of the mapping
    """
    
    co_po_service = service_container.get_co_po_mapping_service()
    
    try:
        mapping = await co_po_service.create_mapping(
            course_id=mapping_data["course_id"],
            program_outcome_id=mapping_data["program_outcome_id"],
            course_outcome_id=mapping_data["course_outcome_id"],
            weight=mapping_data.get("weight", 1.0),
            mapping_type=mapping_data.get("mapping_type", "direct"),
            attainment_thresholds=mapping_data.get("attainment_thresholds"),
            mapping_description=mapping_data.get("mapping_description")
        )
        
        return ResponseFormatter.success(
            data=mapping.__dict__,
            message="CO-PO mapping created successfully",
            status_code=201
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating mapping: {str(e)}")

@router.get("/mappings/{mapping_id}", response_model=Dict[str, Any])
async def get_mapping(
    mapping_id: str = Path(..., description="CO-PO mapping ID"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get a specific CO-PO mapping by ID"""
    
    co_po_service = service_container.get_co_po_mapping_service()
    
    try:
        mapping = await co_po_service.get_mapping_by_id(mapping_id)
        
        if not mapping:
            raise NotFoundError(f"CO-PO mapping not found: {mapping_id}")
        
        return ResponseFormatter.success(
            data=mapping.__dict__,
            message="CO-PO mapping retrieved successfully"
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving mapping: {str(e)}")

@router.get("/courses/{course_id}/mappings", response_model=Dict[str, Any])
async def get_course_mappings(
    course_id: str = Path(..., description="Course ID"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get all CO-PO mappings for a specific course"""
    
    co_po_service = service_container.get_co_po_mapping_service()
    
    try:
        mappings = await co_po_service.get_mappings_by_course(course_id)
        
        return ResponseFormatter.success(
            data=[mapping.__dict__ for mapping in mappings],
            message=f"Found {len(mappings)} CO-PO mappings for course {course_id}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving course mappings: {str(e)}")

@router.get("/program-outcomes/{program_outcome_id}/mappings", response_model=Dict[str, Any])
async def get_program_outcome_mappings(
    program_outcome_id: str = Path(..., description="Program Outcome ID"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get all CO-PO mappings for a specific program outcome"""
    
    co_po_service = service_container.get_co_po_mapping_service()
    
    try:
        mappings = await co_po_service.get_mappings_by_program_outcome(program_outcome_id)
        
        return ResponseFormatter.success(
            data=[mapping.__dict__ for mapping in mappings],
            message=f"Found {len(mappings)} CO-PO mappings for program outcome {program_outcome_id}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving program outcome mappings: {str(e)}")

@router.put("/mappings/{mapping_id}", response_model=Dict[str, Any])
async def update_mapping(
    mapping_id: str = Path(..., description="CO-PO mapping ID"),
    updates: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Update a CO-PO mapping"""
    
    co_po_service = service_container.get_co_po_mapping_service()
    
    try:
        mapping = await co_po_service.update_mapping(mapping_id, updates)
        
        return ResponseFormatter.success(
            data=mapping.__dict__,
            message="CO-PO mapping updated successfully"
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating mapping: {str(e)}")

@router.delete("/mappings/{mapping_id}", response_model=Dict[str, Any])
async def delete_mapping(
    mapping_id: str = Path(..., description="CO-PO mapping ID"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Delete a CO-PO mapping"""
    
    co_po_service = service_container.get_co_po_mapping_service()
    
    try:
        success = await co_po_service.delete_mapping(mapping_id)
        
        if success:
            return ResponseFormatter.success(
                data={"deleted": True, "mapping_id": mapping_id},
                message="CO-PO mapping deleted successfully"
            )
        else:
            raise NotFoundError(f"CO-PO mapping not found: {mapping_id}")
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting mapping: {str(e)}")

# region: Attainment Calculation Endpoints
@router.post("/attainment/student", response_model=Dict[str, Any])
async def calculate_student_attainment(
    attainment_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Calculate attainment for a specific student"""
    
    co_po_service = service_container.get_co_po_mapping_service()
    
    required_fields = ["student_id", "course_id", "assessment_scores"]
    for field in required_fields:
        if field not in attainment_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    try:
        result = await co_po_service.calculate_student_attainment(
            student_id=attainment_data["student_id"],
            course_id=attainment_data["course_id"],
            assessment_scores=attainment_data["assessment_scores"]
        )
        
        return ResponseFormatter.success(
            data=result,
            message="Student attainment calculated successfully"
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating student attainment: {str(e)}")

@router.post("/attainment/batch", response_model=Dict[str, Any])
async def calculate_batch_attainment(
    batch_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Calculate attainment for an entire batch"""
    
    co_po_service = service_container.get_co_po_mapping_service()
    
    required_fields = ["course_id", "batch_id", "academic_year", "semester", "student_assessments"]
    for field in required_fields:
        if field not in batch_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    try:
        result = await co_po_service.calculate_batch_attainment(
            course_id=batch_data["course_id"],
            batch_id=batch_data["batch_id"],
            academic_year=batch_data["academic_year"],
            semester=batch_data["semester"],
            student_assessments=batch_data["student_assessments"]
        )
        
        return ResponseFormatter.success(
            data=result,
            message="Batch attainment calculated successfully"
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating batch attainment: {str(e)}")

# region: Report Generation Endpoints
@router.get("/reports/attainment", response_model=Dict[str, Any])
async def get_attainment_report(
    course_id: str = Query(..., description="Course ID"),
    program_outcome_id: Optional[str] = Query(None, description="Program Outcome ID"),
    batch_id: Optional[str] = Query(None, description="Batch ID"),
    academic_year: Optional[str] = Query(None, description="Academic Year"),
    semester: Optional[str] = Query(None, description="Semester"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Generate attainment report"""
    
    co_po_service = service_container.get_co_po_mapping_service()
    
    try:
        report = await co_po_service.generate_attainment_report(
            course_id=course_id,
            program_outcome_id=program_outcome_id,
            batch_id=batch_id,
            academic_year=academic_year,
            semester=semester
        )
        
        return ResponseFormatter.success(
            data=report,
            message="Attainment report generated successfully"
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@router.post("/reports/attainment/export", response_model=Dict[str, Any])
async def export_attainment_report(
    export_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Export attainment report in specified format"""
    
    required_fields = ["course_id", "format"]
    for field in required_fields:
        if field not in export_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    co_po_service = service_container.get_co_po_mapping_service()
    
    try:
        # Extract filters
        filters = {
            "program_outcome_id": export_data.get("program_outcome_id"),
            "batch_id": export_data.get("batch_id"),
            "academic_year": export_data.get("academic_year"),
            "semester": export_data.get("semester")
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        exported_file = await co_po_service.export_attainment_report(
            course_id=export_data["course_id"],
            format=export_data["format"],
            **filters
        )
        
        return ResponseFormatter.success(
            data={"exported_file": exported_file, "format": export_data["format"]},
            message="Report exported successfully"
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting report: {str(e)}")

# region: Configuration Management Endpoints
@router.post("/config", response_model=Dict[str, Any])
async def create_mapping_config(
    config_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Create mapping configuration"""
    
    required_fields = ["mapping_type"]
    for field in required_fields:
        if field not in config_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    co_po_service = service_container.get_co_po_mapping_service()
    
    try:
        config = await co_po_service.create_mapping_config(
            mapping_type=config_data["mapping_type"],
            calculation_method=config_data.get("calculation_method", "weighted_average"),
            default_thresholds=config_data.get("default_thresholds"),
            description=config_data.get("description")
        )
        
        return ResponseFormatter.success(
            data=config.__dict__,
            message="Mapping configuration created successfully",
            status_code=201
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating configuration: {str(e)}")

@router.get("/config/{mapping_type}", response_model=Dict[str, Any])
async def get_default_config(
    mapping_type: str = Path(..., description="Mapping type"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get default configuration for mapping type"""
    
    co_po_service = service_container.get_co_po_mapping_service()
    
    try:
        config = await co_po_service.get_default_config(mapping_type)
        
        if not config:
            raise NotFoundError(f"Configuration not found for mapping type: {mapping_type}")
        
        return ResponseFormatter.success(
            data=config.__dict__,
            message="Configuration retrieved successfully"
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving configuration: {str(e)}")

# region: Utility Endpoints
@router.get("/outcomes/course", response_model=Dict[str, Any])
async def get_course_outcomes(
    course_id: str = Query(..., description="Course ID"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Get course outcomes for a course"""
    
    # This would integrate with your course outcome service
    # Placeholder implementation
    return ResponseFormatter.success(
        data={"course_id": course_id, "outcomes": []},
        message="Course outcomes retrieved successfully"
    )

@router.get("/outcomes/program", response_model=Dict[str, Any])
async def get_program_outcomes(
    program_id: str = Query(..., description="Program ID"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Get program outcomes for a program"""
    
    # This would integrate with your program outcome service
    # Placeholder implementation
    return ResponseFormatter.success(
        data={"program_id": program_id, "outcomes": []},
        message="Program outcomes retrieved successfully"
    )

@router.get("/attainment/thresholds", response_model=Dict[str, Any])
async def get_attainment_thresholds(
    mapping_type: str = Query("direct", description="Mapping type"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get default attainment thresholds"""
    
    co_po_service = service_container.get_co_po_mapping_service()
    
    try:
        config = await co_po_service.get_default_config(mapping_type)
        
        thresholds = config.default_thresholds or {
            "excellent": 90,
            "very_good": 80,
            "good": 70,
            "satisfactory": 60,
            "poor": 40
        }
        
        return ResponseFormatter.success(
            data={
                "mapping_type": mapping_type,
                "attainment_thresholds": thresholds,
                "calculation_method": config.calculation_method if config else "weighted_average"
            },
            message="Attainment thresholds retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving thresholds: {str(e)}")

# region: Analytics Endpoints
@router.get("/analytics/course/{course_id}", response_model=Dict[str, Any])
async def get_course_attainment_analytics(
    course_id: str = Path(..., description="Course ID"),
    academic_year: Optional[str] = Query(None, description="Academic Year"),
    semester: Optional[str] = Query(None, description="Semester"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get attainment analytics for a course"""
    
    co_po_service = service_container.get_co_po_mapping_service()
    
    try:
        # Generate report with analytics
        report = await co_po_service.generate_attainment_report(
            course_id=course_id,
            academic_year=academic_year,
            semester=semester
        )
        
        # Extract analytics from report
        analytics = {
            "course_id": course_id,
            "academic_year": academic_year,
            "semester": semester,
            "summary": report["summary"],
            "trends": report.get("trends", {}),
            "recommendations": report.get("recommendations", [])
        }
        
        return ResponseFormatter.success(
            data=analytics,
            message="Course analytics generated successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating analytics: {str(e)}")

@router.get("/analytics/program/{program_id}", response_model=Dict[str, Any])
async def get_program_attainment_analytics(
    program_id: str = Path(..., description="Program ID"),
    academic_year: Optional[str] = Query(None, description="Academic Year"),
    semester: Optional[str] = Query(None, description="Semester"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get attainment analytics for a program"""
    
    # This would integrate multiple course analytics
    # Placeholder implementation
    return ResponseFormatter.success(
        data={"program_id": program_id, "analytics": {}},
        message="Program analytics generated successfully"
    )