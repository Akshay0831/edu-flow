"""Course management service for FastAPI."""

from datetime import datetime, date, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4

from src.models.course import (
    Course, CourseCreate, CourseUpdate, CourseResponse, CourseCreateResponse,
    CourseOffering, OfferingCreate, OfferingUpdate, OfferingResponse,
    Enrollment, EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse,
    Department, Prerequisite, CourseStatistics, EnrollmentSummary,
    CourseStatus, CourseLevel, CreditType, Semester, Grade
)
from src.core.exceptions import ValidationError, NotFoundError, UnauthorizedError
from src.auth.service import AuthService


class CourseService:
    """Course management service."""

    def __init__(self, auth_service: AuthService):
        """Initialize course service."""
        self.auth_service = auth_service
        self.courses: Dict[str, Course] = {}
        self.offerings: Dict[str, CourseOffering] = {}
        self.enrollments: Dict[str, Enrollment] = {}
        self.departments: Dict[str, Department] = {
            "DEPT001": Department(
                department_id="DEPT001",
                name="Computer Science",
                code="CS",
                description="Computer Science Department"
            ),
            "DEPT002": Department(
                department_id="DEPT002",
                name="Mathematics",
                code="MATH",
                description="Mathematics Department"
            ),
            "DEPT003": Department(
                department_id="DEPT003",
                name="Physics",
                code="PHY",
                description="Physics Department"
            )
        }

    # Course Management Methods
    
    def create_course(self, course_data: CourseCreate, user_id: str) -> CourseCreateResponse:
        """Create a new course."""
        # Check if user has permission
        if not self.auth_service.has_permission(user_id, "create_course"):
            raise UnauthorizedError("User does not have permission to create courses")
        
        # Check for duplicate course code
        for course in self.courses.values():
            if course.code == course_data.code:
                raise ValidationError(f"Course code {course_data.code} already exists")
        
        # Create course
        course_data_dict = course_data.model_dump()
        course_data_dict.update({
            'is_active': True,
            'prerequisites_approved': False,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        })
        
        course = Course(**course_data_dict)
        
        self.courses[course.course_id] = course
        
        return CourseCreateResponse(
            course=course,
            message="Course created successfully"
        )

    def get_course(self, course_id: str) -> Course:
        """Get a course by ID."""
        if course_id not in self.courses:
            raise NotFoundError(f"Course {course_id} not found")
        
        course = self.courses[course_id]
        
        # Filter out inactive courses if user doesn't have permission
        if not course.is_active:
            raise NotFoundError(f"Course {course_id} not found")
        
        return course

    def get_course_by_code(self, course_code: str) -> Course:
        """Get a course by code."""
        for course in self.courses.values():
            if course.code == course_code and course.is_active:
                return course
        
        raise NotFoundError(f"Course with code {course_code} not found")

    def get_all_courses(self, limit: Optional[int] = None, offset: int = 0) -> List[Course]:
        """Get all courses."""
        courses = [course for course in self.courses.values() if course.is_active]
        courses.sort(key=lambda x: x.title)
        
        if limit is not None:
            return courses[offset:offset + limit]
        
        return courses[offset:]

    def update_course(self, course_id: str, update_data: CourseUpdate, user_id: str) -> Course:
        """Update a course."""
        # Check if user has permission
        if not self.auth_service.has_permission(user_id, "update_course"):
            raise UnauthorizedError("User does not have permission to update courses")
        
        course = self.get_course(course_id)
        
        # Check for duplicate course code
        if hasattr(update_data, 'code') and update_data.code and update_data.code != course.code:
            for existing_course in self.courses.values():
                if existing_course.code == update_data.code and existing_course.course_id != course_id:
                    raise ValidationError(f"Course code {update_data.code} already exists")
        
        # Update course
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(course, key, value)
        
        course.updated_at = datetime.now(timezone.utc)
        
        return course

    def delete_course(self, course_id: str, user_id: str) -> bool:
        """Delete a course (soft delete)."""
        # Check if user has permission
        if not self.auth_service.has_permission(user_id, "delete_course"):
            raise UnauthorizedError("User does not have permission to delete courses")
        
        course = self.get_course(course_id)
        course.is_active = False
        course.updated_at = datetime.now(timezone.utc)
        
        # Return the course with updated state instead of raising NotFoundError
        return True

    def search_courses(self, filters: Dict[str, Any]) -> List[Course]:
        """Search courses by various filters."""
        courses = self.get_all_courses()
        results = courses
        
        # Apply filters
        if 'title' in filters:
            search_term = filters['title'].lower()
            results = [c for c in results if search_term in c.title.lower()]
        
        if 'code' in filters:
            search_term = filters['code'].lower()
            results = [c for c in results if search_term in c.code.lower()]
        
        if 'department_id' in filters:
            dept_id = filters['department_id']
            results = [c for c in results if c.department_id == dept_id]
        
        if 'level' in filters:
            level = filters['level']
            results = [c for c in results if c.level == level]
        
        if 'semester' in filters:
            semester = filters['semester']
            results = [c for c in results if semester in c.typical_semesters]
        
        if 'min_credits' in filters:
            min_credits = filters['min_credits']
            results = [c for c in results if c.credits >= min_credits]
        
        if 'max_credits' in filters:
            max_credits = filters['max_credits']
            results = [c for c in results if c.credits <= max_credits]
        
        return results

    # Course Offering Methods
    
    def create_offering(self, offering_data: OfferingCreate, user_id: str) -> OfferingResponse:
        """Create a new course offering."""
        # Check if user has permission
        if not self.auth_service.has_permission(user_id, "create_offering"):
            raise UnauthorizedError("User does not have permission to create offerings")
        
        # Check if course exists
        if offering_data.course_id not in self.courses:
            raise NotFoundError(f"Course {offering_data.course_id} not found")
        
        # Create offering
        offering = CourseOffering(
            **offering_data.model_dump(exclude_unset=True),
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.offerings[offering.offering_id] = offering
        
        return OfferingResponse(**offering.model_dump())

    def get_offering(self, offering_id: str) -> CourseOffering:
        """Get a course offering by ID."""
        if offering_id not in self.offerings:
            raise NotFoundError(f"Offering {offering_id} not found")
        
        return self.offerings[offering_id]

    def get_course_offerings(self, course_id: str) -> List[CourseOffering]:
        """Get all offerings for a course."""
        return [offering for offering in self.offerings.values() 
                if offering.course_id == course_id and offering.is_active]

    def update_offering(self, offering_id: str, update_data: OfferingUpdate, user_id: str) -> CourseOffering:
        """Update a course offering."""
        # Check if user has permission
        if not self.auth_service.has_permission(user_id, "update_offering"):
            raise UnauthorizedError("User does not have permission to update offerings")
        
        offering = self.get_offering(offering_id)
        
        # Update offering
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(offering, key, value)
        
        offering.updated_at = datetime.now(timezone.utc)
        
        return offering

    def delete_offering(self, offering_id: str, user_id: str) -> bool:
        """Delete a course offering."""
        # Check if user has permission
        if not self.auth_service.has_permission(user_id, "delete_offering"):
            raise UnauthorizedError("User does not have permission to delete offerings")
        
        offering = self.get_offering(offering_id)
        offering.is_active = False
        offering.updated_at = datetime.now(timezone.utc)
        
        return True

    # Enrollment Methods
    
    def enroll_student(self, student_id: str, offering_id: str, user_id: str) -> EnrollmentResponse:
        """Enroll a student in a course offering."""
        # Check if user has permission
        if not self.auth_service.has_permission(user_id, "enroll_student"):
            raise UnauthorizedError("User does not have permission to enroll students")
        
        # Check if offering exists
        if offering_id not in self.offerings:
            raise NotFoundError(f"Offering {offering_id} not found")
        
        offering = self.offerings[offering_id]
        
        # Check if student is already enrolled
        for enrollment in self.enrollments.values():
            if (enrollment.student_id == student_id and 
                enrollment.offering_id == offering_id and 
                enrollment.is_active):
                raise ValidationError(f"Student {student_id} is already enrolled in offering {offering_id}")
        
        # Check if course is full
        if offering.current_enrollment >= offering.max_enrollment:
            # Check if waitlist is available
            if offering.current_waitlist < offering.waitlist_capacity:
                status = "waitlisted"
                offering.current_waitlist += 1
            else:
                raise ValidationError(f"Course {offering_id} is full")
        else:
            status = "enrolled"
            offering.current_enrollment += 1
        
        # Create enrollment
        enrollment = Enrollment(
            student_id=student_id,
            offering_id=offering_id,
            course_id=offering.course_id,
            status=status,
            is_active=True,
            enrollment_date=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.enrollments[enrollment.enrollment_id] = enrollment
        
        return EnrollmentResponse(**enrollment.model_dump())

    def get_student_enrollments(self, student_id: str) -> List[Enrollment]:
        """Get all enrollments for a student."""
        return [enrollment for enrollment in self.enrollments.values() 
                if enrollment.student_id == student_id and enrollment.is_active]

    def get_offering_enrollments(self, offering_id: str) -> List[Enrollment]:
        """Get all enrollments for an offering."""
        return [enrollment for enrollment in self.enrollments.values() 
                if enrollment.offering_id == offering_id and enrollment.is_active]

    def update_enrollment(self, enrollment_id: str, update_data: EnrollmentUpdate, user_id: str) -> Enrollment:
        """Update an enrollment."""
        # Check if user has permission
        if not self.auth_service.has_permission(user_id, "update_enrollment"):
            raise UnauthorizedError("User does not have permission to update enrollments")
        
        enrollment = self.get_enrollment(enrollment_id)
        
        # Update enrollment
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(enrollment, key, value)
        
        # Automatically set status to completed when final_score is provided
        if 'final_score' in update_dict and update_dict['final_score'] is not None:
            enrollment.status = "completed"
        
        enrollment.updated_at = datetime.now(timezone.utc)
        
        return enrollment

    def drop_enrollment(self, enrollment_id: str, user_id: str) -> bool:
        """Drop an enrollment."""
        # Check if user has permission
        if not self.auth_service.has_permission(user_id, "drop_enrollment"):
            raise UnauthorizedError("User does not have permission to drop enrollments")
        
        enrollment = self.get_enrollment(enrollment_id)
        enrollment.is_active = False
        enrollment.drop_date = datetime.now(timezone.utc)
        enrollment.updated_at = datetime.now(timezone.utc)
        
        # Update offering enrollment count
        offering = self.offerings.get(enrollment.offering_id)
        if offering:
            if enrollment.status == "enrolled":
                offering.current_enrollment -= 1
            elif enrollment.status == "waitlisted":
                offering.current_waitlist -= 1
        
        return True

    def get_enrollment(self, enrollment_id: str) -> Enrollment:
        """Get an enrollment by ID."""
        if enrollment_id not in self.enrollments:
            raise NotFoundError(f"Enrollment {enrollment_id} not found")
        
        return self.enrollments[enrollment_id]

    # Analytics Methods
    
    def get_course_statistics(self, course_id: str) -> CourseStatistics:
        """Get statistics for a course."""
        course = self.get_course(course_id)
        
        # Get course enrollments across all offerings
        course_offerings = [o for o in self.offerings.values() if o.course_id == course_id]
        course_enrollments = []
        for offering in course_offerings:
            course_enrollments.extend(self.get_offering_enrollments(offering.offering_id))
        
        completions = [e for e in course_enrollments if e.status == "completed"]
        total_enrollments = len(course_enrollments)
        total_completions = len(completions)
        
        # Calculate statistics
        average_enrollment = total_enrollments / max(1, len([o for o in self.offerings.values() if o.course_id == course_id]))
        completion_rate = total_completions / max(1, total_enrollments)
        
        # Calculate average score
        scores = [e.final_score for e in completions if e.final_score is not None]
        average_score = sum(scores) / max(1, len(scores)) if scores else None
        
        # Create grade distribution
        grade_counts = {}
        for enrollment in completions:
            if enrollment.grade:
                grade_counts[enrollment.grade] = grade_counts.get(enrollment.grade, 0) + 1
        
        # Create semester distribution
        semester_counts = {}
        for offering in self.offerings.values():
            if offering.course_id == course_id and offering.is_active:
                sem_key = f"{offering.academic_year}_{offering.semester}"
                semester_counts[sem_key] = semester_counts.get(sem_key, 0) + 1
        
        # Get department name
        department = self.departments.get(course.department_id, Department(
            department_id=course.department_id,
            name="Unknown Department",
            code="UNK",
            description=""
        ))
        
        return CourseStatistics(
            course_id=course_id,
            title=course.title,
            code=course.code,
            department_name=department.name,
            total_offerings=len([o for o in self.offerings.values() if o.course_id == course_id]),
            total_enrollments=total_enrollments,
            total_completions=total_completions,
            average_enrollment=average_enrollment,
            completion_rate=completion_rate,
            average_score=average_score,
            grade_distribution=grade_counts,
            semester_distribution=semester_counts,
            instructor_distribution={},  # TODO: Implement instructor distribution
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    def get_student_enrollment_summary(self, student_id: str) -> EnrollmentSummary:
        """Get enrollment summary for a student."""
        enrollments = self.get_student_enrollments(student_id)
        active_enrollments = [e for e in enrollments if e.status != "completed"]
        completed_enrollments = [e for e in enrollments if e.status == "completed"]
        
        # Calculate total credits
        total_credits = sum(e.credits_earned or 0 for e in completed_enrollments)
        
        # Calculate GPA (weighted average)
        grade_points = {
            'A': 4.0,
            'B+': 3.5,
            'B': 3.0,
            'C+': 2.5,
            'C': 2.0,
            'D+': 1.5,
            'D': 1.0,
            'F': 0.0
        }
        
        total_points = 0
        graded_courses = 0
        for enrollment in completed_enrollments:
            if enrollment.grade and enrollment.grade in grade_points:
                total_points += grade_points[enrollment.grade]
                graded_courses += 1
        
        gpa = total_points / max(1, graded_courses)
        
        # Calculate average attendance and score
        attendance_rates = [e.attendance_rate for e in completed_enrollments if e.attendance_rate is not None]
        scores = [e.final_score for e in completed_enrollments if e.final_score is not None]
        
        average_attendance = sum(attendance_rates) / max(1, len(attendance_rates)) if attendance_rates else None
        average_score = sum(scores) / max(1, len(scores)) if scores else None
        
        # Create grade distribution
        grade_counts = {}
        for enrollment in completed_enrollments:
            if enrollment.grade:
                grade_counts[enrollment.grade] = grade_counts.get(enrollment.grade, 0) + 1
        
        # Create department distribution
        dept_counts = {}
        for enrollment in enrollments:
            course = self.get_course(enrollment.course_id)
            dept = self.departments.get(course.department_id, Department(
                department_id=course.department_id,
                name="Unknown",
                code="UNK",
                description=""
            ))
            dept_counts[dept.name] = dept_counts.get(dept.name, 0) + 1
        
        # Create level distribution
        level_counts = {}
        for enrollment in enrollments:
            course = self.get_course(enrollment.course_id)
            level_counts[course.level] = level_counts.get(course.level, 0) + 1
        
        return EnrollmentSummary(
            student_id=student_id,
            total_courses=len(enrollments),
            total_credits=total_credits,
            active_enrollments=len(active_enrollments),
            completed_enrollments=len(completed_enrollments),
            gpa=gpa,
            average_attendance=average_attendance,
            average_score=average_score,
            grade_distribution=grade_counts,
            department_distribution=dept_counts,
            level_distribution=level_counts,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    # Department Methods
    
    def get_all_departments(self) -> List[Department]:
        """Get all departments."""
        return list(self.departments.values())

    # Prerequisite Methods
    
    def get_course_prerequisites(self, course_id: str) -> List[Prerequisite]:
        """Get prerequisites for a course."""
        course = self.get_course(course_id)
        return course.prerequisites

    def add_prerequisite(self, course_id: str, prerequisite_data: Dict[str, Any], user_id: str) -> str:
        """Add a prerequisite to a course."""
        # Check if user has permission
        if not self.auth_service.has_permission(user_id, "update_course"):
            raise UnauthorizedError("User does not have permission to update courses")
        
        course = self.get_course(course_id)
        
        # Check if prerequisite course exists
        if prerequisite_data['prerequisite_course_id'] not in self.courses:
            raise NotFoundError(f"Prerequisite course {prerequisite_data['prerequisite_course_id']} not found")
        
        # Create prerequisite
        prerequisite = Prerequisite(
            course_id=course_id,
            prerequisite_course_id=prerequisite_data['prerequisite_course_id'],
            min_grade=prerequisite_data.get('min_grade'),
            created_at=datetime.now(timezone.utc)
        )
        
        course.prerequisites.append(prerequisite)
        course.updated_at = datetime.now(timezone.utc)
        
        return f"Prerequisite added successfully for course {course_id}"

    def remove_prerequisite(self, course_id: str, prerequisite_course_id: str, user_id: str) -> str:
        """Remove a prerequisite from a course."""
        # Check if user has permission
        if not self.auth_service.has_permission(user_id, "update_course"):
            raise UnauthorizedError("User does not have permission to update courses")
        
        course = self.get_course(course_id)
        
        # Remove prerequisite
        course.prerequisites = [
            p for p in course.prerequisites 
            if p.prerequisite_course_id != prerequisite_course_id
        ]
        
        course.updated_at = datetime.now(timezone.utc)
        
        return f"Prerequisite removed successfully from course {course_id}"