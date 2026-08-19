"""
Course Model for Database Operations

This module provides the SQLAlchemy model for Course entity.
It includes all fields and relationships for academic course management.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship

from infrastructure.models.base_model import BaseModel
from core.exceptions import ValidationError
from core.logging import get_logger

logger = get_logger(__name__)


class CourseModel(BaseModel):
    """
    SQLAlchemy model for Course entity.
    
    Represents academic courses with curriculum structure, scheduling, and enrollment.
    """
    __tablename__ = "courses"
    
    # Course identification
    id = Column(String(50), primary_key=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    course_code = Column(String(50), nullable=False, unique=True, index=True)
    
    # Course categorization
    level = Column(String(50), nullable=False)  # undergraduate, postgraduate, doctoral, certificate
    department_id = Column(String(50), ForeignKey("departments.id"), nullable=False)
    program_id = Column(String(50), ForeignKey("programs.id"), nullable=False)
    subject_id = Column(String(50), ForeignKey("subjects.id"), nullable=False)
    
    # Course structure
    course_type = Column(String(50), nullable=False)  # core, elective, foundation, special, remedial
    credit_hours = Column(Integer, default=3)  # Credit hours for the course
    contact_hours = Column(Integer, default=0)  # Contact hours per week
    total_hours = Column(Integer, default=0)  # Total course hours
    lecture_hours = Column(Integer, default=0)  # Lecture hours per week
    lab_hours = Column(Integer, default=0)  # Lab hours per week
    tutorial_hours = Column(Integer, default=0)  # Tutorial hours per week
    
    # Course details
    prerequisites = Column(JSON, default=list)  # List of prerequisite course IDs
    corequisites = Column(JSON, default=list)  # List of corequisite course IDs
    antirequisites = Column(JSON, default=list)  # List of antirequisite course IDs
    syllabus = Column(Text)  # Course syllabus
    learning_objectives = Column(JSON, default=list)  # Learning objectives
    course_outline = Column(JSON, default=list)  # Course outline/structure
    evaluation_scheme = Column(JSON, default=dict)  # Evaluation scheme
    textbooks = Column(JSON, default=list)  # List of textbooks
    references = Column(JSON, default=list)  # List of references
    
    # Course scheduling
    academic_year = Column(String(10), nullable=False)  # 2023-2024
    semester = Column(Integer, nullable=False)  # Semester number
    batch = Column(String(20), nullable=False)  # A, B, C, etc.
    section = Column(String(5), nullable=False)  # 1, 2, 3, etc.
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Course capacity and enrollment
    max_capacity = Column(Integer, default=50)  # Maximum students
    current_enrollment = Column(Integer, default=0)  # Current enrollment
    waitlist_capacity = Column(Integer, default=10)  # Waitlist capacity
    current_waitlist = Column(Integer, default=0)  # Current waitlist
    
    # Course status
    status = Column(String(20), default="planned")  # planned, active, completed, cancelled, suspended
    is_mandatory = Column(Boolean, default=True)
    is_offered = Column(Boolean, default=True)
    enrollment_open = Column(Boolean, default=True)
    enrollment_start_date = Column(DateTime)
    enrollment_end_date = Column(DateTime)
    
    # Course delivery
    delivery_mode = Column(String(50), default="face_to_face")  # face_to_face, online, hybrid, blended
    language = Column(String(50), default="English")  # Language of instruction
    is_bilingual = Column(Boolean, default=False)
    accessibility_features = Column(JSON, default=list)  # Accessibility features
    
    # Course management
    instructor_id = Column(String(50), ForeignKey("users.id"))  # Primary instructor
    coordinator_id = Column(String(50), ForeignKey("users.id"))  # Course coordinator
    teaching_assistants = Column(JSON, default=list)  # List of TA IDs
    classrooms = Column(JSON, default=list)  # List of classroom IDs
    laboratories = Column(JSON, default=list)  # List of laboratory IDs
    
    # Course performance
    success_rate = Column(Float, default=0.0)  # 0-100
    average_grade = Column(Float, default=0.0)  # Average grade
    drop_rate = Column(Float, default=0.0)  # 0-100
    feedback_rating = Column(Float, default=0.0)  # 0-5
    
    # Course metadata
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)  # List of tags for categorization
    attachments = Column(JSON, default=list)  # List of attachment paths/URLs
    
    # Relationships
    department = relationship("DepartmentModel")
    program = relationship("ProgramModel")
    subject = relationship("SubjectModel")
    instructor = relationship("UserModel", foreign_keys=[instructor_id])
    coordinator = relationship("UserModel", foreign_keys=[coordinator_id])
    classes = relationship("ClassModel")
    enrollments = relationship("EnrollmentModel")
    assessments = relationship("AssessmentModel")
    outcomes = relationship("OutcomesModel")
    
    def __init__(self, **kwargs):
        """Initialize the course model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('level', 'undergraduate')
        kwargs.setdefault('credit_hours', 3)
        kwargs.setdefault('contact_hours', 0)
        kwargs.setdefault('total_hours', 0)
        kwargs.setdefault('lecture_hours', 0)
        kwargs.setdefault('lab_hours', 0)
        kwargs.setdefault('tutorial_hours', 0)
        kwargs.setdefault('prerequisites', [])
        kwargs.setdefault('corequisites', [])
        kwargs.setdefault('antirequisites', [])
        kwargs.setdefault('learning_objectives', [])
        kwargs.setdefault('course_outline', [])
        kwargs.setdefault('evaluation_scheme', {})
        kwargs.setdefault('textbooks', [])
        kwargs.setdefault('references', [])
        kwargs.setdefault('semester', 1)
        kwargs.setdefault('batch', 'A')
        kwargs.setdefault('section', '1')
        kwargs.setdefault('max_capacity', 50)
        kwargs.setdefault('current_enrollment', 0)
        kwargs.setdefault('waitlist_capacity', 10)
        kwargs.setdefault('current_waitlist', 0)
        kwargs.setdefault('status', 'planned')
        kwargs.setdefault('is_mandatory', True)
        kwargs.setdefault('is_offered', True)
        kwargs.setdefault('enrollment_open', True)
        kwargs.setdefault('delivery_mode', 'face_to_face')
        kwargs.setdefault('language', 'English')
        kwargs.setdefault('is_bilingual', False)
        kwargs.setdefault('accessibility_features', [])
        kwargs.setdefault('teaching_assistants', [])
        kwargs.setdefault('classrooms', [])
        kwargs.setdefault('laboratories', [])
        kwargs.setdefault('success_rate', 0.0)
        kwargs.setdefault('average_grade', 0.0)
        kwargs.setdefault('drop_rate', 0.0)
        kwargs.setdefault('feedback_rating', 0.0)
        kwargs.setdefault('metadata', {})
        kwargs.setdefault('tags', [])
        kwargs.setdefault('attachments', [])
        
        # Set default dates
        now = datetime.now()
        if 'start_date' not in kwargs:
            kwargs['start_date'] = now
        if 'end_date' not in kwargs:
            kwargs['end_date'] = now + timedelta(days=120)  # Default 4 months
        if 'enrollment_start_date' not in kwargs:
            kwargs['enrollment_start_date'] = now
        if 'enrollment_end_date' not in kwargs:
            kwargs['enrollment_end_date'] = now + timedelta(days=30)  # Default 1 month
        
        super().__init__(**kwargs)
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert the model to a dictionary.
        
        Args:
            include_relationships: Whether to include relationship data
            
        Returns:
            Dictionary representation of the model
        """
        data = super().to_dict()
        
        # Convert date fields to ISO format
        if 'start_date' in data and isinstance(data['start_date'], datetime):
            data['start_date'] = data['start_date'].isoformat()
        else:
            data['start_date'] = datetime.now().isoformat()
        
        if 'end_date' in data and isinstance(data['end_date'], datetime):
            data['end_date'] = data['end_date'].isoformat()
        else:
            data['end_date'] = (datetime.now() + timedelta(days=120)).isoformat()
        
        if 'enrollment_start_date' in data and isinstance(data['enrollment_start_date'], datetime):
            data['enrollment_start_date'] = data['enrollment_start_date'].isoformat()
        else:
            data['enrollment_start_date'] = datetime.now().isoformat()
        
        if 'enrollment_end_date' in data and isinstance(data['enrollment_end_date'], datetime):
            data['enrollment_end_date'] = data['enrollment_end_date'].isoformat()
        else:
            data['enrollment_end_date'] = (datetime.now() + timedelta(days=30)).isoformat()
        
        # Convert JSON fields to proper format
        if 'prerequisites' in data and isinstance(data['prerequisites'], list):
            data['prerequisites'] = data['prerequisites']
        else:
            data['prerequisites'] = []
        
        if 'corequisites' in data and isinstance(data['corequisites'], list):
            data['corequisites'] = data['corequisites']
        else:
            data['corequisites'] = []
        
        if 'antirequisites' in data and isinstance(data['antirequisites'], list):
            data['antirequisites'] = data['antirequisites']
        else:
            data['antirequisites'] = []
        
        if 'learning_objectives' in data and isinstance(data['learning_objectives'], list):
            data['learning_objectives'] = data['learning_objectives']
        else:
            data['learning_objectives'] = []
        
        if 'course_outline' in data and isinstance(data['course_outline'], list):
            data['course_outline'] = data['course_outline']
        else:
            data['course_outline'] = []
        
        if 'evaluation_scheme' in data and isinstance(data['evaluation_scheme'], dict):
            data['evaluation_scheme'] = data['evaluation_scheme']
        else:
            data['evaluation_scheme'] = {}
        
        if 'textbooks' in data and isinstance(data['textbooks'], list):
            data['textbooks'] = data['textbooks']
        else:
            data['textbooks'] = []
        
        if 'references' in data and isinstance(data['references'], list):
            data['references'] = data['references']
        else:
            data['references'] = []
        
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = data['metadata']
        else:
            data['metadata'] = {}
        
        if 'tags' in data and isinstance(data['tags'], list):
            data['tags'] = data['tags']
        else:
            data['tags'] = []
        
        if 'attachments' in data and isinstance(data['attachments'], list):
            data['attachments'] = data['attachments']
        else:
            data['attachments'] = []
        
        # Calculate derived fields
        data['is_full'] = self.is_full()
        data['enrollment_percentage'] = self.get_enrollment_percentage()
        data['waitlist_available'] = self.get_waitlist_available()
        data['enrollment_status'] = self.get_enrollment_status()
        data['duration_days'] = self.get_duration_days()
        data='days_until_start'] = self.get_days_until_start()
        data['days_until_enrollment_end'] = self.get_days_until_enrollment_end()
        data['is_current'] = self.is_current()
        data['course_summary'] = self.get_course_summary()
        data='performance_metrics'] = self.get_performance_metrics()
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'department') and self.department:
                data['department'] = self.department.to_dict()
            else:
                data['department'] = None
            
            if hasattr(self, 'program') and self.program:
                data['program'] = self.program.to_dict()
            else:
                data['program'] = None
            
            if hasattr(self, 'subject') and self.subject:
                data['subject'] = self.subject.to_dict()
            else:
                data['subject'] = None
            
            if hasattr(self, 'instructor') and self.instructor:
                data['instructor'] = self.instructor.to_dict()
            else:
                data['instructor'] = None
            
            if hasattr(self, 'coordinator') and self.coordinator:
                data['coordinator'] = self.coordinator.to_dict()
            else:
                data['coordinator'] = None
            
            if hasattr(self, 'classes') and self.classes:
                data['classes'] = [cls.to_dict() for cls in self.classes]
            else:
                data['classes'] = []
            
            if hasattr(self, 'enrollments') and self.enrollments:
                data['enrollments'] = [enrollment.to_dict() for enrollment in self.enrollments]
            else:
                data['enrollments'] = []
            
            if hasattr(self, 'assessments') and self.assessments:
                data['assessments'] = [assessment.to_dict() for assessment in self.assessments]
            else:
                data['assessments'] = []
            
            if hasattr(self, 'outcomes') and self.outcomes:
                data['outcomes'] = [outcome.to_dict() for outcome in self.outcomes]
            else:
                data['outcomes'] = []
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'prerequisites' in kwargs and isinstance(kwargs['prerequisites'], list):
            self.prerequisites = kwargs['prerequisites']
        if 'corequisites' in kwargs and isinstance(kwargs['corequisites'], list):
            self.corequisites = kwargs['corequisites']
        if 'antirequisites' in kwargs and isinstance(kwargs['antirequisites'], list):
            self.antirequisites = kwargs['antirequisites']
        if 'learning_objectives' in kwargs and isinstance(kwargs['learning_objectives'], list):
            self.learning_objectives = kwargs['learning_objectives']
        if 'course_outline' in kwargs and isinstance(kwargs['course_outline'], list):
            self.course_outline = kwargs['course_outline']
        if 'evaluation_scheme' in kwargs and isinstance(kwargs['evaluation_scheme'], dict):
            self.evaluation_scheme = kwargs['evaluation_scheme']
        if 'textbooks' in kwargs and isinstance(kwargs['textbooks'], list):
            self.textbooks = kwargs['textbooks']
        if 'references' in kwargs and isinstance(kwargs['references'], list):
            self.references = kwargs['references']
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        if 'tags' in kwargs and isinstance(kwargs['tags'], list):
            self.tags = kwargs['tags']
        if 'attachments' in kwargs and isinstance(kwargs['attachments'], list):
            self.attachments = kwargs['attachments']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the course model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Course-specific validations
            if not self.id:
                raise ValidationError("Course ID is required")
            
            if not self.code:
                raise ValidationError("Course code is required")
            
            if not self.title:
                raise ValidationError("Course title is required")
            
            if not self.course_code:
                raise ValidationError("Course code is required")
            
            if not self.level:
                raise ValidationError("Course level is required")
            
            if not self.department_id:
                raise ValidationError("Department ID is required")
            
            if not self.program_id:
                raise ValidationError("Program ID is required")
            
            if not self.subject_id:
                raise ValidationError("Subject ID is required")
            
            if not self.course_type:
                raise ValidationError("Course type is required")
            
            if not self.academic_year:
                raise ValidationError("Academic year is required")
            
            if not self.semester:
                raise ValidationError("Semester is required")
            
            if not self.batch:
                raise ValidationError("Batch is required")
            
            if not self.section:
                raise ValidationError("Section is required")
            
            # Level validation
            valid_levels = ['undergraduate', 'postgraduate', 'doctoral', 'certificate', 'diploma']
            if self.level not in valid_levels:
                raise ValidationError(f"Invalid course level: {self.level}")
            
            # Course type validation
            valid_types = ['core', 'elective', 'foundation', 'special', 'remedial', 'workshop']
            if self.course_type not in valid_types:
                raise ValidationError(f"Invalid course type: {self.course_type}")
            
            # Academic year validation
            if len(self.academic_year) != 9 or self.academic_year[4] != '-':  # 2023-2024
                raise ValidationError("Academic year must be in format YYYY-YYYY")
            
            # Semester validation
            if self.semester < 1:
                raise ValidationError("Semester must be positive")
            
            # Hour validations
            if self.credit_hours <= 0:
                raise ValidationError("Credit hours must be positive")
            
            if self.contact_hours < 0:
                raise ValidationError("Contact hours cannot be negative")
            
            if self.total_hours < 0:
                raise ValidationError("Total hours cannot be negative")
            
            if self.lecture_hours < 0:
                raise ValidationError("Lecture hours cannot be negative")
            
            if self.lab_hours < 0:
                raise ValidationError("Lab hours cannot be negative")
            
            if self.tutorial_hours < 0:
                raise ValidationError("Tutorial hours cannot be negative")
            
            # Capacity validations
            if self.max_capacity <= 0:
                raise ValidationError("Maximum capacity must be positive")
            
            if self.current_enrollment < 0:
                raise ValidationError("Current enrollment cannot be negative")
            
            if self.current_enrollment > self.max_capacity:
                raise ValidationError("Current enrollment cannot exceed maximum capacity")
            
            if self.waitlist_capacity < 0:
                raise ValidationError("Waitlist capacity cannot be negative")
            
            if self.current_waitlist < 0:
                raise ValidationError("Current waitlist cannot be negative")
            
            if self.current_waitlist > self.waitlist_capacity:
                raise ValidationError("Current waitlist cannot exceed waitlist capacity")
            
            # Date validations
            if self.start_date and self.end_date and self.start_date > self.end_date:
                raise ValidationError("Start date must be before end date")
            
            if self.enrollment_start_date and self.enrollment_end_date and self.enrollment_start_date > self.enrollment_end_date:
                raise ValidationError("Enrollment start date must be before enrollment end date")
            
            # Status validation
            valid_statuses = ['planned', 'active', 'completed', 'cancelled', 'suspended']
            if self.status not in valid_statuses:
                raise ValidationError(f"Invalid status: {self.status}")
            
            # Delivery mode validation
            valid_delivery_modes = ['face_to_face', 'online', 'hybrid', 'blended', 'virtual']
            if self.delivery_mode not in valid_delivery_modes:
                raise ValidationError(f"Invalid delivery mode: {self.delivery_mode}")
            
            # Performance metrics validation
            if self.success_rate < 0 or self.success_rate > 100:
                raise ValidationError("Success rate must be between 0 and 100")
            
            if self.average_grade < 0 or self.average_grade > 100:
                raise ValidationError("Average grade must be between 0 and 100")
            
            if self.drop_rate < 0 or self.drop_rate > 100:
                raise ValidationError("Drop rate must be between 0 and 100")
            
            if self.feedback_rating < 0 or self.feedback_rating > 5:
                raise ValidationError("Feedback rating must be between 0 and 5")
            
            # JSON fields validation
            if not isinstance(self.prerequisites, list):
                raise ValidationError("Prerequisites must be a list")
            
            if not isinstance(self.corequisites, list):
                raise ValidationError("Corequisites must be a list")
            
            if not isinstance(self.antirequisites, list):
                raise ValidationError("Antirequisites must be a list")
            
            if not isinstance(self.learning_objectives, list):
                raise ValidationError("Learning objectives must be a list")
            
            if not isinstance(self.course_outline, list):
                raise ValidationError("Course outline must be a list")
            
            if not isinstance(self.evaluation_scheme, dict):
                raise ValidationError("Evaluation scheme must be a dictionary")
            
            if not isinstance(self.textbooks, list):
                raise ValidationError("Textbooks must be a list")
            
            if not isinstance(self.references, list):
                raise ValidationError("References must be a list")
            
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            if not isinstance(self.tags, list):
                raise ValidationError("Tags must be a list")
            
            if not isinstance(self.attachments, list):
                raise ValidationError("Attachments must be a list")
            
            logger.info(f"Course {self.code} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Course validation error: {str(e)}")
            raise ValidationError(f"Course validation error: {str(e)}")
    
    def add_prerequisite(self, course_id: str) -> None:
        """
        Add a prerequisite course.
        
        Args:
            course_id: ID of the prerequisite course
        """
        if course_id not in self.prerequisites:
            self.prerequisites.append(course_id)
            self.updated_at = datetime.now()
            logger.info(f"Added prerequisite {course_id} to course {self.code}")
        else:
            logger.warning(f"Prerequisite {course_id} already exists in course {self.code}")
    
    def remove_prerequisite(self, course_id: str) -> None:
        """
        Remove a prerequisite course.
        
        Args:
            course_id: ID of the prerequisite course to remove
        """
        if course_id in self.prerequisites:
            self.prerequisites.remove(course_id)
            self.updated_at = datetime.now()
            logger.info(f"Removed prerequisite {course_id} from course {self.code}")
        else:
            logger.warning(f"Prerequisite {course_id} not found in course {self.code}")
    
    def add_corequisite(self, course_id: str) -> None:
        """
        Add a corequisite course.
        
        Args:
            course_id: ID of the corequisite course
        """
        if course_id not in self.corequisites:
            self.corequisites.append(course_id)
            self.updated_at = datetime.now()
            logger.info(f"Added corequisite {course_id} to course {self.code}")
        else:
            logger.warning(f"Corequisite {course_id} already exists in course {self.code}")
    
    def remove_corequisite(self, course_id: str) -> None:
        """
        Remove a corequisite course.
        
        Args:
            course_id: ID of the corequisite course to remove
        """
        if course_id in self.corequisites:
            self.corequisites.remove(course_id)
            self.updated_at = datetime.now()
            logger.info(f"Removed corequisite {course_id} from course {self.code}")
        else:
            logger.warning(f"Corequisite {course_id} not found in course {self.code}")
    
    def add_antirequisite(self, course_id: str) -> None:
        """
        Add an antirequisite course.
        
        Args:
            course_id: ID of the antirequisite course
        """
        if course_id not in self.antirequisites:
            self.antirequisites.append(course_id)
            self.updated_at = datetime.now()
            logger.info(f"Added antirequisite {course_id} to course {self.code}")
        else:
            logger.warning(f"Antirequisite {course_id} already exists in course {self.code}")
    
    def remove_antirequisite(self, course_id: str) -> None:
        """
        Remove an antirequisite course.
        
        Args:
            course_id: ID of the antirequisite course to remove
        """
        if course_id in self.antirequisites:
            self.antirequisites.remove(course_id)
            self.updated_at = datetime.now()
            logger.info(f"Removed antirequisite {course_id} from course {self.code}")
        else:
            logger.warning(f"Antirequisite {course_id} not found in course {self.code}")
    
    def add_teaching_assistant(self, ta_id: str) -> None:
        """
        Add a teaching assistant.
        
        Args:
            ta_id: ID of the teaching assistant
        """
        if ta_id not in self.teaching_assistants:
            self.teaching_assistants.append(ta_id)
            self.updated_at = datetime.now()
            logger.info(f"Added teaching assistant {ta_id} to course {self.code}")
        else:
            logger.warning(f"Teaching assistant {ta_id} already exists in course {self.code}")
    
    def remove_teaching_assistant(self, ta_id: str) -> None:
        """
        Remove a teaching assistant.
        
        Args:
            ta_id: ID of the teaching assistant to remove
        """
        if ta_id in self.teaching_assistants:
            self.teaching_assistants.remove(ta_id)
            self.updated_at = datetime.now()
            logger.info(f"Removed teaching assistant {ta_id} from course {self.code}")
        else:
            logger.warning(f"Teaching assistant {ta_id} not found in course {self.code}")
    
    def add_classroom(self, classroom_id: str) -> None:
        """
        Add a classroom.
        
        Args:
            classroom_id: ID of the classroom
        """
        if classroom_id not in self.classrooms:
            self.classrooms.append(classroom_id)
            self.updated_at = datetime.now()
            logger.info(f"Added classroom {classroom_id} to course {self.code}")
        else:
            logger.warning(f"Classroom {classroom_id} already exists in course {self.code}")
    
    def remove_classroom(self, classroom_id: str) -> None:
        """
        Remove a classroom.
        
        Args:
            classroom_id: ID of the classroom to remove
        """
        if classroom_id in self.classrooms:
            self.classrooms.remove(classroom_id)
            self.updated_at = datetime.now()
            logger.info(f"Removed classroom {classroom_id} from course {self.code}")
        else:
            logger.warning(f"Classroom {classroom_id} not found in course {self.code}")
    
    def add_laboratory(self, lab_id: str) -> None:
        """
        Add a laboratory.
        
        Args:
            lab_id: ID of the laboratory
        """
        if lab_id not in self.laboratories:
            self.laboratories.append(lab_id)
            self.updated_at = datetime.now()
            logger.info(f"Added laboratory {lab_id} to course {self.code}")
        else:
            logger.warning(f"Laboratory {lab_id} already exists in course {self.code}")
    
    def remove_laboratory(self, lab_id: str) -> None:
        """
        Remove a laboratory.
        
        Args:
            lab_id: ID of the laboratory to remove
        """
        if lab_id in self.laboratories:
            self.laboratories.remove(lab_id)
            self.updated_at = datetime.now()
            logger.info(f"Removed laboratory {lab_id} from course {self.code}")
        else:
            logger.warning(f"Laboratory {lab_id} not found in course {self.code}")
    
    def add_textbook(self, textbook: dict) -> None:
        """
        Add a textbook.
        
        Args:
            textbook: Textbook information dictionary
        """
        if isinstance(textbook, dict) and 'title' in textbook:
            self.textbooks.append(textbook)
            self.updated_at = datetime.now()
            logger.info(f"Added textbook to course {self.code}: {textbook['title']}")
        else:
            raise ValidationError("Textbook must be a dictionary with title")
    
    def remove_textbook(self, title: str) -> None:
        """
        Remove a textbook by title.
        
        Args:
            title: Title of the textbook to remove
        """
        self.textbooks = [tb for tb in self.textbooks if tb.get('title') != title]
        self.updated_at = datetime.now()
        logger.info(f"Removed textbook {title} from course {self.code}")
    
    def add_reference(self, reference: dict) -> None:
        """
        Add a reference.
        
        Args:
            reference: Reference information dictionary
        """
        if isinstance(reference, dict) and 'title' in reference:
            self.references.append(reference)
            self.updated_at = datetime.now()
            logger.info(f"Added reference to course {self.code}: {reference['title']}")
        else:
            raise ValidationError("Reference must be a dictionary with title")
    
    def remove_reference(self, title: str) -> None:
        """
        Remove a reference by title.
        
        Args:
            title: Title of the reference to remove
        """
        self.references = [ref for ref in self.references if ref.get('title') != title]
        self.updated_at = datetime.now()
        logger.info(f"Removed reference {title} from course {self.code}")
    
    def update_capacity(self, max_capacity: int, waitlist_capacity: int = None) -> None:
        """
        Update course capacity.
        
        Args:
            max_capacity: Maximum capacity
            waitlist_capacity: Waitlist capacity (optional)
        """
        if max_capacity <= 0:
            raise ValidationError("Maximum capacity must be positive")
        
        self.max_capacity = max_capacity
        
        if waitlist_capacity is not None:
            if waitlist_capacity < 0:
                raise ValidationError("Waitlist capacity cannot be negative")
            self.waitlist_capacity = waitlist_capacity
        
        self.updated_at = datetime.now()
        logger.info(f"Updated capacity for course {self.code}: {max_capacity}")
    
    def enroll_student(self) -> None:
        """
        Enroll a student in the course.
        """
        if self.current_enrollment >= self.max_capacity:
            raise ValidationError("Course is full")
        
        if not self.enrollment_open:
            raise ValidationError("Enrollment is closed")
        
        self.current_enrollment += 1
        self.updated_at = datetime.now()
        logger.info(f"Enrolled student in course {self.code}: {self.current_enrollment}")
    
    def unenroll_student(self) -> None:
        """
        Unenroll a student from the course.
        """
        if self.current_enrollment > 0:
            self.current_enrollment -= 1
            self.updated_at = datetime.now()
            logger.info(f"Unenrolled student from course {self.code}: {self.current_enrollment}")
    
    def add_to_waitlist(self) -> None:
        """
        Add a student to the waitlist.
        """
        if self.current_waitlist >= self.waitlist_capacity:
            raise ValidationError("Waitlist is full")
        
        if not self.enrollment_open:
            raise ValidationError("Enrollment is closed")
        
        self.current_waitlist += 1
        self.updated_at = datetime.now()
        logger.info(f"Added student to waitlist for course {self.code}: {self.current_waitlist}")
    
    def remove_from_waitlist(self) -> None:
        """
        Remove a student from the waitlist.
        """
        if self.current_waitlist > 0:
            self.current_waitlist -= 1
            self.updated_at = datetime.now()
            logger.info(f"Removed student from waitlist for course {self.code}: {self.current_waitlist}")
    
    def start_enrollment(self) -> None:
        """
        Start enrollment for the course.
        """
        self.enrollment_open = True
        self.enrollment_start_date = datetime.now()
        self.updated_at = datetime.now()
        logger.info(f"Started enrollment for course {self.code}")
    
    def close_enrollment(self) -> None:
        """
        Close enrollment for the course.
        """
        self.enrollment_open = False
        self.enrollment_end_date = datetime.now()
        self.updated_at = datetime.now()
        logger.info(f"Closed enrollment for course {self.code}")
    
    def activate_course(self) -> None:
        """
        Activate the course.
        """
        self.status = 'active'
        self.updated_at = datetime.now()
        logger.info(f"Activated course {self.code}")
    
    def complete_course(self) -> None:
        """
        Mark the course as completed.
        """
        self.status = 'completed'
        self.updated_at = datetime.now()
        logger.info(f"Completed course {self.code}")
    
    def cancel_course(self, cancellation_reason: str = "") -> None:
        """
        Cancel the course.
        
        Args:
            cancellation_reason: Reason for cancellation (optional)
        """
        self.status = 'cancelled'
        if cancellation_reason:
            self.metadata['cancellation_reason'] = cancellation_reason
        self.updated_at = datetime.now()
        logger.info(f"Cancelled course {self.code}: {cancellation_reason}")
    
    def suspend_course(self, suspension_reason: str = "") -> None:
        """
        Suspend the course.
        
        Args:
            suspension_reason: Reason for suspension (optional)
        """
        self.status = 'suspended'
        if suspension_reason:
            self.metadata['suspension_reason'] = suspension_reason
        self.updated_at = datetime.now()
        logger.info(f"Suspended course {self.code}: {suspension_reason}")
    
    def update_performance_metrics(self, success_rate: float = None, average_grade: float = None,
                                   drop_rate: float = None, feedback_rating: float = None) -> None:
        """
        Update course performance metrics.
        
        Args:
            success_rate: Success rate (0-100) (optional)
            average_grade: Average grade (0-100) (optional)
            drop_rate: Drop rate (0-100) (optional)
            feedback_rating: Feedback rating (0-5) (optional)
        """
        if success_rate is not None:
            if success_rate < 0 or success_rate > 100:
                raise ValidationError("Success rate must be between 0 and 100")
            self.success_rate = success_rate
        
        if average_grade is not None:
            if average_grade < 0 or average_grade > 100:
                raise ValidationError("Average grade must be between 0 and 100")
            self.average_grade = average_grade
        
        if drop_rate is not None:
            if drop_rate < 0 or drop_rate > 100:
                raise ValidationError("Drop rate must be between 0 and 100")
            self.drop_rate = drop_rate
        
        if feedback_rating is not None:
            if feedback_rating < 0 or feedback_rating > 5:
                raise ValidationError("Feedback rating must be between 0 and 5")
            self.feedback_rating = feedback_rating
        
        self.updated_at = datetime.now()
        logger.info(f"Updated performance metrics for course {self.code}")
    
    def is_full(self) -> bool:
        """
        Check if course is full.
        
        Returns:
            True if course is full
        """
        return self.current_enrollment >= self.max_capacity
    
    def get_enrollment_percentage(self) -> float:
        """
        Get enrollment percentage.
        
        Returns:
            Enrollment percentage (0-100)
        """
        if self.max_capacity > 0:
            return (self.current_enrollment / self.max_capacity) * 100
        return 0.0
    
    def get_waitlist_available(self) -> int:
        """
        Get available waitlist spots.
        
        Returns:
            Available waitlist spots
        """
        return max(0, self.waitlist_capacity - self.current_waitlist)
    
    def get_enrollment_status(self) -> str:
        """
        Get enrollment status.
        
        Returns:
            Enrollment status string
        """
        if not self.enrollment_open:
            return 'closed'
        elif self.is_full():
            if self.get_waitlist_available() > 0:
                return 'full_with_waitlist'
            else:
                return 'full_no_waitlist'
        else:
            return 'open'
    
    def get_duration_days(self) -> int:
        """
        Get course duration in days.
        
        Returns:
            Course duration in days
        """
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            return max(0, delta.days)
        return 0
    
    def get_days_until_start(self) -> Optional[int]:
        """
        Get days until course start.
        
        Returns:
            Days until start, or None if no start date
        """
        if self.start_date:
            delta = self.start_date - datetime.now()
            return max(0, delta.days)
        return None
    
    def get_days_until_enrollment_end(self) -> Optional[int]:
        """
        Get days until enrollment end.
        
        Returns:
            Days until enrollment end, or None if no enrollment end date
        """
        if self.enrollment_end_date:
            delta = self.enrollment_end_date - datetime.now()
            return max(0, delta.days)
        return None
    
    def is_current(self) -> bool:
        """
        Check if course is current (active and within date range).
        
        Returns:
            True if course is current
        """
        now = datetime.now()
        return self.status == 'active' and self.start_date <= now <= self.end_date
    
    def get_course_summary(self) -> Dict[str, Any]:
        """
        Get course summary.
        
        Returns:
            Course summary dictionary
        """
        return {
            'id': self.id,
            'code': self.code,
            'title': self.title,
            'level': self.level,
            'course_type': self.course_type,
            'credit_hours': self.credit_hours,
            'delivery_mode': self.delivery_mode,
            'status': self.status,
            'enrollment_status': self.get_enrollment_status(),
            'enrollment_percentage': self.get_enrollment_percentage(),
            'is_full': self.is_full(),
            'current_enrollment': self.current_enrollment,
            'max_capacity': self.max_capacity,
            'waitlist_available': self.get_waitlist_available(),
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'enrollment_open': self.enrollment_open,
            'is_mandatory': self.is_mandatory,
            'is_offered': self.is_offered,
            'is_current': self.is_current(),
            'duration_days': self.get_duration_days()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return {
            'success_rate': self.success_rate,
            'average_grade': self.average_grade,
            'drop_rate': self.drop_rate,
            'feedback_rating': self.feedback_rating,
            'total_enrollments': self.current_enrollment,
            'waitlist_count': self.current_waitlist
        }
    
    def __repr__(self) -> str:
        """String representation of the course model."""
        return f"<CourseModel(code='{self.code}', title='{self.title}', level='{self.level}', status='{self.status}')>"