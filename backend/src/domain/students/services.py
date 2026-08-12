"""
Student domain services

This module contains domain services for student management:
- StudentService: Student business logic service
- AcademicRecordService: Academic record management service
- EnrollmentService: Enrollment management service

Author: Edu-Flow Team
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4

from .entities import Student, AcademicRecord, EnrollmentRecord, GradeLevel, AcademicStanding, RiskLevel, EnrollmentStatus
from ...infrastructure.exceptions import NotFoundError, ValidationError


class StudentService:
    """Domain service for student business logic"""
    
    def __init__(self, student_repository, academic_record_repository, enrollment_repository):
        self.student_repository = student_repository
        self.academic_record_repository = academic_record_repository
        self.enrollment_repository = enrollment_repository
    
    async def create_student(self, student_data: Dict[str, Any]) -> Student:
        """Create a new student"""
        # Create student entity
        student = Student(
            id=str(uuid4()),
            **student_data
        )
        
        # Validate student doesn't already exist
        existing_student = await self.student_repository.get_by_email(student.email)
        if existing_student:
            raise ValidationError("Student with this email already exists")
        
        # Validate student ID uniqueness
        existing_student_id = await self.student_repository.get_by_student_id(student.student_id)
        if existing_student_id:
            raise ValidationError("Student ID already exists")
        
        # Save student
        return await self.student_repository.create(student)
    
    async def get_student_by_id(self, student_id: str) -> Optional[Student]:
        """Get student by ID"""
        student = await self.student_repository.get_by_id(student_id)
        if not student:
            raise NotFoundError("Student not found")
        return student
    
    async def get_student_by_email(self, email: str) -> Optional[Student]:
        """Get student by email"""
        return await self.student_repository.get_by_email(email)
    
    async def get_students_by_grade_level(self, grade_level: GradeLevel) -> List[Student]:
        """Get students by grade level"""
        return await self.student_repository.get_by_grade_level(grade_level)
    
    async def update_student(self, student_id: str, update_data: Dict[str, Any]) -> Student:
        """Update student information"""
        student = await self.get_student_by_id(student_id)
        
        # Update student profile
        student.update_profile(**update_data)
        
        # Save updated student
        return await self.student_repository.update(student)
    
    async def promote_student(self, student_id: str) -> Student:
        """Promote student to next grade level"""
        student = await self.get_student_by_id(student_id)
        
        # Check if student can be promoted
        if student.grade_level >= GradeLevel.TWELFTH:
            raise ValidationError("Student is already at the highest grade level")
        
        # Promote student
        student.promote_to_next_grade()
        
        # Save updated student
        return await self.student_repository.update(student)
    
    async def graduate_student(self, student_id: str) -> Student:
        """Mark student as graduated"""
        student = await self.get_student_by_id(student_id)
        
        # Check if student meets graduation requirements
        academic_records = await self.academic_record_repository.get_by_student_id(student_id)
        total_credits = student.calculate_total_credits(academic_records)
        
        if total_credits < 24:  # Example graduation requirement
            raise ValidationError("Student does not meet graduation requirements")
        
        # Graduate student
        student.graduate()
        
        # Save updated student
        return await self.student_repository.update(student)
    
    async def withdraw_student(self, student_id: str) -> Student:
        """Mark student as withdrawn"""
        student = await self.get_student_by_id(student_id)
        student.withdraw()
        return await self.student_repository.update(student)
    
    async def transfer_student(self, student_id: str) -> Student:
        """Mark student as transferred"""
        student = await self.get_student_by_id(student_id)
        student.transfer()
        return await self.student_repository.update(student)
    
    async def get_student_academic_summary(self, student_id: str) -> Dict[str, Any]:
        """Get comprehensive academic summary for student"""
        student = await self.get_student_by_id(student_id)
        academic_records = await self.academic_record_repository.get_by_student_id(student_id)
        
        # Calculate statistics
        total_credits = student.calculate_total_credits(academic_records)
        avg_grade = sum(record.grade for record in academic_records) / len(academic_records) if academic_records else 0
        
        # Update academic standing based on GPA
        if student.gpa:
            student.update_academic_status()
            await self.student_repository.update(student)
        
        return {
            "student": student,
            "academic_records": academic_records,
            "total_credits": total_credits,
            "average_grade": avg_grade,
            "gpa": student.gpa,
            "academic_standing": student.academic_standing,
            "risk_level": student.risk_level
        }
    
    async def assess_student_risk(self, student_id: str) -> Student:
        """Assess student risk level"""
        student = await self.get_student_by_id(student_id)
        academic_records = await self.academic_record_repository.get_by_student_id(student_id)
        
        # Assess risk level
        student.assess_risk_level(academic_records, student.attendance_rate)
        
        # Save updated student
        return await self.student_repository.update(student)


class AcademicRecordService:
    """Domain service for academic record management"""
    
    def __init__(self, academic_record_repository):
        self.academic_record_repository = academic_record_repository
    
    async def create_academic_record(self, record_data: Dict[str, Any]) -> AcademicRecord:
        """Create a new academic record"""
        # Create academic record entity
        record = AcademicRecord(
            id=str(uuid4()),
            **record_data
        )
        
        # Validate grade is valid
        if record.grade < 0 or record.grade > 100:
            raise ValidationError("Grade must be between 0 and 100")
        
        # Save record
        return await self.academic_record_repository.create(record)
    
    async def get_academic_records_by_student(self, student_id: str) -> List[AcademicRecord]:
        """Get all academic records for a student"""
        return await self.academic_record_repository.get_by_student_id(student_id)
    
    async def get_academic_records_by_course(self, course_id: str) -> List[AcademicRecord]:
        """Get all academic records for a course"""
        return await self.academic_record_repository.get_by_course_id(course_id)
    
    async def update_academic_record(self, record_id: str, update_data: Dict[str, Any]) -> AcademicRecord:
        """Update academic record"""
        record = await self.academic_record_repository.get_by_id(record_id)
        if not record:
            raise NotFoundError("Academic record not found")
        
        # Update record
        for key, value in update_data.items():
            if hasattr(record, key):
                setattr(record, key, value)
        
        # Save updated record
        return await self.academic_record_repository.update(record)
    
    async def delete_academic_record(self, record_id: str) -> bool:
        """Delete academic record"""
        return await self.academic_record_repository.delete(record_id)
    
    async def calculate_student_gpa(self, student_id: str) -> float:
        """Calculate GPA for a student"""
        academic_records = await self.get_academic_records_by_student(student_id)
        
        if not academic_records:
            return 0.0
        
        total_points = 0
        total_credits = 0
        
        for record in academic_records:
            if record.grade >= 60:  # Only passing grades count
                grade_points = record.calculate_grade_points()
                total_points += grade_points * record.credits
                total_credits += record.credits
        
        return total_points / total_credits if total_credits > 0 else 0.0


class EnrollmentService:
    """Domain service for enrollment management"""
    
    def __init__(self, enrollment_repository, course_repository):
        self.enrollment_repository = enrollment_repository
        self.course_repository = course_repository
    
    async def create_enrollment(self, enrollment_data: Dict[str, Any]) -> EnrollmentRecord:
        """Create a new enrollment"""
        # Create enrollment record entity
        enrollment = EnrollmentRecord(
            id=str(uuid4()),
            student_id=enrollment_data["student_id"],
            course_id=enrollment_data["course_id"],
            semester=enrollment_data["semester"],
            academic_year=enrollment_data["academic_year"],
            priority=enrollment_data.get("priority", 1),
            special_accommodations=enrollment_data.get("special_accommodations"),
            status=EnrollmentStatus.ACTIVE
        )
        
        # Validate course exists and has capacity
        course = await self.course_repository.get_by_id(enrollment.course_id)
        if not course:
            raise ValidationError("Course not found")
        
        if course.capacity and course.enrolled_students >= course.capacity:
            raise ValidationError("Course is at capacity")
        
        # Save enrollment
        return await self.enrollment_repository.create(enrollment)
    
    async def get_student_enrollments(self, student_id: str) -> List[EnrollmentRecord]:
        """Get all enrollments for a student"""
        return await self.enrollment_repository.get_by_student_id(student_id)
    
    async def get_course_enrollments(self, course_id: str) -> List[EnrollmentRecord]:
        """Get all enrollments for a course"""
        return await self.enrollment_repository.get_by_course_id(course_id)
    
    async def update_enrollment_status(self, enrollment_id: str, status: str) -> EnrollmentRecord:
        """Update enrollment status"""
        enrollment = await self.enrollment_repository.get_by_id(enrollment_id)
        if not enrollment:
            raise NotFoundError("Enrollment not found")
        
        # Update status
        enrollment.status = status
        enrollment.updated_at = datetime.now()
        
        # Save updated enrollment
        return await self.enrollment_repository.update(enrollment)
    
    async def cancel_enrollment(self, enrollment_id: str) -> EnrollmentRecord:
        """Cancel enrollment"""
        return await self.update_enrollment_status(enrollment_id, "cancelled")
    
    async def enroll_student_in_course(self, student_id: str, course_id: str, semester: str, academic_year: str) -> EnrollmentRecord:
        """Enroll student in course"""
        enrollment_data = {
            "student_id": student_id,
            "course_id": course_id,
            "semester": semester,
            "academic_year": academic_year
        }
        
        return await self.create_enrollment(enrollment_data)