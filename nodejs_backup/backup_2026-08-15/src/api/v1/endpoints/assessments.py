"""
Assessment API endpoints for assessment management.

This module provides:
- Assessment CRUD operations
- Grade management
- Performance tracking
- Student assessment results
- Health checks
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from src.core.exceptions import ValidationError, NotFoundError, AuthenticationError
from src.core.security import AuthService
from src.core.response_handler import ResponseFormatter


router = APIRouter()
security = HTTPBearer()

logger = logging.getLogger(__name__)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user."""
    try:
        token = credentials.credentials
        user = await verify_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/", response_model=Dict[str, Any])
async def create_assessment(
    assessment_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """Create a new assessment."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin', 'teacher']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and teachers can create assessments"
            )
        
        # Validate assessment data
        if not assessment_data.get('title'):
            raise ValidationError("Title is required", "title")
        
        if not assessment_data.get('course_id'):
            raise ValidationError("Course ID is required", "course_id")
        
        if not assessment_data.get('type'):
            raise ValidationError("Assessment type is required", "type")
        
        if not assessment_data.get('total_marks'):
            raise ValidationError("Total marks is required", "total_marks")
        
        # Validate total marks
        if not isinstance(assessment_data['total_marks'], (int, float)) or assessment_data['total_marks'] <= 0:
            raise ValidationError("Total marks must be a positive number", "total_marks")
        
        # Create assessment
        assessment_id = await assessment_service.create_assessment(assessment_data)
        
        # Get created assessment
        created_assessment = await assessment_service.get_assessment_by_id(assessment_id)
        
        logger.info(f"Assessment created: {assessment_id}")
        return ResponseFormatter.success(
            data=created_assessment,
            message="Assessment created successfully",
            status_code=status.HTTP_201_CREATED
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error creating assessment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating assessment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{assessment_id}", response_model=Dict[str, Any])
async def get_assessment(
    assessment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """Get assessment by ID."""
    try:
        assessment = await assessment_service.get_assessment_by_id(assessment_id)
        if not assessment:
            raise NotFoundError("Assessment not found", "assessment_id")
        
        return ResponseFormatter.success(
            data=assessment,
            message="Assessment retrieved successfully"
        )
        
    except NotFoundError as e:
        logger.warning(f"Assessment not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assessment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/{assessment_id}", response_model=Dict[str, Any])
async def update_assessment(
    assessment_id: str,
    update_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """Update assessment information."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin', 'teacher']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and teachers can update assessments"
            )
        
        # Validate update data
        if not update_data:
            raise ValidationError("Update data is required", "update_data")
        
        # Validate total marks if provided
        if 'total_marks' in update_data:
            if not isinstance(update_data['total_marks'], (int, float)) or update_data['total_marks'] <= 0:
                raise ValidationError("Total marks must be a positive number", "total_marks")
        
        # Update assessment
        result = await assessment_service.update_assessment(assessment_id, update_data)
        
        if result == 0:
            raise NotFoundError("Assessment not found", "assessment_id")
        
        # Get updated assessment
        updated_assessment = await assessment_service.get_assessment_by_id(assessment_id)
        
        logger.info(f"Assessment updated: {assessment_id}")
        return ResponseFormatter.success(
            data=updated_assessment,
            message="Assessment updated successfully"
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error updating assessment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        logger.warning(f"Assessment not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating assessment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/", response_model=Dict[str, Any])
async def get_assessments(
    course_id: Optional[str] = Query(None),
    teacher_id: Optional[str] = Query(None),
    assessment_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """Get assessments with filtering and pagination."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin', 'teacher', 'student']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Build filter based on user role
        filter_dict = {}
        
        if course_id:
            filter_dict["course_id"] = course_id
        
        if teacher_id and current_user.get('role') == 'admin':
            filter_dict["teacher_id"] = teacher_id
        
        if assessment_type:
            filter_dict["type"] = assessment_type
        
        # Students can only see assessments from their courses
        if current_user.get('role') == 'student':
            # This would typically be implemented with a join to get student's courses
            # For now, we'll filter by course if provided
            if not course_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Course ID is required for students"
                )
        
        # Get assessments
        assessments = await assessment_service.find_many(
            "assessments",
            filter_dict,
            limit=limit,
            skip=skip
        )
        
        # Get total count
        total = await assessment_service._database.count("assessments", filter_dict)
        
        return ResponseFormatter.success(
            data={
                "assessments": assessments,
                "pagination": {
                    "total": total,
                    "skip": skip,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit
                }
            },
            message="Assessments retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assessments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/{assessment_id}", response_model=Dict[str, Any])
async def delete_assessment(
    assessment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """Delete an assessment."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin', 'teacher']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and teachers can delete assessments"
            )
        
        # Get assessment first
        assessment = await assessment_service.get_assessment_by_id(assessment_id)
        if not assessment:
            raise NotFoundError("Assessment not found", "assessment_id")
        
        # Delete assessment
        result = await assessment_service.delete_one("assessments", {"id": assessment_id})
        
        if result == 0:
            raise NotFoundError("Assessment not found", "assessment_id")
        
        logger.info(f"Assessment deleted: {assessment_id}")
        return ResponseFormatter.success(
            message="Assessment deleted successfully"
        )
        
    except NotFoundError as e:
        logger.warning(f"Assessment not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting assessment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{assessment_id}/results", response_model=Dict[str, Any])
async def get_assessment_results(
    assessment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """Get results for an assessment."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin', 'teacher']:
            # Students can only see their own results
            if current_user.get('role') == 'student':
                # This would typically check if the student has access to this assessment
                # For now, we'll allow it but implement proper access control later
                pass
        
        # Get assessment
        assessment = await assessment_service.get_assessment_by_id(assessment_id)
        if not assessment:
            raise NotFoundError("Assessment not found", "assessment_id")
        
        # This would typically implement student result retrieval
        # For now, we'll return a placeholder response
        results = []  # Placeholder - implement actual result retrieval logic
        
        return ResponseFormatter.success(
            data={
                "assessment_id": assessment_id,
                "assessment_title": assessment.get('title'),
                "results": results,
                "total_students": len(results)
            },
            message="Assessment results retrieved successfully"
        )
        
    except NotFoundError as e:
        logger.warning(f"Assessment not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assessment results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{assessment_id}/health", response_model=Dict[str, Any])
async def assessment_service_health(
    assessment_id: str,
    assessment_service: AssessmentService = Depends(get_assessment_service)
):
    """Health check for assessment service."""
    try:
        health_status = await assessment_service.health_check()
        return ResponseFormatter.success(
            data=health_status,
            message="Assessment service health check completed"
        )
    except Exception as e:
        logger.error(f"Error checking assessment service health: {str(e)}")
        return ResponseFormatter.error(
            message="Assessment service health check failed",
            error_code="SERVICE_HEALTH_ERROR",
            details={"error": str(e)}
        )