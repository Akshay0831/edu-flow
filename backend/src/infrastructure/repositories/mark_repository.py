"""
Marks Repository

This module provides the repository layer for Marks entity operations.
It handles all database interactions related to marks including CRUD operations,
grade calculations, performance tracking, SEE prediction, and assessment management.

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Type
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum
import json

from src.core.exceptions import DatabaseError, NotFoundError, ValidationError, ConflictError
from src.core.logging import get_logger
from src.infrastructure.repositories.base_repository import BaseRepository, QueryResult

logger = get_logger(__name__)


class AssessmentType(Enum):
    """Assessment type enumeration."""
    INTERNAL_ASSESSMENT = "internal_assessment"
    SEMESTER_EXAMINATION = "semester_examination"
    CONTINUOUS_EVALUATION = "continuous_evaluation"
    PROJECT = "project"
    PRACTICAL = "practical"


class GradeStatus(Enum):
    """Grade status enumeration."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    GRADED = "graded"
    VERIFIED = "verified"
    FINALIZED = "finalized"


class MarkFilter(Enum):
    """Marks filter types."""
    BY_STUDENT = "student"
    BY_CLASS = "class"
    BY_SUBJECT = "subject"
    BY_SEMESTER = "semester"
    BY_ASSESSMENT = "assessment"
    BY_GRADE = "grade"
    BY_STATUS = "status"
    BY_DATE_RANGE = "date_range"
    BY_GPA_RANGE = "gpa_range"


