"""
Teacher domain services

This module contains domain services for teacher management:
- TeacherService: Teacher management service
- QualificationService: Qualification management service

Author: Edu-Flow Team
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from .entities import Teacher, Qualification, EmploymentStatus
from ...infrastructure.exceptions import NotFoundError, ValidationError


class TeacherService:
    """Domain service for teacher business logic"""
    
    def __init__(self, teacher_repository, qualification_repository):
        self.teacher_repository = teacher_repository
        self.qualification_repository = qualification_repository
    
    async def create_teacher(self, teacher_data: Dict[str, Any]) -> Teacher:
        """Create a new teacher"""
        # Validate teacher data
        if not teacher_data.get("first_name") or not teacher_data.get("last_name"):
            raise ValidationError("Teacher first name and last name are required")
        
        if not teacher_data.get("email"):
            raise ValidationError("Teacher email is required")
        
        # Check if teacher already exists
        existing_teacher = await self.teacher_repository.find_by_email(teacher_data["email"])
        if existing_teacher:
            raise ValidationError("Teacher with this email already exists")
        
        # Create teacher entity
        teacher = Teacher(
            first_name=teacher_data["first_name"],
            last_name=teacher_data["last_name"],
            email=teacher_data["email"],
            phone=teacher_data.get("phone"),
            hire_date=teacher_data.get("hire_date", datetime.now()),
            status=teacher_data.get("status", EmploymentStatus.ACTIVE),
            department=teacher_data.get("department"),
            specialization=teacher_data.get("specialization"),
            qualifications=[]
        )
        
        # Save teacher
        return await self.teacher_repository.save(teacher)
    
    async def update_teacher(self, teacher_id: str, teacher_data: Dict[str, Any]) -> Teacher:
        """Update an existing teacher"""
        # Get existing teacher
        teacher = await self.teacher_repository.find_by_id(teacher_id)
        if not teacher:
            raise NotFoundError(f"Teacher with ID {teacher_id} not found")
        
        # Update fields
        if "first_name" in teacher_data:
            teacher.first_name = teacher_data["first_name"]
        if "last_name" in teacher_data:
            teacher.last_name = teacher_data["last_name"]
        if "email" in teacher_data:
            # Check if email is already used by another teacher
            existing_teacher = await self.teacher_repository.find_by_email(teacher_data["email"])
            if existing_teacher and existing_teacher.id != teacher_id:
                raise ValidationError("Email already used by another teacher")
            teacher.email = teacher_data["email"]
        if "phone" in teacher_data:
            teacher.phone = teacher_data["phone"]
        if "status" in teacher_data:
            teacher.status = teacher_data["status"]
        if "department" in teacher_data:
            teacher.department = teacher_data["department"]
        if "specialization" in teacher_data:
            teacher.specialization = teacher_data["specialization"]
        
        # Save teacher
        return await self.teacher_repository.save(teacher)
    
    async def delete_teacher(self, teacher_id: str) -> bool:
        """Delete a teacher"""
        # Get existing teacher
        teacher = await self.teacher_repository.find_by_id(teacher_id)
        if not teacher:
            raise NotFoundError(f"Teacher with ID {teacher_id} not found")
        
        # Check if teacher has active assignments
        if teacher.status == EmploymentStatus.ACTIVE:
            raise ValidationError("Cannot delete active teacher. Deactivate first.")
        
        # Delete teacher
        return await self.teacher_repository.delete(teacher_id)
    
    async def get_teacher_by_id(self, teacher_id: str) -> Optional[Teacher]:
        """Get teacher by ID"""
        return await self.teacher_repository.find_by_id(teacher_id)
    
    async def get_teacher_by_email(self, email: str) -> Optional[Teacher]:
        """Get teacher by email"""
        return await self.teacher_repository.find_by_email(email)
    
    async def get_all_teachers(self, skip: int = 0, limit: int = 100) -> List[Teacher]:
        """Get all teachers with pagination"""
        return await self.teacher_repository.find_all(skip=skip, limit=limit)
    
    async def promote_teacher(self, teacher_id: str) -> Teacher:
        """Promote teacher to next employment status"""
        teacher = await self.teacher_repository.find_by_id(teacher_id)
        if not teacher:
            raise NotFoundError(f"Teacher with ID {teacher_id} not found")
        
        # Promotion logic
        if teacher.status == EmploymentStatus.PROBATIONARY:
            teacher.status = EmploymentStatus.PERMANENT
        elif teacher.status == EmploymentStatus.PERMANENT:
            teacher.status = EmploymentStatus.SENIOR
        elif teacher.status == EmploymentStatus.SENIOR:
            teacher.status = EmploymentStatus.PRINCIPAL
        else:
            raise ValidationError("Teacher is already at highest employment status")
        
        # Update promotion date
        teacher.promotion_date = datetime.now()
        
        # Save teacher
        return await self.teacher_repository.save(teacher)
    
    async def get_eligible_for_promotion(self, status: EmploymentStatus) -> List[Teacher]:
        """Get teachers eligible for promotion"""
        return await self.teacher_repository.find_by_status(status)
    
    async def add_qualification(self, teacher_id: str, qualification_data: Dict[str, Any]) -> Qualification:
        """Add qualification to teacher"""
        # Get teacher
        teacher = await self.teacher_repository.find_by_id(teacher_id)
        if not teacher:
            raise NotFoundError(f"Teacher with ID {teacher_id} not found")
        
        # Create qualification
        qualification = Qualification(
            degree=qualification_data["degree"],
            institution=qualification_data["institution"],
            year_obtained=qualification_data["year_obtained"],
            field_of_study=qualification_data.get("field_of_study"),
            teacher_id=teacher_id
        )
        
        # Save qualification
        qualification = await self.qualification_repository.save(qualification)
        
        # Add to teacher's qualifications
        teacher.qualifications.append(qualification)
        
        # Save teacher
        await self.teacher_repository.save(teacher)
        
        return qualification


class QualificationService:
    """Domain service for qualification management"""
    
    def __init__(self, qualification_repository):
        self.qualification_repository = qualification_repository
    
    async def create_qualification(self, qualification_data: Dict[str, Any]) -> Qualification:
        """Create a new qualification"""
        # Validate qualification data
        if not qualification_data.get("degree") or not qualification_data.get("institution"):
            raise ValidationError("Degree and institution are required")
        
        if not qualification_data.get("year_obtained"):
            raise ValidationError("Year obtained is required")
        
        # Create qualification entity
        qualification = Qualification(
            degree=qualification_data["degree"],
            institution=qualification_data["institution"],
            year_obtained=qualification_data["year_obtained"],
            field_of_study=qualification_data.get("field_of_study"),
            teacher_id=qualification_data["teacher_id"]
        )
        
        # Save qualification
        return await self.qualification_repository.save(qualification)
    
    async def get_qualification_by_id(self, qualification_id: str) -> Optional[Qualification]:
        """Get qualification by ID"""
        return await self.qualification_repository.find_by_id(qualification_id)
    
    async def get_qualifications_by_teacher(self, teacher_id: str) -> List[Qualification]:
        """Get all qualifications for a teacher"""
        return await self.qualification_repository.find_by_teacher(teacher_id)
    
    async def update_qualification(self, qualification_id: str, qualification_data: Dict[str, Any]) -> Qualification:
        """Update an existing qualification"""
        # Get existing qualification
        qualification = await self.qualification_repository.find_by_id(qualification_id)
        if not qualification:
            raise NotFoundError(f"Qualification with ID {qualification_id} not found")
        
        # Update fields
        if "degree" in qualification_data:
            qualification.degree = qualification_data["degree"]
        if "institution" in qualification_data:
            qualification.institution = qualification_data["institution"]
        if "year_obtained" in qualification_data:
            qualification.year_obtained = qualification_data["year_obtained"]
        if "field_of_study" in qualification_data:
            qualification.field_of_study = qualification_data["field_of_study"]
        
        # Save qualification
        return await self.qualification_repository.save(qualification)
    
    async def delete_qualification(self, qualification_id: str) -> bool:
        """Delete a qualification"""
        # Get existing qualification
        qualification = await self.qualification_repository.find_by_id(qualification_id)
        if not qualification:
            raise NotFoundError(f"Qualification with ID {qualification_id} not found")
        
        # Delete qualification
        return await self.qualification_repository.delete(qualification_id)