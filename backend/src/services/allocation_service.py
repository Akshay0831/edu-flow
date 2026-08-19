"""
Class & Teacher Allocation Service for Edu-Flow

This service provides functionality for class and teacher allocation:
- Automated teacher-class assignment algorithms
- Availability checking and scheduling
- Constraint-based optimization
- Load balancing across teachers
- Resource allocation and scheduling
- Request management and approval

Author: Edu-Flow Team
"""

import asyncio
import json
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import uuid

from api.deps import get_db
from models.allocation import (
    ClassAllocation, TeacherAvailability, ClassSchedule, AllocationConstraint,
    AllocationRequest, ResourceAvailability, AllocationStatus, ConstraintType
)
from src.services.base_service import BaseService
from core.exceptions import NotFoundError, ValidationError, ConfigurationError
from core.cache import CacheManager
from config.settings import get_settings

class AllocationService(BaseService):
    """Class & Teacher Allocation Service"""
    
    def __init__(self, db: Session, cache_manager: CacheManager):
        super().__init__(db, cache_manager)
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.cache_key_prefix = "allocation"
        
    # region: Basic CRUD Operations
    async def create_allocation(
        self,
        class_id: str,
        teacher_id: str,
        subject_id: str,
        academic_year: str,
        semester: str,
        allocation_priority: int = 1,
        load_percentage: float = 100.0,
        teaching_method: str = "lecture",
        notes: Optional[str] = None
    ) -> ClassAllocation:
        """Create a new class allocation"""
        
        # Validate data exists (placeholder - implement actual validation)
        allocation = ClassAllocation(
            class_id=class_id,
            teacher_id=teacher_id,
            subject_id=subject_id,
            academic_year=academic_year,
            semester=semester,
            allocation_priority=allocation_priority,
            load_percentage=load_percentage,
            teaching_method=teaching_method,
            notes=notes
        )
        
        self.db.add(allocation)
        self.db.commit()
        self.db.refresh(allocation)
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        # Schedule class
        await self._schedule_class(allocation)
        
        self.logger.info(f"Created class allocation: {allocation.id}")
        return allocation
    
    async def get_allocation_by_id(self, allocation_id: str) -> Optional[ClassAllocation]:
        """Get allocation by ID"""
        cache_key = f"{self.cache_key_prefix}_allocation_{allocation_id}"
        
        # Check cache first
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return cached_data
        
        # Get from database
        allocation = self.db.query(ClassAllocation).filter(
            ClassAllocation.id == allocation_id
        ).first()
        
        if allocation:
            await self.cache_manager.set(cache_key, allocation, ttl=3600)  # 1 hour
        
        return allocation
    
    async def get_class_allocations(
        self,
        class_id: Optional[str] = None,
        teacher_id: Optional[str] = None,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[ClassAllocation]:
        """Get allocations based on filters"""
        cache_key = f"{self.cache_key_prefix}_query_{hash(str(locals()))}"
        
        # Check cache first
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return cached_data
        
        # Build query
        query = self.db.query(ClassAllocation).filter(ClassAllocation.is_active == True)
        
        if class_id:
            query = query.filter(ClassAllocation.class_id == class_id)
        if teacher_id:
            query = query.filter(ClassAllocation.teacher_id == teacher_id)
        if academic_year:
            query = query.filter(ClassAllocation.academic_year == academic_year)
        if semester:
            query = query.filter(ClassAllocation.semester == semester)
        if status:
            query = query.filter(ClassAllocation.allocation_status == status)
        
        allocations = query.all()
        
        if allocations:
            await self.cache_manager.set(cache_key, allocations, ttl=3600)  # 1 hour
        
        return allocations
    
    async def update_allocation(
        self,
        allocation_id: str,
        updates: Dict[str, Any]
    ) -> ClassAllocation:
        """Update allocation"""
        allocation = await self.get_allocation_by_id(allocation_id)
        
        if not allocation:
            raise NotFoundError(f"Allocation not found: {allocation_id}")
        
        # Update allowed fields
        allowed_fields = [
            "allocation_status", "allocation_priority", "load_percentage",
            "teaching_method", "evaluation_method", "notes", "is_active"
        ]
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(allocation, field, value)
        
        allocation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(allocation)
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        # Reschedule if needed
        if allocation.is_active:
            await self._schedule_class(allocation)
        
        self.logger.info(f"Updated allocation: {allocation_id}")
        return allocation
    
    async def delete_allocation(self, allocation_id: str) -> bool:
        """Delete allocation"""
        allocation = await self.get_allocation_by_id(allocation_id)
        
        if not allocation:
            raise NotFoundError(f"Allocation not found: {allocation_id}")
        
        allocation.is_active = False
        allocation.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        # Remove schedule
        await self._remove_class_schedule(allocation_id)
        
        self.logger.info(f"Deleted allocation: {allocation_id}")
        return True
    
    # region: Allocation Optimization
    async def optimize_allocation(
        self,
        academic_year: str,
        semester: str,
        allocation_requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Optimize class allocations based on constraints and preferences"""
        
        # Step 1: Validate allocation requests
        valid_requests = await self._validate_allocation_requests(allocation_requests)
        
        # Step 2: Check teacher availability and constraints
        allocation_options = []
        for request in valid_requests:
            options = await self._generate_allocation_options(request, academic_year, semester)
            allocation_options.extend(options)
        
        # Step 3: Apply optimization algorithms
        optimized_allocations = await self._apply_optimization(allocation_options)
        
        # Step 4: Create allocations
        created_allocations = []
        for allocation_data in optimized_allocations:
            allocation = await self.create_allocation(
                class_id=allocation_data["class_id"],
                teacher_id=allocation_data["teacher_id"],
                subject_id=allocation_data["subject_id"],
                academic_year=academic_year,
                semester=semester,
                allocation_priority=allocation_data.get("priority", 1),
                load_percentage=allocation_data.get("load_percentage", 100.0),
                teaching_method=allocation_data.get("teaching_method", "lecture"),
                notes=allocation_data.get("notes")
            )
            created_allocations.append(allocation)
        
        # Step 5: Generate report
        report = {
            "academic_year": academic_year,
            "semester": semester,
            "total_requests": len(allocation_requests),
            "successful_allocations": len(created_allocations),
            "failed_allocations": len(allocation_requests) - len(created_allocations),
            "allocations": [alloc.__dict__ for alloc in created_allocations],
            "optimization_summary": await self._generate_optimization_summary(optimized_allocations),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return report
    
    async def auto_allocate_classes(
        self,
        academic_year: str,
        semester: str,
        force_allocation: bool = False
    ) -> Dict[str, Any]:
        """Automatically allocate classes to available teachers"""
        
        # Get unallocated classes
        unallocated_classes = await self._get_unallocated_classes(academic_year, semester)
        
        # Get available teachers
        available_teachers = await self._get_available_teachers(academic_year, semester)
        
        # Get allocation constraints
        constraints = await self._get_allocation_constraints()
        
        # Generate allocation suggestions
        suggestions = await self._generate_allocation_suggestions(
            unallocated_classes, available_teachers, constraints, academic_year, semester
        )
        
        # Apply suggestions if requested
        if force_allocation:
            created_allocations = []
            for suggestion in suggestions:
                allocation = await self.create_allocation(
                    class_id=suggestion["class_id"],
                    teacher_id=suggestion["teacher_id"],
                    subject_id=suggestion["subject_id"],
                    academic_year=academic_year,
                    semester=semester,
                    allocation_priority=suggestion.get("priority", 1),
                    load_percentage=suggestion.get("load_percentage", 100.0),
                    teaching_method=suggestion.get("teaching_method", "lecture"),
                    notes=suggestion.get("notes", "Auto-allocated")
                )
                created_allocations.append(allocation)
            
            return {
                "action": "auto_allocated",
                "allocated_count": len(created_allocations),
                "allocations": [alloc.__dict__ for alloc in created_allocations],
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "action": "suggested",
                "suggestions": suggestions,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # region: Availability Management
    async def create_teacher_availability(
        self,
        teacher_id: str,
        day_of_week: str,
        start_time: str,
        end_time: str,
        academic_year: str,
        semester: str,
        preference_level: int = 1,
        notes: Optional[str] = None
    ) -> TeacherAvailability:
        """Create teacher availability"""
        
        availability = TeacherAvailability(
            teacher_id=teacher_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            academic_year=academic_year,
            semester=semester,
            preference_level=preference_level,
            notes=notes
        )
        
        self.db.add(availability)
        self.db.commit()
        self.db.refresh(availability)
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        self.logger.info(f"Created teacher availability: {availability.id}")
        return availability
    
    async def check_teacher_availability(
        self,
        teacher_id: str,
        day_of_week: str,
        start_time: str,
        end_time: str,
        academic_year: str,
        semester: str
    ) -> Dict[str, Any]:
        """Check if teacher is available for given time slot"""
        
        # Get teacher's availability
        availabilities = self.db.query(TeacherAvailability).filter(
            TeacherAvailability.teacher_id == teacher_id,
            TeacherAvailability.day_of_week == day_of_week,
            TeacherAvailability.is_available == True,
            TeacherAvailability.academic_year == academic_year,
            TeacherAvailability.semester == semester
        ).all()
        
        # Check for conflicts
        conflicts = []
        for avail in availabilities:
            if self._time_slots_overlap(start_time, end_time, avail.start_time, avail.end_time):
                conflicts.append({
                    "availability_id": avail.id,
                    "start_time": avail.start_time,
                    "end_time": avail.end_time,
                    "preference_level": avail.preference_level
                })
        
        return {
            "teacher_id": teacher_id,
            "requested_slot": {
                "day_of_week": day_of_week,
                "start_time": start_time,
                "end_time": end_time
            },
            "is_available": len(conflicts) == 0,
            "conflicts": conflicts,
            "available_slots": len(availabilities),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def check_resource_availability(
        self,
        resource_id: str,
        resource_type: str,
        day_of_week: str,
        start_time: str,
        end_time: str,
        academic_year: str,
        semester: str
    ) -> Dict[str, Any]:
        """Check if resource is available for given time slot"""
        
        # Get resource availability
        availabilities = self.db.query(ResourceAvailability).filter(
            ResourceAvailability.resource_id == resource_id,
            ResourceAvailability.resource_type == resource_type,
            ResourceAvailability.is_available == True,
            ResourceAvailability.day_of_week == day_of_week,
            ResourceAvailability.academic_year == academic_year,
            ResourceAvailability.semester == semester
        ).all()
        
        # Check for conflicts
        conflicts = []
        for avail in availabilities:
            if self._time_slots_overlap(start_time, end_time, avail.start_time, avail.end_time):
                conflicts.append({
                    "availability_id": avail.id,
                    "start_time": avail.start_time,
                    "end_time": avail.end_time
                })
        
        return {
            "resource_id": resource_id,
            "resource_type": resource_type,
            "requested_slot": {
                "day_of_week": day_of_week,
                "start_time": start_time,
                "end_time": end_time
            },
            "is_available": len(conflicts) == 0,
            "conflicts": conflicts,
            "available_slots": len(availabilities),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # region: Request Management
    async def create_allocation_request(
        self,
        class_id: str,
        subject_id: str,
        academic_year: str,
        semester: str,
        request_reason: Optional[str] = None,
        special_requirements: Optional[str] = None,
        requested_teacher_id: Optional[str] = None,
        requested_by: Optional[str] = None
    ) -> AllocationRequest:
        """Create allocation request"""
        
        request = AllocationRequest(
            class_id=class_id,
            requested_teacher_id=requested_teacher_id,
            subject_id=subject_id,
            academic_year=academic_year,
            semester=semester,
            request_reason=request_reason,
            special_requirements=special_requirements,
            requested_by=requested_by or "system"
        )
        
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        self.logger.info(f"Created allocation request: {request.id}")
        return request
    
    async def approve_allocation_request(
        self,
        request_id: str,
        approved_teacher_id: str,
        notes: Optional[str] = None
    ) -> ClassAllocation:
        """Approve allocation request and create allocation"""
        
        request = self.db.query(AllocationRequest).filter(
            AllocationRequest.id == request_id
        ).first()
        
        if not request:
            raise NotFoundError(f"Allocation request not found: {request_id}")
        
        # Create allocation
        allocation = await self.create_allocation(
            class_id=request.class_id,
            teacher_id=approved_teacher_id,
            subject_id=request.subject_id,
            academic_year=request.academic_year,
            semester=request.semester,
            notes=f"Approved request: {request.request_reason}. {notes or ''}"
        )
        
        # Update request status
        request.request_status = "approved"
        request.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        self.logger.info(f"Approved allocation request: {request_id}")
        return allocation
    
    # region: Scheduling
    async def _schedule_class(self, allocation: ClassAllocation) -> bool:
        """Schedule class based on allocation"""
        # This would implement actual scheduling logic
        # For now, create a placeholder schedule
        pass
    
    async def _remove_class_schedule(self, allocation_id: str) -> bool:
        """Remove class schedule"""
        # This would remove scheduling for the allocation
        pass
    
    async def optimize_timetable(
        self,
        academic_year: str,
        semester: str,
        constraints: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Optimize timetable for given academic year and semester"""
        
        # Get all active allocations
        allocations = await self.get_class_allocations(
            academic_year=academic_year,
            semester=semester,
            status=AllocationStatus.APPROVED.value
        )
        
        # Get schedules
        schedules = self.db.query(ClassSchedule).filter(
            ClassSchedule.academic_year == academic_year,
            ClassSchedule.semester == semester
        ).all()
        
        # Apply optimization algorithm
        optimized_schedules = await self._apply_timetable_optimization(allocations, schedules, constraints)
        
        return {
            "academic_year": academic_year,
            "semester": semester,
            "total_allocations": len(allocations),
            "schedules": [sched.__dict__ for sched in optimized_schedules],
            "optimization_report": await self._generate_timetable_report(allocations, optimized_schedules),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # region: Helper Methods
    def _time_slots_overlap(self, start1: str, end1: str, start2: str, end2: str) -> bool:
        """Check if two time slots overlap"""
        # Simple time overlap check
        # This would need proper time parsing in a real implementation
        return True  # Placeholder
    
    async def _validate_allocation_requests(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate allocation requests"""
        # Placeholder implementation
        return requests
    
    async def _generate_allocation_options(
        self,
        request: Dict[str, Any],
        academic_year: str,
        semester: str
    ) -> List[Dict[str, Any]]:
        """Generate allocation options for a request"""
        # Placeholder implementation
        return []
    
    async def _apply_optimization(self, options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply optimization algorithm to allocation options"""
        # Placeholder implementation
        return options
    
    async def _generate_optimization_summary(self, allocations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate optimization summary"""
        return {
            "total_allocations": len(allocations),
            "avg_load_balance": 100.0,  # Placeholder
            "constraint_violations": 0
        }
    
    async def _get_unallocated_classes(self, academic_year: str, semester: str) -> List[Dict[str, Any]]:
        """Get classes without allocations"""
        # Placeholder implementation
        return []
    
    async def _get_available_teachers(self, academic_year: str, semester: str) -> List[Dict[str, Any]]:
        """Get available teachers"""
        # Placeholder implementation
        return []
    
    async def _get_allocation_constraints(self) -> List[AllocationConstraint]:
        """Get allocation constraints"""
        return self.db.query(AllocationConstraint).filter(
            AllocationConstraint.is_active == True
        ).all()
    
    async def _generate_allocation_suggestions(
        self,
        classes: List[Dict[str, Any]],
        teachers: List[Dict[str, Any]],
        constraints: List[AllocationConstraint],
        academic_year: str,
        semester: str
    ) -> List[Dict[str, Any]]:
        """Generate allocation suggestions"""
        # Placeholder implementation
        return []
    
    async def _apply_timetable_optimization(
        self,
        allocations: List[ClassAllocation],
        schedules: List[ClassSchedule],
        constraints: List[Dict[str, Any]]
    ) -> List[ClassSchedule]:
        """Apply timetable optimization"""
        # Placeholder implementation
        return schedules
    
    async def _generate_timetable_report(
        self,
        allocations: List[ClassAllocation],
        schedules: List[ClassSchedule]
    ) -> Dict[str, Any]:
        """Generate timetable optimization report"""
        return {
            "total_allocations": len(allocations),
            "total_schedules": len(schedules),
            "conflicts": 0,  # Placeholder
            "optimization_score": 0.0  # Placeholder
        }