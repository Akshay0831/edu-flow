"""
Student Management Service

This module provides comprehensive student management functionality:
- Student CRUD operations and validation
- Academic tracking and performance monitoring
- Enrollment management and validation
- Graduation requirements checking
- Risk assessment and intervention tracking
- Data privacy and audit logging

Author: Edu-Flow Team
"""

import uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union
import hashlib
import re

from ..models.student import (
    StudentCreate, StudentUpdate, StudentResponse,
    AcademicRecord, EnrollmentRecord, PerformanceMetrics,
    AcademicSummary, GraduationStatus, RiskAssessment,
    StudentSearch, StudentStatistics, StudentAudit,
    GradeLevel, AcademicStanding, EnrollmentStatus,
    RiskLevel, UserRole
)
from ..core.security import AuthService
from ..core.exceptions import ValidationError, NotFoundError, ForbiddenError, AuthenticationError

class StudentService:
    """Student management service with comprehensive functionality"""
    
    def __init__(self, auth_service: Optional[AuthService] = None):
        self.auth_service = auth_service or AuthService()
        self.students: Dict[str, Dict[str, Any]] = {}
        self.academic_records: List[Dict[str, Any]] = []
        self.enrollment_records: List[Dict[str, Any]] = []
        self.audit_trail: List[Dict[str, Any]] = []
        
        # Initialize with some test data
        self._initialize_test_data()
    
    def _initialize_test_data(self):
        """Initialize with sample student data for testing"""
        sample_students = [
            {
                "id": str(uuid.uuid4()),
                "email": "student1@example.com",
                "password_hash": self.auth_service.get_password_hash("Password123!"),
                "name": "Alice Johnson",
                "role": UserRole.STUDENT,
                "student_id": "STU001",
                "grade_level": GradeLevel.TENTH,
                "enrollment_date": date(2024, 9, 1),
                "department_id": "DEPT001",
                "advisor_id": "TEACH001",
                "gpa": 3.2,
                "attendance_rate": 0.95,
                "academic_standing": AcademicStanding.GOOD,
                "is_active": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "id": str(uuid.uuid4()),
                "email": "student2@example.com",
                "password_hash": self.auth_service.get_password_hash("Password123!"),
                "name": "Bob Smith",
                "role": UserRole.STUDENT,
                "student_id": "STU002",
                "grade_level": GradeLevel.ELEVENTH,
                "enrollment_date": date(2023, 9, 1),
                "department_id": "DEPT002",
                "advisor_id": "TEACH002",
                "gpa": 2.8,
                "attendance_rate": 0.85,
                "academic_standing": AcademicStanding.SATISFACTORY,
                "is_active": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]
        
        for student in sample_students:
            self.students[student["id"]] = student
    
    def _generate_audit_record(self, student_id: str, action: str, performed_by: str, 
                              details: Optional[Dict[str, Any]] = None) -> StudentAudit:
        """Generate audit record for student actions"""
        audit_id = str(uuid.uuid4())
        audit_record = {
            "audit_id": audit_id,
            "student_id": student_id,
            "action": action,
            "performed_by": performed_by,
            "details": details or {},
            "timestamp": datetime.now(),
            "ip_address": "127.0.0.1",
            "user_agent": "Edu-Flow API"
        }
        
        self.audit_trail.append(audit_record)
        return StudentAudit(**audit_record)
    
    def create_student(self, student_data: Dict[str, Any]) -> StudentResponse:
        """Create a new student with comprehensive validation"""
        try:
            # Validate student data
            self.validate_student_data(student_data)
            
            # Check for duplicate email and student ID
            if self._get_student_by_email(student_data["email"]):
                raise ValidationError(f"Student with email {student_data['email']} already exists")
            
            if self._get_student_by_student_id(student_data["student_id"]):
                raise ValidationError(f"Student ID {student_data['student_id']} already exists")
            
            # Create student record
            student_id = str(uuid.uuid4())
            current_time = datetime.now()
            
            student = {
                "id": student_id,
                "email": student_data["email"],
                "password_hash": self.auth_service.get_password_hash(student_data["password"]),
                "name": student_data["name"],
                "role": UserRole.STUDENT,
                "student_id": student_data["student_id"],
                "grade_level": student_data["grade_level"],
                "enrollment_date": student_data["enrollment_date"],
                "department_id": student_data.get("department_id"),
                "advisor_id": student_data.get("advisor_id"),
                "gpa": student_data.get("gpa"),
                "attendance_rate": student_data.get("attendance_rate"),
                "academic_standing": student_data.get("academic_standing"),
                "notes": student_data.get("notes"),
                "phone": student_data.get("phone"),
                "address": student_data.get("address"),
                "emergency_contact": student_data.get("emergency_contact"),
                "medical_info": student_data.get("medical_info"),
                "family_info": student_data.get("family_info"),
                "preferences": student_data.get("preferences"),
                "is_active": True,
                "created_at": current_time,
                "updated_at": current_time,
                "last_login": None
            }
            
            # Remove sensitive data for response
            student_copy = student.copy()
            student_copy.pop("password_hash", None)
            
            self.students[student_id] = student
            
            # Log audit
            self._generate_audit_record(student_id, "create", "system", student_data)
            
            return StudentResponse(**student_copy)
            
        except Exception as e:
            raise ValidationError(f"Failed to create student: {str(e)}")
    
    def get_student(self, student_id: str) -> StudentResponse:
        """Get student by ID with complete information"""
        student = self.students.get(student_id)
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found")
        
        # Remove sensitive data for response
        student_copy = student.copy()
        student_copy.pop("password_hash", None)
        
        return StudentResponse(**student_copy)
    
    def get_student_by_student_id(self, student_id: str) -> StudentResponse:
        """Get student by student ID"""
        student = next((s for s in self.students.values() if s["student_id"] == student_id), None)
        if not student:
            raise NotFoundError(f"Student with student ID {student_id} not found")
        
        # Remove sensitive data for response
        student_copy = student.copy()
        student_copy.pop("password_hash", None)
        
        return StudentResponse(**student_copy)
    
    def get_student_by_email(self, email: str) -> Optional[StudentResponse]:
        """Get student by email (returns None if not found)"""
        student = next((s for s in self.students.values() if s["email"] == email), None)
        if not student:
            return None
        
        # Remove sensitive data for response
        student_copy = student.copy()
        student_copy.pop("password_hash", None)
        
        return StudentResponse(**student_copy)
    
    def update_student(self, student_id: str, update_data: Dict[str, Any]) -> StudentResponse:
        """Update student information with validation"""
        student = self.students.get(student_id)
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found")
        
        # Validate update data
        self.validate_student_update(update_data)
        
        # Update student record
        current_time = datetime.now()
        
        for key, value in update_data.items():
            if key in student:
                student[key] = value
        
        student["updated_at"] = current_time
        
        # Remove sensitive data for response
        student_copy = student.copy()
        student_copy.pop("password_hash", None)
        
        # Log audit
        self._generate_audit_record(student_id, "update", "system", update_data)
        
        return StudentResponse(**student_copy)
    
    def deactivate_student(self, student_id: str) -> StudentResponse:
        """Deactivate a student account"""
        student = self.students.get(student_id)
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found")
        
        current_time = datetime.now()
        student["is_active"] = False
        student["deactivated_at"] = current_time
        student["updated_at"] = current_time
        
        # Remove sensitive data for response
        student_copy = student.copy()
        student_copy.pop("password_hash", None)
        
        # Log audit
        self._generate_audit_record(student_id, "deactivate", "system", {"deactivated_at": current_time})
        
        return StudentResponse(**student_copy)
    
    def activate_student(self, student_id: str) -> StudentResponse:
        """Activate a deactivated student account"""
        student = self.students.get(student_id)
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found")
        
        current_time = datetime.now()
        student["is_active"] = True
        student["deactivated_at"] = None
        student["updated_at"] = current_time
        
        # Remove sensitive data for response
        student_copy = student.copy()
        student_copy.pop("password_hash", None)
        
        # Log audit
        self._generate_audit_record(student_id, "activate", "system", {"activated_at": current_time})
        
        return StudentResponse(**student_copy)
    
    def search_students(self, search_criteria: Optional[Dict[str, Any]] = None, 
                       limit: int = 100, offset: int = 0) -> List[StudentResponse]:
        """Search students with various criteria"""
        if search_criteria is None:
            search_criteria = {}
        
        students_list = list(self.students.values())
        
        # Apply search filters
        filtered_students = []
        for student in students_list:
            if self._matches_search_criteria(student, search_criteria):
                # Remove sensitive data for response
                student_copy = student.copy()
                student_copy.pop("password_hash", None)
                filtered_students.append(student_copy)
        
        # Apply pagination
        paginated_students = filtered_students[offset:offset + limit]
        
        return [StudentResponse(**student) for student in paginated_students]
    
    def get_students_by_department(self, department_id: str) -> List[StudentResponse]:
        """Get all students in a specific department"""
        students = [student for student in self.students.values() 
                   if student.get("department_id") == department_id]
        
        # Remove sensitive data for response
        students_copy = []
        for student in students:
            student_copy = student.copy()
            student_copy.pop("password_hash", None)
            students_copy.append(student_copy)
        
        return [StudentResponse(**student) for student in students_copy]
    
    def get_students_by_advisor(self, advisor_id: str) -> List[StudentResponse]:
        """Get all students assigned to a specific advisor"""
        students = [student for student in self.students.values() 
                   if student.get("advisor_id") == advisor_id]
        
        # Remove sensitive data for response
        students_copy = []
        for student in students:
            student_copy = student.copy()
            student_copy.pop("password_hash", None)
            students_copy.append(student_copy)
        
        return [StudentResponse(**student) for student in students_copy]
    
    def calculate_gpa(self, grades: List[float]) -> float:
        """Calculate GPA from a list of grades"""
        if not grades:
            return 0.0
        
        # Convert percentage grades to 4.0 scale
        grade_points = []
        for grade in grades:
            if grade >= 90:
                grade_points.append(4.0)
            elif grade >= 80:
                grade_points.append(3.0)
            elif grade >= 70:
                grade_points.append(2.0)
            elif grade >= 60:
                grade_points.append(1.0)
            else:
                grade_points.append(0.0)
        
        return sum(grade_points) / len(grade_points) if grade_points else 0.0
    
    def get_student_academic_summary(self, student_id: str, grades: List[float] = None) -> AcademicSummary:
        """Get comprehensive academic summary for a student"""
        student = self.students.get(student_id)
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found")
        
        # Use provided grades or calculate from academic records
        if grades is None:
            grades = [record.get("grade", 0) for record in self.academic_records 
                     if record.get("student_id") == student_id]
            total_credits = sum(record.get("credits", 0) for record in self.academic_records 
                               if record.get("student_id") == student_id)
        else:
            # If grades are provided directly, assume 1 credit per course
            total_credits = len(grades)
        
        gpa = self.calculate_gpa(grades)
        total_courses = len(grades)
        
        # Determine academic standing
        academic_standing = student.get("academic_standing")
        if academic_standing is None:
            if gpa >= 3.5:
                academic_standing = AcademicStanding.EXCELLENT
            elif gpa >= 3.0:
                academic_standing = AcademicStanding.GOOD
            elif gpa >= 2.0:
                academic_standing = AcademicStanding.SATISFACTORY
            else:
                academic_standing = AcademicStanding.NEEDS_IMPROVEMENT
        
        # Generate graduation requirements status
        graduation_requirements = {
            "total_credits_required": 24.0,
            "total_credits_earned": total_credits,
            "gpa_required": 2.0,
            "current_gpa": gpa,
            "requirements_met": [
                "total_credits" if total_credits >= 24.0 else "",
                "gpa" if gpa >= 2.0 else ""
            ]
        }
        
        # Remove empty requirements
        graduation_requirements["requirements_met"] = [req for req in graduation_requirements["requirements_met"] if req]
        
        return AcademicSummary(
            student_id=student_id,
            total_credits=total_credits,
            total_courses=total_courses,
            gpa=gpa,
            academic_standing=academic_standing,
            graduation_requirements=graduation_requirements,
            performance_trend=self._get_performance_trend(student_id),
            risk_factors=self._get_risk_factors(student),
            recommendations=self._generate_recommendations(student, gpa)
        )
    
    def get_student_performance_trend(self, student_id: str, grade_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get student performance trend analysis"""
        if grade_history is None:
            # Generate sample trend data for demonstration
            grade_history = [
                {"semester": "Fall 2023", "gpa": 2.5},
                {"semester": "Spring 2024", "gpa": 2.8},
                {"semester": "Fall 2024", "gpa": 3.2}
            ]
        
        if len(grade_history) < 2:
            return {"trend_direction": "insufficient_data", "improvement_rate": 0.0}
        
        # Calculate trend direction
        gpas = [record["gpa"] for record in grade_history]
        improvement_rate = (gpas[-1] - gpas[0]) / len(gpas)
        
        if improvement_rate > 0.1:
            trend_direction = "improving"
        elif improvement_rate < -0.1:
            trend_direction = "declining"
        else:
            trend_direction = "stable"
        
        return {
            "trend_direction": trend_direction,
            "improvement_rate": improvement_rate,
            "current_gpa": gpas[-1],
            "highest_gpa": max(gpas),
            "lowest_gpa": min(gpas),
            "semester_count": len(grade_history)
        }
    
    def identify_at_risk_students(self) -> List[Dict[str, Any]]:
        """Identify students who are at risk academically"""
        at_risk_students = []
        
        for student in self.students.values():
            if not student.get("is_active", True):
                continue
            
            risk_factors = []
            risk_level = RiskLevel.LOW
            
            # Check GPA risk
            gpa = student.get("gpa", 0.0)
            if gpa <= 1.5:
                risk_factors.append("very_low_gpa")
                risk_level = RiskLevel.CRITICAL
            elif gpa < 2.0:
                risk_factors.append("low_gpa")
                risk_level = RiskLevel.HIGH
            elif gpa < 2.5:
                risk_factors.append("below_average_gpa")
                risk_level = RiskLevel.MEDIUM
            
            # Check attendance risk
            attendance_rate = student.get("attendance_rate", 1.0)
            if attendance_rate < 0.7:
                risk_factors.append("very_low_attendance")
                risk_level = RiskLevel.CRITICAL
            elif attendance_rate < 0.8:
                risk_factors.append("low_attendance")
                if risk_level != RiskLevel.CRITICAL:
                    risk_level = RiskLevel.HIGH
            elif attendance_rate < 0.9:
                risk_factors.append("below_average_attendance")
                if risk_level != RiskLevel.CRITICAL and risk_level != RiskLevel.HIGH:
                    risk_level = RiskLevel.MEDIUM
            
            # Check academic standing
            academic_standing = student.get("academic_standing")
            if academic_standing == AcademicStanding.ACADEMIC_PROBATION:
                risk_factors.append("academic_probation")
                risk_level = RiskLevel.HIGH
            elif academic_standing == AcademicStanding.POOR:
                risk_factors.append("poor_academic_standing")
                risk_level = RiskLevel.CRITICAL
            
            if risk_factors:
                at_risk_students.append({
                    "student_id": student["student_id"],
                    "name": student["name"],
                    "risk_level": risk_level,
                    "risk_factors": risk_factors,
                    "gpa": gpa,
                    "attendance_rate": attendance_rate,
                    "academic_standing": academic_standing
                })
        
        return at_risk_students
    
    def generate_student_report(self, student_id: str) -> Dict[str, Any]:
        """Generate comprehensive student report"""
        student = self.students.get(student_id)
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found")
        
        # Get academic summary
        grades = [record.get("grade", 0) for record in self.academic_records 
                 if record.get("student_id") == student_id]
        academic_summary = self.get_student_academic_summary(student_id, grades)
        
        # Get performance trend
        grade_history = [{"semester": "Fall 2023", "gpa": 2.5}, 
                        {"semester": "Spring 2024", "gpa": 2.8}, 
                        {"semester": "Fall 2024", "gpa": 3.2}]
        performance_trend = self.get_student_performance_trend(student_id, grade_history)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(student, academic_summary.gpa)
        
        return {
            "student_info": {
                "id": student["id"],
                "name": student["name"],
                "student_id": student["student_id"],
                "email": student["email"],
                "grade_level": student["grade_level"],
                "enrollment_date": student["enrollment_date"],
                "department_id": student.get("department_id"),
                "advisor_id": student.get("advisor_id")
            },
            "academic_summary": academic_summary.model_dump(),
            "performance_trend": performance_trend,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
    
    def check_graduation_requirements(self, student_id: str, completed_requirements: Dict[str, Any]) -> GraduationStatus:
        """Check if student meets graduation requirements"""
        student = self.students.get(student_id)
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found")
        
        # Define graduation requirements
        requirements = {
            "total_credits": {"required": 24.0, "current": completed_requirements.get("total_credits", 0)},
            "gpa": {"required": 2.0, "current": completed_requirements.get("gpa", 0)},
            "community_service": {"required": 100, "current": completed_requirements.get("community_service_hours", 0)},
            "assessment_scores": {"required": 70, "current": max(completed_requirements.get("assessment_scores", [0]))},
            "core_courses": {"required": 8, "current": sum(1 for course in completed_requirements.get("courses", []) if course.get("core"))}
        }
        
        # Check each requirement
        met_requirements = 0
        missing_requirements = []
        
        for requirement_name, requirement_data in requirements.items():
            if requirement_data["current"] >= requirement_data["required"]:
                met_requirements += 1
            else:
                missing_requirements.append(f"{requirement_name}: {requirement_data['current']}/{requirement_data['required']}")
        
        # Determine eligibility
        is_eligible = met_requirements == len(requirements)
        graduation_date = completed_requirements.get("graduation_date") if is_eligible else None
        
        # Calculate estimated graduation date
        estimated_graduation_date = None
        if student["grade_level"] == GradeLevel.TWELFTH:
            estimated_graduation_date = datetime.now().date()
        elif student["grade_level"] == GradeLevel.ELEVENTH:
            estimated_graduation_date = (datetime.now() + timedelta(days=365)).date()
        
        # Determine honors status
        honors_status = None
        if completed_requirements.get("gpa", 0) >= 3.8:
            honors_status = "summa cum laude"
        elif completed_requirements.get("gpa", 0) >= 3.6:
            honors_status = "magna cum laude"
        elif completed_requirements.get("gpa", 0) >= 3.4:
            honors_status = "cum laude"
        
        return GraduationStatus(
            student_id=student_id,
            is_eligible=is_eligible,
            requirements_met=met_requirements,
            total_requirements=len(requirements),
            missing_requirements=missing_requirements,
            estimated_graduation_date=estimated_graduation_date,
            graduation_date=graduation_date,
            honors_status=honors_status
        )
    
    def validate_student_data(self, student_data: Dict[str, Any]) -> None:
        """Comprehensive student data validation"""
        required_fields = ["email", "password", "name", "student_id", "grade_level", "enrollment_date"]
        
        # Check required fields
        for field in required_fields:
            if field not in student_data or student_data[field] is None:
                raise ValidationError(f"Required field '{field}' is missing")
        
        # Validate email format
        email = student_data["email"]
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError("Invalid email format")
        
        # Validate password strength
        password = student_data["password"]
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        if not any(c.isupper() for c in password):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain at least one digit")
        
        # Validate student ID format
        student_id = student_data["student_id"]
        if not student_id.isalnum():
            raise ValidationError("Student ID must be alphanumeric")
        if len(student_id) < 3 or len(student_id) > 20:
            raise ValidationError("Student ID must be between 3 and 20 characters")
        
        # Validate grade level
        grade_level = student_data["grade_level"]
        valid_grades = [GradeLevel.NINTH, GradeLevel.TENTH, GradeLevel.ELEVENTH, GradeLevel.TWELFTH]
        if grade_level not in valid_grades:
            raise ValidationError(f"Grade level must be between 9 and 12, got: {grade_level}")
        
        # Validate enrollment date
        enrollment_date = student_data["enrollment_date"]
        if not isinstance(enrollment_date, date):
            raise ValidationError("Enrollment date must be a valid date")
        if enrollment_date > date.today():
            raise ValidationError("Enrollment date cannot be in the future")
        
        # Validate optional fields
        if "gpa" in student_data and student_data["gpa"] is not None:
            gpa = student_data["gpa"]
            if gpa < 0.0 or gpa > 4.0:
                raise ValidationError("GPA must be between 0.0 and 4.0")
        
        if "attendance_rate" in student_data and student_data["attendance_rate"] is not None:
            attendance_rate = student_data["attendance_rate"]
            if attendance_rate < 0.0 or attendance_rate > 1.0:
                raise ValidationError("Attendance rate must be between 0.0 and 1.0")
    
    def validate_student_update(self, update_data: Dict[str, Any]) -> None:
        """Validate student update data"""
        for field, value in update_data.items():
            if field == "gpa" and value is not None:
                if value < 0.0 or value > 4.0:
                    raise ValidationError("GPA must be between 0.0 and 4.0")
            elif field == "attendance_rate" and value is not None:
                if value < 0.0 or value > 1.0:
                    raise ValidationError("Attendance rate must be between 0.0 and 1.0")
            elif field == "academic_standing" and value is not None:
                if value not in [s.value for s in AcademicStanding]:
                    raise ValidationError("Invalid academic standing value")
    
    def _get_student_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get student by email (internal use)"""
        return next((s for s in self.students.values() if s["email"] == email), None)
    
    def _get_student_by_student_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get student by student ID (internal use)"""
        return next((s for s in self.students.values() if s["student_id"] == student_id), None)
    
    def _matches_search_criteria(self, student: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if student matches search criteria"""
        if "name" in criteria and criteria["name"]:
            if criteria["name"].lower() not in student["name"].lower():
                return False
        
        if "email" in criteria and criteria["email"]:
            if student["email"] != criteria["email"]:
                return False
        
        if "student_id" in criteria and criteria["student_id"]:
            if student["student_id"] != criteria["student_id"]:
                return False
        
        if "grade_level" in criteria and criteria["grade_level"] is not None:
            if student["grade_level"] != criteria["grade_level"]:
                return False
        
        if "department_id" in criteria and criteria["department_id"]:
            if student.get("department_id") != criteria["department_id"]:
                return False
        
        if "advisor_id" in criteria and criteria["advisor_id"]:
            if student.get("advisor_id") != criteria["advisor_id"]:
                return False
        
        if "is_active" in criteria and criteria["is_active"] is not None:
            if student["is_active"] != criteria["is_active"]:
                return False
        
        return True
    
    def _get_performance_trend(self, student_id: str) -> Optional[str]:
        """Get performance trend (internal use)"""
        # Simplified trend calculation
        student = self.students.get(student_id)
        if not student:
            return None
        
        gpa = student.get("gpa", 0.0)
        if gpa >= 3.5:
            return "excellent"
        elif gpa >= 3.0:
            return "improving"
        elif gpa >= 2.5:
            return "stable"
        elif gpa >= 2.0:
            return "declining"
        else:
            return "critical"
    
    def _get_risk_factors(self, student: Dict[str, Any]) -> List[str]:
        """Get risk factors for a student (internal use)"""
        risk_factors = []
        
        gpa = student.get("gpa", 0.0)
        if gpa < 2.0:
            risk_factors.append("low_gpa")
        
        attendance_rate = student.get("attendance_rate", 1.0)
        if attendance_rate < 0.8:
            risk_factors.append("low_attendance")
        
        academic_standing = student.get("academic_standing")
        if academic_standing == AcademicStanding.ACADEMIC_PROBATION:
            risk_factors.append("academic_probation")
        
        return risk_factors
    
    def _generate_recommendations(self, student: Dict[str, Any], gpa: float) -> List[str]:
        """Generate recommendations for a student (internal use)"""
        recommendations = []
        
        if gpa < 2.0:
            recommendations.append("Consider tutoring or additional academic support")
        
        attendance_rate = student.get("attendance_rate", 1.0)
        if attendance_rate < 0.9:
            recommendations.append("Improve attendance for better academic outcomes")
        
        if student.get("grade_level") == GradeLevel.TWELFTH and gpa < 2.5:
            recommendations.append("Focus on final coursework to meet graduation requirements")
        
        if not recommendations:
            recommendations.append("Continue current academic performance")
        
        return recommendations
    
    def get_student_audit_trail(self, student_id: str) -> List[StudentAudit]:
        """Get audit trail for a specific student"""
        audit_records = [record for record in self.audit_trail 
                        if record["student_id"] == student_id]
        
        return [StudentAudit(**record) for record in audit_records]
    
    def get_student_statistics(self) -> StudentStatistics:
        """Get comprehensive student statistics"""
        total_students = len(self.students)
        active_students = sum(1 for s in self.students.values() if s.get("is_active", True))
        inactive_students = total_students - active_students
        
        # Statistics by grade level
        by_grade_level = {}
        for grade_level in GradeLevel:
            count = sum(1 for s in self.students.values() if s.get("grade_level") == grade_level)
            by_grade_level[grade_level] = count
        
        # Statistics by department
        by_department = {}
        for student in self.students.values():
            dept_id = student.get("department_id")
            if dept_id:
                by_department[dept_id] = by_department.get(dept_id, 0) + 1
        
        # Statistics by advisor
        by_advisor = {}
        for student in self.students.values():
            advisor_id = student.get("advisor_id")
            if advisor_id:
                by_advisor[advisor_id] = by_advisor.get(advisor_id, 0) + 1
        
        # Calculate average GPA and attendance
        gpas = [s.get("gpa", 0.0) for s in self.students.values()]
        attendances = [s.get("attendance_rate", 0.0) for s in self.students.values() if s.get("attendance_rate") is not None]
        
        average_gpa = sum(gpas) / len(gpas) if gpas else 0.0
        average_attendance = sum(attendances) / len(attendances) if attendances else 0.0
        
        # Statistics by risk level
        by_risk_level = {}
        for risk_level in RiskLevel:
            by_risk_level[risk_level] = 0
        
        # Calculate risk levels for each student
        for student in self.students.values():
            if not student.get("is_active", True):
                continue
            
            risk_factors = []
            gpa = student.get("gpa", 0.0)
            attendance_rate = student.get("attendance_rate", 1.0)
            
            # Determine risk level
            attendance_rate = student.get("attendance_rate", 1.0)
            if attendance_rate is not None:
                if gpa <= 1.5 or attendance_rate < 0.7:
                    risk_level = RiskLevel.CRITICAL
                elif gpa < 2.0 or attendance_rate < 0.8:
                    risk_level = RiskLevel.HIGH
                elif gpa < 2.5 or attendance_rate < 0.9:
                    risk_level = RiskLevel.MEDIUM
                else:
                    risk_level = RiskLevel.LOW
            else:
                # If attendance rate is None, only use GPA for risk assessment
                if gpa <= 1.5:
                    risk_level = RiskLevel.CRITICAL
                elif gpa < 2.0:
                    risk_level = RiskLevel.HIGH
                elif gpa < 2.5:
                    risk_level = RiskLevel.MEDIUM
                else:
                    risk_level = RiskLevel.LOW
            
            by_risk_level[risk_level] = by_risk_level.get(risk_level, 0) + 1
        
        return StudentStatistics(
            total_students=total_students,
            active_students=active_students,
            inactive_students=inactive_students,
            by_grade_level=by_grade_level,
            by_department=by_department,
            by_advisor=by_advisor,
            by_risk_level=by_risk_level,
            average_gpa=average_gpa,
            average_attendance=average_attendance
        )