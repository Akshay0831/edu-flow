"""
Grade Management API Endpoints

This module provides REST API endpoints for grade management operations:
- CRUD operations for grades
- Grade calculation and processing
- Grade reporting and analytics
- Grade policy enforcement
- Bulk grade management

Author: Edu-Flow Team
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, File, UploadFile
from pydantic import BaseModel, Field, validator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.security import auth_service
from core.exceptions import ValidationError, NotFoundError, AuthenticationError, AuthorizationError
from infrastructure.repositories.grade_repository import GradeRepository

# Create router
router = APIRouter(prefix="/grades", tags=["grades"])

# Security
security = HTTPBearer()

# Repositories
grade_repo = GradeRepository()


# Pydantic models
class GradeBase(BaseModel):
    student_id: str = Field(..., min_length=2)
    assessment_id: str = Field(..., min_length=2)
    class_id: str = Field(..., min_length=2)
    subject_id: str = Field(..., min_length=2)
    academic_year: str = Field(..., min_length=4, max_length=10)
    semester: int = Field(..., ge=1, le=12)
    assessment_type: str = Field(..., description="quiz, exam, assignment, project, attendance")
    assessment_name: str = Field(..., max_length=100)
    total_marks: float = Field(..., ge=0)
    obtained_marks: float = Field(..., ge=0)
    percentage: float = Field(..., ge=0, le=100)
    grade: str = Field(..., max_length=5)
    grade_point: float = Field(..., ge=0)
    status: str = Field(..., description="draft, submitted, reviewed, final")
    weightage: float = Field(..., ge=0, le=100, description="Assessment weightage")
    examiner_id: str = Field(..., min_length=2)
    review_notes: Optional[str] = Field(None, max_length=1000)
    feedback: Optional[str] = Field(None, max_length=1000)
    comments: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GradeCreate(GradeBase):
    pass


class GradeUpdate(BaseModel):
    total_marks: Optional[float] = Field(None, ge=0)
    obtained_marks: Optional[float] = Field(None, ge=0)
    percentage: Optional[float] = Field(None, ge=0, le=100)
    grade: Optional[str] = Field(None, max_length=5)
    grade_point: Optional[float] = Field(None, ge=0)
    status: Optional[str] = Field(None)
    weightage: Optional[float] = Field(None, ge=0, le=100)
    examiner_id: Optional[str] = Field(None, min_length=2)
    review_notes: Optional[str] = Field(None, max_length=1000)
    feedback: Optional[str] = Field(None, max_length=1000)
    comments: Optional[str] = Field(None, max_length=500)


class GradeResponse(GradeBase):
    id: str
    created_at: datetime
    updated_at: datetime
    recorded_at: datetime
    is_released: bool
    release_date: Optional[datetime]
    course_name: str
    student_name: str
    examiner_name: str
    grade_position: int = 0
    subject_average: float = 0.0
    class_average: float = 0.0
    subject_position: int = 0
    class_position: int = 0
    
    class Config:
        from_attributes = True


class GradePolicy(BaseModel):
    policy_name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    academic_year: str = Field(..., min_length=4, max_length=10)
    semester: int = Field(..., ge=1, le=12)
    grading_scale: Dict[str, str] = Field(..., description="Grade mapping (e.g., '90-100': 'A')")
    passing_grade: str = Field(..., max_length=5)
    minimum_passing_percentage: float = Field(..., ge=0, le=100)
    late_penalty_policy: str = Field(..., description="Late submission penalty policy")
    plagiarism_policy: str = Field(..., description="Plagiarism handling policy")
    revision_policy: str = Field(..., description="Grade revision policy")
    is_active: bool = Field(True)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GradePolicyCreate(GradePolicy):
    pass


class GradeBulkUpload(BaseModel):
    class_id: str = Field(..., min_length=2)
    assessment_id: str = Field(..., min_length=2)
    assessment_type: str = Field(..., description="quiz, exam, assignment, project, attendance")
    assessment_name: str = Field(..., max_length=100)
    weightage: float = Field(..., ge=0, le=100)
    grades: List[Dict[str, Any]] = Field(..., description="List of grade data")
    batch_reason: Optional[str] = Field(None, description="Reason for bulk upload")
    examiner_id: str = Field(..., min_length=2)


class GradeStats(BaseModel):
    student_id: str
    student_name: str
    total_assessments: int
    average_marks: float
    total_marks: float
    percentage: float
    grade: str
    grade_point: float
    subject_rank: int
    class_rank: int
    academic_performance: str
    improvement_trend: str


class SubjectGradeStats(BaseModel):
    subject_id: str
    subject_name: str
    total_students: int
    average_marks: float
    average_percentage: float
    average_grade_point: float
    grade_distribution: Dict[str, int]
    highest_marks: float
    lowest_marks: float
    pass_percentage: float
    distinction_percentage: float


class ClassGradeStats(BaseModel):
    class_id: str
    class_name: str
    subject_id: str
    total_students: int
    average_marks: float
    average_percentage: float
    average_grade_point: float
    grade_distribution: Dict[str, int]
    highest_marks: float
    lowest_marks: float
    pass_percentage: float
    distinction_percentage: float
    subject_stats: SubjectGradeStats
    individual_stats: List[GradeStats]


@router.get("/", response_model=List[GradeResponse])
async def get_grades(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    student_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    assessment_id: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    assessment_type: Optional[str] = Query(None),
    grade: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_released: Optional[bool] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    Get grades with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        student_id: Filter by student ID
        class_id: Filter by class ID
        subject_id: Filter by subject ID
        assessment_id: Filter by assessment ID
        academic_year: Filter by academic year
        semester: Filter by semester
        assessment_type: Filter by assessment type
        grade: Filter by grade
        status: Filter by status
        is_released: Filter by release status
        search: Search term in student name or assessment name
        
    Returns:
        List of grades
    """
    try:
        grades = await grade_repo.get_all(
            skip=skip,
            limit=limit,
            student_id=student_id,
            class_id=class_id,
            subject_id=subject_id,
            assessment_id=assessment_id,
            academic_year=academic_year,
            semester=semester,
            assessment_type=assessment_type,
            grade=grade,
            status=status,
            is_released=is_released,
            search=search
        )
        
        # Add derived information
        for grade in grades:
            grade.grade_position = await grade_repo.get_grade_position(grade.id)
            grade.subject_average = await grade_repo.get_subject_average(grade.subject_id, grade.academic_year, grade.semester)
            grade.class_average = await grade_repo.get_class_average(grade.class_id, grade.subject_id, grade.academic_year, grade.semester)
            grade.subject_position = await grade_repo.get_subject_position(grade.id)
            grade.class_position = await grade_repo.get_class_position(grade.id)
            grade.course_name = await grade_repo.get_course_name(grade.subject_id)
            grade.student_name = await grade_repo.get_student_name(grade.student_id)
            grade.examiner_name = await grade_repo.get_teacher_name(grade.examiner_id)
        
        return grades
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grades: {str(e)}"
        )


@router.get("/{grade_id}", response_model=GradeResponse)
async def get_grade(grade_id: str):
    """
    Get a specific grade by ID
    
    Args:
        grade_id: Grade ID
        
    Returns:
        Grade details
    """
    try:
        grade = await grade_repo.get_by_id(grade_id)
        if not grade:
            raise NotFoundError(f"Grade not found with ID: {grade_id}")
        
        # Add derived information
        grade.grade_position = await grade_repo.get_grade_position(grade_id)
        grade.subject_average = await grade_repo.get_subject_average(grade.subject_id, grade.academic_year, grade.semester)
        grade.class_average = await grade_repo.get_class_average(grade.class_id, grade.subject_id, grade.academic_year, grade.semester)
        grade.subject_position = await grade_repo.get_subject_position(grade_id)
        grade.class_position = await grade_repo.get_class_position(grade_id)
        grade.course_name = await grade_repo.get_course_name(grade.subject_id)
        grade.student_name = await grade_repo.get_student_name(grade.student_id)
        grade.examiner_name = await grade_repo.get_teacher_name(grade.examiner_id)
        
        return grade
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grade not found with ID: {grade_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grade: {str(e)}"
        )


@router.post("/", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
async def create_grade(
    grade_data: GradeCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new grade
    
    Args:
        grade_data: Grade data
        credentials: JWT token
        
    Returns:
        Created grade
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to create grades")
        
        # Validate grade data
        if grade_data.obtained_marks < 0 or grade_data.obtained_marks > grade_data.total_marks:
            raise ValidationError("Obtained marks must be between 0 and total marks")
        
        # Validate student
        student_exists = await grade_repo.validate_student(grade_data.student_id)
        if not student_exists:
            raise ValidationError("Student not found")
        
        # Validate examiner
        examiner_exists = await grade_repo.validate_teacher(grade_data.examiner_id)
        if not examiner_exists:
            raise ValidationError("Examiner not found")
        
        # Validate assessment
        assessment_exists = await grade_repo.validate_assessment(grade_data.assessment_id)
        if not assessment_exists:
            raise ValidationError("Assessment not found")
        
        # Validate class enrollment
        is_enrolled = await grade_repo.is_student_enrolled(grade_data.student_id, grade_data.class_id)
        if not is_enrolled:
            raise ValidationError("Student is not enrolled in this class")
        
        # Validate assessment submission
        assessment_submitted = await grade_repo.is_assessment_submitted(
            grade_data.student_id, grade_data.assessment_id
        )
        if not assessment_submitted:
            raise ValidationError("Assessment not submitted by student")
        
        # Calculate percentage and grade
        percentage = (grade_data.obtained_marks / grade_data.total_marks) * 100
        grade_mapping = await grade_repo.get_grade_mapping(grade_data.subject_id, grade_data.academic_year, grade_data.semester)
        
        grade_info = grade_repo.calculate_grade(percentage, grade_mapping)
        
        # Create grade
        grade = await grade_repo.create(
            student_id=grade_data.student_id,
            assessment_id=grade_data.assessment_id,
            class_id=grade_data.class_id,
            subject_id=grade_data.subject_id,
            academic_year=grade_data.academic_year,
            semester=grade_data.semester,
            assessment_type=grade_data.assessment_type,
            assessment_name=grade_data.assessment_name,
            total_marks=grade_data.total_marks,
            obtained_marks=grade_data.obtained_marks,
            percentage=percentage,
            grade=grade_info['grade'],
            grade_point=grade_info['grade_point'],
            status=grade_data.status,
            weightage=grade_data.weightage,
            examiner_id=grade_data.examiner_id,
            review_notes=grade_data.review_notes,
            feedback=grade_data.feedback,
            comments=grade_data.comments,
            metadata=grade_data.metadata
        )
        
        return grade
        
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
            detail=f"Failed to create grade: {str(e)}"
        )


@router.put("/{grade_id}", response_model=GradeResponse)
async def update_grade(
    grade_id: str,
    grade_data: GradeUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update a grade
    
    Args:
        grade_id: Grade ID
        grade_data: Updated grade data
        credentials: JWT token
        
    Returns:
        Updated grade
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to update grades")
        
        # Check if grade exists
        existing_grade = await grade_repo.get_by_id(grade_id)
        if not existing_grade:
            raise NotFoundError(f"Grade not found with ID: {grade_id}")
        
        # Validate grade data if updated
        if grade_data.total_marks is not None or grade_data.obtained_marks is not None:
            total_marks = grade_data.total_marks or existing_grade.total_marks
            obtained_marks = grade_data.obtained_marks or existing_grade.obtained_marks
            
            if obtained_marks < 0 or obtained_marks > total_marks:
                raise ValidationError("Obtained marks must be between 0 and total marks")
        
        # Recalculate percentage if marks updated
        if grade_data.total_marks or grade_data.obtained_marks:
            total_marks = grade_data.total_marks or existing_grade.total_marks
            obtained_marks = grade_data.obtained_marks or existing_grade.obtained_marks
            percentage = (obtained_marks / total_marks) * 100
            grade_data.percentage = percentage
        
        # Calculate grade if percentage updated
        if grade_data.percentage:
            grade_mapping = await grade_repo.get_grade_mapping(
                existing_grade.subject_id, existing_grade.academic_year, existing_grade.semester
            )
            grade_info = grade_repo.calculate_grade(grade_data.percentage, grade_mapping)
            grade_data.grade = grade_info['grade']
            grade_data.grade_point = grade_info['grade_point']
        
        # Update grade
        grade = await grade_repo.update(
            grade_id=grade_id,
            **grade_data.dict(exclude_unset=True)
        )
        
        return grade
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grade not found with ID: {grade_id}"
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
            detail=f"Failed to update grade: {str(e)}"
        )


@router.delete("/{grade_id}")
async def delete_grade(
    grade_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a grade
    
    Args:
        grade_id: Grade ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to delete grades")
        
        # Check if grade exists
        existing_grade = await grade_repo.get_by_id(grade_id)
        if not existing_grade:
            raise NotFoundError(f"Grade not found with ID: {grade_id}")
        
        # Check if grade is final
        if existing_grade.status == 'final':
            raise ValidationError("Cannot delete final grades")
        
        # Delete grade
        await grade_repo.delete(grade_id)
        
        return {"message": "Grade deleted successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grade not found with ID: {grade_id}"
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
            detail=f"Failed to delete grade: {str(e)}"
        )


@router.post("/{grade_id}/release")
async def release_grade(
    grade_id: str,
    release_date: Optional[datetime] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Release a grade to students
    
    Args:
        grade_id: Grade ID
        release_date: Release date (optional)
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to release grades")
        
        # Check if grade exists
        existing_grade = await grade_repo.get_by_id(grade_id)
        if not existing_grade:
            raise NotFoundError(f"Grade not found with ID: {grade_id}")
        
        # Release grade
        await grade_repo.release_grade(grade_id, release_date)
        
        return {"message": "Grade released successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grade not found with ID: {grade_id}"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to release grade: {str(e)}"
        )


@router.post("/bulk-upload")
async def bulk_upload_grades(
    upload_data: GradeBulkUpload,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Bulk upload grades
    
    Args:
        upload_data: Grade upload data
        credentials: JWT token
        
    Returns:
        Upload result
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to bulk upload grades")
        
        # Validate assessment
        assessment_exists = await grade_repo.validate_assessment(upload_data.assessment_id)
        if not assessment_exists:
            raise ValidationError("Assessment not found")
        
        # Validate all students
        for grade_data in upload_data.grades:
            student_exists = await grade_repo.validate_student(grade_data['student_id'])
            if not student_exists:
                raise ValidationError(f"Student not found: {grade_data['student_id']}")
            
            # Validate enrollment
            is_enrolled = await grade_repo.is_student_enrolled(
                grade_data['student_id'], upload_data.class_id
            )
            if not is_enrolled:
                raise ValidationError(f"Student {grade_data['student_id']} is not enrolled in this class")
        
        # Validate grade data
        for grade_data in upload_data.grades:
            obtained_marks = grade_data.get('obtained_marks', 0)
            total_marks = grade_data.get('total_marks', 100)
            
            if obtained_marks < 0 or obtained_marks > total_marks:
                raise ValidationError(f"Invalid marks for student {grade_data['student_id']}")
        
        # Bulk upload grades
        result = await grade_repo.bulk_upload_grades(
            class_id=upload_data.class_id,
            assessment_id=upload_data.assessment_id,
            assessment_type=upload_data.assessment_type,
            assessment_name=upload_data.assessment_name,
            weightage=upload_data.weightage,
            grades=upload_data.grades,
            batch_reason=upload_data.batch_reason,
            examiner_id=upload_data.examiner_id
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
            detail=f"Failed to bulk upload grades: {str(e)}"
        )


@router.get("/stats/student/{student_id}")
async def get_student_grade_stats(
    student_id: str,
    class_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get grade statistics for a student
    
    Args:
        student_id: Student ID
        class_id: Filter by class ID
        subject_id: Filter by subject ID
        academic_year: Filter by academic year
        semester: Filter by semester
        credentials: JWT token
        
    Returns:
        Student grade statistics
    """
    try:
        stats = await grade_repo.get_student_grade_stats(
            student_id=student_id,
            class_id=class_id,
            subject_id=subject_id,
            academic_year=academic_year,
            semester=semester
        )
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch student grade stats: {str(e)}"
        )


@router.get("/stats/class/{class_id}")
async def get_class_grade_stats(
    class_id: str,
    subject_id: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get grade statistics for a class
    
    Args:
        class_id: Class ID
        subject_id: Filter by subject ID
        academic_year: Filter by academic year
        semester: Filter by semester
        credentials: JWT token
        
    Returns:
        Class grade statistics
    """
    try:
        stats = await grade_repo.get_class_grade_stats(
            class_id=class_id,
            subject_id=subject_id,
            academic_year=academic_year,
            semester=semester
        )
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch class grade stats: {str(e)}"
        )


@router.get("/stats/subject/{subject_id}")
async def get_subject_grade_stats(
    subject_id: str,
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get grade statistics for a subject
    
    Args:
        subject_id: Subject ID
        academic_year: Filter by academic year
        semester: Filter by semester
        credentials: JWT token
        
    Returns:
        Subject grade statistics
    """
    try:
        stats = await grade_repo.get_subject_grade_stats(
            subject_id=subject_id,
            academic_year=academic_year,
            semester=semester
        )
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subject grade stats: {str(e)}"
        )


@router.get("/policies")
async def get_grade_policies(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get grade policies
    
    Args:
        academic_year: Filter by academic year
        semester: Filter by semester
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of grade policies
    """
    try:
        policies = await grade_repo.get_grade_policies(
            academic_year=academic_year,
            semester=semester,
            skip=skip,
            limit=limit
        )
        return policies
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grade policies: {str(e)}"
        )


@router.post("/policies", response_model=GradePolicy, status_code=status.HTTP_201_CREATED)
async def create_grade_policy(
    policy: GradePolicyCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create grade policy
    
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
            raise AuthorizationError("Insufficient permissions to create grade policies")
        
        # Create policy
        policy_obj = await grade_repo.create_grade_policy(
            policy_name=policy.policy_name,
            description=policy.description,
            academic_year=policy.academic_year,
            semester=policy.semester,
            grading_scale=policy.grading_scale,
            passing_grade=policy.passing_grade,
            minimum_passing_percentage=policy.minimum_passing_percentage,
            late_penalty_policy=policy.late_penalty_policy,
            plagiarism_policy=policy.plagiarism_policy,
            revision_policy=policy.revision_policy,
            is_active=policy.is_active,
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
            detail=f"Failed to create grade policy: {str(e)}"
        )


@router.get("/analytics/trends")
async def get_grade_trends(
    class_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    assessment_type: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get grade trends and analytics
    
    Args:
        class_id: Filter by class ID
        subject_id: Filter by subject ID
        academic_year: Filter by academic year
        semester: Filter by semester
        assessment_type: Filter by assessment type
        credentials: JWT token
        
    Returns:
        Grade trends and analytics
    """
    try:
        trends = await grade_repo.get_grade_trends(
            class_id=class_id,
            subject_id=subject_id,
            academic_year=academic_year,
            semester=semester,
            assessment_type=assessment_type
        )
        return trends
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grade trends: {str(e)}"
        )