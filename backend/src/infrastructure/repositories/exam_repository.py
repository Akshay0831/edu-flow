"""
Exam Repository

This module provides data access operations for exam entities.
It implements the repository pattern with database abstraction.

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from uuid import uuid4
from datetime import datetime, date, time
import json

from core.logging import get_logger
from core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from infrastructure.repositories.base_repository import BaseRepository
from models.exam import ExamCreate, ExamUpdate, ExamResponse, ExamStats

logger = get_logger(__name__)


class ExamRepository(BaseRepository):
    """Exam repository with CRUD operations and data access."""
    
    def __init__(self):
        super().__init__()
        self._collection_name = "exams"
        self._cache = {}
    
    async def create(self, **data) -> ExamResponse:
        """Create a new exam record."""
        try:
            # Validate exam data
            await self._validate_exam_data(data)
            
            # Generate ID if not provided
            if 'id' not in data:
                data['id'] = str(uuid4())
            
            # Add created timestamp
            data['created_at'] = datetime.utcnow().isoformat()
            data['updated_at'] = datetime.utcnow().isoformat()
            
            # Convert date/time objects to strings if needed
            if 'exam_date' in data and isinstance(data['exam_date'], date):
                data['exam_date'] = data['exam_date'].isoformat()
            if 'start_time' in data and isinstance(data['start_time'], time):
                data['start_time'] = data['start_time'].isoformat()
            if 'end_time' in data and isinstance(data['end_time'], time):
                data['end_time'] = data['end_time'].isoformat()
            
            # Create exam
            exam = await self._create(self._collection_name, data)
            
            # Cache the exam
            self._cache[exam.id] = exam
            
            return ExamResponse(**exam)
            
        except Exception as e:
            logger.error(f"Failed to create exam: {str(e)}")
            raise DatabaseError(f"Failed to create exam: {str(e)}")
    
    async def get_by_id(self, id: str) -> Optional[ExamResponse]:
        """Get an exam by ID."""
        try:
            # Check cache first
            if id in self._cache:
                return ExamResponse(**self._cache[id])
            
            # Get exam from database
            exam = await self._get_by_id(self._collection_name, id)
            
            if exam:
                # Convert date strings back to objects if needed
                exam = self._convert_exam_data(exam)
                # Cache the exam
                self._cache[id] = exam
                return ExamResponse(**exam)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get exam by ID {id}: {str(e)}")
            raise DatabaseError(f"Failed to get exam by ID {id}: {str(e)}")
    
    async def update(self, id: str, **data) -> Optional[ExamResponse]:
        """Update an exam by ID."""
        try:
            # Get existing exam
            existing_exam = await self.get_by_id(id)
            if not existing_exam:
                return None
            
            # Validate update data
            await self._validate_exam_update(data)
            
            # Add updated timestamp
            data['updated_at'] = datetime.utcnow().isoformat()
            
            # Convert date/time objects to strings if needed
            if 'exam_date' in data and isinstance(data['exam_date'], date):
                data['exam_date'] = data['exam_date'].isoformat()
            if 'start_time' in data and isinstance(data['start_time'], time):
                data['start_time'] = data['start_time'].isoformat()
            if 'end_time' in data and isinstance(data['end_time'], time):
                data['end_time'] = data['end_time'].isoformat()
            
            # Update exam
            updated_exam = await self._update(self._collection_name, id, data)
            
            if updated_exam:
                # Convert date strings back to objects if needed
                updated_exam = self._convert_exam_data(updated_exam)
                # Update cache
                self._cache[id] = updated_exam
                return ExamResponse(**updated_exam)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to update exam {id}: {str(e)}")
            raise DatabaseError(f"Failed to update exam {id}: {str(e)}")
    
    async def delete(self, id: str) -> bool:
        """Delete an exam by ID."""
        try:
            # Get existing exam
            existing_exam = await self.get_by_id(id)
            if not existing_exam:
                return False
            
            # Delete exam
            result = await self._delete(self._collection_name, id)
            
            # Remove from cache
            if id in self._cache:
                del self._cache[id]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete exam {id}: {str(e)}")
            raise DatabaseError(f"Failed to delete exam {id}: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ExamResponse]:
        """Get all exams."""
        try:
            exams_data = await self._get_all(self._collection_name, skip, limit)
            
            exams = []
            for exam_data in exams_data:
                exam = self._convert_exam_data(exam_data)
                exam_obj = ExamResponse(**exam)
                exams.append(exam_obj)
                # Cache the exam
                self._cache[exam_obj.id] = exam
            
            return exams
            
        except Exception as e:
            logger.error(f"Failed to get all exams: {str(e)}")
            raise DatabaseError(f"Failed to get all exams: {str(e)}")
    
    async def search_exams(self, search_term: str, skip: int = 0, limit: int = 100) -> List[ExamResponse]:
        """Search exams by name, subject, or exam code."""
        try:
            # Search query
            query = {
                "$or": [
                    {"exam_name": {"$regex": search_term, "$options": "i"}},
                    {"subject": {"$regex": search_term, "$options": "i"}},
                    {"exam_code": {"$regex": search_term, "$options": "i"}}
                ]
            }
            
            exams_data = await self._search(self._collection_name, query, skip, limit)
            
            exams = []
            for exam_data in exams_data:
                exam = self._convert_exam_data(exam_data)
                exam_obj = ExamResponse(**exam)
                exams.append(exam_obj)
                # Cache the exam
                self._cache[exam_obj.id] = exam
            
            return exams
            
        except Exception as e:
            logger.error(f"Failed to search exams: {str(e)}")
            raise DatabaseError(f"Failed to search exams: {str(e)}")
    
    async def get_by_subject(self, subject: str, skip: int = 0, limit: int = 100) -> List[ExamResponse]:
        """Get exams by subject."""
        try:
            # Query by subject
            query = {"subject": {"$regex": subject, "$options": "i"}}
            exams_data = await self._search(self._collection_name, query, skip, limit)
            
            exams = []
            for exam_data in exams_data:
                exam = self._convert_exam_data(exam_data)
                exam_obj = ExamResponse(**exam)
                exams.append(exam_obj)
                # Cache the exam
                self._cache[exam_obj.id] = exam
            
            return exams
            
        except Exception as e:
            logger.error(f"Failed to get exams by subject {subject}: {str(e)}")
            raise DatabaseError(f"Failed to get exams by subject {subject}: {str(e)}")
    
    async def get_by_department(self, department_id: str, skip: int = 0, limit: int = 100) -> List[ExamResponse]:
        """Get exams by department."""
        try:
            # Query by department
            query = {"department_id": department_id}
            exams_data = await self._search(self._collection_name, query, skip, limit)
            
            exams = []
            for exam_data in exams_data:
                exam = self._convert_exam_data(exam_data)
                exam_obj = ExamResponse(**exam)
                exams.append(exam_obj)
                # Cache the exam
                self._cache[exam_obj.id] = exam
            
            return exams
            
        except Exception as e:
            logger.error(f"Failed to get exams by department {department_id}: {str(e)}")
            raise DatabaseError(f"Failed to get exams by department {department_id}: {str(e)}")
    
    async def get_upcoming_exams(self, department_id: str = None, skip: int = 0, limit: int = 100) -> List[ExamResponse]:
        """Get upcoming exams."""
        try:
            today = datetime.utcnow().date().isoformat()
            
            # Query for future exams
            query = {"exam_date": {"$gt": today}}
            
            # Add department filter if provided
            if department_id:
                query["department_id"] = department_id
            
            exams_data = await self._search(self._collection_name, query, skip, limit)
            
            exams = []
            for exam_data in exams_data:
                exam = self._convert_exam_data(exam_data)
                exam_obj = ExamResponse(**exam)
                exams.append(exam_obj)
                # Cache the exam
                self._cache[exam_obj.id] = exam
            
            # Sort by date
            exams.sort(key=lambda x: x.exam_date)
            
            return exams
            
        except Exception as e:
            logger.error(f"Failed to get upcoming exams: {str(e)}")
            raise DatabaseError(f"Failed to get upcoming exams: {str(e)}")
    
    async def get_exam_stats(self, exam_id: str) -> ExamStats:
        """Get exam statistics."""
        try:
            # Get exam
            exam = await self.get_by_id(exam_id)
            if not exam:
                raise NotFoundError(f"Exam not found with ID: {exam_id}")
            
            # Get students enrolled in the exam
            from infrastructure.repositories.mark_repository import MarkRepository
            mark_repo = MarkRepository()
            marks = await mark_repo.get_marks_by_exam(exam_id)
            
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
            
            # Create stats object
            stats = ExamStats(
                exam_id=exam_id,
                exam_name=exam.exam_name,
                subject=exam.subject,
                total_students=total_students,
                average_score=round(average_score, 2),
                max_score=max_score,
                min_score=min_score,
                pass_count=pass_count,
                pass_percentage=round(pass_percentage, 2),
                exam_date=exam.exam_date
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get exam stats for {exam_id}: {str(e)}")
            raise DatabaseError(f"Failed to get exam stats for {exam_id}: {str(e)}")
    
    async def batch_update_exams(self, updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple exams."""
        results = {}
        
        for update in updates:
            exam_id = update['exam_id']
            try:
                result = await self.update(exam_id, **update)
                results[exam_id] = result is not None
            except Exception as e:
                logger.error(f"Failed to update exam {exam_id}: {str(e)}")
                results[exam_id] = False
        
        return results
    
    async def batch_delete_exams(self, exam_ids: List[str]) -> Dict[str, bool]:
        """Delete multiple exams."""
        results = {}
        
        for exam_id in exam_ids:
            try:
                result = await self.delete(exam_id)
                results[exam_id] = result
            except Exception as e:
                logger.error(f"Failed to delete exam {exam_id}: {str(e)}")
                results[exam_id] = False
        
        return results
    
    # Private helper methods
    
    def _convert_exam_data(self, exam_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert exam data from database format."""
        # Parse date and time strings
        if 'exam_date' in exam_data and exam_data['exam_date']:
            try:
                exam_data['exam_date'] = exam_data['exam_date']
            except:
                pass  # Keep as string if parsing fails
        
        if 'start_time' in exam_data and exam_data['start_time']:
            try:
                exam_data['start_time'] = exam_data['start_time']
            except:
                pass  # Keep as string if parsing fails
        
        if 'end_time' in exam_data and exam_data['end_time']:
            try:
                exam_data['end_time'] = exam_data['end_time']
            except:
                pass  # Keep as string if parsing fails
        
        return exam_data
    
    async def _validate_exam_data(self, data: Dict[str, Any]) -> None:
        """Validate exam data."""
        # Check required fields
        required_fields = ['exam_name', 'subject', 'exam_date', 'start_time', 'end_time', 'duration', 'total_marks']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate exam date is not in the past
        if data.get('exam_date'):
            exam_date = datetime.fromisoformat(data['exam_date']).date()
            if exam_date < datetime.utcnow().date():
                raise ValidationError("Exam date cannot be in the past")
        
        # Validate start time is before end time
        if data.get('start_time') and data.get('end_time'):
            start_time = datetime.fromisoformat(data['start_time']).time()
            end_time = datetime.fromisoformat(data['end_time']).time()
            if start_time >= end_time:
                raise ValidationError("Start time must be before end time")
        
        # Validate duration matches time difference
        if data.get('start_time') and data.get('end_time') and data.get('duration'):
            start_time = datetime.fromisoformat(data['start_time'])
            end_time = datetime.fromisoformat(data['end_time'])
            calculated_duration = (end_time - start_time).total_seconds() / 60  # in minutes
            if calculated_duration != data['duration']:
                raise ValidationError(f"Duration {data['duration']} minutes does not match time difference")
        
        # Validate total_marks is positive
        if data.get('total_marks', 0) <= 0:
            raise ValidationError("Total marks must be positive")
        
        # Validate exam code uniqueness if provided
        if 'exam_code' in data and data['exam_code']:
            existing_exam = await self.get_by_exam_code(data['exam_code'])
            if existing_exam:
                raise ConflictError(f"Exam with code '{data['exam_code']}' already exists")
    
    async def _validate_exam_update(self, data: Dict[str, Any]) -> None:
        """Validate exam update data."""
        # Validate exam code uniqueness if being updated
        if 'exam_code' in data and data['exam_code']:
            existing_exam = await self.get_by_exam_code(data['exam_code'])
            if existing_exam:
                raise ConflictError(f"Exam with code '{data['exam_code']}' already exists")
        
        # Validate date constraints if being updated
        if 'exam_date' in data and data['exam_date']:
            exam_date = datetime.fromisoformat(data['exam_date']).date()
            if exam_date < datetime.utcnow().date():
                raise ValidationError("Exam date cannot be in the past")
        
        # Validate time constraints if being updated
        if 'start_time' in data and data['start_time'] and 'end_time' in data and data['end_time']:
            start_time = datetime.fromisoformat(data['start_time']).time()
            end_time = datetime.fromisoformat(data['end_time']).time()
            if start_time >= end_time:
                raise ValidationError("Start time must be before end time")
    
    async def get_by_exam_code(self, exam_code: str) -> Optional[ExamResponse]:
        """Get an exam by exam code."""
        try:
            # Query by exam code
            query = {"exam_code": exam_code}
            exam_data = await self._find_one(self._collection_name, query)
            
            if exam_data:
                exam = self._convert_exam_data(exam_data)
                exam_obj = ExamResponse(**exam)
                # Cache the exam
                self._cache[exam_obj.id] = exam
                return exam_obj
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get exam by code {exam_code}: {str(e)}")
            raise DatabaseError(f"Failed to get exam by code {exam_code}: {str(e)}")