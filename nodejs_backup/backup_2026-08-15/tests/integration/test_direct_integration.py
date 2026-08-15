"""
Direct Integration Tests

This module provides direct integration tests that can be run without pytest fixtures.

Author: Edu-Flow Team
"""

import asyncio
from datetime import date
from typing import Dict, List, Any

from src.infrastructure.services.student_service import StudentService
from src.infrastructure.services.teacher_service import TeacherService
from src.infrastructure.services.course_service import CourseService
from src.infrastructure.services.department_service import DepartmentService
from src.models.student import StudentResponse, GradeLevel, UserRole
from src.models.teacher import TeacherResponse
from src.models.course import CourseResponse
from src.models.department_model import DepartmentResponse


class SimpleDepartmentRepository:
    """Simple department repository for testing."""
    
    def __init__(self):
        self.departments = {}
        self.next_id = 1
    
    async def create(self, dept_data: Dict[str, Any]) -> DepartmentResponse:
        """Create a new department."""
        dept_id = str(self.next_id)
        self.next_id += 1
        
        dept = DepartmentResponse(
            id=dept_id,
            name=dept_data.get('name', ''),
            department_code=dept_data.get('department_code', ''),
            description=dept_data.get('description', ''),
            head_id=dept_data.get('head_id', '')
        )
        
        self.departments[dept_id] = dept
        return dept
    
    async def get(self, dept_id: str) -> DepartmentResponse:
        """Get a department by ID."""
        if dept_id not in self.departments:
            raise ValueError(f"Department {dept_id} not found")
        return self.departments[dept_id]
    
    async def get_all(self) -> List[DepartmentResponse]:
        """Get all departments."""
        return list(self.departments.values())


class SimpleTeacherRepository:
    """Simple teacher repository for testing."""
    
    def __init__(self):
        self.teachers = {}
        self.next_id = 1
    
    async def create(self, teacher_data: Dict[str, Any]) -> TeacherResponse:
        """Create a new teacher."""
        teacher_id = str(self.next_id)
        self.next_id += 1
        
        teacher = TeacherResponse(
            id=teacher_id,
            name=teacher_data.get('name', ''),
            email=teacher_data.get('email', ''),
            employee_id=teacher_data.get('employee_id', ''),
            department_id=teacher_data.get('department_id', ''),
            specialization=teacher_data.get('specialization', ''),
            qualification=teacher_data.get('qualification', ''),
            experience_years=teacher_data.get('experience_years', 0)
        )
        
        self.teachers[teacher_id] = teacher
        return teacher
    
    async def get(self, teacher_id: str) -> TeacherResponse:
        """Get a teacher by ID."""
        if teacher_id not in self.teachers:
            raise ValueError(f"Teacher {teacher_id} not found")
        return self.teachers[teacher_id]
    
    async def get_by_department(self, department_id: str) -> List[TeacherResponse]:
        """Get teachers by department."""
        return [t for t in self.teachers.values() if t.department_id == department_id]


class SimpleStudentRepository:
    """Simple student repository for testing."""
    
    def __init__(self):
        self.students = {}
        self.next_id = 1
    
    async def create(self, student_data: Dict[str, Any]) -> StudentResponse:
        """Create a new student."""
        student_id = str(self.next_id)
        self.next_id += 1
        
        student = StudentResponse(
            id=student_id,
            name=student_data.get('name', ''),
            email=student_data.get('email', ''),
            student_id=student_data.get('student_id', ''),
            phone=student_data.get('phone', ''),
            department_id=student_data.get('department_id', ''),
            gpa=student_data.get('gpa', 0.0),
            enrollment_date=student_data.get('enrollment_date', date.today()),
            grade_level=student_data.get('grade_level', GradeLevel.TENTH)
        )
        
        self.students[student_id] = student
        return student
    
    async def get(self, student_id: str) -> StudentResponse:
        """Get a student by ID."""
        if student_id not in self.students:
            raise ValueError(f"Student {student_id} not found")
        return self.students[student_id]
    
    async def get_by_department(self, department_id: str) -> List[StudentResponse]:
        """Get students by department."""
        return [s for s in self.students.values() if s.department_id == department_id]


class SimpleCourseRepository:
    """Simple course repository for testing."""
    
    def __init__(self):
        self.courses = {}
        self.next_id = 1
    
    async def create(self, course_data: Dict[str, Any]) -> CourseResponse:
        """Create a new course."""
        course_id = str(self.next_id)
        self.next_id += 1
        
        course = CourseResponse(
            id=course_id,
            name=course_data.get('name', ''),
            code=course_data.get('code', ''),
            description=course_data.get('description', ''),
            credits=course_data.get('credits', 0),
            department_id=course_data.get('department_id', ''),
            level=course_data.get('level', GradeLevel.TENTH),
            prerequisites=course_data.get('prerequisites', [])
        )
        
        self.courses[course_id] = course
        return course
    
    async def get(self, course_id: str) -> CourseResponse:
        """Get a course by ID."""
        if course_id not in self.courses:
            raise ValueError(f"Course {course_id} not found")
        return self.courses[course_id]
    
    async def get_by_department(self, department_id: str) -> List[CourseResponse]:
        """Get courses by department."""
        return [c for c in self.courses.values() if c.department_id == department_id]


