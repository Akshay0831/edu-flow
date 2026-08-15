"""
Course Outcomes Management API Endpoints

This module provides REST API endpoints for course outcomes management operations:
- CRUD operations for course outcomes
- PO/CO mapping and tracking
- Outcome assessment and evaluation
- Performance analysis
- Reporting and analytics

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field, validator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.security import auth_service
from src.core.exceptions import ValidationError, NotFoundError, AuthenticationError, AuthorizationError
from src.infrastructure.repositories.outcomes_repository import OutcomesRepository

# Create router
router = APIRouter(prefix="/outcomes", tags=["outcomes"])

# Security
security = HTTPBearer()

# Repositories
outcomes_repo = OutcomesRepository()


# Pydantic models
class OutcomeBase(BaseModel):
    course_id: str = Field(..., min_length=2)
    outcome_code: str = Field(..., min_length=1, max_length=10)
    outcome_description: str = Field(..., max_length=500)
    outcome_type: str = Field(..., description="knowledge, skill, attitude")
    po_mapping: Dict[str, int] = Field(..., description="Program outcome mapping with levels")
    co_mapping: Optional[Dict[str, int]] = Field(None, description="Course outcome mapping")
    weightage: float = Field(..., ge=0, le=100, description="Outcome weight percentage")
    assessment_methods: List[str] = Field(..., description="List of assessment methods")
    target_level: str = Field(..., description="Target achievement level")
    measurement_criteria: str = Field(..., description="Criteria for measurement")
    is_active: bool = Field(True)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class OutcomeCreate(OutcomeBase):
    pass


class OutcomeUpdate(BaseModel):
    course_id: Optional[str] = Field(None, min_length=2)
    outcome_code: Optional[str] = Field(None, min_length=1, max_length=10)
    outcome_description: Optional[str] = Field(None, max_length=500)
    outcome_type: Optional[str] = Field(None)
    po_mapping: Optional[Dict[str, int]] = Field(None)
    co_mapping: Optional[Dict[str, int]] = Field(None)
    weightage: Optional[float] = Field(None, ge=0, le=100)
    assessment_methods: Optional[List[str]] = Field(None)
    target_level: Optional[str] = Field(None)
    measurement_criteria: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)


class OutcomeResponse(OutcomeBase):
    id: str
    created_at: datetime
    updated_at: datetime
    assessment_count: int = 0
    average_achievement: float = 0.0
    is_mapped: bool = False
    mapped_course_count: int = 0
    mapped_program_count: int = 0
    
    class Config:
        from_attributes = True


class POMapping(BaseModel):
    po_code: str = Field(..., min_length=1, max_length=10)
    level: int = Field(..., ge=1, le=5, description="Mapping level")
    description: Optional[str] = Field(None, max_length=500)


class COMapping(BaseModel):
    co_code: str = Field(..., min_length=1, max_length=10)
    level: int = Field(..., ge=1, le=5, description="Mapping level")
    description: Optional[str] = Field(None, max_length=500)


class AssessmentRecord(BaseModel):
    assessment_id: str = Field(..., min_length=2)
    method: str = Field(..., description="assessment method")
    score: float = Field(..., ge=0, le=100)
    max_score: float = Field(..., ge=1)
    assessment_date: datetime = Field(...)
    student_id: str = Field(..., min_length=2)
    evaluator_id: str = Field(..., min_length=2)
    comments: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class OutcomePerformance(BaseModel):
    outcome_id: str
    outcome_code: str
    outcome_description: str
    total_assessments: int
    average_score: float
    pass_percentage: float
    target_level: str
    current_level: str
    gap_analysis: Dict[str, Any]
    recommendations: List[str]


@router.get("/", response_model=List[OutcomeResponse])
async def get_outcomes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    course_id: Optional[str] = Query(None),
    outcome_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    Get all outcomes with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        course_id: Filter by course ID
        outcome_type: Filter by outcome type
        is_active: Filter by active status
        search: Search term for description or code
        
    Returns:
        List of outcomes
    """
    try:
        outcomes = await outcomes_repo.get_all(
            skip=skip,
            limit=limit,
            course_id=course_id,
            outcome_type=outcome_type,
            is_active=is_active,
            search=search
        )
        
        # Add performance metrics
        for outcome in outcomes:
            performance = await outcomes_repo.get_outcome_performance(outcome.id)
            outcome.assessment_count = performance.get('total_assessments', 0)
            outcome.average_achievement = performance.get('average_score', 0.0)
            outcome.is_mapped = len(outcome.po_mapping) > 0
            outcome.mapped_course_count = performance.get('mapped_course_count', 0)
            outcome.mapped_program_count = performance.get('mapped_program_count', 0)
        
        return outcomes
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch outcomes: {str(e)}"
        )


