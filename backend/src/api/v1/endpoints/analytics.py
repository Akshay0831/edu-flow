"""
Analytics API endpoints for system analytics and reporting.

This module provides:
- Performance metrics
- User analytics
- Course analytics
- Student performance analytics
- System health metrics
- Custom reports
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import logging
import asyncio

from core.exceptions import ValidationError, NotFoundError, AuthenticationError
from core.security import verify_token
from core.response_handler import ResponseFormatter
from src.services.base_service import (
    UserService, CourseService, StudentService, TeacherService, AssessmentService,
    get_user_service, get_course_service, get_student_service, get_teacher_service, get_assessment_service
)

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

@router.get("/system", response_model=Dict[str, Any])
async def get_system_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get system-wide analytics."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin', 'teacher']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "user_growth": {},
            "course_activity": {},
            "performance_metrics": {},
            "system_health": {}
        }
        
        # Get user growth analytics
        user_service = get_user_service()
        total_users = await user_service.find_many("users", {})
        new_users = await user_service.find_many("users", {
            "created_at": {"$gte": start_date.isoformat()}
        })
        
        analytics["user_growth"] = {
            "total_users": len(total_users),
            "new_users": len(new_users),
            "growth_rate": (len(new_users) / max(len(total_users), 1)) * 100
        }
        
        # Get course activity
        course_service = get_course_service()
        total_courses = await course_service.find_many("courses", {})
        active_courses = await course_service.find_many("courses", {
            "updated_at": {"$gte": start_date.isoformat()}
        })
        
        analytics["course_activity"] = {
            "total_courses": len(total_courses),
            "active_courses": len(active_courses),
            "activity_rate": (len(active_courses) / max(len(total_courses), 1)) * 100
        }
        
        # Get performance metrics
        student_service = get_student_service()
        all_students = await student_service.find_many("students", {})
        
        if all_students:
            # Calculate average performance
            total_performance = sum(student.get('performance_score', 0) for student in all_students)
            avg_performance = total_performance / len(all_students)
            
            # Get performance distribution
            performance_ranges = {
                "excellent": len([s for s in all_students if s.get('performance_score', 0) >= 90]),
                "good": len([s for s in all_students if 80 <= s.get('performance_score', 0) < 90]),
                "average": len([s for s in all_students if 60 <= s.get('performance_score', 0) < 80]),
                "poor": len([s for s in all_students if s.get('performance_score', 0) < 60])
            }
            
            analytics["performance_metrics"] = {
                "average_performance_score": round(avg_performance, 2),
                "performance_distribution": performance_ranges,
                "total_students": len(all_students)
            }
        
        # Get system health (simplified)
        analytics["system_health"] = {
            "uptime_days": days,
            "status": "healthy",
            "last_updated": datetime.now().isoformat()
        }
        
        return ResponseFormatter.success(
            data=analytics,
            message="System analytics retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/users", response_model=Dict[str, Any])
async def get_user_analytics(
    period: str = Query("30d", regex="^\d+[dwm]$", description="Period in days (d), weeks (w), or months (m)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user analytics and statistics."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin', 'teacher']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Parse period
        period_value = int(period[:-1])
        period_unit = period[-1]
        
        if period_unit == 'd':
            delta = timedelta(days=period_value)
        elif period_unit == 'w':
            delta = timedelta(weeks=period_value)
        elif period_unit == 'm':
            delta = timedelta(days=period_value * 30)  # Approximate
        else:
            raise ValidationError("Invalid period format", "period")
        
        end_date = datetime.now()
        start_date = end_date - delta
        
        user_service = get_user_service()
        
        # Get user statistics
        total_users = await user_service.find_many("users", {})
        
        # Get new users
        new_users = await user_service.find_many("users", {
            "created_at": {"$gte": start_date.isoformat()}
        })
        
        # Get active users (logged in recently)
        active_users = await user_service.find_many("users", {
            "last_login": {"$gte": start_date.isoformat()}
        })
        
        # Get user role distribution
        role_distribution = {}
        for user in total_users:
            role = user.get('role', 'unknown')
            role_distribution[role] = role_distribution.get(role, 0) + 1
        
        analytics = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "value": period_value,
                "unit": period_unit
            },
            "user_statistics": {
                "total_users": len(total_users),
                "new_users": len(new_users),
                "active_users": len(active_users),
                "growth_rate": (len(new_users) / max(len(total_users), 1)) * 100,
                "retention_rate": (len(active_users) / max(len(total_users), 1)) * 100
            },
            "role_distribution": role_distribution
        }
        
        return ResponseFormatter.success(
            data=analytics,
            message="User analytics retrieved successfully"
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error getting user analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/courses", response_model=Dict[str, Any])
async def get_course_analytics(
    department_id: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get course analytics and statistics."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin', 'teacher']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        course_service = get_course_service()
        
        # Build filter
        filter_dict = {}
        if department_id:
            filter_dict["department_id"] = department_id
        
        # Get courses
        courses = await course_service.find_many("courses", filter_dict)
        
        # Get course statistics
        course_stats = {
            "total_courses": len(courses),
            "active_courses": len([c for c in courses if c.get('status') == 'active']),
            "inactive_courses": len([c for c in courses if c.get('status') == 'inactive']),
            "department_distribution": {}
        }
        
        # Department distribution
        for course in courses:
            dept_id = course.get('department_id', 'unknown')
            course_stats["department_distribution"][dept_id] = course_stats["department_distribution"].get(dept_id, 0) + 1
        
        # Get enrollment statistics
        student_service = get_student_service()
        all_enrollments = await student_service.find_many("students", {})
        
        enrollments_by_course = {}
        for enrollment in all_enrollments:
            course_id = enrollment.get('course_id')
            if course_id:
                enrollments_by_course[course_id] = enrollments_by_course.get(course_id, 0) + 1
        
        # Calculate average enrollment
        avg_enrollment = sum(enrollments_by_course.values()) / max(len(courses), 1)
        
        analytics = {
            "course_statistics": course_stats,
            "enrollment_statistics": {
                "total_enrollments": len(all_enrollments),
                "average_enrollment_per_course": round(avg_enrollment, 2),
                "enrollment_distribution": enrollments_by_course
            }
        }
        
        return ResponseFormatter.success(
            data=analytics,
            message="Course analytics retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting course analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_analytics(
    course_id: Optional[str] = Query(None),
    period: str = Query("30d", regex="^\d+[dwm]$", description="Period in days (d), weeks (w), or months (m)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get performance analytics for students."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin', 'teacher']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Parse period
        period_value = int(period[:-1])
        period_unit = period[-1]
        
        if period_unit == 'd':
            delta = timedelta(days=period_value)
        elif period_unit == 'w':
            delta = timedelta(weeks=period_value)
        elif period_unit == 'm':
            delta = timedelta(days=period_value * 30)  # Approximate
        else:
            raise ValidationError("Invalid period format", "period")
        
        end_date = datetime.now()
        start_date = end_date - delta
        
        student_service = get_student_service()
        assessment_service = get_assessment_service()
        
        # Build student filter
        student_filter = {}
        if course_id:
            student_filter["course_id"] = course_id
        
        # Get students
        students = await student_service.find_many("students", student_filter)
        
        # Get assessments for the period
        assessment_filter = {}
        if course_id:
            assessment_filter["course_id"] = course_id
        assessment_filter["created_at"] = {"$gte": start_date.isoformat()}
        
        assessments = await assessment_service.find_many("assessments", assessment_filter)
        
        # Calculate performance metrics
        performance_data = []
        
        for student in students:
            student_id = student.get('id')
            
            # Get student's assessments
            student_assessments = [
                a for a in assessments 
                if a.get('student_id') == student_id
            ]
            
            if student_assessments:
                avg_score = sum(a.get('score', 0) for a in student_assessments) / len(student_assessments)
                performance_data.append({
                    "student_id": student_id,
                    "student_name": student.get('name'),
                    "average_score": round(avg_score, 2),
                    "assessment_count": len(student_assessments),
                    "performance_trend": "improving" if len(student_assessments) > 1 else "stable"
                })
            else:
                performance_data.append({
                    "student_id": student_id,
                    "student_name": student.get('name'),
                    "average_score": student.get('performance_score', 0),
                    "assessment_count": 0,
                    "performance_trend": "no_data"
                })
        
        # Calculate class averages
        if performance_data:
            class_average = sum(d['average_score'] for d in performance_data) / len(performance_data)
            grade_distribution = {
                "A": len([d for d in performance_data if d['average_score'] >= 90]),
                "B": len([d for d in performance_data if 80 <= d['average_score'] < 90]),
                "C": len([d for d in performance_data if 70 <= d['average_score'] < 80]),
                "D": len([d for d in performance_data if 60 <= d['average_score'] < 70]),
                "F": len([d for d in performance_data if d['average_score'] < 60])
            }
        else:
            class_average = 0
            grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        
        analytics = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "value": period_value,
                "unit": period_unit
            },
            "class_statistics": {
                "total_students": len(students),
                "assessed_students": len([d for d in performance_data if d['assessment_count'] > 0]),
                "class_average": round(class_average, 2),
                "grade_distribution": grade_distribution
            },
            "individual_performance": performance_data
        }
        
        return ResponseFormatter.success(
            data=analytics,
            message="Performance analytics retrieved successfully"
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error getting performance analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/health", response_model=Dict[str, Any])
async def get_analytics_health(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Health check for analytics service."""
    try:
        # Check permissions
        if current_user.get('role') not in ['admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get service health
        services = {
            "user_service": get_user_service(),
            "course_service": get_course_service(),
            "student_service": get_student_service(),
            "teacher_service": get_teacher_service(),
            "assessment_service": get_assessment_service()
        }
        
        health_status = {
            "analytics_service": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service_health": {}
        }
        
        for service_name, service in services.items():
            try:
                service_health = await service.health_check()
                health_status["service_health"][service_name] = {
                    "status": "healthy" if service_health else "unhealthy",
                    "details": service_health
                }
            except Exception as e:
                health_status["service_health"][service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Determine overall status
        unhealthy_services = [
            name for name, status in health_status["service_health"].items()
            if status.get("status") == "unhealthy"
        ]
        
        if unhealthy_services:
            health_status["analytics_service"] = "degraded"
            health_status["unhealthy_services"] = unhealthy_services
        
        return ResponseFormatter.success(
            data=health_status,
            message="Analytics service health check completed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking analytics health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )