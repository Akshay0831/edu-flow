"""
Mock Database Manager

This module provides a comprehensive mock database manager for testing.
It simulates database operations without requiring a real database connection.

Author: Edu-Flow Team
"""

import asyncio
import uuid
from datetime import datetime, date, time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError


@dataclass
class MockDatabaseEntity:
    """Base class for mock database entities."""
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                result[key] = value
        return result


@dataclass
class MockStudent(MockDatabaseEntity):
    """Mock student entity."""
    name: str
    email: str
    student_id: str
    phone: str
    address: str
    gender: str
    birth_date: str
    enrollment_date: str
    department_id: str
    gpa: float = 0.0
    graduation_date: Optional[str] = None
    status: str = 'active'
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        # Add computed fields
        result['full_name'] = f"{self.name}"
        result['age'] = self.calculate_age()
        return result
    
    def calculate_age(self) -> int:
        """Calculate student age from birth date."""
        try:
            birth_date = datetime.strptime(self.birth_date, '%Y-%m-%d').date()
            today = date.today()
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except:
            return 18  # Default age


@dataclass
class MockTeacher(MockDatabaseEntity):
    """Mock teacher entity."""
    name: str
    email: str
    teacher_id: str
    phone: str
    address: str
    gender: str
    birth_date: str
    hire_date: str
    department_id: str
    specialization: str
    qualifications: List[str] = field(default_factory=list)
    experience_years: int = 0
    status: str = 'active'


@dataclass
class MockCourse(MockDatabaseEntity):
    """Mock course entity."""
    name: str
    code: str
    description: str
    credits: int
    department_id: str
    level: str
    prerequisites: List[str] = field(default_factory=list)
    objectives: List[str] = field(default_factory=list)
    outcomes: List[str] = field(default_factory=list)
    syllabus: str = ''
    assessment_methods: List[str] = field(default_factory=list)
    textbooks: List[str] = field(default_factory=list)
    status: str = 'active'
    academic_year: str = '2023-2024'


@dataclass
class MockDepartment(MockDatabaseEntity):
    """Mock department entity."""
    name: str
    code: str
    description: str
    head_of_department: str = ''
    established_date: str = ''
    location: str = ''
    contact_email: str = ''
    contact_phone: str = ''
    website: str = ''
    status: str = 'active'


@dataclass
class MockSubject(MockDatabaseEntity):
    """Mock subject entity."""
    name: str
    code: str
    description: str
    credits: int
    department_id: str
    level: str
    prerequisites: List[str] = field(default_factory=list)
    objectives: List[str] = field(default_factory=list)
    outcomes: List[str] = field(default_factory=list)
    syllabus: str = ''
    assessment_methods: List[str] = field(default_factory=list)
    textbooks: List[str] = field(default_factory=list)
    status: str = 'active'
    academic_year: str = '2023-2024'


@dataclass
class MockClass(MockDatabaseEntity):
    """Mock class entity."""
    name: str
    subject_id: str
    teacher_id: str
    capacity: int
    enrolled_students: List[str] = field(default_factory=list)
    academic_year: str = '2023-2024'
    semester: str = 'Fall'
    schedule: str = ''
    schedule_details: Dict[str, Any] = field(default_factory=dict)
    location: str = ''
    class_type: str = 'lecture'
    requirements: List[str] = field(default_factory=list)
    objectives: List[str] = field(default_factory=list)
    assessment_methods: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    status: str = 'active'


@dataclass
class MockMark(MockDatabaseEntity):
    """Mock mark entity."""
    student_id: str
    course_id: str
    exam_name: str
    marks_obtained: float
    total_marks: float
    percentage: float
    grade: str = ''
    exam_date: str = ''
    weightage: float = 1.0
    is_final: bool = False
    feedback: str = ''
    status: str = 'graded'