def test_department_teacher_course_integration():
    """Test integration between department, teacher, and course services."""
    print("Starting Department-Teacher-Course Integration Test...")
    
    # Create repositories
    dept_repo = SimpleDepartmentRepository()
    teacher_repo = SimpleTeacherRepository()
    course_repo = SimpleCourseRepository()
    student_repo = SimpleStudentRepository()
    
    # Create services
    student_service = StudentService(student_repo)
    teacher_service = TeacherService(teacher_repo)
    course_service = CourseService(course_repo)
    department_service = DepartmentService(dept_repo)
    
    # Create a department
    dept_data = {
        "name": "Computer Science",
        "department_code": "CSF",
        "description": "Computer Science Department",
        "faculty_id": "F001",
        "head_id": "H001"
    }
    
    department = asyncio.run(department_service.create_department(dept_data))
    print(f"✓ Created department: {department.name} ({department.department_code})")
    
    # Create a teacher in that department
    teacher_data = {
        "name": "Dr. Smith",
        "email": "smith@example.com",
        "employee_id": "T001",
        "department_id": department.id,
        "specialization": "Algorithms",
        "qualification": "PhD",
        "experience_years": 10
    }
    
    teacher = asyncio.run(teacher_service.create_teacher(teacher_data))
    print(f"✓ Created teacher: {teacher.name} in {department.name}")
    
    # Create a course in that department
    course_data = {
        "name": "Data Structures",
        "code": "CS101",
        "description": "Introduction to data structures",
        "credits": 3,
        "department_id": department.id,
        "level": GradeLevel.TENTH,
        "prerequisites": []
    }
    
    course = asyncio.run(course_service.create_course(course_data))
    print(f"✓ Created course: {course.name} in {department.name}")
    
    # Verify integration - teacher and course are in the same department
    teachers_in_dept = asyncio.run(teacher_service.get_teachers_by_department(department.id))
    courses_in_dept = asyncio.run(course_service.get_courses_by_department(department.id))
    
    print(f"✓ Found {len(teachers_in_dept)} teachers in {department.name}")
    print(f"✓ Found {len(courses_in_dept)} courses in {department.name}")
    
    assert len(teachers_in_dept) == 1
    assert len(courses_in_dept) == 1
    assert teachers_in_dept[0].department_id == department.id
    assert courses_in_dept[0].department_id == department.id
    
    print("✓ Department-Teacher-Course Integration Test PASSED!")


def test_student_enrollment_flow():
    """Test student enrollment flow through multiple services."""
    print("\nStarting Student Enrollment Flow Test...")
    
    # Create repositories
    dept_repo = SimpleDepartmentRepository()
    teacher_repo = SimpleTeacherRepository()
    course_repo = SimpleCourseRepository()
    student_repo = SimpleStudentRepository()
    
    # Create services
    student_service = StudentService(student_repo)
    teacher_service = TeacherService(teacher_repo)
    course_service = CourseService(course_repo)
    department_service = DepartmentService(dept_repo)
    
    # Create a department
    dept_data = {
        "name": "Mathematics",
        "department_code": "MATH",
        "description": "Mathematics Department",
        "faculty_id": "F002",
        "head_id": "H002"
    }
    
    department = asyncio.run(department_service.create_department(dept_data))
    print(f"✓ Created department: {department.name} ({department.code})")
    
    # Create a student
    student_data = {
        "email": "student1@example.com",
        "password": "Password123",
        "name": "Alice Johnson",
        "student_id": "S001",
        "enrollment_date": date(2020, 9, 1),
        "grade_level": GradeLevel.TENTH,
        "department_id": department.id,
        "gpa": 3.8
    }
    
    student = asyncio.run(student_service.create_student(student_data))
    print(f"✓ Created student: {student.name} in {department.name}")
    
    # Create a teacher
    teacher_data = {
        "name": "Dr. Johnson",
        "email": "johnson@example.com",
        "employee_id": "T002",
        "department_id": department.id,
        "specialization": "Calculus",
        "qualification": "PhD",
        "experience_years": 8
    }
    
    teacher = asyncio.run(teacher_service.create_teacher(teacher_data))
    print(f"✓ Created teacher: {teacher.name} in {department.name}")
    
    # Create a course
    course_data = {
        "name": "Calculus I",
        "code": "MATH101", 
        "description": "Introduction to differential calculus",
        "credits": 4,
        "department_id": department.id,
        "level": GradeLevel.TENTH,
        "prerequisites": []
    }
    
    course = asyncio.run(course_service.create_course(course_data))
    print(f"✓ Created course: {course.name} in {department.name}")
    
    # Verify the student is in the right department
    assert student.department_id == department.id
    
    # Verify the teacher is in the right department
    assert teacher.department_id == department.id
    
    # Verify the course is in the right department
    assert course.department_id == department.id
    
    # Test student statistics
    stats = asyncio.run(student_service.get_student_statistics())
    print(f"✓ Student statistics: {stats.total_students} students, average GPA: {stats.average_gpa:.2f}")
    
    assert stats.total_students >= 1
    assert stats.average_gpa > 0
    
    print("✓ Student Enrollment Flow Test PASSED!")


