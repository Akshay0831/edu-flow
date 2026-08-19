"""
Course Repository

This module provides data access operations for course entities.
It implements the repository pattern with database abstraction.

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from uuid import uuid4
from datetime import datetime, date

from core.logging import get_logger
from core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from infrastructure.repositories.base_repository_with_db import BaseRepositoryWithDB
from models.course import CourseCreate, CourseUpdate, CourseResponse, CourseStatistics
from models.course_progress import CourseProgress

logger = get_logger(__name__)


class CourseRepository(BaseRepositoryWithDB):
    """Course repository with CRUD operations and data access."""
    
    def __init__(self, database_manager):
        super().__init__("courses", database_manager)
        self._cache = {}
    
    async def create(self, entity_data: Dict[str, Any]) -> CourseResponse:
        """Create a new course record."""
        try:
            # Validate course data
            await self._validate_course_data(entity_data)
            
            # Generate ID if not provided
            if 'id' not in entity_data:
                entity_data['id'] = str(uuid4())
            
            # Add created timestamp
            if 'created_at' not in entity_data:
                entity_data['created_at'] = datetime.utcnow().isoformat()
            if 'updated_at' not in entity_data:
                entity_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Use parent create method
            result = await super().create(entity_data)
            
            if result.success:
                # Cache the course
                self._cache[result.data['id']] = result.data
                return CourseResponse(**result.data)
            
            raise DatabaseError(result.error)
            
        except Exception as e:
            logger.error(f"Failed to create course: {str(e)}")
            raise DatabaseError(f"Failed to create course: {str(e)}")
    
    async def get_by_id(self, entity_id: str) -> Optional[CourseResponse]:
        """Get a course by ID."""
        try:
            # Check cache first
            if entity_id in self._cache:
                return CourseResponse(**self._cache[entity_id])
            
            # Get course from database
            result = await super().get_by_id(entity_id)
            
            if result.success and result.data:
                # Cache the course
                self._cache[entity_id] = result.data
                return CourseResponse(**result.data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get course by ID {entity_id}: {str(e)}")
            raise DatabaseError(f"Failed to get course by ID {entity_id}: {str(e)}")
    
    async def update(self, id: str, **data) -> Optional[CourseResponse]:
        """Update a course by ID."""
        try:
            # Get existing course
            existing_course = await self.get_by_id(id)
            if not existing_course:
                return None
            
            # Validate update data
            await self._validate_course_update(data)
            
            # Add updated timestamp
            data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update course
            updated_course = await self._update(self._collection_name, id, data)
            
            if updated_course:
                # Update cache
                self._cache[id] = updated_course
                return CourseResponse(**updated_course)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to update course {id}: {str(e)}")
            raise DatabaseError(f"Failed to update course {id}: {str(e)}")
    
    async def delete(self, id: str) -> bool:
        """Delete a course by ID."""
        try:
            # Get existing course
            existing_course = await self.get_by_id(id)
            if not existing_course:
                return False
            
            # Check if course has dependent entities
            await self._check_course_dependencies(id)
            
            # Delete course
            result = await self._delete(self._collection_name, id)
            
            # Remove from cache
            if id in self._cache:
                del self._cache[id]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete course {id}: {str(e)}")
            raise DatabaseError(f"Failed to delete course {id}: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[CourseResponse]:
        """Get all courses."""
        try:
            courses_data = await self._get_all(self._collection_name, skip, limit)
            
            courses = []
            for course_data in courses_data:
                course = CourseResponse(**course_data)
                courses.append(course)
                # Cache the course
                self._cache[course.id] = course
            
            return courses
            
        except Exception as e:
            logger.error(f"Failed to get all courses: {str(e)}")
            raise DatabaseError(f"Failed to get all courses: {str(e)}")
    
    async def search_courses(self, search_term: str, skip: int = 0, limit: int = 100) -> List[CourseResponse]:
        """Search courses by name, code, or description."""
        try:
            # Search query
            query = {
                "$or": [
                    {"name": {"$regex": search_term, "$options": "i"}},
                    {"code": {"$regex": search_term, "$options": "i"}},
                    {"description": {"$regex": search_term, "$options": "i"}}
                ]
            }
            
            courses_data = await self._search(self._collection_name, query, skip, limit)
            
            courses = []
            for course_data in courses_data:
                course = CourseResponse(**course_data)
                courses.append(course)
                # Cache the course
                self._cache[course.id] = course
            
            return courses
            
        except Exception as e:
            logger.error(f"Failed to search courses: {str(e)}")
            raise DatabaseError(f"Failed to search courses: {str(e)}")
    
    async def get_by_code(self, code: str) -> Optional[CourseResponse]:
        """Get a course by code."""
        try:
            # Query by code
            query = {"code": code}
            course_data = await self._find_one(self._collection_name, query)
            
            if course_data:
                course = CourseResponse(**course_data)
                # Cache the course
                self._cache[course.id] = course
                return course
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get course by code {code}: {str(e)}")
            raise DatabaseError(f"Failed to get course by code {code}: {str(e)}")
    
    async def get_courses_by_department(self, department_id: str, skip: int = 0, limit: int = 100) -> List[CourseResponse]:
        """Get courses by department."""
        try:
            # Query by department
            query = {"department_id": department_id}
            courses_data = await self._search(self._collection_name, query, skip, limit)
            
            courses = []
            for course_data in courses_data:
                course = CourseResponse(**course_data)
                courses.append(course)
                # Cache the course
                self._cache[course.id] = course
            
            return courses
            
        except Exception as e:
            logger.error(f"Failed to get courses by department {department_id}: {str(e)}")
            raise DatabaseError(f"Failed to get courses by department {department_id}: {str(e)}")
    
    async def get_courses_by_subject(self, subject_id: str, skip: int = 0, limit: int = 100) -> List[CourseResponse]:
        """Get courses by subject."""
        try:
            # Query by subject
            query = {"subject_id": subject_id}
            courses_data = await self._search(self._collection_name, query, skip, limit)
            
            courses = []
            for course_data in courses_data:
                course = CourseResponse(**course_data)
                courses.append(course)
                # Cache the course
                self._cache[course.id] = course
            
            return courses
            
        except Exception as e:
            logger.error(f"Failed to get courses by subject {subject_id}: {str(e)}")
            raise DatabaseError(f"Failed to get courses by subject {subject_id}: {str(e)}")
    
    async def get_active_courses(self, skip: int = 0, limit: int = 100) -> List[CourseResponse]:
        """Get active courses."""
        try:
            # Query for active courses
            query = {"status": "active"}
            courses_data = await self._search(self._collection_name, query, skip, limit)
            
            courses = []
            for course_data in courses_data:
                course = CourseResponse(**course_data)
                courses.append(course)
                # Cache the course
                self._cache[course.id] = course
            
            return courses
            
        except Exception as e:
            logger.error(f"Failed to get active courses: {str(e)}")
            raise DatabaseError(f"Failed to get active courses: {str(e)}")
    
    async def get_course_stats(self, course_id: str) -> CourseStatistics:
        """Get course statistics."""
        try:
            # Get course
            course = await self.get_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Get students enrolled in the course
            from infrastructure.repositories.mark_repository import MarkRepository
            mark_repo = MarkRepository()
            marks = await mark_repo.get_marks_by_course(course_id)
            
            # Calculate statistics
            total_students = len(marks)
            if total_students > 0:
                average_score = sum(mark.score for mark in marks) / total_students
                max_score = max(mark.score for mark in marks)
                min_score = min(mark.score for mark in marks)
                pass_count = sum(1 for mark in marks if mark.score >= 60)
                pass_percentage = (pass_count / total_students) * 100
            else:
                average_score = 0
                max_score = 0
                min_score = 0
                pass_count = 0
                pass_percentage = 0
            
            # Get teachers assigned to the course
            from infrastructure.repositories.teacher_repository import TeacherRepository
            teacher_repo = TeacherRepository()
            teachers = await teacher_repo.get_teachers_by_department(course.department_id)
            
            # Create stats object
            stats = CourseStats(
                course_id=course_id,
                course_name=course.name,
                course_code=course.code,
                total_students=total_students,
                average_score=round(average_score, 2),
                max_score=max_score,
                min_score=min_score,
                pass_count=pass_count,
                pass_percentage=round(pass_percentage, 2),
                total_credits=course.credits,
                department_id=course.department_id,
                teachers_count=len(teachers),
                start_date=course.start_date,
                end_date=course.end_date
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get course stats for {course_id}: {str(e)}")
            raise DatabaseError(f"Failed to get course stats for {course_id}: {str(e)}")
    
    async def get_course_progress(self, course_id: str, student_id: str) -> CourseProgress:
        """Get course progress for a specific student."""
        try:
            # Get course
            course = await self.get_by_id(course_id)
            if not course:
                raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Get student marks in this course
            from infrastructure.repositories.mark_repository import MarkRepository
            mark_repo = MarkRepository()
            marks = await mark_repo.get_marks_by_student_and_course(student_id, course_id)
            
            # Calculate progress
            total_assignments = len(marks)
            completed_assignments = sum(1 for mark in marks if mark.submission_date is not None)
            progress_percentage = (completed_assignments / total_assignments) * 100 if total_assignments > 0 else 0
            
            # Calculate average score
            if marks:
                average_score = sum(mark.score for mark in marks) / len(marks)
            else:
                average_score = 0
            
            # Create progress object
            progress = CourseProgress(
                course_id=course_id,
                student_id=student_id,
                course_name=course.name,
                total_assignments=total_assignments,
                completed_assignments=completed_assignments,
                progress_percentage=round(progress_percentage, 2),
                average_score=round(average_score, 2),
                last_updated=datetime.utcnow().isoformat()
            )
            
            return progress
            
        except Exception as e:
            logger.error(f"Failed to get course progress for {course_id} and {student_id}: {str(e)}")
            raise DatabaseError(f"Failed to get course progress for {course_id} and {student_id}: {str(e)}")
    
    async def batch_update_courses(self, updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple courses."""
        results = {}
        
        for update in updates:
            course_id = update['course_id']
            try:
                result = await self.update(course_id, **update)
                results[course_id] = result is not None
            except Exception as e:
                logger.error(f"Failed to update course {course_id}: {str(e)}")
                results[course_id] = False
        
        return results
    
    async def batch_delete_courses(self, course_ids: List[str]) -> Dict[str, bool]:
        """Delete multiple courses."""
        results = {}
        
        for course_id in course_ids:
            try:
                result = await self.delete(course_id)
                results[course_id] = result
            except Exception as e:
                logger.error(f"Failed to delete course {course_id}: {str(e)}")
                results[course_id] = False
        
        return results
    
    # Private helper methods
    
    async def _validate_course_data(self, data: Dict[str, Any]) -> None:
        """Validate course data."""
        # Check required fields
        required_fields = ['name', 'code', 'credits', 'department_id']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate course code uniqueness
        existing_course = await self.get_by_code(data['code'])
        if existing_course:
            raise ConflictError(f"Course with code '{data['code']}' already exists")
        
        # Validate course name uniqueness
        existing_name = await self._find_one(self._collection_name, {"name": data['name']})
        if existing_name:
            raise ConflictError(f"Course with name '{data['name']}' already exists")
        
        # Validate course code format
        if not data['code'].isalnum():
            raise ValidationError("Course code should be alphanumeric")
        
        # Validate credits
        if data.get('credits', 0) <= 0:
            raise ValidationError("Course credits must be positive")
        
        # Validate dates if provided
        if 'start_date' in data and 'end_date' in data:
            start_date = datetime.fromisoformat(data['start_date']).date()
            end_date = datetime.fromisoformat(data['end_date']).date()
            if start_date >= end_date:
                raise ValidationError("Start date must be before end date")
    
    async def _validate_course_update(self, data: Dict[str, Any]) -> None:
        """Validate course update data."""
        # Check if code is being updated and conflicts exist
        if 'code' in data and data['code']:
            existing_course = await self.get_by_code(data['code'])
            if existing_course:
                raise ConflictError(f"Course with code '{data['code']}' already exists")
        
        # Validate name uniqueness if being updated
        if 'name' in data and data['name']:
            existing_name = await self._find_one(self._collection_name, {"name": data['name']})
            if existing_name:
                raise ConflictError(f"Course with name '{data['name']}' already exists")
        
        # Validate credits if being updated
        if 'credits' in data and data['credits'] <= 0:
            raise ValidationError("Course credits must be positive")
        
        # Validate dates if being updated
        if 'start_date' in data and 'end_date' in data:
            start_date = datetime.fromisoformat(data['start_date']).date()
            end_date = datetime.fromisoformat(data['end_date']).date()
            if start_date >= end_date:
                raise ValidationError("Start date must be before end date")
    
    async def _check_course_dependencies(self, course_id: str) -> None:
        """Check if course has dependent entities."""
        # Check associated marks
        from infrastructure.repositories.mark_repository import MarkRepository
        mark_repo = MarkRepository()
        marks = await mark_repo.get_marks_by_course(course_id)
        if marks:
            raise ValidationError(f"Cannot delete course {course_id} - it has {len(marks)} associated marks")
        
        # Check associated timetable entries
        from infrastructure.repositories.timetable_entry_repository import TimetableEntryRepository
        timetable_repo = TimetableEntryRepository()
        entries = await timetable_repo.get_by_course(course_id)
        if entries:
            raise ValidationError(f"Cannot delete course {course_id} - it has {len(entries)} associated timetable entries")
        
        # Check associated enrollments
        from infrastructure.repositories.mark_repository import MarkRepository
        mark_repo = MarkRepository()
        marks = await mark_repo.get_marks_by_course(course_id)
        if marks:
            raise ValidationError(f"Cannot delete course {course_id} - it has {len(marks)} associated student enrollments")