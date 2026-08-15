"""
Class Management Service

This module provides business logic for class management:
- Class creation and management
- Student enrollment and management
- Class scheduling and timetabling
- Class analytics and reporting
- Attendance tracking
- Performance monitoring

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, time, timedelta
from uuid import uuid4

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.core.logging import get_logger
from src.core.base_service import BaseService
from src.infrastructure.repositories.class_repository import ClassRepository
from src.models.class_model import ClassCreate, ClassUpdate, ClassResponse, ClassStats, AttendanceRecord

logger = get_logger(__name__)


class ClassService(BaseService):
    """Class management service with comprehensive functionality."""
    
    def __init__(self, class_repository: ClassRepository):
        super().__init__(class_repository)
        self._cache = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the class service."""
        try:
            self._initialized = True
            logger.info("Class service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize class service: {str(e)}")
            raise
    
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized
    
    async def dispose(self) -> None:
        """Dispose the class service."""
        try:
            self._cache.clear()
            logger.info("Class service disposed successfully")
        except Exception as e:
            logger.error(f"Failed to dispose class service: {str(e)}")
            raise
    
    # Core Business Operations
    
    async def create_class(self, class_data: Dict[str, Any]) -> ClassResponse:
        """Create a new class with business logic validation."""
        try:
            # Validate class data
            await self._validate_class_creation(class_data)
            
            # Check if class already exists
            existing_class = await self.class_repository.get_by_code(class_data['class_code'])
            if existing_class:
                raise ConflictError(f"Class with code {class_data['class_code']} already exists")
            
            # Create class
            class_obj = await self.class_repository.create(**class_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return class_obj
            
        except Exception as e:
            logger.error(f"Failed to create class: {str(e)}")
            raise
    
    async def update_class(self, class_id: str, class_data: Dict[str, Any]) -> Optional[ClassResponse]:
        """Update an existing class with business logic."""
        try:
            # Validate class exists
            class_obj = await self.class_repository.get_by_id(class_id)
            if not class_obj:
                raise NotFoundError(f"Class not found with ID: {class_id}")
            
            # Validate update data
            await self._validate_class_update(class_data)
            
            # Check for code conflicts if class_code is being updated
            if 'class_code' in class_data and class_data['class_code'] != class_obj.class_code:
                existing_class = await self.class_repository.get_by_code(class_data['class_code'])
                if existing_class:
                    raise ConflictError(f"Class with code {class_data['class_code']} already exists")
            
            # Update class
            updated_class = await self.class_repository.update(class_id, **class_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return updated_class
            
        except Exception as e:
            logger.error(f"Failed to update class {class_id}: {str(e)}")
            raise
    
    async def get_class(self, class_id: str) -> Optional[ClassResponse]:
        """Get a class by ID with caching."""
        try:
            # Check cache first
            if class_id in self._cache:
                return self._cache[class_id]
            
            # Get class from repository
            class_obj = await self.class_repository.get_by_id(class_id)
            
            if class_obj:
                # Cache the result
                self._cache[class_id] = class_obj
            
            return class_obj
            
        except Exception as e:
            logger.error(f"Failed to get class {class_id}: {str(e)}")
            raise
    
    async def get_class_by_code(self, class_code: str) -> Optional[ClassResponse]:
        """Get a class by class code."""
        try:
            return await self.class_repository.get_by_code(class_code)
        except Exception as e:
            logger.error(f"Failed to get class by code {class_code}: {str(e)}")
            raise
    
    async def delete_class(self, class_id: str) -> bool:
        """Delete a class with business logic."""
        try:
            # Validate class exists
            class_obj = await self.class_repository.get_by_id(class_id)
            if not class_obj:
                raise NotFoundError(f"Class not found with ID: {class_id}")
            
            # Check if class has active enrollments
            has_active_enrollments = await self._has_active_enrollments(class_id)
            if has_active_enrollments:
                raise ValidationError("Cannot delete class with active enrollments")
            
            # Check if class has scheduled timetables
            has_schedules = await self._has_schedules(class_id)
            if has_schedules:
                raise ValidationError("Cannot delete class with scheduled timetables")
            
            # Delete class
            result = await self.class_repository.delete(class_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete class {class_id}: {str(e)}")
            raise
    
    # Search and Filtering
    
    async def search_classes(self, search_term: str, skip: int = 0, limit: int = 100) -> List[ClassResponse]:
        """Search for classes by name, code, or description."""
        try:
            classes = await self.class_repository.search_classes(
                search_term=search_term,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for cls in classes:
                self._cache[cls.id] = cls
            
            return classes
            
        except Exception as e:
            logger.error(f"Failed to search classes: {str(e)}")
            raise
    
    async def get_classes_by_department(self, department_id: str, skip: int = 0, limit: int = 100) -> List[ClassResponse]:
        """Get classes by department."""
        try:
            classes = await self.class_repository.get_by_department(
                department_id=department_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for cls in classes:
                self._cache[cls.id] = cls
            
            return classes
            
        except Exception as e:
            logger.error(f"Failed to get classes by department: {str(e)}")
            raise
    
    async def get_classes_by_subject(self, subject_id: str, skip: int = 0, limit: int = 100) -> List[ClassResponse]:
        """Get classes by subject."""
        try:
            classes = await self.class_repository.get_by_subject(
                subject_id=subject_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for cls in classes:
                self._cache[cls.id] = cls
            
            return classes
            
        except Exception as e:
            logger.error(f"Failed to get classes by subject: {str(e)}")
            raise
    
    async def get_classes_by_teacher(self, teacher_id: str, skip: int = 0, limit: int = 100) -> List[ClassResponse]:
        """Get classes by teacher."""
        try:
            classes = await self.class_repository.get_by_teacher(
                teacher_id=teacher_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for cls in classes:
                self._cache[cls.id] = cls
            
            return classes
            
        except Exception as e:
            logger.error(f"Failed to get classes by teacher: {str(e)}")
            raise
    
    async def get_classes_by_semester(self, semester: str, academic_year: str, skip: int = 0, limit: int = 100) -> List[ClassResponse]:
        """Get classes by semester and academic year."""
        try:
            classes = await self.class_repository.get_by_semester(
                semester=semester,
                academic_year=academic_year,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for cls in classes:
                self._cache[cls.id] = cls
            
            return classes
            
        except Exception as e:
            logger.error(f"Failed to get classes by semester: {str(e)}")
            raise
    
    # Student Management
    
    async def enroll_student(self, class_id: str, student_id: str, enrollment_date: datetime = None) -> bool:
        """Enroll a student in a class."""
        try:
            # Validate class exists
            class_obj = await self.class_repository.get_by_id(class_id)
            if not class_obj:
                raise NotFoundError(f"Class not found with ID: {class_id}")
            
            # Validate student exists
            from src.infrastructure.repositories.student_repository import StudentRepository
            student_repo = StudentRepository()
            student = await student_repo.get_by_id(student_id)
            if not student:
                raise NotFoundError(f"Student not found with ID: {student_id}")
            
            # Check if student is already enrolled
            is_enrolled = await self.class_repository.is_student_enrolled(student_id, class_id)
            if is_enrolled:
                raise ConflictError(f"Student {student_id} is already enrolled in class {class_id}")
            
            # Check class capacity
            if not await self._check_class_capacity(class_id):
                raise ValidationError(f"Class {class_id} is full")
            
            # Enroll student
            result = await self.class_repository.enroll_student(
                class_id=class_id,
                student_id=student_id,
                enrollment_date=enrollment_date or datetime.utcnow()
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to enroll student {student_id} in class {class_id}: {str(e)}")
            raise
    
    async def unenroll_student(self, class_id: str, student_id: str, unenrollment_date: datetime = None) -> bool:
        """Unenroll a student from a class."""
        try:
            # Validate class exists
            class_obj = await self.class_repository.get_by_id(class_id)
            if not class_obj:
                raise NotFoundError(f"Class not found with ID: {class_id}")
            
            # Check if student is enrolled
            is_enrolled = await self.class_repository.is_student_enrolled(student_id, class_id)
            if not is_enrolled:
                raise NotFoundError(f"Student {student_id} is not enrolled in class {class_id}")
            
            # Unenroll student
            result = await self.class_repository.unenroll_student(
                class_id=class_id,
                student_id=student_id,
                unenrollment_date=unenrollment_date or datetime.utcnow()
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to unenroll student {student_id} from class {class_id}: {str(e)}")
            raise
    
    async def get_class_students(self, class_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all students enrolled in a class."""
        try:
            return await self.class_repository.get_class_students(
                class_id=class_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get class students for {class_id}: {str(e)}")
            raise
    
    async def get_student_classes(self, student_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all classes a student is enrolled in."""
        try:
            return await self.class_repository.get_student_classes(
                student_id=student_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get student classes for {student_id}: {str(e)}")
            raise
    
    # Attendance Management
    
    async def mark_attendance(self, class_id: str, attendance_records: List[Dict[str, Any]]) -> bool:
        """Mark attendance for a class session."""
        try:
            # Validate class exists
            class_obj = await self.class_repository.get_by_id(class_id)
            if not class_obj:
                raise NotFoundError(f"Class not found with ID: {class_id}")
            
            # Validate attendance records
            await self._validate_attendance_records(attendance_records)
            
            # Mark attendance
            result = await self.class_repository.mark_attendance(
                class_id=class_id,
                attendance_records=attendance_records
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to mark attendance for class {class_id}: {str(e)}")
            raise
    
    async def get_class_attendance(self, class_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get attendance records for a class."""
        try:
            return await self.class_repository.get_class_attendance(
                class_id=class_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get class attendance for {class_id}: {str(e)}")
            raise
    
    async def get_student_class_attendance(self, student_id: str, class_id: str) -> List[Dict[str, Any]]:
        """Get attendance records for a specific student in a class."""
        try:
            return await self.class_repository.get_student_class_attendance(
                student_id=student_id,
                class_id=class_id
            )
        except Exception as e:
            logger.error(f"Failed to get student attendance for {student_id} in class {class_id}: {str(e)}")
            raise
    
    async def calculate_attendance_stats(self, class_id: str) -> Dict[str, float]:
        """Calculate attendance statistics for a class."""
        try:
            return await self.class_repository.calculate_attendance_stats(class_id)
        except Exception as e:
            logger.error(f"Failed to calculate attendance stats for class {class_id}: {str(e)}")
            raise
    
    # Schedule Management
    
    async def schedule_class_session(self, class_id: str, session_data: Dict[str, Any]) -> bool:
        """Schedule a class session."""
        try:
            # Validate class exists
            class_obj = await self.class_repository.get_by_id(class_id)
            if not class_obj:
                raise NotFoundError(f"Class not found with ID: {class_id}")
            
            # Validate session data
            await self._validate_session_data(session_data)
            
            # Check for conflicts
            if await self._check_session_conflicts(class_id, session_data):
                raise ConflictError("Session time conflicts with existing schedules")
            
            # Schedule session
            result = await self.class_repository.schedule_class_session(
                class_id=class_id,
                **session_data
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to schedule session for class {class_id}: {str(e)}")
            raise
    
    async def update_class_session(self, class_id: str, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Update a class session."""
        try:
            # Validate class exists
            class_obj = await self.class_repository.get_by_id(class_id)
            if not class_obj:
                raise NotFoundError(f"Class not found with ID: {class_id}")
            
            # Validate session data
            await self._validate_session_data(session_data)
            
            # Check for conflicts
            if await self._check_session_conflicts(class_id, session_data, session_id):
                raise ConflictError("Updated session time conflicts with existing schedules")
            
            # Update session
            result = await self.class_repository.update_class_session(
                class_id=class_id,
                session_id=session_id,
                **session_data
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update session for class {class_id}: {str(e)}")
            raise
    
    async def cancel_class_session(self, class_id: str, session_id: str, cancellation_reason: str = None) -> bool:
        """Cancel a class session."""
        try:
            # Validate class exists
            class_obj = await self.class_repository.get_by_id(class_id)
            if not class_obj:
                raise NotFoundError(f"Class not found with ID: {class_id}")
            
            # Cancel session
            result = await self.class_repository.cancel_class_session(
                class_id=class_id,
                session_id=session_id,
                cancellation_reason=cancellation_reason
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to cancel session for class {class_id}: {str(e)}")
            raise
    
    async def get_class_sessions(self, class_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all sessions for a class."""
        try:
            return await self.class_repository.get_class_sessions(
                class_id=class_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get class sessions for {class_id}: {str(e)}")
            raise
    
    async def get_class_schedule(self, class_id: str, start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        """Get class schedule for a date range."""
        try:
            return await self.class_repository.get_class_schedule(
                class_id=class_id,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            logger.error(f"Failed to get class schedule for {class_id}: {str(e)}")
            raise
    
    # Performance Management
    
    async def submit_grade(self, class_id: str, grade_data: Dict[str, Any]) -> bool:
        """Submit grades for a class."""
        try:
            # Validate class exists
            class_obj = await self.class_repository.get_by_id(class_id)
            if not class_obj:
                raise NotFoundError(f"Class not found with ID: {class_id}")
            
            # Validate grade data
            await self._validate_grade_data(grade_data)
            
            # Submit grade
            result = await self.class_repository.submit_grade(
                class_id=class_id,
                **grade_data
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to submit grade for class {class_id}: {str(e)}")
            raise
    
    async def get_class_grades(self, class_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get grades for a class."""
        try:
            return await self.class_repository.get_class_grades(
                class_id=class_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get class grades for {class_id}: {str(e)}")
            raise
    
    async def get_student_class_grade(self, student_id: str, class_id: str) -> Optional[Dict[str, Any]]:
        """Get grade for a specific student in a class."""
        try:
            return await self.class_repository.get_student_class_grade(
                student_id=student_id,
                class_id=class_id
            )
        except Exception as e:
            logger.error(f"Failed to get student grade for {student_id} in class {class_id}: {str(e)}")
            raise
    
    async def calculate_class_performance(self, class_id: str) -> Dict[str, float]:
        """Calculate class performance statistics."""
        try:
            return await self.class_repository.calculate_class_performance(class_id)
        except Exception as e:
            logger.error(f"Failed to calculate class performance for {class_id}: {str(e)}")
            raise
    
    # Analytics and Reporting
    
    async def get_class_stats(self, class_id: str) -> ClassStats:
        """Get comprehensive class statistics."""
        try:
            # Validate class exists
            class_obj = await self.class_repository.get_by_id(class_id)
            if not class_obj:
                raise NotFoundError(f"Class not found with ID: {class_id}")
            
            # Get students
            students = await self.get_class_students(class_id)
            total_students = len(students)
            active_students = len([s for s in students if s.get('enrollment_status') == 'active'])
            
            # Get attendance
            attendance = await self.get_class_attendance(class_id)
            total_attendance = len(attendance)
            present_count = len([a for a in attendance if a.get('status') == 'present'])
            attendance_rate = (present_count / total_attendance * 100) if total_attendance > 0 else 0
            
            # Get grades
            grades = await self.get_class_grades(class_id)
            total_grades = len(grades)
            
            # Calculate performance
            performance = await self.calculate_class_performance(class_id)
            
            # Create stats object
            stats = ClassStats(
                class_id=class_id,
                class_name=class_obj.name,
                class_code=class_obj.class_code,
                total_students=total_students,
                active_students=active_students,
                total_attendance=total_attendance,
                attendance_rate=round(attendance_rate, 2),
                total_grades=total_grades,
                average_grade=performance.get('average_grade', 0),
                grade_distribution=performance.get('grade_distribution', {}),
                last_attendance_date=attendance[-1]['date'] if attendance else None,
                last_grade_date=grades[-1]['created_at'] if grades else None,
                completion_rate=performance.get('completion_rate', 0)
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get class stats for {class_id}: {str(e)}")
            raise
    
    async def generate_class_report(self, class_id: str, report_type: str = "attendance", 
                                  start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Generate comprehensive class report."""
        try:
            # Validate class exists
            class_obj = await self.class_repository.get_by_id(class_id)
            if not class_obj:
                raise NotFoundError(f"Class not found with ID: {class_id}")
            
            # Generate report based on type
            if report_type == "attendance":
                return await self._generate_attendance_report(class_id, start_date, end_date)
            elif report_type == "performance":
                return await self._generate_performance_report(class_id, start_date, end_date)
            elif report_type == "enrollment":
                return await self._generate_enrollment_report(class_id, start_date, end_date)
            elif report_type == "schedule":
                return await self._generate_schedule_report(class_id, start_date, end_date)
            else:
                raise ValidationError(f"Unknown report type: {report_type}")
                
        except Exception as e:
            logger.error(f"Failed to generate class report for {class_id}: {str(e)}")
            raise
    
    # Batch Operations
    
    async def batch_enroll_students(self, class_id: str, student_ids: List[str], 
                                  enrollment_date: datetime = None) -> Dict[str, bool]:
        """Enroll multiple students in a class."""
        results = {}
        
        for student_id in student_ids:
            try:
                result = await self.enroll_student(class_id, student_id, enrollment_date)
                results[student_id] = result
            except Exception as e:
                logger.error(f"Failed to enroll student {student_id} in class {class_id}: {str(e)}")
                results[student_id] = False
        
        return results
    
    async def batch_unenroll_students(self, class_id: str, student_ids: List[str], 
                                    unenrollment_date: datetime = None) -> Dict[str, bool]:
        """Unenroll multiple students from a class."""
        results = {}
        
        for student_id in student_ids:
            try:
                result = await self.unenroll_student(class_id, student_id, unenrollment_date)
                results[student_id] = result
            except Exception as e:
                logger.error(f"Failed to unenroll student {student_id} from class {class_id}: {str(e)}")
                results[student_id] = False
        
        return results
    
    async def batch_update_classes(self, updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple classes."""
        results = {}
        
        for update in updates:
            class_id = update['class_id']
            try:
                result = await self.update_class(class_id, update)
                results[class_id] = result is not None
            except Exception as e:
                logger.error(f"Failed to update class {class_id}: {str(e)}")
                results[class_id] = False
        
        return results
    
    # Helper Methods
    
    async def _validate_class_creation(self, data: Dict[str, Any]) -> None:
        """Validate class creation data."""
        required_fields = ['name', 'class_code', 'description', 'subject_id', 'teacher_id', 
                         'department_id', 'semester', 'academic_year', 'capacity']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate class code format
        if not self._validate_class_code(data['class_code']):
            raise ValidationError("Invalid class code format")
        
        # Validate capacity
        if not (1 <= data['capacity'] <= 500):
            raise ValidationError("Capacity must be between 1 and 500")
        
        # Validate semester
        valid_semesters = ['fall', 'spring', 'summer']
        if data['semester'] not in valid_semesters:
            raise ValidationError(f"Invalid semester. Must be one of: {valid_semesters}")
        
        # Validate academic year format
        if not self._validate_academic_year(data['academic_year']):
            raise ValidationError("Invalid academic year format")
        
        # Validate teacher exists
        from src.infrastructure.repositories.teacher_repository import TeacherRepository
        teacher_repo = TeacherRepository()
        teacher = await teacher_repo.get_by_id(data['teacher_id'])
        if not teacher:
            raise NotFoundError(f"Teacher not found with ID: {data['teacher_id']}")
        
        # Validate subject exists
        from src.infrastructure.repositories.subject_repository import SubjectRepository
        subject_repo = SubjectRepository()
        subject = await subject_repo.get_by_id(data['subject_id'])
        if not subject:
            raise NotFoundError(f"Subject not found with ID: {data['subject_id']}")
        
        # Validate department exists
        from src.infrastructure.repositories.department_repository import DepartmentRepository
        dept_repo = DepartmentRepository()
        department = await dept_repo.get_by_id(data['department_id'])
        if not department:
            raise NotFoundError(f"Department not found with ID: {data['department_id']}")
    
    async def _validate_class_update(self, data: Dict[str, Any]) -> None:
        """Validate class update data."""
        allowed_fields = ['name', 'description', 'capacity', 'status', 'syllabus', 'materials']
        
        for field in data.keys():
            if field not in allowed_fields:
                raise ValidationError(f"Cannot update field: {field}")
        
        # Validate capacity if provided
        if 'capacity' in data and data['capacity']:
            if not (1 <= data['capacity'] <= 500):
                raise ValidationError("Capacity must be between 1 and 500")
        
        # Validate status if provided
        if 'status' in data and data['status']:
            valid_statuses = ['active', 'inactive', 'completed', 'cancelled']
            if data['status'] not in valid_statuses:
                raise ValidationError(f"Invalid status. Must be one of: {valid_statuses}")
    
    async def _validate_attendance_records(self, records: List[Dict[str, Any]]) -> None:
        """Validate attendance records."""
        for record in records:
            required_fields = ['student_id', 'status', 'date', 'marked_by']
            
            for field in required_fields:
                if field not in record or not record[field]:
                    raise ValidationError(f"Required attendance field '{field}' is missing or empty")
            
            # Validate status
            valid_statuses = ['present', 'absent', 'late', 'excused']
            if record['status'] not in valid_statuses:
                raise ValidationError(f"Invalid attendance status: {record['status']}")
    
    async def _validate_session_data(self, data: Dict[str, Any]) -> None:
        """Validate session data."""
        required_fields = ['date', 'start_time', 'end_time', 'session_type', 'location']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required session field '{field}' is missing or empty")
        
        # Validate time format
        if not self._validate_time_format(data['start_time']):
            raise ValidationError("Invalid start time format")
        
        if not self._validate_time_format(data['end_time']):
            raise ValidationError("Invalid end time format")
        
        # Validate session type
        valid_types = ['lecture', 'lab', 'seminar', 'exam', 'workshop']
        if data['session_type'] not in valid_types:
            raise ValidationError(f"Invalid session type. Must be one of: {valid_types}")
    
    async def _validate_grade_data(self, data: Dict[str, Any]) -> None:
        """Validate grade data."""
        required_fields = ['student_id', 'grade', 'grade_type', 'graded_by', 'graded_date']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required grade field '{field}' is missing or empty")
        
        # Validate grade
        if not self._validate_grade_format(data['grade']):
            raise ValidationError("Invalid grade format")
        
        # Validate grade type
        valid_types = ['assignment', 'quiz', 'exam', 'participation', 'project']
        if data['grade_type'] not in valid_types:
            raise ValidationError(f"Invalid grade type. Must be one of: {valid_types}")
    
    def _validate_class_code(self, class_code: str) -> bool:
        """Validate class code format."""
        import re
        pattern = r'^[A-Z]{2}[0-9]{4}$'  # Example: CS1010
        return re.match(pattern, class_code) is not None
    
    def _validate_academic_year(self, academic_year: str) -> bool:
        """Validate academic year format."""
        import re
        pattern = r'^20[0-9]{2}-20[0-9]{2}$'  # Example: 2023-2024
        return re.match(pattern, academic_year) is not None
    
    def _validate_time_format(self, time_str: str) -> bool:
        """Validate time format."""
        try:
            datetime.strptime(time_str, '%H:%M')
            return True
        except ValueError:
            return False
    
    def _validate_grade_format(self, grade: str) -> bool:
        """Validate grade format."""
        import re
        # Accepts letter grades with optional modifiers (A+, A, A-, B+, etc.)
        pattern = r'^[A-F][+-]?$|^[A-F]$'
        return re.match(pattern, grade) is not None
    
    async def _has_active_enrollments(self, class_id: str) -> bool:
        """Check if class has active enrollments."""
        students = await self.get_class_students(class_id)
        return any(s.get('enrollment_status') == 'active' for s in students)
    
    async def _has_schedules(self, class_id: str) -> bool:
        """Check if class has scheduled sessions."""
        sessions = await self.get_class_sessions(class_id)
        return len(sessions) > 0
    
    async def _check_class_capacity(self, class_id: str) -> bool:
        """Check if class has capacity for more students."""
        students = await self.get_class_students(class_id)
        class_obj = await self.get_class(class_id)
        
        if not class_obj or not class_obj.capacity:
            return True
        
        return len(students) < class_obj.capacity
    
    async def _check_session_conflicts(self, class_id: str, session_data: Dict[str, Any], 
                                     exclude_session_id: str = None) -> bool:
        """Check for session conflicts."""
        # This would check against existing sessions for conflicts
        # For now, return False (should be implemented)
        return False
    
    async def _generate_attendance_report(self, class_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate attendance report for class."""
        try:
            class_obj = await self.get_class(class_id)
            attendance = await self.get_class_attendance(class_id)
            
            # Filter by date range
            filtered_attendance = [
                a for a in attendance 
                if start_date <= a['date'] <= end_date
            ]
            
            # Calculate attendance summary
            total_sessions = len(filtered_attendance)
            present_count = len([a for a in filtered_attendance if a['status'] == 'present'])
            
            return {
                "class": class_obj.to_dict() if class_obj else None,
                "attendance": filtered_attendance,
                "summary": {
                    "total_sessions": total_sessions,
                    "present_sessions": present_count,
                    "attendance_rate": round((present_count / total_sessions) * 100, 2) if total_sessions > 0 else 0,
                    "absent_count": len([a for a in filtered_attendance if a['status'] == 'absent']),
                    "late_count": len([a for a in filtered_attendance if a['status'] == 'late']),
                    "excused_count": len([a for a in filtered_attendance if a['status'] == 'excused'])
                },
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "attendance"
            }
        except Exception as e:
            logger.error(f"Failed to generate attendance report for {class_id}: {str(e)}")
            raise
    
    async def _generate_performance_report(self, class_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate performance report for class."""
        try:
            class_obj = await self.get_class(class_id)
            grades = await self.get_class_grades(class_id)
            performance = await self.calculate_class_performance(class_id)
            
            # Filter by date range
            from datetime import datetime
            filtered_grades = [
                g for g in grades 
                if datetime.strptime(g['created_at'], '%Y-%m-%d %H:%M:%S').date() >= (start_date or datetime.min.date())
                and datetime.strptime(g['created_at'], '%Y-%m-%d %H:%M:%S').date() <= (end_date or datetime.max.date())
            ]
            
            return {
                "class": class_obj.to_dict() if class_obj else None,
                "grades": filtered_grades,
                "performance": performance,
                "summary": {
                    "total_grades": len(filtered_grades),
                    "average_grade": performance.get('average_grade', 0),
                    "grade_distribution": performance.get('grade_distribution', {}),
                    "highest_grade": performance.get('highest_grade', ''),
                    "lowest_grade": performance.get('lowest_grade', ''),
                    "grade_trend": self._analyze_grade_trend(filtered_grades)
                },
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "performance"
            }
        except Exception as e:
            logger.error(f"Failed to generate performance report for {class_id}: {str(e)}")
            raise
    
    async def _generate_enrollment_report(self, class_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate enrollment report for class."""
        try:
            class_obj = await self.get_class(class_id)
            students = await self.get_class_students(class_id)
            
            # Calculate enrollment summary
            total_students = len(students)
            active_students = len([s for s in students if s.get('enrollment_status') == 'active'])
            dropped_students = len([s for s in students if s.get('enrollment_status') == 'dropped'])
            
            return {
                "class": class_obj.to_dict() if class_obj else None,
                "students": students,
                "summary": {
                    "total_students": total_students,
                    "active_students": active_students,
                    "dropped_students": dropped_students,
                    "retention_rate": round((active_students / total_students) * 100, 2) if total_students > 0 else 0
                },
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "enrollment"
            }
        except Exception as e:
            logger.error(f"Failed to generate enrollment report for {class_id}: {str(e)}")
            raise
    
    async def _generate_schedule_report(self, class_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate schedule report for class."""
        try:
            class_obj = await self.get_class(class_id)
            schedule = await self.get_class_schedule(class_id, start_date, end_date)
            
            # Analyze schedule
            schedule_analysis = self._analyze_schedule(schedule)
            
            return {
                "class": class_obj.to_dict() if class_obj else None,
                "schedule": schedule,
                "analysis": schedule_analysis,
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "schedule"
            }
        except Exception as e:
            logger.error(f"Failed to generate schedule report for {class_id}: {str(e)}")
            raise
    
    def _analyze_grade_trend(self, grades: List[Dict[str, Any]]) -> str:
        """Analyze grade trend."""
        if len(grades) < 2:
            return "Insufficient data"
        
        # Sort by date
        sorted_grades = sorted(grades, key=lambda x: x['created_at'])
        
        # Compare latest and earliest grades
        first_grade = sorted_grades[0]['grade']
        last_grade = sorted_grades[-1]['grade']
        
        grade_values = {'A+': 4.3, 'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7, 
                       'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0}
        
        first_value = grade_values.get(first_grade, 0)
        last_value = grade_values.get(last_grade, 0)
        
        if last_value > first_value + 0.5:
            return "Improving"
        elif last_value < first_value - 0.5:
            return "Declining"
        else:
            return "Stable"
    
    def _analyze_schedule(self, schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze class schedule."""
        if not schedule:
            return {"total_sessions": 0, "by_day": {}, "by_type": {}}
        
        # Group by day of week
        by_day = {}
        # Group by session type
        by_type = {}
        
        for session in schedule:
            day = session['date'].strftime('%A') if 'date' in session else 'Unknown'
            session_type = session.get('session_type', 'Unknown')
            
            by_day[day] = by_day.get(day, 0) + 1
            by_type[session_type] = by_type.get(session_type, 0) + 1
        
        return {
            "total_sessions": len(schedule),
            "by_day": by_day,
            "by_type": by_type,
            "average_sessions_per_week": len(schedule) / 4 if schedule else 0
        }
    
    async def _invalidate_cache(self) -> None:
        """Invalidate class cache."""
        self._cache.clear()
    
    # Abstract method implementations required by BaseService
    
    async def create(self, data: Dict) -> Dict:
        """Create a new class entity."""
        # Reuse existing method
        class_obj = await self.create_class(data)
        return class_obj.dict()
    
    async def get(self, id: str) -> Optional[Dict]:
        """Get a class entity by ID."""
        class_obj = await self.get_class_by_id(id)
        return class_obj.dict() if class_obj else None
    
    async def update(self, id: str, data: Dict) -> Dict:
        """Update a class entity by ID."""
        class_obj = await self.update_class(id, data)
        return class_obj.dict()
    
    async def delete(self, id: str) -> bool:
        """Delete a class entity by ID."""
        return await self.delete_class(id)
    
    async def list(self, skip: int = 0, limit: int = 100, filters: Dict = None) -> List[Dict]:
        """List all class entities."""
        classes = await self.get_all_classes(skip=skip, limit=limit)
        return [class_obj.dict() for class_obj in classes]
    
    async def count(self, filters: Dict = None) -> int:
        """Count total number of class entities."""
        return await self.get_class_count()