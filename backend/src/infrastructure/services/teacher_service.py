"""
Teacher Management Service

This module provides business logic for teacher management:
- Teacher registration and authentication
- Teacher profile management
- Subject expertise tracking
- Class management
- Performance evaluation
- Workload management

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from uuid import uuid4

from core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from core.logging import get_logger
from core.base_service import BaseService
from infrastructure.repositories.base_repository import BaseRepository
from models.user import UserCreate, UserUpdate, User
from models.teacher import TeacherStats

logger = get_logger(__name__)


class TeacherService(BaseService):
    """Teacher management service with comprehensive functionality."""
    
    def __init__(self, repository: BaseRepository):
        super().__init__(repository)
        self._cache = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the teacher service."""
        try:
            self._initialized = True
            logger.info("Teacher service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize teacher service: {str(e)}")
            raise
    
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized
    
    async def dispose(self) -> None:
        """Dispose the teacher service."""
        try:
            self._cache.clear()
            logger.info("Teacher service disposed successfully")
        except Exception as e:
            logger.error(f"Failed to dispose teacher service: {str(e)}")
            raise
    
    # Core Business Operations
    
    async def create_teacher(self, teacher_data: Dict[str, Any]) -> User:
        """Create a new teacher with business logic validation."""
        try:
            # Validate teacher data
            await self._validate_teacher_creation(teacher_data)
            
            # Check if teacher already exists
            existing_teacher = await self.repository.get_by_email(teacher_data['email'])
            if existing_teacher:
                raise ConflictError(f"Teacher with email {teacher_data['email']} already exists")
            
            # Create teacher
            teacher = await self.repository.create(**teacher_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return teacher
            
        except Exception as e:
            logger.error(f"Failed to create teacher: {str(e)}")
            raise
    
    async def update_teacher(self, teacher_id: str, teacher_data: Dict[str, Any]) -> Optional[User]:
        """Update an existing teacher with business logic."""
        try:
            # Validate teacher exists
            teacher = await self.repository.get_by_id(teacher_id)
            if not teacher:
                raise NotFoundError(f"Teacher not found with ID: {teacher_id}")
            
            # Validate update data
            await self._validate_teacher_update(teacher_data)
            
            # Check for email conflicts if email is being updated
            if 'email' in teacher_data and teacher_data['email'] != teacher.email:
                existing_teacher = await self.repository.get_by_email(teacher_data['email'])
                if existing_teacher:
                    raise ConflictError(f"Teacher with email {teacher_data['email']} already exists")
            
            # Update teacher
            updated_teacher = await self.repository.update(teacher_id, **teacher_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return updated_teacher
            
        except Exception as e:
            logger.error(f"Failed to update teacher {teacher_id}: {str(e)}")
            raise
    
    async def get_teacher(self, teacher_id: str) -> Optional[User]:
        """Get a teacher by ID with caching."""
        try:
            # Check cache first
            if teacher_id in self._cache:
                return self._cache[teacher_id]
            
            # Get teacher from repository
            teacher = await self.repository.get_by_id(teacher_id)
            
            if teacher:
                # Cache the result
                self._cache[teacher_id] = teacher
            
            return teacher
            
        except Exception as e:
            logger.error(f"Failed to get teacher {teacher_id}: {str(e)}")
            raise
    
    async def get_teacher_by_email(self, email: str) -> Optional[User]:
        """Get a teacher by email."""
        try:
            return await self.repository.get_by_email(email)
        except Exception as e:
            logger.error(f"Failed to get teacher by email {email}: {str(e)}")
            raise
    
    async def get_teacher_by_employee_id(self, employee_id: str) -> Optional[Dict]:
        """Get a teacher by employee ID."""
        try:
            teacher = await self.repository.get_by_employee_id(employee_id)
            return teacher.dict() if teacher else None
        except Exception as e:
            logger.error(f"Failed to get teacher by employee ID {employee_id}: {str(e)}")
            raise
    
    async def delete_teacher(self, teacher_id: str) -> bool:
        """Delete a teacher with business logic."""
        try:
            # Validate teacher exists
            teacher = await self.repository.get_by_id(teacher_id)
            if not teacher:
                raise NotFoundError(f"Teacher not found with ID: {teacher_id}")
            
            # Check if teacher has active classes
            has_active_classes = await self._has_active_classes(teacher_id)
            if has_active_classes:
                raise ValidationError("Cannot delete teacher with active classes")
            
            # Check if teacher has assigned students
            has_assigned_students = await self._has_assigned_students(teacher_id)
            if has_assigned_students:
                raise ValidationError("Cannot delete teacher with assigned students")
            
            # Delete teacher
            result = await self.repository.delete(teacher_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete teacher {teacher_id}: {str(e)}")
            raise
    
    # Search and Filtering
    
    async def search_teachers(self, search_term: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search for teachers by name, email, or employee ID."""
        try:
            teachers = await self.repository.search_teachers(
                search_term=search_term,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for teacher in teachers:
                self._cache[teacher.id] = teacher
            
            return teachers
            
        except Exception as e:
            logger.error(f"Failed to search teachers: {str(e)}")
            raise
    
    async def get_teachers_by_department(self, department_id: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get teachers by department."""
        try:
            teachers = await self.repository.get_by_department(
                department_id=department_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for teacher in teachers:
                self._cache[teacher.id] = teacher
            
            return teachers
            
        except Exception as e:
            logger.error(f"Failed to get teachers by department: {str(e)}")
            raise
    
    async def get_teachers_by_subject(self, subject_id: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get teachers by subject expertise."""
        try:
            teachers = await self.repository.get_by_subject(
                subject_id=subject_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for teacher in teachers:
                self._cache[teacher.id] = teacher
            
            return teachers
            
        except Exception as e:
            logger.error(f"Failed to get teachers by subject: {str(e)}")
            raise
    
    async def get_teachers_by_qualification(self, qualification: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get teachers by qualification."""
        try:
            teachers = await self.repository.get_by_qualification(
                qualification=qualification,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for teacher in teachers:
                self._cache[teacher.id] = teacher
            
            return teachers
            
        except Exception as e:
            logger.error(f"Failed to get teachers by qualification: {str(e)}")
            raise
    
    # Subject Expertise Management
    
    async def add_subject_expertise(self, teacher_id: str, subject_id: str, expertise_level: str = "intermediate") -> bool:
        """Add subject expertise for a teacher."""
        try:
            # Validate teacher exists
            teacher = await self.repository.get_by_id(teacher_id)
            if not teacher:
                raise NotFoundError(f"Teacher not found with ID: {teacher_id}")
            
            # Validate subject exists
            from infrastructure.repositories.subject_repository import SubjectRepository
            subject_repo = SubjectRepository()
            subject = await subject_repo.get_by_id(subject_id)
            if not subject:
                raise NotFoundError(f"Subject not found with ID: {subject_id}")
            
            # Validate expertise level
            if expertise_level not in ['beginner', 'intermediate', 'advanced', 'expert']:
                raise ValidationError(f"Invalid expertise level: {expertise_level}")
            
            # Add subject expertise
            result = await self.repository.add_subject_expertise(
                teacher_id=teacher_id,
                subject_id=subject_id,
                expertise_level=expertise_level
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to add subject expertise for teacher {teacher_id}: {str(e)}")
            raise
    
    async def remove_subject_expertise(self, teacher_id: str, subject_id: str) -> bool:
        """Remove subject expertise from a teacher."""
        try:
            # Validate teacher exists
            teacher = await self.repository.get_by_id(teacher_id)
            if not teacher:
                raise NotFoundError(f"Teacher not found with ID: {teacher_id}")
            
            # Remove subject expertise
            result = await self.repository.remove_subject_expertise(
                teacher_id=teacher_id,
                subject_id=subject_id
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to remove subject expertise for teacher {teacher_id}: {str(e)}")
            raise
    
    async def update_subject_expertise(self, teacher_id: str, subject_id: str, expertise_level: str) -> bool:
        """Update subject expertise level for a teacher."""
        try:
            # Validate teacher exists
            teacher = await self.repository.get_by_id(teacher_id)
            if not teacher:
                raise NotFoundError(f"Teacher not found with ID: {teacher_id}")
            
            # Validate subject exists
            from infrastructure.repositories.subject_repository import SubjectRepository
            subject_repo = SubjectRepository()
            subject = await subject_repo.get_by_id(subject_id)
            if not subject:
                raise NotFoundError(f"Subject not found with ID: {subject_id}")
            
            # Validate expertise level
            if expertise_level not in ['beginner', 'intermediate', 'advanced', 'expert']:
                raise ValidationError(f"Invalid expertise level: {expertise_level}")
            
            # Update subject expertise
            result = await self.repository.update_subject_expertise(
                teacher_id=teacher_id,
                subject_id=subject_id,
                expertise_level=expertise_level
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update subject expertise for teacher {teacher_id}: {str(e)}")
            raise
    
    async def get_teacher_subjects(self, teacher_id: str) -> List[Dict[str, Any]]:
        """Get all subjects that a teacher is qualified to teach."""
        try:
            return await self.repository.get_teacher_subjects(teacher_id)
        except Exception as e:
            logger.error(f"Failed to get teacher subjects for {teacher_id}: {str(e)}")
            raise
    
    # Class Management
    
    async def assign_teacher_to_class(self, teacher_id: str, class_id: str, 
                                   assigned_by_id: str = None, assignment_date: datetime = None) -> bool:
        """Assign a teacher to a class."""
        try:
            # Validate teacher exists
            teacher = await self.repository.get_by_id(teacher_id)
            if not teacher:
                raise NotFoundError(f"Teacher not found with ID: {teacher_id}")
            
            # Validate class exists
            from infrastructure.repositories.class_repository import ClassRepository
            class_repo = ClassRepository()
            class_obj = await class_repo.get_by_id(class_id)
            if not class_obj:
                raise NotFoundError(f"Class not found with ID: {class_id}")
            
            # Check if teacher is already assigned to class
            is_assigned = await self.repository.is_assigned_to_class(teacher_id, class_id)
            if is_assigned:
                raise ConflictError(f"Teacher {teacher_id} is already assigned to class {class_id}")
            
            # Check if teacher has expertise in the class subject
            subject_id = class_obj.subject_id  # Assuming subject_id is in class object
            if not await self._has_subject_expertise(teacher_id, subject_id):
                raise ValidationError(f"Teacher {teacher_id} does not have expertise in subject {subject_id}")
            
            # Assign teacher to class
            result = await self.repository.assign_to_class(
                teacher_id=teacher_id,
                class_id=class_id,
                assigned_by_id=assigned_by_id,
                assignment_date=assignment_date or datetime.utcnow()
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to assign teacher {teacher_id} to class {class_id}: {str(e)}")
            raise
    
    async def remove_teacher_from_class(self, teacher_id: str, class_id: str, 
                                      removed_by_id: str = None, removal_date: datetime = None) -> bool:
        """Remove a teacher from a class."""
        try:
            # Validate teacher exists
            teacher = await self.repository.get_by_id(teacher_id)
            if not teacher:
                raise NotFoundError(f"Teacher not found with ID: {teacher_id}")
            
            # Check if teacher is assigned to class
            is_assigned = await self.repository.is_assigned_to_class(teacher_id, class_id)
            if not is_assigned:
                raise NotFoundError(f"Teacher {teacher_id} is not assigned to class {class_id}")
            
            # Remove teacher from class
            result = await self.repository.remove_from_class(
                teacher_id=teacher_id,
                class_id=class_id,
                removed_by_id=removed_by_id,
                removal_date=removal_date or datetime.utcnow()
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to remove teacher {teacher_id} from class {class_id}: {str(e)}")
            raise
    
    async def get_teacher_classes(self, teacher_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all classes assigned to a teacher."""
        try:
            return await self.repository.get_teacher_classes(
                teacher_id=teacher_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get teacher classes for {teacher_id}: {str(e)}")
            raise
    
    # Performance Evaluation
    
    async def submit_performance_evaluation(self, teacher_id: str, evaluation_data: Dict[str, Any]) -> bool:
        """Submit a performance evaluation for a teacher."""
        try:
            # Validate teacher exists
            teacher = await self.repository.get_by_id(teacher_id)
            if not teacher:
                raise NotFoundError(f"Teacher not found with ID: {teacher_id}")
            
            # Validate evaluation data
            await self._validate_evaluation_data(evaluation_data)
            
            # Submit evaluation
            result = await self.repository.submit_performance_evaluation(
                teacher_id=teacher_id,
                **evaluation_data
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to submit performance evaluation for teacher {teacher_id}: {str(e)}")
            raise
    
    async def get_teacher_evaluations(self, teacher_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all performance evaluations for a teacher."""
        try:
            return await self.repository.get_teacher_evaluations(
                teacher_id=teacher_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get teacher evaluations for {teacher_id}: {str(e)}")
            raise
    
    async def get_teacher_performance_summary(self, teacher_id: str, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get teacher performance summary."""
        try:
            return await self.repository.get_teacher_performance_summary(
                teacher_id=teacher_id,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            logger.error(f"Failed to get teacher performance summary for {teacher_id}: {str(e)}")
            raise
    
    # Workload Management
    
    async def calculate_workload(self, teacher_id: str, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Calculate teacher workload."""
        try:
            return await self.repository.calculate_workload(
                teacher_id=teacher_id,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            logger.error(f"Failed to calculate workload for teacher {teacher_id}: {str(e)}")
            raise
    
    async def check_workload_compliance(self, teacher_id: str) -> bool:
        """Check if teacher workload complies with standards."""
        try:
            workload = await self.calculate_workload(teacher_id)
            max_hours = 40  # Maximum standard hours per week
            current_hours = workload.get('total_hours_per_week', 0)
            
            return current_hours <= max_hours
            
        except Exception:
            return False
    
    # Profile Management
    
    async def update_teacher_profile(self, teacher_id: str, profile_data: Dict[str, Any]) -> Optional[User]:
        """Update teacher profile information."""
        try:
            # Validate teacher exists
            teacher = await self.repository.get_by_id(teacher_id)
            if not teacher:
                raise NotFoundError(f"Teacher not found with ID: {teacher_id}")
            
            # Validate profile data
            await self._validate_profile_update(profile_data)
            
            # Update profile
            updated_teacher = await self.repository.update(teacher_id, **profile_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return updated_teacher
            
        except Exception as e:
            logger.error(f"Failed to update teacher profile for {teacher_id}: {str(e)}")
            raise
    
    async def update_teacher_credentials(self, teacher_id: str, current_password: str, new_password: str) -> bool:
        """Update teacher credentials."""
        try:
            # Validate teacher exists
            teacher = await self.repository.get_by_id(teacher_id)
            if not teacher:
                raise NotFoundError(f"Teacher not found with ID: {teacher_id}")
            
            # Validate current password
            if not await self._validate_password(teacher_id, current_password):
                raise ValidationError("Current password is incorrect")
            
            # Validate new password
            await self._validate_password_requirements(new_password)
            
            # Update password
            result = await self.repository.update_password(
                teacher_id=teacher_id,
                new_password=new_password
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update teacher credentials for {teacher_id}: {str(e)}")
            raise
    
    async def update_teacher_qualifications(self, teacher_id: str, qualifications: List[Dict[str, Any]]) -> bool:
        """Update teacher qualifications."""
        try:
            # Validate teacher exists
            teacher = await self.repository.get_by_id(teacher_id)
            if not teacher:
                raise NotFoundError(f"Teacher not found with ID: {teacher_id}")
            
            # Validate qualifications
            await self._validate_qualifications(qualifications)
            
            # Update qualifications
            result = await self.repository.update_qualifications(
                teacher_id=teacher_id,
                qualifications=qualifications
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update teacher qualifications for {teacher_id}: {str(e)}")
            raise
    
    # Analytics and Reports
    
    async def get_teacher_stats(self, teacher_id: str, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get comprehensive teacher statistics."""
        try:
            # Validate teacher exists
            teacher = await self.repository.get_by_id(teacher_id)
            if not teacher:
                raise NotFoundError(f"Teacher not found with ID: {teacher_id}")
            
            # Get classes
            classes = await self.get_teacher_classes(teacher_id)
            total_classes = len(classes)
            active_classes = len([c for c in classes if c.get('assignment_status') == 'active'])
            
            # Get evaluations
            evaluations = await self.get_teacher_evaluations(teacher_id)
            total_evaluations = len(evaluations)
            
            # Calculate performance score
            performance_score = await self._calculate_teacher_performance_score(teacher_id)
            
            # Get workload
            workload = await self.calculate_workload(teacher_id, start_date, end_date)
            
            # Get stats from repository
            stats = await self.repository.get_teacher_stats(teacher_id, start_date, end_date)
            return stats.dict()
            
        except Exception as e:
            logger.error(f"Failed to get teacher stats for {teacher_id}: {str(e)}")
            raise
    
    async def generate_teacher_report(self, teacher_id: str, report_type: str = "performance", 
                                     start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Generate comprehensive teacher report."""
        try:
            # Validate teacher exists
            teacher = await self.repository.get_by_id(teacher_id)
            if not teacher:
                raise NotFoundError(f"Teacher not found with ID: {teacher_id}")
            
            # Generate report based on type
            if report_type == "performance":
                return await self._generate_performance_report(teacher_id, start_date, end_date)
            elif report_type == "workload":
                return await self._generate_workload_report(teacher_id, start_date, end_date)
            elif report_type == "classes":
                return await self._generate_classes_report(teacher_id, start_date, end_date)
            elif report_type == "evaluation":
                return await self._generate_evaluation_report(teacher_id, start_date, end_date)
            else:
                raise ValidationError(f"Unknown report type: {report_type}")
                
        except Exception as e:
            logger.error(f"Failed to generate teacher report for {teacher_id}: {str(e)}")
            raise
    
    # Batch Operations
    
    async def batch_update_teachers(self, updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple teachers."""
        results = {}
        
        for update in updates:
            teacher_id = update['teacher_id']
            try:
                result = await self.update_teacher(teacher_id, update)
                results[teacher_id] = result is not None
            except Exception as e:
                logger.error(f"Failed to update teacher {teacher_id}: {str(e)}")
                results[teacher_id] = False
        
        return results
    
    async def batch_assign_to_classes(self, assignments: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Batch assign teachers to classes."""
        results = {}
        
        for assignment in assignments:
            teacher_id = assignment['teacher_id']
            class_id = assignment['class_id']
            try:
                result = await self.assign_teacher_to_class(teacher_id, class_id)
                results[f"{teacher_id}_{class_id}"] = result
            except Exception as e:
                logger.error(f"Failed to assign teacher {teacher_id} to class {class_id}: {str(e)}")
                results[f"{teacher_id}_{class_id}"] = False
        
        return results
    
    # Helper Methods
    
    async def _validate_teacher_creation(self, data: Dict[str, Any]) -> None:
        """Validate teacher creation data."""
        required_fields = ['name', 'email', 'employee_id', 'date_of_birth', 
                         'gender', 'phone_number', 'address', 'department_id', 
                         'qualification', 'subjects_taught']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate email format
        if not self._validate_email(data['email']):
            raise ValidationError("Invalid email format")
        
        # Validate employee ID format
        if not self._validate_employee_id(data['employee_id']):
            raise ValidationError("Invalid employee ID format")
        
        # Validate phone number format
        if not self._validate_phone_number(data['phone_number']):
            raise ValidationError("Invalid phone number format")
        
        # Validate date of birth
        if not self._validate_date_of_birth(data['date_of_birth']):
            raise ValidationError("Invalid date of birth")
        
        # Validate gender
        if data['gender'] not in ['male', 'female', 'other']:
            raise ValidationError("Invalid gender value")
        
        # Validate password if provided
        if 'password' in data and data['password']:
            await self._validate_password_requirements(data['password'])
    
    async def _validate_teacher_update(self, data: Dict[str, Any]) -> None:
        """Validate teacher update data."""
        allowed_fields = ['name', 'email', 'phone_number', 'address', 'city', 
                         'state', 'postal_code', 'country', 'profile_picture', 
                         'bio', 'skills', 'achievements', 'status']
        
        for field in data.keys():
            if field not in allowed_fields:
                raise ValidationError(f"Cannot update field: {field}")
        
        # Validate email if provided
        if 'email' in data and data['email']:
            if not self._validate_email(data['email']):
                raise ValidationError("Invalid email format")
        
        # Validate phone numbers if provided
        if 'phone_number' in data and data['phone_number']:
            if not self._validate_phone_number(data['phone_number']):
                raise ValidationError("Invalid phone number format")
        
        # Validate date of birth if provided
        if 'date_of_birth' in data and data['date_of_birth']:
            if not self._validate_date_of_birth(data['date_of_birth']):
                raise ValidationError("Invalid date of birth")
        
        # Validate gender if provided
        if 'gender' in data and data['gender']:
            if data['gender'] not in ['male', 'female', 'other']:
                raise ValidationError("Invalid gender value")
        
        # Validate password if provided
        if 'password' in data and data['password']:
            await self._validate_password_requirements(data['password'])
    
    async def _validate_profile_update(self, data: Dict[str, Any]) -> None:
        """Validate profile update data."""
        allowed_fields = ['name', 'date_of_birth', 'gender', 'profile_picture', 
                         'bio', 'skills', 'achievements', 'status']
        
        for field in data.keys():
            if field not in allowed_fields:
                raise ValidationError(f"Cannot update field: {field}")
        
        # Validate date of birth if provided
        if 'date_of_birth' in data and data['date_of_birth']:
            if not self._validate_date_of_birth(data['date_of_birth']):
                raise ValidationError("Invalid date of birth")
        
        # Validate gender if provided
        if 'gender' in data and data['gender']:
            if data['gender'] not in ['male', 'female', 'other']:
                raise ValidationError("Invalid gender value")
    
    async def _validate_evaluation_data(self, data: Dict[str, Any]) -> None:
        """Validate evaluation data."""
        required_fields = ['evaluator_id', 'evaluation_type', 'score', 'comments']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate score range
        if not (0 <= data['score'] <= 100):
            raise ValidationError("Score must be between 0 and 100")
        
        # Validate evaluation type
        valid_types = ['teaching', 'research', 'service', 'overall']
        if data['evaluation_type'] not in valid_types:
            raise ValidationError(f"Invalid evaluation type. Must be one of: {valid_types}")
    
    async def _validate_qualifications(self, qualifications: List[Dict[str, Any]]) -> None:
        """Validate qualifications list."""
        for qual in qualifications:
            required_fields = ['qualification_name', 'institution', 'year', 'level']
            
            for field in required_fields:
                if field not in qual or not qual[field]:
                    raise ValidationError(f"Required qualification field '{field}' is missing or empty")
            
            # Validate level
            valid_levels = ['certificate', 'diploma', 'degree', 'master', 'phd', 'other']
            if qual['level'] not in valid_levels:
                raise ValidationError(f"Invalid qualification level: {qual['level']}")
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_employee_id(self, employee_id: str) -> bool:
        """Validate employee ID format."""
        # Basic validation - alphanumeric with specific format
        import re
        pattern = r'^EMP[0-9]{3}$'  # Example: EMP001
        return re.match(pattern, employee_id) is not None
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format."""
        # Basic validation - numeric with international format
        import re
        pattern = r'^\+[0-9]{1,3}\-[0-9]{4,15}$'  # Example: +1-1234567890
        return re.match(pattern, phone_number) is not None
    
    def _validate_date_of_birth(self, date_of_birth) -> bool:
        """Validate date of birth."""
        try:
            if isinstance(date_of_birth, str):
                datetime.strptime(date_of_birth, '%Y-%m-%d')
            elif isinstance(date_of_birth, datetime):
                pass  # Valid datetime object
            else:
                return False
            
            # Check if date is not in the future
            if isinstance(date_of_birth, str):
                dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
            else:
                dob = date_of_birth
            
            return dob <= datetime.utcnow()
        except Exception:
            return False
    
    async def _validate_password_requirements(self, password: str) -> None:
        """Validate password requirements."""
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            raise ValidationError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            raise ValidationError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain at least one digit")
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            raise ValidationError("Password must contain at least one special character")
    
    async def _validate_password(self, teacher_id: str, password: str) -> bool:
        """Validate teacher password."""
        # This would hash the password and compare with stored hash
        # For now, return True (should be implemented properly)
        return True
    
    async def _has_active_classes(self, teacher_id: str) -> bool:
        """Check if teacher has active classes."""
        classes = await self.get_teacher_classes(teacher_id)
        return any(c.get('assignment_status') == 'active' for c in classes)
    
    async def _has_assigned_students(self, teacher_id: str) -> bool:
        """Check if teacher has assigned students."""
        # This would check enrollment records
        # For now, return False (should be implemented)
        return False
    
    async def _has_subject_expertise(self, teacher_id: str, subject_id: str) -> bool:
        """Check if teacher has expertise in a subject."""
        subjects = await self.get_teacher_subjects(teacher_id)
        return any(s['subject_id'] == subject_id for s in subjects)
    
    async def _calculate_teacher_performance_score(self, teacher_id: str) -> float:
        """Calculate teacher performance score."""
        try:
            evaluations = await self.get_teacher_evaluations(teacher_id)
            if not evaluations:
                return 0.0
            
            # Calculate weighted average score
            total_score = sum(eval['score'] for eval in evaluations)
            return total_score / len(evaluations)
            
        except Exception:
            return 0.0
    
    def _get_compliance_status(self, teacher_id: str) -> str:
        """Get teacher compliance status."""
        # This would check various compliance metrics
        # For now, return "compliant" (should be implemented)
        return "compliant"
    
    async def _generate_performance_report(self, teacher_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate performance report for teacher."""
        try:
            teacher = await self.get_teacher(teacher_id)
            stats = await self.get_teacher_stats(teacher_id, start_date, end_date)
            evaluations = await self.get_teacher_evaluations(teacher_id)
            classes = await self.get_teacher_classes(teacher_id, 0, 100)
            
            return {
                "teacher": teacher.to_dict() if teacher else None,
                "statistics": stats.to_dict() if stats else None,
                "evaluations": evaluations,
                "classes": classes,
                "performance_trend": self._analyze_performance_trend(evaluations),
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "performance"
            }
        except Exception as e:
            logger.error(f"Failed to generate performance report for {teacher_id}: {str(e)}")
            raise
    
    async def _generate_workload_report(self, teacher_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate workload report for teacher."""
        try:
            teacher = await self.get_teacher(teacher_id)
            workload = await self.calculate_workload(teacher_id, start_date, end_date)
            classes = await self.get_teacher_classes(teacher_id, 0, 100)
            
            return {
                "teacher": teacher.to_dict() if teacher else None,
                "workload": workload,
                "classes": classes,
                "workload_compliance": await self.check_workload_compliance(teacher_id),
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "workload"
            }
        except Exception as e:
            logger.error(f"Failed to generate workload report for {teacher_id}: {str(e)}")
            raise
    
    async def _generate_classes_report(self, teacher_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate classes report for teacher."""
        try:
            teacher = await self.get_teacher(teacher_id)
            classes = await self.get_teacher_classes(teacher_id, 0, 100)
            workload = await self.calculate_workload(teacher_id, start_date, end_date)
            
            return {
                "teacher": teacher.to_dict() if teacher else None,
                "classes": classes,
                "workload": workload,
                "class_distribution": self._analyze_class_distribution(classes),
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "classes"
            }
        except Exception as e:
            logger.error(f"Failed to generate classes report for {teacher_id}: {str(e)}")
            raise
    
    async def _generate_evaluation_report(self, teacher_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate evaluation report for teacher."""
        try:
            teacher = await self.get_teacher(teacher_id)
            evaluations = await self.get_teacher_evaluations(teacher_id)
            summary = await self.get_teacher_performance_summary(teacher_id, start_date, end_date)
            
            return {
                "teacher": teacher.to_dict() if teacher else None,
                "evaluations": evaluations,
                "summary": summary,
                "evaluation_trend": self._analyze_evaluation_trend(evaluations),
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "evaluation"
            }
        except Exception as e:
            logger.error(f"Failed to generate evaluation report for {teacher_id}: {str(e)}")
            raise
    
    def _analyze_performance_trend(self, evaluations: List[Dict[str, Any]]) -> str:
        """Analyze teacher performance trend."""
        if not evaluations:
            return "No data"
        
        # Sort by date
        sorted_evals = sorted(evaluuations, key=lambda x: x.get('created_at', datetime.min))
        
        # Calculate trend
        scores = [eval['score'] for eval in sorted_evals]
        if len(scores) >= 2:
            if scores[-1] > scores[0] + 10:
                return "Improving"
            elif scores[-1] < scores[0] - 10:
                return "Declining"
            else:
                return "Stable"
        else:
            return "Insufficient data"
    
    def _analyze_class_distribution(self, classes: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze class distribution by subject/level."""
        distribution = {}
        
        for cls in classes:
            subject = cls.get('subject_name', 'Unknown')
            level = cls.get('level', 'Unknown')
            
            key = f"{subject}_{level}"
            distribution[key] = distribution.get(key, 0) + 1
        
        return distribution
    
    def _analyze_evaluation_trend(self, evaluations: List[Dict[str, Any]]) -> str:
        """Analyze evaluation trend."""
        if not evaluations:
            return "No data"
        
        # Sort by date
        sorted_evals = sorted(evaluations, key=lambda x: x.get('created_at', datetime.min))
        
        # Calculate trend
        scores = [eval['score'] for eval in sorted_evals]
        if len(scores) >= 2:
            if scores[-1] > scores[0] + 10:
                return "Improving"
            elif scores[-1] < scores[0] - 10:
                return "Declining"
            else:
                return "Stable"
        else:
            return "Insufficient data"
    
    async def _invalidate_cache(self) -> None:
        """Invalidate teacher cache."""
        self._cache.clear()
    
    # Abstract method implementations required by BaseService
    
    async def create(self, data: Dict) -> Dict:
        """Create a new teacher entity."""
        # Reuse existing method
        teacher = await self.create_teacher(data)
        return teacher.dict()
    
    async def get(self, id: str) -> Optional[Dict]:
        """Get a teacher entity by ID."""
        teacher = await self.get_teacher(id)
        return teacher.dict() if teacher else None
    
    async def update(self, id: str, data: Dict) -> Dict:
        """Update a teacher entity by ID."""
        teacher = await self.update_teacher(id, data)
        return teacher.dict()
    
    async def delete(self, id: str) -> bool:
        """Delete a teacher entity by ID."""
        return await self.delete_teacher(id)
    
    async def list(self, skip: int = 0, limit: int = 100, filters: Dict = None) -> List[Dict]:
        """List all teacher entities."""
        teachers = await self.repository.get_all(skip=skip, limit=limit)
        return [teacher.dict() for teacher in teachers]
    
    async def count(self, filters: Dict = None) -> int:
        """Count total number of teacher entities."""
        return await self.repository.count()