@dataclass
class MockGrade(MockDatabaseEntity):
    """Mock grade entity."""
    student_id: str
    course_id: str
    grade: str
    percentage: float
    letter_grade: str
    grade_points: float
    comments: str = ''
    issued_date: str = ''
    issued_by: str = ''


@dataclass
class MockTimetableEntry(MockDatabaseEntity):
    """Mock timetable entry entity."""
    class_id: str
    room_id: str
    day_of_week: str
    start_time: str
    end_time: str
    academic_year: str = '2023-2024'
    semester: str = 'Fall'
    is_recurring: bool = False
    recurring_pattern: str = ''
    notes: str = ''


@dataclass
class MockLaboratory(MockDatabaseEntity):
    """Mock laboratory entity."""
    name: str
    building: str
    floor: int
    capacity: int
    lab_type: str
    equipment: List[str] = field(default_factory=list)
    safety_equipment: List[str] = field(default_factory=list)
    maintenance_schedule: str = ''
    status: str = 'active'


@dataclass
class MockRoom(MockDatabaseEntity):
    """Mock room entity."""
    name: str
    building: str
    floor: int
    capacity: int
    room_type: str
    facilities: List[str] = field(default_factory=list)
    availability: str = 'available'
    maintenance_schedule: str = ''
    status: str = 'active'