def test_bulk_department_course_creation():
    """Test bulk creation of departments and courses."""
    print("\nStarting Bulk Department-Course Creation Test...")
    
    # Create repositories
    dept_repo = SimpleDepartmentRepository()
    teacher_repo = SimpleTeacherRepository()
    course_repo = SimpleCourseRepository()
    student_repo = SimpleStudentRepository()
    
    # Create services
    student_service = StudentService(student_repo)
    teacher_service = TeacherService(teacher_repo)
    course_service = CourseService(course_repo)
    department_service = DepartmentService(dept_repo)
    
    # Create multiple departments
    dept1 = asyncio.run(department_service.create_department({
        "name": "Computer Science",
        "department_code": "CSF",
        "description": "Computer Science Department",
        "faculty_id": "F001",
        "head_id": "H001"
    }))
    
    dept2 = asyncio.run(department_service.create_department({
        "name": "Mathematics",
        "department_code": "MTH",
        "description": "Mathematics Department",
        "faculty_id": "F002",
        "head_id": "H002"
    }))
    
    dept3 = asyncio.run(department_service.create_department({
        "name": "Physics",
        "department_code": "PHY",
        "description": "Physics Department",
        "faculty_id": "F003",
        "head_id": "H003"
    }))
    
    print(f"✓ Created {len([dept1, dept2, dept3])} departments")
    
    # Create courses for each department
    cs_course = asyncio.run(course_service.create_course({
        "name": "Algorithms",
        "code": "CS201",
        "description": "Advanced algorithms",
        "credits": 4,
        "department_id": dept1.id,
        "level": GradeLevel.ELEVENTH,
        "prerequisites": []
    }))
    
    math_course = asyncio.run(course_service.create_course({
        "name": "Linear Algebra",
        "code": "MATH201",
        "description": "Introduction to linear algebra",
        "credits": 3,
        "department_id": dept2.id,
        "level": GradeLevel.ELEVENTH,
        "prerequisites": []
    }))
    
    physics_course = asyncio.run(course_service.create_course({
        "name": "Quantum Mechanics",
        "code": "PHYS301",
        "description": "Introduction to quantum mechanics",
        "credits": 4,
        "department_id": dept3.id,
        "level": GradeLevel.TWELFTH,
        "prerequisites": []
    }))
    
    print(f"✓ Created {len([cs_course, math_course, physics_course])} courses")
    
    # Verify all departments have their courses
    cs_courses = asyncio.run(course_service.get_courses_by_department(dept1.id))
    math_courses = asyncio.run(course_service.get_courses_by_department(dept2.id))
    physics_courses = asyncio.run(course_service.get_courses_by_department(dept3.id))
    
    print(f"✓ CS department has {len(cs_courses)} courses")
    print(f"✓ Math department has {len(math_courses)} courses")
    print(f"✓ Physics department has {len(physics_courses)} courses")
    
    assert len(cs_courses) == 1
    assert len(math_courses) == 1
    assert len(physics_courses) == 1
    
    assert cs_courses[0].department_id == dept1.id
    assert math_courses[0].department_id == dept2.id
    assert physics_courses[0].department_id == dept3.id
    
    # Verify courses are at correct levels
    assert cs_courses[0].level == GradeLevel.ELEVENTH
    assert math_courses[0].level == GradeLevel.ELEVENTH
    assert physics_courses[0].level == GradeLevel.TWELFTH
    
    print("✓ Bulk Department-Course Creation Test PASSED!")


if __name__ == "__main__":
    print("Running Integration Tests...")
    print("=" * 50)
    
    try:
        test_department_teacher_course_integration()
        test_student_enrollment_flow()
        test_bulk_department_course_creation()
        
        print("\n" + "=" * 50)
        print("ALL INTEGRATION TESTS PASSED! 🎉")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()