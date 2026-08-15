"""
Laboratory Management Service

This module provides business logic for laboratory management:
- Laboratory booking and scheduling
- Equipment management
- Resource allocation
- Utilization analytics
- Maintenance scheduling
- Compliance checking

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, time, timedelta
from uuid import uuid4

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.core.logging import get_logger
from src.core.base_service import BaseService
from src.infrastructure.repositories.laboratory_repository import LaboratoryRepository
from src.models.laboratory import (
    LabCreate as LaboratoryCreate, LabUpdate as LaboratoryUpdate, LabResponse as LaboratoryResponse,
    LabStats as LaboratoryStats, EquipmentResponse as Equipment
)

logger = get_logger(__name__)


class LaboratoryService(BaseService):
    """Laboratory management service with comprehensive functionality."""
    
    def __init__(self, laboratory_repository: LaboratoryRepository):
        super().__init__(laboratory_repository)
        self._cache = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the laboratory service."""
        try:
            self._initialized = True
            logger.info("Laboratory service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize laboratory service: {str(e)}")
            raise
    
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized
    
    async def dispose(self) -> None:
        """Dispose the laboratory service."""
        try:
            self._cache.clear()
            logger.info("Laboratory service disposed successfully")
        except Exception as e:
            logger.error(f"Failed to dispose laboratory service: {str(e)}")
            raise
    
    # Core Business Operations
    
    async def create_laboratory(self, lab_data: Dict[str, Any]) -> LaboratoryResponse:
        """Create a new laboratory with business logic validation."""
        try:
            # Validate laboratory data
            await self._validate_laboratory_creation(lab_data)
            
            # Create laboratory
            laboratory = await self.laboratory_repository.create(**lab_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return laboratory
            
        except Exception as e:
            logger.error(f"Failed to create laboratory: {str(e)}")
            raise
    
    async def update_laboratory(self, lab_id: str, lab_data: Dict[str, Any]) -> Optional[LaboratoryResponse]:
        """Update an existing laboratory with business logic."""
        try:
            # Validate laboratory exists
            laboratory = await self.laboratory_repository.get_by_id(lab_id)
            if not laboratory:
                raise NotFoundError(f"Laboratory not found with ID: {lab_id}")
            
            # Validate update data
            await self._validate_laboratory_update(lab_data)
            
            # Check if name is being changed and conflicts exist
            if 'name' in lab_data and lab_data['name'] != laboratory.name:
                existing_lab = await self.laboratory_repository.get_by_name(lab_data['name'])
                if existing_lab:
                    raise ConflictError(f"Laboratory with name '{lab_data['name']}' already exists")
            
            # Update laboratory
            updated_laboratory = await self.laboratory_repository.update(lab_id, **lab_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return updated_laboratory
            
        except Exception as e:
            logger.error(f"Failed to update laboratory {lab_id}: {str(e)}")
            raise
    
    async def get_laboratory(self, lab_id: str) -> Optional[LaboratoryResponse]:
        """Get a laboratory by ID with caching."""
        try:
            # Check cache first
            if lab_id in self._cache:
                return self._cache[lab_id]
            
            # Get laboratory from repository
            laboratory = await self.laboratory_repository.get_by_id(lab_id)
            
            if laboratory:
                # Cache the result
                self._cache[lab_id] = laboratory
            
            return laboratory
            
        except Exception as e:
            logger.error(f"Failed to get laboratory {lab_id}: {str(e)}")
            raise
    
    async def delete_laboratory(self, lab_id: str) -> bool:
        """Delete a laboratory with business logic."""
        try:
            # Validate laboratory exists
            laboratory = await self.laboratory_repository.get_by_id(lab_id)
            if not laboratory:
                raise NotFoundError(f"Laboratory not found with ID: {lab_id}")
            
            # Check if laboratory has active bookings
            if await self._has_active_bookings(lab_id):
                raise ValidationError("Cannot delete laboratory with active bookings")
            
            # Check if laboratory has equipment
            if laboratory.equipment:
                raise ValidationError("Cannot delete laboratory with equipment")
            
            # Check if laboratory has been used recently
            if await self._was_recently_used(lab_id):
                raise ValidationError("Cannot delete laboratory that was recently used")
            
            # Delete laboratory
            result = await self.laboratory_repository.delete(lab_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete laboratory {lab_id}: {str(e)}")
            raise
    
    # Search and Filtering
    
    async def search_laboratories(self, search_term: str, skip: int = 0, limit: int = 100) -> List[LaboratoryResponse]:
        """Search for laboratories by name, department, or type."""
        try:
            laboratories = await self.laboratory_repository.search_laboratories(
                search_term=search_term,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for lab in laboratories:
                self._cache[lab.id] = lab
            
            return laboratories
            
        except Exception as e:
            logger.error(f"Failed to search laboratories: {str(e)}")
            raise
    
    async def get_laboratories_by_department(self, department_id: str, skip: int = 0, limit: int = 100) -> List[LaboratoryResponse]:
        """Get laboratories for a department."""
        try:
            laboratories = await self.laboratory_repository.get_by_department(
                department_id=department_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for lab in laboratories:
                self._cache[lab.id] = lab
            
            return laboratories
            
        except Exception as e:
            logger.error(f"Failed to get laboratories for department {department_id}: {str(e)}")
            raise
    
    async def get_laboratories_by_type(self, lab_type: str, skip: int = 0, limit: int = 100) -> List[LaboratoryResponse]:
        """Get laboratories by type."""
        try:
            laboratories = await self.laboratory_repository.get_by_type(
                lab_type=lab_type,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for lab in laboratories:
                self._cache[lab.id] = lab
            
            return laboratories
            
        except Exception as e:
            logger.error(f"Failed to get laboratories by type {lab_type}: {str(e)}")
            raise
    
    async def get_laboratories_by_capacity(self, min_capacity: int, max_capacity: int = None) -> List[LaboratoryResponse]:
        """Get laboratories by capacity range."""
        try:
            laboratories = await self.laboratory_repository.get_by_capacity(
                min_capacity=min_capacity,
                max_capacity=max_capacity
            )
            
            # Cache results
            for lab in laboratories:
                self._cache[lab.id] = lab
            
            return laboratories
            
        except Exception as e:
            logger.error(f"Failed to get laboratories by capacity: {str(e)}")
            raise
    
    # Booking and Scheduling
    
    async def book_laboratory(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Book a laboratory for use."""
        try:
            # Validate booking data
            await self._validate_booking_data(booking_data)
            
            # Check laboratory availability
            if not await self._is_laboratory_available(
                booking_data['laboratory_id'],
                booking_data['start_date'],
                booking_data['end_date']
            ):
                raise ConflictError("Laboratory is not available for the requested time")
            
            # Check equipment availability
            if not await self._is_equipment_available(
                booking_data['laboratory_id'],
                booking_data['equipment_needed']
            ):
                raise ConflictError("Required equipment is not available")
            
            # Create booking
            booking = await self.laboratory_repository.create_booking(**booking_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return booking
            
        except Exception as e:
            logger.error(f"Failed to book laboratory: {str(e)}")
            raise
    
    async def cancel_booking(self, booking_id: str) -> bool:
        """Cancel a laboratory booking."""
        try:
            # Validate booking exists
            booking = await self.laboratory_repository.get_booking_by_id(booking_id)
            if not booking:
                raise NotFoundError(f"Booking not found with ID: {booking_id}")
            
            # Check if booking can be cancelled (not started and not in the past)
            if not await self._can_cancel_booking(booking):
                raise ValidationError("Cannot cancel booking that has already started or is in the past")
            
            # Cancel booking
            result = await self.laboratory_repository.cancel_booking(booking_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to cancel booking {booking_id}: {str(e)}")
            raise
    
    async def get_laboratory_availability(self, lab_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get laboratory availability for a date range."""
        try:
            # Get laboratory
            laboratory = await self.get_laboratory(lab_id)
            if not laboratory:
                raise NotFoundError(f"Laboratory not found with ID: {lab_id}")
            
            # Get existing bookings
            bookings = await self.laboratory_repository.get_bookings_by_date_range(
                laboratory_id=lab_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Calculate availability
            availability = self._calculate_availability(laboratory, bookings, start_date, end_date)
            
            return {
                "laboratory_id": lab_id,
                "laboratory_name": laboratory.name,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "availability": availability,
                "total_hours": len(availability) * 8,  # Assuming 8-hour workday
                "available_hours": len([a for a in availability if a['available']]) * 8,
                "utilization_rate": round((1 - len([a for a in availability if a['available']]) / len(availability)) * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get laboratory availability for {lab_id}: {str(e)}")
            raise
    
    async def get_booking_history(self, lab_id: str, start_date: date = None, end_date: date = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get booking history for a laboratory."""
        try:
            return await self.laboratory_repository.get_booking_history(
                laboratory_id=lab_id,
                start_date=start_date,
                end_date=end_date,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get booking history for laboratory {lab_id}: {str(e)}")
            raise
    
    # Equipment Management
    
    async def add_equipment(self, lab_id: str, equipment_data: Dict[str, Any]) -> Equipment:
        """Add equipment to a laboratory."""
        try:
            # Validate laboratory exists
            laboratory = await self.get_laboratory(lab_id)
            if not laboratory:
                raise NotFoundError(f"Laboratory not found with ID: {lab_id}")
            
            # Validate equipment data
            await self._validate_equipment_data(equipment_data)
            
            # Add equipment
            equipment = await self.laboratory_repository.add_equipment(
                laboratory_id=lab_id,
                **equipment_data
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return equipment
            
        except Exception as e:
            logger.error(f"Failed to add equipment to laboratory {lab_id}: {str(e)}")
            raise
    
    async def update_equipment(self, lab_id: str, equipment_id: str, equipment_data: Dict[str, Any]) -> Optional[Equipment]:
        """Update equipment in a laboratory."""
        try:
            # Validate laboratory exists
            laboratory = await self.get_laboratory(lab_id)
            if not laboratory:
                raise NotFoundError(f"Laboratory not found with ID: {lab_id}")
            
            # Validate equipment exists
            existing_equipment = await self.laboratory_repository.get_equipment_by_id(equipment_id)
            if not existing_equipment:
                raise NotFoundError(f"Equipment not found with ID: {equipment_id}")
            
            # Validate equipment data
            await self._validate_equipment_update(equipment_data)
            
            # Update equipment
            updated_equipment = await self.laboratory_repository.update_equipment(
                laboratory_id=lab_id,
                equipment_id=equipment_id,
                **equipment_data
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return updated_equipment
            
        except Exception as e:
            logger.error(f"Failed to update equipment {equipment_id} in laboratory {lab_id}: {str(e)}")
            raise
    
    async def remove_equipment(self, lab_id: str, equipment_id: str) -> bool:
        """Remove equipment from a laboratory."""
        try:
            # Validate laboratory exists
            laboratory = await self.get_laboratory(lab_id)
            if not laboratory:
                raise NotFoundError(f"Laboratory not found with ID: {lab_id}")
            
            # Validate equipment exists
            equipment = await self.laboratory_repository.get_equipment_by_id(equipment_id)
            if not equipment:
                raise NotFoundError(f"Equipment not found with ID: {equipment_id}")
            
            # Check if equipment is booked
            if await self._is_equipment_booked(equipment_id):
                raise ValidationError("Cannot remove equipment that is currently booked")
            
            # Remove equipment
            result = await self.laboratory_repository.remove_equipment(
                laboratory_id=lab_id,
                equipment_id=equipment_id
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to remove equipment {equipment_id} from laboratory {lab_id}: {str(e)}")
            raise
    
    async def get_equipment_maintenance_schedule(self, lab_id: str) -> List[Dict[str, Any]]:
        """Get maintenance schedule for laboratory equipment."""
        try:
            return await self.laboratory_repository.get_equipment_maintenance_schedule(lab_id)
        except Exception as e:
            logger.error(f"Failed to get equipment maintenance schedule for laboratory {lab_id}: {str(e)}")
            raise
    
    # Analytics and Reporting
    
    async def get_laboratory_stats(self, lab_id: str) -> LaboratoryStats:
        """Get comprehensive statistics for a laboratory."""
        try:
            # Get laboratory
            laboratory = await self.get_laboratory(lab_id)
            if not laboratory:
                raise NotFoundError(f"Laboratory not found with ID: {lab_id}")
            
            # Get booking statistics
            total_bookings = await self.laboratory_repository.get_total_bookings(lab_id)
            completed_bookings = await self.laboratory_repository.get_completed_bookings(lab_id)
            cancelled_bookings = await self.laboratory_repository.get_cancelled_bookings(lab_id)
            
            # Calculate utilization
            utilization_rate = await self._calculate_utilization_rate(lab_id)
            
            # Get equipment statistics
            equipment_count = len(laboratory.equipment)
            equipment_utilization = await self._calculate_equipment_utilization(lab_id)
            
            # Create stats object
            stats = LaboratoryStats(
                laboratory_id=lab_id,
                laboratory_name=laboratory.name,
                total_bookings=total_bookings,
                completed_bookings=completed_bookings,
                cancelled_bookings=cancelled_bookings,
                utilization_rate=utilization_rate,
                equipment_count=equipment_count,
                equipment_utilization=equipment_utilization,
                average_booking_duration=await self._calculate_average_booking_duration(lab_id),
                last_booking_date=await self._get_last_booking_date(lab_id),
                maintenance_required=await self._check_maintenance_required(lab_id),
                safety_compliance=await self._check_safety_compliance(lab_id)
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get laboratory stats for {lab_id}: {str(e)}")
            raise
    
    async def generate_laboratory_report(self, report_type: str = "overview", 
                                      lab_id: str = None, department_id: str = None, 
                                      start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Generate comprehensive laboratory report."""
        try:
            # Generate report based on type
            if report_type == "overview":
                return await self._generate_overview_report(lab_id, department_id, start_date, end_date)
            elif report_type == "utilization":
                return await self._generate_utilization_report(lab_id, department_id, start_date, end_date)
            elif report_type == "equipment":
                return await self._generate_equipment_report(lab_id, department_id, start_date, end_date)
            elif report_type == "maintenance":
                return await self._generate_maintenance_report(lab_id, department_id, start_date, end_date)
            else:
                raise ValidationError(f"Unknown report type: {report_type}")
                
        except Exception as e:
            logger.error(f"Failed to generate laboratory report: {str(e)}")
            raise
    
    # Maintenance and Compliance
    
    async def schedule_maintenance(self, lab_id: str, maintenance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule maintenance for a laboratory."""
        try:
            # Validate laboratory exists
            laboratory = await self.get_laboratory(lab_id)
            if not laboratory:
                raise NotFoundError(f"Laboratory not found with ID: {lab_id}")
            
            # Validate maintenance data
            await self._validate_maintenance_data(maintenance_data)
            
            # Check if laboratory can be maintained
            if not await self._can_perform_maintenance(lab_id, maintenance_data['start_date'], maintenance_data['end_date']):
                raise ConflictError("Cannot schedule maintenance during active bookings")
            
            # Schedule maintenance
            maintenance = await self.laboratory_repository.schedule_maintenance(
                laboratory_id=lab_id,
                **maintenance_data
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return maintenance
            
        except Exception as e:
            logger.error(f"Failed to schedule maintenance for laboratory {lab_id}: {str(e)}")
            raise
    
    async def complete_maintenance(self, maintenance_id: str, completion_data: Dict[str, Any]) -> bool:
        """Complete maintenance for a laboratory."""
        try:
            # Validate completion data
            await self._validate_maintenance_completion(completion_data)
            
            # Complete maintenance
            result = await self.laboratory_repository.complete_maintenance(
                maintenance_id=maintenance_id,
                **completion_data
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to complete maintenance {maintenance_id}: {str(e)}")
            raise
    
    async def check_safety_compliance(self, lab_id: str) -> Dict[str, Any]:
        """Check safety compliance for a laboratory."""
        try:
            # Get laboratory
            laboratory = await self.get_laboratory(lab_id)
            if not laboratory:
                raise NotFoundError(f"Laboratory not found with ID: {lab_id}")
            
            # Check various compliance factors
            compliance_issues = []
            
            # Check equipment maintenance
            overdue_maintenance = await self.laboratory_repository.get_overdue_maintenance(lab_id)
            if overdue_maintenance:
                compliance_issues.append({
                    "type": "maintenance_overdue",
                    "severity": "high",
                    "description": f"{len(overdue_maintenance)} equipment items have overdue maintenance",
                    "affected_items": overdue_maintenance
                })
            
            # Check equipment status
            faulty_equipment = await self.laboratory_repository.get_faulty_equipment(lab_id)
            if faulty_equipment:
                compliance_issues.append({
                    "type": "equipment_faulty",
                    "severity": "high",
                    "description": f"{len(faulty_equipment)} equipment items are faulty",
                    "affected_items": faulty_equipment
                })
            
            # Check safety certifications
            expired_certifications = await self.laboratory_repository.get_expired_certifications(lab_id)
            if expired_certifications:
                compliance_issues.append({
                    "type": "certification_expired",
                    "severity": "medium",
                    "description": f"{len(expired_certifications)} safety certifications have expired",
                    "affected_items": expired_certifications
                })
            
            # Overall compliance status
            compliance_status = "compliant"
            if any(issue["severity"] == "high" for issue in compliance_issues):
                compliance_status = "non_compliant"
            elif compliance_issues:
                compliance_status = "warning"
            
            return {
                "laboratory_id": lab_id,
                "laboratory_name": laboratory.name,
                "compliance_status": compliance_status,
                "compliance_issues": compliance_issues,
                "compliance_score": self._calculate_compliance_score(compliance_issues),
                "last_checked": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to check safety compliance for laboratory {lab_id}: {str(e)}")
            raise
    
    # Batch Operations
    
    async def batch_update_laboratories(self, updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple laboratories."""
        results = {}
        
        for update in updates:
            lab_id = update['laboratory_id']
            try:
                result = await self.update_laboratory(lab_id, update)
                results[lab_id] = result is not None
            except Exception as e:
                logger.error(f"Failed to update laboratory {lab_id}: {str(e)}")
                results[lab_id] = False
        
        return results
    
    async def batch_delete_laboratories(self, lab_ids: List[str]) -> Dict[str, bool]:
        """Delete multiple laboratories."""
        results = {}
        
        for lab_id in lab_ids:
            try:
                result = await self.delete_laboratory(lab_id)
                results[lab_id] = result
            except Exception as e:
                logger.error(f"Failed to delete laboratory {lab_id}: {str(e)}")
                results[lab_id] = False
        
        return results
    
    async def batch_book_laboratories(self, bookings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Book multiple laboratories."""
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
                result = await self.book_laboratory(booking)
                results["success"].append({
                    "laboratory_id": booking["laboratory_id"],
                    "booking_id": result.get("id"),
                    "status": "booked"
                })
                results["summary"]["success"] += 1
                
            except Exception as e:
                results["failed"].append({
                    "laboratory_id": booking.get("laboratory_id"),
                    "error": str(e),
                    "status": "failed"
                })
                results["summary"]["failed"] += 1
        
        return results
    
    # Helper Methods
    
    async def _validate_laboratory_creation(self, data: Dict[str, Any]) -> None:
        """Validate laboratory creation data."""
        required_fields = ['name', 'department_id', 'lab_type', 'capacity', 'location']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate name uniqueness
        existing_lab = await self.laboratory_repository.get_by_name(data['name'])
        if existing_lab:
            raise ConflictError(f"Laboratory with name '{data['name']}' already exists")
        
        # Validate capacity
        if not isinstance(data['capacity'], int) or data['capacity'] <= 0:
            raise ValidationError("Capacity must be a positive integer")
        
        # Validate department exists
        from src.infrastructure.repositories.department_repository import DepartmentRepository
        dept_repo = DepartmentRepository()
        department = await dept_repo.get_by_id(data['department_id'])
        if not department:
            raise NotFoundError(f"Department not found with ID: {data['department_id']}")
        
        # Validate lab type
        valid_types = ['physics', 'chemistry', 'biology', 'computer', 'engineering', 'general']
        if data['lab_type'] not in valid_types:
            raise ValidationError(f"Invalid laboratory type: {data['lab_type']}")
    
    async def _validate_laboratory_update(self, data: Dict[str, Any]) -> None:
        """Validate laboratory update data."""
        allowed_fields = ['name', 'lab_type', 'capacity', 'location', 'description', 'safety_features']
        
        for field in data.keys():
            if field not in allowed_fields:
                raise ValidationError(f"Cannot update field: {field}")
        
        # Validate capacity if provided
        if 'capacity' in data and data['capacity']:
            if not isinstance(data['capacity'], int) or data['capacity'] <= 0:
                raise ValidationError("Capacity must be a positive integer")
    
    async def _validate_booking_data(self, data: Dict[str, Any]) -> None:
        """Validate booking data."""
        required_fields = ['laboratory_id', 'booked_by', 'start_date', 'end_date', 'purpose']
        
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
        
        # Validate laboratory exists
        laboratory = await self.get_laboratory(data['laboratory_id'])
        if not laboratory:
            raise NotFoundError(f"Laboratory not found with ID: {data['laboratory_id']}")
    
    def _calculate_availability(self, laboratory: LaboratoryResponse, bookings: List[Dict[str, Any]], start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Calculate laboratory availability for a date range."""
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
                    "laboratory_id": laboratory.id
                })
            
            availability.extend(day_availability)
            current_date += timedelta(days=1)
        
        return availability
    
    async def _is_laboratory_available(self, lab_id: str, start_date: date, end_date: date) -> bool:
        """Check if laboratory is available for a date range."""
        bookings = await self.laboratory_repository.get_bookings_by_date_range(
            laboratory_id=lab_id,
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
    
    async def _is_equipment_available(self, lab_id: str, equipment_needed: List[Dict[str, Any]]) -> bool:
        """Check if equipment is available for booking."""
        # This would check equipment availability in the repository
        # For now, return True (should be implemented)
        return True
    
    async def _can_cancel_booking(self, booking: Dict[str, Any]) -> bool:
        """Check if booking can be cancelled."""
        start_date = datetime.strptime(booking['start_date'], '%Y-%m-%d').date()
        
        # Can cancel if booking hasn't started and is not in the past
        return start_date > date.today()
    
    async def _has_active_bookings(self, lab_id: str) -> bool:
        """Check if laboratory has active bookings."""
        # This would check for active bookings in the repository
        # For now, return False (should be implemented)
        return False
    
    async def _was_recently_used(self, lab_id: str) -> bool:
        """Check if laboratory was recently used."""
        # This would check recent usage in the repository
        # For now, return False (should be implemented)
        return False
    
    def _calculate_utilization_rate(self, lab_id: str) -> float:
        """Calculate laboratory utilization rate."""
        # This would calculate utilization rate from booking data
        # For now, return 0.0 (should be implemented)
        return 0.0
    
    def _calculate_equipment_utilization(self, lab_id: str) -> float:
        """Calculate equipment utilization rate."""
        # This would calculate equipment utilization rate
        # For now, return 0.0 (should be implemented)
        return 0.0
    
    async def _calculate_average_booking_duration(self, lab_id: str) -> float:
        """Calculate average booking duration for a laboratory."""
        # This would calculate average booking duration
        # For now, return 0.0 (should be implemented)
        return 0.0
    
    async def _get_last_booking_date(self, lab_id: str) -> Optional[str]:
        """Get last booking date for a laboratory."""
        # This would get the last booking date
        # For now, return None (should be implemented)
        return None
    
    async def _check_maintenance_required(self, lab_id: str) -> bool:
        """Check if maintenance is required for a laboratory."""
        # This would check maintenance requirements
        # For now, return False (should be implemented)
        return False
    
    async def _check_safety_compliance(self, lab_id: str) -> bool:
        """Check if laboratory is safety compliant."""
        # This would check safety compliance
        # For now, return True (should be implemented)
        return True
    
    async def _can_perform_maintenance(self, lab_id: str, start_date: date, end_date: date) -> bool:
        """Check if maintenance can be performed on a laboratory."""
        # This would check if maintenance can be performed
        # For now, return True (should be implemented)
        return True
    
    async def _validate_maintenance_data(self, data: Dict[str, Any]) -> None:
        """Validate maintenance data."""
        required_fields = ['start_date', 'end_date', 'description', 'maintenance_type']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required maintenance field '{field}' is missing or empty")
        
        # Validate date format
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError("Invalid date format. Expected: YYYY-MM-DD")
        
        # Validate date logic
        if start_date > end_date:
            raise ValidationError("Start date cannot be after end date")
    
    async def _validate_maintenance_completion(self, data: Dict[str, Any]) -> None:
        """Validate maintenance completion data."""
        required_fields = ['completion_date', 'work_completed', 'next_maintenance_date']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required maintenance completion field '{field}' is missing or empty")
    
    async def _validate_equipment_data(self, data: Dict[str, Any]) -> None:
        """Validate equipment data."""
        required_fields = ['name', 'type', 'quantity', 'condition']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required equipment field '{field}' is missing or empty")
        
        # Validate type
        valid_types = ['microscope', 'computer', 'chemical', 'instrument', 'safety', 'other']
        if data['type'] not in valid_types:
            raise ValidationError(f"Invalid equipment type: {data['type']}")
        
        # Validate condition
        valid_conditions = ['new', 'good', 'fair', 'poor', 'broken']
        if data['condition'] not in valid_conditions:
            raise ValidationError(f"Invalid equipment condition: {data['condition']}")
        
        # Validate quantity
        if not isinstance(data['quantity'], int) or data['quantity'] <= 0:
            raise ValidationError("Quantity must be a positive integer")
    
    async def _validate_equipment_update(self, data: Dict[str, Any]) -> None:
        """Validate equipment update data."""
        allowed_fields = ['name', 'type', 'quantity', 'condition', 'last_maintenance', 'notes']
        
        for field in data.keys():
            if field not in allowed_fields:
                raise ValidationError(f"Cannot update equipment field: {field}")
        
        # Validate type if provided
        if 'type' in data and data['type']:
            valid_types = ['microscope', 'computer', 'chemical', 'instrument', 'safety', 'other']
            if data['type'] not in valid_types:
                raise ValidationError(f"Invalid equipment type: {data['type']}")
        
        # Validate condition if provided
        if 'condition' in data and data['condition']:
            valid_conditions = ['new', 'good', 'fair', 'poor', 'broken']
            if data['condition'] not in valid_conditions:
                raise ValidationError(f"Invalid equipment condition: {data['condition']}")
        
        # Validate quantity if provided
        if 'quantity' in data and data['quantity']:
            if not isinstance(data['quantity'], int) or data['quantity'] < 0:
                raise ValidationError("Quantity must be a non-negative integer")
    
    async def _is_equipment_booked(self, equipment_id: str) -> bool:
        """Check if equipment is currently booked."""
        # This would check if equipment is booked
        # For now, return False (should be implemented)
        return False
    
    def _calculate_compliance_score(self, compliance_issues: List[Dict[str, Any]]) -> int:
        """Calculate compliance score based on issues."""
        if not compliance_issues:
            return 100
        
        score = 100
        for issue in compliance_issues:
            if issue['severity'] == 'high':
                score -= 30
            elif issue['severity'] == 'medium':
                score -= 15
            else:
                score -= 5
        
        return max(0, score)
    
    async def _generate_overview_report(self, lab_id: str, department_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate overview report for laboratories."""
        try:
            # Get laboratories based on filters
            if lab_id:
                laboratories = [await self.get_laboratory(lab_id)]
            elif department_id:
                laboratories = await self.get_laboratories_by_department(department_id, 0, 1000)
            else:
                # Get all laboratories
                laboratories = await self.laboratory_repository.get_all(0, 1000)
            
            if not laboratories:
                raise NotFoundError("No laboratories found for specified criteria")
            
            # Calculate summary statistics
            total_labs = len(laboratories)
            total_capacity = sum(lab.capacity for lab in laboratories)
            total_equipment = sum(len(lab.equipment) for lab in laboratories)
            
            # Group by type
            by_type = {}
            for lab in laboratories:
                lab_type = lab.lab_type
                by_type[lab_type] = by_type.get(lab_type, 0) + 1
            
            return {
                "laboratories": laboratories,
                "summary": {
                    "total_laboratories": total_labs,
                    "total_capacity": total_capacity,
                    "total_equipment": total_equipment,
                    "average_capacity": round(total_capacity / total_labs, 2) if total_labs > 0 else 0,
                    "by_type": by_type
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
    
    async def _generate_utilization_report(self, lab_id: str, department_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate utilization report for laboratories."""
        try:
            # Get laboratories based on filters
            if lab_id:
                laboratories = [await self.get_laboratory(lab_id)]
            elif department_id:
                laboratories = await self.get_laboratories_by_department(department_id, 0, 1000)
            else:
                laboratories = await self.laboratory_repository.get_all(0, 1000)
            
            if not laboratories:
                raise NotFoundError("No laboratories found for specified criteria")
            
            # Calculate utilization for each lab
            utilization_data = []
            total_bookings = 0
            total_utilization = 0
            
            for lab in laboratories:
                stats = await self.get_laboratory_stats(lab.id)
                utilization_data.append({
                    "laboratory_id": lab.id,
                    "laboratory_name": lab.name,
                    "utilization_rate": stats.utilization_rate,
                    "total_bookings": stats.total_bookings,
                    "completed_bookings": stats.completed_bookings,
                    "cancelled_bookings": stats.cancelled_bookings
                })
                
                total_bookings += stats.total_bookings
                total_utilization += stats.utilization_rate
            
            # Calculate overall utilization
            overall_utilization = total_utilization / len(laboratories) if laboratories else 0
            
            return {
                "laboratories": utilization_data,
                "summary": {
                    "total_laboratories": len(laboratories),
                    "total_bookings": total_bookings,
                    "overall_utilization": round(overall_utilization, 2),
                    "peak_utilization_lab": max(utilization_data, key=lambda x: x['utilization_rate']) if utilization_data else None,
                    "lowest_utilization_lab": min(utilization_data, key=lambda x: x['utilization_rate']) if utilization_data else None
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
    
    async def _generate_equipment_report(self, lab_id: str, department_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate equipment report for laboratories."""
        try:
            # Get laboratories based on filters
            if lab_id:
                laboratories = [await self.get_laboratory(lab_id)]
            elif department_id:
                laboratories = await self.get_laboratories_by_department(department_id, 0, 1000)
            else:
                laboratories = await self.laboratory_repository.get_all(0, 1000)
            
            if not laboratories:
                raise NotFoundError("No laboratories found for specified criteria")
            
            # Calculate equipment statistics
            equipment_data = []
            total_equipment = 0
            by_type = {}
            by_condition = {}
            
            for lab in laboratories:
                for equipment in lab.equipment:
                    equipment_data.append({
                        "laboratory_id": lab.id,
                        "laboratory_name": lab.name,
                        "equipment_id": equipment.id,
                        "equipment_name": equipment.name,
                        "equipment_type": equipment.type,
                        "condition": equipment.condition,
                        "quantity": equipment.quantity,
                        "last_maintenance": equipment.last_maintenance
                    })
                    
                    total_equipment += equipment.quantity
                    
                    # Group by type
                    eq_type = equipment.type
                    by_type[eq_type] = by_type.get(eq_type, 0) + equipment.quantity
                    
                    # Group by condition
                    condition = equipment.condition
                    by_condition[condition] = by_condition.get(condition, 0) + equipment.quantity
            
            return {
                "equipment": equipment_data,
                "summary": {
                    "total_equipment": total_equipment,
                    "total_laboratories": len(laboratories),
                    "average_equipment_per_lab": round(total_equipment / len(laboratories), 2) if laboratories else 0,
                    "by_type": by_type,
                    "by_condition": by_condition
                },
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "equipment"
            }
        except Exception as e:
            logger.error(f"Failed to generate equipment report: {str(e)}")
            raise
    
    async def _generate_maintenance_report(self, lab_id: str, department_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate maintenance report for laboratories."""
        try:
            # Get laboratories based on filters
            if lab_id:
                laboratories = [await self.get_laboratory(lab_id)]
            elif department_id:
                laboratories = await self.get_laboratories_by_department(department_id, 0, 1000)
            else:
                laboratories = await self.laboratory_repository.get_all(0, 1000)
            
            if not laboratories:
                raise NotFoundError("No laboratories found for specified criteria")
            
            # Get maintenance data for each lab
            maintenance_data = []
            total_maintenance = 0
            overdue_maintenance = 0
            
            for lab in laboratories:
                maintenance_schedule = await self.get_equipment_maintenance_schedule(lab.id)
                
                for maintenance in maintenance_schedule:
                    if start_date <= datetime.strptime(maintenance['scheduled_date'], '%Y-%m-%d').date() <= end_date:
                        maintenance_data.append({
                            "laboratory_id": lab.id,
                            "laboratory_name": lab.name,
                            "equipment_id": maintenance['equipment_id'],
                            "equipment_name": maintenance['equipment_name'],
                            "maintenance_type": maintenance['maintenance_type'],
                            "scheduled_date": maintenance['scheduled_date'],
                            "status": maintenance['status'],
                            "overdue": maintenance['overdue']
                        })
                        
                        total_maintenance += 1
                        if maintenance['overdue']:
                            overdue_maintenance += 1
            
            return {
                "maintenance": maintenance_data,
                "summary": {
                    "total_maintenance": total_maintenance,
                    "overdue_maintenance": overdue_maintenance,
                    "on_schedule_maintenance": total_maintenance - overdue_maintenance,
                    "maintenance_rate": round((overdue_maintenance / total_maintenance) * 100, 2) if total_maintenance > 0 else 0,
                    "total_laboratories": len(laboratories)
                },
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "report_generated_at": datetime.utcnow().isoformat(),
                "report_type": "maintenance"
            }
        except Exception as e:
            logger.error(f"Failed to generate maintenance report: {str(e)}")
            raise
    
    async def _invalidate_cache(self) -> None:
        """Invalidate laboratory cache."""
        self._cache.clear()
    
    # Abstract method implementations required by BaseService
    
    async def create(self, data: Dict) -> Dict:
        """Create a new laboratory entity."""
        laboratory = await self.create_laboratory(data)
        return laboratory.dict()
    
    async def get(self, id: str) -> Optional[Dict]:
        """Get a laboratory entity by ID."""
        laboratory = await self.get_laboratory_by_id(id)
        return laboratory.dict() if laboratory else None
    
    async def update(self, id: str, data: Dict) -> Dict:
        """Update a laboratory entity by ID."""
        laboratory = await self.update_laboratory(id, data)
        return laboratory.dict()
    
    async def delete(self, id: str) -> bool:
        """Delete a laboratory entity by ID."""
        return await self.delete_laboratory(id)
    
    async def list(self, skip: int = 0, limit: int = 100, filters: Dict = None) -> List[Dict]:
        """List all laboratory entities."""
        laboratories = await self.get_all_laboratories(skip=skip, limit=limit)
        return [laboratory.dict() for laboratory in laboratories]
    
    async def count(self, filters: Dict = None) -> int:
        """Count total number of laboratory entities."""
        return await self.get_laboratory_count()
        self._cache.clear()