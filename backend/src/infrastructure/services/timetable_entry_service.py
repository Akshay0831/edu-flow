"""
Timetable Entry Management Service

This module provides business logic for timetable entry management:
- Timetable entry creation and management
- Scheduling and resource allocation
- Conflict detection and resolution
- Occurrence management
- Analytics and reporting
- Resource optimization

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, time, timedelta
from uuid import uuid4

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.core.logging import get_logger
from src.core.base_service import BaseService
from src.infrastructure.repositories.timetable_entry_repository import TimetableEntryRepository
from src.models.timetable_entry import TimetableEntryCreate, TimetableEntryUpdate, TimetableEntryResponse, TimetableStats

logger = get_logger(__name__)


class TimetableEntryService(BaseService):
    """Timetable entry management service with comprehensive functionality."""
    
    def __init__(self, timetable_entry_repository: TimetableEntryRepository):
        super().__init__(timetable_entry_repository)
        self._cache = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the timetable entry service."""
        try:
            self._initialized = True
            logger.info("Timetable entry service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize timetable entry service: {str(e)}")
            raise
    
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized
    
    async def dispose(self) -> None:
        """Dispose the timetable entry service."""
        try:
            self._cache.clear()
            logger.info("Timetable entry service disposed successfully")
        except Exception as e:
            logger.error(f"Failed to dispose timetable entry service: {str(e)}")
            raise
    
    # Core Business Operations
    
    async def create_timetable_entry(self, entry_data: Dict[str, Any]) -> TimetableEntryResponse:
        """Create a new timetable entry with business logic validation."""
        try:
            # Validate timetable entry data
            await self._validate_entry_creation(entry_data)
            
            # Check for conflicts
            if await self._check_entry_conflicts(entry_data):
                raise ConflictError("Timetable entry conflicts with existing schedules")
            
            # Create timetable entry
            entry = await self.timetable_entry_repository.create(**entry_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return entry
            
        except Exception as e:
            logger.error(f"Failed to create timetable entry: {str(e)}")
            raise
    
    async def update_timetable_entry(self, entry_id: str, entry_data: Dict[str, Any]) -> Optional[TimetableEntryResponse]:
        """Update an existing timetable entry with business logic."""
        try:
            # Validate timetable entry exists
            entry = await self.timetable_entry_repository.get_by_id(entry_id)
            if not entry:
                raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
            
            # Validate update data
            await self._validate_entry_update(entry_data)
            
            # Check for conflicts if times are being updated
            if await self._should_check_conflicts(entry_data, entry):
                if await self._check_entry_conflicts(entry_data, entry_id):
                    raise ConflictError("Updated timetable entry conflicts with existing schedules")
            
            # Update timetable entry
            updated_entry = await self.timetable_entry_repository.update(entry_id, **entry_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return updated_entry
            
        except Exception as e:
            logger.error(f"Failed to update timetable entry {entry_id}: {str(e)}")
            raise
    
    async def get_timetable_entry(self, entry_id: str) -> Optional[TimetableEntryResponse]:
        """Get a timetable entry by ID with caching."""
        try:
            # Check cache first
            if entry_id in self._cache:
                return self._cache[entry_id]
            
            # Get timetable entry from repository
            entry = await self.timetable_entry_repository.get_by_id(entry_id)
            
            if entry:
                # Cache the result
                self._cache[entry_id] = entry
            
            return entry
            
        except Exception as e:
            logger.error(f"Failed to get timetable entry {entry_id}: {str(e)}")
            raise
    
    async def delete_timetable_entry(self, entry_id: str) -> bool:
        """Delete a timetable entry with business logic."""
        try:
            # Validate timetable entry exists
            entry = await self.timetable_entry_repository.get_by_id(entry_id)
            if not entry:
                raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
            
            # Check if entry has associated resources
            if await self._has_associated_resources(entry_id):
                raise ValidationError("Cannot delete timetable entry that has allocated resources")
            
            # Check if entry has future occurrences
            if await self._has_future_occurrences(entry_id):
                raise ValidationError("Cannot delete timetable entry with future occurrences")
            
            # Delete timetable entry
            result = await self.timetable_entry_repository.delete(entry_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            # Release resources
            await self._release_entry_resources(entry_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete timetable entry {entry_id}: {str(e)}")
            raise
    
    # Search and Filtering
    
    async def search_timetable_entries(self, search_term: str, skip: int = 0, limit: int = 100) -> List[TimetableEntryResponse]:
        """Search for timetable entries by class name, subject, or teacher."""
        try:
            entries = await self.timetable_entry_repository.search_entries(
                search_term=search_term,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for entry in entries:
                self._cache[entry.id] = entry
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to search timetable entries: {str(e)}")
            raise
    
    async def get_entries_by_class(self, class_id: str, skip: int = 0, limit: int = 100) -> List[TimetableEntryResponse]:
        """Get timetable entries for a class."""
        try:
            entries = await self.timetable_entry_repository.get_by_class(
                class_id=class_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for entry in entries:
                self._cache[entry.id] = entry
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to get entries for class {class_id}: {str(e)}")
            raise
    
    async def get_entries_by_teacher(self, teacher_id: str, skip: int = 0, limit: int = 100) -> List[TimetableEntryResponse]:
        """Get timetable entries for a teacher."""
        try:
            entries = await self.timetable_entry_repository.get_by_teacher(
                teacher_id=teacher_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for entry in entries:
                self._cache[entry.id] = entry
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to get entries for teacher {teacher_id}: {str(e)}")
            raise
    
    async def get_entries_by_room(self, room_id: str, skip: int = 0, limit: int = 100) -> List[TimetableEntryResponse]:
        """Get timetable entries for a room."""
        try:
            entries = await self.timetable_entry_repository.get_by_room(
                room_id=room_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for entry in entries:
                self._cache[entry.id] = entry
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to get entries for room {room_id}: {str(e)}")
            raise
    
    async def get_entries_by_date_range(self, start_date: date, end_date: date, skip: int = 0, limit: int = 100) -> List[TimetableEntryResponse]:
        """Get timetable entries within a date range."""
        try:
            entries = await self.timetable_entry_repository.get_by_date_range(
                start_date=start_date,
                end_date=end_date,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for entry in entries:
                self._cache[entry.id] = entry
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to get entries for date range: {str(e)}")
            raise
    
    async def get_entries_by_day_of_week(self, day_of_week: str, skip: int = 0, limit: int = 100) -> List[TimetableEntryResponse]:
        """Get timetable entries for a specific day of week."""
        try:
            entries = await self.timetable_entry_repository.get_by_day_of_week(
                day_of_week=day_of_week,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for entry in entries:
                self._cache[entry.id] = entry
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to get entries for day {day_of_week}: {str(e)}")
            raise
    
    # Scheduling and Resource Management
    
    async def schedule_recurring_entry(self, entry_data: Dict[str, Any], recurrence_data: Dict[str, Any]) -> List[TimetableEntryResponse]:
        """Schedule a recurring timetable entry."""
        try:
            # Validate entry data
            await self._validate_entry_creation(entry_data)
            
            # Validate recurrence data
            await self._validate_recurrence_data(recurrence_data)
            
            # Generate recurring entries
            recurring_entries = []
            start_date = datetime.strptime(entry_data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(entry_data['end_date'], '%Y-%m-%d').date()
            recurrence_pattern = recurrence_data['pattern']
            
            current_date = start_date
            while current_date <= end_date:
                if self._should_include_date(current_date, recurrence_data):
                    # Create entry for this date
                    entry_copy = entry_data.copy()
                    entry_copy['start_date'] = current_date.strftime('%Y-%m-%d')
                    entry_copy['end_date'] = current_date.strftime('%Y-%m-%d')
                    
                    # Check for conflicts
                    if not await self._check_entry_conflicts(entry_copy):
                        entry = await self.timetable_entry_repository.create(**entry_copy)
                        recurring_entries.append(entry)
                
                # Move to next occurrence
                current_date = self._get_next_date(current_date, recurrence_pattern)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return recurring_entries
            
        except Exception as e:
            logger.error(f"Failed to schedule recurring entry: {str(e)}")
            raise
    
    async def reschedule_entry(self, entry_id: str, new_start_date: date, new_end_date: date) -> bool:
        """Reschedule a timetable entry."""
        try:
            # Validate entry exists
            entry = await self.timetable_entry_repository.get_by_id(entry_id)
            if not entry:
                raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
            
            # Validate new dates
            await self._validate_reschedule_dates(entry, new_start_date, new_end_date)
            
            # Check for conflicts
            if await self._check_reschedule_conflicts(entry_id, new_start_date, new_end_date):
                raise ConflictError("New schedule conflicts with existing entries")
            
            # Reschedule entry
            result = await self.timetable_entry_repository.reschedule_entry(
                entry_id=entry_id,
                new_start_date=new_start_date,
                new_end_date=new_end_date
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to reschedule entry {entry_id}: {str(e)}")
            raise
    
    async def allocate_resources(self, entry_id: str, resource_data: Dict[str, Any]) -> bool:
        """Allocate resources to a timetable entry."""
        try:
            # Validate entry exists
            entry = await self.timetable_entry_repository.get_by_id(entry_id)
            if not entry:
                raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
            
            # Validate resource data
            await self._validate_resource_data(resource_data)
            
            # Check resource availability
            if not await self._check_resource_availability(entry, resource_data):
                raise ConflictError("Requested resources are not available")
            
            # Allocate resources
            result = await self.timetable_entry_repository.allocate_resources(
                entry_id=entry_id,
                **resource_data
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to allocate resources for entry {entry_id}: {str(e)}")
            raise
    
    async def release_resources(self, entry_id: str) -> bool:
        """Release resources from a timetable entry."""
        try:
            # Validate entry exists
            entry = await self.timetable_entry_repository.get_by_id(entry_id)
            if not entry:
                raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
            
            # Release resources
            result = await self.timetable_entry_repository.release_resources(entry_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to release resources for entry {entry_id}: {str(e)}")
            raise
    
    # Occurrence Management
    
    async def create_occurrence(self, entry_id: str, occurrence_date: date) -> bool:
        """Create a specific occurrence of a timetable entry."""
        try:
            # Validate entry exists
            entry = await self.timetable_entry_repository.get_by_id(entry_id)
            if not entry:
                raise NotFoundError(f"Timetable entry not found with ID: {entry_id}")
            
            # Validate occurrence date
            await self._validate_occurrence_date(entry, occurrence_date)
            
            # Create occurrence
            result = await self.timetable_entry_repository.create_occurrence(
                entry_id=entry_id,
                occurrence_date=occurrence_date
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create occurrence for entry {entry_id}: {str(e)}")
            raise
    
    async def update_occurrence_status(self, occurrence_id: str, status: str, notes: str = None) -> bool:
        """Update occurrence status."""
        try:
            # Validate status
            valid_statuses = ['scheduled', 'completed', 'cancelled', 'postponed']
            if status not in valid_statuses:
                raise ValidationError(f"Invalid status: {status}")
            
            # Update occurrence
            result = await self.timetable_entry_repository.update_occurrence_status(
                occurrence_id=occurrence_id,
                status=status,
                notes=notes
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update occurrence status for {occurrence_id}: {str(e)}")
            raise
    
    async def get_occurrences_by_date(self, occurrence_date: date, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all occurrences for a specific date."""
        try:
            return await self.timetable_entry_repository.get_occurrences_by_date(
                occurrence_date=occurrence_date,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get occurrences for date {occurrence_date}: {str(e)}")
            raise
    
    # Analytics and Reporting
    
    async def get_timetable_stats(self, class_id: str = None, teacher_id: str = None, 
                                 room_id: str = None, start_date: date = None, 
                                 end_date: date = None) -> TimetableStats:
        """Get comprehensive timetable statistics."""
        try:
            # Get timetable entries based on filters
            entries = await self.get_entries_by_date_range(start_date or date.min, end_date or date.max, 0, 1000)
            
            if class_id:
                entries = [e for e in entries if e.class_id == class_id]
            if teacher_id:
                entries = [e for e in entries if e.teacher_id == teacher_id]
            if room_id:
                entries = [e for e in entries if e.room_id == room_id]
            
            if not entries:
                raise NotFoundError("No timetable entries found for specified criteria")
            
            # Calculate statistics
            total_sessions = len(entries)
            completed_sessions = len([e for e in entries if e.status == 'completed'])
            scheduled_sessions = len([e for e in entries if e.status == 'scheduled'])
            cancelled_sessions = len([e for e in entries if e.status == 'cancelled'])
            
            # Calculate time utilization
            total_hours = sum(self._calculate_session_duration(e) for e in entries)
            average_session_duration = total_hours / total_sessions if total_sessions > 0 else 0
            
            # Resource utilization
            room_utilization = self._calculate_room_utilization(entries)
            teacher_utilization = self._calculate_teacher_utilization(entries)
            
            # Create stats object
            stats = TimetableStats(
                total_sessions=total_sessions,
                completed_sessions=completed_sessions,
                scheduled_sessions=scheduled_sessions,
                cancelled_sessions=cancelled_sessions,
                completion_rate=round((completed_sessions / total_sessions) * 100, 2) if total_sessions > 0 else 0,
                total_hours=round(total_hours, 2),
                average_session_duration=round(average_session_duration, 2),
                room_utilization=room_utilization,
                teacher_utilization=teacher_utilization,
                last_updated=datetime.utcnow().isoformat()
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get timetable stats: {str(e)}")
            raise
    
    async def generate_timetable_report(self, report_type: str = "overview", 
                                     class_id: str = None, teacher_id: str = None, 
                                     room_id: str = None, start_date: date = None, 
                                     end_date: date = None) -> Dict[str, Any]:
        """Generate comprehensive timetable report."""
        try:
            # Generate report based on type
            if report_type == "overview":
                return await self._generate_overview_report(class_id, teacher_id, room_id, start_date, end_date)
            elif report_type == "conflicts":
                return await self._generate_conflicts_report(class_id, teacher_id, room_id, start_date, end_date)
            elif report_type == "utilization":
                return await self._generate_utilization_report(class_id, teacher_id, room_id, start_date, end_date)
            elif report_type == "attendance":
                return await self._generate_attendance_report(class_id, teacher_id, room_id, start_date, end_date)
            else:
                raise ValidationError(f"Unknown report type: {report_type}")
                
        except Exception as e:
            logger.error(f"Failed to generate timetable report: {str(e)}")
            raise
    
    # Batch Operations
    
    async def batch_update_entries(self, updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple timetable entries."""
        results = {}
        
        for update in updates:
            entry_id = update['entry_id']
            try:
                result = await self.update_timetable_entry(entry_id, update)
                results[entry_id] = result is not None
            except Exception as e:
                logger.error(f"Failed to update entry {entry_id}: {str(e)}")
                results[entry_id] = False
        
        return results
    
    async def batch_delete_entries(self, entry_ids: List[str]) -> Dict[str, bool]:
        """Delete multiple timetable entries."""
        results = {}
        
        for entry_id in entry_ids:
            try:
                result = await self.delete_timetable_entry(entry_id)
                results[entry_id] = result
            except Exception as e:
                logger.error(f"Failed to delete entry {entry_id}: {str(e)}")
                results[entry_id] = False
        
        return results
    
    async def batch_allocate_resources(self, allocations: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Allocate resources to multiple timetable entries."""
        results = {}
        
        for allocation in allocations:
            entry_id = allocation['entry_id']
            try:
                result = await self.allocate_resources(entry_id, allocation)
                results[entry_id] = result
            except Exception as e:
                logger.error(f"Failed to allocate resources for entry {entry_id}: {str(e)}")
                results[entry_id] = False
        
        return results
    
    # Helper Methods
    
    async def _validate_entry_creation(self, data: Dict[str, Any]) -> None:
        """Validate timetable entry creation data."""
        required_fields = ['class_id', 'teacher_id', 'subject_id', 'room_id', 'start_date', 'end_date', 'start_time', 'end_time']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate date and time formats
        await self._validate_datetime_fields(data)
        
        # Validate class exists
        from src.infrastructure.repositories.class_repository import ClassRepository
        class_repo = ClassRepository()
        class_obj = await class_repo.get_by_id(data['class_id'])
        if not class_obj:
            raise NotFoundError(f"Class not found with ID: {data['class_id']}")
        
        # Validate teacher exists
        from src.infrastructure.repositories.teacher_repository import TeacherRepository
        teacher_repo = TeacherRepository()
        teacher = await teacher_repo.get_by_id(data['teacher_id'])
        if not teacher:
            raise NotFoundError(f"Teacher not found with ID: {data['teacher_id']}")
        
        # Validate subject exists
        from src.infrastructure.repositories.subject_repository import SubjectRepository
        subject_repo = SubjectRepository()
        subject = await subject_repo.get_by_id(data['subject_id'])
        if not subject:
            raise NotFoundError(f"Subject not found with ID: {data['subject_id']}")
        
        # Validate room exists
        from src.infrastructure.repositories.room_repository import RoomRepository
        room_repo = RoomRepository()
        room = await room_repo.get_by_id(data['room_id'])
        if not room:
            raise NotFoundError(f"Room not found with ID: {data['room_id']}")
    
    async def _validate_entry_update(self, data: Dict[str, Any]) -> None:
        """Validate timetable entry update data."""
        allowed_fields = ['start_date', 'end_date', 'start_time', 'end_time', 'status', 'notes', 'room_id']
        
        for field in data.keys():
            if field not in allowed_fields:
                raise ValidationError(f"Cannot update field: {field}")
        
        # Validate datetime fields if provided
        if any(field in data for field in ['start_date', 'end_date', 'start_time', 'end_time']):
            await self._validate_datetime_fields(data)
    
    async def _validate_datetime_fields(self, data: Dict[str, Any]) -> None:
        """Validate date and time fields."""
        if 'start_date' in data and data['start_date']:
            try:
                datetime.strptime(data['start_date'], '%Y-%m-%d')
            except ValueError:
                raise ValidationError("Invalid start date format")
        
        if 'end_date' in data and data['end_date']:
            try:
                datetime.strptime(data['end_date'], '%Y-%m-%d')
            except ValueError:
                raise ValidationError("Invalid end date format")
        
        if 'start_time' in data and data['start_time']:
            try:
                datetime.strptime(data['start_time'], '%H:%M')
            except ValueError:
                raise ValidationError("Invalid start time format")
        
        if 'end_time' in data and data['end_time']:
            try:
                datetime.strptime(data['end_time'], '%H:%M')
            except ValueError:
                raise ValidationError("Invalid end time format")
    
    async def _validate_reschedule_dates(self, entry: TimetableEntryResponse, new_start_date: date, new_end_date: date) -> None:
        """Validate reschedule dates."""
        if new_start_date > new_end_date:
            raise ValidationError("Start date cannot be after end date")
        
        # Check if dates are in the future
        if new_start_date < date.today():
            raise ValidationError("Start date cannot be in the past")
    
    async def _validate_recurrence_data(self, data: Dict[str, Any]) -> None:
        """Validate recurrence data."""
        required_fields = ['pattern', 'end_date']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required recurrence field '{field}' is missing or empty")
        
        # Validate pattern
        valid_patterns = ['daily', 'weekly', 'monthly', 'custom']
        if data['pattern'] not in valid_patterns:
            raise ValidationError(f"Invalid recurrence pattern: {data['pattern']}")
        
        # Validate end date
        try:
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            if end_date < date.today():
                raise ValidationError("Recurrence end date cannot be in the past")
        except ValueError:
            raise ValidationError("Invalid recurrence end date format")
    
    async def _validate_resource_data(self, data: Dict[str, Any]) -> None:
        """Validate resource data."""
        if not data:
            raise ValidationError("Resource data is required")
        
        # Validate room if provided
        if 'room_id' in data and data['room_id']:
            from src.infrastructure.repositories.room_repository import RoomRepository
            room_repo = RoomRepository()
            room = await room_repo.get_by_id(data['room_id'])
            if not room:
                raise NotFoundError(f"Room not found with ID: {data['room_id']}")
        
        # Validate equipment if provided
        if 'equipment' in data and data['equipment']:
            if not isinstance(data['equipment'], list):
                raise ValidationError("Equipment must be a list")
    
    async def _validate_occurrence_date(self, entry: TimetableEntryResponse, occurrence_date: date) -> None:
        """Validate occurrence date."""
        entry_start = datetime.strptime(entry.start_date, '%Y-%m-%d').date()
        entry_end = datetime.strptime(entry.end_date, '%Y-%m-%d').date()
        
        if occurrence_date < entry_start or occurrence_date > entry_end:
            raise ValidationError("Occurrence date must be within the entry date range")
    
    def _should_check_conflicts(self, entry_data: Dict[str, Any], existing_entry: TimetableEntryResponse) -> bool:
        """Determine if conflict checking is needed."""
        # Check if time-related fields are being updated
        time_fields = ['start_date', 'end_date', 'start_time', 'end_time', 'room_id']
        return any(field in entry_data for field in time_fields)
    
    async def _check_entry_conflicts(self, entry_data: Dict[str, Any], exclude_entry_id: str = None) -> bool:
        """Check for timetable entry conflicts."""
        # This would implement conflict detection logic
        # For now, return False (should be implemented)
        return False
    
    async def _check_reschedule_conflicts(self, entry_id: str, new_start_date: date, new_end_date: date) -> bool:
        """Check for reschedule conflicts."""
        # This would implement reschedule conflict logic
        # For now, return False (should be implemented)
        return False
    
    def _calculate_session_duration(self, entry: TimetableEntryResponse) -> float:
        """Calculate session duration in hours."""
        start_time = datetime.strptime(entry.start_time, '%H:%M')
        end_time = datetime.strptime(entry.end_time, '%H:%M')
        
        duration = end_time - start_time
        return duration.total_seconds() / 3600
    
    def _calculate_room_utilization(self, entries: List[TimetableEntryResponse]) -> float:
        """Calculate room utilization rate."""
        if not entries:
            return 0.0
        
        total_possible_hours = len(entries) * 8  # Assuming 8-hour workday
        actual_hours = sum(self._calculate_session_duration(e) for e in entries)
        
        return round((actual_hours / total_possible_hours) * 100, 2)
    
    def _calculate_teacher_utilization(self, entries: List[TimetableEntryResponse]) -> float:
        """Calculate teacher utilization rate."""
        if not entries:
            return 0.0
        
        unique_teachers = len(set(e.teacher_id for e in entries))
        if unique_teachers == 0:
            return 0.0
        
        total_possible_hours = unique_teachers * 8  # Assuming 8-hour workday
        actual_hours = sum(self._calculate_session_duration(e) for e in entries)
        
        return round((actual_hours / total_possible_hours) * 100, 2)
    
    def _should_include_date(self, current_date: date, recurrence_data: Dict[str, Any]) -> bool:
        """Check if date should be included in recurrence."""
        pattern = recurrence_data['pattern']
        
        if pattern == 'daily':
            return True
        elif pattern == 'weekly':
            day_of_week = recurrence_data.get('day_of_week', current_date.strftime('%A'))
            return current_date.strftime('%A') == day_of_week
        elif pattern == 'monthly':
            day_of_month = recurrence_data.get('day_of_month', current_date.day)
            return current_date.day == day_of_month
        elif pattern == 'custom':
            # Custom pattern logic would be implemented here
            return True
        
        return False
    
    def _get_next_date(self, current_date: date, pattern: str) -> date:
        """Get next date based on recurrence pattern."""
        if pattern == 'daily':
            return current_date + timedelta(days=1)
        elif pattern == 'weekly':
            return current_date + timedelta(weeks=1)
        elif pattern == 'monthly':
            # Approximate monthly by adding 30 days
            return current_date + timedelta(days=30)
        else:
            return current_date + timedelta(days=1)
    
    async def _has_associated_resources(self, entry_id: str) -> bool:
        """Check if timetable entry has associated resources."""
        # This would check if entry has allocated equipment, materials, etc.
        # For now, return False (should be implemented)
        return False
    
    async def _has_future_occurrences(self, entry_id: str) -> bool:
        """Check if timetable entry has future occurrences."""
        # This would check for future scheduled occurrences
        # For now, return False (should be implemented)
        return False
    
    async def _release_entry_resources(self, entry_id: str) -> None:
        """Release resources from a timetable entry."""
        try:
            # This would release all allocated resources
            # For now, just log the operation
            logger.info(f"Releasing resources for entry {entry_id}")
            
        except Exception as e:
            logger.error(f"Failed to release resources for entry {entry_id}: {str(e)}")
            raise
    
    async def _check_resource_availability(self, entry: TimetableEntryResponse, resource_data: Dict[str, Any]) -> bool:
        """Check resource availability for a timetable entry."""
        # This would implement resource availability checking
        # For now, return True (should be implemented)
        return True
    
    async def _generate_overview_report(self, class_id: str, teacher_id: str, room_id: str, 
                                     start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate overview report for timetable."""
        try:
            # Get entries
            entries = await self.get_entries_by_date_range(start_date, end_date, 0, 1000)
            
            if class_id:
                entries = [e for e in entries if e.class_id == class_id]
            if teacher_id:
                entries = [e for e in entries if e.teacher_id == teacher_id]
            if room_id:
                entries = [e for e in entries if e.room_id == room_id]
            
            # Calculate summary statistics
            total_sessions = len(entries)
            completed_sessions = len([e for e in entries if e.status == 'completed'])
            scheduled_sessions = len([e for e in entries if e.status == 'scheduled'])
            cancelled_sessions = len([e for e in entries if e.status == 'cancelled'])
            
            # Group by day of week
            by_day = {}
            for entry in entries:
                day = entry.start_date.strftime('%A')
                by_day[day] = by_day.get(day, 0) + 1
            
            return {
                "entries": entries,
                "summary": {
                    "total_sessions": total_sessions,
                    "completed_sessions": completed_sessions,
                    "scheduled_sessions": scheduled_sessions,
                    "cancelled_sessions": cancelled_sessions,
                    "completion_rate": round((completed_sessions / total_sessions) * 100, 2) if total_sessions > 0 else 0,
                    "by_day": by_day
                },
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "overview"
            }
        except Exception as e:
            logger.error(f"Failed to generate overview report: {str(e)}")
            raise
    
    async def _generate_conflicts_report(self, class_id: str, teacher_id: str, room_id: str, 
                                       start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate conflicts report for timetable."""
        try:
            # Get potential conflicts (this would be implemented in the repository)
            conflicts = await self.timetable_entry_repository.get_conflicts(
                class_id=class_id,
                teacher_id=teacher_id,
                room_id=room_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "conflicts": conflicts,
                "summary": {
                    "total_conflicts": len(conflicts),
                    "by_type": self._group_conflicts_by_type(conflicts),
                    "by_severity": self._group_conflicts_by_severity(conflicts)
                },
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "conflicts"
            }
        except Exception as e:
            logger.error(f"Failed to generate conflicts report: {str(e)}")
            raise
    
    async def _generate_utilization_report(self, class_id: str, teacher_id: str, room_id: str, 
                                         start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate utilization report for timetable."""
        try:
            # Get entries
            entries = await self.get_entries_by_date_range(start_date, end_date, 0, 1000)
            
            if class_id:
                entries = [e for e in entries if e.class_id == class_id]
            if teacher_id:
                entries = [e for e in entries if e.teacher_id == teacher_id]
            if room_id:
                entries = [e for e in entries if e.room_id == room_id]
            
            # Calculate utilization
            room_utilization = self._calculate_room_utilization(entries)
            teacher_utilization = self._calculate_teacher_utilization(entries)
            time_utilization = self._calculate_time_utilization(entries)
            
            return {
                "entries": entries,
                "utilization": {
                    "room_utilization": room_utilization,
                    "teacher_utilization": teacher_utilization,
                    "time_utilization": time_utilization,
                    "peak_hours": self._find_peak_hours(entries),
                    "utilization_by_day": self._calculate_utilization_by_day(entries)
                },
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "utilization"
            }
        except Exception as e:
            logger.error(f"Failed to generate utilization report: {str(e)}")
            raise
    
    async def _generate_attendance_report(self, class_id: str, teacher_id: str, room_id: str, 
                                        start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate attendance report for timetable."""
        try:
            # This would get attendance data for timetable entries
            # For now, return mock data
            attendance_data = {
                "total_sessions": 50,
                "attended_sessions": 45,
                "absent_sessions": 5,
                "attendance_rate": 90.0,
                "by_day": {}
            }
            
            return {
                "attendance_data": attendance_data,
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "attendance"
            }
        except Exception as e:
            logger.error(f"Failed to generate attendance report: {str(e)}")
            raise
    
    def _group_conflicts_by_type(self, conflicts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group conflicts by type."""
        by_type = {}
        for conflict in conflicts:
            conflict_type = conflict.get('type', 'Unknown')
            by_type[conflict_type] = by_type.get(conflict_type, 0) + 1
        return by_type
    
    def _group_conflicts_by_severity(self, conflicts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group conflicts by severity."""
        by_severity = {}
        for conflict in conflicts:
            severity = conflict.get('severity', 'Unknown')
            by_severity[severity] = by_severity.get(severity, 0) + 1
        return by_severity
    
    def _calculate_time_utilization(self, entries: List[TimetableEntryResponse]) -> float:
        """Calculate time utilization rate."""
        if not entries:
            return 0.0
        
        total_possible_hours = len(entries) * 8  # Assuming 8-hour workday
        actual_hours = sum(self._calculate_session_duration(e) for e in entries)
        
        return round((actual_hours / total_possible_hours) * 100, 2)
    
    def _find_peak_hours(self, entries: List[TimetableEntryResponse]) -> List[str]:
        """Find peak hours for timetable."""
        hour_counts = {}
        
        for entry in entries:
            start_time = datetime.strptime(entry.start_time, '%H:%M').hour
            hour_key = f"{start_time:02d}:00"
            hour_counts[hour_key] = hour_counts.get(hour_key, 0) + 1
        
        # Find top 3 peak hours
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]
    
    def _calculate_utilization_by_day(self, entries: List[TimetableEntryResponse]) -> Dict[str, float]:
        """Calculate utilization by day of week."""
        by_day = {}
        day_counts = {}
        
        for entry in entries:
            day = entry.start_date.strftime('%A')
            by_day[day] = by_day.get(day, 0) + self._calculate_session_duration(entry)
            day_counts[day] = day_counts.get(day, 0) + 1
        
        # Calculate utilization rate per day
        utilization = {}
        for day in by_day:
            if day_counts[day] > 0:
                utilization[day] = round((by_day[day] / (day_counts[day] * 8)) * 100, 2)
            else:
                utilization[day] = 0
        
        return utilization
    
    async def _invalidate_cache(self) -> None:
        """Invalidate timetable entry cache."""
        self._cache.clear()
    
    # Abstract method implementations required by BaseService
    
    async def create(self, data: Dict) -> Dict:
        """Create a new timetable entry entity."""
        timetable_entry = await self.create_timetable_entry(data)
        return timetable_entry.dict()
    
    async def get(self, id: str) -> Optional[Dict]:
        """Get a timetable entry entity by ID."""
        timetable_entry = await self.get_timetable_entry_by_id(id)
        return timetable_entry.dict() if timetable_entry else None
    
    async def update(self, id: str, data: Dict) -> Dict:
        """Update a timetable entry entity by ID."""
        timetable_entry = await self.update_timetable_entry(id, data)
        return timetable_entry.dict()
    
    async def delete(self, id: str) -> bool:
        """Delete a timetable entry entity by ID."""
        return await self.delete_timetable_entry(id)
    
    async def list(self, skip: int = 0, limit: int = 100, filters: Dict = None) -> List[Dict]:
        """List all timetable entry entities."""
        timetable_entries = await self.get_all_timetable_entries(skip=skip, limit=limit)
        return [timetable_entry.dict() for timetable_entry in timetable_entries]
    
    async def count(self, filters: Dict = None) -> int:
        """Count total number of timetable entry entities."""
        return await self.get_timetable_entry_count()
        self._cache.clear()