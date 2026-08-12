"""
Course domain services

This module contains domain services for course management:
- CourseService: Course management service
- CourseOfferingService: Course offering management service

Author: Edu-Flow Team
"""

from datetime import datetime, date, time, timedelta
from typing import Optional, List, Dict, Any
from .entities import Course, CourseOffering, Schedule, PrerequisiteType, CourseLevel, CourseStatus, Semester, DayOfWeek
from ...infrastructure.exceptions import NotFoundError, ValidationError, ConflictError


class CourseService:
    """Domain service for course business logic"""
    
    def __init__(self, course_repository, course_offering_repository, schedule_repository):
        self.course_repository = course_repository
        self.course_offering_repository = course_offering_repository
        self.schedule_repository = schedule_repository
    
    async def create_course(self, course_data: Dict[str, Any]) -> Course:
        """Create a new course"""
        # Validate course data
        if not course_data.get("title") or not course_data.get("code"):
            raise ValidationError("Course title and code are required")
        
        if not course_data.get("department"):
            raise ValidationError("Course department is required")
        
        # Check if course code already exists
        existing_course = await self.course_repository.find_by_code(course_data["code"])
        if existing_course:
            raise ValidationError(f"Course with code {course_data['code']} already exists")
        
        # Create course entity
        course = Course(
            title=course_data["title"],
            code=course_data["code"],
            description=course_data.get("description"),
            level=course_data.get("level", CourseLevel.BEGINNER),
            credits=course_data.get("credits", 3),
            department=course_data["department"],
            prerequisites=[]
        )
        
        # Save course
        return await self.course_repository.save(course)
    
    async def update_course(self, course_id: str, course_data: Dict[str, Any]) -> Course:
        """Update an existing course"""
        # Get existing course
        course = await self.course_repository.find_by_id(course_id)
        if not course:
            raise NotFoundError(f"Course with ID {course_id} not found")
        
        # Update fields
        if "title" in course_data:
            course.title = course_data["title"]
        if "code" in course_data:
            # Check if code is already used by another course
            existing_course = await self.course_repository.find_by_code(course_data["code"])
            if existing_course and existing_course.id != course_id:
                raise ValidationError(f"Course code {course_data['code']} already used by another course")
            course.code = course_data["code"]
        if "description" in course_data:
            course.description = course_data["description"]
        if "level" in course_data:
            course.level = course_data["level"]
        if "credits" in course_data:
            course.credits = course_data["credits"]
        if "department" in course_data:
            course.department = course_data["department"]
        
        # Save course
        return await self.course_repository.save(course)
    
    async def delete_course(self, course_id: str) -> bool:
        """Delete a course"""
        # Get existing course
        course = await self.course_repository.find_by_id(course_id)
        if not course:
            raise NotFoundError(f"Course with ID {course_id} not found")
        
        # Check if course has active offerings
        active_offerings = await self.course_offering_repository.find_by_course(course_id, active_only=True)
        if active_offerings:
            raise ConflictError("Cannot delete course with active offerings. Deactivate offerings first.")
        
        # Delete course
        return await self.course_repository.delete(course_id)
    
    async def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """Get course by ID"""
        return await self.course_repository.find_by_id(course_id)
    
    async def get_course_by_code(self, code: str) -> Optional[Course]:
        """Get course by code"""
        return await self.course_repository.find_by_code(code)
    
    async def get_all_courses(self, skip: int = 0, limit: int = 100) -> List[Course]:
        """Get all courses with pagination"""
        return await self.course_repository.find_all(skip=skip, limit=limit)
    
    async def get_courses_by_department(self, department: str, skip: int = 0, limit: int = 100) -> List[Course]:
        """Get courses by department"""
        return await self.course_repository.find_by_department(department, skip=skip, limit=limit)
    
    async def get_courses_by_level(self, level: CourseLevel, skip: int = 0, limit: int = 100) -> List[Course]:
        """Get courses by level"""
        return await self.course_repository.find_by_level(level, skip=skip, limit=limit)
    
    async def add_prerequisite(self, course_id: str, prerequisite_data: Dict[str, Any]) -> "CoursePrerequisite":
        """Add prerequisite to course"""
        # Get course
        course = await self.course_repository.find_by_id(course_id)
        if not course:
            raise NotFoundError(f"Course with ID {course_id} not found")
        
        # Create prerequisite
        from .entities import CoursePrerequisite
        prerequisite = CoursePrerequisite(
            id=f"prereq_{len(course.prerequisites) + 1}",
            course_id=course_id,
            type=prerequisite_data["type"],
            requirement=prerequisite_data["requirement"],
            min_score=prerequisite_data.get("min_score"),
            description=prerequisite_data.get("description"),
            created_at=datetime.now()
        )
        
        # Save prerequisite
        # Note: This would need a prerequisite repository in a real implementation
        course.prerequisites.append(prerequisite)
        
        # Save course
        await self.course_repository.save(course)
        
        return prerequisite


