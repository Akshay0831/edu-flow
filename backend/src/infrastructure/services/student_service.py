"""
Student Management Service

This module provides business logic for student management:
- Student registration and authentication
- Student profile management
- Academic performance tracking
- Enrollment management
- Attendance tracking
- Report generation

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from uuid import uuid4

from core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from core.logging import get_logger
from core.base_service import BaseService
from infrastructure.repositories.student_repository import StudentRepository
from models.student import StudentCreate, StudentUpdate, StudentResponse
from models.student_stats import StudentStats

logger = get_logger(__name__)


class StudentService(BaseService):
    """Student management service with comprehensive functionality."""
    
    def __init__(self, student_repository: StudentRepository):
        super().__init__(student_repository)
        self._cache = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the student service."""
        try:
            self._initialized = True
            logger.info("Student service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize student service: {str(e)}")
            raise
    
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized
    
    async def dispose(self) -> None:
        """Dispose the student service."""
        try:
            await super().dispose()
            self._cache.clear()
            logger.info("Student service disposed successfully")
        except Exception as e:
            logger.error(f"Failed to dispose student service: {str(e)}")
            raise
    
    # Core Business Operations
    
    async def create_student(self, student_data: Dict[str, Any]) -> StudentResponse:
        """Create a new student with business logic validation."""
        try:
            # Validate student data
            await self._validate_student_creation(student_data)
            
            # Check if student already exists
            existing_student = await self.repository.get_by_email(student_data['email'])
            if existing_student:
                raise ConflictError(f"Student with email {student_data['email']} already exists")
            
            # Create student
            result = await self.repository.create(**student_data)
            if not result.success:
                raise DatabaseError(f"Failed to create student: {result.error}")
            
            student = result.data
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return student
            
        except Exception as e:
            logger.error(f"Failed to create student: {str(e)}")
            raise
    
    async def update_student(self, student_id: str, student_data: Dict[str, Any]) -> Optional[StudentResponse]:
        """Update an existing student with business logic."""
        try:
            # Validate student exists
            student = await self.repository.get_by_id(student_id)
            if not student:
                raise NotFoundError(f"Student not found with ID: {student_id}")
            
            # Validate update data
            await self._validate_student_update(student_data)
            
            # Check for email conflicts if email is being updated
            if 'email' in student_data and student_data['email'] != student.email:
                existing_student = await self.repository.get_by_email(student_data['email'])
                if existing_student:
                    raise ConflictError(f"Student with email {student_data['email']} already exists")
            
            # Update student
            updated_student = await self.repository.update(student_id, **student_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return updated_student
            
        except Exception as e:
            logger.error(f"Failed to update student {student_id}: {str(e)}")
            raise
    
    async def get_student(self, student_id: str) -> Optional[StudentResponse]:
        """Get a student by ID with caching."""
        try:
            # Check cache first
            if student_id in self._cache:
                return self._cache[student_id]
            
            # Get student from repository
            student = await self.repository.get_by_id(student_id)
            
            if student:
                # Cache the result
                self._cache[student_id] = student
            
            return student
            
        except Exception as e:
            logger.error(f"Failed to get student {student_id}: {str(e)}")
            raise
    
    async def get_student_by_email(self, email: str) -> Optional[StudentResponse]:
        """Get a student by email."""
        try:
            return await self.repository.get_by_email(email)
        except Exception as e:
            logger.error(f"Failed to get student by email {email}: {str(e)}")
            raise
    
    async def get_student_by_reg_number(self, registration_number: str) -> Optional[StudentResponse]:
        """Get a student by registration number."""
        try:
            return await self.repository.get_by_registration_number(registration_number)
        except Exception as e:
            logger.error(f"Failed to get student by registration number {registration_number}: {str(e)}")
            raise
    
    async def delete_student(self, student_id: str) -> bool:
        """Delete a student with business logic."""
        try:
            # Validate student exists
            student = await self.repository.get_by_id(student_id)
            if not student:
                raise NotFoundError(f"Student not found with ID: {student_id}")
            
            # Check if student has active enrollments
            has_active_enrollments = await self._has_active_enrollments(student_id)
            if has_active_enrollments:
                raise ValidationError("Cannot delete student with active enrollments")
            
            # Check if student has outstanding dues
            has_outstanding_dues = await self._has_outstanding_dues(student_id)
            if has_outstanding_dues:
                raise ValidationError("Cannot delete student with outstanding dues")
            
            # Delete student
            result = await self.repository.delete(student_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete student {student_id}: {str(e)}")
            raise
    
    # Search and Filtering
    
    async def search_students(self, search_term: str, skip: int = 0, limit: int = 100) -> List[StudentResponse]:
        """Search for students by name, email, or registration number."""
        try:
            students = await self.repository.search_students(
                search_term=search_term,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for student in students:
                self._cache[student.id] = student
            
            return students
            
        except Exception as e:
            logger.error(f"Failed to search students: {str(e)}")
            raise
    
    async def get_students_by_department(self, department_id: str, skip: int = 0, limit: int = 100) -> List[StudentResponse]:
        """Get students by department."""
        try:
            students = await self.repository.get_by_department(
                department_id=department_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for student in students:
                self._cache[student.id] = student
            
            return students
            
        except Exception as e:
            logger.error(f"Failed to get students by department: {str(e)}")
            raise
    
    async def get_students_by_class(self, class_id: str, skip: int = 0, limit: int = 100) -> List[StudentResponse]:
        """Get students by class."""
        try:
            students = await self.repository.get_by_class(
                class_id=class_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for student in students:
                self._cache[student.id] = student
            
            return students
            
        except Exception as e:
            logger.error(f"Failed to get students by class: {str(e)}")
            raise
    
    async def get_students_by_batch(self, batch_id: str, skip: int = 0, limit: int = 100) -> List[StudentResponse]:
        """Get students by batch."""
        try:
            students = await self.repository.get_by_batch(
                batch_id=batch_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for student in students:
                self._cache[student.id] = student
            
            return students
            
        except Exception as e:
            logger.error(f"Failed to get students by batch: {str(e)}")
            raise
    
    # Enrollment Management
    
    async def enroll_student(self, student_id: str, class_id: str, enrollment_date: datetime = None) -> bool:
        """Enroll a student in a class."""
        try:
            # Validate student exists
            student = await self.repository.get_by_id(student_id)
            if not student:
                raise NotFoundError(f"Student not found with ID: {student_id}")
            
            # Validate class exists
            from infrastructure.repositories.class_repository import ClassRepository
            class_repo = ClassRepository()
            class_obj = await class_repo.get_by_id(class_id)
            if not class_obj:
                raise NotFoundError(f"Class not found with ID: {class_id}")
            
            # Check if student is already enrolled
            is_enrolled = await self.repository.is_enrolled(student_id, class_id)
            if is_enrolled:
                raise ConflictError(f"Student {student_id} is already enrolled in class {class_id}")
            
            # Check class capacity
            if not await self._check_class_capacity(class_id):
                raise ValidationError(f"Class {class_id} is full")
            
            # Enroll student
            result = await self.repository.enroll_student(
                student_id=student_id,
                class_id=class_id,
                enrollment_date=enrollment_date or datetime.utcnow()
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to enroll student {student_id} in class {class_id}: {str(e)}")
            raise
    
    async def unenroll_student(self, student_id: str, class_id: str, unenrollment_date: datetime = None) -> bool:
        """Unenroll a student from a class."""
        try:
            # Validate student exists
            student = await self.repository.get_by_id(student_id)
            if not student:
                raise NotFoundError(f"Student not found with ID: {student_id}")
            
            # Check if student is enrolled
            is_enrolled = await self.repository.is_enrolled(student_id, class_id)
            if not is_enrolled:
                raise NotFoundError(f"Student {student_id} is not enrolled in class {class_id}")
            
            # Unenroll student
            result = await self.repository.unenroll_student(
                student_id=student_id,
                class_id=class_id,
                unenrollment_date=unenrollment_date or datetime.utcnow()
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to unenroll student {student_id} from class {class_id}: {str(e)}")
            raise
    
    async def get_student_enrollments(self, student_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all enrollments for a student."""
        try:
            return await self.repository.get_student_enrollments(
                student_id=student_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get student enrollments for {student_id}: {str(e)}")
            raise
    
    # Academic Performance
    
    async def get_student_grades(self, student_id: str, subject_id: str = None, class_id: str = None, 
                              academic_year: str = None, semester: str = None) -> List[Dict[str, Any]]:
        """Get student grades with optional filtering."""
        try:
            return await self.repository.get_student_grades(
                student_id=student_id,
                subject_id=subject_id,
                class_id=class_id,
                academic_year=academic_year,
                semester=semester
            )
        except Exception as e:
            logger.error(f"Failed to get student grades for {student_id}: {str(e)}")
            raise
    
    async def get_student_attendance(self, student_id: str, start_date: date = None, 
                                   end_date: date = None, class_id: str = None) -> List[Dict[str, Any]]:
        """Get student attendance records."""
        try:
            return await self.repository.get_student_attendance(
                student_id=student_id,
                start_date=start_date,
                end_date=end_date,
                class_id=class_id
            )
        except Exception as e:
            logger.error(f"Failed to get student attendance for {student_id}: {str(e)}")
            raise
    
    async def get_student_performance(self, student_id: str, subject_id: str = None, 
                                    academic_year: str = None) -> Dict[str, Any]:
        """Get student performance summary."""
        try:
            return await self.repository.get_student_performance(
                student_id=student_id,
                subject_id=subject_id,
                academic_year=academic_year
            )
        except Exception as e:
            logger.error(f"Failed to get student performance for {student_id}: {str(e)}")
            raise
    
    # Profile Management
    
    async def update_student_profile(self, student_id: str, profile_data: Dict[str, Any]) -> Optional[StudentResponse]:
        """Update student profile information."""
        try:
            # Validate student exists
            student = await self.repository.get_by_id(student_id)
            if not student:
                raise NotFoundError(f"Student not found with ID: {student_id}")
            
            # Validate profile data
            await self._validate_profile_update(profile_data)
            
            # Update profile
            updated_student = await self.repository.update(student_id, **profile_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return updated_student
            
        except Exception as e:
            logger.error(f"Failed to update student profile for {student_id}: {str(e)}")
            raise
    
    async def update_student_contacts(self, student_id: str, contact_data: Dict[str, Any]) -> Optional[StudentResponse]:
        """Update student contact information."""
        try:
            # Validate student exists
            student = await self.repository.get_by_id(student_id)
            if not student:
                raise NotFoundError(f"Student not found with ID: {student_id}")
            
            # Validate contact data
            await self._validate_contact_update(contact_data)
            
            # Update contacts
            updated_student = await self.repository.update(student_id, **contact_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return updated_student
            
        except Exception as e:
            logger.error(f"Failed to update student contacts for {student_id}: {str(e)}")
            raise
    
    async def update_student_password(self, student_id: str, current_password: str, new_password: str) -> bool:
        """Update student password."""
        try:
            # Validate student exists
            student = await self.repository.get_by_id(student_id)
            if not student:
                raise NotFoundError(f"Student not found with ID: {student_id}")
            
            # Validate current password
            if not await self._validate_password(student_id, current_password):
                raise ValidationError("Current password is incorrect")
            
            # Validate new password
            await self._validate_password_requirements(new_password)
            
            # Update password
            result = await self.repository.update_password(
                student_id=student_id,
                new_password=new_password
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update student password for {student_id}: {str(e)}")
            raise
    
    # Analytics and Reports
    
    async def get_student_stats(self, student_id: str, start_date: date = None, end_date: date = None) -> StudentStats:
        """Get comprehensive student statistics."""
        try:
            # Validate student exists
            student = await self.repository.get_by_id(student_id)
            if not student:
                raise NotFoundError(f"Student not found with ID: {student_id}")
            
            # Get enrollment count
            enrollments = await self.get_student_enrollments(student_id)
            total_enrollments = len(enrollments)
            active_enrollments = len([e for e in enrollments if e.get('enrollment_status') == 'active'])
            
            # Get grades
            grades = await self.get_student_grades(student_id)
            total_grades = len(grades)
            
            # Calculate GPA
            gpa = await self._calculate_student_gpa(student_id)
            
            # Get attendance
            attendance = await self.get_student_attendance(student_id, start_date, end_date)
            total_attendance = len(attendance)
            present_count = len([a for a in attendance if a.get('status') == 'present'])
            attendance_rate = (present_count / total_attendance * 100) if total_attendance > 0 else 0
            
            # Get performance metrics
            performance = await self.get_student_performance(student_id)
            
            # Create stats object
            stats = StudentStats(
                student_id=student_id,
                student_name=student.name,
                total_enrollments=total_enrollments,
                active_enrollments=active_enrollments,
                total_grades=total_grades,
                gpa=gpa,
                attendance_rate=round(attendance_rate, 2),
                performance_score=performance.get('performance_score', 0),
                subjects_passed=performance.get('subjects_passed', 0),
                subjects_failed=performance.get('subjects_failed', 0),
                total_credits=performance.get('total_credits', 0),
                semester_gpa=performance.get('semester_gpa', 0),
                academic_year=performance.get('academic_year', ''),
                last_grade_date=performance.get('last_grade_date'),
                last_attendance_date=attendance[-1]['date'] if attendance else None
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get student stats for {student_id}: {str(e)}")
            raise
    
    async def generate_student_report(self, student_id: str, report_type: str = "academic", 
                                    start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Generate comprehensive student report."""
        try:
            # Validate student exists
            student = await self.repository.get_by_id(student_id)
            if not student:
                raise NotFoundError(f"Student not found with ID: {student_id}")
            
            # Generate report based on type
            if report_type == "academic":
                return await self._generate_academic_report(student_id, start_date, end_date)
            elif report_type == "attendance":
                return await self._generate_attendance_report(student_id, start_date, end_date)
            elif report_type == "performance":
                return await self._generate_performance_report(student_id, start_date, end_date)
            else:
                raise ValidationError(f"Unknown report type: {report_type}")
                
        except Exception as e:
            logger.error(f"Failed to generate student report for {student_id}: {str(e)}")
            raise
    
    # Batch Operations
    
    async def batch_enroll_students(self, student_ids: List[str], class_id: str, 
                                  enrollment_date: datetime = None) -> Dict[str, bool]:
        """Enroll multiple students in a class."""
        results = {}
        
        for student_id in student_ids:
            try:
                result = await self.enroll_student(student_id, class_id, enrollment_date)
                results[student_id] = result
            except Exception as e:
                logger.error(f"Failed to enroll student {student_id}: {str(e)}")
                results[student_id] = False
        
        return results
    
    async def batch_update_students(self, updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple students."""
        results = {}
        
        for update in updates:
            student_id = update['student_id']
            try:
                result = await self.update_student(student_id, update)
                results[student_id] = result is not None
            except Exception as e:
                logger.error(f"Failed to update student {student_id}: {str(e)}")
                results[student_id] = False
        
        return results
    
    # Helper Methods
    
    async def _validate_student_creation(self, data: Dict[str, Any]) -> None:
        """Validate student creation data."""
        required_fields = ['name', 'email', 'registration_number', 'date_of_birth', 
                         'gender', 'phone_number', 'address']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate email format
        if not self._validate_email(data['email']):
            raise ValidationError("Invalid email format")
        
        # Validate registration number format
        if not self._validate_registration_number(data['registration_number']):
            raise ValidationError("Invalid registration number format")
        
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
    
    async def _validate_student_update(self, data: Dict[str, Any]) -> None:
        """Validate student update data."""
        # Validate email if provided
        if 'email' in data and data['email']:
            if not self._validate_email(data['email']):
                raise ValidationError("Invalid email format")
        
        # Validate phone number if provided
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
                         'bio', 'skills', 'interests', 'achievements']
        
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
    
    async def _validate_contact_update(self, data: Dict[str, Any]) -> None:
        """Validate contact update data."""
        allowed_fields = ['email', 'phone_number', 'address', 'city', 'state', 
                         'postal_code', 'country', 'emergency_contact_name', 
                         'emergency_contact_phone']
        
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
        
        if 'emergency_contact_phone' in data and data['emergency_contact_phone']:
            if not self._validate_phone_number(data['emergency_contact_phone']):
                raise ValidationError("Invalid emergency contact phone number format")
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_registration_number(self, registration_number: str) -> bool:
        """Validate registration number format."""
        # Accept formats: STU001, AA123456, STU123, ABC12345
        # More specific patterns: STU001 (3 letters + 3+ digits) or AA123456 (2-3 letters + 6+ digits)
        import re
        if re.match(r'^[A-Z]{3}\d{3,5}$', registration_number) and len(registration_number) >= 6:
            # STU001 format (exactly 3 letters + 3+ digits, minimum 6 chars)
            return True
        elif re.match(r'^[A-Z]{2,3}\d{5,6}$', registration_number) and len(registration_number) >= 6:
            # AA123456 format (2-3 letters + 5-6 digits, minimum 6 chars)
            return True
        return False
    
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
    
    async def _validate_password(self, student_id: str, password: str) -> bool:
        """Validate student password."""
        # This would hash the password and compare with stored hash
        # For now, return True (should be implemented properly)
        return True
    
    async def _has_active_enrollments(self, student_id: str) -> bool:
        """Check if student has active enrollments."""
        enrollments = await self.get_student_enrollments(student_id)
        return any(e.get('enrollment_status') == 'active' for e in enrollments)
    
    async def _has_outstanding_dues(self, student_id: str) -> bool:
        """Check if student has outstanding dues."""
        # This would check payment records
        # For now, return False (should be implemented)
        return False
    
    async def _check_class_capacity(self, class_id: str) -> bool:
        """Check if class has capacity for more students."""
        # This would check current enrollment vs class capacity
        # For now, return True (should be implemented)
        return True
    
    async def _calculate_student_gpa(self, student_id: str) -> float:
        """Calculate student GPA."""
        try:
            grades = await self.get_student_grades(student_id)
            if not grades:
                return 0.0
            
            # Calculate weighted GPA
            total_credits = 0
            total_points = 0
            
            for grade in grades:
                credit = grade.get('credit_hours', 1)
                grade_point = self._letter_to_grade_point(grade.get('grade', ''))
                
                total_credits += credit
                total_points += credit * grade_point
            
            return total_points / total_credits if total_credits > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _letter_to_grade_point(self, grade: str) -> float:
        """Convert letter grade to grade point."""
        grade_map = {
            'A+': 4.0, 'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'D-': 0.7,
            'F': 0.0
        }
        return grade_map.get(grade.upper(), 0.0)
    
    async def _generate_academic_report(self, student_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate academic report for student."""
        try:
            student = await self.get_student(student_id)
            stats = await self.get_student_stats(student_id, start_date, end_date)
            grades = await self.get_student_grades(student_id)
            enrollments = await self.get_student_enrollments(student_id)
            
            return {
                "student": student.to_dict() if student else None,
                "statistics": stats.to_dict() if stats else None,
                "grades": grades,
                "enrollments": enrollments,
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "academic"
            }
        except Exception as e:
            logger.error(f"Failed to generate academic report for {student_id}: {str(e)}")
            raise
    
    async def _generate_attendance_report(self, student_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate attendance report for student."""
        try:
            student = await self.get_student(student_id)
            attendance = await self.get_student_attendance(student_id, start_date, end_date)
            
            # Calculate attendance summary
            total_days = len(attendance)
            present_days = len([a for a in attendance if a.get('status') == 'present'])
            absent_days = len([a for a in attendance if a.get('status') == 'absent'])
            
            return {
                "student": student.to_dict() if student else None,
                "attendance": attendance,
                "summary": {
                    "total_days": total_days,
                    "present_days": present_days,
                    "absent_days": absent_days,
                    "attendance_rate": round((present_days / total_days) * 100, 2) if total_days > 0 else 0,
                    "late_count": len([a for a in attendance if a.get('status') == 'late']),
                    "excused_absent_count": len([a for a in attendance if a.get('status') == 'excused'])
                },
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "attendance"
            }
        except Exception as e:
            logger.error(f"Failed to generate attendance report for {student_id}: {str(e)}")
            raise
    
    async def _generate_performance_report(self, student_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate performance report for student."""
        try:
            student = await self.get_student(student_id)
            performance = await self.get_student_performance(student_id)
            grades = await self.get_student_grades(student_id)
            
            # Analyze performance trends
            if grades:
                recent_grades = sorted(grades, key=lambda x: x.get('created_at', datetime.min), reverse=True)[:10]
                performance_trend = self._analyze_performance_trend(recent_grades)
            else:
                performance_trend = "No data"
            
            return {
                "student": student.to_dict() if student else None,
                "performance": performance,
                "grades": grades,
                "trend_analysis": performance_trend,
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "performance"
            }
        except Exception as e:
            logger.error(f"Failed to generate performance report for {student_id}: {str(e)}")
            raise
    
    def _analyze_performance_trend(self, grades: List[Dict[str, Any]]) -> str:
        """Analyze student performance trend."""
        if not grades:
            return "No data"
        
        # Calculate average grade points
        grade_points = [self._letter_to_grade_point(g.get('grade', '')) for g in grades]
        average_gpa = sum(grade_points) / len(grade_points)
        
        if average_gpa >= 3.5:
            return "Excellent"
        elif average_gpa >= 3.0:
            return "Good"
        elif average_gpa >= 2.5:
            return "Average"
        elif average_gpa >= 2.0:
            return "Below Average"
        else:
            return "Poor"
    
    async def _invalidate_cache(self) -> None:
        """Invalidate student cache."""
        self._cache.clear()

        # Clear any related caches (this would be more sophisticated in a real system)
        # For now, just clear the student cache
    
    # Abstract method implementations required by BaseService
    
    async def create(self, data: Dict) -> Dict:
        """Create a new student entity."""
        # Reuse existing method
        student = await self.create_student(data)
        return student.dict()
    
    async def get(self, id: str) -> Optional[Dict]:
        """Get a student entity by ID."""
        student = await self.get_student_by_id(id)
        return student.dict() if student else None
    
    async def update(self, id: str, data: Dict) -> Dict:
        """Update a student entity by ID."""
        student = await self.update_student(id, data)
        return student.dict()
    
    async def delete(self, id: str) -> bool:
        """Delete a student entity by ID."""
        return await self.delete_student(id)
    
    async def list(self, skip: int = 0, limit: int = 100, filters: Dict = None) -> List[Dict]:
        """List all student entities."""
        students = await self.get_all_students(skip=skip, limit=limit)
        return [student.dict() for student in students]
    
    async def count(self, filters: Dict = None) -> int:
        """Count total number of student entities."""
        return await self.get_student_count()