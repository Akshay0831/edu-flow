"""
Room Management Service

This module provides business logic for room management:
- Room booking and scheduling
- Room allocation and management
- Capacity management
- Waiting list management
- Resource optimization
- Analytics and reporting

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, time, timedelta
from uuid import uuid4
import statistics

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.core.logging import get_logger
from src.core.base_service import BaseService
from src.infrastructure.repositories.room_repository import RoomRepository
from src.models.room import RoomCreate, RoomUpdate, RoomResponse, RoomStats

logger = get_logger(__name__)


class RoomService(BaseService):
    """Room management service with comprehensive functionality."""
    
    def __init__(self, room_repository: RoomRepository):
        super().__init__(room_repository)
        self._cache = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the room service."""
        try:
            self._initialized = True
            logger.info("Room service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize room service: {str(e)}")
            raise
    
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized
    
    async def dispose(self) -> None:
        """Dispose the room service."""
        try:
            self._cache.clear()
            logger.info("Room service disposed successfully")
        except Exception as e:
            logger.error(f"Failed to dispose room service: {str(e)}")
            raise
    
    # Core Business Operations
    
    async def create_room(self, room_data: Dict[str, Any]) -> RoomResponse:
        """Create a new room with business logic validation."""
        try:
            # Validate room data
            await self._validate_room_creation(room_data)
            
            # Create room
            room = await self.room_repository.create(**room_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return room
            
        except Exception as e:
            logger.error(f"Failed to create room: {str(e)}")
            raise
    
    async def update_room(self, room_id: str, room_data: Dict[str, Any]) -> Optional[RoomResponse]:
        """Update an existing room with business logic."""
        try:
            # Validate room exists
            room = await self.room_repository.get_by_id(room_id)
            if not room:
                raise NotFoundError(f"Room not found with ID: {room_id}")
            
            # Validate update data
            await self._validate_room_update(room_data)
            
            # Check if name is being changed and conflicts exist
            if 'name' in room_data and room_data['name'] != room.name:
                existing_room = await self.room_repository.get_by_name(room_data['name'])
                if existing_room:
                    raise ConflictError(f"Room with name '{room_data['name']}' already exists")
            
            # Update room
            updated_room = await self.room_repository.update(room_id, **room_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return updated_room
            
        except Exception as e:
            logger.error(f"Failed to update room {room_id}: {str(e)}")
            raise
    
    async def get_room(self, room_id: str) -> Optional[RoomResponse]:
        """Get a room by ID with caching."""
        try:
            # Check cache first
            if room_id in self._cache:
                return self._cache[room_id]
            
            # Get room from repository
            room = await self.room_repository.get_by_id(room_id)
            
            if room:
                # Cache the result
                self._cache[room_id] = room
            
            return room
            
        except Exception as e:
            logger.error(f"Failed to get room {room_id}: {str(e)}")
            raise
    
    async def delete_room(self, room_id: str) -> bool:
        """Delete a room with business logic."""
        try:
            # Validate room exists
            room = await self.room_repository.get_by_id(room_id)
            if not room:
                raise NotFoundError(f"Room not found with ID: {room_id}")
            
            # Check if room has active bookings
            if await self._has_active_bookings(room_id):
                raise ValidationError("Cannot delete room with active bookings")
            
            # Check if room has waiting list entries
            if await self._has_waiting_list_entries(room_id):
                raise ValidationError("Cannot delete room with waiting list entries")
            
            # Check if room has been used recently
            if await self._was_recently_used(room_id):
                raise ValidationError("Cannot delete room that was recently used")
            
            # Delete room
            result = await self.room_repository.delete(room_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete room {room_id}: {str(e)}")
            raise
    
    # Search and Filtering
    
    async def search_rooms(self, search_term: str, skip: int = 0, limit: int = 100) -> List[RoomResponse]:
        """Search for rooms by name, building, type, or features."""
        try:
            rooms = await self.room_repository.search_rooms(
                search_term=search_term,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for room in rooms:
                self._cache[room.id] = room
            
            return rooms
            
        except Exception as e:
            logger.error(f"Failed to search rooms: {str(e)}")
            raise
    
    async def get_rooms_by_building(self, building_id: str, skip: int = 0, limit: int = 100) -> List[RoomResponse]:
        """Get rooms for a building."""
        try:
            rooms = await self.room_repository.get_by_building(
                building_id=building_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for room in rooms:
                self._cache[room.id] = room
            
            return rooms
            
        except Exception as e:
            logger.error(f"Failed to get rooms for building {building_id}: {str(e)}")
            raise
    
    async def get_rooms_by_type(self, room_type: str, skip: int = 0, limit: int = 100) -> List[RoomResponse]:
        """Get rooms by type."""
        try:
            rooms = await self.room_repository.get_by_type(
                room_type=room_type,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for room in rooms:
                self._cache[room.id] = room
            
            return rooms
            
        except Exception as e:
            logger.error(f"Failed to get rooms by type {room_type}: {str(e)}")
            raise
    
    async def get_rooms_by_capacity(self, min_capacity: int, max_capacity: int = None) -> List[RoomResponse]:
        """Get rooms by capacity range."""
        try:
            rooms = await self.room_repository.get_by_capacity(
                min_capacity=min_capacity,
                max_capacity=max_capacity
            )
            
            # Cache results
            for room in rooms:
                self._cache[room.id] = room
            
            return rooms
            
        except Exception as e:
            logger.error(f"Failed to get rooms by capacity: {str(e)}")
            raise
    
    async def get_rooms_by_availability(self, start_date: date, end_date: date, min_capacity: int = None) -> List[RoomResponse]:
        """Get available rooms for a date range."""
        try:
            rooms = await self.room_repository.get_rooms_by_availability(
                start_date=start_date,
                end_date=end_date,
                min_capacity=min_capacity
            )
            
            # Cache results
            for room in rooms:
                self._cache[room.id] = room
            
            return rooms
            
        except Exception as e:
            logger.error(f"Failed to get available rooms: {str(e)}")
            raise
    
    # Booking and Scheduling
    
    async def book_room(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Book a room for use."""
        try:
            # Validate booking data
            await self._validate_booking_data(booking_data)
            
            # Check room availability
            if not await self._is_room_available(
                booking_data['room_id'],
                booking_data['start_date'],
                booking_data['end_date']
            ):
                raise ConflictError("Room is not available for the requested time")
            
            # Create booking
            booking = await self.room_repository.create_booking(**booking_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return booking
            
        except Exception as e:
            logger.error(f"Failed to book room: {str(e)}")
            raise
    
    async def cancel_booking(self, booking_id: str) -> bool:
        """Cancel a room booking."""
        try:
            # Validate booking exists
            booking = await self.room_repository.get_booking_by_id(booking_id)
            if not booking:
                raise NotFoundError(f"Booking not found with ID: {booking_id}")
            
            # Check if booking can be cancelled (not started and not in the past)
            if not await self._can_cancel_booking(booking):
                raise ValidationError("Cannot cancel booking that has already started or is in the past")
            
            # Cancel booking
            result = await self.room_repository.cancel_booking(booking_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to cancel booking {booking_id}: {str(e)}")
            raise
    
    async def reschedule_booking(self, booking_id: str, new_start_date: date, new_end_date: date) -> bool:
        """Reschedule a room booking."""
        try:
            # Validate booking exists
            booking = await self.room_repository.get_booking_by_id(booking_id)
            if not booking:
                raise NotFoundError(f"Booking not found with ID: {booking_id}")
            
            # Validate new dates
            await self._validate_reschedule_dates(booking, new_start_date, new_end_date)
            
            # Check for conflicts
            if await self._check_reschedule_conflicts(booking_id, new_start_date, new_end_date):
                raise ConflictError("New schedule conflicts with existing bookings")
            
            # Reschedule booking
            result = await self.room_repository.reschedule_booking(
                booking_id=booking_id,
                new_start_date=new_start_date,
                new_end_date=new_end_date
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to reschedule booking {booking_id}: {str(e)}")
            raise
    
    async def get_room_availability(self, room_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get room availability for a date range."""
        try:
            # Get room
            room = await self.get_room(room_id)
            if not room:
                raise NotFoundError(f"Room not found with ID: {room_id}")
            
            # Get existing bookings
            bookings = await self.room_repository.get_bookings_by_date_range(
                room_id=room_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Calculate availability
            availability = self._calculate_availability(room, bookings, start_date, end_date)
            
            return {
                "room_id": room_id,
                "room_name": room.name,
                "room_capacity": room.capacity,
                "room_type": room.room_type,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "availability": availability,
                "total_slots": len(availability),
                "available_slots": len([a for a in availability if a['available']]),
                "utilization_rate": round((1 - len([a for a in availability if a['available']]) / len(availability)) * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get room availability for {room_id}: {str(e)}")
            raise
    
    async def get_booking_history(self, room_id: str, start_date: date = None, end_date: date = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get booking history for a room."""
        try:
            return await self.room_repository.get_booking_history(
                room_id=room_id,
                start_date=start_date,
                end_date=end_date,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get booking history for room {room_id}: {str(e)}")
            raise
    
    # Waiting List Management
    
    async def add_to_waiting_list(self, waiting_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add user to room waiting list."""
        try:
            # Validate waiting list data
            await self._validate_waiting_list_data(waiting_list_data)
            
            # Check if user is already on waiting list
            existing_entry = await self.room_repository.get_waiting_list_entry(
                room_id=waiting_list_data['room_id'],
                user_id=waiting_list_data['user_id']
            )
            if existing_entry:
                raise ConflictError("User is already on the waiting list for this room")
            
            # Add to waiting list
            entry = await self.room_repository.add_to_waiting_list(**waiting_list_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return entry
            
        except Exception as e:
            logger.error(f"Failed to add to waiting list: {str(e)}")
            raise
    
    async def remove_from_waiting_list(self, waiting_list_id: str) -> bool:
        """Remove user from room waiting list."""
        try:
            # Validate waiting list entry exists
            entry = await self.room_repository.get_waiting_list_entry_by_id(waiting_list_id)
            if not entry:
                raise NotFoundError(f"Waiting list entry not found with ID: {waiting_list_id}")
            
            # Remove from waiting list
            result = await self.room_repository.remove_from_waiting_list(waiting_list_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to remove from waiting list {waiting_list_id}: {str(e)}")
            raise
    
    async def get_waiting_list(self, room_id: str) -> List[Dict[str, Any]]:
        """Get waiting list for a room."""
        try:
            return await self.room_repository.get_waiting_list(room_id)
        except Exception as e:
            logger.error(f"Failed to get waiting list for room {room_id}: {str(e)}")
            raise
    
    async def process_waiting_list(self, room_id: str, booking_date: date) -> List[Dict[str, Any]]:
        """Process waiting list for a room."""
        try:
            # Get room
            room = await self.get_room(room_id)
            if not room:
                raise NotFoundError(f"Room not found with ID: {room_id}")
            
            # Get available slots for the date
            availability = await self.get_room_availability(room_id, booking_date, booking_date)
            available_slots = [a for a in availability['availability'] if a['available']]
            
            if not available_slots:
                return []
            
            # Get waiting list entries
            waiting_list = await self.get_waiting_list(room_id)
            waiting_list.sort(key=lambda x: x['position'])
            
            # Process entries
            processed_entries = []
            for entry in waiting_list:
                if len(processed_entries) >= len(available_slots):
                    break
                
                # Create booking
                booking_data = {
                    'room_id': room_id,
                    'user_id': entry['user_id'],
                    'start_date': booking_date.strftime('%Y-%m-%d'),
                    'end_date': booking_date.strftime('%Y-%m-%d'),
                    'purpose': entry.get('purpose', 'Waiting list booking'),
                    'status': 'confirmed'
                }
                
                try:
                    booking = await self.book_room(booking_data)
                    processed_entries.append({
                        'waiting_list_id': entry['id'],
                        'booking_id': booking['id'],
                        'user_id': entry['user_id'],
                        'processed_at': datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Failed to create booking from waiting list: {str(e)}")
                    continue
            
            # Remove processed entries from waiting list
            for entry in processed_entries:
                await self.remove_from_waiting_list(entry['waiting_list_id'])
            
            return processed_entries
            
        except Exception as e:
            logger.error(f"Failed to process waiting list for room {room_id}: {str(e)}")
            raise
    
    # Analytics and Reporting
    
    async def get_room_stats(self, room_id: str) -> RoomStats:
        """Get comprehensive statistics for a room."""
        try:
            # Get room
            room = await self.get_room(room_id)
            if not room:
                raise NotFoundError(f"Room not found with ID: {room_id}")
            
            # Get booking statistics
            total_bookings = await self.room_repository.get_total_bookings(room_id)
            completed_bookings = await self.room_repository.get_completed_bookings(room_id)
            cancelled_bookings = await self.room_repository.get_cancelled_bookings(room_id)
            
            # Calculate utilization
            utilization_rate = await self._calculate_utilization_rate(room_id)
            
            # Get waiting list statistics
            waiting_list_count = await self.room_repository.get_waiting_list_count(room_id)
            avg_waiting_time = await self._calculate_average_waiting_time(room_id)
            
            # Create stats object
            stats = RoomStats(
                room_id=room_id,
                room_name=room.name,
                room_capacity=room.capacity,
                room_type=room.room_type,
                total_bookings=total_bookings,
                completed_bookings=completed_bookings,
                cancelled_bookings=cancelled_bookings,
                utilization_rate=utilization_rate,
                waiting_list_count=waiting_list_count,
                average_waiting_time=avg_waiting_time,
                average_booking_duration=await self._calculate_average_booking_duration(room_id),
                last_booking_date=await self._get_last_booking_date(room_id),
                peak_usage_hours=await self._get_peak_usage_hours(room_id)
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get room stats for {room_id}: {str(e)}")
            raise
    
    async def generate_room_report(self, report_type: str = "overview", 
                                room_id: str = None, building_id: str = None, 
                                start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Generate comprehensive room report."""
        try:
            # Generate report based on type
            if report_type == "overview":
                return await self._generate_overview_report(room_id, building_id, start_date, end_date)
            elif report_type == "utilization":
                return await self._generate_utilization_report(room_id, building_id, start_date, end_date)
            elif report_type == "booking":
                return await self._generate_booking_report(room_id, building_id, start_date, end_date)
            elif report_type == "waiting_list":
                return await self._generate_waiting_list_report(room_id, building_id, start_date, end_date)
            else:
                raise ValidationError(f"Unknown report type: {report_type}")
                
        except Exception as e:
            logger.error(f"Failed to generate room report: {str(e)}")
            raise
    
    # Resource Optimization
    
    async def optimize_room_allocation(self, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize room allocation based on criteria."""
        try:
            # Validate allocation data
            await self._validate_optimization_data(allocation_data)
            
            # Get requirements
            required_capacity = allocation_data.get('required_capacity', 0)
            preferred_types = allocation_data.get('preferred_types', [])
            date_range = allocation_data.get('date_range', {})
            
            start_date = datetime.strptime(date_range['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(date_range['end_date'], '%Y-%m-%d').date()
            
            # Get available rooms
            available_rooms = await self.get_rooms_by_availability(start_date, end_date, required_capacity)
            
            # Filter by preferred types
            if preferred_types:
                available_rooms = [r for r in available_rooms if r.room_type in preferred_types]
            
            # Score rooms based on criteria
            scored_rooms = []
            for room in available_rooms:
                score = await self._score_room(room, allocation_data)
                scored_rooms.append({
                    'room': room,
                    'score': score
                })
            
            # Sort by score
            scored_rooms.sort(key=lambda x: x['score'], reverse=True)
            
            # Generate recommendations
            recommendations = []
            for i, (room_score, room_name) in enumerate([(r['score'], r['room'].name) for r in scored_rooms[:5]], 1):
                recommendations.append({
                    'rank': i,
                    'room_name': room_name,
                    'room_id': scored_rooms[i-1]['room'].id,
                    'score': room_score,
                    'capacity': scored_rooms[i-1]['room'].capacity,
                    'room_type': scored_rooms[i-1]['room'].room_type,
                    'building_id': scored_rooms[i-1]['room'].building_id,
                    'features': scored_rooms[i-1]['room'].features
                })
            
            return {
                'recommendations': recommendations,
                'total_rooms_considered': len(available_rooms),
                'optimization_criteria': allocation_data,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize room allocation: {str(e)}")
            raise
    
    # Batch Operations
    
    async def batch_update_rooms(self, updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple rooms."""
        results = {}
        
        for update in updates:
            room_id = update['room_id']
            try:
                result = await self.update_room(room_id, update)
                results[room_id] = result is not None
            except Exception as e:
                logger.error(f"Failed to update room {room_id}: {str(e)}")
                results[room_id] = False
        
        return results
    
    async def batch_delete_rooms(self, room_ids: List[str]) -> Dict[str, bool]:
        """Delete multiple rooms."""
        results = {}
        
        for room_id in room_ids:
            try:
                result = await self.delete_room(room_id)
                results[room_id] = result
            except Exception as e:
                logger.error(f"Failed to delete room {room_id}: {str(e)}")
                results[room_id] = False
        
        return results
    
    async def batch_book_rooms(self, bookings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Book multiple rooms."""
        results = {
            "success": [],
            "failed": [],
            "summary": {
                "total": len(bookings),
                "success": 0,
                "failed": 0
            }
        }
        
        for booking in bookings:
            try:
                result = await self.book_room(booking)
                results["success"].append({
                    "room_id": booking["room_id"],
                    "booking_id": result.get("id"),
                    "status": "booked"
                })
                results["summary"]["success"] += 1
                
            except Exception as e:
                results["failed"].append({
                    "room_id": booking.get("room_id"),
                    "error": str(e),
                    "status": "failed"
                })
                results["summary"]["failed"] += 1
        
        return results
    
    # Helper Methods
    
    async def _validate_room_creation(self, data: Dict[str, Any]) -> None:
        """Validate room creation data."""
        required_fields = ['name', 'building_id', 'room_type', 'capacity', 'location']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate name uniqueness
        existing_room = await self.room_repository.get_by_name(data['name'])
        if existing_room:
            raise ConflictError(f"Room with name '{data['name']}' already exists")
        
        # Validate capacity
        if not isinstance(data['capacity'], int) or data['capacity'] <= 0:
            raise ValidationError("Capacity must be a positive integer")
        
        # Validate building exists
        from src.infrastructure.repositories.building_repository import BuildingRepository
        building_repo = BuildingRepository()
        building = await building_repo.get_by_id(data['building_id'])
        if not building:
            raise NotFoundError(f"Building not found with ID: {data['building_id']}")
        
        # Validate room type
        valid_types = ['classroom', 'laboratory', 'office', 'conference', 'library', 'cafeteria', 'other']
        if data['room_type'] not in valid_types:
            raise ValidationError(f"Invalid room type: {data['room_type']}")
    
    async def _validate_room_update(self, data: Dict[str, Any]) -> None:
        """Validate room update data."""
        allowed_fields = ['name', 'room_type', 'capacity', 'location', 'description', 'features']
        
        for field in data.keys():
            if field not in allowed_fields:
                raise ValidationError(f"Cannot update field: {field}")
        
        # Validate capacity if provided
        if 'capacity' in data and data['capacity']:
            if not isinstance(data['capacity'], int) or data['capacity'] <= 0:
                raise ValidationError("Capacity must be a positive integer")
    
    async def _validate_booking_data(self, data: Dict[str, Any]) -> None:
        """Validate booking data."""
        required_fields = ['room_id', 'user_id', 'start_date', 'end_date', 'purpose']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate date format
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError("Invalid date format. Expected: YYYY-MM-DD")
        
        # Validate date logic
        if start_date > end_date:
            raise ValidationError("Start date cannot be after end date")
        
        # Validate dates are in the future
        if start_date < date.today():
            raise ValidationError("Start date cannot be in the past")
        
        # Validate room exists
        room = await self.get_room(data['room_id'])
        if not room:
            raise NotFoundError(f"Room not found with ID: {data['room_id']}")
        
        # Validate capacity requirement
        if data.get('required_capacity', 0) > room.capacity:
            raise ValidationError(f"Required capacity {data['required_capacity']} exceeds room capacity {room.capacity}")
    
    def _calculate_availability(self, room: RoomResponse, bookings: List[Dict[str, Any]], start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Calculate room availability for a date range."""
        availability = []
        
        current_date = start_date
        while current_date <= end_date:
            day_availability = []
            
            # Generate 8-hour slots (9:00 AM to 5:00 PM)
            for hour in range(9, 17):
                slot_time = f"{hour:02d}:00"
                
                # Check if slot is booked
                slot_booked = False
                for booking in bookings:
                    if booking['start_date'] == current_date.strftime('%Y-%m-%d'):
                        booking_start = int(booking['start_time'].split(':')[0])
                        booking_end = int(booking['end_time'].split(':')[0])
                        
                        if booking_start <= hour < booking_end:
                            slot_booked = True
                            break
                
                day_availability.append({
                    "date": current_date.strftime('%Y-%m-%d'),
                    "time": slot_time,
                    "available": not slot_booked,
                    "room_id": room.id
                })
            
            availability.extend(day_availability)
            current_date += timedelta(days=1)
        
        return availability
    
    async def _is_room_available(self, room_id: str, start_date: date, end_date: date) -> bool:
        """Check if room is available for a date range."""
        bookings = await self.room_repository.get_bookings_by_date_range(
            room_id=room_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Check if any bookings overlap with the requested time
        for booking in bookings:
            booking_start = datetime.strptime(booking['start_date'], '%Y-%m-%d').date()
            booking_end = datetime.strptime(booking['end_date'], '%Y-%m-%d').date()
            
            if not (end_date < booking_start or start_date > booking_end):
                return False
        
        return True
    
    async def _can_cancel_booking(self, booking: Dict[str, Any]) -> bool:
        """Check if booking can be cancelled."""
        start_date = datetime.strptime(booking['start_date'], '%Y-%m-%d').date()
        
        # Can cancel if booking hasn't started and is not in the past
        return start_date > date.today()
    
    async def _validate_reschedule_dates(self, booking: Dict[str, Any], new_start_date: date, new_end_date: date) -> None:
        """Validate reschedule dates."""
        if new_start_date > new_end_date:
            raise ValidationError("Start date cannot be after end date")
        
        # Check if dates are in the future
        if new_start_date < date.today():
            raise ValidationError("Start date cannot be in the past")
    
    async def _check_reschedule_conflicts(self, booking_id: str, new_start_date: date, new_end_date: date) -> bool:
        """Check for reschedule conflicts."""
        # This would check for conflicts excluding the current booking
        # For now, return False (should be implemented)
        return False
    
    async def _has_active_bookings(self, room_id: str) -> bool:
        """Check if room has active bookings."""
        # This would check for active bookings in the repository
        # For now, return False (should be implemented)
        return False
    
    async def _has_waiting_list_entries(self, room_id: str) -> bool:
        """Check if room has waiting list entries."""
        count = await self.room_repository.get_waiting_list_count(room_id)
        return count > 0
    
    async def _was_recently_used(self, room_id: str) -> bool:
        """Check if room was recently used."""
        # This would check recent usage in the repository
        # For now, return False (should be implemented)
        return False
    
    def _calculate_utilization_rate(self, room_id: str) -> float:
        """Calculate room utilization rate."""
        # This would calculate utilization rate from booking data
        # For now, return 0.0 (should be implemented)
        return 0.0
    
    async def _calculate_average_booking_duration(self, room_id: str) -> float:
        """Calculate average booking duration for a room."""
        # This would calculate average booking duration
        # For now, return 0.0 (should be implemented)
        return 0.0
    
    async def _get_last_booking_date(self, room_id: str) -> Optional[str]:
        """Get last booking date for a room."""
        # This would get the last booking date
        # For now, return None (should be implemented)
        return None
    
    async def _get_peak_usage_hours(self, room_id: str) -> List[str]:
        """Get peak usage hours for a room."""
        # This would get peak usage hours
        # For now, return empty list (should be implemented)
        return []
    
    async def _calculate_average_waiting_time(self, room_id: str) -> float:
        """Calculate average waiting time for a room."""
        # This would calculate average waiting time
        # For now, return 0.0 (should be implemented)
        return 0.0
    
    async def _validate_waiting_list_data(self, data: Dict[str, Any]) -> None:
        """Validate waiting list data."""
        required_fields = ['room_id', 'user_id', 'purpose']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate room exists
        room = await self.get_room(data['room_id'])
        if not room:
            raise NotFoundError(f"Room not found with ID: {data['room_id']}")
        
        # Validate user exists (would need user repository)
        # For now, just check that user_id is provided
        if not data['user_id']:
            raise ValidationError("User ID is required")
    
    async def _validate_optimization_data(self, data: Dict[str, Any]) -> None:
        """Validate optimization data."""
        required_fields = ['date_range']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate date range
        if 'start_date' not in data['date_range'] or 'end_date' not in data['date_range']:
            raise ValidationError("Date range must include start_date and end_date")
        
        try:
            start_date = datetime.strptime(data['date_range']['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['date_range']['end_date'], '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError("Invalid date format. Expected: YYYY-MM-DD")
        
        if start_date > end_date:
            raise ValidationError("Start date cannot be after end date")
    
    async def _score_room(self, room: RoomResponse, criteria: Dict[str, Any]) -> float:
        """Score a room based on optimization criteria."""
        score = 0.0
        
        # Capacity score
        required_capacity = criteria.get('required_capacity', 0)
        if room.capacity >= required_capacity:
            score += 40.0  # 40 points for meeting capacity
            # Bonus points for having extra capacity
            extra_capacity = room.capacity - required_capacity
            score += min(extra_capacity * 2, 10.0)  # Up to 10 bonus points
        else:
            score -= (required_capacity - room.capacity) * 5.0  # Penalty for insufficient capacity
        
        # Type preference score
        preferred_types = criteria.get('preferred_types', [])
        if room.room_type in preferred_types:
            score += 20.0  # 20 points for preferred type
        else:
            score -= 10.0  # 10 point penalty for non-preferred type
        
        # Features score
        required_features = criteria.get('required_features', [])
        room_features = room.features or []
        
        matching_features = set(required_features) & set(room_features)
        if matching_features:
            score += len(matching_features) * 5.0  # 5 points per matching feature
        
        # Location score (if building preference specified)
        preferred_buildings = criteria.get('preferred_buildings', [])
        if preferred_buildings and room.building_id in preferred_buildings:
            score += 15.0  # 15 points for preferred building
        
        # Availability score (would need to check actual availability)
        # For now, just give a base score
        score += 10.0
        
        # Ensure score is non-negative
        return max(0.0, score)
    
    async def _generate_overview_report(self, room_id: str, building_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate overview report for rooms."""
        try:
            # Get rooms based on filters
            if room_id:
                rooms = [await self.get_room(room_id)]
            elif building_id:
                rooms = await self.get_rooms_by_building(building_id, 0, 1000)
            else:
                # Get all rooms
                rooms = await self.room_repository.get_all(0, 1000)
            
            if not rooms:
                raise NotFoundError("No rooms found for specified criteria")
            
            # Calculate summary statistics
            total_rooms = len(rooms)
            total_capacity = sum(room.capacity for room in rooms)
            by_type = {}
            by_building = {}
            
            for room in rooms:
                # Group by type
                room_type = room.room_type
                by_type[room_type] = by_type.get(room_type, 0) + 1
                
                # Group by building
                building_id = room.building_id
                by_building[building_id] = by_building.get(building_id, 0) + 1
            
            return {
                "rooms": rooms,
                "summary": {
                    "total_rooms": total_rooms,
                    "total_capacity": total_capacity,
                    "average_capacity": round(total_capacity / total_rooms, 2) if total_rooms > 0 else 0,
                    "by_type": by_type,
                    "by_building": by_building
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
    
    async def _generate_utilization_report(self, room_id: str, building_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate utilization report for rooms."""
        try:
            # Get rooms based on filters
            if room_id:
                rooms = [await self.get_room(room_id)]
            elif building_id:
                rooms = await self.get_rooms_by_building(building_id, 0, 1000)
            else:
                rooms = await self.room_repository.get_all(0, 1000)
            
            if not rooms:
                raise NotFoundError("No rooms found for specified criteria")
            
            # Calculate utilization for each room
            utilization_data = []
            total_bookings = 0
            total_utilization = 0
            
            for room in rooms:
                stats = await self.get_room_stats(room.id)
                utilization_data.append({
                    "room_id": room.id,
                    "room_name": room.name,
                    "utilization_rate": stats.utilization_rate,
                    "total_bookings": stats.total_bookings,
                    "completed_bookings": stats.completed_bookings,
                    "cancelled_bookings": stats.cancelled_bookings
                })
                
                total_bookings += stats.total_bookings
                total_utilization += stats.utilization_rate
            
            # Calculate overall utilization
            overall_utilization = total_utilization / len(rooms) if rooms else 0
            
            return {
                "rooms": utilization_data,
                "summary": {
                    "total_rooms": len(rooms),
                    "total_bookings": total_bookings,
                    "overall_utilization": round(overall_utilization, 2),
                    "peak_utilization_room": max(utilization_data, key=lambda x: x['utilization_rate']) if utilization_data else None,
                    "lowest_utilization_room": min(utilization_data, key=lambda x: x['utilization_rate']) if utilization_data else None
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
    
    async def _generate_booking_report(self, room_id: str, building_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate booking report for rooms."""
        try:
            # Get rooms based on filters
            if room_id:
                rooms = [await self.get_room(room_id)]
            elif building_id:
                rooms = await self.get_rooms_by_building(building_id, 0, 1000)
            else:
                rooms = await self.room_repository.get_all(0, 1000)
            
            if not rooms:
                raise NotFoundError("No rooms found for specified criteria")
            
            # Get booking data for each room
            booking_data = []
            total_bookings = 0
            by_status = {}
            by_purpose = {}
            
            for room in rooms:
                bookings = await self.get_booking_history(room.id, start_date, end_date, 0, 1000)
                
                for booking in bookings:
                    booking_data.append({
                        "room_id": room.id,
                        "room_name": room.name,
                        "booking_id": booking.get('id'),
                        "user_id": booking.get('user_id'),
                        "start_date": booking.get('start_date'),
                        "end_date": booking.get('end_date'),
                        "purpose": booking.get('purpose'),
                        "status": booking.get('status')
                    })
                    
                    total_bookings += 1
                    
                    # Group by status
                    status = booking.get('status', 'unknown')
                    by_status[status] = by_status.get(status, 0) + 1
                    
                    # Group by purpose
                    purpose = booking.get('purpose', 'unknown')
                    by_purpose[purpose] = by_purpose.get(purpose, 0) + 1
            
            return {
                "bookings": booking_data,
                "summary": {
                    "total_bookings": total_bookings,
                    "by_status": by_status,
                    "by_purpose": by_purpose,
                    "average_bookings_per_room": round(total_bookings / len(rooms), 2) if rooms else 0
                },
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "booking"
            }
        except Exception as e:
            logger.error(f"Failed to generate booking report: {str(e)}")
            raise
    
    async def _generate_waiting_list_report(self, room_id: str, building_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate waiting list report for rooms."""
        try:
            # Get rooms based on filters
            if room_id:
                rooms = [await self.get_room(room_id)]
            elif building_id:
                rooms = await self.get_rooms_by_building(building_id, 0, 1000)
            else:
                rooms = await self.room_repository.get_all(0, 1000)
            
            if not rooms:
                raise NotFoundError("No rooms found for specified criteria")
            
            # Get waiting list data for each room
            waiting_list_data = []
            total_waiting_list = 0
            by_priority = {}
            by_department = {}
            
            for room in rooms:
                waiting_list = await self.get_waiting_list(room.id)
                
                for entry in waiting_list:
                    waiting_list_data.append({
                        "room_id": room.id,
                        "room_name": room.name,
                        "waiting_list_id": entry.get('id'),
                        "user_id": entry.get('user_id'),
                        "position": entry.get('position'),
                        "priority": entry.get('priority'),
                        "purpose": entry.get('purpose'),
                        "added_date": entry.get('added_date')
                    })
                    
                    total_waiting_list += 1
                    
                    # Group by priority
                    priority = entry.get('priority', 'normal')
                    by_priority[priority] = by_priority.get(priority, 0) + 1
                    
                    # Group by department (would need user data)
                    # For now, just use 'unknown'
                    department = 'unknown'
                    by_department[department] = by_department.get(department, 0) + 1
            
            return {
                "waiting_list": waiting_list_data,
                "summary": {
                    "total_waiting_list": total_waiting_list,
                    "by_priority": by_priority,
                    "by_department": by_department,
                    "average_waiting_time": await self._calculate_average_waiting_time_timeframe(room_id or building_id)
                },
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "waiting_list"
            }
        except Exception as e:
            logger.error(f"Failed to generate waiting list report: {str(e)}")
            raise
    
    async def _calculate_average_waiting_time_timeframe(self, room_id: str) -> float:
        """Calculate average waiting time for a room or building."""
        # This would calculate average waiting time for the specified timeframe
        # For now, return 0.0 (should be implemented)
        return 0.0
    
    async def _invalidate_cache(self) -> None:
        """Invalidate room cache."""
        self._cache.clear()
    
    # Abstract method implementations required by BaseService
    
    async def create(self, data: Dict) -> Dict:
        """Create a new room entity."""
        room = await self.create_room(data)
        return room.dict()
    
    async def get(self, id: str) -> Optional[Dict]:
        """Get a room entity by ID."""
        room = await self.get_room_by_id(id)
        return room.dict() if room else None
    
    async def update(self, id: str, data: Dict) -> Dict:
        """Update a room entity by ID."""
        room = await self.update_room(id, data)
        return room.dict()
    
    async def delete(self, id: str) -> bool:
        """Delete a room entity by ID."""
        return await self.delete_room(id)
    
    async def list(self, skip: int = 0, limit: int = 100, filters: Dict = None) -> List[Dict]:
        """List all room entities."""
        rooms = await self.get_all_rooms(skip=skip, limit=limit)
        return [room.dict() for room in rooms]
    
    async def count(self, filters: Dict = None) -> int:
        """Count total number of room entities."""
        return await self.get_room_count()
        self._cache.clear()