class CourseOfferingService:
    """Domain service for course offering business logic"""
    
    def __init__(self, course_offering_repository, schedule_repository):
        self.course_offering_repository = course_offering_repository
        self.schedule_repository = schedule_repository
    
    async def create_course_offering(self, offering_data: Dict[str, Any]) -> CourseOffering:
        """Create a new course offering"""
        # Validate offering data
        if not offering_data.get("course_id"):
            raise ValidationError("Course ID is required")
        
        if not offering_data.get("semester") or not offering_data.get("academic_year"):
            raise ValidationError("Semester and academic year are required")
        
        # Get course
        from .entities import Course
        # In a real implementation, we'd inject the course repository
        course = await self.course_offering_repository.get_course_by_id(offering_data["course_id"])
        if not course:
            raise NotFoundError(f"Course with ID {offering_data['course_id']} not found")
        
        # Check if offering already exists
        existing_offering = await self.course_offering_repository.find_by_course_semester(
            offering_data["course_id"], offering_data["semester"], offering_data["academic_year"]
        )
        if existing_offering:
            raise ValidationError(f"Course offering for {course.title} in {offering_data['semester']} {offering_data['academic_year']} already exists")
        
        # Create course offering entity
        offering = CourseOffering(
            course_id=offering_data["course_id"],
            semester=offering_data["semester"],
            academic_year=offering_data["academic_year"],
            status=offering_data.get("status", CourseStatus.ACTIVE),
            max_capacity=offering_data.get("max_capacity", 30),
            current_enrollment=0,
            schedules=[]
        )
        
        # Save course offering
        return await self.course_offering_repository.save(offering)
    
    async def update_course_offering(self, offering_id: str, offering_data: Dict[str, Any]) -> CourseOffering:
        """Update an existing course offering"""
        # Get existing offering
        offering = await self.course_offering_repository.find_by_id(offering_id)
        if not offering:
            raise NotFoundError(f"Course offering with ID {offering_id} not found")
        
        # Update fields
        if "semester" in offering_data:
            offering.semester = offering_data["semester"]
        if "academic_year" in offering_data:
            offering.academic_year = offering_data["academic_year"]
        if "status" in offering_data:
            offering.status = offering_data["status"]
        if "max_capacity" in offering_data:
            offering.max_capacity = offering_data["max_capacity"]
        
        # Save course offering
        return await self.course_offering_repository.save(offering)
    
    async def delete_course_offering(self, offering_id: str) -> bool:
        """Delete a course offering"""
        # Get existing offering
        offering = await self.course_offering_repository.find_by_id(offering_id)
        if not offering:
            raise NotFoundError(f"Course offering with ID {offering_id} not found")
        
        # Check if offering has enrollments
        if offering.current_enrollment > 0:
            raise ConflictError("Cannot delete course offering with existing enrollments")
        
        # Delete offering
        return await self.course_offering_repository.delete(offering_id)
    
    async def get_course_offering_by_id(self, offering_id: str) -> Optional[CourseOffering]:
        """Get course offering by ID"""
        return await self.course_offering_repository.find_by_id(offering_id)
    
    async def get_course_offerings_by_course(self, course_id: str, semester: Optional[str] = None, academic_year: Optional[str] = None) -> List[CourseOffering]:
        """Get course offerings by course with optional semester/year filter"""
        return await self.course_offering_repository.find_by_course(course_id, semester=semester, academic_year=academic_year)
    
    async def get_course_offerings_by_semester_year(self, semester: str, academic_year: str) -> List[CourseOffering]:
        """Get course offerings by semester and academic year"""
        return await self.course_offering_repository.find_by_semester_year(semester, academic_year)
    
    async def add_schedule_to_offering(self, offering_id: str, schedule_data: Dict[str, Any]) -> Schedule:
        """Add schedule to course offering"""
        # Get offering
        offering = await self.course_offering_repository.find_by_id(offering_id)
        if not offering:
            raise NotFoundError(f"Course offering with ID {offering_id} not found")
        
        # Create schedule
        schedule = Schedule(
            id=f"schedule_{len(offering.schedules) + 1}",
            course_id=offering_id,
            day_of_week=schedule_data["day_of_week"],
            start_time=schedule_data["start_time"],
            end_time=schedule_data["end_time"],
            room_number=schedule_data.get("room_number"),
            building=schedule_data.get("building"),
            instructor_id=schedule_data.get("instructor_id"),
            semester=schedule_data["semester"],
            academic_year=schedule_data["academic_year"],
            max_capacity=schedule_data.get("max_capacity", offering.max_capacity),
            current_enrollment=0,
            is_active=True,
            created_at=datetime.now()
        )
        
        # Save schedule
        # Note: This would need a schedule repository in a real implementation
        offering.schedules.append(schedule)
        
        # Save offering
        await self.course_offering_repository.save(offering)
        
        return schedule
    
    async def check_schedule_conflict(self, schedule_data: Dict[str, Any]) -> bool:
        """Check if schedule conflicts with existing schedules"""
        # In a real implementation, we'd query the schedule repository
        # For now, return false (no conflict)
        return False
    
    async def get_available_seats(self, offering_id: str) -> int:
        """Get available seats in a course offering"""
        offering = await self.course_offering_repository.find_by_id(offering_id)
        if not offering:
            raise NotFoundError(f"Course offering with ID {offering_id} not found")
        
        return offering.max_capacity - offering.current_enrollment


