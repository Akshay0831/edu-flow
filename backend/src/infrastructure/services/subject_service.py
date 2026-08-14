"""
Subject Management Service

This module provides business logic for subject management:
- Subject creation and management
- Subject categorization and organization
- Subject prerequisites and dependencies
- Subject analytics and reporting
- Subject mapping to courses
- Performance tracking by subject

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from uuid import uuid4

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.core.logging import get_logger
from src.core.base_service import BaseService
from src.infrastructure.repositories.subject_repository import SubjectRepository
from src.models.subject_model import SubjectCreate, SubjectUpdate, SubjectResponse, SubjectStats

logger = get_logger(__name__)


class SubjectService(BaseService):
    """Subject management service with comprehensive functionality."""
    
    def __init__(self, subject_repository: SubjectRepository):
        super().__init__()
        self.subject_repository = subject_repository
        self._cache = {}
    
    async def initialize(self) -> None:
        """Initialize the subject service."""
        try:
            await super().initialize()
            logger.info("Subject service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize subject service: {str(e)}")
            raise
    
    async def dispose(self) -> None:
        """Dispose the subject service."""
        try:
            await super().dispose()
            self._cache.clear()
            logger.info("Subject service disposed successfully")
        except Exception as e:
            logger.error(f"Failed to dispose subject service: {str(e)}")
            raise
    
    # Core Business Operations
    
    async def create_subject(self, subject_data: Dict[str, Any]) -> SubjectResponse:
        """Create a new subject with business logic validation."""
        try:
            # Validate subject data
            await self._validate_subject_creation(subject_data)
            
            # Check if subject already exists
            existing_subject = await self.subject_repository.get_by_code(subject_data['subject_code'])
            if existing_subject:
                raise ConflictError(f"Subject with code {subject_data['subject_code']} already exists")
            
            # Create subject
            subject = await self.subject_repository.create(**subject_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return subject
            
        except Exception as e:
            logger.error(f"Failed to create subject: {str(e)}")
            raise
    
    async def update_subject(self, subject_id: str, subject_data: Dict[str, Any]) -> Optional[SubjectResponse]:
        """Update an existing subject with business logic."""
        try:
            # Validate subject exists
            subject = await self.subject_repository.get_by_id(subject_id)
            if not subject:
                raise NotFoundError(f"Subject not found with ID: {subject_id}")
            
            # Validate update data
            await self._validate_subject_update(subject_data)
            
            # Check for code conflicts if subject_code is being updated
            if 'subject_code' in subject_data and subject_data['subject_code'] != subject.subject_code:
                existing_subject = await self.subject_repository.get_by_code(subject_data['subject_code'])
                if existing_subject:
                    raise ConflictError(f"Subject with code {subject_data['subject_code']} already exists")
            
            # Update subject
            updated_subject = await self.subject_repository.update(subject_id, **subject_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return updated_subject
            
        except Exception as e:
            logger.error(f"Failed to update subject {subject_id}: {str(e)}")
            raise
    
    async def get_subject(self, subject_id: str) -> Optional[SubjectResponse]:
        """Get a subject by ID with caching."""
        try:
            # Check cache first
            if subject_id in self._cache:
                return self._cache[subject_id]
            
            # Get subject from repository
            subject = await self.subject_repository.get_by_id(subject_id)
            
            if subject:
                # Cache the result
                self._cache[subject_id] = subject
            
            return subject
            
        except Exception as e:
            logger.error(f"Failed to get subject {subject_id}: {str(e)}")
            raise
    
    async def get_subject_by_code(self, subject_code: str) -> Optional[SubjectResponse]:
        """Get a subject by subject code."""
        try:
            return await self.subject_repository.get_by_code(subject_code)
        except Exception as e:
            logger.error(f"Failed to get subject by code {subject_code}: {str(e)}")
            raise
    
    async def delete_subject(self, subject_id: str) -> bool:
        """Delete a subject with business logic."""
        try:
            # Validate subject exists
            subject = await self.subject_repository.get_by_id(subject_id)
            if not subject:
                raise NotFoundError(f"Subject not found with ID: {subject_id}")
            
            # Check if subject has associated courses
            has_courses = await self._has_associated_courses(subject_id)
            if has_courses:
                raise ValidationError("Cannot delete subject that has associated courses")
            
            # Check if subject has associated classes
            has_classes = await self._has_associated_classes(subject_id)
            if has_classes:
                raise ValidationError("Cannot delete subject that has associated classes")
            
            # Delete subject
            result = await self.subject_repository.delete(subject_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete subject {subject_id}: {str(e)}")
            raise
    
    # Search and Filtering
    
    async def search_subjects(self, search_term: str, skip: int = 0, limit: int = 100) -> List[SubjectResponse]:
        """Search for subjects by name, code, or description."""
        try:
            subjects = await self.subject_repository.search_subjects(
                search_term=search_term,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for subject in subjects:
                self._cache[subject.id] = subject
            
            return subjects
            
        except Exception as e:
            logger.error(f"Failed to search subjects: {str(e)}")
            raise
    
    async def get_subjects_by_department(self, department_id: str, skip: int = 0, limit: int = 100) -> List[SubjectResponse]:
        """Get subjects by department."""
        try:
            subjects = await self.subject_repository.get_by_department(
                department_id=department_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for subject in subjects:
                self._cache[subject.id] = subject
            
            return subjects
            
        except Exception as e:
            logger.error(f"Failed to get subjects by department: {str(e)}")
            raise
    
    async def get_subjects_by_level(self, level: str, skip: int = 0, limit: int = 100) -> List[SubjectResponse]:
        """Get subjects by academic level."""
        try:
            subjects = await self.subject_repository.get_by_level(
                level=level,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for subject in subjects:
                self._cache[subject.id] = subject
            
            return subjects
            
        except Exception as e:
            logger.error(f"Failed to get subjects by level: {str(e)}")
            raise
    
    async def get_subjects_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[SubjectResponse]:
        """Get subjects by category."""
        try:
            subjects = await self.subject_repository.get_by_category(
                category=category,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for subject in subjects:
                self._cache[subject.id] = subject
            
            return subjects
            
        except Exception as e:
            logger.error(f"Failed to get subjects by category: {str(e)}")
            raise
    
    async def get_subjects_by_credits(self, min_credits: int, max_credits: int, skip: int = 0, limit: int = 100) -> List[SubjectResponse]:
        """Get subjects by credit range."""
        try:
            subjects = await self.subject_repository.get_by_credits(
                min_credits=min_credits,
                max_credits=max_credits,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for subject in subjects:
                self._cache[subject.id] = subject
            
            return subjects
            
        except Exception as e:
            logger.error(f"Failed to get subjects by credits: {str(e)}")
            raise
    
    # Subject Categorization
    
    async def categorize_subject(self, subject_id: str, categories: List[str]) -> bool:
        """Categorize a subject."""
        try:
            # Validate subject exists
            subject = await self.subject_repository.get_by_id(subject_id)
            if not subject:
                raise NotFoundError(f"Subject not found with ID: {subject_id}")
            
            # Validate categories
            valid_categories = ['core', 'elective', 'prerequisite', 'advanced', 'foundational', 'specialized']
            for category in categories:
                if category not in valid_categories:
                    raise ValidationError(f"Invalid category: {category}")
            
            # Categorize subject
            result = await self.subject_repository.categorize_subject(
                subject_id=subject_id,
                categories=categories
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to categorize subject {subject_id}: {str(e)}")
            raise
    
    async def remove_subject_category(self, subject_id: str, category: str) -> bool:
        """Remove a category from a subject."""
        try:
            # Validate subject exists
            subject = await self.subject_repository.get_by_id(subject_id)
            if not subject:
                raise NotFoundError(f"Subject not found with ID: {subject_id}")
            
            # Remove category
            result = await self.subject_repository.remove_subject_category(
                subject_id=subject_id,
                category=category
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to remove category from subject {subject_id}: {str(e)}")
            raise
    
    async def get_subject_categories(self, subject_id: str) -> List[str]:
        """Get all categories for a subject."""
        try:
            return await self.subject_repository.get_subject_categories(subject_id)
        except Exception as e:
            logger.error(f"Failed to get subject categories for {subject_id}: {str(e)}")
            raise
    
    async def get_subjects_by_categories(self, categories: List[str], skip: int = 0, limit: int = 100) -> List[SubjectResponse]:
        """Get subjects that have all specified categories."""
        try:
            subjects = await self.subject_repository.get_subjects_by_categories(
                categories=categories,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for subject in subjects:
                self._cache[subject.id] = subject
            
            return subjects
            
        except Exception as e:
            logger.error(f"Failed to get subjects by categories: {str(e)}")
            raise
    
    # Prerequisite Management
    
    async def add_prerequisite(self, subject_id: str, prerequisite_id: str, 
                            prerequisite_type: str = "required") -> bool:
        """Add a prerequisite to a subject."""
        try:
            # Validate subject exists
            subject = await self.subject_repository.get_by_id(subject_id)
            if not subject:
                raise NotFoundError(f"Subject not found with ID: {subject_id}")
            
            # Validate prerequisite exists
            prerequisite = await self.subject_repository.get_by_id(prerequisite_id)
            if not prerequisite:
                raise NotFoundError(f"Prerequisite subject not found with ID: {prerequisite_id}")
            
            # Validate prerequisite type
            if prerequisite_type not in ['required', 'recommended']:
                raise ValidationError(f"Invalid prerequisite type: {prerequisite_type}")
            
            # Check for circular dependencies
            if await self._creates_circular_dependency(subject_id, prerequisite_id):
                raise ValidationError("Adding this prerequisite would create a circular dependency")
            
            # Add prerequisite
            result = await self.subject_repository.add_prerequisite(
                subject_id=subject_id,
                prerequisite_id=prerequisite_id,
                prerequisite_type=prerequisite_type
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to add prerequisite for subject {subject_id}: {str(e)}")
            raise
    
    async def remove_prerequisite(self, subject_id: str, prerequisite_id: str) -> bool:
        """Remove a prerequisite from a subject."""
        try:
            # Validate subject exists
            subject = await self.subject_repository.get_by_id(subject_id)
            if not subject:
                raise NotFoundError(f"Subject not found with ID: {subject_id}")
            
            # Remove prerequisite
            result = await self.subject_repository.remove_prerequisite(
                subject_id=subject_id,
                prerequisite_id=prerequisite_id
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to remove prerequisite for subject {subject_id}: {str(e)}")
            raise
    
    async def get_subject_prerequisites(self, subject_id: str) -> List[Dict[str, Any]]:
        """Get all prerequisites for a subject."""
        try:
            return await self.subject_repository.get_subject_prerequisites(subject_id)
        except Exception as e:
            logger.error(f"Failed to get subject prerequisites for {subject_id}: {str(e)}")
            raise
    
    async def get_dependent_subjects(self, subject_id: str) -> List[Dict[str, Any]]:
        """Get all subjects that depend on this subject."""
        try:
            return await self.subject_repository.get_dependent_subjects(subject_id)
        except Exception as e:
            logger.error(f"Failed to get dependent subjects for {subject_id}: {str(e)}")
            raise
    
    # Subject Mapping
    
    async def map_subject_to_courses(self, subject_id: str, course_ids: List[str]) -> bool:
        """Map a subject to courses."""
        try:
            # Validate subject exists
            subject = await self.subject_repository.get_by_id(subject_id)
            if not subject:
                raise NotFoundError(f"Subject not found with ID: {subject_id}")
            
            # Validate courses exist
            from src.infrastructure.repositories.course_repository import CourseRepository
            course_repo = CourseRepository()
            for course_id in course_ids:
                course = await course_repo.get_by_id(course_id)
                if not course:
                    raise NotFoundError(f"Course not found with ID: {course_id}")
            
            # Map subject to courses
            result = await self.subject_repository.map_subject_to_courses(
                subject_id=subject_id,
                course_ids=course_ids
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to map subject {subject_id} to courses: {str(e)}")
            raise
    
    async def unmap_subject_from_courses(self, subject_id: str, course_ids: List[str]) -> bool:
        """Unmap a subject from courses."""
        try:
            # Validate subject exists
            subject = await self.subject_repository.get_by_id(subject_id)
            if not subject:
                raise NotFoundError(f"Subject not found with ID: {subject_id}")
            
            # Unmap subject from courses
            result = await self.subject_repository.unmap_subject_from_courses(
                subject_id=subject_id,
                course_ids=course_ids
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to unmap subject {subject_id} from courses: {str(e)}")
            raise
    
    async def get_subject_courses(self, subject_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all courses associated with a subject."""
        try:
            return await self.subject_repository.get_subject_courses(
                subject_id=subject_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get subject courses for {subject_id}: {str(e)}")
            raise
    
    async def get_courses_by_subject(self, subject_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all courses that use this subject."""
        try:
            return await self.subject_repository.get_courses_by_subject(
                subject_id=subject_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get courses by subject {subject_id}: {str(e)}")
            raise
    
    # Analytics and Reporting
    
    async def get_subject_stats(self, subject_id: str) -> SubjectStats:
        """Get comprehensive subject statistics."""
        try:
            # Validate subject exists
            subject = await self.subject_repository.get_by_id(subject_id)
            if not subject:
                raise NotFoundError(f"Subject not found with ID: {subject_id}")
            
            # Get courses
            courses = await self.get_subject_courses(subject_id)
            total_courses = len(courses)
            active_courses = len([c for c in courses if c.get('status') == 'active'])
            
            # Get prerequisites
            prerequisites = await self.get_subject_prerequisites(subject_id)
            prerequisite_count = len(prerequisites)
            
            # Get dependencies
            dependents = await self.get_dependent_subjects(subject_id)
            dependent_count = len(dependents)
            
            # Get categories
            categories = await self.get_subject_categories(subject_id)
            
            # Create stats object
            stats = SubjectStats(
                subject_id=subject_id,
                subject_name=subject.name,
                subject_code=subject.subject_code,
                total_courses=total_courses,
                active_courses=active_courses,
                prerequisite_count=prerequisite_count,
                dependent_count=dependent_count,
                categories=categories,
                last_course_update=courses[-1]['updated_at'] if courses else None,
                prerequisites_met=await self._check_prerequisites_met(subject_id),
                is_core='core' in categories,
                total_credits=subject.credits
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get subject stats for {subject_id}: {str(e)}")
            raise
    
    async def generate_subject_report(self, subject_id: str, report_type: str = "overview", 
                                    start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Generate comprehensive subject report."""
        try:
            # Validate subject exists
            subject = await self.subject_repository.get_by_id(subject_id)
            if not subject:
                raise NotFoundError(f"Subject not found with ID: {subject_id}")
            
            # Generate report based on type
            if report_type == "overview":
                return await self._generate_overview_report(subject_id)
            elif report_type == "courses":
                return await self._generate_courses_report(subject_id, start_date, end_date)
            elif report_type == "prerequisites":
                return await self._generate_prerequisites_report(subject_id)
            elif report_type == "performance":
                return await self._generate_performance_report(subject_id, start_date, end_date)
            else:
                raise ValidationError(f"Unknown report type: {report_type}")
                
        except Exception as e:
            logger.error(f"Failed to generate subject report for {subject_id}: {str(e)}")
            raise
    
    # Batch Operations
    
    async def batch_update_subjects(self, updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple subjects."""
        results = {}
        
        for update in updates:
            subject_id = update['subject_id']
            try:
                result = await self.update_subject(subject_id, update)
                results[subject_id] = result is not None
            except Exception as e:
                logger.error(f"Failed to update subject {subject_id}: {str(e)}")
                results[subject_id] = False
        
        return results
    
    async def batch_map_subjects_to_courses(self, mappings: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Map multiple subjects to courses."""
        results = {}
        
        for mapping in mappings:
            subject_id = mapping['subject_id']
            try:
                result = await self.map_subject_to_courses(
                    subject_id=subject_id,
                    course_ids=mapping['course_ids']
                )
                results[subject_id] = result
            except Exception as e:
                logger.error(f"Failed to map subject {subject_id} to courses: {str(e)}")
                results[subject_id] = False
        
        return results
    
    # Helper Methods
    
    async def _validate_subject_creation(self, data: Dict[str, Any]) -> None:
        """Validate subject creation data."""
        required_fields = ['name', 'subject_code', 'description', 'department_id', 'credits', 'level']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate subject code format
        if not self._validate_subject_code(data['subject_code']):
            raise ValidationError("Invalid subject code format")
        
        # Validate credits
        if not (1 <= data['credits'] <= 10):
            raise ValidationError("Credits must be between 1 and 10")
        
        # Validate level
        valid_levels = ['undergraduate', 'graduate', 'postgraduate']
        if data['level'] not in valid_levels:
            raise ValidationError(f"Invalid subject level. Must be one of: {valid_levels}")
        
        # Validate department exists
        from src.infrastructure.repositories.department_repository import DepartmentRepository
        dept_repo = DepartmentRepository()
        department = await dept_repo.get_by_id(data['department_id'])
        if not department:
            raise NotFoundError(f"Department not found with ID: {data['department_id']}")
    
    async def _validate_subject_update(self, data: Dict[str, Any]) -> None:
        """Validate subject update data."""
        allowed_fields = ['name', 'description', 'credits', 'level', 'categories', 'syllabus']
        
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
                raise ValidationError(f"Invalid subject level. Must be one of: {valid_levels}")
        
        # Validate categories if provided
        if 'categories' in data and data['categories']:
            valid_categories = ['core', 'elective', 'prerequisite', 'advanced', 'foundational', 'specialized']
            for category in data['categories']:
                if category not in valid_categories:
                    raise ValidationError(f"Invalid category: {category}")
    
    def _validate_subject_code(self, subject_code: str) -> bool:
        """Validate subject code format."""
        import re
        pattern = r'^[A-Z]{3}[0-9]{3}$'  # Example: CS101
        return re.match(pattern, subject_code) is not None
    
    async def _has_associated_courses(self, subject_id: str) -> bool:
        """Check if subject has associated courses."""
        courses = await self.get_subject_courses(subject_id)
        return len(courses) > 0
    
    async def _has_associated_classes(self, subject_id: str) -> bool:
        """Check if subject has associated classes."""
        from src.infrastructure.repositories.class_repository import ClassRepository
        class_repo = ClassRepository()
        classes = await class_repo.get_by_subject(subject_id)
        return len(classes) > 0
    
    async def _creates_circular_dependency(self, subject_id: str, prerequisite_id: str) -> bool:
        """Check if adding prerequisite creates circular dependency."""
        # This would implement a graph traversal algorithm to detect cycles
        # For now, return False (should be implemented)
        return False
    
    async def _check_prerequisites_met(self, subject_id: str) -> bool:
        """Check if all prerequisites are met for this subject."""
        prerequisites = await self.get_subject_prerequisites(subject_id)
        if not prerequisites:
            return True
        
        # This would check if student has completed all prerequisite subjects
        # For now, return True (should be implemented)
        return True
    
    async def _generate_overview_report(self, subject_id: str) -> Dict[str, Any]:
        """Generate overview report for subject."""
        try:
            subject = await self.get_subject(subject_id)
            stats = await self.get_subject_stats(subject_id)
            courses = await self.get_subject_courses(subject_id, 0, 100)
            
            return {
                "subject": subject.to_dict() if subject else None,
                "stats": stats,
                "courses": courses,
                "prerequisites": await self.get_subject_prerequisites(subject_id),
                "dependencies": await self.get_dependent_subjects(subject_id),
                "categories": await self.get_subject_categories(subject_id),
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "overview"
            }
        except Exception as e:
            logger.error(f"Failed to generate overview report for {subject_id}: {str(e)}")
            raise
    
    async def _generate_courses_report(self, subject_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate courses report for subject."""
        try:
            subject = await self.get_subject(subject_id)
            courses = await self.get_subject_courses(subject_id, 0, 100)
            
            # Analyze courses
            course_analysis = self._analyze_courses(courses)
            
            return {
                "subject": subject.to_dict() if subject else None,
                "courses": courses,
                "analysis": course_analysis,
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "courses"
            }
        except Exception as e:
            logger.error(f"Failed to generate courses report for {subject_id}: {str(e)}")
            raise
    
    async def _generate_prerequisites_report(self, subject_id: str) -> Dict[str, Any]:
        """Generate prerequisites report for subject."""
        try:
            subject = await self.get_subject(subject_id)
            prerequisites = await self.get_subject_prerequisites(subject_id)
            dependents = await self.get_dependent_subjects(subject_id)
            
            return {
                "subject": subject.to_dict() if subject else None,
                "prerequisites": prerequisites,
                "dependents": dependents,
                "prerequisite_tree": self._build_prerequisite_tree(subject_id),
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "prerequisites"
            }
        except Exception as e:
            logger.error(f"Failed to generate prerequisites report for {subject_id}: {str(e)}")
            raise
    
    async def _generate_performance_report(self, subject_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate performance report for subject."""
        try:
            subject = await self.get_subject(subject_id)
            courses = await self.get_subject_courses(subject_id, 0, 100)
            
            # Aggregate performance data from all courses
            course_performances = []
            for course in courses:
                # This would get performance data for each course
                # For now, create mock data
                course_performance = {
                    "course_id": course.get('id'),
                    "course_name": course.get('name'),
                    "average_grade": 0,
                    "total_students": 0,
                    "pass_rate": 0
                }
                course_performances.append(course_performance)
            
            return {
                "subject": subject.to_dict() if subject else None,
                "course_performances": course_performances,
                "summary": self._summarize_performance(course_performances),
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "performance"
            }
        except Exception as e:
            logger.error(f"Failed to generate performance report for {subject_id}: {str(e)}")
            raise
    
    def _analyze_courses(self, courses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze courses associated with a subject."""
        if not courses:
            return {"total_courses": 0, "by_level": {}, "by_semester": {}}
        
        # Group by level
        by_level = {}
        # Group by semester
        by_semester = {}
        # Group by department
        by_department = {}
        
        for course in courses:
            level = course.get('level', 'Unknown')
            semester = course.get('semester', 'Unknown')
            department = course.get('department_id', 'Unknown')
            
            by_level[level] = by_level.get(level, 0) + 1
            by_semester[semester] = by_semester.get(semester, 0) + 1
            by_department[department] = by_department.get(department, 0) + 1
        
        return {
            "total_courses": len(courses),
            "by_level": by_level,
            "by_semester": by_semester,
            "by_department": by_department,
            "average_credits": sum(c.get('credits', 0) for c in courses) / len(courses) if courses else 0
        }
    
    def _summarize_performance(self, performances: List[Dict[str, Any]]) -> Dict[str, float]:
        """Summarize performance data."""
        if not performances:
            return {
                "total_courses": 0,
                "average_grade": 0,
                "total_students": 0,
                "pass_rate": 0,
                "highest_average": 0,
                "lowest_average": 0
            }
        
        total_students = sum(p.get('total_students', 0) for p in performances)
        total_passing = sum(p.get('total_students', 0) * (p.get('pass_rate', 0) / 100) for p in performances)
        
        return {
            "total_courses": len(performances),
            "average_grade": sum(p.get('average_grade', 0) for p in performances) / len(performances),
            "total_students": total_students,
            "pass_rate": (total_passing / total_students * 100) if total_students > 0 else 0,
            "highest_average": max(p.get('average_grade', 0) for p in performances),
            "lowest_average": min(p.get('average_grade', 0) for p in performances)
        }
    
    def _build_prerequisite_tree(self, subject_id: str) -> Dict[str, Any]:
        """Build prerequisite tree for a subject."""
        # This would implement a recursive algorithm to build a tree structure
        # For now, return empty dict
        return {}
    
    async def _invalidate_cache(self) -> None:
        """Invalidate subject cache."""
        self._cache.clear()