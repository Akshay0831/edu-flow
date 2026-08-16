"""
Course management API endpoints

This module provides course management endpoints:
- Create courses
- List courses
- Get course details
- Update courses
- Delete courses
- Manage course enrollments

Author: Edu-Flow Team
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from src.core.security import auth_service
from src.core.dependencies import get_current_user
from src.core.exceptions import ValidationError, NotFoundError
from src.services.database_service_dev import database_service

router = APIRouter(prefix="/courses", tags=["courses"])

class CourseCreate(BaseModel):
    """Course creation model"""
    name: str = Field(..., description="Course name")
    code: str = Field(..., description="Course code")
    description: Optional[str] = Field(None, description="Course description")
    credits: int = Field(..., ge=1, le=10, description="Course credits")
    department_id: str = Field(..., description="Department ID")

class CourseUpdate(BaseModel):
    """Course update model"""
    name: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[int] = Field(None, ge=1, le=10)

class CourseResponse(BaseModel):
    """Course response model"""
    id: str
    name: str
    code: str
    description: Optional[str]
    credits: int
    department_id: str
    created_at: str
    updated_at: str



@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    current_user: str = Depends(get_current_user)
):
    """Create a new course"""
    try:
        # Only teachers and admins can create courses
        if current_user != "mock_user_id":  # Mock user validation - replace with real user lookup
            # In real implementation, get user from database and check role
            user_role = "admin"  # Mock role
            if user_role not in ["teacher", "admin"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only teachers and admins can create courses"
                )
            # For demo purposes, allow if it's the mock user
            if current_user != "mock_user_id":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only teachers and admins can create courses"
                )
        
        # Check if course code already exists
        existing_course = await database_service.get_sqlite("Course", course_data.code)
        if existing_course:
            raise ValidationError("Course code already exists")
        
        # Create course
        course_payload = {
            "name": course_data.name,
            "code": course_data.code,
            "description": course_data.description,
            "credits": course_data.credits,
            "department_id": course_data.department_id
        }
        
        course_id = await database_service.create_sqlite("Course", course_payload)
        
        return {
            "id": course_id,
            "name": course_data.name,
            "code": course_data.code,
            "description": course_data.description,
            "credits": course_data.credits,
            "department_id": course_data.department_id,
            "created_at": course_id,  # Using ID as placeholder for timestamp
            "message": "Course created successfully"
        }
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create course"
        )

@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_courses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: str = Depends(get_current_user)
):
    """Get all courses with pagination"""
    try:
        # Get all courses from database
        courses_data = await database_service.get_all_sqlite("Course")
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_courses = courses_data[start_idx:end_idx]
        
        # Format courses using list comprehension for better performance
        courses = [
            {
                "id": course.get("id"),
                "name": course.get("name"),
                "code": course.get("code"),
                "description": course.get("description"),
                "credits": course.get("credits"),
                "department_id": course.get("department_id"),
                "created_at": course.get("created_at"),
                "updated_at": course.get("updated_at")
            }
            for course in paginated_courses
        ]
        
        return {
            "courses": courses,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": len(courses_data),
                "total_pages": (len(courses_data) + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get courses"
        )

@router.get("/{course_id}", response_model=Dict[str, Any])
async def get_course(course_id: str, current_user: str = Depends(get_current_user)):
    """Get specific course by ID"""
    try:
        course = await database_service.get_sqlite("Course", course_id)
        if not course:
            raise NotFoundError("Course not found")
        
        return {
            "id": course.get("id"),
            "name": course.get("name"),
            "code": course.get("code"),
            "description": course.get("description"),
            "credits": course.get("credits"),
            "department_id": course.get("department_id"),
            "created_at": course.get("created_at"),
            "updated_at": course.get("updated_at")
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get course"
        )

@router.put("/{course_id}", response_model=Dict[str, Any])
async def update_course(
    course_id: str,
    course_data: CourseUpdate,
    current_user: str = Depends(get_current_user)
):
    """Update course details"""
    try:
        # Only teachers and admins can update courses
        if current_user != "mock_user_id":  # Mock user validation
            # In real implementation, get user from database and check role
            user_role = "admin"  # Mock role
            if user_role not in ["teacher", "admin"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only teachers and admins can update courses"
                )
            # For demo purposes, allow if it's the mock user
            if current_user != "mock_user_id":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only teachers and admins can update courses"
                )
        
        # Check if course exists
        existing_course = await database_service.get_sqlite("Course", course_id)
        if not existing_course:
            raise NotFoundError("Course not found")
        
        # Prepare update data
        update_data = {}
        if course_data.name is not None:
            update_data["name"] = course_data.name
        if course_data.description is not None:
            update_data["description"] = course_data.description
        if course_data.credits is not None:
            update_data["credits"] = course_data.credits
        
        # Update course
        await database_service.update_sqlite("Course", course_id, update_data)
        
        # Get updated course
        updated_course = await database_service.get_sqlite("Course", course_id)
        
        return {
            "id": updated_course.get("id"),
            "name": updated_course.get("name"),
            "code": updated_course.get("code"),
            "description": updated_course.get("description"),
            "credits": updated_course.get("credits"),
            "department_id": updated_course.get("department_id"),
            "updated_at": updated_course.get("updated_at"),
            "message": "Course updated successfully"
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update course"
        )

@router.delete("/{course_id}", response_model=Dict[str, Any])
async def delete_course(
    course_id: str,
    current_user: str = Depends(get_current_user)
):
    """Delete a course"""
    try:
        # Only admins can delete courses
        if current_user != "mock_user_id":  # Mock user validation
            # In real implementation, get user from database and check role
            user_role = "admin"  # Mock role
            if user_role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can delete courses"
                )
            # For demo purposes, allow if it's the mock user
            if current_user != "mock_user_id":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can delete courses"
                )
        
        # Check if course exists
        existing_course = await database_service.get_sqlite("Course", course_id)
        if not existing_course:
            raise NotFoundError("Course not found")
        
        # Delete course
        await database_service.delete_sqlite("Course", course_id)
        
        return {
            "message": "Course deleted successfully",
            "course_id": course_id
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete course"
        )