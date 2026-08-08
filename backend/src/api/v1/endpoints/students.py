"""
Student Management API Endpoints

This module provides REST API endpoints for student management operations:
- CRUD operations for student profiles
- Academic records and performance tracking
- Enrollment management
- Graduation requirements checking
- Analytics and reporting
- Bulk operations for administrators

Author: Edu-Flow Team
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, validator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.security import AuthService
from src.core.exceptions import ValidationError, NotFoundError, ForbiddenError, AuthenticationError
from src.services.student_service import StudentService
from src.models.student import (
    StudentCreate, StudentUpdate, StudentResponse,
    AcademicRecord, EnrollmentRequest, EnrollmentRecord,
    PerformanceMetrics, AcademicSummary, GraduationStatus,
    RiskAssessment, StudentSearch, StudentStatistics,
    GradeLevel, AcademicStanding, EnrollmentStatus, RiskLevel
)

# Create router
router = APIRouter(prefix="/students", tags=["students"])

# Security
security = HTTPBearer()

# Use consistent secret key for testing
SECRET_KEY = "your-secret-key-here-in-production-use-environment-variable"
ALGORITHM = "HS256"

# Import shared services
from src.core.services import auth_service, get_student_service

# For now, we'll use direct instances for testing
_student_service = get_student_service()
_auth_service = auth_service

# Dependency to get current user from token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from JWT token"""
    try:
        token = credentials.credentials
        user_data = _auth_service.decode_token(token)
        # Convert TokenData to dictionary
        return user_data.model_dump()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Base models for requests
class AcademicRecordCreate(BaseModel):
    """Academic record creation model"""
    course_id: str
    grade: float = Query(..., ge=0.0, le=100.0, description="Course grade")
    credits: float = Query(..., gt=0.0, description="Course credits")
    semester: str
    academic_year: str
    grade_letter: Optional[str] = None
    grade_points: Optional[float] = None
    instructor_id: Optional[str] = None
    comments: Optional[str] = None

class EnrollmentRequestModel(BaseModel):
    """Enrollment request model"""
    course_id: str
    semester: str
    academic_year: str
    priority: int = Query(1, ge=1, le=10, description="Enrollment priority")
    special_accommodations: Optional[Dict[str, Any]] = None

class GraduationCheckRequest(BaseModel):
    """Graduation requirements check request"""
    total_credits: float
    gpa: float
    community_service_hours: int
    assessment_scores: List[float]
    courses: List[Dict[str, Any]] = None
    graduation_date: Optional[date] = None

