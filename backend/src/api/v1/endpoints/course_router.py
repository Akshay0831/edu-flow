"""Course management API endpoints."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query

from models.course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseCreateResponse,
    CourseOffering, OfferingCreate, OfferingUpdate, OfferingResponse,
    Enrollment, EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse,
    Department, Prerequisite, CourseStatistics, EnrollmentSummary,
    CourseStatus, CourseLevel, CreditType, Semester, Grade
)
from src.services.course_service import CourseService
from core.exceptions import ValidationError, NotFoundError, UnauthorizedError
from core.security import AuthService

router = APIRouter(prefix="/courses", tags=["courses"])

# Initialize services
from auth.service import AuthService
auth_service = AuthService()
course_service = CourseService(auth_service)

@router.post("/", response_model=CourseCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_course(course: CourseCreate):
    """Create a new course."""
    try:
        result = course_service.create_course(course, current_user)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/", response_model=List[CourseResponse])
async def get_all_courses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Get all courses with pagination."""
    try:
        courses = course_service.get_all_courses()
        # Simple pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_courses = courses[start_idx:end_idx]
        
        return paginated_courses
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Get a specific course by ID."""
    try:
        course = course_service.get_course(course_id)
        return course
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    course_update: CourseUpdate,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Update a course."""
    try:
        updated_course = course_service.update_course(course_id, course_update, current_user)
        return updated_course
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/{course_id}")
async def delete_course(
    course_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Delete a course."""
    try:
        success = course_service.delete_course(course_id, current_user)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Course deleted successfully", "success": success}
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/search", response_model=List[CourseResponse])
async def search_courses(
    title: Optional[str] = Query(None, description="Search by title"),
    code: Optional[str] = Query(None, description="Search by course code"),
    department_id: Optional[str] = Query(None, description="Filter by department"),
    level: Optional[CourseLevel] = Query(None, description="Filter by course level"),
    min_credits: Optional[float] = Query(None, ge=0, description="Minimum credits required"),
    max_credits: Optional[float] = Query(None, ge=0, description="Maximum credits allowed"),
    semester: Optional[Semester] = Query(None, description="Filter by semester"),
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Search courses with filters."""
    try:
        filters = {}
        if title is not None:
            filters["title"] = title
        if code is not None:
            filters["code"] = code
        if department_id is not None:
            filters["department_id"] = department_id
        if level is not None:
            filters["level"] = level
        if min_credits is not None:
            filters["min_credits"] = min_credits
        if max_credits is not None:
            filters["max_credits"] = max_credits
        if semester is not None:
            filters["semester"] = semester
            
        results = course_service.search_courses(filters)
        return results
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/{course_id}/offerings", response_model=OfferingResponse, status_code=status.HTTP_201_CREATED)
async def create_offering(
    course_id: str,
    offering: OfferingCreate,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Create a course offering."""
    try:
        result = course_service.create_offering(offering, current_user)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{course_id}/offerings/{offering_id}", response_model=OfferingResponse)
async def get_offering(
    course_id: str,
    offering_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Get a specific course offering."""
    try:
        offering = course_service.get_offering(offering_id)
        return offering
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/{course_id}/offerings/{offering_id}", response_model=OfferingResponse)
async def update_offering(
    course_id: str,
    offering_id: str,
    offering_update: OfferingUpdate,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Update a course offering."""
    try:
        updated_offering = course_service.update_offering(offering_id, offering_update, current_user)
        return updated_offering
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/{course_id}/offerings/{offering_id}")
async def delete_offering(
    course_id: str,
    offering_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Delete a course offering."""
    try:
        success = course_service.delete_offering(offering_id, current_user)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Offering deleted successfully", "success": success}
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{course_id}/offerings", response_model=List[OfferingResponse])
async def get_course_offerings(
    course_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Get all offerings for a course."""
    try:
        offerings = course_service.get_course_offerings(course_id)
        return offerings
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/{course_id}/prerequisites", response_model=Dict[str, str])
async def add_prerequisite(
    course_id: str,
    prerequisite_data: Dict[str, str],
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Add prerequisite to a course."""
    try:
        result = course_service.add_prerequisite(course_id, prerequisite_data, current_user)
        return {"message": result}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/{course_id}/prerequisites/{prerequisite_course_id}")
async def remove_prerequisite(
    course_id: str,
    prerequisite_course_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Remove prerequisite from a course."""
    try:
        result = course_service.remove_prerequisite(course_id, prerequisite_course_id, current_user)
        return {"message": result}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{course_id}/statistics", response_model=CourseStatistics)
async def get_course_statistics(
    course_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Get course statistics and analytics."""
    try:
        statistics = course_service.get_course_statistics(course_id)
        return statistics
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/departments", response_model=List[Department])
async def get_departments(
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Get all departments."""
    try:
        departments = course_service.get_all_departments()
        return departments
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Enrollment endpoints
@router.post("/students/{student_id}/enroll", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_student(
    student_id: str,
    enrollment_data: Dict[str, str],
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Enroll a student in a course offering."""
    try:
        offering_id = enrollment_data.get("offering_id")
        if not offering_id:
            raise HTTPException(status_code=422, detail="offering_id is required")
        
        result = course_service.enroll_student(student_id, offering_id, current_user)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/students/{student_id}/enrollments", response_model=List[EnrollmentResponse])
async def get_student_enrollments(
    student_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Get all enrollments for a student."""
    try:
        enrollments = course_service.get_student_enrollments(student_id)
        return enrollments
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/students/{student_id}/summary", response_model=EnrollmentSummary)
async def get_student_summary(
    student_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Get student enrollment summary."""
    try:
        summary = course_service.get_student_enrollment_summary(student_id)
        return summary
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/students/{student_id}/enrollments/{enrollment_id}", response_model=EnrollmentResponse)
async def update_enrollment(
    student_id: str,
    enrollment_id: str,
    enrollment_update: EnrollmentUpdate,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Update student enrollment."""
    try:
        result = course_service.update_enrollment(enrollment_id, enrollment_update, current_user)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/students/{student_id}/enrollments/{enrollment_id}")
async def cancel_enrollment(
    student_id: str,
    enrollment_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Cancel a student enrollment."""
    try:
        success = course_service.cancel_enrollment(enrollment_id, current_user)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Enrollment cancelled successfully", "success": success}
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/students/{student_id}/enrollments/{enrollment_id}", response_model=EnrollmentResponse)
async def get_enrollment(
    student_id: str,
    enrollment_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Get a specific student enrollment."""
    try:
        enrollment = course_service.get_enrollment(enrollment_id)
        return enrollment
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Batch operations
@router.post("/batch-create", response_model=List[CourseCreateResponse], status_code=status.HTTP_201_CREATED)
async def batch_create_courses(
    courses: List[CourseCreate],
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Create multiple courses in a batch operation."""
    try:
        results = []
        for course in courses:
            result = course_service.create_course(course, current_user)
            results.append(result)
        return results
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/export/{format}")
async def export_courses(
    format: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db_connection)
):
    """Export course data in various formats."""
    try:
        # Validate format
        if format not in ["json", "csv", "pdf"]:
            raise HTTPException(status_code=400, detail="Invalid export format. Must be json, csv, or pdf")
        
        # This would implement actual export functionality
        if format == "json":
            courses = course_service.get_all_courses()
            return {"format": "json", "data": jsonable_encoder(courses), "count": len(courses)}
        elif format == "csv":
            # Would return CSV data
            return {"format": "csv", "message": "CSV export not implemented yet"}
        elif format == "pdf":
            # Would return PDF data
            return {"format": "pdf", "message": "PDF export not implemented yet"}
        else:
            raise HTTPException(status_code=400, detail="Invalid export format")
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")