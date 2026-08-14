"""
Department Management Service

This module provides business logic for department management:
- Department creation and management
- Department hierarchy and structure
- Department staff management
- Department analytics and reporting
- Department budget management
- Department performance tracking

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from uuid import uuid4

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.core.logging import get_logger
from src.core.base_service import BaseService
from src.infrastructure.repositories.department_repository import DepartmentRepository
from src.models.department_model import DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentStats

logger = get_logger(__name__)


class DepartmentService(BaseService):
    """Department management service with comprehensive functionality."""
    
    def __init__(self, department_repository: DepartmentRepository):
        super().__init__()
        self.department_repository = department_repository
        self._cache = {}
    
    async def initialize(self) -> None:
        """Initialize the department service."""
        try:
            await super().initialize()
            logger.info("Department service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize department service: {str(e)}")
            raise
    
    async def dispose(self) -> None:
        """Dispose the department service."""
        try:
            await super().dispose()
            self._cache.clear()
            logger.info("Department service disposed successfully")
        except Exception as e:
            logger.error(f"Failed to dispose department service: {str(e)}")
            raise
    
    # Core Business Operations
    
    async def create_department(self, department_data: Dict[str, Any]) -> DepartmentResponse:
        """Create a new department with business logic validation."""
        try:
            # Validate department data
            await self._validate_department_creation(department_data)
            
            # Check if department already exists
            existing_department = await self.department_repository.get_by_code(department_data['department_code'])
            if existing_department:
                raise ConflictError(f"Department with code {department_data['department_code']} already exists")
            
            # Create department
            department = await self.department_repository.create(**department_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return department
            
        except Exception as e:
            logger.error(f"Failed to create department: {str(e)}")
            raise
    
    async def update_department(self, department_id: str, department_data: Dict[str, Any]) -> Optional[DepartmentResponse]:
        """Update an existing department with business logic."""
        try:
            # Validate department exists
            department = await self.department_repository.get_by_id(department_id)
            if not department:
                raise NotFoundError(f"Department not found with ID: {department_id}")
            
            # Validate update data
            await self._validate_department_update(department_data)
            
            # Check for code conflicts if department_code is being updated
            if 'department_code' in department_data and department_data['department_code'] != department.department_code:
                existing_department = await self.department_repository.get_by_code(department_data['department_code'])
                if existing_department:
                    raise ConflictError(f"Department with code {department_data['department_code']} already exists")
            
            # Update department
            updated_department = await self.department_repository.update(department_id, **department_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return updated_department
            
        except Exception as e:
            logger.error(f"Failed to update department {department_id}: {str(e)}")
            raise
    
    async def get_department(self, department_id: str) -> Optional[DepartmentResponse]:
        """Get a department by ID with caching."""
        try:
            # Check cache first
            if department_id in self._cache:
                return self._cache[department_id]
            
            # Get department from repository
            department = await self.department_repository.get_by_id(department_id)
            
            if department:
                # Cache the result
                self._cache[department_id] = department
            
            return department
            
        except Exception as e:
            logger.error(f"Failed to get department {department_id}: {str(e)}")
            raise
    
    async def get_department_by_code(self, department_code: str) -> Optional[DepartmentResponse]:
        """Get a department by department code."""
        try:
            return await self.department_repository.get_by_code(department_code)
        except Exception as e:
            logger.error(f"Failed to get department by code {department_code}: {str(e)}")
            raise
    
    async def delete_department(self, department_id: str) -> bool:
        """Delete a department with business logic."""
        try:
            # Validate department exists
            department = await self.department_repository.get_by_id(department_id)
            if not department:
                raise NotFoundError(f"Department not found with ID: {department_id}")
            
            # Check if department has associated staff
            has_staff = await self._has_associated_staff(department_id)
            if has_staff:
                raise ValidationError("Cannot delete department that has associated staff")
            
            # Check if department has associated subjects
            has_subjects = await self._has_associated_subjects(department_id)
            if has_subjects:
                raise ValidationError("Cannot delete department that has associated subjects")
            
            # Check if department has associated courses
            has_courses = await self._has_associated_courses(department_id)
            if has_courses:
                raise ValidationError("Cannot delete department that has associated courses")
            
            # Delete department
            result = await self.department_repository.delete(department_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete department {department_id}: {str(e)}")
            raise
    
    # Search and Filtering
    
    async def search_departments(self, search_term: str, skip: int = 0, limit: int = 100) -> List[DepartmentResponse]:
        """Search for departments by name, code, or description."""
        try:
            departments = await self.department_repository.search_departments(
                search_term=search_term,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for dept in departments:
                self._cache[dept.id] = dept
            
            return departments
            
        except Exception as e:
            logger.error(f"Failed to search departments: {str(e)}")
            raise
    
    async def get_departments_by_faculty(self, faculty_id: str, skip: int = 0, limit: int = 100) -> List[DepartmentResponse]:
        """Get departments by faculty."""
        try:
            departments = await self.department_repository.get_by_faculty(
                faculty_id=faculty_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for dept in departments:
                self._cache[dept.id] = dept
            
            return departments
            
        except Exception as e:
            logger.error(f"Failed to get departments by faculty: {str(e)}")
            raise
    
    async def get_departments_by_head(self, head_id: str, skip: int = 0, limit: int = 100) -> List[DepartmentResponse]:
        """Get departments by head."""
        try:
            departments = await self.department_repository.get_by_head(
                head_id=head_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for dept in departments:
                self._cache[dept.id] = dept
            
            return departments
            
        except Exception as e:
            logger.error(f"Failed to get departments by head: {str(e)}")
            raise
    
    async def get_active_departments(self, skip: int = 0, limit: int = 100) -> List[DepartmentResponse]:
        """Get all active departments."""
        try:
            departments = await self.department_repository.get_active_departments(
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for dept in departments:
                self._cache[dept.id] = dept
            
            return departments
            
        except Exception as e:
            logger.error(f"Failed to get active departments: {str(e)}")
            raise
    
    # Department Hierarchy
    
    async def set_department_hierarchy(self, department_id: str, parent_id: str = None) -> bool:
        """Set department hierarchy relationship."""
        try:
            # Validate department exists
            department = await self.department_repository.get_by_id(department_id)
            if not department:
                raise NotFoundError(f"Department not found with ID: {department_id}")
            
            # Validate parent exists if provided
            if parent_id:
                parent = await self.department_repository.get_by_id(parent_id)
                if not parent:
                    raise NotFoundError(f"Parent department not found with ID: {parent_id}")
                
                # Check for circular hierarchy
                if await self._creates_circular_hierarchy(department_id, parent_id):
                    raise ValidationError("Setting this hierarchy would create a circular dependency")
            
            # Set hierarchy
            result = await self.department_repository.set_department_hierarchy(
                department_id=department_id,
                parent_id=parent_id
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to set hierarchy for department {department_id}: {str(e)}")
            raise
    
    async def get_department_hierarchy(self, department_id: str) -> Dict[str, Any]:
        """Get department hierarchy structure."""
        try:
            return await self.department_repository.get_department_hierarchy(department_id)
        except Exception as e:
            logger.error(f"Failed to get hierarchy for department {department_id}: {str(e)}")
            raise
    
    async def get_department_children(self, department_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all child departments."""
        try:
            return await self.department_repository.get_department_children(
                department_id=department_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get children for department {department_id}: {str(e)}")
            raise
    
    async def get_department_parent(self, department_id: str) -> Optional[Dict[str, Any]]:
        """Get parent department."""
        try:
            return await self.department_repository.get_department_parent(department_id)
        except Exception as e:
            logger.error(f"Failed to get parent for department {department_id}: {str(e)}")
            raise
    
    # Staff Management
    
    async def assign_head(self, department_id: str, head_id: str) -> bool:
        """Assign a department head."""
        try:
            # Validate department exists
            department = await self.department_repository.get_by_id(department_id)
            if not department:
                raise NotFoundError(f"Department not found with ID: {department_id}")
            
            # Validate head exists
            from src.infrastructure.repositories.teacher_repository import TeacherRepository
            teacher_repo = TeacherRepository()
            head = await teacher_repo.get_by_id(head_id)
            if not head:
                raise NotFoundError(f"Teacher not found with ID: {head_id}")
            
            # Check if teacher is already head of another department
            current_head_dept = await self.get_department_by_head(head_id)
            if current_head_dept and current_head_dept.id != department_id:
                raise ConflictError(f"Teacher is already head of department {current_head_dept.department_code}")
            
            # Assign head
            result = await self.department_repository.assign_head(
                department_id=department_id,
                head_id=head_id
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to assign head for department {department_id}: {str(e)}")
            raise
    
    async def remove_head(self, department_id: str) -> bool:
        """Remove department head."""
        try:
            # Validate department exists
            department = await self.department_repository.get_by_id(department_id)
            if not department:
                raise NotFoundError(f"Department not found with ID: {department_id}")
            
            # Remove head
            result = await self.department_repository.remove_head(department_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to remove head for department {department_id}: {str(e)}")
            raise
    
    async def get_department_staff(self, department_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all staff in a department."""
        try:
            return await self.department_repository.get_department_staff(
                department_id=department_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get staff for department {department_id}: {str(e)}")
            raise
    
    async def assign_staff_to_department(self, department_id: str, staff_ids: List[str]) -> bool:
        """Assign staff to a department."""
        try:
            # Validate department exists
            department = await self.department_repository.get_by_id(department_id)
            if not department:
                raise NotFoundError(f"Department not found with ID: {department_id}")
            
            # Validate staff exists
            from src.infrastructure.repositories.teacher_repository import TeacherRepository
            teacher_repo = TeacherRepository()
            for staff_id in staff_ids:
                staff = await teacher_repo.get_by_id(staff_id)
                if not staff:
                    raise NotFoundError(f"Staff member not found with ID: {staff_id}")
            
            # Assign staff
            result = await self.department_repository.assign_staff_to_department(
                department_id=department_id,
                staff_ids=staff_ids
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to assign staff to department {department_id}: {str(e)}")
            raise
    
    async def remove_staff_from_department(self, department_id: str, staff_ids: List[str]) -> bool:
        """Remove staff from a department."""
        try:
            # Validate department exists
            department = await self.department_repository.get_by_id(department_id)
            if not department:
                raise NotFoundError(f"Department not found with ID: {department_id}")
            
            # Remove staff
            result = await self.department_repository.remove_staff_from_department(
                department_id=department_id,
                staff_ids=staff_ids
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to remove staff from department {department_id}: {str(e)}")
            raise
    
    # Budget Management
    
    async def update_department_budget(self, department_id: str, budget_data: Dict[str, Any]) -> bool:
        """Update department budget."""
        try:
            # Validate department exists
            department = await self.department_repository.get_by_id(department_id)
            if not department:
                raise NotFoundError(f"Department not found with ID: {department_id}")
            
            # Validate budget data
            await self._validate_budget_data(budget_data)
            
            # Update budget
            result = await self.department_repository.update_department_budget(
                department_id=department_id,
                **budget_data
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update budget for department {department_id}: {str(e)}")
            raise
    
    async def get_department_budget(self, department_id: str) -> Optional[Dict[str, Any]]:
        """Get department budget."""
        try:
            return await self.department_repository.get_department_budget(department_id)
        except Exception as e:
            logger.error(f"Failed to get budget for department {department_id}: {str(e)}")
            raise
    
    async def generate_budget_report(self, department_id: str, fiscal_year: str = None) -> Dict[str, Any]:
        """Generate department budget report."""
        try:
            # Validate department exists
            department = await self.department_repository.get_by_id(department_id)
            if not department:
                raise NotFoundError(f"Department not found with ID: {department_id}")
            
            # Generate report
            return await self._generate_budget_report(department_id, fiscal_year)
            
        except Exception as e:
            logger.error(f"Failed to generate budget report for department {department_id}: {str(e)}")
            raise
    
    # Analytics and Reporting
    
    async def get_department_stats(self, department_id: str) -> DepartmentStats:
        """Get comprehensive department statistics."""
        try:
            # Validate department exists
            department = await self.department_repository.get_by_id(department_id)
            if not department:
                raise NotFoundError(f"Department not found with ID: {department_id}")
            
            # Get staff
            staff = await self.get_department_staff(department_id)
            total_staff = len(staff)
            active_staff = len([s for s in staff if s.get('status') == 'active'])
            
            # Get head
            head_info = await self.get_department_parent(department_id)
            head_name = head_info['head_name'] if head_info else None
            
            # Get subjects
            from src.infrastructure.repositories.subject_repository import SubjectRepository
            subject_repo = SubjectRepository()
            subjects = await subject_repo.get_by_department(department_id)
            total_subjects = len(subjects)
            active_subjects = len([s for s in subjects if s.get('status') == 'active'])
            
            # Get courses
            from src.infrastructure.repositories.course_repository import CourseRepository
            course_repo = CourseRepository()
            courses = await course_repo.get_by_department(department_id)
            total_courses = len(courses)
            active_courses = len([c for c in courses if c.get('status') == 'active'])
            
            # Get classes
            from src.infrastructure.repositories.class_repository import ClassRepository
            class_repo = ClassRepository()
            classes = await class_repo.get_by_department(department_id)
            total_classes = len(classes)
            active_classes = len([c for c in classes if c.get('status') == 'active'])
            
            # Get budget
            budget = await self.get_department_budget(department_id)
            budget_total = budget.get('total_budget', 0) if budget else 0
            budget_used = budget.get('used_budget', 0) if budget else 0
            
            # Create stats object
            stats = DepartmentStats(
                department_id=department_id,
                department_name=department.name,
                department_code=department.department_code,
                total_staff=total_staff,
                active_staff=active_staff,
                head_name=head_name,
                total_subjects=total_subjects,
                active_subjects=active_subjects,
                total_courses=total_courses,
                active_courses=active_courses,
                total_classes=total_classes,
                active_classes=active_classes,
                total_budget=budget_total,
                used_budget=budget_used,
                utilization_rate=round((budget_used / budget_total * 100) if budget_total > 0 else 0, 2),
                last_budget_update=budget.get('last_updated') if budget else None
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get department stats for {department_id}: {str(e)}")
            raise
    
    async def generate_department_report(self, department_id: str, report_type: str = "overview", 
                                       start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Generate comprehensive department report."""
        try:
            # Validate department exists
            department = await self.department_repository.get_by_id(department_id)
            if not department:
                raise NotFoundError(f"Department not found with ID: {department_id}")
            
            # Generate report based on type
            if report_type == "overview":
                return await self._generate_overview_report(department_id)
            elif report_type == "staff":
                return await self._generate_staff_report(department_id, start_date, end_date)
            elif report_type == "budget":
                return await self.generate_budget_report(department_id)
            elif report_type == "academic":
                return await self._generate_academic_report(department_id, start_date, end_date)
            elif report_type == "hierarchy":
                return await self._generate_hierarchy_report(department_id)
            else:
                raise ValidationError(f"Unknown report type: {report_type}")
                
        except Exception as e:
            logger.error(f"Failed to generate department report for {department_id}: {str(e)}")
            raise
    
    # Batch Operations
    
    async def batch_update_departments(self, updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple departments."""
        results = {}
        
        for update in updates:
            department_id = update['department_id']
            try:
                result = await self.update_department(department_id, update)
                results[department_id] = result is not None
            except Exception as e:
                logger.error(f"Failed to update department {department_id}: {str(e)}")
                results[department_id] = False
        
        return results
    
    async def batch_assign_staff(self, assignments: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Assign staff to multiple departments."""
        results = {}
        
        for assignment in assignments:
            department_id = assignment['department_id']
            try:
                result = await self.assign_staff_to_department(
                    department_id=department_id,
                    staff_ids=assignment['staff_ids']
                )
                results[department_id] = result
            except Exception as e:
                logger.error(f"Failed to assign staff to department {department_id}: {str(e)}")
                results[department_id] = False
        
        return results
    
    # Helper Methods
    
    async def _validate_department_creation(self, data: Dict[str, Any]) -> None:
        """Validate department creation data."""
        required_fields = ['name', 'department_code', 'description', 'faculty_id', 'head_id']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate department code format
        if not self._validate_department_code(data['department_code']):
            raise ValidationError("Invalid department code format")
        
        # Validate faculty exists
        from src.infrastructure.repositories.faculty_repository import FacultyRepository
        faculty_repo = FacultyRepository()
        faculty = await faculty_repo.get_by_id(data['faculty_id'])
        if not faculty:
            raise NotFoundError(f"Faculty not found with ID: {data['faculty_id']}")
        
        # Validate head exists
        from src.infrastructure.repositories.teacher_repository import TeacherRepository
        teacher_repo = TeacherRepository()
        head = await teacher_repo.get_by_id(data['head_id'])
        if not head:
            raise NotFoundError(f"Head teacher not found with ID: {data['head_id']}")
    
    async def _validate_department_update(self, data: Dict[str, Any]) -> None:
        """Validate department update data."""
        allowed_fields = ['name', 'description', 'head_id', 'status', 'budget', 'mission', 'vision']
        
        for field in data.keys():
            if field not in allowed_fields:
                raise ValidationError(f"Cannot update field: {field}")
        
        # Validate head if provided
        if 'head_id' in data and data['head_id']:
            from src.infrastructure.repositories.teacher_repository import TeacherRepository
            teacher_repo = TeacherRepository()
            head = await teacher_repo.get_by_id(data['head_id'])
            if not head:
                raise NotFoundError(f"Head teacher not found with ID: {data['head_id']}")
    
    def _validate_department_code(self, department_code: str) -> bool:
        """Validate department code format."""
        import re
        pattern = r'^[A-Z]{3}$'  # Example: CSF, COM
        return re.match(pattern, department_code) is not None
    
    async def _validate_budget_data(self, data: Dict[str, Any]) -> None:
        """Validate budget data."""
        required_fields = ['total_budget', 'budget_year']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required budget field '{field}' is missing or empty")
        
        # Validate budget amounts
        if not (0 <= data['total_budget'] <= 1000000000):  # Max 1 billion
            raise ValidationError("Total budget must be between 0 and 1,000,000,000")
        
        if 'used_budget' in data and data['used_budget']:
            if not (0 <= data['used_budget'] <= data['total_budget']):
                raise ValidationError("Used budget cannot exceed total budget")
        
        # Validate fiscal year format
        if not self._validate_fiscal_year(data['budget_year']):
            raise ValidationError("Invalid fiscal year format")
    
    def _validate_fiscal_year(self, fiscal_year: str) -> bool:
        """Validate fiscal year format."""
        import re
        pattern = r'^20[0-9]{2}-20[0-9]{2}$'  # Example: 2023-2024
        return re.match(pattern, fiscal_year) is not None
    
    async def _has_associated_staff(self, department_id: str) -> bool:
        """Check if department has associated staff."""
        staff = await self.get_department_staff(department_id)
        return len(staff) > 0
    
    async def _has_associated_subjects(self, department_id: str) -> bool:
        """Check if department has associated subjects."""
        from src.infrastructure.repositories.subject_repository import SubjectRepository
        subject_repo = SubjectRepository()
        subjects = await subject_repo.get_by_department(department_id)
        return len(subjects) > 0
    
    async def _has_associated_courses(self, department_id: str) -> bool:
        """Check if department has associated courses."""
        from src.infrastructure.repositories.course_repository import CourseRepository
        course_repo = CourseRepository()
        courses = await course_repo.get_by_department(department_id)
        return len(courses) > 0
    
    async def _creates_circular_hierarchy(self, department_id: str, parent_id: str) -> bool:
        """Check if setting hierarchy creates circular dependency."""
        # This would implement a graph traversal algorithm to detect cycles
        # For now, return False (should be implemented)
        return False
    
    async def _generate_overview_report(self, department_id: str) -> Dict[str, Any]:
        """Generate overview report for department."""
        try:
            department = await self.get_department(department_id)
            stats = await self.get_department_stats(department_id)
            hierarchy = await self.get_department_hierarchy(department_id)
            staff = await self.get_department_staff(department_id, 0, 100)
            
            return {
                "department": department.to_dict() if department else None,
                "stats": stats,
                "hierarchy": hierarchy,
                "staff": staff,
                "budget": await self.get_department_budget(department_id),
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "overview"
            }
        except Exception as e:
            logger.error(f"Failed to generate overview report for {department_id}: {str(e)}")
            raise
    
    async def _generate_staff_report(self, department_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate staff report for department."""
        try:
            department = await self.get_department(department_id)
            staff = await self.get_department_staff(department_id, 0, 100)
            
            # Analyze staff data
            staff_analysis = self._analyze_staff(staff)
            
            return {
                "department": department.to_dict() if department else None,
                "staff": staff,
                "analysis": staff_analysis,
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "staff"
            }
        except Exception as e:
            logger.error(f"Failed to generate staff report for {department_id}: {str(e)}")
            raise
    
    async def _generate_academic_report(self, department_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate academic report for department."""
        try:
            department = await self.get_department(department_id)
            subjects = []
            courses = []
            classes = []
            
            # Get academic entities
            from src.infrastructure.repositories.subject_repository import SubjectRepository
            subject_repo = SubjectRepository()
            subjects = await subject_repo.get_by_department(department_id, 0, 100)
            
            from src.infrastructure.repositories.course_repository import CourseRepository
            course_repo = CourseRepository()
            courses = await course_repo.get_by_department(department_id, 0, 100)
            
            from src.infrastructure.repositories.class_repository import ClassRepository
            class_repo = ClassRepository()
            classes = await class_repo.get_by_department(department_id, 0, 100)
            
            # Analyze academic performance
            academic_analysis = self._analyze_academic_performance(courses, classes)
            
            return {
                "department": department.to_dict() if department else None,
                "subjects": subjects,
                "courses": courses,
                "classes": classes,
                "analysis": academic_analysis,
                "report_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "academic"
            }
        except Exception as e:
            logger.error(f"Failed to generate academic report for {department_id}: {str(e)}")
            raise
    
    async def _generate_hierarchy_report(self, department_id: str) -> Dict[str, Any]:
        """Generate hierarchy report for department."""
        try:
            department = await self.get_department(department_id)
            hierarchy = await self.get_department_hierarchy(department_id)
            children = await self.get_department_children(department_id, 0, 100)
            
            # Build complete hierarchy tree
            hierarchy_tree = self._build_hierarchy_tree(department_id)
            
            return {
                "department": department.to_dict() if department else None,
                "hierarchy": hierarchy,
                "children": children,
                "hierarchy_tree": hierarchy_tree,
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "hierarchy"
            }
        except Exception as e:
            logger.error(f"Failed to generate hierarchy report for {department_id}: {str(e)}")
            raise
    
    def _analyze_staff(self, staff: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze department staff."""
        if not staff:
            return {"total_staff": 0, "by_role": {}, "by_experience": {}}
        
        # Group by role
        by_role = {}
        # Group by experience
        by_experience = {}
        # Group by qualification
        by_qualification = {}
        
        for person in staff:
            role = person.get('role', 'Unknown')
            experience = person.get('experience_years', 0)
            qualification = person.get('qualification', 'Unknown')
            
            by_role[role] = by_role.get(role, 0) + 1
            by_experience_level = 'Junior' if experience < 3 else 'Mid' if experience < 7 else 'Senior'
            by_experience[by_experience_level] = by_experience.get(by_experience_level, 0) + 1
            by_qualification[qualification] = by_qualification.get(qualification, 0) + 1
        
        return {
            "total_staff": len(staff),
            "by_role": by_role,
            "by_experience": by_experience,
            "by_qualification": by_qualification,
            "average_experience": sum(p.get('experience_years', 0) for p in staff) / len(staff),
            "staff_turnover_rate": 0  # Would need historical data
        }
    
    def _analyze_academic_performance(self, courses: List[Dict[str, Any]], classes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze department academic performance."""
        if not courses and not classes:
            return {
                "total_courses": 0,
                "total_classes": 0,
                "average_enrollment": 0,
                "completion_rate": 0,
                "success_rate": 0
            }
        
        # Calculate enrollment statistics
        total_enrollment = sum(c.get('total_students', 0) for c in courses)
        average_enrollment = total_enrollment / len(courses) if courses else 0
        
        # Mock performance data
        completion_rate = 85.0  # Would come from actual course completion data
        success_rate = 78.5     # Would come from actual success rates
        
        return {
            "total_courses": len(courses),
            "total_classes": len(classes),
            "average_enrollment": round(average_enrollment, 2),
            "completion_rate": completion_rate,
            "success_rate": success_rate,
            "courses_by_level": self._group_courses_by_level(courses),
            "classes_by_semester": self._group_classes_by_semester(classes)
        }
    
    def _group_courses_by_level(self, courses: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group courses by academic level."""
        by_level = {}
        for course in courses:
            level = course.get('level', 'Unknown')
            by_level[level] = by_level.get(level, 0) + 1
        return by_level
    
    def _group_classes_by_semester(self, classes: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group classes by semester."""
        by_semester = {}
        for class_obj in classes:
            semester = class_obj.get('semester', 'Unknown')
            by_semester[semester] = by_semester.get(semester, 0) + 1
        return by_semester
    
    def _build_hierarchy_tree(self, department_id: str) -> Dict[str, Any]:
        """Build complete hierarchy tree for department."""
        # This would implement a recursive tree building algorithm
        # For now, return empty dict
        return {}
    
    async def _generate_budget_report(self, department_id: str, fiscal_year: str) -> Dict[str, Any]:
        """Generate budget report for department."""
        try:
            department = await self.get_department(department_id)
            budget = await self.get_department_budget(department_id)
            
            if not budget:
                raise NotFoundError(f"Budget not found for department {department_id}")
            
            # Analyze budget usage
            budget_analysis = self._analyze_budget(budget)
            
            return {
                "department": department.to_dict() if department else None,
                "budget": budget,
                "analysis": budget_analysis,
                "fiscal_year": fiscal_year,
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "budget"
            }
        except Exception as e:
            logger.error(f"Failed to generate budget report for {department_id}: {str(e)}")
            raise
    
    def _analyze_budget(self, budget: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze department budget."""
        total_budget = budget.get('total_budget', 0)
        used_budget = budget.get('used_budget', 0)
        remaining_budget = total_budget - used_budget
        
        return {
            "utilization_rate": round((used_budget / total_budget * 100) if total_budget > 0 else 0, 2),
            "remaining_budget": remaining_budget,
            "budget_variance": budget.get('budget_variance', 0),
            "forecast_completion": self._calculate_budget_forecast(total_budget, used_budget),
            "spending_trend": self._analyze_spending_trend(budget.get('historical_spending', []))
        }
    
    def _calculate_budget_forecast(self, total_budget: float, used_budget: float) -> str:
        """Calculate budget forecast."""
        if used_budget == 0:
            return "No spending data available"
        
        current_rate = used_budget / total_budget
        if current_rate < 0.25:
            return "On track"
        elif current_rate < 0.5:
            return "Moderate usage"
        elif current_rate < 0.75:
            return "High usage - monitor closely"
        else:
            return "At risk - may exceed budget"
    
    def _analyze_spending_trend(self, historical_spending: List[Dict[str, Any]]) -> str:
        """Analyze spending trend."""
        if len(historical_spending) < 2:
            return "Insufficient data"
        
        # Simple trend analysis
        recent = historical_spending[-1]['amount']
        previous = historical_spending[-2]['amount']
        
        if recent > previous * 1.1:
            return "Increasing"
        elif recent < previous * 0.9:
            return "Decreasing"
        else:
            return "Stable"
    
    async def _invalidate_cache(self) -> None:
        """Invalidate department cache."""
        self._cache.clear()