class ScheduleService:
    """Domain service for schedule business logic"""
    
    def __init__(self, schedule_repository):
        self.schedule_repository = schedule_repository
    
    async def create_schedule(self, schedule_data: Dict[str, Any]) -> Schedule:
        """Create a new schedule"""
        # Validate schedule data
        if not schedule_data.get("course_id"):
            raise ValidationError("Course ID is required")
        
        if not schedule_data.get("day_of_week"):
            raise ValidationError("Day of week is required")
        
        if not schedule_data.get("start_time") or not schedule_data.get("end_time"):
            raise ValidationError("Start and end times are required")
        
        # Check for schedule conflicts
        if await self.check_schedule_conflict(schedule_data):
            raise ConflictError("Schedule conflicts with existing schedules")
        
        # Create schedule entity
        schedule = Schedule(
            id=f"schedule_{datetime.now().timestamp()}",
            course_id=schedule_data["course_id"],
            day_of_week=schedule_data["day_of_week"],
            start_time=schedule_data["start_time"],
            end_time=schedule_data["end_time"],
            room_number=schedule_data.get("room_number"),
            building=schedule_data.get("building"),
            instructor_id=schedule_data.get("instructor_id"),
            semester=schedule_data.get("semester"),
            academic_year=schedule_data.get("academic_year"),
            max_capacity=schedule_data.get("max_capacity", 30),
            current_enrollment=0,
            is_active=True,
            created_at=datetime.now()
        )
        
        # Save schedule
        return await self.schedule_repository.save(schedule)
    
    async def update_schedule(self, schedule_id: str, schedule_data: Dict[str, Any]) -> Schedule:
        """Update an existing schedule"""
        # Get existing schedule
        schedule = await self.schedule_repository.find_by_id(schedule_id)
        if not schedule:
            raise NotFoundError(f"Schedule with ID {schedule_id} not found")
        
        # Update fields
        if "day_of_week" in schedule_data:
            schedule.day_of_week = schedule_data["day_of_week"]
        if "start_time" in schedule_data:
            schedule.start_time = schedule_data["start_time"]
        if "end_time" in schedule_data:
            schedule.end_time = schedule_data["end_time"]
        if "room_number" in schedule_data:
            schedule.room_number = schedule_data["room_number"]
        if "building" in schedule_data:
            schedule.building = schedule_data["building"]
        if "instructor_id" in schedule_data:
            schedule.instructor_id = schedule_data["instructor_id"]
        if "max_capacity" in schedule_data:
            schedule.max_capacity = schedule_data["max_capacity"]
        if "is_active" in schedule_data:
            schedule.is_active = schedule_data["is_active"]
        
        # Save schedule
        return await self.schedule_repository.save(schedule)
    
    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule"""
        # Get existing schedule
        schedule = await self.schedule_repository.find_by_id(schedule_id)
        if not schedule:
            raise NotFoundError(f"Schedule with ID {schedule_id} not found")
        
        # Delete schedule
        return await self.schedule_repository.delete(schedule_id)
    
    async def get_schedule_by_id(self, schedule_id: str) -> Optional[Schedule]:
        """Get schedule by ID"""
        return await self.schedule_repository.find_by_id(schedule_id)
    
    async def get_schedules_by_course(self, course_id: str) -> List[Schedule]:
        """Get all schedules for a course"""
        return await self.schedule_repository.find_by_course(course_id)
    
    async def get_schedules_by_instructor(self, instructor_id: str) -> List[Schedule]:
        """Get all schedules for an instructor"""
        return await self.schedule_repository.find_by_instructor(instructor_id)
    
    async def get_schedules_by_day(self, day_of_week: DayOfWeek, semester: Optional[str] = None, academic_year: Optional[str] = None) -> List[Schedule]:
        """Get schedules by day of week"""
        return await self.schedule_repository.find_by_day(day_of_week, semester=semester, academic_year=academic_year)
    
    async def check_schedule_conflict(self, schedule_data: Dict[str, Any]) -> bool:
        """Check if schedule conflicts with existing schedules"""
        # In a real implementation, we'd query the schedule repository
        # For now, return false (no conflict)
        return False