@dataclass
class MockUser(MockDatabaseEntity):
    """Mock user entity."""
    username: str
    email: str
    full_name: str
    password_hash: str
    role: str
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class MockDatabaseManager:
    """Mock database manager that simulates database operations."""
    
    def __init__(self):
        self.entities = {
            'students': {},
            'teachers': {},
            'courses': {},
            'departments': {},
            'subjects': {},
            'classes': {},
            'marks': {},
            'grades': {},
            'timetable_entries': {},
            'laboratories': {},
            'rooms': {},
            'users': {}
        }
        
        self.cache = {}
        self.next_id_counter = 1
        
        # Initialize with some sample data
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample data for testing."""
        # Create sample department
        dept = MockDepartment(
            id=str(uuid.uuid4()),
            name='Computer Science',
            code='CS',
            description='Department of Computer Science',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.entities['departments'][dept.id] = dept
        
        # Create sample course
        course = MockCourse(
            id=str(uuid.uuid4()),
            name='Introduction to Programming',
            code='CS101',
            description='Basic programming concepts',
            credits=3,
            department_id=dept.id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.entities['courses'][course.id] = course
        
        # Create sample student
        student = MockStudent(
            id=str(uuid.uuid4()),
            name='John Doe',
            email='john.doe@example.com',
            student_id='STU001',
            phone='+1234567890',
            address='123 Campus St',
            gender='M',
            birth_date='2000-01-01',
            enrollment_date='2023-09-01',
            department_id=dept.id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.entities['students'][student.id] = student
    
    def _generate_id(self) -> str:
        """Generate a unique ID."""
        return str(uuid.uuid4())
    
    def _validate_entity_data(self, entity_type: str, data: Dict[str, Any]) -> None:
        """Validate entity data."""
        required_fields = {
            'students': ['name', 'email', 'student_id', 'phone', 'address', 'gender', 'birth_date', 'enrollment_date', 'department_id'],
            'teachers': ['name', 'email', 'teacher_id', 'phone', 'address', 'gender', 'birth_date', 'hire_date', 'department_id', 'specialization'],
            'courses': ['name', 'code', 'description', 'credits', 'department_id'],
            'departments': ['name', 'code', 'description'],
            'subjects': ['name', 'code', 'description', 'credits', 'department_id'],
            'classes': ['name', 'subject_id', 'teacher_id', 'capacity', 'academic_year', 'semester'],
            'marks': ['student_id', 'course_id', 'exam_name', 'marks_obtained', 'total_marks', 'percentage'],
            'grades': ['student_id', 'course_id', 'grade', 'percentage'],
            'timetable_entries': ['class_id', 'room_id', 'day_of_week', 'start_time', 'end_time', 'academic_year'],
            'laboratories': ['name', 'building', 'floor', 'capacity', 'lab_type'],
            'rooms': ['name', 'building', 'floor', 'capacity', 'room_type'],
            'users': ['username', 'email', 'full_name', 'password_hash', 'role']
        }
        
        if entity_type in required_fields:
            for field in required_fields[entity_type]:
                if field not in data or data[field] is None:
                    raise ValidationError(f"Missing required field: {field}")
        
        # Validate data types
        if entity_type == 'students' and 'birth_date' in data:
            try:
                datetime.strptime(data['birth_date'], '%Y-%m-%d')
            except ValueError:
                raise ValidationError("Invalid date format for birth_date")
    
    def _create_entity(self, entity_type: str, data: Dict[str, Any], entity_class) -> MockDatabaseEntity:
        """Create a new entity."""
        self._validate_entity_data(entity_type, data)
        
        entity_id = self._generate_id()
        created_at = datetime.now()
        updated_at = created_at
        
        # Create entity instance
        entity = entity_class(
            id=entity_id,
            created_at=created_at,
            updated_at=updated_at,
            **data
        )
        
        # Store entity
        self.entities[entity_type][entity_id] = entity
        
        # Clear cache
        self.cache[entity_type] = {}
        
        return entity
    
    def _update_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> MockDatabaseEntity:
        """Update an existing entity."""
        if entity_id not in self.entities[entity_type]:
            raise NotFoundError(f"{entity_type} with id {entity_id} not found")
        
        entity = self.entities[entity_type][entity_id]
        updated_at = datetime.now()
        
        # Update fields
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        entity.updated_at = updated_at
        
        # Clear cache
        if entity_type in self.cache:
            self.cache[entity_type][entity_id] = None
        
        return entity
    
    def _delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """Delete an entity."""
        if entity_id not in self.entities[entity_type]:
            return False
        
        del self.entities[entity_type][entity_id]
        
        # Clear cache
        if entity_type in self.cache:
            if entity_id in self.cache[entity_type]:
                del self.cache[entity_type][entity_id]
        
        return True
    
    async def create_student(self, data: Dict[str, Any]) -> MockStudent:
        """Create a new student."""
        return self._create_entity('students', data, MockStudent)
    
    async def get_student(self, student_id: str) -> Optional[MockStudent]:
        """Get a student by ID."""
        if student_id in self.cache.get('students', {}):
            return self.cache['students'][student_id]
        
        student = self.entities['students'].get(student_id)
        if student:
            # Cache the result
            if 'students' not in self.cache:
                self.cache['students'] = {}
            self.cache['students'][student_id] = student
        
        return student
    
    async def get_student_by_id(self, student_id: str) -> Optional[MockStudent]:
        """Get a student by student ID."""
        for student in self.entities['students'].values():
            if student.student_id == student_id:
                return student
        return None
    
    async def get_students_by_department(self, department_id: str) -> List[MockStudent]:
        """Get students by department."""
        return [student for student in self.entities['students'].values() 
                if student.department_id == department_id]
    
    async def get_student_statistics(self, student_id: str) -> Dict[str, Any]:
        """Get student statistics."""
        student = await self.get_student(student_id)
        if not student:
            raise NotFoundError(f"Student {student_id} not found")
        
        return {
            'total_courses': 10,
            'completed_courses': 8,
            'gpa': 3.5,
            'enrollment_count': 1,
            'attendance_rate': 95.0,
            'average_marks': 85.0
        }
    
    async def create_teacher(self, data: Dict[str, Any]) -> MockTeacher:
        """Create a new teacher."""
        return self._create_entity('teachers', data, MockTeacher)
    
    async def get_teacher(self, teacher_id: str) -> Optional[MockTeacher]:
        """Get a teacher by ID."""
        return self.entities['teachers'].get(teacher_id)
    
    async def get_teacher_by_id(self, teacher_id: str) -> Optional[MockTeacher]:
        """Get a teacher by teacher ID."""
        for teacher in self.entities['teachers'].values():
            if teacher.teacher_id == teacher_id:
                return teacher
        return None
    
    async def get_teachers_by_department(self, department_id: str) -> List[MockTeacher]:
        """Get teachers by department."""
        return [teacher for teacher in self.entities['teachers'].values() 
                if teacher.department_id == department_id]
    
    async def create_course(self, data: Dict[str, Any]) -> MockCourse:
        """Create a new course."""
        return self._create_entity('courses', data, MockCourse)
    
    async def get_course(self, course_id: str) -> Optional[MockCourse]:
        """Get a course by ID."""
        return self.entities['courses'].get(course_id)
    
    async def get_course_by_code(self, course_code: str) -> Optional[MockCourse]:
        """Get a course by course code."""
        for course in self.entities['courses'].values():
            if course.code == course_code:
                return course
        return None
    
    async def get_courses_by_department(self, department_id: str) -> List[MockCourse]:
        """Get courses by department."""
        return [course for course in self.entities['courses'].values() 
                if course.department_id == department_id]
    
    async def create_class(self, data: Dict[str, Any]) -> MockClass:
        """Create a new class."""
        return self._create_entity('classes', data, MockClass)
    
    async def get_class(self, class_id: str) -> Optional[MockClass]:
        """Get a class by ID."""
        return self.entities['classes'].get(class_id)
    
    async def get_classes_by_teacher(self, teacher_id: str) -> List[MockClass]:
        """Get classes by teacher."""
        return [class_obj for class_obj in self.entities['classes'].values() 
                if class_obj.teacher_id == teacher_id]
    
    async def create_mark(self, data: Dict[str, Any]) -> MockMark:
        """Create a new mark."""
        return self._create_entity('marks', data, MockMark)
    
    async def get_mark(self, mark_id: str) -> Optional[MockMark]:
        """Get a mark by ID."""
        return self.entities['marks'].get(mark_id)
    
    async def get_marks_by_student(self, student_id: str) -> List[MockMark]:
        """Get marks by student."""
        return [mark for mark in self.entities['marks'].values() 
                if mark.student_id == student_id]
    
    async def create_department(self, data: Dict[str, Any]) -> MockDepartment:
        """Create a new department."""
        return self._create_entity('departments', data, MockDepartment)
    
    async def get_department(self, department_id: str) -> Optional[MockDepartment]:
        """Get a department by ID."""
        return self.entities['departments'].get(department_id)
    
    async def get_department_by_code(self, department_code: str) -> Optional[MockDepartment]:
        """Get a department by code."""
        for department in self.entities['departments'].values():
            if department.code == department_code:
                return department
        return None
    
    async def get_departments_by_head(self, head_id: str) -> List[MockDepartment]:
        """Get departments by head."""
        return [dept for dept in self.entities['departments'].values() 
                if dept.head_of_department == head_id]
    
    async def create_subject(self, data: Dict[str, Any]) -> MockSubject:
        """Create a new subject."""
        return self._create_entity('subjects', data, MockSubject)
    
    async def get_subject(self, subject_id: str) -> Optional[MockSubject]:
        """Get a subject by ID."""
        return self.entities['subjects'].get(subject_id)
    
    async def get_subjects_by_department(self, department_id: str) -> List[MockSubject]:
        """Get subjects by department."""
        return [subject for subject in self.entities['subjects'].values() 
                if subject.department_id == department_id]
    
    async def create_user(self, data: Dict[str, Any]) -> MockUser:
        """Create a new user."""
        return self._create_entity('users', data, MockUser)
    
    async def get_user(self, user_id: str) -> Optional[MockUser]:
        """Get a user by ID."""
        return self.entities['users'].get(user_id)
    
    async def get_user_by_username(self, username: str) -> Optional[MockUser]:
        """Get a user by username."""
        for user in self.entities['users'].values():
            if user.username == username:
                return user
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[MockUser]:
        """Get a user by email."""
        for user in self.entities['users'].values():
            if user.email == email:
                return user
        return None
    
    async def get_room(self, room_id: str) -> Optional[MockRoom]:
        """Get a room by ID."""
        return self.entities['rooms'].get(room_id)
    
    async def get_rooms_by_building(self, building: str) -> List[MockRoom]:
        """Get rooms by building."""
        return [room for room in self.entities['rooms'].values() 
                if room.building == building]
    
    async def get_laboratory(self, lab_id: str) -> Optional[MockLaboratory]:
        """Get a laboratory by ID."""
        return self.entities['laboratories'].get(lab_id)
    
    async def get_laboratories_by_building(self, building: str) -> List[MockLaboratory]:
        """Get laboratories by building."""
        return [lab for lab in self.entities['laboratories'].values() 
                if lab.building == building]
    
    async def get_timetable_entry(self, entry_id: str) -> Optional[MockTimetableEntry]:
        """Get a timetable entry by ID."""
        return self.entities['timetable_entries'].get(entry_id)
    
    async def get_timetable_by_class(self, class_id: str) -> List[MockTimetableEntry]:
        """Get timetable entries by class."""
        return [entry for entry in self.entities['timetable_entries'].values() 
                if entry.class_id == class_id]
    
    # Generic CRUD operations
    async def get_all(self, entity_type: str, skip: int = 0, limit: int = 100) -> List[MockDatabaseEntity]:
        """Get all entities of a type."""
        entities = list(self.entities.get(entity_type, {}).values())
        return entities[skip:skip + limit]
    
    async def count(self, entity_type: str) -> int:
        """Count entities of a type."""
        return len(self.entities.get(entity_type, {}))
    
    async def update(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> MockDatabaseEntity:
        """Update an entity."""
        return self._update_entity(entity_type, entity_id, data)
    
    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """Delete an entity."""
        return self._delete_entity(entity_type, entity_id)
    
    # Utility methods
    async def clear_database(self) -> None:
        """Clear all entities."""
        for entity_type in self.entities:
            self.entities[entity_type].clear()
        self.cache.clear()
        self._initialize_sample_data()
    
    async def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        stats = {}
        for entity_type, entities in self.entities.items():
            stats[entity_type] = len(entities)
        return stats
    
    async def backup_database(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Create a backup of the database."""
        backup = {}
        for entity_type, entities in self.entities.items():
            backup[entity_type] = {entity_id: entity.to_dict() for entity_id, entity in entities.items()}
        return backup
    
    async def restore_database(self, backup: Dict[str, Dict[str, Dict[str, Any]]]) -> None:
        """Restore database from backup."""
        self.clear_database()
        
        for entity_type, entities in backup.items():
            for entity_id, data in entities.items():
                if entity_type in ['students', 'teachers', 'courses', 'departments', 'subjects', 'classes', 'marks', 'grades', 'timetable_entries', 'laboratories', 'rooms', 'users']:
                    # Convert data back to entity objects
                    entity_class = {
                        'students': MockStudent,
                        'teachers': MockTeacher,
                        'courses': MockCourse,
                        'departments': MockDepartment,
                        'subjects': MockSubject,
                        'classes': MockClass,
                        'marks': MockMark,
                        'grades': MockGrade,
                        'timetable_entries': MockTimetableEntry,
                        'laboratories': MockLaboratory,
                        'rooms': MockRoom,
                        'users': MockUser
                    }.get(entity_type)
                    
                    if entity_class:
                        entity = entity_class(id=data['id'], created_at=datetime.fromisoformat(data['created_at']), updated_at=datetime.fromisoformat(data['updated_at']), **data)
                        self.entities[entity_type][entity_id] = entity