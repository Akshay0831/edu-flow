"""
Teacher Repository

This module provides data access operations for teacher entities.
It implements the repository pattern with database abstraction.

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from uuid import uuid4
from datetime import datetime, date

from src.core.logging import get_logger
from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.infrastructure.repositories.base_repository import BaseRepository, QueryResult
from src.models.user import UserCreate, UserUpdate, User

logger = get_logger(__name__)


class TeacherRepository(BaseRepository):
    """Teacher repository with CRUD operations and data access."""
    
    def __init__(self):
        super().__init__("teachers")
        self._cache = {}
    
    async def create(self, entity_data: Dict[str, Any]) -> QueryResult:
        """Create a new teacher record."""
        try:
            # Validate teacher data
            await self._validate_teacher_data(entity_data)
            
            # Generate ID if not provided
            if 'id' not in entity_data:
                entity_data['id'] = str(uuid4())
            
            # Add created timestamp
            entity_data['created_at'] = datetime.utcnow().isoformat()
            entity_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Create teacher
            mock_db = self._get_mock_db()
            teacher_id = await mock_db.insert_one(self._collection_name, entity_data)
            
            # Cache the teacher
            self._cache[teacher_id] = entity_data
            
            return QueryResult(success=True, data=User(**entity_data))
            
        except Exception as e:
            logger.error(f"Failed to create teacher: {str(e)}")
            return QueryResult(success=False, error=f"Failed to create teacher: {str(e)}")
    
    async def get_by_id(self, entity_id: str) -> QueryResult:
        """Get a teacher by ID."""
        try:
            # Check cache first
            if entity_id in self._cache:
                return QueryResult(success=True, data=User(**self._cache[entity_id]))
            
            # Get teacher from database
            mock_db = self._get_mock_db()
            teacher = await mock_db.find_one(self._collection_name, {"id": entity_id})
            
            if teacher:
                # Cache the teacher
                self._cache[entity_id] = teacher
                return QueryResult(success=True, data=User(**teacher))
            
            return QueryResult(success=True, data=None)
            
        except Exception as e:
            logger.error(f"Failed to get teacher by ID {entity_id}: {str(e)}")
            return QueryResult(success=False, error=f"Failed to get teacher by ID {entity_id}: {str(e)}")
    
    async def update(self, entity_id: str, entity_data: Dict[str, Any]) -> QueryResult:
        """Update a teacher by ID."""
        try:
            # Get existing teacher
            existing_result = await self.get_by_id(entity_id)
            if not existing_result.success:
                return existing_result
            if not existing_result.data:
                return QueryResult(success=True, data=None)
            
            # Validate update data
            await self._validate_teacher_update(entity_data)
            
            # Add updated timestamp
            entity_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update teacher
            mock_db = self._get_mock_db()
            result = await mock_db.update_one(self._collection_name, {"id": entity_id}, entity_data)
            
            if result:
                # Update cache
                self._cache[entity_id] = entity_data
                return QueryResult(success=True, data=User(**entity_data))
            
            return QueryResult(success=True, data=None)
            
        except Exception as e:
            logger.error(f"Failed to update teacher {entity_id}: {str(e)}")
            return QueryResult(success=False, error=f"Failed to update teacher {entity_id}: {str(e)}")
    
    async def delete(self, entity_id: str) -> QueryResult:
        """Delete a teacher by ID."""
        try:
            # Get existing teacher
            existing_result = await self.get_by_id(entity_id)
            if not existing_result.success:
                return existing_result
            if not existing_result.data:
                return QueryResult(success=True, data=True)
            
            # Delete teacher
            mock_db = self._get_mock_db()
            result = await mock_db.delete_one(self._collection_name, {"id": entity_id})
            
            # Remove from cache
            if entity_id in self._cache:
                del self._cache[entity_id]
            
            return QueryResult(success=True, data=result)
            
        except Exception as e:
            logger.error(f"Failed to delete teacher {entity_id}: {str(e)}")
            return QueryResult(success=False, error=f"Failed to delete teacher {entity_id}: {str(e)}")
    
    async def update(self, id: str, **data) -> Optional[User]:
        """Update a teacher by ID."""
        try:
            # Get existing teacher
            existing_teacher = await self.get_by_id(id)
            if not existing_teacher:
                return None
            
            # Validate update data
            await self._validate_teacher_update(data)
            
            # Add updated timestamp
            data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update teacher
            updated_teacher = await self._update(self._collection_name, id, data)
            
            if updated_teacher:
                # Update cache
                self._cache[id] = updated_teacher
                return User(**updated_teacher)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to update teacher {id}: {str(e)}")
            raise DatabaseError(f"Failed to update teacher {id}: {str(e)}")
    
    async def delete(self, id: str) -> bool:
        """Delete a teacher by ID."""
        try:
            # Get existing teacher
            existing_teacher = await self.get_by_id(id)
            if not existing_teacher:
                return False
            
            # Delete teacher
            result = await self._delete(self._collection_name, id)
            
            # Remove from cache
            if id in self._cache:
                del self._cache[id]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete teacher {id}: {str(e)}")
            raise DatabaseError(f"Failed to delete teacher {id}: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all teachers."""
        try:
            teachers_data = await self._get_all(self._collection_name, skip, limit)
            
            teachers = []
            for teacher_data in teachers_data:
                teacher = UserResponse(**teacher_data)
                teachers.append(teacher)
                # Cache the teacher
                self._cache[teacher.id] = teacher
            
            return teachers
            
        except Exception as e:
            logger.error(f"Failed to get all teachers: {str(e)}")
            raise DatabaseError(f"Failed to get all teachers: {str(e)}")
    
    async def search_teachers(self, search_term: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search teachers by name, email, or teacher ID."""
        try:
            # Search query
            query = {
                "$or": [
                    {"name": {"$regex": search_term, "$options": "i"}},
                    {"email": {"$regex": search_term, "$options": "i"}},
                    {"teacher_id": {"$regex": search_term, "$options": "i"}}
                ]
            }
            
            teachers_data = await self._search(self._collection_name, query, skip, limit)
            
            teachers = []
            for teacher_data in teachers_data:
                teacher = UserResponse(**teacher_data)
                teachers.append(teacher)
                # Cache the teacher
                self._cache[teacher.id] = teacher
            
            return teachers
            
        except Exception as e:
            logger.error(f"Failed to search teachers: {str(e)}")
            raise DatabaseError(f"Failed to search teachers: {str(e)}")
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a teacher by email."""
        try:
            # Query by email
            query = {"email": email}
            teacher_data = await self._find_one(self._collection_name, query)
            
            if teacher_data:
                teacher = UserResponse(**teacher_data)
                # Cache the teacher
                self._cache[teacher.id] = teacher
                return teacher
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get teacher by email {email}: {str(e)}")
            raise DatabaseError(f"Failed to get teacher by email {email}: {str(e)}")
    
    async def get_by_teacher_id(self, teacher_id: str) -> Optional[User]:
        """Get a teacher by teacher ID."""
        try:
            # Query by teacher ID
            query = {"teacher_id": teacher_id}
            teacher_data = await self._find_one(self._collection_name, query)
            
            if teacher_data:
                teacher = UserResponse(**teacher_data)
                # Cache the teacher
                self._cache[teacher.id] = teacher
                return teacher
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get teacher by teacher ID {teacher_id}: {str(e)}")
            raise DatabaseError(f"Failed to get teacher by teacher ID {teacher_id}: {str(e)}")
    
    async def get_teachers_by_department(self, department_id: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get teachers by department."""
        try:
            # Query by department
            query = {"department_id": department_id}
            teachers_data = await self._search(self._collection_name, query, skip, limit)
            
            teachers = []
            for teacher_data in teachers_data:
                teacher = UserResponse(**teacher_data)
                teachers.append(teacher)
                # Cache the teacher
                self._cache[teacher.id] = teacher
            
            return teachers
            
        except Exception as e:
            logger.error(f"Failed to get teachers by department {department_id}: {str(e)}")
            raise DatabaseError(f"Failed to get teachers by department {department_id}: {str(e)}")
    
    async def get_active_teachers(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active teachers."""
        try:
            # Query for active teachers
            query = {"status": "active"}
            teachers_data = await self._search(self._collection_name, query, skip, limit)
            
            teachers = []
            for teacher_data in teachers_data:
                teacher = UserResponse(**teacher_data)
                teachers.append(teacher)
                # Cache the teacher
                self._cache[teacher.id] = teacher
            
            return teachers
            
        except Exception as e:
            logger.error(f"Failed to get active teachers: {str(e)}")
            raise DatabaseError(f"Failed to get active teachers: {str(e)}")
    
    async def batch_update_teachers(self, updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple teachers."""
        results = {}
        
        for update in updates:
            teacher_id = update['teacher_id']
            try:
                result = await self.update(teacher_id, **update)
                results[teacher_id] = result is not None
            except Exception as e:
                logger.error(f"Failed to update teacher {teacher_id}: {str(e)}")
                results[teacher_id] = False
        
        return results
    
    async def batch_delete_teachers(self, teacher_ids: List[str]) -> Dict[str, bool]:
        """Delete multiple teachers."""
        results = {}
        
        for teacher_id in teacher_ids:
            try:
                result = await self.delete(teacher_id)
                results[teacher_id] = result
            except Exception as e:
                logger.error(f"Failed to delete teacher {teacher_id}: {str(e)}")
                results[teacher_id] = False
        
        return results
    
    # Private helper methods
    
    async def _validate_teacher_data(self, data: Dict[str, Any]) -> None:
        """Validate teacher data."""
        # Check required fields
        required_fields = ['name', 'email', 'teacher_id']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate email format
        if '@' not in data.get('email', ''):
            raise ValidationError("Invalid email format")
        
        # Validate teacher ID uniqueness
        existing_teacher = await self.get_by_teacher_id(data['teacher_id'])
        if existing_teacher:
            raise ConflictError(f"Teacher with ID '{data['teacher_id']}' already exists")
        
        # Validate email uniqueness
        existing_email = await self.get_by_email(data['email'])
        if existing_email:
            raise ConflictError(f"Teacher with email '{data['email']}' already exists")
    
    async def _validate_teacher_update(self, data: Dict[str, Any]) -> None:
        """Validate teacher update data."""
        # Check if email is being updated and conflicts exist
        if 'email' in data and data['email']:
            existing_email = await self.get_by_email(data['email'])
            if existing_email:
                raise ConflictError(f"Teacher with email '{data['email']}' already exists")
        
        # Validate teacher ID if being updated
        if 'teacher_id' in data and data['teacher_id']:
            existing_teacher = await self.get_by_teacher_id(data['teacher_id'])
            if existing_teacher:
                raise ConflictError(f"Teacher with ID '{data['teacher_id']}' already exists")
    
    # Abstract method implementations
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> QueryResult:
        """List all teachers with pagination."""
        try:
            mock_db = self._get_mock_db()
            teachers_data = await mock_db.find_many(self._collection_name, {}, limit=limit, skip=offset)
            
            teachers = []
            for teacher_data in teachers_data:
                teacher = UserResponse(**teacher_data)
                teachers.append(teacher)
                # Cache the teacher
                self._cache[teacher.id] = teacher
            
            return QueryResult(success=True, data=teachers)
            
        except Exception as e:
            logger.error(f"Failed to list all teachers: {str(e)}")
            return QueryResult(success=False, error=f"Failed to list all teachers: {str(e)}")
    
    async def search(self, search_term: str, limit: int = 100, offset: int = 0) -> QueryResult:
        """Search teachers by name, email, or teacher ID."""
        try:
            # Search query (simplified for mock database)
            mock_db = self._get_mock_db()
            teachers_data = await mock_db.find_many(self._collection_name, {"name": search_term}, limit=limit, skip=offset)
            
            teachers = []
            for teacher_data in teachers_data:
                teacher = UserResponse(**teacher_data)
                teachers.append(teacher)
                # Cache the teacher
                self._cache[teacher.id] = teacher
            
            return QueryResult(success=True, data=teachers)
            
        except Exception as e:
            logger.error(f"Failed to search teachers: {str(e)}")
            return QueryResult(success=False, error=f"Failed to search teachers: {str(e)}")
    
    async def filter(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> QueryResult:
        """Filter teachers by criteria."""
        try:
            mock_db = self._get_mock_db()
            teachers_data = await mock_db.find_many(self._collection_name, filters, limit=limit, skip=offset)
            
            teachers = []
            for teacher_data in teachers_data:
                teacher = UserResponse(**teacher_data)
                teachers.append(teacher)
                # Cache the teacher
                self._cache[teacher.id] = teacher
            
            return QueryResult(success=True, data=teachers)
            
        except Exception as e:
            logger.error(f"Failed to filter teachers: {str(e)}")
            return QueryResult(success=False, error=f"Failed to filter teachers: {str(e)}")