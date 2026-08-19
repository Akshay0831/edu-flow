"""
Laboratory Management Repository

This module provides database operations for laboratory management:
- CRUD operations for laboratories
- Laboratory booking and scheduling
- Equipment management and maintenance
- Laboratory analytics and reporting
- Resource allocation and optimization
- Compliance tracking

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, time, date, timedelta
from uuid import uuid4

from core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from core.logging import get_logger
from core.database_abstraction import DatabaseManager, DatabaseInterface
from infrastructure.repositories.base_repository import BaseRepository, QueryResult, RepositoryOperation
from models.laboratory import (
    LabCreate as LaboratoryCreate, LabUpdate as LaboratoryUpdate, LabResponse as LaboratoryResponse,
    LaboratoryBooking, LaboratoryBookingResponse,
    LaboratoryEquipment, LaboratoryMaintenance,
    LabStats as LaboratoryStats, LaboratoryConflict, ResourceAllocation
)

logger = get_logger(__name__)


class LaboratoryRepository(BaseRepository):
    """Laboratory management repository with comprehensive functionality."""
    
    def __init__(self, database_manager: DatabaseManager = None):
        super().__init__()
        self._database = database_manager.get_database() if database_manager else None
        self._collection = "laboratories"
        self._bookings_collection = "laboratory_bookings"
        self._equipment_collection = "laboratory_equipment"
        self._maintenance_collection = "laboratory_maintenance"
        self._conflicts_collection = "laboratory_conflicts"
    
    # Core CRUD Operations
    
    async def get_by_id(self, laboratory_id: str) -> Optional[LaboratoryResponse]:
        """Get a laboratory by ID."""
        try:
            result = await self._find_one(self._collection, {"laboratory_id": laboratory_id})
            if result:
                return LaboratoryResponse(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting laboratory by ID {laboratory_id}: {str(e)}")
            raise DatabaseError(f"Failed to get laboratory: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100, 
                     filters: Dict[str, Any] = None) -> List[LaboratoryResponse]:
        """Get all laboratories with optional filtering."""
        try:
            query_filter = filters or {}
            result = await self._find_many(
                self._collection, 
                query_filter,
                skip=skip,
                limit=limit,
                sort=[("created_at", -1)]
            )
            
            return [LaboratoryResponse(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting all laboratories: {str(e)}")
            raise DatabaseError(f"Failed to fetch laboratories: {str(e)}")
    
    async def create(self, **data) -> LaboratoryResponse:
        """Create a new laboratory."""
        try:
            # Add required fields
            if 'laboratory_id' not in data:
                data['laboratory_id'] = str(uuid4())
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow()
            if 'updated_at' not in data:
                data['updated_at'] = datetime.utcnow()
            
            # Validate laboratory data
            await self._validate_laboratory_data(data)
            
            # Insert into database
            result = await self._insert(self._collection, data)
            if result.inserted_id:
                created_laboratory = await self.get_by_id(data['laboratory_id'])
                return created_laboratory
            else:
                raise DatabaseError("Failed to create laboratory")
                
        except Exception as e:
            logger.error(f"Error creating laboratory: {str(e)}")
            raise DatabaseError(f"Failed to create laboratory: {str(e)}")
    
    async def update(self, laboratory_id: str, **data) -> Optional[LaboratoryResponse]:
        """Update an existing laboratory."""
        try:
            # Update timestamps
            data['updated_at'] = datetime.utcnow()
            
            # Validate updated laboratory data
            await self._validate_laboratory_data(data)
            
            # Update in database
            result = await self._update(
                self._collection,
                {"laboratory_id": laboratory_id},
                {"$set": data}
            )
            
            if result.modified_count > 0:
                updated_laboratory = await self.get_by_id(laboratory_id)
                return updated_laboratory
            else:
                raise NotFoundError(f"Laboratory not found with ID: {laboratory_id}")
                
        except Exception as e:
            logger.error(f"Error updating laboratory {laboratory_id}: {str(e)}")
            raise DatabaseError(f"Failed to update laboratory: {str(e)}")
    
    async def delete(self, laboratory_id: str) -> bool:
        """Delete a laboratory and related data."""
        try:
            # Check if laboratory has active bookings
            has_active_bookings = await self.has_active_bookings(laboratory_id)
            if has_active_bookings:
                raise ValidationError("Cannot delete laboratory with active bookings")
            
            # Delete the laboratory
            result = await self._delete(self._collection, {"laboratory_id": laboratory_id})
            
            if result.deleted_count > 0:
                # Delete related data
                await self._delete(self._bookings_collection, {"laboratory_id": laboratory_id})
                await self._delete(self._equipment_collection, {"laboratory_id": laboratory_id})
                await self._delete(self._maintenance_collection, {"laboratory_id": laboratory_id})
                await self._delete(self._conflicts_collection, {"laboratory_id": laboratory_id})
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error deleting laboratory {laboratory_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete laboratory: {str(e)}")
    
    # Laboratory-specific Operations
    
    async def validate_laboratory(self, laboratory_id: str) -> bool:
        """Validate that a laboratory exists."""
        try:
            laboratory = await self._find_one(self._collection, {"laboratory_id": laboratory_id}, limit=1)
            return laboratory is not None
        except Exception:
            return False
    
    async def validate_code(self, code: str) -> bool:
        """Validate that a laboratory code is unique."""
        try:
            existing = await self._find_one(self._collection, {"code": code}, limit=1)
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
    
    async def get_laboratory_stats(self, laboratory_id: str, start_date: date = None, end_date: date = None) -> LaboratoryStats:
        """Get statistics for a laboratory."""
        try:
            # Get the laboratory
            laboratory = await self.get_by_id(laboratory_id)
            if not laboratory:
                raise NotFoundError(f"Laboratory not found with ID: {laboratory_id}")
            
            # Get bookings for the date range
            bookings = await self.get_laboratory_bookings(
                laboratory_id=laboratory_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Calculate statistics
            stats = LaboratoryStats(
                laboratory_id=laboratory_id,
                laboratory_name=laboratory.name,
                total_bookings=len(bookings),
                active_bookings=len([b for b in bookings if b.booking_status == "confirmed"]),
                average_utilization=await self._calculate_utilization_rate(laboratory_id, start_date, end_date),
                peak_utilization_hours=await self._calculate_peak_hours(laboratory_id, start_date, end_date),
                equipment_utilization=await self._calculate_equipment_utilization(laboratory_id, start_date, end_date),
                maintenance_frequency=await self._calculate_maintenance_frequency(laboratory_id),
                compliance_score=await self._calculate_compliance_score(laboratory_id),
                safety_incidents_count=await self._get_safety_incidents(laboratory_id),
                reschedule_rate=await self._calculate_reschedule_rate(laboratory_id),
                cancellation_rate=await self._calculate_cancellation_rate(laboratory_id),
                popular_equipment=await self._get_popular_equipment(laboratory_id, start_date, end_date)
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting laboratory stats for {laboratory_id}: {str(e)}")
            raise DatabaseError(f"Failed to get laboratory stats: {str(e)}")
    
    async def get_laboratory_availability(self, laboratory_id: str, start_date: date = None, 
                                        end_date: date = None, time_slot: str = None) -> Dict[str, Any]:
        """Get laboratory availability information."""
        try:
            laboratory = await self.get_by_id(laboratory_id)
            if not laboratory:
                raise NotFoundError(f"Laboratory not found with ID: {laboratory_id}")
            
            # Get bookings for the specified date range
            bookings = await self.get_laboratory_bookings(
                laboratory_id=laboratory_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Calculate availability
            availability = {
                "laboratory_id": laboratory_id,
                "laboratory_name": laboratory.name,
                "laboratory_capacity": laboratory.capacity,
                "current_date": datetime.utcnow().date(),
                "requested_range": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "time_slot": time_slot
                },
                "availability_status": "available",
                "unavailable_periods": [],
                "equipment_status": await self._get_equipment_availability(laboratory_id),
                "maintenance_periods": await self._get_maintenance_periods(laboratory_id, start_date, end_date),
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
            logger.error(f"Error getting laboratory availability for {laboratory_id}: {str(e)}")
            raise DatabaseError(f"Failed to get laboratory availability: {str(e)}")
    
    # Booking Management
    
    async def create_booking(self, **data) -> LaboratoryBookingResponse:
        """Create a laboratory booking."""
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
                raise DatabaseError("Failed to create laboratory booking")
                
        except Exception as e:
            logger.error(f"Error creating laboratory booking: {str(e)}")
            raise DatabaseError(f"Failed to create laboratory booking: {str(e)}")
    
    async def get_laboratory_bookings(self, laboratory_id: str, skip: int = 0, limit: int = 100,
                                    booking_status: str = None, start_date: datetime = None,
                                    end_date: datetime = None, booking_type: str = None,
                                    teacher_id: str = None, class_id: str = None,
                                    search: str = None) -> List[LaboratoryBookingResponse]:
        """Get laboratory bookings with optional filtering."""
        try:
            query_filter = {"laboratory_id": laboratory_id}
            
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
            
            return [LaboratoryBookingResponse(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting laboratory bookings: {str(e)}")
            raise DatabaseError(f"Failed to fetch laboratory bookings: {str(e)}")
    
    async def get_booking_by_id(self, booking_id: str) -> Optional[LaboratoryBookingResponse]:
        """Get a laboratory booking by ID."""
        try:
            result = await self._find_one(self._bookings_collection, {"booking_id": booking_id})
            if result:
                return LaboratoryBookingResponse(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting laboratory booking by ID {booking_id}: {str(e)}")
            raise DatabaseError(f"Failed to get laboratory booking: {str(e)}")
    
    async def confirm_booking(self, booking_id: str, confirmed_by_id: str = None, 
                            confirmation_notes: str = None) -> bool:
        """Confirm a laboratory booking."""
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
        """Cancel a laboratory booking."""
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
    
    async def has_active_bookings(self, laboratory_id: str) -> bool:
        """Check if a laboratory has active bookings."""
        try:
            result = await self._find_one(
                self._bookings_collection,
                {"laboratory_id": laboratory_id, "booking_status": "confirmed"}
            )
            return result is not None
        except Exception:
            return False
    
    async def check_booking_conflicts(self, laboratory_id: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Check for booking conflicts."""
        try:
            query_filter = {
                "laboratory_id": laboratory_id,
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
    
    async def check_capacity_availability(self, laboratory_id: str, participants_count: int) -> bool:
        """Check if laboratory has capacity for the required number of participants."""
        try:
            laboratory = await self.get_by_id(laboratory_id)
            if not laboratory:
                return False
            
            # Check if the request exceeds laboratory capacity
            return participants_count <= laboratory.capacity
            
        except Exception:
            return False
    
    async def check_equipment_availability(self, laboratory_id: str, equipment_required: List[str]) -> bool:
        """Check if required equipment is available."""
        try:
            if not equipment_required:
                return True
            
            # Get laboratory equipment
            equipment = await self._find_many(
                self._equipment_collection,
                {"laboratory_id": laboratory_id, "is_available": True}
            )
            
            available_equipment = [eq['equipment_name'] for eq in equipment]
            
            # Check if all required equipment is available
            for required in equipment_required:
                if required not in available_equipment:
                    return False
            
            return True
            
        except Exception:
            return False
    
    # Equipment Management
    
    async def add_equipment(self, laboratory_id: str, equipment_data: Dict[str, Any]) -> bool:
        """Add equipment to a laboratory."""
        try:
            # Validate laboratory
            if not await self.validate_laboratory(laboratory_id):
                raise NotFoundError(f"Laboratory not found with ID: {laboratory_id}")
            
            # Add equipment ID if not provided
            if 'equipment_id' not in equipment_data:
                equipment_data['equipment_id'] = str(uuid4())
            
            # Add timestamp
            equipment_data['created_at'] = datetime.utcnow()
            equipment_data['updated_at'] = datetime.utcnow()
            
            # Insert equipment
            result = await self._insert(self._equipment_collection, equipment_data)
            
            return result.inserted_id is not None
            
        except Exception as e:
            logger.error(f"Error adding equipment to laboratory {laboratory_id}: {str(e)}")
            raise DatabaseError(f"Failed to add equipment: {str(e)}")
    
    async def get_laboratory_equipment(self, laboratory_id: str) -> List[LaboratoryEquipment]:
        """Get all equipment for a laboratory."""
        try:
            result = await self._find_many(
                self._equipment_collection,
                {"laboratory_id": laboratory_id},
                sort=[("equipment_name", 1)]
            )
            
            return [LaboratoryEquipment(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting laboratory equipment: {str(e)}")
            raise DatabaseError(f"Failed to fetch laboratory equipment: {str(e)}")
    
    # Maintenance Management
    
    async def schedule_maintenance(self, **data) -> LaboratoryMaintenance:
        """Schedule maintenance for a laboratory."""
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
    
    async def get_maintenance_records(self, laboratory_id: str, skip: int = 0, limit: int = 100,
                                   maintenance_type: str = None, status: str = None) -> List[LaboratoryMaintenance]:
        """Get maintenance records for a laboratory."""
        try:
            query_filter = {"laboratory_id": laboratory_id}
            
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
            
            return [LaboratoryMaintenance(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting maintenance records: {str(e)}")
            raise DatabaseError(f"Failed to fetch maintenance records: {str(e)}")
    
    async def get_maintenance_by_id(self, maintenance_id: str) -> Optional[LaboratoryMaintenance]:
        """Get a maintenance record by ID."""
        try:
            result = await self._find_one(self._maintenance_collection, {"maintenance_id": maintenance_id})
            if result:
                return LaboratoryMaintenance(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting maintenance record by ID {maintenance_id}: {str(e)}")
            raise DatabaseError(f"Failed to get maintenance record: {str(e)}")
    
    # Analytics and Monitoring
    
    async def get_current_utilization(self, laboratory_id: str) -> float:
        """Get current utilization percentage for a laboratory."""
        try:
            # Get current date and time
            now = datetime.utcnow()
            today = now.date()
            
            # Get today's bookings
            today_bookings = await self.get_laboratory_bookings(
                laboratory_id=laboratory_id,
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
    
    async def get_total_bookings(self, laboratory_id: str) -> int:
        """Get total number of bookings for a laboratory."""
        try:
            result = await self._find_many(
                self._bookings_collection,
                {"laboratory_id": laboratory_id}
            )
            return len(result)
        except Exception:
            return 0
    
    async def get_active_bookings(self, laboratory_id: str) -> int:
        """Get number of active bookings for a laboratory."""
        try:
            result = await self._find_many(
                self._bookings_collection,
                {"laboratory_id": laboratory_id, "booking_status": "confirmed"}
            )
            return len(result)
        except Exception:
            return 0
    
    async def get_next_maintenance(self, laboratory_id: str) -> Optional[datetime]:
        """Get next scheduled maintenance for a laboratory."""
        try:
            maintenance = await self._find_one(
                self._maintenance_collection,
                {
                    "laboratory_id": laboratory_id,
                    "status": {"$in": ["scheduled", "in_progress"]}
                },
                sort=[("scheduled_date", 1)]
            )
            return maintenance['scheduled_date'] if maintenance else None
        except Exception:
            return None
    
    async def get_last_maintenance(self, laboratory_id: str) -> Optional[datetime]:
        """Get last completed maintenance for a laboratory."""
        try:
            maintenance = await self._find_one(
                self._maintenance_collection,
                {
                    "laboratory_id": laboratory_id,
                    "status": "completed"
                },
                sort=[("completion_date", -1)]
            )
            return maintenance['completion_date'] if maintenance else None
        except Exception:
            return None
    
    async def check_compliance(self, laboratory_id: str) -> tuple:
        """Check if laboratory is compliant with regulations."""
        try:
            # Get laboratory
            laboratory = await self.get_by_id(laboratory_id)
            if not laboratory:
                return False, 0.0
            
            # Check various compliance factors
            compliance_factors = {
                'safety_features_compliance': len(laboratory.safety_features) >= 3,
                'equipment_maintenance': await self._check_equipment_maintenance(laboratory_id),
                'capacity_compliance': laboratory.capacity >= 10,
                'availability_compliance': await self._check_availability_compliance(laboratory_id),
                'booking_compliance': await self._check_booking_compliance(laboratory_id)
            }
            
            # Calculate compliance score
            compliant_factors = sum(1 for factor in compliance_factors.values() if factor)
            compliance_score = (compliant_factors / len(compliance_factors)) * 100
            
            return all(compliance_factors.values()), round(compliance_score, 2)
            
        except Exception:
            return False, 0.0
    
    # Helper Methods
    
    async def _validate_laboratory_data(self, data: Dict[str, Any]) -> None:
        """Validate laboratory data."""
        required_fields = ['name', 'code', 'building_id', 'floor', 'capacity', 'equipment', 'amenities', 'safety_features', 'operating_hours', 'usage_policy']
        
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
        
        # Validate code uniqueness if provided
        if 'code' in data and data['code']:
            existing = await self._find_one(self._collection, {"code": data['code']}, limit=1)
            if existing:
                raise ValidationError("Laboratory code already exists")
    
    async def _validate_booking_data(self, data: Dict[str, Any]) -> None:
        """Validate booking data."""
        required_fields = ['laboratory_id', 'class_id', 'subject_id', 'teacher_id', 'start_time', 'end_time', 'booking_type', 'purpose', 'participants_count']
        
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
        required_fields = ['laboratory_id', 'maintenance_type', 'description', 'scheduled_date', 'estimated_duration', 'maintenance_team', 'equipment_involved', 'cost_estimate', 'safety_measures']
        
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
    
    async def _calculate_utilization_rate(self, laboratory_id: str, start_date: date, end_date: date) -> float:
        """Calculate utilization rate for a laboratory."""
        if not start_date or not end_date:
            return 0.0
        
        # Get total hours in the period
        total_hours = (end_date - start_date).days * 24
        
        # Get confirmed bookings
        bookings = await self.get_laboratory_bookings(
            laboratory_id=laboratory_id,
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
    
    async def _calculate_peak_hours(self, laboratory_id: str, start_date: date, end_date: date) -> Dict[str, float]:
        """Calculate peak utilization hours."""
        # This would analyze bookings by hour of day
        # For now, return empty dict
        return {}
    
    async def _calculate_equipment_utilization(self, laboratory_id: str, start_date: date, end_date: date) -> Dict[str, float]:
        """Calculate equipment utilization."""
        # This would analyze equipment usage
        # For now, return empty dict
        return {}
    
    async def _calculate_maintenance_frequency(self, laboratory_id: str) -> float:
        """Calculate maintenance frequency per month."""
        try:
            # Get maintenance records for the last year
            one_year_ago = datetime.utcnow() - timedelta(days=365)
            maintenance = await self.get_maintenance_records(
                laboratory_id=laboratory_id,
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
    
    async def _calculate_compliance_score(self, laboratory_id: str) -> float:
        """Calculate compliance score."""
        is_compliant, score = await self.check_compliance(laboratory_id)
        return score
    
    async def _get_safety_incidents(self, laboratory_id: str) -> int:
        """Get number of safety incidents."""
        # This would query incidents collection
        return 0
    
    async def _calculate_reschedule_rate(self, laboratory_id: str) -> float:
        """Calculate reschedule rate."""
        # This would analyze booking modifications
        return 0.0
    
    async def _calculate_cancellation_rate(self, laboratory_id: str) -> float:
        """Calculate cancellation rate."""
        try:
            total_bookings = await self.get_total_bookings(laboratory_id)
            cancelled_bookings = await self.get_laboratory_bookings(
                laboratory_id=laboratory_id,
                booking_status="cancelled"
            )
            
            return (len(cancelled_bookings) / total_bookings) * 100 if total_bookings > 0 else 0.0
            
        except Exception:
            return 0.0
    
    async def _get_popular_equipment(self, laboratory_id: str, start_date: date, end_date: date) -> List[str]:
        """Get most popular equipment."""
        # This would analyze equipment usage
        return []
    
    async def _get_equipment_availability(self, laboratory_id: str) -> Dict[str, Any]:
        """Get equipment availability status."""
        try:
            equipment = await self.get_laboratory_equipment(laboratory_id)
            availability = {}
            
            for item in equipment:
                availability[item.equipment_name] = {
                    "available": item.is_available,
                    "condition": item.condition,
                    "quantity": item.quantity
                }
            
            return availability
            
        except Exception:
            return {}
    
    async def _get_maintenance_periods(self, laboratory_id: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get maintenance periods within date range."""
        try:
            if not start_date or not end_date:
                return []
            
            maintenance = await self.get_maintenance_records(
                laboratory_id=laboratory_id,
                status="scheduled"
            )
            
            periods = []
            for record in maintenance:
                record_date = record['scheduled_date'].date()
                if start_date <= record_date <= end_date:
                    periods.append({
                        "start_date": record_date,
                        "end_date": record_date,
                        "type": record['maintenance_type'],
                        "description": record['description']
                    })
            
            return periods
            
        except Exception:
            return []
    
    async def _check_equipment_maintenance(self, laboratory_id: str) -> bool:
        """Check if equipment is properly maintained."""
        try:
            equipment = await self.get_laboratory_equipment(laboratory_id)
            
            # Check if equipment has maintenance records
            for item in equipment:
                if item.next_maintenance and item.next_maintenance < datetime.utcnow():
                    return False
            
            return True
            
        except Exception:
            return True
    
    async def _check_availability_compliance(self, laboratory_id: str) -> bool:
        """Check availability compliance."""
        # This would check if laboratory meets minimum availability requirements
        return True
    
    async def _check_booking_compliance(self, laboratory_id: str) -> bool:
        """Check booking compliance."""
        # This would check booking policies and procedures
        return True