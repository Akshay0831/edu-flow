"""
Student Repository

This module provides data access operations for student entities.
It implements the repository pattern with database abstraction.

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from uuid import uuid4
from datetime import datetime, date

from src.core.logging import get_logger
from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.infrastructure.repositories.base_repository import BaseRepository, QueryResult
from src.models.student import StudentCreate, StudentUpdate, StudentResponse
from src.models.student_stats import StudentStats

logger = get_logger(__name__)


class StudentRepository(BaseRepository):
    """Student repository with CRUD operations and data access."""
    
    def __init__(self):
        super().__init__("students")
        self._cache = {}
    
    async def create(self, entity_data: Dict[str, Any]) -> QueryResult:
        """Create a new student record."""
        try:
            # Validate student data
            await self._validate_student_data(entity_data)
            
            # Generate ID if not provided
            if 'id' not in entity_data:
                entity_data['id'] = str(uuid4())
            
            # Add created timestamp
            entity_data['created_at'] = datetime.utcnow().isoformat()
            entity_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Get database instance and create student
            from src.core.database_abstraction import DatabaseInterface
            # For now, create a mock database interface that we can replace later
            mock_db = self._get_mock_db()
            student_id = await mock_db.insert_one(self._collection_name, entity_data)
            
            # Cache the student
            self._cache[student_id] = entity_data
            
            return QueryResult(success=True, data=StudentResponse(**entity_data))
            
        except Exception as e:
            logger.error(f"Failed to create student: {str(e)}")
            return QueryResult(success=False, error=f"Failed to create student: {str(e)}")
    
    def _get_mock_db(self):
        """Get a mock database interface for testing."""
        class MockDatabase:
            async def insert_one(self, collection, document):
                return document['id']
            
            async def find_one(self, collection, filter):
                # Simple mock for testing
                for student_id, student_data in self._cache.items():
                    if all(student_data.get(k) == v for k, v in filter.items()):
                        return student_data
                return None
            
            async def update_one(self, collection, filter, update):
                return 1
            
            async def delete_one(self, collection, filter):
                return 1
            
            async def find_many(self, collection, filter, limit=None, skip=None):
                # Return mock data for testing - optimized list comprehension
                cache_keys = list(self._cache.keys())
                if limit:
                    return [self._cache[k] for k in cache_keys[:limit]]
                else:
                    return [self._cache[k] for k in cache_keys]
        
        return MockDatabase()
    
    async def get_by_id(self, entity_id: str) -> QueryResult:
        """Get a student by ID."""
        try:
            # Check cache first
            if entity_id in self._cache:
                return QueryResult(success=True, data=StudentResponse(**self._cache[entity_id]))
            
            # Get student from database
            mock_db = self._get_mock_db()
            student = await mock_db.find_one(self._collection_name, {"id": entity_id})
            
            if student:
                # Cache the student
                self._cache[entity_id] = student
                return QueryResult(success=True, data=StudentResponse(**student))
            
            return QueryResult(success=True, data=None)
            
        except Exception as e:
            logger.error(f"Failed to get student by ID {entity_id}: {str(e)}")
            return QueryResult(success=False, error=f"Failed to get student by ID {entity_id}: {str(e)}")
    
    async def update(self, entity_id: str, entity_data: Dict[str, Any]) -> QueryResult:
        """Update a student by ID."""
        try:
            # Get existing student
            existing_result = await self.get_by_id(entity_id)
            if not existing_result.success:
                return existing_result
            if not existing_result.data:
                return QueryResult(success=True, data=None)
            
            # Validate update data
            await self._validate_student_update(entity_data)
            
            # Add updated timestamp
            entity_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update student
            mock_db = self._get_mock_db()
            result = await mock_db.update_one(self._collection_name, {"id": entity_id}, entity_data)
            
            if result:
                # Update cache
                self._cache[entity_id] = entity_data
                return QueryResult(success=True, data=StudentResponse(**entity_data))
            
            return QueryResult(success=True, data=None)
            
        except Exception as e:
            logger.error(f"Failed to update student {entity_id}: {str(e)}")
            return QueryResult(success=False, error=f"Failed to update student {entity_id}: {str(e)}")
    
    async def delete(self, entity_id: str) -> QueryResult:
        """Delete a student by ID."""
        try:
            # Get existing student
            existing_result = await self.get_by_id(entity_id)
            if not existing_result.success:
                return existing_result
            if not existing_result.data:
                return QueryResult(success=True, data=True)
            
            # Delete student
            mock_db = self._get_mock_db()
            result = await mock_db.delete_one(self._collection_name, {"id": entity_id})
            
            # Remove from cache
            if entity_id in self._cache:
                del self._cache[entity_id]
            
            return QueryResult(success=True, data=result)
            
        except Exception as e:
            logger.error(f"Failed to delete student {entity_id}: {str(e)}")
            return QueryResult(success=False, error=f"Failed to delete student {entity_id}: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[StudentResponse]:
        """Get all students."""
        try:
            students_data = await self._get_all(self._collection_name, skip, limit)
            
            students = []
            for student_data in students_data:
                student = StudentResponse(**student_data)
                students.append(student)
                # Cache the student
                self._cache[student.id] = student
            
            return students
            
        except Exception as e:
            logger.error(f"Failed to get all students: {str(e)}")
            raise DatabaseError(f"Failed to get all students: {str(e)}")
    
    async def search_students(self, search_term: str, skip: int = 0, limit: int = 100) -> List[StudentResponse]:
        """Search students by name, email, or student ID."""
        try:
            # Search query
            query = {
                "$or": [
                    {"name": {"$regex": search_term, "$options": "i"}},
                    {"email": {"$regex": search_term, "$options": "i"}},
                    {"student_id": {"$regex": search_term, "$options": "i"}}
                ]
            }
            
            students_data = await self._search(self._collection_name, query, skip, limit)
            
            students = []
            for student_data in students_data:
                student = StudentResponse(**student_data)
                students.append(student)
                # Cache the student
                self._cache[student.id] = student
            
            return students
            
        except Exception as e:
            logger.error(f"Failed to search students: {str(e)}")
            raise DatabaseError(f"Failed to search students: {str(e)}")
    
    async def get_by_email(self, email: str) -> Optional[StudentResponse]:
        """Get a student by email."""
        try:
            # Query by email
            query = {"email": email}
            student_data = await self._find_one(self._collection_name, query)
            
            if student_data:
                student = StudentResponse(**student_data)
                # Cache the student
                self._cache[student.id] = student
                return student
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get student by email {email}: {str(e)}")
            raise DatabaseError(f"Failed to get student by email {email}: {str(e)}")
    
    async def get_by_student_id(self, student_id: str) -> Optional[StudentResponse]:
        """Get a student by student ID."""
        try:
            # Query by student ID
            query = {"student_id": student_id}
            student_data = await self._find_one(self._collection_name, query)
            
            if student_data:
                student = StudentResponse(**student_data)
                # Cache the student
                self._cache[student.id] = student
                return student
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get student by student ID {student_id}: {str(e)}")
            raise DatabaseError(f"Failed to get student by student ID {student_id}: {str(e)}")
    
    async def get_students_by_department(self, department_id: str, skip: int = 0, limit: int = 100) -> List[StudentResponse]:
        """Get students by department."""
        try:
            # Query by department
            query = {"department_id": department_id}
            students_data = await self._search(self._collection_name, query, skip, limit)
            
            students = []
            for student_data in students_data:
                student = StudentResponse(**student_data)
                students.append(student)
                # Cache the student
                self._cache[student.id] = student
            
            return students
            
        except Exception as e:
            logger.error(f"Failed to get students by department {department_id}: {str(e)}")
            raise DatabaseError(f"Failed to get students by department {department_id}: {str(e)}")
    
    async def get_student_stats(self, student_id: str) -> StudentStats:
        """Get student statistics."""
        try:
            # Get student
            student = await self.get_by_id(student_id)
            if not student:
                raise NotFoundError(f"Student not found with ID: {student_id}")
            
            # Get courses associated with student
            from src.infrastructure.repositories.course_repository import CourseRepository
            course_repo = CourseRepository()
            courses = await course_repo.get_courses_by_student(student_id)
            
            # Get marks associated with student
            from src.infrastructure.repositories.mark_repository import MarkRepository
            mark_repo = MarkRepository()
            marks = await mark_repo.get_marks_by_student(student_id)
            
            # Calculate statistics
            total_courses = len(courses)
            total_marks = len(marks)
            average_score = sum(mark.score for mark in marks) / total_marks if total_marks > 0 else 0
            
            # Create stats object
            stats = StudentStats(
                student_id=student_id,
                student_name=student.name,
                total_courses=total_courses,
                total_marks=total_marks,
                average_score=round(average_score, 2),
                gpa=await self._calculate_gpa(marks),
                registration_date=student.created_at,
                last_activity=student.updated_at
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get student stats for {student_id}: {str(e)}")
            raise DatabaseError(f"Failed to get student stats for {student_id}: {str(e)}")
    
    async def get_active_students(self, skip: int = 0, limit: int = 100) -> List[StudentResponse]:
        """Get active students."""
        try:
            # Query for active students
            query = {"status": "active"}
            students_data = await self._search(self._collection_name, query, skip, limit)
            
            students = []
            for student_data in students_data:
                student = StudentResponse(**student_data)
                students.append(student)
                # Cache the student
                self._cache[student.id] = student
            
            return students
            
        except Exception as e:
            logger.error(f"Failed to get active students: {str(e)}")
            raise DatabaseError(f"Failed to get active students: {str(e)}")
    
    async def batch_update_students(self, updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple students."""
        results = {}
        
        for update in updates:
            student_id = update['student_id']
            try:
                result = await self.update(student_id, **update)
                results[student_id] = result is not None
            except Exception as e:
                logger.error(f"Failed to update student {student_id}: {str(e)}")
                results[student_id] = False
        
        return results
    
    async def batch_delete_students(self, student_ids: List[str]) -> Dict[str, bool]:
        """Delete multiple students."""
        results = {}
        
        for student_id in student_ids:
            try:
                result = await self.delete(student_id)
                results[student_id] = result
            except Exception as e:
                logger.error(f"Failed to delete student {student_id}: {str(e)}")
                results[student_id] = False
        
        return results
    
    # Private helper methods
    
    async def _validate_student_data(self, data: Dict[str, Any]) -> None:
        """Validate student data."""
        # Check required fields
        required_fields = ['name', 'email', 'student_id']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate email format
        if '@' not in data.get('email', ''):
            raise ValidationError("Invalid email format")
        
        # Validate student ID uniqueness
        existing_student = await self.get_by_student_id(data['student_id'])
        if existing_student:
            raise ConflictError(f"Student with ID '{data['student_id']}' already exists")
        
        # Validate email uniqueness
        existing_email = await self.get_by_email(data['email'])
        if existing_email:
            raise ConflictError(f"Student with email '{data['email']}' already exists")
    
    async def _validate_student_update(self, data: Dict[str, Any]) -> None:
        """Validate student update data."""
        # Check if email is being updated and conflicts exist
        if 'email' in data and data['email']:
            existing_email = await self.get_by_email(data['email'])
            if existing_email:
                raise ConflictError(f"Student with email '{data['email']}' already exists")
        
        # Validate student ID if being updated
        if 'student_id' in data and data['student_id']:
            existing_student = await self.get_by_student_id(data['student_id'])
            if existing_student:
                raise ConflictError(f"Student with ID '{data['student_id']}' already exists")
    
    async def _calculate_gpa(self, marks: List[Any]) -> float:
        """Calculate GPA from marks."""
        if not marks:
            return 0.0
        
        total_points = 0
        for mark in marks:
            # Convert score to GPA points (simple 4.0 scale)
            if mark.score >= 90:
                total_points += 4.0
            elif mark.score >= 80:
                total_points += 3.0
            elif mark.score >= 70:
                total_points += 2.0
            elif mark.score >= 60:
                total_points += 1.0
            else:
                total_points += 0.0
        
        return round(total_points / len(marks), 2)
    
    # Abstract method implementations
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> QueryResult:
        """List all students with pagination."""
        try:
            mock_db = self._get_mock_db()
            students_data = await mock_db.find_many(self._collection_name, {}, limit=limit, skip=offset)
            
            students = []
            for student_data in students_data:
                student = StudentResponse(**student_data)
                students.append(student)
                # Cache the student
                self._cache[student.id] = student
            
            return QueryResult(success=True, data=students)
            
        except Exception as e:
            logger.error(f"Failed to list all students: {str(e)}")
            return QueryResult(success=False, error=f"Failed to list all students: {str(e)}")
    
    async def search(self, search_term: str, limit: int = 100, offset: int = 0) -> QueryResult:
        """Search students by name, email, or student ID."""
        try:
            # Search query (simplified for mock database)
            # Convert MongoDB regex to simple string matching for mock
            query = {
                "name": search_term,
                "email": search_term,
                "student_id": search_term
            }
            
            mock_db = self._get_mock_db()
            students_data = await mock_db.find_many(self._collection_name, query, limit=limit, skip=offset)
            
            students = []
            for student_data in students_data:
                student = StudentResponse(**student_data)
                students.append(student)
                # Cache the student
                self._cache[student.id] = student
            
            return QueryResult(success=True, data=students)
            
        except Exception as e:
            logger.error(f"Failed to search students: {str(e)}")
            return QueryResult(success=False, error=f"Failed to search students: {str(e)}")
    
    async def filter(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> QueryResult:
        """Filter students by criteria."""
        try:
            mock_db = self._get_mock_db()
            students_data = await mock_db.find_many(self._collection_name, filters, limit=limit, skip=offset)
            
            students = []
            for student_data in students_data:
                student = StudentResponse(**student_data)
                students.append(student)
                # Cache the student
                self._cache[student.id] = student
            
            return QueryResult(success=True, data=students)
            
        except Exception as e:
            logger.error(f"Failed to filter students: {str(e)}")
            return QueryResult(success=False, error=f"Failed to filter students: {str(e)}")