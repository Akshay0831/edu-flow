"""
Course Routes - REST API Endpoints

This module provides comprehensive REST API endpoints for course management,
including CRUD operations, scheduling, enrollment management, and analytics.

Author: Edu-Flow Team
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta
import json
from logging import getLogger

from models.course import Course
from src.services.course_service import CourseService
from core.dependencies import get_db, get_current_user, get_current_active_admin, get_current_active_teacher
from core.exceptions import CourseNotFoundError, DepartmentNotFoundError, EnrollmentError
from models.user import User, UserRole

logger = getLogger(__name__)

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/", response_model=List[Dict[str, Any]])
async def get_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    department_id: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    teacher_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of courses with filtering options
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        department_id: Filter by department
        semester: Filter by semester
        teacher_id: Filter by teacher
        search: Search term for course name or code
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of course dictionaries
    """
    course_service = CourseService(db)
    courses = await course_service.get_courses(
        skip=skip,
        limit=limit,
        department_id=department_id,
        semester=semester,
        teacher_id=teacher_id,
        search=search
    )
    return courses


@router.get("/{course_id}", response_model=Dict[str, Any])
async def get_course_by_id(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get course by ID
    
    Args:
        course_id: Course ID to retrieve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Course information
        
    Raises:
        HTTPException: If course not found
    """
    try:
        course_service = CourseService(db)
        course = await course_service.get_course_by_id(course_id)
        return course
        
    except CourseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )


@router.post("/", response_model=Dict[str, str], status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new course (admin only)
    
    Args:
        course_data: Course data to create
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        Success message with course ID
        
    Raises:
        HTTPException: If course already exists or validation fails
    """
    try:
        course_service = CourseService(db)
        
        # Validate required fields
        required_fields = ["name", "code", "department_id", "credits"]
        for field in required_fields:
            if field not in course_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Validate department exists
        try:
            await course_service.get_department_by_id(course_data["department_id"])
        except DepartmentNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found"
            )
        
        # Create course
        course = await course_service.create_course(course_data)
        
        logger.info(f"New course created: {course.name} ({course.code})")
        return {"message": "Course created successfully", "course_id": str(course.id)}
        
    except Exception as e:
        logger.error(f"Course creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Course creation failed"
        )


@router.put("/{course_id}", response_model=Dict[str, Any])
async def update_course(
    course_id: str,
    course_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Update course information (admin only)
    
    Args:
        course_id: Course ID to update
        course_data: Course data to update
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        Updated course information
        
    Raises:
        HTTPException: If course not found
    """
    try:
        course_service = CourseService(db)
        updated_course = await course_service.update_course(course_id, course_data)
        return updated_course
    except CourseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: str,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Delete course (admin only)
    
    Args:
        course_id: Course ID to delete
        current_user: Current authenticated user (admin)
        db: Database session
        background_tasks: Background tasks for cleanup
        
    Raises:
        HTTPException: If course not found
    """
    try:
        course_service = CourseService(db)
        await course_service.delete_course(course_id, background_tasks)
        
        logger.info(f"Course deleted: {course_id}")
        return None
        
    except CourseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )


@router.get("/{course_id}/students", response_model=List[Dict[str, Any]])
async def get_course_students(
    course_id: str,
    current_user: User = Depends(get_current_active_teacher),
    db: Session = Depends(get_db)
):
    """
    Get students enrolled in a course
    
    Args:
        course_id: Course ID to get students for
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of students enrolled in the course
    """
    try:
        course_service = CourseService(db)
        students = await course_service.get_course_students(course_id)
        return students
        
    except CourseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )


@router.post("/{course_id}/students/{student_id}/enroll", response_model=Dict[str, str])
async def enroll_student_in_course(
    course_id: str,
    student_id: str,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Enroll a student in a course (admin only)
    
    Args:
        course_id: Course ID to enroll student in
        student_id: Student ID to enroll
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If course or student not found
    """
    try:
        course_service = CourseService(db)
        await course_service.enroll_student(course_id, student_id)
        
        logger.info(f"Student {student_id} enrolled in course {course_id}")
        return {"message": "Student enrolled successfully"}
        
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


@router.delete("/{course_id}/students/{student_id}/unenroll", response_model=Dict[str, str])
async def unenroll_student_from_course(
    course_id: str,
    student_id: str,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Unenroll a student from a course (admin only)
    
    Args:
        course_id: Course ID to unenroll student from
        student_id: Student ID to unenroll
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If course or student not found
    """
    try:
        course_service = CourseService(db)
        await course_service.unenroll_student(course_id, student_id)
        
        logger.info(f"Student {student_id} unenrolled from course {course_id}")
        return {"message": "Student unenrolled successfully"}
        
    except CourseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )


@router.get("/{course_id}/schedule", response_model=List[Dict[str, Any]])
async def get_course_schedule(
    course_id: str,
    semester: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get course schedule information
    
    Args:
        course_id: Course ID to get schedule for
        semester: Filter by semester
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of schedule entries for the course
    """
    try:
        course_service = CourseService(db)
        schedule = await course_service.get_course_schedule(course_id, semester)
        return schedule
        
    except CourseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )


@router.get("/{course_id}/performance", response_model=Dict[str, Any])
async def get_course_performance(
    course_id: str,
    semester: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_teacher),
    db: Session = Depends(get_db)
):
    """
    Get course performance analytics
    
    Args:
        course_id: Course ID to get performance for
        semester: Filter by semester
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Course performance analytics
    """
    try:
        course_service = CourseService(db)
        performance = await course_service.get_course_performance(course_id, semester)
        return performance
        
    except CourseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )


@router.get("/{course_id}/assignments", response_model=List[Dict[str, Any]])
async def get_course_assignments(
    course_id: str,
    current_user: User = Depends(get_current_active_teacher),
    db: Session = Depends(get_db)
):
    """
    Get assignments for a course
    
    Args:
        course_id: Course ID to get assignments for
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of assignments for the course
    """
    try:
        course_service = CourseService(db)
        assignments = await course_service.get_course_assignments(course_id)
        return assignments
        
    except CourseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )


@router.get("/{course_id}/attendance", response_model=List[Dict[str, Any]])
async def get_course_attendance(
    course_id: str,
    semester: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_teacher),
    db: Session = Depends(get_db)
):
    """
    Get attendance records for a course
    
    Args:
        course_id: Course ID to get attendance for
        semester: Filter by semester
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of attendance records for the course
    """
    try:
        course_service = CourseService(db)
        attendance = await course_service.get_course_attendance(course_id, semester)
        return attendance
        
    except CourseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )


@router.get("/stats/enrollment", response_model=Dict[str, Any])
async def get_course_enrollment_statistics(
    department_id: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Get course enrollment statistics
    
    Args:
        department_id: Filter by department
        semester: Filter by semester
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        Course enrollment statistics
    """
    course_service = CourseService(db)
    stats = await course_service.get_course_enrollment_statistics(
        department_id=department_id,
        semester=semester
    )
    return stats