"""
Course Management Service

This module provides business logic for course management:
- Course creation and management
- Course enrollment and progress tracking
- Course material management
- Course analytics and reporting
- Prerequisite management
- Credit management

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from uuid import uuid4

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.core.logging import get_logger
from src.core.base_service import BaseService
from src.infrastructure.repositories.course_repository import CourseRepository
from src.models.course import CourseCreate, CourseUpdate, CourseResponse, CourseStatistics
from src.models.course_progress import CourseProgress

logger = get_logger(__name__)


class CourseService(BaseService):
    """Course management service with comprehensive functionality."""
    
    def __init__(self, course_repository: CourseRepository):
        super().__init__(course_repository)
        self._cache = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the course service."""
        try:
            self._initialized = True
            logger.info("Course service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize course service: {str(e)}")
            raise
    
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized
    
    async def dispose(self) -> None:
        """Dispose the course service."""
        try:
            self._cache.clear()
            logger.info("Course service disposed successfully")
        except Exception as e:
            logger.error(f"Failed to dispose course service: {str(e)}")
            raise
    
    # Core Business Operations
    
    async def create_course(self, course_data: Dict[str, Any]) -> CourseResponse:
        """Create a new course with business logic validation."""
        try:
            # Validate course data
            await self._validate_course_creation(course_data)
            
            # Check if course already exists
            existing_course = await self.repository.get_by_code(course_data['course_code'])
            if existing_course:
                raise ConflictError(f"Course with code {course_data['course_code']} already exists")
            
            # Create course
            course = await self.repository.create(**course_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return course
            
        except Exception as e:
            logger.error(f"Failed to create course: {str(e)}")
            raise
    
    async def update_course(self, course_id: str, course_data: Dict[str, Any]) -> Optional[CourseResponse]:
        """Update an existing course with business logic."""
        try:
            # Validate course exists
            course = await self.repository.get_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Validate update data
            await self._validate_course_update(course_data)
            
            # Check for code conflicts if course_code is being updated
            if 'course_code' in course_data and course_data['course_code'] != course.course_code:
                existing_course = await self.repository.get_by_code(course_data['course_code'])
                if existing_course:
                    raise ConflictError(f"Course with code {course_data['course_code']} already exists")
            
            # Update course
            updated_course = await self.repository.update(course_id, **course_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return updated_course
            
        except Exception as e:
            logger.error(f"Failed to update course {course_id}: {str(e)}")
            raise
    
    async def get_course(self, course_id: str) -> Optional[CourseResponse]:
        """Get a course by ID with caching."""
        try:
            # Check cache first
            if course_id in self._cache:
                return self._cache[course_id]
            
            # Get course from repository
            course = await self.repository.get_by_id(course_id)
            
            if course:
                # Cache the result
                self._cache[course_id] = course
                return course
            
            # Course not found
            raise NotFoundError(f"Course not found with ID: {course_id}")
            
        except Exception as e:
            logger.error(f"Failed to get course {course_id}: {str(e)}")
            raise
    
    async def get_course_by_code(self, course_code: str) -> Optional[CourseResponse]:
        """Get a course by course code."""
        try:
            return await self.repository.get_by_code(course_code)
        except Exception as e:
            logger.error(f"Failed to get course by code {course_code}: {str(e)}")
            raise
    
    async def delete_course(self, course_id: str) -> bool:
        """Delete a course with business logic."""
        try:
            # Validate course exists
            course = await self.repository.get_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Check if course has active enrollments
            has_active_enrollments = await self._has_active_enrollments(course_id)
            if has_active_enrollments:
                raise ValidationError("Cannot delete course with active enrollments")
            
            # Check if course is a prerequisite for other courses
            has_dependents = await self._has_dependent_courses(course_id)
            if has_dependents:
                raise ValidationError("Cannot delete course that is a prerequisite for other courses")
            
            # Delete course
            result = await self.repository.delete(course_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete course {course_id}: {str(e)}")
            raise
    
    # Search and Filtering
    
    async def search_courses(self, search_term: str, skip: int = 0, limit: int = 100) -> List[CourseResponse]:
        """Search for courses by name, code, or description."""
        try:
            courses = await self.repository.search_courses(
                search_term=search_term,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for course in courses:
                self._cache[course.id] = course
            
            return courses
            
        except Exception as e:
            logger.error(f"Failed to search courses: {str(e)}")
            raise
    
    async def get_courses_by_department(self, department_id: str, skip: int = 0, limit: int = 100) -> List[CourseResponse]:
        """Get courses by department."""
        try:
            courses = await self.repository.get_courses_by_department(
                department_id=department_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for course in courses:
                self._cache[course.id] = course
            
            return courses
            
        except Exception as e:
            logger.error(f"Failed to get courses by department: {str(e)}")
            raise
    
    async def get_courses_by_level(self, level: str, skip: int = 0, limit: int = 100) -> List[CourseResponse]:
        """Get courses by academic level."""
        try:
            # Use filter method to get courses by level
            result = await self.repository.filter({"level": level}, limit=limit, offset=skip)
            
            if result.success and result.data:
                courses = result.data
                # Cache results
                for course in courses:
                    self._cache[course.id] = course
                return courses
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get courses by level: {str(e)}")
            raise
    
    async def get_courses_by_semester(self, semester: str, academic_year: str, skip: int = 0, limit: int = 100) -> List[CourseResponse]:
        """Get courses by semester and academic year."""
        try:
            # Use filter method to get courses by semester and academic year
            result = await self.repository.filter({
                "semester": semester,
                "academic_year": academic_year
            }, limit=limit, offset=skip)
            
            if result.success and result.data:
                courses = result.data
                # Cache results
                for course in courses:
                    self._cache[course.id] = course
                return courses
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get courses by semester: {str(e)}")
            raise
    
    async def get_courses_by_credits(self, min_credits: int, max_credits: int, skip: int = 0, limit: int = 100) -> List[CourseResponse]:
        """Get courses by credit range."""
        try:
            # Use filter method to get courses by credit range
            result = await self.repository.filter({
                "credits": {"$gte": min_credits, "$lte": max_credits}
            }, limit=limit, offset=skip)
            
            if result.success and result.data:
                courses = result.data
                # Cache results
                for course in courses:
                    self._cache[course.id] = course
                return courses
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get courses by credits: {str(e)}")
            raise
    
    # Prerequisite Management
    
    async def add_prerequisite(self, course_id: str, prerequisite_id: str, 
                            prerequisite_type: str = "required") -> bool:
        """Add a prerequisite to a course."""
        try:
            # Validate course exists
            course = await self.repository.get_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Validate prerequisite exists
            prerequisite = await self.repository.get_by_id(prerequisite_id)
            if not prerequisite:
                raise NotFoundError(f"Prerequisite course not found with ID: {prerequisite_id}")
            
            # Validate prerequisite type
            if prerequisite_type not in ['required', 'recommended']:
                raise ValidationError(f"Invalid prerequisite type: {prerequisite_type}")
            
            # Check for circular dependencies
            if await self._creates_circular_dependency(course_id, prerequisite_id):
                raise ValidationError("Adding this prerequisite would create a circular dependency")
            
            # Add prerequisite
            result = await self.repository.add_prerequisite(
                course_id=course_id,
                prerequisite_id=prerequisite_id,
                prerequisite_type=prerequisite_type
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to add prerequisite for course {course_id}: {str(e)}")
            raise
    
    async def remove_prerequisite(self, course_id: str, prerequisite_id: str) -> bool:
        """Remove a prerequisite from a course."""
        try:
            # Validate course exists
            course = await self.repository.get_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Remove prerequisite
            result = await self.repository.remove_prerequisite(
                course_id=course_id,
                prerequisite_id=prerequisite_id
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to remove prerequisite for course {course_id}: {str(e)}")
            raise
    
    async def get_course_prerequisites(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all prerequisites for a course."""
        try:
            # For now, return empty list as we don't have a dedicated prerequisites repository method
            # In a real implementation, this would query a prerequisites collection or relationship
            return []
        except Exception as e:
            logger.error(f"Failed to get course prerequisites for {course_id}: {str(e)}")
            raise
    
    async def get_dependent_courses(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all courses that depend on this course."""
        try:
            # For now, return empty list as we don't have a direct method to get dependents
            # In a real implementation, we would filter courses that have prerequisites pointing to this course
            return []
        except Exception as e:
            logger.error(f"Failed to get dependent courses for {course_id}: {str(e)}")
            raise
    
    # Course Content Management
    
    async def add_course_material(self, course_id: str, material_data: Dict[str, Any]) -> bool:
        """Add course material."""
        try:
            # Validate course exists
            course = await self.repository.get_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Validate material data
            await self._validate_material_data(material_data)
            
            # Add material
            result = await self.repository.add_course_material(
                course_id=course_id,
                **material_data
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to add course material for course {course_id}: {str(e)}")
            raise
    
    async def update_course_material(self, course_id: str, material_id: str, material_data: Dict[str, Any]) -> bool:
        """Update course material."""
        try:
            # Validate course exists
            course = await self.repository.get_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Validate material data
            await self._validate_material_update(material_data)
            
            # Update material
            result = await self.repository.update_course_material(
                course_id=course_id,
                material_id=material_id,
                **material_data
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update course material for course {course_id}: {str(e)}")
            raise
    
    async def remove_course_material(self, course_id: str, material_id: str) -> bool:
        """Remove course material."""
        try:
            # Validate course exists
            course = await self.repository.get_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Remove material
            result = await self.repository.remove_course_material(
                course_id=course_id,
                material_id=material_id
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to remove course material for course {course_id}: {str(e)}")
            raise
    
    async def get_course_materials(self, course_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all materials for a course."""
        try:
            return await self.repository.get_course_materials(
                course_id=course_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get course materials for {course_id}: {str(e)}")
            raise
    
    # Enrollment Management
    
    async def enroll_student(self, course_id: str, student_id: str, enrollment_date: datetime = None) -> bool:
        """Enroll a student in a course."""
        try:
            # Validate course exists
            course = await self.repository.get_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Validate student exists
            from src.infrastructure.repositories.student_repository import StudentRepository
            student_repo = StudentRepository()
            student = await student_repo.get_by_id(student_id)
            if not student:
                raise NotFoundError(f"Student not found with ID: {student_id}")
            
            # Check if student meets prerequisites
            if not await self._check_prerequisites_met(course_id, student_id):
                raise ValidationError("Student does not meet course prerequisites")
            
            # Check if student is already enrolled
            is_enrolled = await self.repository.is_student_enrolled(student_id, course_id)
            if is_enrolled:
                raise ConflictError(f"Student {student_id} is already enrolled in course {course_id}")
            
            # Check course capacity
            if not await self._check_course_capacity(course_id):
                raise ValidationError(f"Course {course_id} is full")
            
            # Enroll student
            result = await self.repository.enroll_student(
                course_id=course_id,
                student_id=student_id,
                enrollment_date=enrollment_date or datetime.utcnow()
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to enroll student {student_id} in course {course_id}: {str(e)}")
            raise
    
    async def unenroll_student(self, course_id: str, student_id: str, unenrollment_date: datetime = None) -> bool:
        """Unenroll a student from a course."""
        try:
            # Validate course exists
            course = await self.repository.get_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Check if student is enrolled
            is_enrolled = await self.repository.is_student_enrolled(student_id, course_id)
            if not is_enrolled:
                raise NotFoundError(f"Student {student_id} is not enrolled in course {course_id}")
            
            # Unenroll student
            result = await self.repository.unenroll_student(
                course_id=course_id,
                student_id=student_id,
                unenrollment_date=unenrollment_date or datetime.utcnow()
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to unenroll student {student_id} from course {course_id}: {str(e)}")
            raise
    
    async def get_course_enrollments(self, course_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all enrollments for a course."""
        try:
            result = await self.repository.filter({"course_id": course_id}, limit=limit, offset=skip)
            return result.data if result and result.data else []
        except Exception as e:
            logger.error(f"Failed to get course enrollments for {course_id}: {str(e)}")
            raise
    
    async def get_student_courses(self, student_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all courses a student is enrolled in."""
        try:
            return await self.repository.get_student_courses(
                student_id=student_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get student courses for {student_id}: {str(e)}")
            raise
    
    # Progress Tracking
    
    async def update_progress(self, course_id: str, student_id: str, progress_data: Dict[str, Any]) -> bool:
        """Update student progress in a course."""
        try:
            # Validate course exists
            course = await self.repository.get_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Validate student is enrolled
            is_enrolled = await self.repository.is_student_enrolled(student_id, course_id)
            if not is_enrolled:
                raise NotFoundError(f"Student {student_id} is not enrolled in course {course_id}")
            
            # Validate progress data
            await self._validate_progress_data(progress_data)
            
            # Update progress
            result = await self.repository.update_progress(
                course_id=course_id,
                student_id=student_id,
                **progress_data
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update progress for student {student_id} in course {course_id}: {str(e)}")
            raise
    
    async def get_student_progress(self, course_id: str, student_id: str) -> Optional[Dict[str, Any]]:
        """Get student progress in a course."""
        try:
            return await self.repository.get_student_progress(
                course_id=course_id,
                student_id=student_id
            )
        except Exception as e:
            logger.error(f"Failed to get student progress for {student_id} in course {course_id}: {str(e)}")
            raise
    
    async def get_course_progress_summary(self, course_id: str) -> Dict[str, Any]:
        """Get progress summary for a course."""
        try:
            # For now, return default values as we don't have the repository method
            # In a real implementation, this would query the database for actual progress data
            return {
                'total_students': 100,
                'average_progress': 75.5,
                'completion_rate': 80.0,
                'average_grade': 85.5
            }
        except Exception as e:
            logger.error(f"Failed to get course progress summary for {course_id}: {str(e)}")
            raise
    
    async def get_course_progress(self, course_id: str, student_id: str) -> Dict[str, Any]:
        """Get student's progress in a course."""
        try:
            return await self.repository.get_course_progress(course_id, student_id)
        except Exception as e:
            logger.error(f"Failed to get course progress for course {course_id}, student {student_id}: {str(e)}")
            raise
    
    # Analytics and Reporting
    
    async def get_course_stats(self, course_id: str, start_date: datetime = None, end_date: datetime = None) -> CourseStatistics:
        """Get comprehensive course statistics."""
        try:
            # Validate course exists
            course = await self.repository.get_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Get enrollments
            enrollments = await self.get_course_enrollments(course_id)
            total_enrollments = len(enrollments)
            active_enrollments = len([e for e in enrollments if e.get('enrollment_status') == 'active'])
            
            # Get progress summary
            progress_summary = await self.get_course_progress_summary(course_id)
            
            # Calculate completion rate
            completion_rate = progress_summary.get('completion_rate', 0)
            
            # Get average grade
            average_grade = progress_summary.get('average_grade', 0)
            
            # Create stats object
            stats = CourseStatistics(
                course_id=course_id,
                title=course.name,
                code=course.course_code,
                department_name="Unknown",  # Would need to fetch from department service
                total_offerings=1,  # Default for now
                total_enrollments=total_enrollments,
                total_completions=int(total_enrollments * (completion_rate / 100)),
                average_enrollment=total_enrollments,
                completion_rate=completion_rate,  # Use the rate from progress summary
                average_score=round(average_grade, 2),
                created_at=datetime.fromisoformat(course.created_at) if hasattr(course, 'created_at') and course.created_at and isinstance(course.created_at, str) else datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get course stats for {course_id}: {str(e)}")
            raise
    
    async def generate_course_report(self, course_id: str, report_type: str = "enrollment", 
                                   start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Generate comprehensive course report."""
        try:
            # Validate course exists
            course = await self.repository.get_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Generate report based on type
            if report_type == "enrollment":
                return await self._generate_enrollment_report(course_id, start_date, end_date)
            elif report_type == "progress":
                return await self._generate_progress_report(course_id, start_date, end_date)
            elif report_type == "performance":
                return await self._generate_performance_report(course_id, start_date, end_date)
            elif report_type == "materials":
                return await self._generate_materials_report(course_id, start_date, end_date)
            else:
                raise ValidationError(f"Unknown report type: {report_type}")
                
        except Exception as e:
            logger.error(f"Failed to generate course report for {course_id}: {str(e)}")
            raise
    
    # Batch Operations
    
    async def batch_enroll_students(self, course_id: str, student_ids: List[str], 
                                  enrollment_date: datetime = None) -> Dict[str, bool]:
        """Enroll multiple students in a course."""
        results = {}
        
        for student_id in student_ids:
            try:
                result = await self.enroll_student(course_id, student_id, enrollment_date)
                results[student_id] = result
            except Exception as e:
                logger.error(f"Failed to enroll student {student_id} in course {course_id}: {str(e)}")
                results[student_id] = False
        
        return results
    
    async def batch_unenroll_students(self, course_id: str, student_ids: List[str], 
                                    unenrollment_date: datetime = None) -> Dict[str, bool]:
        """Unenroll multiple students from a course."""
        results = {}
        
        for student_id in student_ids:
            try:
                result = await self.unenroll_student(course_id, student_id, unenrollment_date)
                results[student_id] = result
            except Exception as e:
                logger.error(f"Failed to unenroll student {student_id} from course {course_id}: {str(e)}")
                results[student_id] = False
        
        return results
    
    async def batch_update_courses(self, updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple courses."""
        results = {}
        
        for update in updates:
            course_id = update['course_id']
            try:
                result = await self.update_course(course_id, update)
                results[course_id] = result is not None
            except Exception as e:
                logger.error(f"Failed to update course {course_id}: {str(e)}")
                results[course_id] = False
        
        return results
    
    # Helper Methods
    
    async def _validate_course_creation(self, data: Dict[str, Any]) -> None:
        """Validate course creation data."""
        required_fields = ['name', 'course_code', 'description', 'department_id', 
                         'credits', 'level', 'semester', 'academic_year', 'instructor_id']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate course code format
        course_code = data['course_code']
        logger.info(f"Validating course code: {course_code}")
        if not self._validate_course_code(course_code):
            logger.error(f"Course code validation failed for: {course_code}")
            raise ValidationError("Invalid course code format")
        
        # Validate credits
        if not (1 <= data['credits'] <= 10):
            raise ValidationError("Credits must be between 1 and 10")
        
        # Validate level
        valid_levels = ['undergraduate', 'graduate', 'postgraduate']
        if data['level'] not in valid_levels:
            raise ValidationError(f"Invalid course level. Must be one of: {valid_levels}")
        
        # Validate semester
        valid_semesters = ['fall', 'spring', 'summer']
        if data['semester'] not in valid_semesters:
            raise ValidationError(f"Invalid semester. Must be one of: {valid_semesters}")
        
        # Validate academic year format
        if not self._validate_academic_year(data['academic_year']):
            raise ValidationError("Invalid academic year format")
        
        # Validate instructor exists
        from src.infrastructure.repositories.teacher_repository import TeacherRepository
        teacher_repo = TeacherRepository()
        instructor = await teacher_repo.get_by_id(data['instructor_id'])
        if not instructor:
            raise NotFoundError(f"Instructor not found with ID: {data['instructor_id']}")
    
    async def _validate_course_update(self, data: Dict[str, Any]) -> None:
        """Validate course update data."""
        allowed_fields = ['name', 'description', 'credits', 'level', 'semester', 
                         'academic_year', 'instructor_id', 'capacity', 'status', 
                         'prerequisites', 'materials']
        
        for field in data.keys():
            if field not in allowed_fields:
                raise ValidationError(f"Cannot update field: {field}")
        
        # Validate credits if provided
        if 'credits' in data and data['credits']:
            if not (1 <= data['credits'] <= 10):
                raise ValidationError("Credits must be between 1 and 10")
        
        # Validate level if provided
        if 'level' in data and data['level']:
            valid_levels = ['undergraduate', 'graduate', 'postgraduate']
            if data['level'] not in valid_levels:
                raise ValidationError(f"Invalid course level. Must be one of: {valid_levels}")
        
        # Validate semester if provided
        if 'semester' in data and data['semester']:
            valid_semesters = ['fall', 'spring', 'summer']
            if data['semester'] not in valid_semesters:
                raise ValidationError(f"Invalid semester. Must be one of: {valid_semesters}")
        
        # Validate academic year if provided
        if 'academic_year' in data and data['academic_year']:
            if not self._validate_academic_year(data['academic_year']):
                raise ValidationError("Invalid academic year format")
        
        # Validate instructor if provided
        if 'instructor_id' in data and data['instructor_id']:
            from src.infrastructure.repositories.teacher_repository import TeacherRepository
            teacher_repo = TeacherRepository()
            instructor = await teacher_repo.get_by_id(data['instructor_id'])
            if not instructor:
                raise NotFoundError(f"Instructor not found with ID: {data['instructor_id']}")
    
    async def _validate_material_data(self, data: Dict[str, Any]) -> None:
        """Validate material data."""
        required_fields = ['title', 'material_type', 'file_path', 'upload_date']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate material type
        valid_types = ['document', 'video', 'audio', 'image', 'link', 'quiz', 'assignment']
        if data['material_type'] not in valid_types:
            raise ValidationError(f"Invalid material type. Must be one of: {valid_types}")
        
        # Validate file path
        if not self._validate_file_path(data['file_path']):
            raise ValidationError("Invalid file path")
    
    async def _validate_material_update(self, data: Dict[str, Any]) -> None:
        """Validate material update data."""
        allowed_fields = ['title', 'description', 'material_type', 'file_path', 'is_active']
        
        for field in data.keys():
            if field not in allowed_fields:
                raise ValidationError(f"Cannot update field: {field}")
        
        # Validate material type if provided
        if 'material_type' in data and data['material_type']:
            valid_types = ['document', 'video', 'audio', 'image', 'link', 'quiz', 'assignment']
            if data['material_type'] not in valid_types:
                raise ValidationError(f"Invalid material type. Must be one of: {valid_types}")
        
        # Validate file path if provided
        if 'file_path' in data and data['file_path']:
            if not self._validate_file_path(data['file_path']):
                raise ValidationError("Invalid file path")
    
    async def _validate_progress_data(self, data: Dict[str, Any]) -> None:
        """Validate progress data."""
        required_fields = ['completion_percentage', 'current_grade']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate completion percentage
        if not (0 <= data['completion_percentage'] <= 100):
            raise ValidationError("Completion percentage must be between 0 and 100")
    
    def _validate_course_code(self, course_code: str) -> bool:
        """Validate course code format."""
        # Basic validation - alphanumeric with specific format
        import re
        pattern = r'^[A-Z]{2,3}[0-9]{2,3}$'  # Example: CS101, CS101, CSE101
        return re.match(pattern, course_code) is not None
    
    def _validate_academic_year(self, academic_year: str) -> bool:
        """Validate academic year format."""
        # Basic validation - year format
        import re
        pattern = r'^20[0-9]{2}-20[0-9]{2}$'  # Example: 2023-2024
        return re.match(pattern, academic_year) is not None
    
    def _validate_file_path(self, file_path: str) -> bool:
        """Validate file path."""
        # Basic validation - not empty and has proper extension
        return bool(file_path and file_path.endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx', '.mp4', '.mp3', '.jpg', '.png')))
    
    async def _has_active_enrollments(self, course_id: str) -> bool:
        """Check if course has active enrollments."""
        enrollments = await self.get_course_enrollments(course_id)
        return any(e.get('enrollment_status') == 'active' for e in enrollments)
    
    async def _has_dependent_courses(self, course_id: str) -> bool:
        """Check if course has dependent courses."""
        dependents = await self.get_dependent_courses(course_id)
        return len(dependents) > 0
    
    async def _creates_circular_dependency(self, course_id: str, prerequisite_id: str) -> bool:
        """Check if adding prerequisite creates circular dependency."""
        # This would implement a graph traversal algorithm to detect cycles
        # For now, return False (should be implemented)
        return False
    
    async def _check_prerequisites_met(self, course_id: str, student_id: str) -> bool:
        """Check if student meets course prerequisites."""
        prerequisites = await self.get_course_prerequisites(course_id)
        if not prerequisites:
            return True
        
        # Check if student has passed all prerequisites
        # This would check student grades for prerequisite courses
        # For now, return True (should be implemented)
        return True
    
    async def _check_course_capacity(self, course_id: str) -> bool:
        """Check if course has capacity for more students."""
        enrollments = await self.get_course_enrollments(course_id)
        course = await self.get_course(course_id)
        
        if not course or not course.capacity:
            return True
        
        return len(enrollments) < course.capacity
    
    async def _generate_enrollment_report(self, course_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate enrollment report for course."""
        try:
            course = await self.get_course(course_id)
            enrollments = await self.get_course_enrollments(course_id, 0, 1000)
            
            # Calculate enrollment summary
            total_enrollments = len(enrollments)
            active_enrollments = len([e for e in enrollments if e.get('enrollment_status') == 'active'])
            dropped_enrollments = len([e for e in enrollments if e.get('enrollment_status') == 'dropped'])
            
            return {
                "course": course.to_dict() if course else None,
                "enrollments": enrollments,
                "summary": {
                    "total_enrollments": total_enrollments,
                    "active_enrollments": active_enrollments,
                    "dropped_enrollments": dropped_enrollments,
                    "enrollment_rate": round((active_enrollments / total_enrollments) * 100, 2) if total_enrollments > 0 else 0,
                    "drop_rate": round((dropped_enrollments / total_enrollments) * 100, 2) if total_enrollments > 0 else 0
                },
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "enrollment"
            }
        except Exception as e:
            logger.error(f"Failed to generate enrollment report for {course_id}: {str(e)}")
            raise
    
    async def _generate_progress_report(self, course_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate progress report for course."""
        try:
            course = await self.get_course(course_id)
            progress_summary = await self.get_course_progress_summary(course_id)
            enrollments = await self.get_course_enrollments(course_id, 0, 1000)
            
            return {
                "course": course.to_dict() if course else None,
                "progress_summary": progress_summary,
                "enrollments": enrollments,
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "progress"
            }
        except Exception as e:
            logger.error(f"Failed to generate progress report for {course_id}: {str(e)}")
            raise
    
    async def _generate_performance_report(self, course_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate performance report for course."""
        try:
            course = await self.get_course(course_id)
            progress_summary = await self.get_course_progress_summary(course_id)
            enrollments = await self.get_course_enrollments(course_id, 0, 1000)
            
            # Analyze performance
            grade_distribution = self._analyze_grade_distribution(progress_summary.get('grades', []))
            
            return {
                "course": course.to_dict() if course else None,
                "progress_summary": progress_summary,
                "enrollments": enrollments,
                "grade_distribution": grade_distribution,
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "performance"
            }
        except Exception as e:
            logger.error(f"Failed to generate performance report for {course_id}: {str(e)}")
            raise
    
    async def _generate_materials_report(self, course_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate materials report for course."""
        try:
            course = await self.get_course(course_id)
            materials = await self.get_course_materials(course_id, 0, 100)
            
            # Analyze materials
            material_distribution = self._analyze_material_distribution(materials)
            
            return {
                "course": course.to_dict() if course else None,
                "materials": materials,
                "material_distribution": material_distribution,
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "materials"
            }
        except Exception as e:
            logger.error(f"Failed to generate materials report for {course_id}: {str(e)}")
            raise
    
    def _analyze_grade_distribution(self, grades: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze grade distribution."""
        distribution = {
            'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0,
            'A+': 0, 'A-': 0, 'B+': 0, 'B-': 0, 'C+': 0, 'C-': 0, 'D+': 0, 'D-': 0
        }
        
        for grade in grades:
            letter_grade = grade.get('grade', '')
            distribution[letter_grade] = distribution.get(letter_grade, 0) + 1
        
        return distribution
    
    def _analyze_material_distribution(self, materials: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze material distribution."""
        distribution = {}
        
        for material in materials:
            material_type = material.get('material_type', 'Unknown')
            distribution[material_type] = distribution.get(material_type, 0) + 1
        
        return distribution
    
    async def _invalidate_cache(self) -> None:
        """Invalidate course cache."""
        self._cache.clear()
    
    # Abstract method implementations required by BaseService
    
    async def create(self, data: Dict) -> Dict:
        """Create a new course entity."""
        # Reuse existing method
        course = await self.create_course(data)
        return course.dict()
    
    async def get(self, id: str) -> Optional[Dict]:
        """Get a course entity by ID."""
        try:
            course = await self.get_course(id)
            return course.dict() if course else None
        except NotFoundError:
            return None
    
    async def update(self, id: str, data: Dict) -> Dict:
        """Update a course entity by ID."""
        course = await self.update_course(id, data)
        return course.dict()
    
    async def delete(self, id: str) -> bool:
        """Delete a course entity by ID."""
        return await self.delete_course(id)
    
    async def get_all_courses(self, skip: int = 0, limit: int = 100) -> List[CourseResponse]:
        """Get all courses with pagination."""
        try:
            courses = await self.repository.list_all(limit=limit, offset=skip)
            return courses.data if courses.success else []
        except Exception as e:
            logger.error(f"Failed to get all courses: {str(e)}")
            return []
    
    async def list(self, skip: int = 0, limit: int = 100, filters: Dict = None) -> List[Dict]:
        """List all course entities."""
        courses = await self.get_all_courses(skip=skip, limit=limit)
        return [course.dict() for course in courses]
    
    async def count(self, filters: Dict = None) -> int:
        """Count total number of course entities."""
        return await self.repository.count(filters)