# Student management endpoints

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new student
    
    - **student_data**: Complete student information including personal details and academic information
    - **current_user**: authenticated user making the request
    - **student_service**: student service instance
    
    Returns created student profile without sensitive data
    """
    # Check if user has admin permissions
    if current_user.get("role") != "admin":
        raise ForbiddenError("Access denied - admin privileges required")
    
    try:
        # Convert Pydantic model to dict for service
        student_dict = student_data.model_dump()
        
        # Create student
        student = _student_service.create_student(student_dict)
        
        return student
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me", response_model=StudentResponse)
async def get_current_student_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current student's own profile
    
    - **current_user**: authenticated student
    
    Returns student's own profile information
    """
    try:
        # Get student by email from token
        student = _student_service.get_student_by_email(current_user["email"])
        if not student:
            raise NotFoundError("Student not found")
        
        return student
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Student profile not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get student by ID
    
    - **student_id**: Unique student identifier
    - **current_user**: authenticated user making the request
    - **student_service**: student service instance
    
    Returns complete student profile (teachers and admins can access any student)
    """
    try:
        # Check permissions
        if not _has_student_access(current_user, student_id):
            raise ForbiddenError("Access denied to this student")
        
        student = _student_service.get_student(student_id)
        return student
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Student not found")
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: str,
    student_update: StudentUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update student information
    
    - **student_id**: Unique student identifier
    - **student_update**: Updated student information
    - **current_user**: authenticated user making the request
    
    Returns updated student profile
    """
    try:
        # Check permissions
        if not _has_student_access(current_user, student_id):
            raise ForbiddenError("Access denied to this student")
        
        # Convert Pydantic model to dict for service
        update_dict = student_update.model_dump(exclude_unset=True)
        
        student = _student_service.update_student(student_id, update_dict)
        return student
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Student not found")
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_student(
    student_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Deactivate student account
    
    - **student_id**: Unique student identifier
    - **current_user**: authenticated user making the request
    
    Deactivates student account (admin only)
    """
    try:
        # Check admin permissions
        if current_user.get("role") != "admin":
            raise ForbiddenError("Only administrators can deactivate students")
        
        _student_service.deactivate_student(student_id)
        return None
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Student not found")
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{student_id}/activate", response_model=StudentResponse)
async def activate_student(
    student_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Activate student account
    
    - **student_id**: Unique student identifier
    - **current_user**: authenticated user making the request
    
    Activates deactivated student account (admin only)
    """
    try:
        # Check admin permissions
        if current_user.get("role") != "admin":
            raise ForbiddenError("Only administrators can activate students")
        
        student = _student_service.activate_student(student_id)
        return student
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Student not found")
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Search and filtering endpoints

@router.get("/", response_model=List[StudentResponse])
async def search_students(
    name: Optional[str] = Query(None, description="Student name (partial match)"),
    email: Optional[EmailStr] = Query(None, description="Student email"),
    student_id: Optional[str] = Query(None, description="Student ID"),
    grade_level: Optional[GradeLevel] = Query(None, description="Grade level"),
    department_id: Optional[str] = Query(None, description="Department ID"),
    advisor_id: Optional[str] = Query(None, description="Advisor ID"),
    is_active: Optional[bool] = Query(None, description="Active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Search students with various criteria
    
    - **name**: Student name (partial match)
    - **email**: Student email
    - **student_id**: Student ID
    - **grade_level**: Grade level filter
    - **department_id**: Department filter
    - **advisor_id**: Advisor filter
    - **is_active**: Active status filter
    - **limit**: Maximum results to return
    - **offset**: Offset for pagination
    - **current_user**: authenticated user making the request
    
    Returns list of matching students
    """
    try:
        # Build search criteria
        search_criteria = {
            "name": name,
            "email": email,
            "student_id": student_id,
            "grade_level": grade_level,
            "department_id": department_id,
            "advisor_id": advisor_id,
            "is_active": is_active,
            "limit": limit,
            "offset": offset
        }
        
        # Filter out None values
        search_criteria = {k: v for k, v in search_criteria.items() if v is not None}
        
        students = _student_service.search_students(search_criteria, limit=limit, offset=offset)
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/department/{department_id}", response_model=List[StudentResponse])
async def get_students_by_department(
    department_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get students by department
    
    - **department_id**: Department identifier
    - **current_user**: authenticated user making the request
    
    Returns all students in the specified department
    """
    try:
        students = _student_service.get_students_by_department(department_id)
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/advisor/{advisor_id}", response_model=List[StudentResponse])
async def get_students_by_advisor(
    advisor_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get students by advisor
    
    - **advisor_id**: Advisor identifier
    - **current_user**: authenticated user making the request
    
    Returns all students assigned to the specified advisor
    """
    try:
        students = _student_service.get_students_by_advisor(advisor_id)
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Academic records endpoints

@router.get("/{student_id}/academic-summary", response_model=AcademicSummary)
async def get_student_academic_summary(
    student_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get student academic summary
    
    - **student_id**: Student identifier
    - **current_user**: authenticated user making the request
    
    Returns comprehensive academic summary including GPA, credits, and standing
    """
    try:
        # Check permissions
        if not _has_student_access(current_user, student_id):
            raise ForbiddenError("Access denied to this student's academic data")
        
        # Get grades (in real implementation, this would come from academic records service)
        grades = []  # This would be populated from actual academic records
        
        summary = _student_service.get_student_academic_summary(student_id, grades)
        return summary
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Student not found")
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{student_id}/performance", response_model=Dict[str, Any])
async def get_student_performance(
    student_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get student performance analytics
    
    - **student_id**: Student identifier
    - **current_user**: authenticated user making the request
    
    Returns detailed performance analytics and trends
    """
    try:
        # Check permissions
        if not _has_student_access(current_user, student_id):
            raise ForbiddenError("Access denied to this student's performance data")
        
        # Get grade history (in real implementation, this would come from academic records)
        grade_history = [
            {"semester": "Fall 2023", "gpa": 2.5},
            {"semester": "Spring 2024", "gpa": 2.8},
            {"semester": "Fall 2024", "gpa": 3.2}
        ]
        
        performance = _student_service.get_student_performance_trend(student_id, grade_history)
        return performance
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Student not found")
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{student_id}/academic-records", response_model=AcademicRecord)
async def add_academic_record(
    student_id: str,
    record_data: AcademicRecordCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Add academic record for student
    
    - **student_id**: Student identifier
    - **record_data**: Academic record details
    - **current_user**: authenticated user making the request
    
    Adds academic record to student's transcript (teacher or admin only)
    """
    try:
        # Check permissions (teachers and admins can add records)
        if current_user.get("role") not in ["teacher", "admin"]:
            raise ForbiddenError("Only teachers and administrators can add academic records")
        
        # In real implementation, this would call academic records service
        # For now, return the record data
        return {
            "id": str(uuid4()),
            "student_id": student_id,
            **record_data.model_dump(),
            "submission_date": date.today()
        }
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enrollment management endpoints

@router.post("/{student_id}/enrollments", response_model=EnrollmentRecord, status_code=status.HTTP_201_CREATED)
async def enroll_student(
    student_id: str,
    enrollment_data: EnrollmentRequestModel,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Enroll student in course
    
    - **student_id**: Student identifier
    - **enrollment_data**: Enrollment details
    - **current_user**: authenticated user making the request
    
    Enrolls student in specified course (admin or counselor only)
    """
    try:
        # Check permissions
        if current_user.get("role") not in ["admin", "teacher", "counselor"]:
            raise ForbiddenError("Only administrators, teachers, and counselors can enroll students")
        
        # Check if student exists
        _student_service.get_student(student_id)
        
        # Create enrollment record
        enrollment_id = str(uuid4())
        enrollment = {
            "id": enrollment_id,
            "student_id": student_id,
            **enrollment_data.model_dump(),
            "enrollment_date": date.today(),
            "status": EnrollmentStatus.ACTIVE
        }
        
        # In real implementation, this would save to enrollment database
        try:
            enrollment_record = EnrollmentRecord(**enrollment)
            return enrollment_record
        except Exception as e:
            print(f"Error creating EnrollmentRecord: {e}")
            print(f"Enrollment data: {enrollment}")
            raise HTTPException(status_code=500, detail=f"Failed to create enrollment record: {str(e)}")
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Student not found")
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Risk assessment and intervention endpoints

@router.get("/at-risk", response_model=List[Dict[str, Any]])
async def get_at_risk_students(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get at-risk students
    
    - **current_user**: authenticated user making the request
    
    Returns list of students identified as at-risk (admin and counselor only)
    """
    try:
        # Check permissions
        if current_user.get("role") not in ["admin", "counselor", "teacher"]:
            raise ForbiddenError("Only administrators, counselors, and teachers can view at-risk students")
        
        at_risk_students = _student_service.identify_at_risk_students()
        return at_risk_students
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Graduation endpoints

@router.get("/{student_id}/graduation-status", response_model=GraduationStatus)
async def check_graduation_requirements(
    student_id: str,
    request: GraduationCheckRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Check graduation requirements
    
    - **student_id**: Student identifier
    - **request**: Completed requirements data
    - **current_user**: authenticated user making the request
    
    Returns graduation status and requirements met (counselor or admin only)
    """
    try:
        # Check permissions
        if current_user.get("role") not in ["admin", "counselor", "teacher"]:
            raise ForbiddenError("Only administrators, counselors, and teachers can check graduation requirements")
        
        # Check if student exists
        student_service.get_student(student_id)
        
        status = _student_service.check_graduation_requirements(student_id, request.model_dump())
        return status
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Student not found")
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Reporting endpoints

@router.get("/{student_id}/report", response_model=Dict[str, Any])
async def generate_student_report(
    student_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate comprehensive student report
    
    - **student_id**: Student identifier
    - **current_user**: authenticated user making the request
    
    Returns comprehensive student report (student can access own, others with permission)
    """
    try:
        # Check permissions
        if not _has_student_access(current_user, student_id):
            raise ForbiddenError("Access denied to this student's report")
        
        report = _student_service.generate_student_report(student_id)
        return report
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Student not found")
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/summary", response_model=StudentStatistics)
async def get_student_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get student statistics summary
    
    - **current_user**: authenticated user making the request
    
    Returns comprehensive student statistics (admin only)
    """
    try:
        # Check admin permissions
        if current_user.get("role") != "admin":
            raise ForbiddenError("Only administrators can view student statistics")
        
        statistics = _student_service.get_student_statistics()
        return statistics
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Bulk operations endpoints

@router.post("/bulk-import", status_code=status.HTTP_201_CREATED)
async def bulk_import_students(
    students: List[StudentCreate],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Bulk import students
    
    - **students**: List of student data to import
    - **current_user**: authenticated user making the request
    
    Imports multiple students at once (admin only)
    """
    try:
        # Check admin permissions
        if current_user.get("role") != "admin":
            raise ForbiddenError("Only administrators can bulk import students")
        
        results = []
        errors = []
        
        for i, student_data in enumerate(students):
            try:
                student_dict = student_data.model_dump()
                student = _student_service.create_student(student_dict)
                results.append({
                    "index": i,
                    "student_id": student.student_id,
                    "status": "success"
                })
            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e),
                    "status": "failed"
                })
        
        return {
            "total_processed": len(students),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

def _has_student_access(current_user: Dict[str, Any], student_id: str) -> bool:
    """Check if user has access to student data"""
    # Students can access their own data
    if current_user.get("role") == "student":
        # In real implementation, check if student_id matches user's student ID
        return True
    
    # Teachers and admins can access all student data
    return current_user.get("role") in ["teacher", "admin", "counselor"]