@router.get("/{outcome_id}", response_model=OutcomeResponse)
async def get_outcome(outcome_id: str):
    """
    Get a specific outcome by ID
    
    Args:
        outcome_id: Outcome ID
        
    Returns:
        Outcome details
    """
    try:
        outcome = await outcomes_repo.get_by_id(outcome_id)
        if not outcome:
            raise NotFoundError(f"Outcome not found with ID: {outcome_id}")
        
        # Add performance metrics
        performance = await outcomes_repo.get_outcome_performance(outcome_id)
        outcome.assessment_count = performance.get('total_assessments', 0)
        outcome.average_achievement = performance.get('average_score', 0.0)
        outcome.is_mapped = len(outcome.po_mapping) > 0
        outcome.mapped_course_count = performance.get('mapped_course_count', 0)
        outcome.mapped_program_count = performance.get('mapped_program_count', 0)
        
        return outcome
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Outcome not found with ID: {outcome_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch outcome: {str(e)}"
        )


@router.post("/", response_model=OutcomeResponse, status_code=status.HTTP_201_CREATED)
async def create_outcome(
    outcome_data: OutcomeCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new course outcome
    
    Args:
        outcome_data: Outcome data
        credentials: JWT token
        
    Returns:
        Created outcome
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to create outcomes")
        
        # Validate weightage
        total_weightage = sum(outcome_data.po_mapping.values()) if outcome_data.po_mapping else 0
        if total_weightage > 100:
            raise ValidationError("Total PO mapping weightage cannot exceed 100")
        
        if outcome_data.weightage <= 0 or outcome_data.weightage > 100:
            raise ValidationError("Outcome weightage must be between 0 and 100")
        
        # Validate assessment methods
        if not outcome_data.assessment_methods:
            raise ValidationError("At least one assessment method is required")
        
        # Validate mapping levels
        for level in outcome_data.po_mapping.values():
            if level < 1 or level > 5:
                raise ValidationError("PO mapping level must be between 1 and 5")
        
        # Validate if course exists
        course_exists = await outcomes_repo.validate_course(outcome_data.course_id)
        if not course_exists:
            raise ValidationError("Course not found")
        
        # Create outcome
        outcome = await outcomes_repo.create(
            course_id=outcome_data.course_id,
            outcome_code=outcome_data.outcome_code,
            outcome_description=outcome_data.outcome_description,
            outcome_type=outcome_data.outcome_type,
            po_mapping=outcome_data.po_mapping,
            co_mapping=outcome_data.co_mapping,
            weightage=outcome_data.weightage,
            assessment_methods=outcome_data.assessment_methods,
            target_level=outcome_data.target_level,
            measurement_criteria=outcome_data.measurement_criteria,
            is_active=outcome_data.is_active,
            metadata=outcome_data.metadata
        )
        
        return outcome
        
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
            detail=f"Failed to create outcome: {str(e)}"
        )


@router.put("/{outcome_id}", response_model=OutcomeResponse)
async def update_outcome(
    outcome_id: str,
    outcome_data: OutcomeUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update an outcome
    
    Args:
        outcome_id: Outcome ID
        outcome_data: Updated outcome data
        credentials: JWT token
        
    Returns:
        Updated outcome
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to update outcomes")
        
        # Check if outcome exists
        existing_outcome = await outcomes_repo.get_by_id(outcome_id)
        if not existing_outcome:
            raise NotFoundError(f"Outcome not found with ID: {outcome_id}")
        
        # Validate weightage if updated
        if outcome_data.weightage is not None:
            if outcome_data.weightage <= 0 or outcome_data.weightage > 100:
                raise ValidationError("Outcome weightage must be between 0 and 100")
        
        # Validate PO mapping if updated
        if outcome_data.po_mapping is not None:
            total_weightage = sum(outcome_data.po_mapping.values())
            if total_weightage > 100:
                raise ValidationError("Total PO mapping weightage cannot exceed 100")
            
            for level in outcome_data.po_mapping.values():
                if level < 1 or level > 5:
                    raise ValidationError("PO mapping level must be between 1 and 5")
        
        # Validate assessment methods if updated
        if outcome_data.assessment_methods is not None:
            if not outcome_data.assessment_methods:
                raise ValidationError("At least one assessment method is required")
        
        # Validate course if updated
        if outcome_data.course_id:
            course_exists = await outcomes_repo.validate_course(outcome_data.course_id)
            if not course_exists:
                raise ValidationError("Course not found")
        
        # Update outcome
        outcome = await outcomes_repo.update(
            outcome_id=outcome_id,
            **outcome_data.dict(exclude_unset=True)
        )
        
        return outcome
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Outcome not found with ID: {outcome_id}"
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
            detail=f"Failed to update outcome: {str(e)}"
        )


