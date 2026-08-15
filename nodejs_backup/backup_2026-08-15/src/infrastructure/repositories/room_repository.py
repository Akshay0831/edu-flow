"""
Room Management Repository

This module provides database operations for room management:
- CRUD operations for rooms
- Room booking and scheduling
- Room capacity and utilization
- Waiting list management
- Room analytics and reporting
- Maintenance scheduling

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, time, date, timedelta
from uuid import uuid4
from queue import Queue
import heapq

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.core.logging import get_logger
from src.core.database_abstraction import DatabaseManager, DatabaseInterface
from src.infrastructure.repositories.base_repository import BaseRepository, QueryResult, RepositoryOperation
from src.models.room import (
    RoomCreate, RoomUpdate, RoomResponse,
    RoomBooking, RoomBookingResponse,
    RoomMaintenance, RoomStats
)

logger = get_logger(__name__)


class RoomRepository(BaseRepository):
    """Room management repository with comprehensive functionality."""
    
    def __init__(self, database_manager: DatabaseManager = None):
        super().__init__()
        self._database = database_manager.get_database() if database_manager else None
        self._collection = "rooms"
        self._bookings_collection = "room_bookings"
        self._maintenance_collection = "room_maintenance"
        self._waiting_list_collection = "room_waiting_list"
        self._conflicts_collection = "room_conflicts"
    
    # Core CRUD Operations
    
    async def get_by_id(self, room_id: str) -> Optional[RoomResponse]:
        """Get a room by ID."""
        try:
            result = await self._find_one(self._collection, {"room_id": room_id})
            if result:
                return RoomResponse(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting room by ID {room_id}: {str(e)}")
            raise DatabaseError(f"Failed to get room: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100, 
                     filters: Dict[str, Any] = None) -> List[RoomResponse]:
        """Get all rooms with optional filtering."""
        try:
            query_filter = filters or {}
            result = await self._find_many(
                self._collection, 
                query_filter,
                skip=skip,
                limit=limit,
                sort=[("created_at", -1)]
            )
            
            return [RoomResponse(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting all rooms: {str(e)}")
            raise DatabaseError(f"Failed to fetch rooms: {str(e)}")
    
    async def create(self, **data) -> RoomResponse:
        """Create a new room."""
        try:
            # Add required fields
            if 'room_id' not in data:
                data['room_id'] = str(uuid4())
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow()
            if 'updated_at' not in data:
                data['updated_at'] = datetime.utcnow()
            
            # Validate room data
            await self._validate_room_data(data)
            
            # Insert into database
            result = await self._insert(self._collection, data)
            if result.inserted_id:
                created_room = await self.get_by_id(data['room_id'])
                return created_room
            else:
                raise DatabaseError("Failed to create room")
                
        except Exception as e:
            logger.error(f"Error creating room: {str(e)}")
            raise DatabaseError(f"Failed to create room: {str(e)}")
    
    async def update(self, room_id: str, **data) -> Optional[RoomResponse]:
        """Update an existing room."""
        try:
            # Update timestamps
            data['updated_at'] = datetime.utcnow()
            
            # Validate updated room data
            await self._validate_room_data(data)
            
            # Update in database
            result = await self._update(
                self._collection,
                {"room_id": room_id},
                {"$set": data}
            )
            
            if result.modified_count > 0:
                updated_room = await self.get_by_id(room_id)
                return updated_room
            else:
                raise NotFoundError(f"Room not found with ID: {room_id}")
                
        except Exception as e:
            logger.error(f"Error updating room {room_id}: {str(e)}")
            raise DatabaseError(f"Failed to update room: {str(e)}")
    
    async def delete(self, room_id: str) -> bool:
        """Delete a room and related data."""
        try:
            # Check if room has active bookings
            has_active_bookings = await self.has_active_bookings(room_id)
            if has_active_bookings:
                raise ValidationError("Cannot delete room with active bookings")
            
            # Delete the room
            result = await self._delete(self._collection, {"room_id": room_id})
            
            if result.deleted_count > 0:
                # Delete related data
                await self._delete(self._bookings_collection, {"room_id": room_id})
                await self._delete(self._maintenance_collection, {"room_id": room_id})
                await self._delete(self._waiting_list_collection, {"room_id": room_id})
                await self._delete(self._conflicts_collection, {"room_id": room_id})
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error deleting room {room_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete room: {str(e)}")
    
    # Room-specific Operations
    
    async def validate_room(self, room_id: str) -> bool:
        """Validate that a room exists."""
        try:
            room = await self._find_one(self._collection, {"room_id": room_id}, limit=1)
            return room is not None
        except Exception:
            return False
    
    async def validate_code(self, code: str) -> bool:
        """Validate that a room code is unique."""
        try:
            existing = await self._find_one(self._collection, {"room_code": code}, limit=1)
            return existing is not None
        except Exception:
            return False
    
    async def validate_building(self, building_id: str) -> bool:
        """Validate that a building exists."""
        try:
            building = await self._find_one("buildings", {"building_id": building_id}, limit=1)
            return building is not None
        except Exception:
            return False
    
    async def validate_teacher(self, teacher_id: str) -> bool:
        """Validate that a teacher exists."""
        try:
            teacher = await self._find_one("teachers", {"teacher_id": teacher_id}, limit=1)
            return teacher is not None
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
    
    async def get_room_stats(self, room_id: str, start_date: datetime = None, end_date: datetime = None) -> RoomStats:
        """Get statistics for a room."""
        try:
            # Get the room
            room = await self.get_by_id(room_id)
            if not room:
                raise NotFoundError(f"Room not found with ID: {room_id}")
            
            # Get bookings for the date range
            bookings = await self.get_room_bookings(
                room_id=room_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Calculate statistics
            stats = RoomStats(
                room_id=room_id,
                room_name=room.name,
                total_bookings=len(bookings),
                active_bookings=len([b for b in bookings if b.booking_status == "confirmed"]),
                average_utilization=await self._calculate_utilization_rate(room_id, start_date, end_date),
                peak_utilization_hours=await self._calculate_peak_hours(room_id, start_date, end_date),
                equipment_utilization=await self._calculate_equipment_utilization(room_id, start_date, end_date),
                maintenance_frequency=await self._calculate_maintenance_frequency(room_id),
                compliance_score=await self._calculate_compliance_score(room_id),
                booking_cancellation_rate=await self._calculate_cancellation_rate(room_id),
                booking_reschedule_rate=await self._calculate_reschedule_rate(room_id),
                popular_equipment=await self._get_popular_equipment(room_id, start_date, end_date),
                waiting_list_stats=await self._get_waiting_list_stats(room_id)
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting room stats for {room_id}: {str(e)}")
            raise DatabaseError(f"Failed to get room stats: {str(e)}")
    
    async def get_room_availability(self, room_id: str, start_date: datetime = None, 
                                   end_date: datetime = None, time_slot: str = None) -> Dict[str, Any]:
        """Get room availability information."""
        try:
            room = await self.get_by_id(room_id)
            if not room:
                raise NotFoundError(f"Room not found with ID: {room_id}")
            
            # Get bookings for the specified date range
            bookings = await self.get_room_bookings(
                room_id=room_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Calculate availability
            availability = {
                "room_id": room_id,
                "room_name": room.name,
                "room_capacity": room.capacity,
                "room_type": room.room_type,
                "current_date": datetime.utcnow().date(),
                "requested_range": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "time_slot": time_slot
                },
                "availability_status": "available",
                "unavailable_periods": [],
                "equipment_status": await self._get_equipment_availability(room_id),
                "maintenance_periods": await self._get_maintenance_periods(room_id, start_date, end_date),
                "booking_conflicts": []
            }
            
            # Check for conflicts
            if time_slot:
                slot_start, slot_end = self._parse_time_slot(time_slot)
                for booking in bookings:
                    if self._time_ranges_overlap(slot_start, slot_end, booking.start_time, booking.end_time):
                        availability["booking_conflicts"].append({
                            "booking_id": booking.id,
                            "start_time": booking.start_time,
                            "end_time": booking.end_time,
                            "booking_type": booking.booking_type,
                            "purpose": booking.purpose
                        })
                        availability["availability_status"] = "conflicted"
            
            # Calculate availability percentage
            if start_date and end_date:
                total_hours = (end_date - start_date).days * 24
                booked_hours = sum(
                    (b.end_time - b.start_time).total_seconds() / 3600 
                    for b in bookings if b.booking_status == "confirmed"
                )
                availability["availability_percentage"] = max(0, (total_hours - booked_hours) / total_hours * 100)
            
            return availability
            
        except Exception as e:
            logger.error(f"Error getting room availability for {room_id}: {str(e)}")
            raise DatabaseError(f"Failed to get room availability: {str(e)}")
    
    # Booking Management
    
    async def create_booking(self, **data) -> RoomBookingResponse:
        """Create a room booking."""
        try:
            # Add required fields
            if 'booking_id' not in data:
                data['booking_id'] = str(uuid4())
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow()
            if 'updated_at' not in data:
                data['updated_at'] = datetime.utcnow()
            if 'booking_status' not in data:
                data['booking_status'] = "pending"
            
            # Validate booking data
            await self._validate_booking_data(data)
            
            # Insert booking
            result = await self._insert(self._bookings_collection, data)
            if result.inserted_id:
                created_booking = await self.get_booking_by_id(data['booking_id'])
                return created_booking
            else:
                raise DatabaseError("Failed to create room booking")
                
        except Exception as e:
            logger.error(f"Error creating room booking: {str(e)}")
            raise DatabaseError(f"Failed to create room booking: {str(e)}")
    
    async def get_room_bookings(self, room_id: str, skip: int = 0, limit: int = 100,
                              booking_status: str = None, start_date: datetime = None,
                              end_date: datetime = None, booking_type: str = None,
                              teacher_id: str = None, class_id: str = None,
                              search: str = None) -> List[RoomBookingResponse]:
        """Get room bookings with optional filtering."""
        try:
            query_filter = {"room_id": room_id}
            
            if booking_status:
                query_filter["booking_status"] = booking_status
            if booking_type:
                query_filter["booking_type"] = booking_type
            if teacher_id:
                query_filter["teacher_id"] = teacher_id
            if class_id:
                query_filter["class_id"] = class_id
            if start_date and end_date:
                query_filter["start_time"] = {"$gte": start_date, "$lte": end_date}
            
            # Search in purpose and booking notes
            if search:
                query_filter["$or"] = [
                    {"purpose": {"$regex": search, "$options": "i"}},
                    {"booking_notes": {"$regex": search, "$options": "i"}}
                ]
            
            result = await self._find_many(
                self._bookings_collection,
                query_filter,
                skip=skip,
                limit=limit,
                sort=[("start_time", 1)]
            )
            
            return [RoomBookingResponse(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting room bookings: {str(e)}")
            raise DatabaseError(f"Failed to fetch room bookings: {str(e)}")
    
    async def get_booking_by_id(self, booking_id: str) -> Optional[RoomBookingResponse]:
        """Get a room booking by ID."""
        try:
            result = await self._find_one(self._bookings_collection, {"booking_id": booking_id})
            if result:
                return RoomBookingResponse(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting room booking by ID {booking_id}: {str(e)}")
            raise DatabaseError(f"Failed to get room booking: {str(e)}")
    
    async def confirm_booking(self, booking_id: str, confirmed_by_id: str = None, 
                            confirmation_notes: str = None) -> bool:
        """Confirm a room booking."""
        try:
            result = await self._update(
                self._bookings_collection,
                {"booking_id": booking_id},
                {
                    "$set": {
                        "booking_status": "confirmed",
                        "confirmed_at": datetime.utcnow(),
                        "confirmed_by_id": confirmed_by_id,
                        "confirmation_notes": confirmation_notes,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error confirming booking {booking_id}: {str(e)}")
            raise DatabaseError(f"Failed to confirm booking: {str(e)}")
    
    async def cancel_booking(self, booking_id: str, cancellation_reason: str = None,
                           cancelled_by_id: str = None) -> bool:
        """Cancel a room booking."""
        try:
            result = await self._update(
                self._bookings_collection,
                {"booking_id": booking_id},
                {
                    "$set": {
                        "booking_status": "cancelled",
                        "cancelled_at": datetime.utcnow(),
                        "cancellation_reason": cancellation_reason,
                        "cancelled_by_id": cancelled_by_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error cancelling booking {booking_id}: {str(e)}")
            raise DatabaseError(f"Failed to cancel booking: {str(e)}")
    
    async def has_active_bookings(self, room_id: str) -> bool:
        """Check if a room has active bookings."""
        try:
            result = await self._find_one(
                self._bookings_collection,
                {"room_id": room_id, "booking_status": "confirmed"}
            )
            return result is not None
        except Exception:
            return False
    
    async def check_booking_conflicts(self, room_id: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Check for booking conflicts."""
        try:
            query_filter = {
                "room_id": room_id,
                "booking_status": "confirmed",
                "$or": [
                    {"start_time": {"$lt": end_time, "$gte": start_time}},
                    {"end_time": {"$gt": start_time, "$lte": end_time}},
                    {"start_time": {"$lte": start_time}, "end_time": {"$gte": end_time}}
                ]
            }
            
            conflicting_bookings = await self._find_many(self._bookings_collection, query_filter)
            
            return {
                "has_conflict": len(conflicting_bookings) > 0,
                "conflict_count": len(conflicting_bookings),
                "conflicting_bookings": conflicting_bookings,
                "conflict_details": self._generate_conflict_message(conflicting_bookings)
            }
            
        except Exception as e:
            logger.error(f"Error checking booking conflicts: {str(e)}")
            raise DatabaseError(f"Failed to check booking conflicts: {str(e)}")
    
    async def check_capacity_availability(self, room_id: str, participants_count: int) -> bool:
        """Check if room has capacity for the required number of participants."""
        try:
            room = await self.get_by_id(room_id)
            if not room:
                return False
            
            # Check if the request exceeds room capacity
            return participants_count <= room.capacity
            
        except Exception:
            return False
    
    async def check_equipment_availability(self, room_id: str, equipment_required: List[str]) -> bool:
        """Check if required equipment is available."""
        try:
            if not equipment_required:
                return True
            
            # Get room equipment
            room = await self.get_by_id(room_id)
            if not room or not room.equipment:
                return False
            
            available_equipment = list(room.equipment.keys())
            
            # Check if all required equipment is available
            for required in equipment_required:
                if required not in available_equipment:
                    return False
            
            return True
            
        except Exception:
            return False
    
    # Waiting List Management
    
    async def add_to_waiting_list(self, room_id: str, participants_count: int, 
                               start_time: datetime, end_time: datetime,
                               requested_by_id: str) -> int:
        """Add a booking request to the waiting list."""
        try:
            # Validate room
            if not await self.validate_room(room_id):
                raise NotFoundError(f"Room not found with ID: {room_id}")
            
            # Calculate priority based on various factors
            priority = await self._calculate_waiting_list_priority(
                room_id, participants_count, start_time, end_time
            )
            
            # Create waiting list entry
            waiting_entry = {
                "waiting_id": str(uuid4()),
                "room_id": room_id,
                "participants_count": participants_count,
                "start_time": start_time,
                "end_time": end_time,
                "requested_by_id": requested_by_id,
                "priority": priority,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "waiting",
                "notes": ""
            }
            
            # Insert waiting list
            result = await self._insert(self._waiting_list_collection, waiting_entry)
            
            if result.inserted_id:
                # Calculate position in waiting list
                position = await self._get_waiting_list_position(room_id, result.inserted_id)
                return position
            
            raise DatabaseError("Failed to add to waiting list")
            
        except Exception as e:
            logger.error(f"Error adding to waiting list: {str(e)}")
            raise DatabaseError(f"Failed to add to waiting list: {str(e)}")
    
    async def get_waiting_list(self, room_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get waiting list for a room."""
        try:
            query_filter = {"room_id": room_id, "status": "waiting"}
            result = await self._find_many(
                self._waiting_list_collection,
                query_filter,
                skip=skip,
                limit=limit,
                sort=[("priority", 1), ("created_at", 1)]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting waiting list: {str(e)}")
            raise DatabaseError(f"Failed to fetch waiting list: {str(e)}")
    
    async def get_waiting_list_count(self, room_id: str) -> int:
        """Get number of entries in waiting list for a room."""
        try:
            result = await self._find_many(
                self._waiting_list_collection,
                {"room_id": room_id, "status": "waiting"}
            )
            return len(result)
        except Exception:
            return 0
    
    async def _get_waiting_list_position(self, room_id: str, waiting_id: str) -> int:
        """Calculate position in waiting list."""
        try:
            # Get all entries with higher priority or same priority but earlier creation
            higher_priority = await self._find_many(
                self._waiting_list_collection,
                {
                    "room_id": room_id,
                    "$or": [
                        {"priority": {"$lt": self._get_entry_priority(waiting_id)}},
                        {
                            "priority": self._get_entry_priority(waiting_id),
                            "created_at": {"$lt": self._get_entry_created_at(waiting_id)}
                        }
                    ],
                    "status": "waiting"
                }
            )
            
            return len(higher_priority) + 1
            
        except Exception:
            return 1
    
    async def _get_entry_priority(self, waiting_id: str) -> int:
        """Get priority of a waiting list entry."""
        try:
            entry = await self._find_one(
                self._waiting_list_collection,
                {"waiting_id": waiting_id}
            )
            return entry.get('priority', 1) if entry else 1
        except Exception:
            return 1
    
    async def _get_entry_created_at(self, waiting_id: str) -> datetime:
        """Get creation time of a waiting list entry."""
        try:
            entry = await self._find_one(
                self._waiting_list_collection,
                {"waiting_id": waiting_id}
            )
            return entry.get('created_at', datetime.min) if entry else datetime.min
        except Exception:
            return datetime.min
    
    async def _calculate_waiting_list_priority(self, room_id: str, participants_count: int, 
                                            start_time: datetime, end_time: datetime) -> int:
        """Calculate priority for waiting list entry."""
        try:
            # Base priority
            priority = 1
            
            # Urgency factors
            time_until_booking = (start_time - datetime.utcnow()).total_seconds()
            
            # Shorter time until booking = higher priority
            if time_until_booking < 86400:  # Less than 24 hours
                priority += 3
            elif time_until_booking < 604800:  # Less than 1 week
                priority += 2
            elif time_until_booking < 2592000:  # Less than 1 month
                priority += 1
            
            # Participants count (more participants = higher priority)
            if participants_count > room.capacity * 0.8:  # More than 80% capacity
                priority += 2
            elif participants_count > room.capacity * 0.5:  # More than 50% capacity
                priority += 1
            
            # Room type priority (certain room types are more in demand)
            room = await self.get_by_id(room_id)
            if room.room_type in ['lecture', 'lab']:
                priority += 2
            elif room.room_type == 'seminar':
                priority += 1
            
            return min(priority, 10)  # Cap at 10
            
        except Exception:
            return 1
    
    # Maintenance Management
    
    async def schedule_maintenance(self, **data) -> RoomMaintenance:
        """Schedule maintenance for a room."""
        try:
            # Add required fields
            if 'maintenance_id' not in data:
                data['maintenance_id'] = str(uuid4())
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow()
            if 'updated_at' not in data:
                data['updated_at'] = datetime.utcnow()
            if 'status' not in data:
                data['status'] = "scheduled"
            
            # Validate maintenance data
            await self._validate_maintenance_data(data)
            
            # Insert maintenance record
            result = await self._insert(self._maintenance_collection, data)
            if result.inserted_id:
                maintenance = await self.get_maintenance_by_id(data['maintenance_id'])
                return maintenance
            else:
                raise DatabaseError("Failed to schedule maintenance")
                
        except Exception as e:
            logger.error(f"Error scheduling maintenance: {str(e)}")
            raise DatabaseError(f"Failed to schedule maintenance: {str(e)}")
    
    async def get_maintenance_records(self, room_id: str, skip: int = 0, limit: int = 100,
                                   maintenance_type: str = None, status: str = None) -> List[RoomMaintenance]:
        """Get maintenance records for a room."""
        try:
            query_filter = {"room_id": room_id}
            
            if maintenance_type:
                query_filter["maintenance_type"] = maintenance_type
            if status:
                query_filter["status"] = status
            
            result = await self._find_many(
                self._maintenance_collection,
                query_filter,
                skip=skip,
                limit=limit,
                sort=[("scheduled_date", 1)]
            )
            
            return [RoomMaintenance(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting maintenance records: {str(e)}")
            raise DatabaseError(f"Failed to fetch maintenance records: {str(e)}")
    
    async def get_maintenance_by_id(self, maintenance_id: str) -> Optional[RoomMaintenance]:
        """Get a maintenance record by ID."""
        try:
            result = await self._find_one(self._maintenance_collection, {"maintenance_id": maintenance_id})
            if result:
                return RoomMaintenance(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting maintenance record by ID {maintenance_id}: {str(e)}")
            raise DatabaseError(f"Failed to get maintenance record: {str(e)}")
    
    # Analytics and Monitoring
    
    async def get_current_utilization(self, room_id: str) -> float:
        """Get current utilization percentage for a room."""
        try:
            # Get current date and time
            now = datetime.utcnow()
            today = now.date()
            
            # Get today's bookings
            today_bookings = await self.get_room_bookings(
                room_id=room_id,
                start_date=today,
                end_date=today,
                booking_status="confirmed"
            )
            
            if not today_bookings:
                return 0.0
            
            # Calculate utilization
            total_capacity_minutes = 24 * 60  # 24 hours in minutes
            booked_minutes = sum(
                (booking.end_time - booking.start_time).total_seconds() / 60
                for booking in today_bookings
            )
            
            utilization = (booked_minutes / total_capacity_minutes) * 100
            return round(utilization, 2)
            
        except Exception:
            return 0.0
    
    async def get_total_bookings(self, room_id: str) -> int:
        """Get total number of bookings for a room."""
        try:
            result = await self._find_many(
                self._bookings_collection,
                {"room_id": room_id}
            )
            return len(result)
        except Exception:
            return 0
    
    async def get_active_bookings(self, room_id: str) -> int:
        """Get number of active bookings for a room."""
        try:
            result = await self._find_many(
                self._bookings_collection,
                {"room_id": room_id, "booking_status": "confirmed"}
            )
            return len(result)
        except Exception:
            return 0
    
    async def get_next_maintenance(self, room_id: str) -> Optional[datetime]:
        """Get next scheduled maintenance for a room."""
        try:
            maintenance = await self._find_one(
                self._maintenance_collection,
                {
                    "room_id": room_id,
                    "status": {"$in": ["scheduled", "in_progress"]}
                },
                sort=[("scheduled_date", 1)]
            )
            return maintenance['scheduled_date'] if maintenance else None
        except Exception:
            return None
    
    async def get_last_maintenance(self, room_id: str) -> Optional[datetime]:
        """Get last completed maintenance for a room."""
        try:
            maintenance = await self._find_one(
                self._maintenance_collection,
                {
                    "room_id": room_id,
                    "status": "completed"
                },
                sort=[("completion_date", -1)]
            )
            return maintenance['completion_date'] if maintenance else None
        except Exception:
            return None
    
    async def check_compliance(self, room_id: str) -> tuple:
        """Check if room is compliant with regulations."""
        try:
            # Get room
            room = await self.get_by_id(room_id)
            if not room:
                return False, 0.0
            
            # Check various compliance factors
            compliance_factors = {
                'room_type_compliance': room.room_type in ['lecture', 'lab', 'seminar', 'meeting', 'office'],
                'capacity_compliance': room.capacity >= 5,
                'equipment_compliance': len(room.equipment) >= 1,
                'safety_features_compliance': len(room.features) >= 2,
                'availability_compliance': await self._check_availability_compliance(room_id),
                'maintenance_compliance': await self._check_maintenance_compliance(room_id)
            }
            
            # Calculate compliance score
            compliant_factors = sum(1 for factor in compliance_factors.values() if factor)
            compliance_score = (compliant_factors / len(compliance_factors)) * 100
            
            return all(compliance_factors.values()), round(compliance_score, 2)
            
        except Exception:
            return False, 0.0
    
    # Helper Methods
    
    async def _validate_room_data(self, data: Dict[str, Any]) -> None:
        """Validate room data."""
        required_fields = ['name', 'room_code', 'building_id', 'floor', 'room_type', 'capacity', 'amenities', 'equipment', 'features', 'availability', 'usage_policy']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate floor
        if 'floor' in data and data['floor']:
            if data['floor'] < 1 or data['floor'] > 20:
                raise ValidationError("Floor must be between 1 and 20")
        
        # Validate capacity
        if 'capacity' in data and data['capacity']:
            if data['capacity'] < 1 or data['capacity'] > 500:
                raise ValidationError("Capacity must be between 1 and 500")
        
        # Validate room type
        valid_types = ['lecture', 'lab', 'seminar', 'office', 'meeting', 'storage']
        if 'room_type' in data and data['room_type']:
            if data['room_type'] not in valid_types:
                raise ValidationError(f"Invalid room type. Must be one of: {valid_types}")
        
        # Validate code uniqueness if provided
        if 'room_code' in data and data['room_code']:
            existing = await self._find_one(self._collection, {"room_code": data['room_code']}, limit=1)
            if existing:
                raise ValidationError("Room code already exists")
    
    async def _validate_booking_data(self, data: Dict[str, Any]) -> None:
        """Validate booking data."""
        required_fields = ['room_id', 'class_id', 'subject_id', 'teacher_id', 'start_time', 'end_time', 'booking_type', 'purpose', 'participants_count']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate time range
        if 'start_time' in data and 'end_time' in data:
            start_time = data['start_time']
            end_time = data['end_time']
            
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            
            if end_time <= start_time:
                raise ValidationError("End time must be after start time")
        
        # Validate participants count
        if 'participants_count' in data and data['participants_count']:
            if data['participants_count'] < 1 or data['participants_count'] > 500:
                raise ValidationError("Participants count must be between 1 and 500")
        
        # Validate priority
        if 'priority' in data and data['priority']:
            if data['priority'] < 1 or data['priority'] > 5:
                raise ValidationError("Priority must be between 1 and 5")
    
    async def _validate_maintenance_data(self, data: Dict[str, Any]) -> None:
        """Validate maintenance data."""
        required_fields = ['room_id', 'maintenance_type', 'description', 'scheduled_date', 'estimated_duration', 'maintenance_team', 'equipment_involved', 'cost_estimate', 'safety_measures']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate maintenance types
        valid_types = ['preventive', 'corrective', 'emergency']
        if data['maintenance_type'] not in valid_types:
            raise ValidationError(f"Invalid maintenance type. Must be one of: {valid_types}")
        
        # Validate duration
        if data['estimated_duration'] < 1:
            raise ValidationError("Estimated duration must be at least 1 hour")
        
        # Validate cost
        if data['cost_estimate'] < 0:
            raise ValidationError("Cost estimate must be non-negative")
    
    def _parse_time_slot(self, time_slot: str) -> tuple:
        """Parse time slot string into start and end times."""
        try:
            start_str, end_str = time_slot.split('-')
            start_time = datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.strptime(end_str, "%H:%M").time()
            return start_time, end_time
        except Exception:
            return None, None
    
    def _time_ranges_overlap(self, start1, end1, start2, end2) -> bool:
        """Check if two time ranges overlap."""
        return (start1 < end2) and (start2 < end1)
    
    def _generate_conflict_message(self, conflicts: List[Dict[str, Any]]) -> str:
        """Generate conflict message."""
        if not conflicts:
            return "No conflicts"
        
        return f"{len(conflicts)} booking conflict(s) found"
    
    async def _calculate_utilization_rate(self, room_id: str, start_date: datetime, end_date: datetime) -> float:
        """Calculate utilization rate for a room."""
        if not start_date or not end_date:
            return 0.0
        
        # Get total hours in the period
        total_hours = (end_date - start_date).days * 24
        
        # Get confirmed bookings
        bookings = await self.get_room_bookings(
            room_id=room_id,
            start_date=start_date,
            end_date=end_date,
            booking_status="confirmed"
        )
        
        # Calculate booked hours
        booked_hours = sum(
            (b.end_time - b.start_time).total_seconds() / 3600 
            for b in bookings
        )
        
        return (booked_hours / total_hours) * 100 if total_hours > 0 else 0.0
    
    async def _calculate_peak_hours(self, room_id: str, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate peak utilization hours."""
        # This would analyze bookings by hour of day
        # For now, return empty dict
        return {}
    
    async def _calculate_equipment_utilization(self, room_id: str, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate equipment utilization."""
        # This would analyze equipment usage
        # For now, return empty dict
        return {}
    
    async def _calculate_maintenance_frequency(self, room_id: str) -> float:
        """Calculate maintenance frequency per month."""
        try:
            # Get maintenance records for the last year
            one_year_ago = datetime.utcnow() - timedelta(days=365)
            maintenance = await self.get_maintenance_records(
                room_id=room_id,
                maintenance_type="preventive"
            )
            
            # Count monthly maintenance
            monthly_maintenance = {}
            for record in maintenance:
                month_key = record['scheduled_date'].strftime("%Y-%m")
                monthly_maintenance[month_key] = monthly_maintenance.get(month_key, 0) + 1
            
            # Calculate average per month
            if monthly_maintenance:
                return sum(monthly_maintenance.values()) / len(monthly_maintenance)
            return 0.0
            
        except Exception:
            return 0.0
    
    async def _calculate_compliance_score(self, room_id: str) -> float:
        """Calculate compliance score."""
        is_compliant, score = await self.check_compliance(room_id)
        return score
    
    async def _calculate_cancellation_rate(self, room_id: str) -> float:
        """Calculate cancellation rate."""
        try:
            total_bookings = await self.get_total_bookings(room_id)
            cancelled_bookings = await self.get_room_bookings(
                room_id=room_id,
                booking_status="cancelled"
            )
            
            return (len(cancelled_bookings) / total_bookings) * 100 if total_bookings > 0 else 0.0
            
        except Exception:
            return 0.0
    
    async def _calculate_reschedule_rate(self, room_id: str) -> float:
        """Calculate reschedule rate."""
        # This would analyze booking modifications
        return 0.0
    
    async def _get_popular_equipment(self, room_id: str, start_date: datetime, end_date: datetime) -> List[str]:
        """Get most popular equipment."""
        # This would analyze equipment usage
        return []
    
    async def _get_waiting_list_stats(self, room_id: str) -> Dict[str, int]:
        """Get waiting list statistics."""
        try:
            waiting_list = await self.get_waiting_list(room_id)
            
            return {
                "total_waiting": len(waiting_list),
                "high_priority": len([w for w in waiting_list if w.get('priority', 1) >= 3]),
                "medium_priority": len([w for w in waiting_list if w.get('priority', 1) == 2]),
                "low_priority": len([w for w in waiting_list if w.get('priority', 1) == 1])
            }
            
        except Exception:
            return {"total_waiting": 0, "high_priority": 0, "medium_priority": 0, "low_priority": 0}
    
    async def _get_equipment_availability(self, room_id: str) -> Dict[str, Any]:
        """Get equipment availability status."""
        try:
            room = await self.get_by_id(room_id)
            if not room or not room.equipment:
                return {}
            
            availability = {}
            for equipment_name, equipment_info in room.equipment.items():
                availability[equipment_name] = {
                    "available": True,  # This would need more sophisticated logic
                    "quantity": equipment_info.get('quantity', 1),
                    "condition": equipment_info.get('condition', 'good')
                }
            
            return availability
            
        except Exception:
            return {}
    
    async def _get_maintenance_periods(self, room_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get maintenance periods within date range."""
        try:
            if not start_date or not end_date:
                return []
            
            maintenance = await self.get_maintenance_records(
                room_id=room_id,
                status="scheduled"
            )
            
            periods = []
            for record in maintenance:
                record_date = record['scheduled_date'].date()
                if start_date.date() <= record_date <= end_date.date():
                    periods.append({
                        "start_date": record_date,
                        "end_date": record_date,
                        "type": record['maintenance_type'],
                        "description": record['description']
                    })
            
            return periods
            
        except Exception:
            return []
    
    async def _check_availability_compliance(self, room_id: str) -> bool:
        """Check availability compliance."""
        # This would check if room meets minimum availability requirements
        return True
    
    async def _check_maintenance_compliance(self, room_id: str) -> bool:
        """Check maintenance compliance."""
        # This would check maintenance schedules and procedures
        return True