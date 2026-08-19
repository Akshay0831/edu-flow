"""
Timetable Entry Management Repository

This module provides database operations for timetable entry management:
- CRUD operations for individual timetable entries
- Entry scheduling and occurrence tracking
- Resource allocation and conflict management
- Entry analytics and reporting
- Recurring schedule management
- Batch operations and optimization

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, time, date, timedelta
from uuid import uuid4

from core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from core.logging import get_logger
from core.database_abstraction import DatabaseManager, DatabaseInterface
from infrastructure.repositories.base_repository_with_db import BaseRepositoryWithDB, QueryResult
from models.timetable_entry import (
    TimetableEntryCreate, TimetableEntryUpdate, TimetableEntryResponse,
    TimetableEntryOccurrence, TimetableEntryConflict, ResourceAllocationRequest,
    ResourceAllocationResponse, ResourceAllocation
)

logger = get_logger(__name__)


class TimetableEntryRepository(BaseRepositoryWithDB):
    """Timetable entry management repository with comprehensive functionality."""
    
    def __init__(self, database_manager):
        super().__init__("timetable_entries", database_manager)
        self._occurrences_collection = "timetable_occurrences"
        self._allocations_collection = "resource_allocations"
        self._conflicts_collection = "schedule_conflicts"
    
    # Core CRUD Operations
    
    async def get_by_id(self, entry_id: str) -> Optional[TimetableEntryResponse]:
        """Get a timetable entry by ID."""
        try:
            result = await self._find_one(self._collection, {"entry_id": entry_id})
            if result:
                return TimetableEntryResponse(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting timetable entry by ID {entry_id}: {str(e)}")
            raise DatabaseError(f"Failed to get timetable entry: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100, 
                     filters: Dict[str, Any] = None) -> List[TimetableEntryResponse]:
        """Get all timetable entries with optional filtering."""
        try:
            query_filter = filters or {}
            result = await self._find_many(
                self._collection, 
                query_filter,
                skip=skip,
                limit=limit,
                sort=[("created_at", -1)]
            )
            
            return [TimetableEntryResponse(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting all timetable entries: {str(e)}")
            raise DatabaseError(f"Failed to fetch timetable entries: {str(e)}")
    
    async def create(self, **data) -> TimetableEntryResponse:
        """Create a new timetable entry."""
        try:
            # Add required fields
            if 'entry_id' not in data:
                data['entry_id'] = str(uuid4())
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow()
            if 'updated_at' not in data:
                data['updated_at'] = datetime.utcnow()
            
            # Validate timetable entry data
            await self._validate_entry_data(data)
            
            # Insert into database
            result = await self._insert(self._collection, data)
            if result.inserted_id:
                created_entry = await self.get_by_id(data['entry_id'])
                return created_entry
            else:
                raise DatabaseError("Failed to create timetable entry")
                
        except Exception as e:
            logger.error(f"Error creating timetable entry: {str(e)}")
            raise DatabaseError(f"Failed to create timetable entry: {str(e)}")
    
    async def update(self, entry_id: str, **data) -> Optional[TimetableEntryResponse]:
        """Update an existing timetable entry."""
        try:
            # Update timestamps
            data['updated_at'] = datetime.utcnow()
            
            # Validate updated timetable entry data
            await self._validate_entry_data(data)
            
            # Update in database
            result = await self._update(
                self._collection,
                {"entry_id": entry_id},
                {"$set": data}
            )
            
            if result.modified_count > 0:
                updated_entry = await self.get_by_id(entry_id)
                return updated_entry
            else:
                raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
                
        except Exception as e:
            logger.error(f"Error updating timetable entry {entry_id}: {str(e)}")
            raise DatabaseError(f"Failed to update timetable entry: {str(e)}")
    
    async def delete(self, entry_id: str) -> bool:
        """Delete a timetable entry and related data."""
        try:
            # Delete the entry
            result = await self._delete(self._collection, {"entry_id": entry_id})
            
            if result.deleted_count > 0:
                # Also delete related occurrences, allocations, and conflicts
                await self._delete(self._occurrences_collection, {"entry_id": entry_id})
                await self._delete(self._allocations_collection, {"entry_id": entry_id})
                await self._delete(self._conflicts_collection, {"entry_id": entry_id})
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error deleting timetable entry {entry_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete timetable entry: {str(e)}")
    
    # Entry-specific Operations
    
    async def get_timetable_entries(self, timetable_id: str, filters: Dict[str, Any] = None) -> List[TimetableEntryResponse]:
        """Get all entries for a specific timetable."""
        try:
            query_filter = {"timetable_id": timetable_id}
            query_filter.update(filters or {})
            
            result = await self._find_many(
                self._collection,
                query_filter,
                sort=[("day_of_week", 1), ("start_time", 1)]
            )
            
            return [TimetableEntryResponse(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting entries for timetable {timetable_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch timetable entries: {str(e)}")
    
    async def get_teacher_schedule(self, teacher_id: str, start_date: date = None, end_date: date = None) -> List[TimetableEntryResponse]:
        """Get schedule for a specific teacher."""
        try:
            query_filter = {"teacher_id": teacher_id}
            
            if start_date and end_date:
                query_filter["start_date"] = {"$gte": start_date, "$lte": end_date}
            
            result = await self._find_many(
                self._collection,
                query_filter,
                sort=[("day_of_week", 1), ("start_time", 1)]
            )
            
            return [TimetableEntryResponse(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting teacher schedule for {teacher_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch teacher schedule: {str(e)}")
    
    async def get_class_schedule(self, class_id: str, start_date: date = None, end_date: date = None) -> List[TimetableEntryResponse]:
        """Get schedule for a specific class."""
        try:
            query_filter = {"class_id": class_id}
            
            if start_date and end_date:
                query_filter["start_date"] = {"$gte": start_date, "$lte": end_date}
            
            result = await self._find_many(
                self._collection,
                query_filter,
                sort=[("day_of_week", 1), ("start_time", 1)]
            )
            
            return [TimetableEntryResponse(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting class schedule for {class_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch class schedule: {str(e)}")
    
    # Conflict Detection and Management
    
    async def check_entry_conflicts(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for scheduling conflicts for a new entry."""
        try:
            # Build query for conflict detection
            query_filter = {
                "timetable_id": entry_data["timetable_id"],
                "day_of_week": entry_data["day_of_week"],
                "entry_id": {"$ne": entry_data.get("entry_id", "")},
                "is_active": True
            }
            
            # Find overlapping times
            conflicting_entries = await self._find_many(self._collection, query_filter)
            conflicts = []
            
            for existing_entry in conflicting_entries:
                if self._times_overlap(
                    existing_entry["start_time"], existing_entry["end_time"],
                    entry_data["start_time"], entry_data["end_time"]
                ):
                    conflict_type = self._determine_conflict_type(existing_entry, entry_data)
                    conflicts.append({
                        "entry_id": existing_entry["entry_id"],
                        "conflict_type": conflict_type,
                        "existing_entry": existing_entry
                    })
            
            return {
                "has_conflict": len(conflicts) > 0,
                "conflict_count": len(conflicts),
                "conflicts": conflicts,
                "conflict_details": self._generate_conflict_message(conflicts)
            }
            
        except Exception as e:
            logger.error(f"Error checking entry conflicts: {str(e)}")
            raise DatabaseError(f"Failed to check entry conflicts: {str(e)}")
    
    async def resolve_conflict(self, conflict_id: str, resolution_type: str, resolution_data: Dict[str, Any]) -> bool:
        """Resolve a scheduling conflict."""
        try:
            # Get the conflict
            conflict = await self._find_one(self._conflicts_collection, {"conflict_id": conflict_id})
            if not conflict:
                raise NotFoundError(f"Conflict not found with ID: {conflict_id}")
            
            # Apply resolution based on type
            if resolution_type == "reschedule":
                await self._apply_resolution(conflict, resolution_data)
            elif resolution_type == "resource_change":
                await self._apply_resource_change(conflict, resolution_data)
            elif resolution_type == "cancellation":
                await self._apply_cancellation(conflict, resolution_data)
            else:
                raise ValidationError(f"Unknown resolution type: {resolution_type}")
            
            # Mark conflict as resolved
            await self._update(self._conflicts_collection, {"conflict_id": conflict_id}, {"$set": {"status": "resolved"}})
            
            return True
            
        except Exception as e:
            logger.error(f"Error resolving conflict {conflict_id}: {str(e)}")
            raise DatabaseError(f"Failed to resolve conflict: {str(e)}")
    
    # Occurrence Management
    
    async def create_occurrence(self, entry_id: str, occurrence_date: date, **data) -> TimetableEntryOccurrence:
        """Create a specific occurrence of a timetable entry."""
        try:
            # Get the original entry
            original_entry = await self.get_by_id(entry_id)
            if not original_entry:
                raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
            
            # Create occurrence data
            occurrence_data = {
                "occurrence_id": str(uuid4()),
                "entry_id": entry_id,
                "occurrence_date": occurrence_date,
                "start_time": original_entry.start_time,
                "end_time": original_entry.end_time,
                "status": "scheduled",
                "created_at": datetime.utcnow(),
                **data
            }
            
            # Insert occurrence
            result = await self._insert(self._occurrences_collection, occurrence_data)
            if result.inserted_id:
                return TimetableEntryOccurrence(**occurrence_data)
            else:
                raise DatabaseError("Failed to create occurrence")
                
        except Exception as e:
            logger.error(f"Error creating occurrence for entry {entry_id}: {str(e)}")
            raise DatabaseError(f"Failed to create occurrence: {str(e)}")
    
    async def get_occurrences(self, entry_id: str, start_date: date = None, end_date: date = None, 
                             status: str = None, skip: int = 0, limit: int = 100) -> List[TimetableEntryOccurrence]:
        """Get occurrences for a timetable entry."""
        try:
            query_filter = {"entry_id": entry_id}
            
            if start_date:
                query_filter["occurrence_date"] = {"$gte": start_date}
            if end_date:
                query_filter["occurrence_date"]["$lte"] = end_date
            if status:
                query_filter["status"] = status
            
            result = await self._find_many(
                self._occurrences_collection,
                query_filter,
                skip=skip,
                limit=limit,
                sort=[("occurrence_date", 1)]
            )
            
            return [TimetableEntryOccurrence(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting occurrences for entry {entry_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch occurrences: {str(e)}")
    
    async def cancel_occurrence(self, entry_id: str, occurrence_date: date, 
                               cancelled_by_id: str = None, cancellation_reason: str = None) -> bool:
        """Cancel a specific occurrence."""
        try:
            result = await self._update(
                self._occurrences_collection,
                {"entry_id": entry_id, "occurrence_date": occurrence_date},
                {
                    "$set": {
                        "status": "cancelled",
                        "cancelled_at": datetime.utcnow(),
                        "cancelled_by_id": cancelled_by_id,
                        "cancellation_reason": cancellation_reason
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error cancelling occurrence for entry {entry_id}: {str(e)}")
            raise DatabaseError(f"Failed to cancel occurrence: {str(e)}")
    
    # Resource Allocation
    
    async def allocate_resources(self, entry_id: str, allocation_date: date, 
                               allocated_resources: Dict[str, Any], allocation_reason: str = None,
                               priority: int = 1, metadata: Dict[str, Any] = None,
                               allocated_by_id: str = None) -> ResourceAllocationResponse:
        """Allocate resources to a timetable entry."""
        try:
            # Get the entry to allocate for
            entry = await self.get_by_id(entry_id)
            if not entry:
                raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
            
            # Create allocation data
            allocation_data = {
                "allocation_id": str(uuid4()),
                "entry_id": entry_id,
                "allocation_date": allocation_date,
                "allocated_resources": allocated_resources,
                "allocation_status": "pending",
                "allocation_reason": allocation_reason,
                "priority": priority,
                "allocated_by_id": allocated_by_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                **(metadata or {})
            }
            
            # Insert allocation
            result = await self._insert(self._allocations_collection, allocation_data)
            if result.inserted_id:
                return ResourceAllocationResponse(**allocation_data)
            else:
                raise DatabaseError("Failed to create resource allocation")
                
        except Exception as e:
            logger.error(f"Error allocating resources for entry {entry_id}: {str(e)}")
            raise DatabaseError(f"Failed to allocate resources: {str(e)}")
    
    async def confirm_allocation(self, entry_id: str, allocation_id: str, 
                               confirmed_by_id: str = None, confirmation_notes: str = None) -> bool:
        """Confirm a resource allocation."""
        try:
            result = await self._update(
                self._allocations_collection,
                {"entry_id": entry_id, "allocation_id": allocation_id},
                {
                    "$set": {
                        "allocation_status": "confirmed",
                        "confirmed_at": datetime.utcnow(),
                        "confirmed_by_id": confirmed_by_id,
                        "confirmation_notes": confirmation_notes,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error confirming allocation for entry {entry_id}: {str(e)}")
            raise DatabaseError(f"Failed to confirm allocation: {str(e)}")
    
    # Analytics and Reporting
    
    async def get_entry_analytics(self, entry_id: str, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get analytics for a timetable entry."""
        try:
            # Get the entry
            entry = await self.get_by_id(entry_id)
            if not entry:
                raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
            
            # Get occurrences for the date range
            occurrences = await self.get_occurrences(entry_id, start_date, end_date)
            
            # Calculate analytics
            analytics = {
                "entry_id": entry_id,
                "entry_details": {
                    "timetable_id": entry.timetable_id,
                    "subject_id": entry.subject_id,
                    "class_id": entry.class_id,
                    "teacher_id": entry.teacher_id,
                    "room_id": entry.room_id,
                    "day_of_week": entry.day_of_week,
                    "start_time": entry.start_time,
                    "end_time": entry.end_time,
                    "duration_minutes": await self.get_entry_duration(entry_id)
                },
                "occurrence_stats": {
                    "total_occurrences": len(occurrences),
                    "scheduled_occurrences": len([o for o in occurrences if o.status == "scheduled"]),
                    "completed_occurrences": len([o for o in occurrences if o.status == "completed"]),
                    "cancelled_occurrences": len([o for o in occurrences if o.status == "cancelled"]),
                    "attendance_rate": self._calculate_attendance_rate(occurrences)
                },
                "resource_utilization": {
                    "total_allocations": len(await self.get_allocations(entry_id)),
                    "confirmed_allocations": len([a for a in await self.get_allocations(entry_id) if a.allocation_status == "confirmed"]),
                    "utilization_rate": await self.calculate_utilization_rate(entry_id)
                },
                "conflict_stats": {
                    "total_conflicts": len(await self.get_entry_conflicts(entry_id)),
                    "resolved_conflicts": len([c for c in await self.get_entry_conflicts(entry_id) if c.status == "resolved"]),
                    "pending_conflicts": len([c for c in await self.get_entry_conflicts(entry_id) if c.status == "pending"])
                },
                "performance_metrics": {
                    "punctuality_rate": await self.calculate_punctuality_rate(entry_id),
                    "consistency_score": await self.calculate_consistency_score(entry_id)
                }
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting analytics for entry {entry_id}: {str(e)}")
            raise DatabaseError(f"Failed to get entry analytics: {str(e)}")
    
    # Utility Methods
    
    async def validate_teacher(self, teacher_id: str) -> bool:
        """Validate that a teacher exists."""
        try:
            teacher = await self._find_one("teachers", {"teacher_id": teacher_id}, limit=1)
            return teacher is not None
        except Exception:
            return False
    
    async def validate_room(self, room_id: str) -> bool:
        """Validate that a room exists."""
        try:
            room = await self._find_one("rooms", {"room_id": room_id}, limit=1)
            return room is not None
        except Exception:
            return False
    
    async def validate_class(self, class_id: str) -> bool:
        """Validate that a class exists."""
        try:
            class_obj = await self._find_one("classes", {"class_id": class_id}, limit=1)
            return class_obj is not None
        except Exception:
            return False
    
    async def validate_subject(self, subject_id: str) -> bool:
        """Validate that a subject exists."""
        try:
            subject = await self._find_one("subjects", {"subject_id": subject_id}, limit=1)
            return subject is not None
        except Exception:
            return False
    
    async def get_entry_duration(self, entry_id: str) -> int:
        """Get the duration of a timetable entry in minutes."""
        try:
            entry = await self.get_by_id(entry_id)
            if not entry:
                return 0
            
            start_time = entry.start_time
            end_time = entry.end_time
            
            # Convert to minutes and calculate difference
            start_minutes = start_time.hour * 60 + start_time.minute
            end_minutes = end_time.hour * 60 + end_time.minute
            
            return end_minutes - start_minutes
            
        except Exception:
            return 0
    
    async def has_entry_conflict(self, entry_id: str) -> bool:
        """Check if an entry has conflicts."""
        try:
            conflicts = await self.get_entry_conflicts(entry_id)
            return len(conflicts) > 0
        except Exception:
            return False
    
    async def is_entry_allocated(self, entry_id: str) -> bool:
        """Check if an entry has confirmed allocations."""
        try:
            allocations = await self.get_allocations(entry_id)
            return any(a.allocation_status == "confirmed" for a in allocations)
        except Exception:
            return False
    
    async def get_resource_utilization(self, entry_id: str) -> float:
        """Calculate resource utilization rate for an entry."""
        try:
            allocations = await self.get_allocations(entry_id)
            if not allocations:
                return 0.0
            
            confirmed_count = len([a for a in allocations if a.allocation_status == "confirmed"])
            return confirmed_count / len(allocations) * 100
            
        except Exception:
            return 0.0
    
    async def get_scheduled_dates(self, entry_id: str) -> List[date]:
        """Get all scheduled dates for a recurring entry."""
        try:
            occurrences = await self.get_occurrences(entry_id, status="scheduled")
            return [occ.occurrence_date for occ in occurrences]
        except Exception:
            return []
    
    async def get_next_occurrence(self, entry_id: str) -> Optional[date]:
        """Get the next occurrence date for an entry."""
        try:
            occurrences = await self.get_occurrences(entry_id, status="scheduled")
            if occurrences:
                next_occurrence = min(occ.occurrence_date for occ in occurrences)
                return next_occurrence
            return None
        except Exception:
            return None
    
    async def get_occurrence_count(self, entry_id: str) -> int:
        """Get total occurrence count for an entry."""
        try:
            occurrences = await self.get_occurrences(entry_id)
            return len(occurrences)
        except Exception:
            return 0
    
    async def get_cancellation_count(self, entry_id: str) -> int:
        """Get cancellation count for an entry."""
        try:
            occurrences = await self.get_occurrences(entry_id, status="cancelled")
            return len(occurrences)
        except Exception:
            return 0
    
    # Helper Methods
    
    async def _validate_entry_data(self, data: Dict[str, Any]) -> None:
        """Validate timetable entry data."""
        required_fields = ['timetable_id', 'day_of_week', 'start_time', 'end_time', 'class_id', 'subject_id', 'teacher_id', 'room_id', 'building_id']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate time format and range
        if 'start_time' in data and 'end_time' in data:
            start_time = data['start_time']
            end_time = data['end_time']
            
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, "%H:%M").time()
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, "%H:%M").time()
            
            if end_time <= start_time:
                raise ValidationError("End time must be after start time")
        
        # Validate frequency
        if 'frequency' in data and data['frequency']:
            if data['frequency'] < 1 or data['frequency'] > 52:
                raise ValidationError("Frequency must be between 1 and 52")
        
        # Validate priority
        if 'priority' in data and data['priority']:
            if data['priority'] < 1 or data['priority'] > 5:
                raise ValidationError("Priority must be between 1 and 5")
    
    def _times_overlap(self, start1: time, end1: time, start2: time, end2: time) -> bool:
        """Check if two time ranges overlap."""
        return (start1 < end2) and (start2 < end1)
    
    def _determine_conflict_type(self, existing_entry: Dict[str, Any], new_entry: Dict[str, Any]) -> str:
        """Determine the type of conflict between two entries."""
        if existing_entry['teacher_id'] == new_entry['teacher_id']:
            return "teacher_conflict"
        elif existing_entry['room_id'] == new_entry['room_id']:
            return "room_conflict"
        elif existing_entry['class_id'] == new_entry['class_id']:
            return "class_conflict"
        else:
            return "resource_conflict"
    
    def _generate_conflict_message(self, conflicts: List[Dict[str, Any]]) -> str:
        """Generate a human-readable conflict message."""
        if not conflicts:
            return "No conflicts"
        
        message_parts = []
        for conflict in conflicts:
            conflict_type = conflict['conflict_type']
            if conflict_type == "teacher_conflict":
                message_parts.append("Teacher scheduling conflict")
            elif conflict_type == "room_conflict":
                message_parts.append("Room booking conflict")
            elif conflict_type == "class_conflict":
                message_parts.append("Class scheduling conflict")
            else:
                message_parts.append("Resource conflict")
        
        return "; ".join(message_parts)
    
    def _calculate_attendance_rate(self, occurrences: List[Dict[str, Any]]) -> float:
        """Calculate attendance rate for occurrences."""
        if not occurrences:
            return 0.0
        
        attended_count = len([o for o in occurrences if o.get('is_attended', False)])
        return attended_count / len(occurrences) * 100
    
    def _calculate_utilization_rate(self, entry_id: str) -> float:
        """Calculate resource utilization rate."""
        # This would need to be implemented based on specific business logic
        return 0.0
    
    def _calculate_punctuality_rate(self, entry_id: str) -> float:
        """Calculate punctuality rate."""
        # This would need to be implemented based on specific business logic
        return 0.0
    
    def _calculate_consistency_score(self, entry_id: str) -> float:
        """Calculate consistency score."""
        # This would need to be implemented based on specific business logic
        return 0.0
    
    async def get_allocations(self, entry_id: str) -> List[ResourceAllocation]:
        """Get all resource allocations for an entry."""
        try:
            result = await self._find_many(self._allocations_collection, {"entry_id": entry_id})
            return [ResourceAllocation(**item) for item in result]
        except Exception:
            return []
    
    async def get_entry_conflicts(self, entry_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get conflicts for a timetable entry."""
        try:
            result = await self._find_many(
                self._conflicts_collection,
                {"entry_id": entry_id},
                skip=skip,
                limit=limit,
                sort=[("created_at", -1)]
            )
            return result
        except Exception:
            return []