@router.delete("/{outcome_id}")
async def delete_outcome(
    outcome_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete an outcome
    
    Args:
        outcome_id: Outcome ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to delete outcomes")
        
        # Check if outcome exists
        existing_outcome = await outcomes_repo.get_by_id(outcome_id)
        if not existing_outcome:
            raise NotFoundError(f"Outcome not found with ID: {outcome_id}")
        
        # Check if outcome has assessments
        has_assessments = await outcomes_repo.has_assessments(outcome_id)
        if has_assessments:
            raise ValidationError("Cannot delete outcome with existing assessments")
        
        # Delete outcome
        await outcomes_repo.delete(outcome_id)
        
        return {"message": "Outcome deleted successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Outcome not found with ID: {outcome_id}"
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
            detail=f"Failed to delete outcome: {str(e)}"
        )


@router.post("/{outcome_id}/assessment")
async def add_assessment_record(
    outcome_id: str,
    assessment: AssessmentRecord,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Add assessment record to an outcome
    
    Args:
        outcome_id: Outcome ID
        assessment: Assessment record
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to add assessments")
        
        # Check if outcome exists
        outcome_exists = await outcomes_repo.validate_outcome(outcome_id)
        if not outcome_exists:
            raise ValidationError("Outcome not found")
        
        # Validate score
        if assessment.score < 0 or assessment.score > assessment.max_score:
            raise ValidationError("Score must be between 0 and maximum score")
        
        # Validate student
        student_exists = await outcomes_repo.validate_student(assessment.student_id)
        if not student_exists:
            raise ValidationError("Student not found")
        
        # Validate evaluator
        evaluator_exists = await outcomes_repo.validate_teacher(assessment.evaluator_id)
        if not evaluator_exists:
            raise ValidationError("Evaluator not found")
        
        # Add assessment record
        await outcomes_repo.add_assessment_record(outcome_id, assessment)
        
        return {"message": "Assessment record added successfully"}
        
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
            detail=f"Failed to add assessment record: {str(e)}"
        )


@router.get("/outcomes/{outcome_id}/performance")
async def get_outcome_performance(
    outcome_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get outcome performance metrics
    
    Args:
        outcome_id: Outcome ID
        start_date: Start date filter (YYYY-MM-DD)
        end_date: End date filter (YYYY-MM-DD)
        credentials: JWT token
        
    Returns:
        Outcome performance metrics
    """
    try:
        performance = await outcomes_repo.get_outcome_performance(
            outcome_id=outcome_id,
            start_date=start_date,
            end_date=end_date
        )
        return performance
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch outcome performance: {str(e)}"
        )


@router.get("/course/{course_id}/outcomes")
async def get_course_outcomes(
    course_id: str,
    outcome_type: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get outcomes for a specific course
    
    Args:
        course_id: Course ID
        outcome_type: Filter by outcome type
        credentials: JWT token
        
    Returns:
        List of course outcomes
    """
    try:
        outcomes = await outcomes_repo.get_course_outcomes(
            course_id=course_id,
            outcome_type=outcome_type
        )
        return outcomes
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch course outcomes: {str(e)}"
        )


@router.get("/program/{program_id}/outcomes")
async def get_program_outcomes(
    program_id: str,
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get outcomes for a specific program
    
    Args:
        program_id: Program ID
        academic_year: Filter by academic year
        semester: Filter by semester
        credentials: JWT token
        
    Returns:
        Program outcomes with mapping details
    """
    try:
        outcomes = await outcomes_repo.get_program_outcomes(
            program_id=program_id,
            academic_year=academic_year,
            semester=semester
        )
        return outcomes
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch program outcomes: {str(e)}"
        )


@router.post("/{outcome_id}/po-mapping")
async def update_po_mapping(
    outcome_id: str,
    po_mappings: List[POMapping],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update PO mapping for an outcome
    
    Args:
        outcome_id: Outcome ID
        po_mappings: List of PO mappings
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to update PO mappings")
        
        # Validate mappings
        if not po_mappings:
            raise ValidationError("At least one PO mapping is required")
        
        for mapping in po_mappings:
            if mapping.level < 1 or mapping.level > 5:
                raise ValidationError("PO mapping level must be between 1 and 5")
        
        # Update PO mapping
        await outcomes_repo.update_po_mapping(outcome_id, po_mappings)
        
        return {"message": "PO mapping updated successfully"}
        
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
            detail=f"Failed to update PO mapping: {str(e)}"
        )


@router.get("/analysis/gap-analysis")
async def get_outcome_gap_analysis(
    course_id: Optional[str] = Query(None),
    program_id: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get outcome gap analysis
    
    Args:
        course_id: Filter by course ID
        program_id: Filter by program ID
        academic_year: Filter by academic year
        semester: Filter by semester
        credentials: JWT token
        
    Returns:
        Gap analysis results
    """
    try:
        analysis = await outcomes_repo.get_outcome_gap_analysis(
            course_id=course_id,
            program_id=program_id,
            academic_year=academic_year,
            semester=semester
        )
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch gap analysis: {str(e)}"
        )


@router.get("/analysis/improvement-suggestions")
async def get_improvement_suggestions(
    course_id: Optional[str] = Query(None),
    outcome_type: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get improvement suggestions for outcomes
    
    Args:
        course_id: Filter by course ID
        outcome_type: Filter by outcome type
        credentials: JWT token
        
    Returns:
        Improvement suggestions
    """
    try:
        suggestions = await outcomes_repo.get_improvement_suggestions(
            course_id=course_id,
            outcome_type=outcome_type
        )
        return suggestions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch improvement suggestions: {str(e)}"
        )