class SortOrder(Enum):
    """Sort order for marks queries."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class MarkQuery:
    """Structured query for marks operations."""
    filters: Dict[str, Any] = None
    sort_by: str = None
    sort_order: SortOrder = SortOrder.ASC
    limit: int = 100
    offset: int = 0
    search_term: str = None


class MarkRepository(BaseRepository):
    """
    Repository for Marks entity operations.
    
    Handles CRUD operations, grade calculations, performance tracking, 
    SEE prediction, and assessment management.
    """
    
    def __init__(self, database_manager):
        """
        Initialize the marks repository.
        
        Args:
            database_manager: Database connection manager instance
        """
        super().__init__("marks")
        self.db = database_manager
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        
    async def create(self, mark_data: Dict[str, Any]) -> QueryResult:
        """
        Create a new marks record in the database.
        
        Args:
            mark_data: Marks data including all required fields
            
        Returns:
            QueryResult with created marks record
        """
        start_time = datetime.now()
        
        try:
            # Validate marks data
            if not self._validate_entity_data(mark_data):
                return self._create_result(error="Invalid marks data")
            
            # Validate required fields
            required_fields = ['student_id', 'class_id', 'subject_id', 'assessment_type', 'marks_obtained', 'max_marks']
            for field in required_fields:
                if field not in mark_data:
                    return self._create_result(error=f"Missing required field: {field}")
            
            # Set default values for optional fields
            mark_data.setdefault('created_at', datetime.now())
            mark_data.setdefault('updated_at', datetime.now())
            mark_data.setdefault('grade_letter', '')
            mark_data.setdefault('grade_points', 0.0)
            mark_data.setdefault('percentage', 0.0)
            mark_data.setdefault('status', GradeStatus.PENDING.value)
            mark_data.setdefault('comments', '')
            mark_data.setdefault('metadata', {})
            
            # Convert complex fields to JSON strings for storage
            if 'assessment_marks' in mark_data:
                mark_data['assessment_marks'] = json.dumps(mark_data['assessment_marks'])
            if 'metadata' in mark_data:
                mark_data['metadata'] = json.dumps(mark_data['metadata'])
            
            # Calculate grade information
            grade_result = self._calculate_grade(mark_data)
            if not grade_result.success:
                return grade_result
            
            # Update mark_data with calculated grade
            mark_data.update(grade_result.data)
            
            # Insert into database
            query = """
            INSERT INTO marks 
            (student_id, class_id, subject_id, assessment_type, marks_obtained, max_marks,
             percentage, grade_letter, grade_points, status, comments, metadata, 
             created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING *
            """
            
            values = [
                mark_data['student_id'],
                mark_data['class_id'],
                mark_data['subject_id'],
                mark_data['assessment_type'],
                mark_data['marks_obtained'],
                mark_data['max_marks'],
                mark_data.get('percentage', 0.0),
                mark_data.get('grade_letter', ''),
                mark_data.get('grade_points', 0.0),
                mark_data.get('status'),
                mark_data.get('comments', ''),
                mark_data.get('metadata'),
                mark_data['created_at'],
                mark_data['updated_at']
            ]
            
            result = await self.db.execute_query(query, values)
            
            if result.success and result.data:
                # Parse JSON fields back to dict
                created_mark = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.CREATE,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=created_mark,
                    query_time=query_time
                )
            else:
                return self._create_result(error="Failed to create marks record")
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error creating marks record: {str(e)}")
            return self._create_result(
                error=f"Database error creating marks record: {str(e)}",
                query_time=query_time
            )
    
    async def get_by_id(self, mark_id: str) -> QueryResult:
        """
        Get a marks record by its ID.
        
        Args:
            mark_id: Unique identifier for the marks record
            
        Returns:
            QueryResult with the marks record data
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(mark_id):
                return self._create_result(error="Invalid marks ID")
            
            query = "SELECT * FROM marks WHERE id = $1"
            result = await self.db.execute_query(query, [mark_id])
            
            if result.success and result.data:
                mark_record = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=mark_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=mark_record,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=mark_id,
                    duration=query_time,
                    success=False
                )
                return self._create_result(
                    error="Marks record not found",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting marks record {mark_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting marks record: {str(e)}",
                query_time=query_time
            )
    
    async def update(self, mark_id: str, mark_data: Dict[str, Any]) -> QueryResult:
        """
        Update an existing marks record.
        
        Args:
            mark_id: Unique identifier for the marks record
            mark_data: Updated data for the marks record
            
        Returns:
            QueryResult with the updated marks record
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(mark_id):
                return self._create_result(error="Invalid marks ID")
            
            if not self._validate_entity_data(mark_data):
                return self._create_result(error="Invalid marks data")
            
            # Check if marks record exists
            existing_result = await self.get_by_id(mark_id)
            if not existing_result.success:
                return existing_result
            
            existing_mark = existing_result.data
            
            # Recalculate grade if marks_obtained or max_marks changed
            if 'marks_obtained' in mark_data or 'max_marks' in mark_data:
                grade_result = self._calculate_grade(mark_data)
                if not grade_result.success:
                    return grade_result
                
                # Update mark_data with calculated grade
                mark_data.update(grade_result.data)
            
            # Convert complex fields to JSON strings
            if 'assessment_marks' in mark_data:
                mark_data['assessment_marks'] = json.dumps(mark_data['assessment_marks'])
            if 'metadata' in mark_data:
                mark_data['metadata'] = json.dumps(mark_data['metadata'])
            
            # Update timestamp
            mark_data['updated_at'] = datetime.now()
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            for field, value in mark_data.items():
                if field != 'id':
                    update_fields.append(f"{field} = ${len(values) + 1}")
                    values.append(value)
            
            values.append(mark_id)
            query = f"""
            UPDATE marks 
            SET {', '.join(update_fields)} 
            WHERE id = ${len(values)}
            RETURNING *
            """
            
            result = await self.db.execute_query(query, values)
            
            if result.success and result.data:
                updated_mark = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.UPDATE,
                    entity_id=mark_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=updated_mark,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to update marks record",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error updating marks record {mark_id}: {str(e)}")
            return self._create_result(
                error=f"Database error updating marks record: {str(e)}",
                query_time=query_time
            )
    
    async def delete(self, mark_id: str) -> QueryResult:
        """
        Delete a marks record by its ID.
        
        Args:
            mark_id: Unique identifier for the marks record
            
        Returns:
            QueryResult with deletion status
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(mark_id):
                return self._create_result(error="Invalid marks ID")
            
            # Check if marks record exists
            existing_result = await self.get_by_id(mark_id)
            if not existing_result.success:
                return existing_result
            
            # Delete the marks record
            query = "DELETE FROM marks WHERE id = $1"
            result = await self.db.execute_query(query, [mark_id])
            
            if result.success:
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.DELETE,
                    entity_id=mark_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data={"deleted": True, "mark_id": mark_id},
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to delete marks record",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error deleting marks record {mark_id}: {str(e)}")
            return self._create_result(
                error=f"Database error deleting marks record: {str(e)}",
                query_time=query_time
            )
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        List all marks records with pagination.
        
        Args:
            limit: Maximum number of marks records to return
            offset: Number of marks records to skip
            
        Returns:
            QueryResult with list of marks records
        """
        start_time = datetime.now()
        
        try:
            query = "SELECT * FROM marks ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            result = await self.db.execute_query(query, [limit, offset])
            
            if result.success:
                marks = [self._parse_json_fields(mark) for mark in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = "SELECT COUNT(*) FROM marks"
                count_result = await self.db.execute_query(count_query)
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.LIST,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=marks,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to list marks records",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error listing marks records: {str(e)}")
            return self._create_result(
                error=f"Database error listing marks records: {str(e)}",
                query_time=query_time
            )
    
    async def search(self, search_term: str, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Search marks records by term.
        
        Args:
            search_term: Search term for filtering
            limit: Maximum number of marks records to return
            offset: Number of marks records to skip
            
        Returns:
            QueryResult with search results
        """
        start_time = datetime.now()
        
        try:
            if not search_term:
                return await self.list_all(limit, offset)
            
            # Search in student_id, class_id, subject_id, and comments
            query = """
            SELECT * FROM marks 
            WHERE (LOWER(student_id) LIKE LOWER($1) OR 
                   LOWER(class_id) LIKE LOWER($1) OR 
                   LOWER(subject_id) LIKE LOWER($1) OR 
                   LOWER(comments) LIKE LOWER($1))
            ORDER BY created_at DESC 
            LIMIT $2 OFFSET $3
            """
            
            search_pattern = f"%{search_term}%"
            result = await self.db.execute_query(query, [search_pattern, limit, offset])
            
            if result.success:
                marks = [self._parse_json_fields(mark) for mark in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = """
                SELECT COUNT(*) FROM marks 
                WHERE (LOWER(student_id) LIKE LOWER($1) OR 
                       LOWER(class_id) LIKE LOWER($1) OR 
                       LOWER(subject_id) LIKE LOWER($1) OR 
                       LOWER(comments) LIKE LOWER($1))
                """
                count_result = await self.db.execute_query(count_query, [search_pattern])
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.SEARCH,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=marks,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to search marks records",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error searching marks records: {str(e)}")
            return self._create_result(
                error=f"Database error searching marks records: {str(e)}",
                query_time=query_time
            )
    
    async def filter(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Filter marks records by criteria.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of marks records to return
            offset: Number of marks records to skip
            
        Returns:
            QueryResult with filtered results
        """
        start_time = datetime.now()
        
        try:
            if not filters:
                return await self.list_all(limit, offset)
            
            # Build query dynamically based on filters
            conditions = []
            values = []
            
            for field, value in filters.items():
                if field == 'student_id':
                    conditions.append(f"student_id = ${len(values) + 1}")
                    values.append(value)
                elif field == 'class_id':
                    conditions.append(f"class_id = ${len(values) + 1}")
                    values.append(value)
                elif field == 'subject_id':
                    conditions.append(f"subject_id = ${len(values) + 1}")
                    values.append(value)
                elif field == 'assessment_type':
                    conditions.append(f"assessment_type = ${len(values) + 1}")
                    values.append(value)
                elif field == 'status':
                    conditions.append(f"status = ${len(values) + 1}")
                    values.append(value)
                elif field == 'semester':
                    conditions.append(f"semester = ${len(values) + 1}")
                    values.append(value)
                elif field == 'grade_letter':
                    conditions.append(f"grade_letter = ${len(values) + 1}")
                    values.append(value)
                elif field == 'min_marks':
                    conditions.append(f"marks_obtained >= ${len(values) + 1}")
                    values.append(value)
                elif field == 'max_marks':
                    conditions.append(f"marks_obtained <= ${len(values) + 1}")
                    values.append(value)
                elif field == 'min_percentage':
                    conditions.append(f"percentage >= ${len(values) + 1}")
                    values.append(value)
                elif field == 'max_percentage':
                    conditions.append(f"percentage <= ${len(values) + 1}")
                    values.append(value)
                elif field == 'date_range_start':
                    conditions.append(f"created_at >= ${len(values) + 1}")
                    values.append(value)
                elif field == 'date_range_end':
                    conditions.append(f"created_at <= ${len(values) + 1}")
                    values.append(value)
            
            query_conditions = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM marks WHERE {query_conditions} ORDER BY created_at DESC LIMIT ${len(values) + 1} OFFSET ${len(values) + 2}"
            
            values.extend([limit, offset])
            result = await self.db.execute_query(query, values)
            
            if result.success:
                marks = [self._parse_json_fields(mark) for mark in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM marks WHERE {query_conditions}"
                count_result = await self.db.execute_query(count_query, values[:-2])
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.FILTER,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=marks,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to filter marks records",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error filtering marks records: {str(e)}")
            return self._create_result(
                error=f"Database error filtering marks records: {str(e)}",
                query_time=query_time
            )
    
    async def get_student_performance(self, student_id: str, semester: str = None) -> QueryResult:
        """
        Get performance summary for a student.
        
        Args:
            student_id: Unique identifier for the student
            semester: Optional semester filter
            
        Returns:
            QueryResult with student performance summary
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(student_id):
                return self._create_result(error="Invalid student ID")
            
            conditions = ["student_id = $1"]
            values = [student_id]
            
            if semester:
                conditions.append("semester = $2")
                values.append(semester)
            
            query_conditions = " AND ".join(conditions)
            query = f"""
            SELECT * FROM marks 
            WHERE {query_conditions}
            ORDER BY created_at DESC
            """
            
            result = await self.db.execute_query(query, values)
            
            if result.success:
                marks = [self._parse_json_fields(mark) for mark in result.data]
                
                # Calculate performance statistics
                if marks:
                    total_marks = sum(mark['marks_obtained'] for mark in marks)
                    max_possible = sum(mark['max_marks'] for mark in marks)
                    average_percentage = (total_marks / max_possible * 100) if max_possible > 0 else 0
                    
                    # Calculate GPA
                    total_grade_points = sum(mark['grade_points'] for mark in marks)
                    gpa = total_grade_points / len(marks) if marks else 0
                    
                    # Grade distribution
                    grade_distribution = {}
                    for mark in marks:
                        grade = mark['grade_letter']
                        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
                else:
                    total_marks = 0
                    max_possible = 0
                    average_percentage = 0
                    gpa = 0
                    grade_distribution = {}
                
                performance_summary = {
                    'student_id': student_id,
                    'semester': semester,
                    'total_marks': total_marks,
                    'max_possible_marks': max_possible,
                    'average_percentage': round(average_percentage, 2),
                    'gpa': round(gpa, 2),
                    'total_assessments': len(marks),
                    'grade_distribution': grade_distribution,
                    'marks': marks
                }
                
                query_time = (datetime.now() - start_time).total_seconds()
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=f"{student_id}_performance",
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=performance_summary,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to get student performance",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting student performance for {student_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting student performance: {str(e)}",
                query_time=query_time
            )
    
    async def get_class_statistics(self, class_id: str) -> QueryResult:
        """
        Get statistical summary for a class.
        
        Args:
            class_id: Unique identifier for the class
            
        Returns:
            QueryResult with class statistics
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(class_id):
                return self._create_result(error="Invalid class ID")
            
            # Get all marks for the class
            query = "SELECT * FROM marks WHERE class_id = $1 ORDER BY created_at DESC"
            result = await self.db.execute_query(query, [class_id])
            
            if result.success:
                marks = [self._parse_json_fields(mark) for mark in result.data]
                
                if marks:
                    # Calculate class statistics
                    total_students = len(set(mark['student_id'] for mark in marks))
                    total_assessments = len(marks)
                    average_percentage = sum(mark['percentage'] for mark in marks) / len(marks)
                    
                    # Calculate grade distribution
                    grade_distribution = {}
                    for mark in marks:
                        grade = mark['grade_letter']
                        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
                    
                    # Calculate pass/fail statistics
                    passed_count = sum(1 for mark in marks if mark['grade_letter'] in ['A', 'B', 'C', 'D'])
                    fail_count = total_assessments - passed_count
                    
                    statistics = {
                        'class_id': class_id,
                        'total_students': total_students,
                        'total_assessments': total_assessments,
                        'average_percentage': round(average_percentage, 2),
                        'pass_count': passed_count,
                        'fail_count': fail_count,
                        'pass_rate': round((passed_count / total_assessments) * 100, 2) if total_assessments > 0 else 0,
                        'grade_distribution': grade_distribution,
                        'marks': marks
                    }
                else:
                    statistics = {
                        'class_id': class_id,
                        'total_students': 0,
                        'total_assessments': 0,
                        'average_percentage': 0,
                        'pass_count': 0,
                        'fail_count': 0,
                        'pass_rate': 0,
                        'grade_distribution': {},
                        'marks': []
                    }
                
                query_time = (datetime.now() - start_time).total_seconds()
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=f"{class_id}_statistics",
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=statistics,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to get class statistics",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting class statistics for {class_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting class statistics: {str(e)}",
                query_time=query_time
            )
    
    async def predict_see_marks(self, student_id: str, subject_id: str) -> QueryResult:
        """
        Predict SEE marks for a student based on IA performance.
        
        Args:
            student_id: Unique identifier for the student
            subject_id: Unique identifier for the subject
            
        Returns:
            QueryResult with SEE prediction data
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(student_id):
                return self._create_result(error="Invalid student ID")
            
            if not self._validate_id(subject_id):
                return self._create_result(error="Invalid subject ID")
            
            # Get IA marks for the student and subject
            query = """
            SELECT * FROM marks 
            WHERE student_id = $1 AND subject_id = $2 AND assessment_type = 'internal_assessment'
            ORDER BY created_at DESC
            """
            
            result = await self.db.execute_query(query, [student_id, subject_id])
            
            if result.success and result.data:
                ia_marks = [self._parse_json_fields(mark) for mark in result.data]
                
                if ia_marks:
                    # Calculate average IA percentage
                    ia_percentages = [mark['percentage'] for mark in ia_marks]
                    average_ia_percentage = sum(ia_percentages) / len(ia_percentages)
                    
                    # Simple SEE prediction (this can be enhanced with ML models)
                    # Assuming SEE is generally 10-15% lower than average IA
                    predicted_see_percentage = max(0, average_ia_percentage - 12.5)
                    
                    # Convert to grade
                    predicted_grade = self._get_grade_from_percentage(predicted_see_percentage)
                    
                    prediction_data = {
                        'student_id': student_id,
                        'subject_id': subject_id,
                        'average_ia_percentage': round(average_ia_percentage, 2),
                        'predicted_see_percentage': round(predicted_see_percentage, 2),
                        'predicted_grade': predicted_grade,
                        'confidence': 'medium',  # Can be calculated based on variance
                        'historical_performance': ia_marks
                    }
                else:
                    prediction_data = {
                        'student_id': student_id,
                        'subject_id': subject_id,
                        'average_ia_percentage': 0,
                        'predicted_see_percentage': 0,
                        'predicted_grade': 'F',
                        'confidence': 'low',
                        'historical_performance': []
                    }
                
                query_time = (datetime.now() - start_time).total_seconds()
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=f"{student_id}_{subject_id}_prediction",
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=prediction_data,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to predict SEE marks",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error predicting SEE marks for {student_id}: {str(e)}")
            return self._create_result(
                error=f"Database error predicting SEE marks: {str(e)}",
                query_time=query_time
            )
    
    def _calculate_grade(self, mark_data: Dict[str, Any]) -> QueryResult:
        """
        Calculate grade information based on marks.
        
        Args:
            mark_data: Marks data to calculate grade for
            
        Returns:
            QueryResult with calculated grade information
        """
        try:
            marks_obtained = mark_data.get('marks_obtained', 0)
            max_marks = mark_data.get('max_marks', 1)
            
            # Calculate percentage
            percentage = (marks_obtained / max_marks) * 100 if max_marks > 0 else 0
            
            # Determine grade based on percentage
            grade_letter, grade_points = self._get_grade_from_percentage(percentage)
            
            return self._create_result(data={
                'percentage': round(percentage, 2),
                'grade_letter': grade_letter,
                'grade_points': grade_points
            })
            
        except Exception as e:
            self.logger.error(f"Error calculating grade: {str(e)}")
            return self._create_result(error=f"Error calculating grade: {str(e)}")
    
    def _get_grade_from_percentage(self, percentage: float) -> tuple:
        """
        Get grade letter and grade points from percentage.
        
        Args:
            percentage: Percentage score
            
        Returns:
            Tuple of (grade_letter, grade_points)
        """
        if percentage >= 90:
            return 'A+', 10.0
        elif percentage >= 80:
            return 'A', 9.0
        elif percentage >= 70:
            return 'B+', 8.0
        elif percentage >= 60:
            return 'B', 7.0
        elif percentage >= 50:
            return 'C', 6.0
        elif percentage >= 40:
            return 'D', 5.0
        else:
            return 'F', 0.0
    
    def _parse_json_fields(self, mark_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse JSON fields back to dictionary format.
        
        Args:
            mark_data: Marks data from database
            
        Returns:
            Marks data with parsed JSON fields
        """
        if not mark_data:
            return {}
        
        parsed_data = mark_data.copy()
        
        # Parse JSON fields
        if 'assessment_marks' in parsed_data and parsed_data['assessment_marks']:
            try:
                parsed_data['assessment_marks'] = json.loads(parsed_data['assessment_marks'])
            except json.JSONDecodeError:
                parsed_data['assessment_marks'] = {}
        
        if 'metadata' in parsed_data and parsed_data['metadata']:
            try:
                parsed_data['metadata'] = json.loads(parsed_data['metadata'])
            except json.JSONDecodeError:
                parsed_data['metadata'] = {}
        
        return parsed_data