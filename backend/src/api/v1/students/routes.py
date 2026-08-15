"""
Student Routes - REST API Endpoints

This module provides comprehensive REST API endpoints for student management,
including academic operations, enrollment management, and performance tracking.

Author: Edu-Flow Team
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
import asyncio
from datetime import datetime, timedelta
import json
from logging import getLogger

from src.models.student import StudentBase as Student
from src.services.student_service import StudentService
from src.core.dependencies import get_db, get_current_user, get_current_active_admin, get_current_active_teacher
from src.core.exceptions import StudentNotFoundError, CourseNotFoundError, EnrollmentError
from src.models.user import User, UserRole

logger = getLogger(__name__)

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/", response_model=List[Dict[str, Any]])
async def get_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    department_id: Optional[str] = Query(None),
    course_id: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of students with filtering options
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        department_id: Filter by department
        course_id: Filter by course
        semester: Filter by semester
        search: Search term for student name or ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of student dictionaries
    """
    student_service = StudentService(db)
    users = await student_service.get_students(
        skip=skip,
        limit=limit,
        department_id=department_id,
        course_id=course_id,
        semester=semester,
        search=search
    )
    return users


@router.get("/me", response_model=Dict[str, Any])
async def get_current_student_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current student's profile information
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Student profile information
    """
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    student_service = StudentService(db)
    student_info = await student_service.get_student_by_user_id(current_user.id)
    return student_info


@router.get("/{student_id}", response_model=Dict[str, Any])
async def get_student_by_id(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get student by ID
    
    Args:
        student_id: Student ID to retrieve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Student information
        
    Raises:
        HTTPException: If student not found
    """
    try:
        student_service = StudentService(db)
        student = await student_service.get_student_by_id(student_id)
        
        # Check permissions - students can only see their own info, teachers can see all
        if current_user.role == UserRole.STUDENT and current_user.id != student.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this student"
            )
        
        return student
        
    except StudentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )


@router.put("/me", response_model=Dict[str, Any])
async def update_current_student(
    student_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current student's profile information
    
    Args:
        student_data: Student data to update
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated student information
    """
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    student_service = StudentService(db)
    updated_student = await student_service.update_student(current_user.id, student_data)
    return updated_student


@router.put("/{student_id}", response_model=Dict[str, Any])
async def update_student(
    student_id: str,
    student_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Update student information (admin/teacher only)
    
    Args:
        student_id: Student ID to update
        student_data: Student data to update
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated student information
        
    Raises:
        HTTPException: If student not found
    """
    try:
        student_service = StudentService(db)
        updated_student = await student_service.update_student(student_id, student_data)
        return updated_student
    except StudentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )


@router.post("/{student_id}/courses/{course_id}/enroll", response_model=Dict[str, str])
async def enroll_student_in_course(
    student_id: str,
    course_id: str,
    current_user: User = Depends(get_current_active_teacher),
    db: Session = Depends(get_db)
):
    """
    Enroll a student in a course (teacher/admin only)
    
    Args:
        student_id: Student ID to enroll
        course_id: Course ID to enroll in
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If student or course not found
    """
    try:
        student_service = StudentService(db)
        await student_service.enroll_student(student_id, course_id)
        
        logger.info(f"Student {student_id} enrolled in course {course_id}")
        return {"message": "Student enrolled successfully"}
        
    except StudentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    except CourseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    except EnrollmentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{student_id}/courses/{course_id}/unenroll", response_model=Dict[str, str])
async def unenroll_student_from_course(
    student_id: str,
    course_id: str,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Unenroll a student from a course (admin only)
    
    Args:
        student_id: Student ID to unenroll
        course_id: Course ID to unenroll from
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If student or course not found
    """
    try:
        student_service = StudentService(db)
        await student_service.unenroll_student(student_id, course_id)
        
        logger.info(f"Student {student_id} unenrolled from course {course_id}")
        return {"message": "Student unenrolled successfully"}
        
    except StudentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    except CourseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )


@router.get("/{student_id}/courses", response_model=List[Dict[str, Any]])
async def get_student_courses(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get courses for a specific student
    
    Args:
        student_id: Student ID to get courses for
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of courses the student is enrolled in
    """
    try:
        student_service = StudentService(db)
        courses = await student_service.get_student_courses(student_id)
        
        # Check permissions
        if current_user.role == UserRole.STUDENT and current_user.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this student's courses"
            )
        
        return courses
        
    except StudentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )


@router.get("/{student_id}/marks", response_model=List[Dict[str, Any]])
async def get_student_marks(
    student_id: str,
    course_id: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get marks/grades for a specific student
    
    Args:
        student_id: Student ID to get marks for
        course_id: Filter by course
        semester: Filter by semester
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of marks/grades for the student
    """
    try:
        student_service = StudentService(db)
        marks = await student_service.get_student_marks(
            student_id,
            course_id=course_id,
            semester=semester
        )
        
        # Check permissions
        if current_user.role == UserRole.STUDENT and current_user.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this student's marks"
            )
        
        return marks
        
    except StudentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )


@router.get("/{student_id}/performance", response_model=Dict[str, Any])
async def get_student_performance(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get student performance analysis
    
    Args:
        student_id: Student ID to get performance for
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Student performance analysis data
    """
    try:
        student_service = StudentService(db)
        performance = await student_service.get_student_performance(student_id)
        
        # Check permissions
        if current_user.role == UserRole.STUDENT and current_user.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this student's performance"
            )
        
        return performance
        
    except StudentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )


@router.get("/{student_id}/attendance", response_model=List[Dict[str, Any]])
async def get_student_attendance(
    student_id: str,
    course_id: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get attendance records for a specific student
    
    Args:
        student_id: Student ID to get attendance for
        course_id: Filter by course
        semester: Filter by semester
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of attendance records for the student
    """
    try:
        student_service = StudentService(db)
        attendance = await student_service.get_student_attendance(
            student_id,
            course_id=course_id,
            semester=semester
        )
        
        # Check permissions
        if current_user.role == UserRole.STUDENT and current_user.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this student's attendance"
            )
        
        return attendance
        
    except StudentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )


@router.get("/{student_id}/activity", response_model=List[Dict[str, Any]])
async def get_student_activity(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get student activity logs
    
    Args:
        student_id: Student ID to get activity for
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of student activity logs
    """
    # Admin users can see any student's activity, regular users can only see their own
    if current_user.role != UserRole.ADMIN and current_user.role != UserRole.TEACHER and current_user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this student's activity"
        )
    
    student_service = StudentService(db)
    activity_logs = await student_service.get_student_activity(student_id)
    return activity_logs


@router.get("/stats/enrollment", response_model=Dict[str, Any])
async def get_enrollment_statistics(
    department_id: Optional[str] = Query(None),
    course_id: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Get enrollment statistics
    
    Args:
        department_id: Filter by department
        course_id: Filter by course
        semester: Filter by semester
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        Enrollment statistics
    """
    student_service = StudentService(db)
    stats = await student_service.get_enrollment_statistics(
        department_id=department_id,
        course_id=course_id,
        semester=semester
    )
    return stats